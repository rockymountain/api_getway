# ADR-021: Zero-Downtime Deployment for APIs (Triển khai không gián đoạn)

* **Trạng thái**: Đã chấp thuận ✅
* **Ngày**: 04/06/2025
* **Người đề xuất**: Trần Quang H (DevOps Lead)
* **Bối cảnh**: Dự án Chuyển đổi số VAS

---

## 📌 Bối cảnh

API Gateway là tuyến đầu xử lý toàn bộ request từ client (web, mobile, partner). Việc deploy phiên bản mới (gateway, route logic, auth middleware...) không được phép gây downtime, vì sẽ ảnh hưởng ngay đến người dùng. Một số deployment cũng yêu cầu nâng cấp schema, chỉnh sửa logic header, hoặc cập nhật OpenAPI mà không phá vỡ kết nối đang tồn tại.

---

## 🧠 Quyết định

**Áp dụng chiến lược triển khai không gián đoạn (Zero-Downtime Deployment) dựa trên Cloud Run revisions, canary rollout theo traffic splitting, backward compatibility, và kiểm tra tự động trước/sau deploy.**

---

## ⚙️ Thành phần của chiến lược

### 1. Canary rollout bằng Cloud Run traffic splitting

* Mỗi deploy tạo 1 revision mới
* Rollout theo giai đoạn:

  * 5% traffic trong 3 phút → 25% → 100% nếu không có lỗi
* Dùng GitHub Actions + gcloud CLI để kiểm soát rollout
* Có thể rollback nhanh về revision cũ chỉ với 1 lệnh CLI (gcloud) hoặc qua UI Console

### 2. Backward Compatibility

* Không deploy breaking change nếu chưa có version mới (/v2)
* Middleware mới, logic auth, header mới phải **không thay đổi hành vi cho client hiện tại**
* Nếu cần thay đổi schema → đánh dấu optional hoặc giới thiệu field mới qua versioned model

### 3. Sticky traffic & long-lived connections

* Tránh thay đổi cấu trúc header hoặc token đột ngột giữa các revision
* Cho phép request cũ (chưa có header mới) hoạt động song song
* Cloud Run hỗ trợ xử lý graceful shutdown: giữ các HTTP keep-alive hoặc long-polling connection đang mở trên revision cũ cho đến khi kết thúc
* Nếu dùng gRPC: đảm bảo client có retry logic và reconnect timeout phù hợp

### 4. Database migration không blocking

* Không thực hiện destructive migration đồng thời với deploy
* Áp dụng chiến lược migration 2 bước:

  * Add column mới → deploy → migrate dữ liệu → xoá hoặc đổi schema sau (post-deploy)
* Sử dụng `alembic` để quản lý migration theo version + CI kiểm tra checksum

### 5. Tự động hoá kiểm tra trước và sau khi deploy

* Trước deploy:

  * Kiểm tra schema diff bằng `oasdiff` hoặc `schemathesis diff`
  * Contract testing (Pact) với các consumer hiện tại
* Sau deploy:

  * Giám sát log error, circuit breaker, latency spike (Cloud Monitoring)
  * Nếu pass 100% → gửi Slack confirmation + đánh tag revision ổn định

### 6. Health check & revision warm-up

* Dùng endpoint `/healthz` (không phụ thuộc DB) để xác định readiness
* Gọi warm-up request trước rollout để cache schema/middleware/token verifier
* Cloud Run giữ min-instances > 0 để đảm bảo không cold-start khi switch revision

### 7. Rollback chiến lược

* Mỗi deploy có tag cụ thể (`deploy-20240604T0930-githash1234`)
* Nếu có lỗi:

  * Chạy: `gcloud run services update-traffic --to-revisions=rev_sha=100`
  * Hệ thống trở lại revision ổn định **trong vòng < 30s**, bao gồm thời gian phát hiện, xác nhận lỗi, và thực hiện rollback thủ công hoặc từ alert automation (Slack → Bot → CLI)

---

## ✅ Lợi ích

* Tránh downtime cho API critical
* Rollback nhanh và traceable
* Giám sát và kiểm soát rollout rõ ràng từng revision
* Tăng độ tin cậy khi triển khai tính năng mới, migration, hoặc refactor lớn

---

## ❌ Rủi ro & Giải pháp

| Rủi ro                                                | Giải pháp                                                            |
| ----------------------------------------------------- | -------------------------------------------------------------------- |
| Breaking change chưa versioned → lỗi client           | Bắt buộc kiểm tra schema diff + test contract trước khi rollout      |
| Lỗi logic nhưng không fail request → rollout tiếp tục | Tích hợp metric + alert nếu error rate bất thường dù response là 200 |
| Cold start khi switch revision                        | Dùng min-instances + warm-up logic để đảm bảo readiness              |

---

## 🔄 Các lựa chọn đã loại bỏ

* **Recreate service thay vì revision**: gây downtime, mất traceability
* **Blue/Green bằng 2 service khác nhau**: tăng chi phí + khó quản lý domain + IAM routing
* **Không kiểm tra gì trước rollout 100%**: tăng nguy cơ gây outage cho production

---

## 📎 Tài liệu liên quan

* Rollout GitHub Workflow: [`.github/workflows/deploy.yml`](../../.github/workflows/deploy.yml)
* Canary Strategy Config: [`infra/deploy/canary.yaml`](../../infra/deploy/canary.yaml)
* Dev Guide – Deployment & Release: [`DEV_GUIDE.md`](../DEV_GUIDE.md)
* ADR liên quan: [`adr-010-deployment-strategy.md`](./adr-010-deployment-strategy.md)

---

> “Triển khai không gián đoạn không phải là lựa chọn xa xỉ – mà là tiêu chuẩn cho API hiện đại.”
