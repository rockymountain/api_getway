# ADR-010: Chiến lược triển khai (Deployment Strategy) cho API Gateway (DX VAS)

* **Trạng thái**: Đã chấp thuận ✅
* **Ngày**: 24/05/2025
* **Người đề xuất**: Nguyễn Văn L (DevOps)
* **Bối cảnh**: Dự án Chuyển đổi số VAS

---

## 📌 Bối cảnh

API Gateway là thành phần trung tâm của hệ thống, định tuyến mọi request frontend đến các backend dịch vụ như SIS, CRM, LMS. Việc triển khai thay đổi (deploy code mới) cần đảm bảo:

* Không gây downtime cho người dùng cuối
* Cho phép rollback nhanh khi có lỗi
* Có thể thử nghiệm bản mới (canary) trước khi rollout toàn bộ
* Tự động hoá trong CI/CD nhưng vẫn an toàn kiểm soát

---

## 🧠 Quyết định

**Áp dụng chiến lược triển khai theo mô hình Blue/Green kết hợp Canary rollout (cho staging/production) sử dụng Cloud Run revisions và traffic splitting.**

---

## 🚀 Chi tiết triển khai

### 1. Sử dụng Cloud Run Revisions

* Mỗi lần deploy tạo 1 revision mới (immutable)
* Có thể truy cập từng revision bằng URL riêng (để kiểm thử nội bộ)

### 2. Canary rollout bằng traffic splitting

* Khi deploy staging hoặc production:

  * **Giai đoạn 1**: 5% traffic → revision mới, 95% → stable
  * **Giai đoạn 2**: sau 5 phút, nếu không có alert:

    * 50% traffic → revision mới
    * 50% traffic → stable
  * **Giai đoạn 3**: sau 10 phút tiếp theo không có lỗi → 100% traffic chuyển sang revision mới
* Các chỉ số được giám sát trong mỗi giai đoạn:

  * Tỷ lệ lỗi 5xx, 4xx bất thường qua Cloud Monitoring
  * Latency trung bình (p50/p90) không tăng >30% so với baseline
  * Tỷ lệ `429` hoặc `RBAC denied` tăng bất thường
* Có thể dừng rollout hoặc revert bằng `gcloud run services update-traffic`

### 3. Rollback nhanh bằng revision stable

* Nếu xảy ra lỗi sau khi rollout:

  * Revert ngay về revision trước đó (chỉ 1 lệnh CLI hoặc GitHub Action)
  * Không cần rebuild lại image, rollback trong vài giây
  * Log nguyên nhân tự động ghi nhận từ Alert đã kích hoạt rollback (dựa vào `incident_id`, metric\_name, revision\_id)

### 4. Triển khai staging → production

* Mỗi commit lên `dev` → build + deploy lên `staging`
* Sau khi test xong + approve thủ công → merge vào `main`
* `main` trigger deploy production + bắt đầu canary rollout
* **Giai đoạn chuyển từ 50% → 100% cần approval manual step trong GitHub Actions** để đảm bảo kiểm soát tuyệt đối trước khi chuyển toàn bộ lưu lượng

### 5. Canary condition (success/fail)

* **Success nếu**:

  * Không có alert 5xx/latency/4xx tăng bất thường
  * Latency không tăng >30% so với baseline 1 giờ qua (so sánh p50 và p90)
* **Fail nếu**:

  * Alert >5% lỗi trong 5 phút
  * Canary bị rollback tự động + ghi nhận alert trigger root cause

---

## ✅ Lợi ích

* Không downtime khi deploy
* Giảm rủi ro sản xuất do rollout sai
* Có thể kiểm thử nội bộ qua URL revision
* Rollback cực nhanh chỉ với 1 command
* Kiểm soát rollout rõ ràng qua approval workflow
* Gắn chặt với CI/CD và Cloud Run native

---

## ❌ Rủi ro & Giải pháp

| Rủi ro                                             | Giải pháp                                                                                          |
| -------------------------------------------------- | -------------------------------------------------------------------------------------------------- |
| Canary rollout thất bại nhưng alert phát hiện chậm | Tối ưu alert theo thời gian thực (Cloud Monitoring) + refine metric & SLO                          |
| Rollback thủ công tốn thời gian                    | Script rollback (`gcloud run services update-traffic`) + trigger GitHub Action rollback nếu fail   |
| Khó theo dõi rollout tiến trình                    | Log chi tiết trạng thái rollout + gửi Slack/email notification tự động từ CI/CD khi deploy/cutover |

---

## 🔄 Các lựa chọn đã loại bỏ

* **Recreate toàn bộ service mỗi lần deploy**: Gây downtime ngắn, rollback chậm, không tận dụng Cloud Run revision
* **Manual deploy bằng `gcloud run deploy` mỗi lần**: Không phù hợp với CI/CD automation, dễ sai sót
* **Blue/Green tách hẳn 2 service**: Phức tạp trong quản lý domain, SSL, IAM + tăng chi phí

---

## 📎 Tài liệu liên quan

* GitHub Actions CI/CD: [`.github/workflows/ci.yml`](../../.github/workflows/ci.yml)
* Cloud Run rollout: [https://cloud.google.com/run/docs/deploying#rollbacks](https://cloud.google.com/run/docs/deploying#rollbacks)
* Dev Guide – CI/CD section: [`DEV_GUIDE.md`](../DEV_GUIDE.md)
* ADR liên quan: [`adr-003-ci-cd-structure.md`](./adr-003-ci-cd-structure.md)

---

> “Triển khai an toàn là sự kết hợp giữa tự động hóa và kiểm soát thông minh.”
