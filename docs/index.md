# 👋 Chào mừng đến với Tài liệu API Gateway – Dự án Chuyển đổi số VAS

---

Dự án **API Gateway – DX VAS** là thành phần trung tâm trong nền tảng chuyển đổi số của hệ thống VAS, đóng vai trò làm cầu nối an toàn, nhất quán giữa frontend, backend và các dịch vụ bên ngoài.

📚 Đây là cổng tài liệu kỹ thuật chính thức dành cho:

- Developer backend, frontend hoặc mobile
- DevOps, SRE và QA
- Người mới tham gia dự án (onboarding)
- Kiểm tra và bảo trì hạ tầng

---

## 📖 Nội dung chính

| Mục | Mô tả |
|-----|------|
| 🚀 [Hướng dẫn Dev](DEV_GUIDE.md) | Tài liệu "From 0 to Hero" để lập trình viên triển khai và hiểu toàn bộ hệ thống |
| 🤝 [Quy trình làm việc](CONTRIBUTING.md) | Quy ước code, review, PR, branch, naming |
| 🧠 [Kiến trúc hệ thống & ADRs](ADR/adr-001-fastapi.md) | Các quyết định kiến trúc được ghi lại chính thức |
| 📚 [API Reference](API_REFERENCE.md) | Tham chiếu các endpoint của API Gateway |
| 👥 [Onboarding & Offboarding](ONBOARDING.md) | Checklist cho người mới và khi rời team |

---

## 🧠 Về kiến trúc tổng thể

- API Gateway sử dụng **FastAPI** và triển khai qua **Google Cloud Run**
- Quản lý hạ tầng với **Terraform**
- CI/CD sử dụng **GitHub Actions**
- Logging, metrics, và tracing theo chuẩn **Observability 3 Pillars**
- Security theo hướng **Zero Trust + RBAC + Secret Rotation**

📌 Các quyết định kiến trúc được ghi lại dưới dạng [ADR (Architecture Decision Records)](ADR/adr-001-fastapi.md)

---

## 📈 Đóng góp

Bạn muốn cải thiện tài liệu này?  
Hãy xem [hướng dẫn đóng góp](CONTRIBUTING.md) hoặc tạo Pull Request.

_“Code tốt là khi team hiểu được, tài liệu tốt là khi người mới không phải hỏi lại.”_

---

