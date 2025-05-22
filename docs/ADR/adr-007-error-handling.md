# ADR-007: Chiến lược xử lý lỗi (Error Handling) cho API Gateway (DX VAS)

* **Trạng thái**: Đã bị thay thế (superseded by `dx_vas/adr-011-api-error-format.md`)
* **Ngày**: 21/05/2025
* **Người đề xuất**: Nguyễn Văn K (Tech Lead)
* **Bối cảnh**: Dự án Chuyển đổi số VAS

---

## 📌 Bối cảnh

API Gateway là nơi tiếp nhận toàn bộ request từ frontend và định tuyến đến các backend. Việc xử lý lỗi phải thống nhất, rõ ràng và dễ hiểu đối với cả người dùng cuối (qua frontend) và developer (qua log và debug). Các hệ thống backend (SIS, CRM, LMS) cũng có thể trả về lỗi theo format riêng, cần chuẩn hóa lại ở gateway.

---

## 🧠 Quyết định

**Tuân thủ theo định dạng lỗi chuẩn đã được quy định trong [DX-VAS/ADR-011 (API Error Format)](https://github.com/rockymountain/dx_vas/blob/main/docs/ADR/adr-011-api-error-format.md) cho toàn hệ thống.**

---

## 🛠 Triển khai tại API Gateway

### 1. Middleware xử lý tập trung

* Sử dụng `exception_handler` trong FastAPI để xử lý toàn bộ lỗi tại một điểm
* Custom các exception cụ thể:
  * `HTTPException`
  * `ValidationError` (Pydantic/FastAPI)
  * `RBACPermissionDenied`
  * `TokenExpiredError`
  * Các lỗi không mong muốn như `ValueError`, `TypeError`, `RuntimeError`... sẽ được map thành lỗi `500 Internal Server Error` với `trace_id` và `message` chung

### 2. Forward lỗi từ backend

* Nếu backend trả lỗi không chuẩn:
  * Lấy status code + message → wrap lại theo định dạng chuẩn
  * Gắn `meta.source: backend_service_name` nếu cần (giúp phân tích root cause dễ hơn)

### 3. Mapping lỗi phổ biến tại Gateway

| HTTP Code | Mô tả             | Khi nào xảy ra                           |
| --------- | ----------------- | ---------------------------------------- |
| 400       | Bad Request       | Thiếu param, body sai định dạng          |
| 401       | Unauthorized      | Thiếu/không hợp lệ Access Token          |
| 403       | Forbidden         | Không đủ quyền truy cập (RBAC)           |
| 404       | Not Found         | Endpoint không tồn tại                   |
| 422       | Validation Error  | Request đúng format JSON nhưng sai logic |
| 429       | Too Many Requests | Rate limit                               |
| 502       | Bad Gateway       | Backend trả lỗi hoặc không phản hồi      |

---

## ✅ Lợi ích

* Tuân thủ chính sách chung toàn hệ thống
* Tăng khả năng giám sát & phân tích lỗi tập trung
* Cho phép các đội frontend/backend xử lý lỗi thống nhất

---

## ❌ Rủi ro & Giải pháp

| Rủi ro                            | Giải pháp                                                                                                                                                    |
| --------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Thông tin lỗi lộ dữ liệu nhạy cảm | Trong môi trường production, trường `details` sẽ bị lược bỏ hoặc thay bằng thông báo chung. Chi tiết lỗi chỉ được ghi vào log nội bộ (Cloud Logging, stdout) |
| Backend trả lỗi không rõ ràng     | Mapping lại tại gateway và thêm `meta.source` để trace                                                                                                       |

---

## 🔄 Trạng thái kế thừa

> ADR này **được thay thế bởi** [DX-VAS/ADR-011 (API Error Format)](https://github.com/rockymountain/dx_vas/blob/main/docs/ADR/adr-011-api-error-format.md). Tài liệu này chỉ giữ lại các đặc tả triển khai cụ thể tại API Gateway.

---

## 📎 Tài liệu liên quan

* Exception middleware: [`utils/exception_handler.py`](../../utils/exception_handler.py)
* Dev Guide – Error Handling section: [`DEV_GUIDE.md`](../DEV_GUIDE.md)
* ADR Dự Án Tổng [DX-VAS/ADR-011 (API Error Format)](https://github.com/rockymountain/dx_vas/blob/main/docs/ADR/adr-011-api-error-format.md)

---
> “Một hệ thống tốt không chỉ chạy tốt khi đúng – mà còn phản hồi tốt khi sai.”
