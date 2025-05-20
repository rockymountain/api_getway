**Tài liệu Dev Guide – Từ 0 đến Hero – Dự án Chuyển đổi số VAS**

---

## **I. Mục tiêu của tài liệu**

Hướng dẫn chi tiết dành cho developer mới bắt đầu tham gia vào hệ thống DX VAS, bao gồm quy trình thiết lập môi trường, coding convention, làm việc nhóm, testing, CI/CD, bảo mật và vận hành. Tài liệu này giúp đảm bảo mọi thành viên đều có thể làm việc hiệu quả và thống nhất.

---

## **II. Thiết lập môi trường phát triển**

### **1. Công cụ cần cài đặt**

* Python >= 3.10
* Docker & Docker Compose
* Git
* PostgreSQL client (psql hoặc DBeaver)
* Redis client (redis-cli hoặc TablePlus)
* VSCode hoặc PyCharm

### **2. Clone dự án và cấu hình ban đầu**

```bash
git clone https://github.com/rockymountain/api-gateway.git
cd api-gateway
cp .env.example .env
```

#### **Pre-commit hooks (Legendary Touch)**

```bash
pip install pre-commit
pre-commit install
```

File `.pre-commit-config.yaml` nên bao gồm:

```yaml
repos:
  - repo: https://github.com/psf/black
    rev: stable
    hooks:
      - id: black
  - repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
      - id: flake8
  - repo: https://github.com/PyCQA/isort
    rev: 5.12.0
    hooks:
      - id: isort
```

### **3. (Tùy chọn) Tạo môi trường ảo nếu không dùng Docker**

```bash
python -m venv venv
source venv/bin/activate  # Trên Windows: .\venv\Scripts\activate
pip install -r requirements.txt
```

Nếu có file riêng `requirements-dev.txt`:

```bash
pip install -r requirements-dev.txt
```

### **4. Chạy dự án local bằng Docker Compose**

```bash
docker-compose up --build
```

Truy cập FastAPI docs tại `http://localhost:8000/docs`

### **5. prestart.sh (Legendary Touch)**

File `prestart.sh`:

```bash
#!/bin/bash
# ./wait-for-postgres.sh $DB_HOST $DB_PORT --timeout=30
alembic upgrade head
exec uvicorn app.main:app --host 0.0.0.0 --port 8080
```

Nên được gọi từ Dockerfile như sau:

```Dockerfile
CMD ["/bin/bash", "prestart.sh"]
```

---

## **III. Cấu trúc dự án (Backend)**

```
auth/
rbac/
notify/
utils/
  ├── db.py
  ├── cache.py
  ├── exceptions.py
  ├── logging.py
  └── security.py
migrations/
  ├── versions/
  ├── env.py
  └── script.py.mako
main.py
config.py
prestart.sh
alembic.ini
requirements.in
requirements.txt
requirements-dev.txt
Dockerfile
docker-compose.yml
.pre-commit-config.yaml
.gitignore
README.md
```

---

## **IV. Coding Convention & Quy trình làm việc**

Dựa trên [`docs/CONTRIBUTING.md`](CONTRIBUTING.md), mọi lập trình viên nên tuân theo các nguyên tắc sau:

* **Code style:**

  * Tuân theo [PEP8](https://peps.python.org/pep-0008/)
  * Dùng `black` để format code, `flake8` để lint, `isort` để sắp xếp import
  * Sử dụng **type hinting đầy đủ** cho mọi hàm và class
  * Viết docstring theo [Google Style Guide](https://google.github.io/styleguide/pyguide.html)

* **Quy ước đặt tên:**

  * Tên file, biến, hàm: `snake_case`
  * Tên class: `PascalCase`
  * Commit message: tuân theo chuẩn [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/)

* **Workflow:**

  * Tạo branch từ `dev`: `feature/<ten-tinh-nang>` hoặc `hotfix/<ten-loi>`
  * Rebase trước khi tạo PR nếu branch đã tồn tại
  * Pull Request cần ít nhất 1 reviewer và nên **nhỏ gọn**, rõ mục tiêu
  * Review cần phản hồi trong vòng 48h

---

## **V. Testing Strategy**

Theo [ADR-019 (Contract Testing Strategy)](ADR/adr-019-contract-testing.md), chiến lược test bao gồm:

* **Unit Test:** dùng `pytest`

  * Mỗi service/module phải có test riêng trong `tests/`
  * Viết test cho edge case & logic phức tạp

* **Integration Test:**

  * Test các tương tác với DB, Redis hoặc giữa module
  * Có thể dùng fixture và test DB riêng (docker hoặc memory)

* **Contract Test:** (nếu applicable)

  * Sử dụng Pact để đảm bảo giao tiếp giữa các microservice không bị phá vỡ

* **Coverage:**

  * Mục tiêu ≥ 80%
  * Dùng `pytest-cov` để đo và xem báo cáo coverage

```bash
pytest --cov=app tests/
```

* **CI:** mọi commit/PR sẽ được CI kiểm tra tự động `lint + test`

---

## **VI. CI/CD (Continuous Integration & Deployment)**

Tóm tắt từ [ADR-003 (CICD Structure)](ADR/adr-003-ci-cd-structure.md), [ADR-010 (Deployment Strategy)](ADR/adr-010-deployment-strategy.md), và [ADR-021 (Zero Downtime Deployment)](ADR/adr-021-zero-downtime-deployment.md):

* **CI Pipeline:** GitHub Actions sẽ tự động:

  * Kiểm tra code format: `black`, `flake8`, `isort`
  * Chạy test và đo coverage bằng `pytest`
  * Scan bảo mật: `bandit`, `safety`, `trivy`

* **CD Pipeline:**

  * Tự động build Docker image và deploy lên Cloud Run cho môi trường staging
  * Môi trường production yêu cầu manual approval trước khi deploy
  * Triển khai canary hoặc blue-green được hỗ trợ (xem ADR-010 & ADR-021)

* **Hạ tầng:**

  * Quản lý bằng Terraform (xem mục VII bên dưới và ADR-023)
  * Mọi thay đổi Terraform sẽ chạy `terraform plan` và yêu cầu review trước khi apply

* **Secrets:**

  * CI sử dụng GitHub Secrets
  * Ứng dụng đọc secrets từ GCP Secret Manager

---

## **VII. Quản lý Hạ tầng bằng Terraform (IaC)**

Dự án sử dụng **Terraform** để quản lý toàn bộ hạ tầng triển khai trên Google Cloud Platform (GCP) nhằm đảm bảo:

* Có thể theo dõi và review hạ tầng như mã nguồn
* Tái sử dụng được qua modules, tách riêng các môi trường
* Triển khai an toàn, có kiểm soát và rollback được nếu cần

### **1. Cấu trúc thư mục Terraform**

Hạ tầng được đặt trong thư mục `infra/terraform/`, chia làm 2 phần:

* `modules/`: tập trung các tài nguyên có thể tái sử dụng (Cloud Run, Cloud SQL, Redis, IAM…)
* `envs/staging/` và `envs/production/`: khai báo riêng cho từng môi trường

Chi tiết được mô tả tại [ADR-023 (Infrastructure as Code Terraform Strategy)](ADR/adr-023-infrastructure-as-code-terraform-strategy.md)

### **2. Hướng dẫn cho Developer**

* **Cài Terraform:** [Tải tại đây](https://www.terraform.io/downloads) – Phiên bản ≥ 1.5
* **Chạy Terraform local (nếu được cấp quyền):**

```bash
cd infra/terraform/envs/staging
terraform init
terraform plan -var-file="staging.tfvars"
```

> ⚠️ Không chạy `terraform apply` nếu chưa có sự đồng thuận từ DevOps

* **Thay đổi hạ tầng:**

  * Tạo Pull Request với thay đổi trong `infra/terraform/`
  * Được review bởi DevOps trước khi merge vào `dev` hoặc `main`
  * CI/CD sẽ tự động chạy `terraform plan`; production yêu cầu approval trước khi apply

### **3. Quản lý state và secrets**

* Terraform **state** được lưu trữ và khóa trạng thái tự động trong Google Cloud Storage (GCS)
* Secrets KHÔNG được commit vào `.tf` hay `.tfvars` – thay vào đó:

  * Được inject qua CI (`TF_VAR_xyz`)
  * Hoặc đọc từ Google Secrets Manager thông qua Terraform provider

> IaC là một phần không thể thiếu trong quy trình DevOps hiện đại – giúp hạ tầng được kiểm soát, dễ triển khai và phục hồi.

---

## **VIII. API Design & Governance**

Dựa trên [ADR-004 (API Versioning)](./ADR/adr-004-api-versioning.md), [ADR-018 (OpenAPI Governance)](./ADR/adr-018-api-governance.md), [ADR-020 (API Lifecycle Deprecation)](./ADR/adr-020-api-lifecycle-deprecation.md), và [ADR-007 (Error Handling)](./ADR/adr-007-error-handling.md):

### **1. Thiết kế API**

* RESTful theo chuẩn HTTP verbs (`GET`, `POST`, `PUT`, `DELETE`)
* Endpoint đặt tên rõ nghĩa, dạng số nhiều: `/students`, `/roles`
* Không dùng động từ trong endpoint (đã có trong HTTP verb)

### **2. Phiên bản hóa API**

* Dùng prefix `/api/v1/...` để version rõ ràng (ADR-004)
* Không breaking changes trong cùng 1 version

### **3. OpenAPI & Tự động hóa tài liệu**

* Tài liệu endpoint sinh tự động từ FastAPI (`/docs`, `/redoc`)
* Pydantic model mô tả schema rõ ràng
* Mỗi route nên có docstring để hiển thị trong Swagger

### **4. Quản lý vòng đời API**

* Tài liệu mỗi endpoint nên ghi rõ: stable, beta, deprecated
* Deprecate cần thông báo sớm và có deadline loại bỏ (ADR-020)

### **5. Xử lý lỗi chuẩn hóa**

Mọi lỗi API phải trả về theo cấu trúc chuẩn theo [ADR-007 (Error Handling)](./ADR/adr-007-error-handling.md):

```json
{
  "error_code": 403,
  "message": "Permission denied",
  "details": "Permission 'EDIT_STUDENT' is required",
  "request_id": "abc-123",
  "timestamp": "2025-05-21T08:30:00Z"
}
```

* `error_code`: mã HTTP status (400, 403, 404, 500...)
* `message`: thông báo ngắn gọn cho client
* `details`: mô tả rõ hơn (optional)
* `request_id`: ID duy nhất giúp debug truy vết lỗi
* `timestamp`: thời điểm xảy ra lỗi (UTC ISO format)

> 📘 Thiết kế API tốt là nền tảng cho frontend, tích hợp hệ thống và mở rộng trong tương lai.

## **IX. Resilience, Caching & Performance**

Dựa trên [ADR-016 (Resilience Fallback Strategy)](./ADR/adr-016-resilience-fallback-strategy.md) và [ADR-017 (Caching Strategy)](./ADR/adr-017-caching-strategy.md):

### **1. Timeout & Retry**

* Thiết lập timeout rõ ràng cho mọi external call
* Dùng retry với backoff cho các request idempotent (như GET)
* Tăng độ ổn định hệ thống khi backend tạm thời lỗi hoặc chậm

### **2. Circuit Breaker (Tuỳ chọn nâng cao)**

* Có thể dùng thư viện `tenacity` hoặc custom logic khi cần cách ly lỗi
* Nếu 1 backend liên tục lỗi, tạm thời dừng gửi request trong 1 khoảng thời gian

### **3. Caching**

* Dữ liệu ít thay đổi nên cache tại API Gateway hoặc Redis
* Caching phân tầng:

  * In-memory (tuổi thọ ngắn, dùng cho response tạm thời)
  * Redis (chia sẻ giữa instances)
* Cache key nên bao gồm đầy đủ các param ảnh hưởng đến nội dung

### **4. Tối ưu hoá truy vấn**

* Tránh N+1 query với SQLAlchemy bằng cách dùng `selectinload`, `joinedload`
* Giới hạn size dữ liệu trả về bằng `limit`, `offset`, `pagination`

> ⚡ Tối ưu hiệu năng & độ ổn định là yếu tố sống còn khi hệ thống phát triển quy mô lớn

## **X. Multi-Environment Configuration**

Dựa trên [ADR-014 (Multi-Environment Config)](ADR/adr-014-multi-env-config.md):

### **1. .env và biến môi trường**

* Mỗi môi trường (`local`, `staging`, `production`) có file `.env` riêng
* Cấu hình như DB\_URL, REDIS\_URL, JWT\_SECRET được định nghĩa dưới dạng biến môi trường

### **2. Load cấu hình động trong code**

* Sử dụng thư viện như `pydantic-settings` hoặc custom config loader
* Phân biệt rõ các cấu hình `dev`, `prod`, `test` trong `config.py`

### **3. Terraform tách riêng theo env**

* `infra/terraform/envs/staging/`, `envs/production/` chứa config riêng biệt
* Mỗi môi trường có state file riêng (tránh đè nhau)

> 🧭 Đa môi trường giúp đảm bảo CI/CD linh hoạt, rollback dễ dàng, và tách biệt rủi ro rõ ràng

## **XI. Database Migrations & Alembic**

### **1. Alembic**

* Dùng để quản lý schema migration cho PostgreSQL
* Cấu hình trong `alembic.ini`, logic trong `migrations/`

### **2. Tạo và áp dụng migration**

```bash
alembic revision --autogenerate -m "Add table xyz"
alembic upgrade head
```

* Mỗi PR nên đi kèm migration nếu có thay đổi DB schema

### **3. Không downtime**

* Luôn kiểm tra kỹ migration để tránh `DROP`, `ALTER` gây lock table
* Nếu thay đổi lớn, nên chia nhỏ thành các bước an toàn (xem ADR-021)

> 🗃️ Migrations an toàn là điều kiện bắt buộc cho deploy tự động trong môi trường production\*\*

## **XII. Observability (Logging, Metrics, Tracing, Audit, Cost)**

Dựa trên [ADR-005 (Observability Strategy)](ADR/adr-005-observability.md), [ADR-012 (Audit Logging)](ADR/adr-012-audit-logging.md), [ADR-022 (3rd-Party Observability)](ADR/adr-022-observability-third-party.md), và [ADR-015 (Cost Observability)](ADR/adr-015-cost-observability.md):

### **1. Logging**

* Sử dụng structured logging với `python-json-logger`
* Logs cần có: `request_id`, `user_id`, `path`, `status_code`
* Gửi logs lên Cloud Logging với phân loại rõ ràng (`INFO`, `WARNING`, `ERROR`)

### **2. Metrics**

* Thu thập qua OpenTelemetry SDK → GCP Monitoring
* Theo dõi: latency, error rate, số lượng request theo endpoint/module

### **3. Distributed Tracing**

* Header: `X-Request-ID`, `traceparent`,... truyền giữa các service
* Sử dụng GCP Trace hoặc Jaeger nếu cần

### **4. Audit Logging**

* Ghi log cho thao tác nhạy cảm: login, phân quyền, cập nhật dữ liệu
* Trường bắt buộc: `actor_id`, `action`, `target_id`, `timestamp`, `ip_address`
* Lưu riêng, không bị xóa hoặc sửa

### **5. Cost Observability**

* Gắn label cho mọi resource tạo ra: `project`, `team`, `env`
* Theo dõi chi phí theo team/module qua Billing Dashboard

> 🔍 Observability không chỉ là thu thập – mà là khả năng hiểu **điều gì đang xảy ra** để phản ứng đúng lúc.

## **XIII. Security Best Practices**
Dựa trên [ADR-009 (Security Hardening)](ADR/adr-009-security-hardening.md), [ADR-011 (Secrets Rotation)](ADR/adr-011-secrets-rotation.md), và các chiến lược tổng hợp:

### **1. Transport & Token Security**
* Chỉ dùng HTTPS (Cloud Run mặc định)
* JWT: TTL ngắn, dùng Authorization: Bearer <token>, lưu ở memory

### **2. Input Validation**
* Validate kỹ mọi đầu vào bằng Pydantic
* Từ chối request quá lớn, sai Content-Type

### **3. HTTP Headers**
* Thêm HSTS, X-Frame-Options, CSP, Referrer-Policy

### **4. Rate Limiting**
* Sử dụng Redis hoặc GCP Cloud Armor
* [ADR-008 (Rate-Limiting)](ADR/adr-008-rate-limiting.md) mô tả rõ

### **5. Dependency & Image Scanning**
* Sử dụng safety, bandit trong CI
* Scan Docker image với trivy

### **6. Secrets Management**
* Tuyệt đối không lưu secrets trong Git
* Sử dụng GCP Secret Manager + Terraform để inject
* Thay secret định kỳ (rotation theo ADR-011)

> 🛡️ Bảo mật không phải là tính năng – mà là yêu cầu nền tảng. Mỗi dòng code cần được viết với tư duy bảo vệ người dùng và dữ liệu.

> 📘 Tài liệu này cần được cập nhật liên tục khi các ADR hoặc hệ thống thay đổi. Hãy đảm bảo bạn theo dõi repo để nắm các cập nhật mới nhất!

