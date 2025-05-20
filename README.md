# API Gateway – Dự án Chuyển đổi số VAS

[![Build Status](https://github.com/vas-org/api-gateway/actions/workflows/ci.yml/badge.svg)](https://github.com/vas-org/api-gateway/actions/workflows/ci.yml)
[![Coverage Status](https://coveralls.io/repos/github/vas-org/api-gateway/badge.svg?branch=main)](https://coveralls.io/github/vas-org/api-gateway?branch=main)
[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)

Hệ thống API Gateway xây dựng bằng **FastAPI**, triển khai trên **Google Cloud Run**, đóng vai trò trung tâm xác thực, phân quyền RBAC, định tuyến backend và ghi log toàn bộ lưu lượng frontend/backend.

> 💡 Đây là phiên bản "From 0 to Hero" – đầy đủ quy trình Dev + CI/CD + IaC + Monitoring + Security + Dev Culture.

---

## 🚀 Mục tiêu

* Làm điểm truy cập duy nhất cho toàn bộ frontend (PWA, SPA)
* Kiểm tra xác thực Google OAuth2, phân quyền động RBAC
* Gửi log và metrics lên Cloud Logging / Monitoring
* Quản lý và deploy bằng CI/CD & Infrastructure as Code

---

## 📁 Cấu trúc thư mục dự án

<details>
<summary>Hiển thị cây thư mục đầy đủ</summary>

```bash
api-gateway/
├── .env.example
├── .gitignore
├── .pre-commit-config.yaml
├── README.md
├── config.py
├── main.py
├── requirements.in
├── requirements.txt
├── requirements-dev.txt
├── Dockerfile
├── docker-compose.yml
├── prestart.sh
│
├── auth/
│   ├── router.py
│   ├── services.py
│   ├── schemas.py
│   └── models.py
│
├── rbac/
│   ├── router.py
│   ├── services.py
│   ├── schemas.py
│   └── models.py
│
├── notify/
│   ├── router.py
│   ├── services.py
│   └── schemas.py
│
├── utils/
│   ├── logging.py
│   ├── exceptions.py
│   ├── security.py
│   ├── db.py
│   └── cache.py
│
├── tests/
│   ├── test_auth.py
│   ├── test_rbac.py
│   ├── test_notify.py
│   ├── conftest.py
│   └── __init__.py
│
├── ci/
│   ├── build-docker.sh
│   ├── deploy-cloudrun.sh
│   ├── bandit.yaml
│   └── trivy.yaml
│
├── .github/
│   └── workflows/
│       └── ci.yml
│
├── infra/
│   └── terraform/
│       ├── main.tf
│       ├── cloudrun.tf
│       ├── sql.tf
│       ├── redis.tf
│       ├── iam.tf
│       ├── variables.tf
│       └── outputs.tf
│
├── otel/
│   ├── otel-config.yaml
│   ├── metrics.py
│   ├── tracing.py
│   └── exporters/
│       └── logging.py
│
├── alerting/
│   ├── latency_alert.json
│   └── error_rate_alert.json
│
├── docs/
│   ├── DEV_GUIDE.md
│   ├── API_REFERENCE.md
│   ├── ONBOARDING.md
│   ├── OFFBOARDING.md
│   ├── CONTRIBUTING.md
│   └── ADR/
│       ├── adr-001-fastapi.md
│       └── adr-002-rbac-design.md
```

</details>

---

## 🛠️ Thiết lập nhanh (Local Development)

**Điều kiện tiên quyết:**

* [Git](https://git-scm.com/)
* [Python 3.10+](https://www.python.org/)
* [Docker & Docker Compose](https://www.docker.com/products/docker-desktop)
* (Tùy chọn) `pip` để cài `pre-commit` nếu chưa có

**Các bước thực hiện:**

```bash
git clone https://github.com/vas-org/api-gateway.git
cd api-gateway
cp .env.example .env

pip install pre-commit
pre-commit install

docker-compose up --build
```

* Truy cập: [http://localhost:8000/docs](http://localhost:8000/docs)
* Test: `pytest`
* Lint: `black`, `flake8`, `isort`

---

## ✅ Triển khai CI/CD & Infrastructure as Code

* Branch `dev` → Staging | Branch `main` → Production
* Sử dụng GitHub Actions: `.github/workflows/ci.yml` cho việc build, test, và deploy ứng dụng API Gateway.
* **Hạ tầng được định nghĩa và quản lý bằng Terraform (Infrastructure as Code)**, bao gồm các tài nguyên Google Cloud Platform như Cloud Run services, Cloud SQL instances, Redis instances, IAM roles, và các cấu hình liên quan.

  * Mã Terraform được tổ chức trong thư mục `infra/terraform/` với các modules và cấu hình riêng cho từng môi trường (chi tiết trong [`docs/ADR/adr-023-infrastructure-as-code-terraform-strategy.md`](./docs/ADR/adr-023-infrastructure-as-code-terraform-strategy.md)).
  * Các thay đổi về hạ tầng được áp dụng thông qua pipeline CI/CD chuyên biệt cho Terraform, bao gồm các bước `plan` (với review cho production) và `apply`.
  * State file của Terraform được lưu trữ an toàn trên Google Cloud Storage.
* Secrets ứng dụng (`DB_URL`, `REDIS_URL`, `JWT_SECRET_KEY`, ...) được quản lý bởi Google Secret Manager và inject vào Cloud Run services thông qua cấu hình Terraform. Secrets cho CI/CD (ví dụ: `WIF_PROVIDER`, `WIF_SERVICE_ACCOUNT` cho GitHub Actions) được lưu trong GitHub Secrets.
* (Tùy chọn) Truy cập staging: [https://api-stg.truongvietanh.edu.vn](https://api-stg.truongvietanh.edu.vn)

---

## 📊 Monitoring & Security

* Logging: structured JSON logs (`python-json-logger`)
* Metrics: custom metrics đẩy lên Cloud Monitoring
* Alert: latency, error rate, resource usage
* Security scan: Bandit, Safety, Trivy trong CI

---

## 📚 Tài liệu dành cho Dev

* `docs/DEV_GUIDE.md`: hướng dẫn đầy đủ “From 0 to Hero”
* `docs/ONBOARDING.md`: checklist dev mới
* `docs/OFFBOARDING.md`: checklist nghỉ dự án
* `docs/API_REFERENCE.md`: tài liệu endpoint (auto-gen). *Lưu ý: Cần có kế hoạch để tài liệu này được tự động tạo hoặc đồng bộ từ OpenAPI specification (theo ADR-018) thay vì tổng hợp thủ công để đảm bảo tính chính xác và cập nhật.*
* `docs/ADR/`: Các quyết định kiến trúc quan trọng (Architecture Decision Records)

---

## 🤝 Đóng góp

Chúng tôi luôn chào đón sự đóng góp! Vui lòng xem qua [hướng dẫn đóng góp (`docs/CONTRIBUTING.md`)](./docs/CONTRIBUTING.md) để biết thêm chi tiết về quy trình làm việc, coding convention và cách tạo Pull Request.

## ✨ Bản quyền & Giấy phép

© Trường Việt Anh – DX VAS Project 2025. Mọi quyền được bảo lưu. Mã nguồn dành riêng cho mục đích nội bộ và đào tạo.

---

> Made with ❤️ by the Legendary DevOps & Backend Team @ VAS
