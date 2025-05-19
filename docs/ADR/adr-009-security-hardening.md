# ADR-009: Chiến lược tăng cường bảo mật (Security Hardening) cho API Gateway (DX VAS)

* **Trạng thái**: Đã chấp thuận ✅
* **Ngày**: 23/05/2025
* **Người đề xuất**: Trần Thị B (DevOps)
* **Bối cảnh**: Dự án Chuyển đổi số VAS

---

## 📌 Bối cảnh

API Gateway là điểm đầu của toàn bộ hệ thống backend. Mọi dữ liệu và thao tác từ phía frontend đều đi qua đây. Việc tăng cường bảo mật là **bắt buộc** để:

* Ngăn chặn tấn công phổ biến (SQLi, XSS, CSRF, header injection…)
* Bảo vệ thông tin người dùng (PII, token, dữ liệu học sinh)
* Tuân thủ tiêu chuẩn bảo mật nội bộ và ngành giáo dục
* Giảm thiểu bề mặt tấn công toàn hệ thống

---

## 🧠 Quyết định

**Áp dụng chiến lược Security Hardening toàn diện tại API Gateway, bao gồm các lớp: transport, application, header, token/session, logging, dependency, và CI/CD.**

---

## 🔐 Các lớp bảo vệ chính

### 1. Transport Layer

* Chỉ chấp nhận kết nối qua HTTPS (bắt buộc Cloud Run HTTPS)
* Tắt HTTP fallback nếu dùng Cloud Load Balancer
* Dùng TLS 1.2+ và Google-managed cert

### 2. Application Layer (FastAPI)

* Sanitize input: tất cả dữ liệu từ body/query/header đều được kiểm tra qua Pydantic
* Giới hạn kích thước request body (upload, JSON...)
* Tự động từ chối content-type không hợp lệ
* Nguy cơ CSRF hiện tại rất thấp do sử dụng token-based auth, nhưng nếu trong tương lai có endpoint nhận form/cookie (đặc biệt trang admin), cần xem xét bảo vệ CSRF token rõ ràng

### 3. Header Security

* Thêm các header bảo vệ chuẩn OWASP:

  * `Strict-Transport-Security`
  * `X-Frame-Options: DENY`
  * `X-Content-Type-Options: nosniff`
  * `Referrer-Policy: no-referrer`
  * `Permissions-Policy: geolocation=()`
  * *(Optional nếu có HTML content)*: `Content-Security-Policy`
* Xoá các header mặc định tiết lộ thông tin nội bộ: `server`, `x-powered-by`

### 4. Token & Session

* Bắt buộc `Authorization: Bearer <token>` với JWT access token
* Không bao giờ đưa token lên URL (chỉ gửi qua header)
* Refresh token được mã hoá và lưu server-side (DB), có thể đặt trong HttpOnly cookie nếu hỗ trợ web frontend
* Access Token nên lưu trong memory hoặc sessionStorage, **không dùng localStorage** để tránh XSS
* TTL access token ngắn (\~15 phút), refresh token có thể bị revoke bất kỳ lúc nào

### 5. Rate limiting & IP filter

* Áp dụng rate limiting (xem [ADR-008](./adr-008-rate-limiting.md))
* Cloud Armor chặn IP trong deny-list, hoặc các vùng địa lý bị hạn chế

### 6. Logging & Monitoring

* Không log access token/refresh token trong bất kỳ context nào
* Gắn `request_id`, `user_id`, `path`, `status_code`, `latency_ms` cho mỗi request
* Cảnh báo nếu phát hiện truy cập sai pattern, brute-force, tăng đột biến bất thường

### 7. Dependency & Image

* Lock version `requirements.txt` và tách rõ `dev` vs `prod`
* Quét bảo mật tự động bằng `safety`, `bandit` trong CI
* Dùng `python:3.10-slim` hoặc `distroless` làm base image
* Multi-stage Docker build để giảm attack surface
* Scan image bằng `trivy` hoặc Cloud Build Security Scanner

### 8. CI/CD & Secrets

* Dùng **Workload Identity Federation** để tránh dùng file service-account key
* Secrets quản lý qua GitHub Secrets hoặc GCP Secret Manager
* Không hard-code bất kỳ secret/token nào trong codebase
* PR bắt buộc pass pre-commit, test, lint, security scan trước khi deploy

---

## ✅ Lợi ích

* Giảm thiểu rủi ro bảo mật theo OWASP Top 10
* Bảo vệ dữ liệu người dùng và hệ thống backend ở nhiều tầng
* Tăng uy tín và độ tin cậy vận hành cho hệ thống
* Chuẩn hoá các tiêu chuẩn nội bộ và sẵn sàng scale lớn

---

## ❌ Rủi ro & Giải pháp

| Rủi ro                                          | Giải pháp                                                           |
| ----------------------------------------------- | ------------------------------------------------------------------- |
| Vô tình chặn request hợp lệ                     | Ghi log chi tiết + allowlist tạm thời cho IP/token/debug nếu cần    |
| Dependency lỗi bảo mật nhưng chưa được cập nhật | Dùng Dependabot + cảnh báo định kỳ CI scan                          |
| Secrets bị log ra stdout                        | Đặt guard trong middleware log + CI kiểm tra output trước khi merge |

---

## 🔄 Các lựa chọn đã loại bỏ

* **Không dùng HTTPS ở local**: Có thể chấp nhận cho local dev, nhưng staging & prod luôn yêu cầu HTTPS
* **Dùng JWT chứa nhiều thông tin nhạy cảm (PII)**: Thay thế bằng ID và lấy thông tin theo thời gian thực (RBAC)
* **Lưu access token trong localStorage**: Chuyển sang lưu session hoặc memory để giảm thiểu XSS

---

## 📎 Tài liệu liên quan

* Middleware bảo mật: [`utils/security_headers.py`](../../utils/security_headers.py)
* Dev Guide – Security section: [`DEV_GUIDE.md`](../DEV_GUIDE.md)
* ADR trước: [`adr-008-rate-limiting.md`](./adr-008-rate-limiting.md)

---

> “Bảo mật không phải là một lựa chọn – mà là một cam kết lâu dài.”
