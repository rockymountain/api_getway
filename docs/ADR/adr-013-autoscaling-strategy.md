# ADR-013: Chiến lược autoscaling cho API Gateway (DX VAS)

* **Trạng thái**: Đã chấp thuận ✅
* **Ngày**: 27/05/2025
* **Người đề xuất**: Nguyễn Minh T (Infrastructure Lead)
* **Bối cảnh**: Dự án Chuyển đổi số VAS

---

## 📌 Bối cảnh

API Gateway là điểm đầu tiếp nhận toàn bộ lưu lượng từ frontend và định tuyến đến backend. Lưu lượng có thể biến động mạnh theo thời điểm (giờ cao điểm, nhập học, chiến dịch truyền thông...). Để đảm bảo tính sẵn sàng, hiệu năng và tối ưu chi phí, cần có chiến lược **autoscaling linh hoạt, phản ứng nhanh và kiểm soát được**.

---

## 🧠 Quyết định

**Triển khai autoscaling dựa trên Cloud Run với các thông số tinh chỉnh cụ thể, kết hợp scaling theo concurrency và alert-based pre-scaling.**

---

## ⚙️ Cấu hình autoscaling chi tiết

### 1. Nền tảng: Cloud Run (fully managed)

* Tự động scale-out instance khi có nhiều request đồng thời
* Tự động scale-in khi idle, tiết kiệm chi phí

### 2. Tham số chính

| Tham số          | Giá trị đề xuất                                                                                                       |
| ---------------- | --------------------------------------------------------------------------------------------------------------------- |
| `max-instances`  | 50 (có thể nâng lên theo nhu cầu)                                                                                     |
| `min-instances`  | 1 (giữ ấm 1 pod, tránh cold start)                                                                                    |
| `concurrency`    | 40 request/instance *(giá trị khởi đầu phù hợp I/O-bound, cần được tinh chỉnh dựa trên kết quả load testing thực tế)* |
| `cpu-throttling` | disabled (giữ CPU active cho min instance)                                                                            |

### 3. Pre-scaling theo cảnh báo (alert-based burst prep)

* Nếu lượng request > 80% tổng capacity trong 2 phút → tăng `min-instances` tạm thời (qua script hoặc GitHub Actions)
* Nếu có lịch cao điểm dự đoán (ví dụ: 8h sáng thứ 2) → tăng min trước 15 phút
* Quản lý qua `gcloud run services update` hoặc thông qua Terraform kết hợp với scheduler/bot để giữ trạng thái hạ tầng nhất quán

### 4. Hạn chế và fallback

* Nếu đạt `max-instances`, Cloud Run sẽ trả 429
* Hệ thống log + alert nếu rate 429 > 1% trong 5 phút
* Cho phép mở rộng `max-instances` qua Alert Policy hoặc dashboard thủ công nhanh chóng

### 5. Giám sát và thử nghiệm chiến lược

* Sử dụng load testing định kỳ để đánh giá phản ứng autoscaling
* Theo dõi metric: `container/busy_request_count`, `concurrent_requests`, `cold_start_duration`
* Tinh chỉnh `concurrency`, `min/max-instances` dựa trên dữ liệu thực tế

---

## ✅ Lợi ích

* Đáp ứng lưu lượng biến động mạnh mà không cần scale thủ công
* Tối ưu chi phí *(chỉ duy trì số lượng instance tối thiểu cần thiết, có thể scale xuống 1 instance khi idle)*
* Giảm cold-start nhờ `min-instances`
* Tự động phản ứng với traffic đột biến qua Alert pre-scaling
* Hạ tầng serverless đơn giản nhưng hiệu quả cao

---

## ❌ Rủi ro & Giải pháp

| Rủi ro                                        | Giải pháp                                                                     |
| --------------------------------------------- | ----------------------------------------------------------------------------- |
| Cold start gây trễ request đầu tiên           | Duy trì `min-instances: 1`, giữ CPU active và theo dõi thời gian cold start   |
| Đạt trần `max-instances` quá sớm              | Theo dõi alert + tự động tăng giới hạn qua Terraform hoặc CLI khi cần         |
| Autoscaling không phản ứng kịp với burst ngắn | Dùng Alert-based pre-scaling + học lịch sử traffic để chủ động tăng min trước |

---

## 🔄 Các lựa chọn đã loại bỏ

* **GKE / Kubernetes HPA**: Quản lý phức tạp hơn, không cần thiết với Gateway stateless
* **Always-on fixed pod count**: Tốn chi phí, không tận dụng được serverless
* **Manual scaling**: Phản ứng chậm, không phù hợp hệ thống real-time traffic biến động

---

## 📎 Tài liệu liên quan

* Cloud Run autoscaling: [https://cloud.google.com/run/docs/about-autoscaling](https://cloud.google.com/run/docs/about-autoscaling)
* Script pre-scaling: [`scripts/pre_scale.sh`](../../scripts/pre_scale.sh)
* Dev Guide – Deployment: [`DEV_GUIDE.md`](../DEV_GUIDE.md)
* ADR liên quan: [`adr-010-deployment-strategy.md`](./adr-010-deployment-strategy.md)

---

> “Autoscaling không chỉ là mở rộng – mà là phản ứng thông minh với sự thay đổi.”
