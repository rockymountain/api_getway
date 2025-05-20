# ADR-007: Chiến lược xử lý lỗi (Error Handling) cho API Gateway (DX VAS)

* **Trạng thái**: Đã chấp thuận ✅
* **Ngày**: 21/05/2025
* **Người đề xuất**: Nguyễn Văn K (Tech Lead)
* **Bối cảnh**: Dự án Chuyển đổi số VAS

---

## 📌 Bối cảnh

API Gateway là nơi tiếp nhận toàn bộ request từ frontend và định tuyến đến các backend. Việc xử lý lỗi phải thống nhất, rõ ràng và dễ hiểu đối với cả người dùng cuối (qua frontend) và developer (qua log và debug). Các hệ thống backend (SIS, CRM, LMS) cũng có thể trả về lỗi theo format riêng, cần chuẩn hóa lại ở gateway.

---

## 🧠 Quyết định

**Áp dụng chiến lược xử lý lỗi tập trung, với định dạng JSON chuẩn hóa cho tất cả response lỗi từ API Gateway.**

---

## 🛠 Thiết kế

### 1. Mục tiêu

* Đảm bảo mọi lỗi đều trả về JSON đúng định dạng
* Giao diện frontend có thể hiển thị lỗi dễ hiểu
* Developer dễ truy vết và debug
* Dễ dàng log & monitor lỗi theo mã

### 2. Định dạng lỗi chuẩn hóa

```json
{
  "error_code": 403,
  "message": "Permission denied",
  "details": "Permission 'EDIT_STUDENT' is required",
  "request_id": "abc-123",
  "timestamp": "2025-05-21T08:30:00Z"
}
```

* `error_code`: HTTP status code (hoặc có thể mở rộng thành mã lỗi nội bộ trong tương lai)
* `message`: mô tả lỗi chính (cho người dùng)
* `details`: thông tin chi tiết hơn (cho developer/frontend debug)
* `request_id`: phục vụ tracing/log
* `timestamp`: ISO8601

### 3. Mapping lỗi phổ biến

| HTTP Code | Mô tả             | Khi nào xảy ra                           |
| --------- | ----------------- | ---------------------------------------- |
| 400       | Bad Request       | Thiếu param, body sai định dạng          |
| 401       | Unauthorized      | Thiếu/không hợp lệ Access Token          |
| 403       | Forbidden         | Không đủ quyền truy cập (RBAC)           |
| 404       | Not Found         | Endpoint không tồn tại                   |
| 422       | Validation Error  | Request đúng format JSON nhưng sai logic |
| 429       | Too Many Requests | Rate limit                               |
| 502       | Bad Gateway       | Backend trả lỗi hoặc không phản hồi      |

### 4. Middleware xử lý tập trung

* Sử dụng `exception_handler` trong FastAPI để xử lý toàn bộ lỗi tại một điểm
* Custom các exception cụ thể:

  * `HTTPException`
  * `ValidationError` (Pydantic/FastAPI)
  * `RBACPermissionDenied`
  * `TokenExpiredError`
  * Các lỗi không mong muốn như `ValueError`, `TypeError`, `RuntimeError`... sẽ được map thành lỗi `500 Internal Server Error` với request\_id và message chung, tránh trả về stacktrace cho client

### 5. Forward lỗi từ backend

* Nếu backend trả lỗi không chuẩn, gateway sẽ:

  * Lấy status code + message → wrap lại theo định dạng chuẩn
  * Gắn `source: backend_service_name` nếu cần (giúp phân tích root cause dễ hơn)

---

## ✅ Lợi ích

* Trải nghiệm frontend nhất quán
* Developer dễ log và test
* Giám sát lỗi dễ hơn (có thể alert theo error\_code hoặc request\_id)
* Tăng độ tin cậy của toàn hệ thống

---

## ❌ Rủi ro & Giải pháp

| Rủi ro                            | Giải pháp                                                                                                                                                    |
| --------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Format lỗi không đồng nhất        | Áp dụng handler trung tâm cho mọi exception                                                                                                                  |
| Thông tin lỗi lộ dữ liệu nhạy cảm | Trong môi trường production, trường `details` sẽ bị lược bỏ hoặc thay bằng thông báo chung. Chi tiết lỗi chỉ được ghi vào log nội bộ (Cloud Logging, stdout) |
| Backend trả lỗi không rõ ràng     | Mapping lại tại gateway và thêm `source` để trace                                                                                                            |

---

## 🔄 Các lựa chọn đã loại bỏ

* **Trả lỗi mặc định theo FastAPI/Pydantic**: Khó hiểu, không có timestamp, thiếu context
* **Trả lỗi HTML (default)**: Không phù hợp với REST API
* **Trả lỗi từng nơi tự xử lý**: Thiếu thống nhất, dễ lỗi không chuẩn

---

## 📎 Tài liệu liên quan

* Exception middleware: [`utils/exception_handler.py`](../../utils/exception_handler.py)
* Dev Guide – Error Handling section: [`DEV_GUIDE.md`](../DEV_GUIDE.md)
* ADR trước: [`adr-006-auth-design.md`](./adr-006-auth-design.md)

---

> “Một hệ thống tốt không chỉ chạy tốt khi đúng – mà còn phản hồi tốt khi sai.”
