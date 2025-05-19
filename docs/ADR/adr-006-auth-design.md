# ADR-006: Thiết kế hệ thống xác thực (Auth) cho API Gateway (DX VAS)

* **Trạng thái**: Đã chấp thuận ✅
* **Ngày**: 20/05/2025
* **Người đề xuất**: Nguyễn Thành D (Backend Lead)
* **Bối cảnh**: Dự án Chuyển đổi số VAS

---

## 📌 Bối cảnh

API Gateway của DX VAS đóng vai trò kiểm soát quyền truy cập cho toàn bộ hệ thống frontend (Admin Webapp, Customer Portal). Vì vậy, yêu cầu một cơ chế xác thực:

* Tin cậy (dựa trên hệ thống có sẵn như Google OAuth2)
* Đơn giản với người dùng (SSO)
* Dễ kiểm tra và xác minh ở API Gateway
* Tích hợp tốt với cơ chế RBAC động đã được chọn ở [ADR-002](./adr-002-rbac-design.md)

---

## 🧠 Quyết định

**Sử dụng OAuth2 của Google làm cơ chế xác thực chính, kết hợp JWT để giao tiếp nội bộ.**

---

## 🔐 Mô hình xác thực

### 1. Đăng nhập (Login Flow)

* Người dùng chọn đăng nhập bằng Google
* Sau khi xác thực OAuth2 thành công, hệ thống sẽ:

  * Lấy `id_token` từ Google (dùng để xác minh danh tính phía server)
  * Decode payload (`sub`, `email`, `name`, `picture`...)
  * Đồng bộ user vào hệ thống nếu chưa có (dựa theo email)
  * Tạo **Access Token** (JWT ngắn hạn) + **Refresh Token** (DB)

### 2. JWT Access Token

* JWT được ký bởi secret key riêng của hệ thống (symmetric HMAC SHA256)
* Payload bao gồm:

```json
{
  "sub": "user_id",
  "email": "abc@truongvietanh.edu.vn",
  "role": "teacher",
  "exp": 1700000000
}
```

* Token được sử dụng cho các request đến API Gateway qua header `Authorization: Bearer <token>`
* **Lưu ý:** Trường `role` trong JWT là thông tin tạm thời nhằm hỗ trợ hiển thị giao diện phía frontend nhanh hơn. **Quyết định phân quyền động vẫn dựa trên `user_id → role → permission` từ Redis/DB (RBAC) như mô tả trong [ADR-002](./adr-002-rbac-design.md)**

### 3. Refresh Token

* Lưu **ưu tiên trong DB** (`user_refresh_token`) để đảm bảo tính bền vững và dễ quản lý (revoke all, audit log)
* Có thể sử dụng Redis có persistence nếu cần tốc độ, với TTL khoảng 7 ngày
* Refresh token được mã hóa trước khi lưu trữ trong DB để tăng cường bảo mật

### 4. Middleware kiểm tra token

* Trích `Authorization` header
* Decode và kiểm tra chữ ký, `exp`, `nbf`
* Nếu hợp lệ → gán `request.user`, `X-User-Id`, `X-Role`, `X-Permissions`

### 5. Logout

* Xoá refresh token khỏi DB hoặc Redis
* Xoá session frontend (nếu có)

---

## ✅ Lợi ích

* Đơn giản hoá trải nghiệm người dùng với SSO Google
* Hạn chế phải lưu trữ mật khẩu (không có local password)
* JWT hiệu suất cao, không cần truy vấn DB mỗi request
* Dễ tích hợp với RBAC, forwarding backend

---

## ❌ Rủi ro & Giải pháp

| Rủi ro                     | Giải pháp                                                                               |
| -------------------------- | --------------------------------------------------------------------------------------- |
| JWT bị đánh cắp            | Giới hạn thời gian sống (15 phút), bắt buộc HTTPS                                       |
| Refresh Token bị lộ        | Mã hóa khi lưu, lưu trong DB thay vì cookie/localStorage, revoke khi logout/all devices |
| Người ngoài đăng nhập được | Chỉ cho phép email thuộc domain `@truongvietanh.edu.vn` qua Google OAuth config         |

---

## 🔄 Các lựa chọn đã loại bỏ

* **Local login bằng email/password**:

  * Tăng rủi ro bảo mật, cần flow reset mật khẩu, lưu trữ password
* **SSO nội bộ riêng**:

  * Không có hạ tầng hiện tại; Google Workspace đã sẵn sàng và đáng tin cậy
* **Access token là session ID (non-JWT)**:

  * Không thể forward an toàn, không self-contained, khó mở rộng đa dịch vụ

---

## 📎 Tài liệu liên quan

* FastAPI Auth flow: [`auth/router.py`](../../auth/router.py)
* JWT utils: [`utils/security.py`](../../utils/security.py)
* Dev Guide: [`DEV_GUIDE.md`](../DEV_GUIDE.md)
* RBAC flow: [`adr-002-rbac-design.md`](./adr-002-rbac-design.md)

---

> “SSO đơn giản cho người dùng – JWT rõ ràng cho hệ thống.”
