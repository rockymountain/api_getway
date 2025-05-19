# ADR-015: Chiến lược quan sát chi phí vận hành (Cost Observability Strategy) cho API Gateway (DX VAS)

* **Trạng thái**: Đã chấp thuận ✅
* **Ngày**: 29/05/2025
* **Người đề xuất**: Nguyễn Văn B (FinOps + DevOps)
* **Bối cảnh**: Dự án Chuyển đổi số VAS

---

## 📌 Bối cảnh

API Gateway vận hành trên nền tảng Cloud Run và sử dụng các tài nguyên liên quan như:

* Redis (memory store)
* Cloud Logging / Monitoring
* Secret Manager, IAM, và gọi đến các backend như SIS, CRM, LMS

Chi phí có thể tăng đột biến nếu không được giám sát. Vì vậy, cần có chiến lược **Cost Observability** giúp:

* Hiểu rõ chi phí theo môi trường, thành phần, tính năng
* Cảnh báo sớm khi chi phí vượt ngưỡng bất thường
* Hỗ trợ tối ưu hóa hạ tầng, autoscaling và usage pattern
* Đáp ứng yêu cầu từ CTO, tài chính, và bảo vệ ngân sách kỹ thuật

---

## 🧠 Quyết định

**Áp dụng chiến lược Cost Observability toàn diện bằng cách gắn nhãn (label), phân nhóm tài nguyên theo môi trường, sử dụng Cloud Billing Export kết hợp BigQuery + Looker Studio để theo dõi và cảnh báo.**

---

## 📊 Thành phần chính của chiến lược

### 1. Gắn nhãn chi phí theo môi trường và module

* Gắn label khi deploy Cloud Run, Redis, Secret Manager:

  * `env=dev|staging|prod`
  * `component=api-gateway`
  * `application=api-gateway`
  * `owner=dx-vas`
* Dùng Terraform hoặc GitHub Actions để enforce tự động gắn label

### 2. Export Billing sang BigQuery

* Bật **Cloud Billing Export → BigQuery** (daily hoặc realtime)
* Tạo bảng `billing_dx_vas` theo format chuẩn của Google Cloud
* Kết nối với Looker Studio hoặc Data Studio để tạo dashboard

### 3. Dashboard chi phí theo chiều:

* Theo thời gian (ngày, tuần, tháng)
* Theo môi trường: `dev`, `staging`, `prod`
* Theo dịch vụ: Cloud Run, Redis, Secret Manager, Logging...
* Theo endpoint (nếu có usage-based pricing như GPT API/Zalo...)
* Theo **tính năng (feature)**: nếu mapping được request hoặc resource với feature cụ thể (dựa trên labeling hoặc usage metadata)

### 4. Alert vượt ngưỡng bất thường

* Cảnh báo qua Cloud Monitoring hoặc Cloud Billing Budgets:

  * Khi chi phí tăng > 30% so với tuần trước
  * Khi vượt 70%, 90% budget theo tháng
* Gửi cảnh báo qua email + Slack (channel `#infra-alert`)

### 5. Best practice & kiểm soát chi phí

* Dọn log cũ: Logging retention giữ 30 ngày (default), không giữ quá dài nếu không cần
* `min-instances`: giữ hợp lý để tránh cold start nhưng không tiêu tốn tài nguyên
* Logging/Tracing chỉ bật DEBUG ở `dev`, bật sampling ở `staging`
* Kiểm soát request outbound (Zalo/GPT) nếu tính phí per-call
* Chọn đúng machine type/size cho Cloud Run instance (CPU/RAM) phù hợp workload
* Review và xóa các tài nguyên không sử dụng (unattached disk, old snapshots, idle services...)

### 6. Trình bày định kỳ (visibility)

* Gửi báo cáo chi phí tự động hàng tuần cho Tech Lead & CTO
* Có dashboard thời gian thực để theo dõi spike bất thường
* Họp FinOps hàng quý để review chi phí, cơ hội tối ưu, và cập nhật ngưỡng cảnh báo

---

## ✅ Lợi ích

* Chủ động kiểm soát ngân sách và tránh sốc chi phí
* Phân tích chi phí chi tiết theo môi trường, thành phần, tính năng
* Tăng khả năng dự báo tài chính và báo cáo kỹ thuật minh bạch
* Gắn liền DevOps ↔ FinOps, hỗ trợ tối ưu chi phí kỹ thuật chiến lược

---

## ❌ Rủi ro & Giải pháp

| Rủi ro                                  | Giải pháp                                                                              |
| --------------------------------------- | -------------------------------------------------------------------------------------- |
| Tài nguyên bị deploy thiếu label        | Terraform enforce hoặc validate CI/CD step                                             |
| Billing export delay ảnh hưởng cảnh báo | Kết hợp Cloud Billing Budgets + BigQuery refresh thường xuyên                          |
| Developer không hiểu dashboard chi phí  | Đào tạo + chú thích rõ filter `env`, `service`, `application`, `owner` trong dashboard |

---

## 🔄 Các lựa chọn đã loại bỏ

* **Theo dõi chi phí thủ công từ billing UI**: Không chi tiết theo môi trường / component
* **Không cảnh báo chi phí tăng đột biến**: Nguy cơ vượt ngân sách mà không biết
* **Không gắn label tài nguyên**: Không thể truy vết chi phí theo nhóm

---

## 📎 Tài liệu liên quan

* Terraform Label Enforcement: [`infra/modules/labels.tf`](../../infra/modules/labels.tf)
* Dev Guide – FinOps: [`DEV_GUIDE.md`](../DEV_GUIDE.md)
* ADR liên quan: [`adr-013-autoscaling-strategy.md`](./adr-013-autoscaling-strategy.md)

---

> “Bạn không thể tối ưu điều mình không đo lường – chi phí cũng cần observability như hệ thống.”
