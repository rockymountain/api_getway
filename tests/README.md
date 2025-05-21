# 🧪 Bộ kiểm thử Tuân thủ Kiến trúc – API Gateway DX VAS

Dưới đây là kế hoạch xây dựng bộ kiểm thử đầy đủ để đảm bảo team phát triển (nội bộ hoặc thuê ngoài) tuân thủ đúng thiết kế và các quyết định kiến trúc của hệ thống API Gateway DX VAS.

---

## 🔹 BƯỚC 1 – Xây dựng Khung Kiểm thử (Test Framework Setup)

### 🔧 Ngôn ngữ và Thư viện
- **Ngôn ngữ:** Python
- **Testing Framework:**
  - `pytest`
  - `pytest-asyncio` (cho FastAPI async)
  - `httpx` (hỗ trợ async client)
  - `schemathesis` (OpenAPI test)
  - `pact-python` (Contract Testing)
  - `pytest-cov` (Coverage)

### 📁 Cấu trúc thư mục `tests/`
```bash
tests/
├── conftest.py
├── test_auth.py                     # adr-006-auth-design.md
├── test_rbac.py                     # adr-002-rbac-design.md
├── test_error_format.py             # adr-007-error-handling.md
├── test_versioning.py               # adr-004-api-versioning.md
├── test_rate_limit.py               # adr-008-rate-limiting.md
├── test_security_headers.py         # adr-009-security-hardening.md
├── test_caching.py                  # adr-017-caching-strategy.md
├── test_fallback.py                 # adr-016-resilience-fallback-strategy.md
├── test_openapi_compliance.py       # adr-018-api-governance.md
├── test_proxy_logic.py              # Proxy logic testing
├── test_request_validation.py       # Pydantic schema tests
├── test_notification_integration.py# Notify service
├── contract/
│   └── consumer_test.py             # adr-019-contract-testing.md
└── performance/
    └── (Locust, k6 - optional)
```

---

## 🔹 BƯỚC 2 – Định nghĩa Bộ Scenarios Chính (Test Design)

### ✅ Scenario chính liên kết ADRs:
| Tên Test Case | Mục tiêu | ADR liên quan |
|---------------|----------|----------------|
| `test_login_google_oauth2()` | Đăng nhập & token | adr-006-auth-design.md |
| `test_jwt_signature_invalid()` | Xử lý JWT lỗi | adr-006-auth-design.md |
| `test_refresh_token_valid()` | Làm mới access token | adr-006-auth-design.md |
| `test_refresh_token_expired()` | Token hết hạn | adr-006-auth-design.md |
| `test_rbac_permission_denied()` | Thiếu quyền | adr-002-rbac-design.md, adr-007-error-handling.md |
| `test_rbac_permission_granted_specific_role()` | Gán đúng quyền | adr-002-rbac-design.md |
| `test_rbac_cache_invalidation_on_permission_change()` | Invalidate cache | adr-002-rbac-design.md, adr-017-caching-strategy.md |
| `test_api_prefix_version()` | `/api/v1` đúng | adr-004-api-versioning.md |
| `test_rate_limit_exceeded()` | Trả 429 | adr-008-rate-limiting.md |
| `test_security_headers()` | HSTS, CSP, etc. | adr-009-security-hardening.md |
| `test_cache_behavior()` | TTL & storage | adr-017-caching-strategy.md |
| `test_proxy_backend_timeout()` | fallback 503 | adr-016-resilience-fallback-strategy.md |
| `test_error_schema_fields()` | error_code, message... | adr-007-error-handling.md |
| `contract_test_sis_proxy()` | Pact Contract | adr-019-contract-testing.md |
| `test_structured_logging_format()` | Đúng log format | adr-005-observability.md |
| `test_audit_log_created_for_sensitive_action()` | Log hành động nhạy cảm | adr-012-audit-logging.md |
| `test_secret_loaded_from_gcp()` | Secret Manager | adr-011-secrets-rotation.md |

### 🔎 Bổ sung theo kiến trúc:
- Test `X-Request-ID`, `traceparent`, distributed trace (adr-005-observability.md)
- Xác minh (qua pipeline IaC/policy tools) rằng `Terraform apply` tạo Cloud Run, Redis, SQL đúng tags (adr-023-infrastructure-as-code-terraform-strategy.md)
- Test header forwarding khi proxy (X-User-Id, X-Role, ...)

---

## 🔹 BƯỚC 3 – Tích hợp vào CI/CD

### 🛠 GitHub Actions (trích đoạn):
```yaml
- name: 🔍 Run API Compliance Tests
  run: |
    pip install -r requirements-dev.txt
    pytest --cov=app tests/
```

### ✅ Notes:
- `--cov=app` cần map đúng thư mục mã nguồn
- Contract tests (Pact) có thể tách job riêng
- Có thể tạo badge coverage với Codecov hoặc Coveralls
- Áp dụng triệt để pip-tools:
  - Hãy tạo các file requirements.in và requirements-dev.in tương ứng.
  - Sử dụng pip-compile để tạo ra các file requirements.txt và requirements-dev.txt.
  - Hướng dẫn team dev sử dụng workflow mới này (ví dụ: khi thêm dependency mới, thêm vào file .in rồi chạy pip-compile).
  ```bash
  pip install -r requirements-dev.txt # Để cài đặt tất cả cho môi trường dev
  ```
---

## 📌 Lời nhắn cho Tem Dev và QA/QC

---

### **1. Hiện thực hóa các Test Scenarios còn lại**

Dựa trên phần **"BƯỚC 2 – Định nghĩa Bộ Scenarios Chính (Test Design)"** team phát triển (hoặc QA) sẽ tiếp tục:

- Viết code chi tiết cho các test case chưa được hiện thực hóa.
- Bao gồm các luồng "happy path" và các trường hợp biên (edge case).
- Liên kết rõ ràng mỗi test case với ADR tương ứng để đảm bảo tuân thủ thiết kế.

---

### **2. Tinh chỉnh Fixtures**

- Mở rộng hoặc tái cấu trúc các fixtures trong `conftest.py`:
  - Thêm user với nhiều role/permission phức tạp hơn.
  - Tạo fixture JWT token cho các vai trò như `admin`, `teacher`, `guest`, v.v.
  - Mock các dịch vụ bên ngoài nếu cần (ví dụ: Google OAuth2, Redis cache…).

---

### **3. Xác định chính xác Key Pattern cho Rate Limit**

- Đảm bảo hiểu rõ cách thư viện rate limit tạo key trong Redis.
- Tinh chỉnh pattern trong fixture `reset_rate_limit_for_client_ip` để:
  - Xóa đúng các key Redis cho test.
  - Không ảnh hưởng đến dữ liệu dev hoặc các test khác.
- Đây là bước thiết yếu để các test rate limit luôn hoạt động ổn định.

---

### **4. Thiết lập và Phát triển Contract Tests (Pact)**

- Áp dụng theo [ADR-019 - Contract Testing].
- Phối hợp với các nhóm frontend/mobile hoặc đối tác bên thứ ba.
- Thiết kế các "contract" rõ ràng và kiểm tra việc thực hiện đúng ở cả 2 phía (consumer - provider).
- Đưa vào CI/CD để chạy định kỳ hoặc theo sự kiện.

---

### **5. Lên kế hoạch cho Performance Tests**

- Dù là *optional* ở giai đoạn này, cần có roadmap cụ thể:
  - Khi nào bắt đầu?
  - Dùng công cụ nào? (Locust, k6, Artillery…)
  - Mục tiêu gì? (Throughput, latency, stability…)

---

### **6. Liên tục Review và Cải tiến Bộ Test**

- Bộ test là một **thực thể sống**:
  - Luôn cập nhật khi có thay đổi trong hệ thống.
  - Thêm test cho bug đã fix, feature mới.
  - Cải thiện tốc độ và độ tin cậy.
- Khuyến khích mỗi Pull Request phải đi kèm test case (hoặc lý do rõ ràng nếu không cần).
- Định kỳ rà soát code coverage và chất lượng test.

---

## 🎯 Lời khuyên “Legendary Hero”

- **Bắt đầu sớm:** định nghĩa test từ khi giao team ngoài
- **Giao cho QA/Dev triển khai, bạn chỉ cần phê duyệt test scenario**
- **CI/CD phải fail nếu vi phạm quy ước (ADR, schema lỗi, coverage < 80%)**