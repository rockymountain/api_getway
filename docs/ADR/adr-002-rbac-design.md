# ADR-002: Thiết kế hệ thống phân quyền RBAC động cho API Gateway

* **Trạng thái**: Đã chấp thuận ✅
* **Ngày**: 16/05/2025
* **Người đề xuất**: Trần Thị B
* **Bối cảnh**: Dự án Chuyển đổi số VAS

---

## 📌 Bối cảnh

Dự án DX VAS cần một cơ chế phân quyền đủ linh hoạt để đáp ứng:

* Môi trường giáo dục có nhiều vai trò (học sinh, giáo viên, admin, phụ huynh…)
* Frontend không xử lý logic phân quyền, tất cả phải kiểm tra tại API Gateway
* Dễ cập nhật khi thay đổi quy định truy cập / chức năng hệ thống
* Có thể cấu hình trực tiếp qua Admin Webapp

Trước đây, các hệ thống SIS/LMS sử dụng phân quyền tĩnh hoặc hardcoded, dẫn đến khó mở rộng và bảo trì.

---

## 🧠 Quyết định

**Áp dụng cơ chế phân quyền động RBAC (Role-Based Access Control) tại API Gateway, với khả năng cấu hình thông qua bảng dữ liệu và cache Redis.**

---

## ✅ Mô hình được chọn

### 1. Bảng dữ liệu chính:

* `roles (id, name, description)`
* `permissions (id, code, description)`
* `role_permission (role_id, permission_id)`
* `users (id, email, name)`
* `user_role (user_id, role_id)`
* `route_permission_map (id, path_pattern, method, required_permission)`

### 2. Nguyên lý xử lý:

* Mỗi API request gửi lên sẽ có:

  * `Authorization` chứa JWT → decode để lấy `user_id`
  * Kiểm tra quyền qua Redis → nếu không có thì fallback DB
  * Đối chiếu endpoint hiện tại với bảng `route_permission_map`
* Nếu `user_permissions` chứa `required_permission` → cho phép

### 3. Cache và hiệu năng:

* Redis key:

  * `user:{user_id}:permissions`
  * `pattern:{method}:{path}` → required\_permission
* Khi thay đổi role/permission → xóa cache liên quan
* Dùng mô hình **cache-aside**, đảm bảo consistency

### 4. Giao diện cấu hình:

* Admin Webapp có module `/rbac/`

  * Gán role cho user
  * Tạo/sửa/xóa role và permission
  * Cập nhật permission cho endpoint

---

## ✨ Lợi ích

* Phân quyền tập trung, không cần sửa code mỗi khi có thay đổi quyền
* Có thể phân quyền đến từng method + endpoint cụ thể
* Dễ mở rộng khi hệ thống có thêm microservice
* Có thể audit log permission violation cho mục đích bảo mật

---

## ❌ Rủi ro & Giải pháp

| Vấn đề                            | Giải pháp                                  |
| --------------------------------- | ------------------------------------------ |
| Cache không đồng bộ               | Dùng invalidation theo user\_id và pattern |
| Sai cấu hình dẫn đến từ chối nhầm | Thêm log chi tiết + công cụ test quyền     |
| Giao diện phân quyền bị lạm dụng  | Chỉ admin có `MANAGE_RBAC` mới truy cập    |

---

## 🔄 Các lựa chọn đã loại bỏ

* **Hardcoded trong route**: nhanh nhưng không linh hoạt, khó bảo trì
* **JWT nhúng toàn bộ permission**: payload lớn, không phản ánh thay đổi real-time
* **Backend kiểm tra riêng**: phân tán logic, khó kiểm soát và bảo mật

---

## 📎 Tài liệu liên quan

* Dev Guide: [`DEV_GUIDE.md`](../DEV_GUIDE.md)
* RBAC module: [`rbac/`](../../rbac/)
* Swagger UI mô tả: [`/docs`](http://localhost:8000/docs)
* ADR trước: [`adr-001-fastapi.md`](./adr-001-fastapi.md)

---

> “Permission should be configurable – not compiled.”
