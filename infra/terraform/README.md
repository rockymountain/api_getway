# 🛠️ Terraform Infrastructure – DX VAS

> Repository con hoặc thư mục `infra/terraform/` trong hệ thống API Gateway dự án **Chuyển đổi số VAS**. Dùng để triển khai hạ tầng GCP bằng mã nguồn (Infrastructure as Code – IaC) với **Terraform**.

---

## 📁 Cấu trúc thư mục

```bash
infra/terraform/
├── modules/                 # Các module tái sử dụng được
│   ├── cloud_run_service/
│   ├── cloud_sql_instance/
│   ├── redis_instance/
│   ├── iam/
│   └── monitoring/
│
├── envs/                   # Tách cấu hình theo môi trường
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
├── backend.tf              # (Tùy chọn) cấu hình backend chung nếu dùng workspace
└── README.md               # Tài liệu này
```

> 📌 Mỗi môi trường nên có khai báo `backend "gcs"` riêng trong `main.tf` để tách biệt state rõ ràng. Tránh dùng workspace nếu team chưa quen.

---

## 🧪 Yêu cầu cài đặt

* [Terraform >= 1.5](https://www.terraform.io/downloads)
* GCP IAM Service Account với quyền tối thiểu cần thiết:

  * `roles/cloudrun.admin`
  * `roles/cloudsql.admin`
  * `roles/iam.serviceAccountUser`
  * `roles/redis.admin`
  * `roles/monitoring.editor`
  * `roles/storage.admin` (cho state backend bucket)

> ⚠️ Tránh cấp `roles/editor`. Áp dụng **Principle of Least Privilege**.

---

## 🚀 Cách sử dụng

### 1. Thiết lập môi trường (ví dụ: staging)

```bash
cd infra/terraform/envs/staging
terraform init
terraform plan -var-file="staging.tfvars" -out=plan.tfplan
terraform apply plan.tfplan
```

> 🔒 `terraform init` sẽ tự đọc backend block từ `main.tf`. Không cần dùng `-backend-config` nếu đã khai báo đúng.

### 2. Ví dụ gọi module trong `main.tf`

```hcl
module "api_gateway_staging_service" {
  source        = "../../modules/cloud_run_service"
  project_id    = var.project_id
  service_name  = "api-gateway-staging"
  image         = var.docker_image_staging
  env_vars      = var.staging_env_vars
}
```

---

## ⚙️ CI/CD đề xuất

* Pull Request:

  * `terraform fmt`, `validate`, `plan`
  * Lưu file `.tfplan` làm artifact
* `apply`:

  * Tự động cho staging
  * Production cần **manual approval** hoặc trigger riêng
* Gợi ý dùng \[OPA + Sentinel (Terraform Cloud)] để enforce policy nếu cần kiểm soát cao

---

## 🔐 Bảo mật & quản lý secrets

* **Không commit secrets** trong bất kỳ `.tf` hay `.tfvars`
* Secrets được cung cấp qua:

  * GitHub Secrets → biến môi trường: `TF_VAR_db_password=...`
  * GCP Secrets Manager (qua module hoặc provider)
  * Terraform Cloud Variable Store (nếu dùng)

---

## 🧠 Quản lý Terraform State

* Dùng backend `gcs` với `bucket` riêng và `prefix` theo env:

```hcl
terraform {
  backend "gcs" {
    bucket  = "tf-state-vas"
    prefix  = "terraform/state/api-gateway/staging"
  }
}
```

* GCS hỗ trợ **state locking**, tránh conflict khi apply song song

---

## 📌 Tài liệu liên quan

* [ADR-023 – Chiến lược Terraform IaC](../docs/ADR/ADR-023-Infrastructure-as-Code-Terraform-Strategy.md)
* [Terraform Docs](https://developer.hashicorp.com/terraform/docs)
* [GCP Terraform Provider](https://registry.terraform.io/providers/hashicorp/google/latest/docs)
* [Best Practices – Terraform GCP](https://cloud.google.com/docs/terraform/best-practices)

---

> ☁️ “Hạ tầng không chỉ là tài nguyên – nó là **code có thể review, test và triển khai an toàn**.”
