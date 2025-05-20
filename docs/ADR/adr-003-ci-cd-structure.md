# ADR-003: Cấu trúc CI/CD cho API Gateway (DX VAS)

* **Trạng thái**: Đã chấp thuận ✅
* **Ngày**: 17/05/2025
* **Người đề xuất**: Lê Văn C (DevOps)
* **Bối cảnh**: Dự án Chuyển đổi số VAS

---

## 📌 Bối cảnh

Hệ thống API Gateway cần được triển khai trên Google Cloud Run, đảm bảo các yêu cầu:

* Triển khai tự động (Continuous Deployment) từ GitHub
* Kiểm tra chất lượng code: lint, test, security scan trước khi deploy
* Có môi trường `staging` và `production` tách biệt
* Dễ dàng rollback khi cần

Công cụ được lựa chọn: **GitHub Actions** làm CI/CD runner chính.

---

## 🧠 Quyết định

**Áp dụng cấu trúc CI/CD sử dụng GitHub Actions với 2 pipeline chính:**

* `dev` → Deploy lên Staging
* `main` → Deploy lên Production

---

## 🛠 Cấu trúc pipeline đề xuất

```yaml
name: CI/CD Pipeline

on:
  push:
    branches: [dev, main]

env:
  PROJECT_ID: truongvietanh-dev
  REGION: asia-southeast1
  SERVICE_NAME: api-gateway

jobs:
  build-and-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'

      - name: Cache dependencies
        uses: actions/cache@v3
        with:
          path: ~/.cache/pip
          key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements.txt') }}

      - name: Install deps & run checks
        run: |
          pip install -r requirements.txt
          pip install -r requirements-dev.txt
          pre-commit run --all-files
          pytest --cov
          bandit -r .
          safety check

      - name: Build Docker image
        run: |
          docker build -t gcr.io/${{ env.PROJECT_ID }}/${{ env.SERVICE_NAME }}:${{ github.sha }} .

  deploy-staging:
    if: github.ref == 'refs/heads/dev'
    needs: build-and-test
    runs-on: ubuntu-latest
    steps:
      - name: Authenticate to GCP
        uses: google-github-actions/auth@v1
        with:
          workload_identity_provider: ${{ secrets.WIF_PROVIDER }}
          service_account: ${{ secrets.WIF_SERVICE_ACCOUNT }}

      - name: Deploy to Cloud Run (staging)
        uses: google-github-actions/deploy-cloudrun@v1
        with:
          service: api-gateway-stg
          image: gcr.io/${{ env.PROJECT_ID }}/${{ env.SERVICE_NAME }}:${{ github.sha }}
          region: ${{ env.REGION }}

  deploy-production:
    if: github.ref == 'refs/heads/main'
    needs: build-and-test
    runs-on: ubuntu-latest
    steps:
      - name: Authenticate to GCP
        uses: google-github-actions/auth@v1
        with:
          workload_identity_provider: ${{ secrets.WIF_PROVIDER }}
          service_account: ${{ secrets.WIF_SERVICE_ACCOUNT }}

      - name: Deploy to Cloud Run (prod)
        uses: google-github-actions/deploy-cloudrun@v1
        with:
          service: api-gateway
          image: gcr.io/${{ env.PROJECT_ID }}/${{ env.SERVICE_NAME }}:${{ github.sha }}
          region: ${{ env.REGION }}
```

---

## ✅ Thành phần chính

| Thành phần    | Công cụ / Gợi ý                                                                                                                                                     |
| ------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Runner        | GitHub Actions (`.github/workflows/ci.yml`)                                                                                                                         |
| Container     | Dockerfile chuẩn hóa, tag image bằng SHA (`gcr.io/project/api-gateway:$GITHUB_SHA`)                                                                                 |
| Deploy        | Dùng `google-github-actions/deploy-cloudrun` + [Workload Identity Federation](https://cloud.google.com/iam/docs/workload-identity-federation) (không cần file JSON) |
| Secrets       | Lưu trong GitHub Secrets: `WIF_PROVIDER`, `WIF_SERVICE_ACCOUNT`, `DB_URL`, ...                                                                                      |
| Rollback      | Dùng `gcloud run revisions list` để revert phiên bản trước                                                                                                          |
| Observability | Cloud Logging, Monitoring, Alert nếu lỗi >5% trong 5 phút                                                                                                           |

---

## ✨ Lợi ích

* **Liên tục**: Mỗi push lên `dev` hoặc `main` đều tự động build/test/deploy
* **An toàn**: Luôn kiểm tra lint + test + scan trước khi deploy
* **Tách biệt**: `staging` dùng service riêng (`api-gateway-stg`) và domain phụ (`api-stg.truongvietanh.edu.vn`)
* **Dễ rollback**: Dựa vào revision Cloud Run
* **Giám sát tốt**: Ghi log + alert bằng Cloud Monitoring
* **Không cần lưu key file**: Sử dụng Workload Identity Federation thay vì JSON key

---

## ❌ Rủi ro & Giải pháp

| Rủi ro                                   | Giải pháp                                                                               |
| ---------------------------------------- | --------------------------------------------------------------------------------------- |
| Build sai do code chưa đủ test           | Bắt buộc test coverage ≥ 80% + chạy pytest trong CI                                     |
| Secrets bị lộ                            | Dùng Workload Identity Federation thay vì key file; không commit bất kỳ biến bí mật nào |
| Deploy trễ vì lỗi nhỏ (lint, formatting) | Dùng pre-commit hook để bắt sớm tại local                                               |

---

## 🔄 Các lựa chọn đã loại bỏ

* **Jenkins**: Quá nặng, không cần tự host
* **GitLab CI**: Dự án đang nằm trên GitHub, không phù hợp
* **Cloud Build độc lập**: Khó kiểm soát version/lifecycle PR như GitHub Actions

---

## 📎 Tài liệu liên quan

* Dockerfile: [`/Dockerfile`](../../Dockerfile)
* CI workflow: [`.github/workflows/ci.yml`](../../.github/workflows/ci.yml)
* Dev Guide CI/CD section: [`DEV_GUIDE.md`](../DEV_GUIDE.md)
* ADR trước: [`adr-002-rbac-design.md`](./adr-002-rbac-design.md)

---

> “Mỗi lần push là một lần tin tưởng – hãy để CI đảm bảo bạn xứng đáng.”
