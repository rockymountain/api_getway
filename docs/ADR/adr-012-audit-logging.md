# ADR-012: Thiết kế hệ thống Audit Logging cho API Gateway (DX VAS)

* **Trạng thái**: Đã chấp thuận ✅
* **Ngày**: 26/05/2025
* **Người đề xuất**: Nguyễn Văn H (Platform Architect)
* **Bối cảnh**: Dự án Chuyển đổi số VAS

---

## 📌 Bối cảnh

API Gateway xử lý tất cả các luồng truy cập từ frontend đến backend. Ngoài việc log lỗi và hoạt động hệ thống (observability), còn cần hệ thống **Audit Logging** phục vụ các mục đích:

* Ghi nhận hành vi truy cập/thao tác của người dùng cuối (user-level activity)
* Theo dõi các hành động quan trọng (truy cập dữ liệu học sinh, cập nhật thông tin giáo viên...)
* Đáp ứng yêu cầu kiểm toán nội bộ hoặc theo tiêu chuẩn ngành giáo dục
* Phân tích bảo mật khi có sự cố hoặc nghi ngờ truy cập trái phép

---

## 🧠 Quyết định

**Áp dụng chiến lược Audit Logging tập trung tại API Gateway bằng cách ghi lại có chọn lọc các hành động quan trọng, gửi về Cloud Logging và hỗ trợ lưu trữ dài hạn nếu cần.**

---

## 🛠 Thiết kế hệ thống Audit Log

### 1. Mô hình log

* Mỗi log entry là một JSON object với các trường:

```json
{
  "timestamp": "2025-05-26T10:45:00Z",
  "request_id": "abc-123",
  "user_id": "u_567",
  "role": "teacher",
  "ip": "203.113.1.5",
  "action": "update_student",
  "resource": "student/102",
  "method": "PUT",
  "status_code": 200,
  "latency_ms": 147,
  "source": "api-gateway",
  "actor_type": "human",
  "audit_level": "critical"
}
```

* `actor_type`: có thể là `human`, `service`, hoặc `system`
* `resource`: theo định dạng `{resource_type}/{resource_id}`

### 2. Các loại hành động cần audit

| Loại hành động              | Ví dụ                                      |
| --------------------------- | ------------------------------------------ |
| Truy cập dữ liệu nhạy cảm   | GET student, GET grades                    |
| Thay đổi thông tin          | PUT/PATCH student/teacher                  |
| Tác vụ hệ thống             | Đăng nhập, đổi mật khẩu, phân quyền        |
| Gọi API outbound quan trọng | Gửi thông báo, gửi dữ liệu đến CRM         |
| Thay đổi cấu hình bảo mật   | Sửa RBAC, sửa limit cấu hình (nếu qua API) |

### 3. Tích hợp tại API Gateway

* Middleware xử lý trước và sau khi request được forward đến backend:

  * Trước: phân tích method, path, role, RBAC để quyết định cần audit
  * Sau: ghi log audit đầy đủ kèm `status_code`, `latency_ms`
* Gửi log ra stdout dưới định dạng JSON → Cloud Logging ingest tự động

### 4. Audit Level

* `critical`: thao tác ghi nhạy cảm (PUT, DELETE, phân quyền...)
* `info`: thao tác xem thông tin nhưng có dữ liệu nhạy cảm
* `debug`: thao tác API phụ, chỉ log nếu bật debug

### 5. Truy vấn và lưu trữ

* Truy vấn log qua Cloud Logging hoặc xuất ra BigQuery để phân tích nâng cao
* Lưu trữ:

  * Cloud Logging: tối thiểu 180 ngày
  * Long-term: GCS hoặc BigQuery từ 1–3 năm theo yêu cầu kiểm toán
* Đảm bảo tính toàn vẹn log:

  * Log không thể bị chỉnh sửa thủ công
  * Có thể tích hợp WORM storage hoặc ký số từng dòng log nếu cần tuân thủ nghiêm ngặt

### 6. Quyền truy cập audit log

* Chỉ nhóm **Platform Admin** hoặc **Security Engineer** được truy cập log đầy đủ
* Phân quyền chi tiết:

  * `log.reader.system`: xem log kỹ thuật
  * `log.reader.audit`: xem hành vi người dùng
* Audit cả hành động truy cập vào Audit Log (Cloud Logging hỗ trợ)

---

## ✅ Lợi ích

* Ghi nhận rõ hành vi người dùng và thay đổi hệ thống quan trọng
* Hỗ trợ điều tra, phản ứng bảo mật, và phân tích root cause nhanh chóng
* Tuân thủ các quy định nội bộ và bên ngoài (GDPR, kiểm toán ngành giáo dục...)
* Đảm bảo audit không phụ thuộc backend, tập trung tại điểm trung gian

---

## ❌ Rủi ro & Giải pháp

| Rủi ro                       | Giải pháp                                                        |
| ---------------------------- | ---------------------------------------------------------------- |
| Log quá nhiều → gây noise    | Chỉ audit hành vi theo danh sách cho phép, audit\_level rõ ràng  |
| Log chứa dữ liệu nhạy cảm    | Không log payload, chỉ log ID/tên field; hash nếu cần xác minh   |
| Truy cập trái phép log audit | Tách vai trò, logging truy cập log, principle of least privilege |

---

## 🔄 Các lựa chọn đã loại bỏ

* **Chỉ audit ở backend**: không kiểm soát được toàn bộ hành vi, thiếu thông tin nếu bị chặn bởi RBAC từ gateway
* **Gộp audit vào log hệ thống**: gây lẫn lộn, khó filter & không hỗ trợ phân quyền riêng

---

## 📎 Tài liệu liên quan

* Middleware: [`utils/audit_logger.py`](../../utils/audit_logger.py)
* Dev Guide – Logging Strategy: [`DEV_GUIDE.md`](../DEV_GUIDE.md)
* ADR liên quan: [`adr-005-observability.md`](./adr-005-observability.md)

---

> “Đừng chỉ log hệ thống – hãy log hành vi người dùng quan trọng để bảo vệ họ và chính bạn.”
