# ADR-004: Chiến lược versioning cho API Gateway (DX VAS)

* **Trạng thái**: Đã chấp thuận ✅
* **Ngày**: 18/05/2025
* **Người đề xuất**: Nguyễn Thành D
* **Bối cảnh**: Dự án Chuyển đổi số VAS

---

## 📌 Bối cảnh

API Gateway đóng vai trò trung gian giữa frontend và các dịch vụ backend như SIS, CRM, LMS. Hệ thống sẽ được mở rộng trong tương lai, có khả năng:

* Thêm tính năng mới mà không phá vỡ tính tương thích
* Giữ ổn định các client cũ khi backend nâng cấp
* Triển khai nhiều frontend (Admin, Portal, Mobile) với kỳ vọng khác nhau về contract API

Do đó, cần có một **chiến lược versioning rõ ràng**, vừa dễ sử dụng vừa đảm bảo backward compatibility.

---

## 🧠 Quyết định

**Áp dụng versioning bằng URL prefix – cụ thể là `/api/v1/` và sẽ tăng version nếu có breaking changes.**

---

## 📐 Cách triển khai

### 1. Cấu trúc routing

* Tất cả các endpoint đều được prefix bằng `/api/v{version}/...`
* Ví dụ:

  * `/api/v1/sis/students`
  * `/api/v1/auth/login`

### 2. Nguyên tắc tăng version

* `v1` là version chính thức đầu tiên
* Chỉ tăng version (v2, v3...) khi có **breaking change**:

  * Thay đổi contract (input/output)
  * Thay đổi logic xử lý quan trọng ảnh hưởng tới client

### 3. Song song nhiều version (nếu cần)

* `/api/v1/` và `/api/v2/` có thể tồn tại đồng thời
* Frontend cần chỉ định version rõ trong mọi request

### 4. Cấu trúc mã nguồn (FastAPI)

* Dùng router phân version:

```python
# main.py
app.include_router(api_v1_router, prefix="/api/v1")
```

* Mỗi version có thư mục/tệp riêng nếu cần:

```python
routers/api_v1/
routers/api_v2/
```

---

## ✅ Lợi ích

* Giữ backward compatibility cho các frontend cũ
* Triển khai phiên bản mới song song, giảm downtime và rủi ro
* Đơn giản, rõ ràng, không phụ thuộc vào header hoặc param ẩn
* Dễ cấu hình RBAC và route permission theo version

---

## ❌ Rủi ro & Giải pháp

| Vấn đề                              | Giải pháp                                                             |
| ----------------------------------- | --------------------------------------------------------------------- |
| Tăng version quá nhiều, khó quản lý | Áp dụng Semantic Versioning về mặt tư tưởng, chỉ tăng khi thật sự cần |
| Duplicated code giữa các version    | Tách shared logic vào `services`, tránh lặp lại router                |
| Frontend gọi sai version            | Áp dụng test tích hợp + monitoring request headers                    |

---

## 🔄 Các lựa chọn đã loại bỏ

* **Version bằng Header (`Accept: application/vnd.api+json; version=1`)**:

  * Khó debug, không rõ ràng khi dùng trực tiếp từ browser/devtool

* **Query Param (`?version=1`)**:

  * Không RESTful, dễ bị cache sai

* **Không version**:

  * Không đảm bảo backward compatibility

---

## 📎 Tài liệu liên quan

* Dev Guide – API Design: [`DEV_GUIDE.md`](../DEV_GUIDE.md)
* Route Map cho RBAC: [`route_permission_map`](../../rbac/models.py)
* Swagger UI: [`/docs`](http://localhost:8000/docs)
* ADR trước: [`adr-003-ci-cd-structure.md`](./adr-003-ci-cd-structure.md)

---

> “Thêm v1 từ đầu – bạn sẽ không bao giờ hối hận.”
