# ADR-011: Chiến lược quản lý và xoay vòng secrets (Secrets Rotation) cho API Gateway (DX VAS)

* **Trạng thái**: Đã chấp thuận ✅
* **Ngày**: 25/05/2025
* **Người đề xuất**: Nguyễn Thị H (Security Engineer)
* **Bối cảnh**: Dự án Chuyển đổi số VAS

---

## 📌 Bối cảnh

API Gateway cần truy cập nhiều hệ thống khác như Cloud SQL, Redis, third-party API (Zalo, Google OAuth...), và CI/CD. Những hệ thống này sử dụng các **secrets** như access token, API key, database password hoặc service account. Để đảm bảo an toàn lâu dài, cần có chiến lược **quản lý, lưu trữ và xoay vòng (rotate) secrets định kỳ**.

---

## 🧠 Quyết định

**Áp dụng chiến lược lưu trữ secrets tập trung bằng Google Secret Manager kết hợp GitHub Secrets cho CI/CD, và định kỳ xoay vòng (rotation) tối thiểu mỗi 90 ngày hoặc sớm hơn nếu bị lộ.**

---

## 🔐 Chi tiết chiến lược

### 1. Lưu trữ secrets

* Secrets dùng cho **runtime** lưu trong **Google Secret Manager**, được inject trực tiếp vào container Cloud Run thông qua cấu hình service (khuyến nghị chính thức của Google)
* Secrets dùng cho **CI/CD build-time** (GitHub Actions) lưu trong **GitHub Secrets**
* Không commit bất kỳ secrets nào vào codebase, log hoặc output pipeline

### 2. Loại secrets áp dụng

| Loại secrets    | Ví dụ                                                               |
| --------------- | ------------------------------------------------------------------- |
| DB password     | Cloud SQL user password                                             |
| API key         | Zalo, Firebase, OAuth2 credentials                                  |
| JWT secret      | Signing key cho access token                                        |
| Webhook secret  | Slack, Zalo outbound validation                                     |
| Redis password  | redis\://:<secret>@host\:port                                       |
| Service account | GCP identity used for CI/CD auth (qua Workload Identity Federation) |

### 3. Cách truy xuất tại runtime

* Secrets được inject tự động từ **Google Secret Manager** vào **biến môi trường của container** (qua Cloud Run service config)
* Không gọi Secret Manager mỗi request (tránh ảnh hưởng hiệu năng/cost)
* Secrets cũng có thể được mount vào file hoặc .env qua `gcloud secrets versions access` trong `prestart.sh` nếu chưa dùng native Cloud Run secret integration

### 4. Xoay vòng (rotation policy)

* **Xoay vòng mặc định mỗi 90 ngày** cho tất cả secrets (tuân thủ nguyên tắc zero-trust)
* Một số secrets quan trọng như JWT signing key → xoay mỗi 30 ngày, hỗ trợ multi-version key (forward compatibility)
* Cho phép **xoay sớm** khi:

  * Có thay đổi nhân sự (offboarding)
  * Nghi ngờ rò rỉ
  * Key/API sắp hết hạn hoặc bị revoke

### 5. Rotation workflow

* Secrets mới được tạo bằng CLI (`gcloud secrets versions add`) hoặc Terraform
* Với **runtime secrets**:

  * Cập nhật `revision` của Cloud Run để sử dụng phiên bản secret mới
  * Deploy thông qua CI/CD hoặc `gcloud run services update`
* Với **CI/CD secrets**:

  * Cập nhật giá trị mới trong GitHub Secrets hoặc Secret Manager nếu dùng workload identity
* Có thể tự động hóa rotation bằng Cloud Scheduler hoặc CI bot cho một số loại secrets (ví dụ: Cloud SQL auto-rotate + trigger pipeline)
* Sau khi rollout thành công → **vô hiệu hóa (disable)** bản secret cũ sau 24 giờ

### 6. Giám sát & alert

* Cảnh báo nếu secret tồn tại >90 ngày chưa rotate
* Log mọi truy cập vào secret trong Cloud Audit Logging
* Security bot CI chạy định kỳ (tuần/lần) để cảnh báo secrets không được sử dụng hoặc trùng nhau

---

## ✅ Lợi ích

* Bảo vệ khỏi rủi ro bị rò rỉ credentials lâu dài
* Giảm rủi ro lỗi con người qua quy trình xoay vòng tự động hóa
* Gắn liền với CI/CD, có thể kiểm soát và audit dễ dàng
* Hỗ trợ rollback nhanh khi secret gây lỗi

---

## ❌ Rủi ro & Giải pháp

| Rủi ro                                       | Giải pháp                                                                             |
| -------------------------------------------- | ------------------------------------------------------------------------------------- |
| Quên cập nhật secret mới vào cấu hình deploy | Tích hợp check PR, Slack reminder, validate secrets trước deploy                      |
| Secret bị log ra stdout hoặc debug           | Kiểm tra kỹ output pipeline, log masking, cấm log giá trị có `SECRET`, `TOKEN`, `KEY` |
| Secret mới bị lỗi runtime                    | Luôn rollout đầu tiên ở `staging`, giữ secret cũ hoạt động 24h để fallback nếu cần    |

---

## 🔄 Các lựa chọn đã loại bỏ

* **Lưu secrets trong `.env` commit trong Git**: Không an toàn, không kiểm soát được quyền truy cập
* **Lưu tất cả secrets trong GitHub Secrets**: Thiếu phân quyền runtime, không audit được
* **Không xoay vòng**: Rủi ro nghiêm trọng nếu secrets bị lộ, không tuân thủ tiêu chuẩn bảo mật ngành

---

## 📎 Tài liệu liên quan

* Secrets loading script (legacy fallback): [`scripts/load_secrets.sh`](../../scripts/load_secrets.sh)
* Dev Guide – Secrets & Security: [`DEV_GUIDE.md`](../DEV_GUIDE.md)
* ADR liên quan: [`adr-009-security-hardening.md`](./adr-009-security-hardening.md)

---

> “Không có secret nào nên sống mãi – mọi credentials đều cần được thay thế định kỳ.”
