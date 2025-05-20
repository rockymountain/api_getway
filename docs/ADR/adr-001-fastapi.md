# ADR-001: Chọn FastAPI làm framework cho API Gateway

* **Trạng thái**: Đã chấp thuận ✅
* **Ngày**: 15/05/2025
* **Người đề xuất**: Nguyễn Văn A
* **Bối cảnh**: Dự án Chuyển đổi số VAS

---

## 📌 Bối cảnh

Dự án DX VAS yêu cầu xây dựng một API Gateway:

* Làm điểm truy cập duy nhất cho các frontend (PWA, SPA).
* Kiểm tra xác thực OAuth2, phân quyền RBAC động.
* Gửi log, monitor, forward request đến các backend như SIS, CRM, LMS.
* Có thể mở rộng, bảo trì tốt và hiệu suất cao.

Các framework Python phổ biến được xem xét:

* Flask
* FastAPI
* Django Rest Framework
* Tornado

---

## 🧠 Quyết định

**Chúng tôi chọn sử dụng [FastAPI](https://fastapi.tiangolo.com/) làm framework chính cho API Gateway.**

---

## ✅ Lý do chính

| Tiêu chí                 | FastAPI                      | Lý do                                              |
| ------------------------ | ---------------------------- | -------------------------------------------------- |
| Hiệu suất                | ✅ Rất cao (ASGI + Starlette) | Đáp ứng nhu cầu forward nhanh và concurrency       |
| Kiểu tĩnh + type hinting | ✅ Rõ ràng                    | Tối ưu autocomplete, dễ debug                      |
| Docs tự động             | ✅ Có                         | Swagger + ReDoc sinh tự động, hỗ trợ frontend & QA |
| Cộng đồng                | Đang phát triển mạnh         | Nhiều thư viện hỗ trợ, tài liệu rõ ràng            |
| Tích hợp async           | ✅ Tốt                        | Dễ kết hợp httpx, aioRedis, asyncpg                |
| Học nhanh                | ✅ Dễ tiếp cận                | Ngắn gọn, gần với Flask style                      |

---

## ❌ Đánh đổi / Rủi ro

* Cộng đồng nhỏ hơn Django, Flask (nhưng đang phát triển mạnh)
* Cần chú ý cấu trúc module khi scale lớn
* Một số thư viện legacy chưa hỗ trợ async tốt (đã chọn lib tương thích)

---

## ✨ Ảnh hưởng

* Tăng tốc phát triển, dễ maintain codebase
* Có thể tách thành microservice trong tương lai dễ dàng nhờ ASGI-native
* Frontend & QA có tài liệu endpoint tự động qua `/docs`, `/redoc`

---

## 🔄 Các lựa chọn đã loại bỏ

* **Flask**: Không hỗ trợ async natively, cần mở rộng nhiều để đạt hiệu năng tương đương.
* **Django Rest Framework**: Quá nặng cho nhu cầu Gateway, nhiều boilerplate.
* **Tornado**: Mạnh về async nhưng API quá thấp, khó maintain với team đa cấp độ.

---

## 📎 Tài liệu liên quan

* Kiến trúc hệ thống: `docs/System_Architect.pdf`
* Dev Guide: [`DEV_GUIDE.md`](../DEV_GUIDE.md)
* ADR tiếp theo: [`adr-002-rbac-design.md`](./adr-002-rbac-design.md)

---

> “Simple. Typed. Fast. That’s FastAPI.”
