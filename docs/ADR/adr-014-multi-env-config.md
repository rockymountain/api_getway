# ADR-014: Chiến lược cấu hình đa môi trường (Multi-Environment Configuration) cho API Gateway (DX VAS)

* **Trạng thái**: Đã chấp thuận ✅
* **Ngày**: 28/05/2025
* **Người đề xuất**: Nguyễn Thị D (DevOps)
* **Bối cảnh**: Dự án Chuyển đổi số VAS

---

## 📌 Bối cảnh

API Gateway cần hoạt động ổn định trên nhiều môi trường khác nhau (dev, staging, production) với cấu hình phù hợp từng mục đích. Các thông số như endpoint backend, biến môi trường, database URL, JWT key, logging level... sẽ khác nhau giữa các môi trường.

Việc quản lý cấu hình đa môi trường cần:

* Tách biệt rõ cấu hình từng môi trường
* Không hard-code giá trị theo môi trường vào mã nguồn
* Dễ tích hợp với CI/CD, Cloud Run, và Terraform

---

## 🧠 Quyết định

**Áp dụng chiến lược cấu hình đa môi trường bằng cách phân tách cấu hình theo profile (env), sử dụng biến môi trường và secrets được inject thông qua GitHub Actions, Google Secret Manager hoặc Terraform khi deploy lên Cloud Run.**

---

## 🛠 Thiết kế

### 1. Cấu trúc thư mục cấu hình (cho local dev và CI build-time)

```bash
/config
  ├── base.env
  ├── dev.env
  ├── staging.env
  └── prod.env
```

* `base.env`: cấu hình mặc định dùng chung
* `*.env`: override theo từng môi trường cụ thể
* Các file `.env` này **không được build vào Docker image**, chỉ dùng để hỗ trợ local development hoặc để CI/CD pipeline load và inject chính xác biến môi trường khi deploy

### 2. Biến môi trường quan trọng

| Key                   | Mô tả                             |
| --------------------- | --------------------------------- |
| ENV                   | dev / staging / prod              |
| LOG\_LEVEL            | debug / info / warning            |
| BACKEND\_URL\_SIS     | URL kết nối tới SIS service       |
| JWT\_SECRET           | Secret dùng để ký JWT             |
| RATE\_LIMIT\_PER\_MIN | Số request cho phép / user / phút |

### 3. Cách nạp cấu hình

* App sử dụng thư viện như `pydantic-settings` hoặc `python-dotenv`
* Thứ tự ưu tiên cấu hình:

  1. Biến môi trường hệ thống (Cloud Run inject hoặc Terraform inject)
  2. File `.env` nếu có (dành cho local dev)
  3. Giá trị mặc định trong code (base config)
* Khi deploy lên Cloud Run:

  * Biến môi trường được inject qua GitHub Actions, `gcloud run deploy`, hoặc **Terraform** (preferred để đảm bảo IaC)
  * Secrets như `JWT_SECRET`, `DB_PASSWORD` được inject từ Google Secret Manager, theo môi trường tương ứng

### 4. Tích hợp CI/CD

* Workflow GitHub Actions xác định môi trường qua branch hoặc tag:

  * `dev` → `ENV=dev`
  * `main` → `ENV=prod`
* Pipeline đọc `.env` tương ứng (chỉ chứa non-secret) hoặc inject biến trực tiếp
* Secrets staging/prod không được log hoặc output ra artifact

### 5. Kiểm soát cấu hình an toàn

* Validate cấu hình bằng schema (`pydantic.BaseSettings`)
* Secrets không được lưu trong `.env`, dùng placeholder như `JWT_SECRET=__INJECTED__`
* IAM của Secret Manager tách riêng theo môi trường

### 6. Quy ước phân biệt hành vi theo môi trường

* Debug tool, OpenAPI docs chỉ bật nếu `ENV != prod`
* Logging:

  * `dev`: log đầy đủ `debug`
  * `prod`: chỉ log `warning` trở lên
* CORS:

  * `dev`: `*`
  * `prod/staging`: chỉ cho phép domain cụ thể

---

## ✅ Lợi ích

* Cấu hình rõ ràng, dễ kiểm soát theo từng môi trường
* Không phụ thuộc code branch logic phức tạp
* Secrets được tách biệt và quản lý an toàn
* CI/CD dễ triển khai, không rò rỉ giá trị nhạy cảm

---

## ❌ Rủi ro & Giải pháp

| Rủi ro                          | Giải pháp                                                                          |
| ------------------------------- | ---------------------------------------------------------------------------------- |
| Nhầm biến môi trường khi deploy | CI/CD log rõ `ENV`, đặt tag revision rõ ràng (vd: `vas-api-gw:staging-2025-05-28`) |
| Secrets sai môi trường          | Tách Secret theo môi trường, phân quyền IAM rõ ràng                                |
| `.env` bị commit nhầm           | `.gitignore`, CI hook + scan check trước khi merge                                 |

---

## 🔄 Các lựa chọn đã loại bỏ

* **Hard-code cấu hình trong mã nguồn**: Không audit được, khó maintain
* **Dùng chung secret cho mọi môi trường**: Rất rủi ro, xoay vòng không linh hoạt
* **Chỉ dùng GitHub Secrets cho mọi biến**: Không đủ cho runtime, khó phân quyền chi tiết

---

## 📎 Tài liệu liên quan

* Cấu hình base: [`config/base.env`](../../config/base.env)
* Dev Guide – Configuration section: [`DEV_GUIDE.md`](../DEV_GUIDE.md)
* ADR liên quan: [`adr-011-secrets-rotation.md`](./adr-011-secrets-rotation.md)

---

> “Một môi trường, một cấu hình – tách biệt rõ ràng để vận hành an toàn.”
