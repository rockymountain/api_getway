# ADR-023: Hạ tầng dưới dạng mã nguồn (IaC) – Chiến lược dùng Terraform

**Trạng thái:** Đã chấp thuận
**Ngày:** 2025-05-18
**Người đề xuất:** DevOps Team – DX VAS

---

## 🎯 Bối cảnh

Hệ thống API Gateway và các dịch vụ liên quan của dự án Chuyển đổi số VAS đang được triển khai trên nền tảng **Google Cloud Platform (GCP)**.

Chúng tôi muốn đảm bảo rằng việc quản lý hạ tầng được:

* **Lặp lại được** (reproducible)
* **Dễ theo dõi thay đổi** (trackable in Git)
* **Tự động hóa & kiểm thử được** (testable in CI/CD)
* **Chia sẻ dễ dàng giữa các môi trường (staging/production)**

Hiện tại, hạ tầng gồm các thành phần chính:

* Google Cloud Run (triển khai container)
* Cloud SQL (PostgreSQL)
* Redis Instance (Memory Store)
* IAM Roles và Service Accounts
* Cloud Logging & Monitoring

---

## 💡 Quyết định

Chúng tôi quyết định sử dụng **Terraform** làm công cụ chính cho quản lý hạ tầng, với các đặc điểm sau:

### 🧱 Cấu trúc thư mục Terraform đề xuất

```bash
infra/terraform/
├── modules/
│   ├── cloud_run_service/
│   ├── cloud_sql_instance/
│   ├── redis_instance/
│   ├── iam/
│   └── monitoring/
│
├── envs/
│   ├── staging/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   ├── outputs.tf
│   │   └── staging.tfvars
│   └── production/
│       ├── main.tf
│       ├── variables.tf
│       ├── outputs.tf
│       └── production.tfvars
│
├── backend.tf  # cấu hình backend chung hoặc riêng cho từng env
└── README.md   # hướng dẫn chạy và cấu trúc
```

> 🧩 **Modules** giúp tái sử dụng & chuẩn hóa resource lặp lại. Mỗi môi trường staging/production chỉ cần gọi các module này và truyền biến phù hợp.

### ⚙️ Chiến lược sử dụng

* **State file**: lưu trữ trên GCS bucket, bật versioning và encryption
* **Environment separation**:

  * Dùng `envs/staging/` và `envs/production/` để tách toàn bộ cấu hình và state
  * Mỗi env có thể có backend riêng hoặc dùng workspace nếu muốn đơn giản hơn
* **Secrets**: không hardcode. Được inject qua CI/CD hoặc từ GCP Secrets Manager
* **Terraform Cloud** (nâng cao): dùng để enforce policy, approve production apply

---

## ✅ Ưu điểm

* Dễ dàng nhân bản môi trường mới (test, staging)
* Review hạ tầng như review code
* Quản lý lifecycle của resource (tạo, cập nhật, xóa)
* Chuẩn hoá việc gán quyền IAM và bảo mật
* Dễ dàng mở rộng và tích hợp với hệ thống giám sát (monitoring)

---

## 🔁 Các phương án khác đã cân nhắc

| Giải pháp                       | Lý do không chọn                                                          |
| ------------------------------- | ------------------------------------------------------------------------- |
| GCP Console thủ công            | Không lặp lại được, dễ sai lệch giữa môi trường                           |
| Google Cloud Deployment Manager | Ít phổ biến, tài liệu hạn chế hơn Terraform                               |
| Pulumi                          | Mạnh nhưng cần học thêm TypeScript/Python SDK, ít phổ biến hơn trong team |

---

## 📌 Hành động tiếp theo

* [ ] Khởi tạo repo `infra/terraform/`
* [ ] Thiết lập GCS bucket làm remote state backend (riêng cho staging và production)
* [ ] Viết các module chuẩn hóa cho: Cloud Run, Cloud SQL, Redis, IAM, Monitoring
* [ ] Thiết lập môi trường `staging` và `production` trong thư mục `envs/`
* [ ] Viết script CI/CD:

  * `terraform validate`
  * `terraform plan` + lưu file `.tfplan` dưới dạng artifact
  * `terraform apply` tự động cho staging, manual approval cho production
* [ ] Áp dụng chính sách review bắt buộc trước khi apply lên production
* [ ] (Tùy chọn) Tích hợp Policy as Code (OPA) để enforce quy định nội bộ trước khi apply

---

> Quyết định này giúp chuẩn hoá hạ tầng của hệ thống, đảm bảo an toàn – và quan trọng hơn, biến nó thành **một phần của quy trình phát triển phần mềm hiện đại**.
