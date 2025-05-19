# ADR-008: Thiết kế cơ chế Rate Limiting cho API Gateway (DX VAS)

* **Trạng thái**: Đã chấp thuận ✅
* **Ngày**: 22/05/2025
* **Người đề xuất**: Nguyễn Quốc T (Infra Lead)
* **Bối cảnh**: Dự án Chuyển đổi số VAS

---

## 📌 Bối cảnh

Hệ thống API Gateway là điểm đầu xử lý toàn bộ lưu lượng từ frontend. Để đảm bảo ổn định, chống lạm dụng và bảo vệ backend khỏi bị tấn công từ chối dịch vụ (DoS), cần thiết kế cơ chế **Rate Limiting**:

* Giới hạn số lượng request từ một user/IP trong một khoảng thời gian nhất định
* Cảnh báo hoặc từ chối khi vượt ngưỡng
* Ghi log và theo dõi hành vi người dùng
* Kết hợp linh hoạt với các giải pháp ở tầng hạ tầng như Cloud Armor

---

## 🧠 Quyết định

**Áp dụng cơ chế Rate Limiting theo IP và theo user\_id (nếu có), kết hợp Redis để đếm và giới hạn request trong gateway.**

---

## 🛠 Thiết kế

### 1. Cơ chế áp dụng

* Dựa trên middleware (vd: `slowapi` hoặc middleware custom)
* Dựa theo:

  * `user_id` nếu có token hợp lệ
  * `client_ip` nếu là anonymous / chưa đăng nhập
* Ngưỡng mặc định (có thể cấu hình):

  * 60 request/phút/user
  * 30 request/phút/IP với anonymous

### 2. Redis-backed Sliding Window Counter (ưu tiên)

* Sử dụng thuật toán Sliding Window Counter để đảm bảo giới hạn chính xác hơn Fixed Window
* Redis lưu thông tin `count` + TTL theo key:

  * `ratelimit:user:{user_id}`
  * `ratelimit:ip:{ip}`
* TTL = 60 giây (configurable)
* Nếu vượt quá ngưỡng → trả lỗi 429
* Có thể nâng cấp lên leaky bucket hoặc token bucket nếu yêu cầu co giãn (burst control) rõ rệt hơn trong tương lai

### 3. Phản hồi khi vượt ngưỡng

```json
{
  "error_code": 429,
  "message": "Too Many Requests",
  "details": "You have exceeded the allowed rate limit. Please wait and try again.",
  "retry_after": 30
}
```

* Trả kèm header `Retry-After: 30`
* Ghi log cảnh báo và gắn `request_id`

### 4. Mở rộng theo vai trò / loại người dùng

* Với `role = admin` → có thể nâng ngưỡng hoặc miễn giới hạn (internal service)
* Hạn mức có thể điều chỉnh theo `role`, `endpoint`, `path pattern`
* Hỗ trợ cấu hình từ bảng DB hoặc file YAML/Redis

### 5. Giám sát & Alert

* Log mỗi lần trả lỗi 429 (ghi `user_id`, `ip`, `path`, `request_id`)
* Thu thập metric: `rate_limit_exceeded_total`
* Tạo cảnh báo khi:

  * > 5% tổng request trong 5 phút bị 429
  * Một IP vượt 1000 lần 429 trong 1 giờ

### 6. Kết hợp với Cloud Armor (bổ sung phòng thủ tầng thấp)

* Dùng Cloud Armor để chặn:

  * Các IP đã biết độc hại (deny list)
  * DDoS ở tầng HTTP(S)
* API Gateway xử lý rate limit tinh vi hơn theo user/role/endpoint

---

## ✅ Lợi ích

* Chống spam/tấn công từ client xấu
* Bảo vệ tài nguyên backend
* Cải thiện hiệu suất chung trong giờ cao điểm
* Dễ giám sát và mở rộng theo nhu cầu từng nhóm người dùng
* Linh hoạt và mở rộng được (RBAC-based rate limiting)

---

## ❌ Rủi ro & Giải pháp

| Rủi ro                            | Giải pháp                                                                                                                      |
| --------------------------------- | ------------------------------------------------------------------------------------------------------------------------------ |
| Người dùng bị giới hạn nhầm       | Thông báo rõ ràng + log chi tiết + có header Retry-After để frontend retry                                                     |
| IP bị NAT (nhiều user trùng IP)   | Ưu tiên theo `user_id` nếu có, và cho phép tăng ngưỡng IP nếu nhận diện mạng tin cậy                                           |
| Redis bị lỗi → mất kiểm soát rate | Áp dụng timeout fail-open (ví dụ 30s), hoặc degrade mềm: tạm thời không giới hạn hoặc đặt ngưỡng rất cao thay vì block toàn bộ |

---

## 🔄 Các lựa chọn đã loại bỏ

* **Không giới hạn (open)**: Dễ bị lạm dụng, không kiểm soát được lưu lượng
* **Chỉ dùng Cloud Armor**: Không đủ linh hoạt theo user/role/endpoint, khó điều chỉnh động
* **Block toàn bộ sau N lỗi**: Không phân biệt intent, dễ gây bức xúc người dùng hợp lệ

---

## 📎 Tài liệu liên quan

* Middleware: [`utils/rate_limiter.py`](../../utils/rate_limiter.py)
* Dev Guide – Security & Throttling section: [`DEV_GUIDE.md`](../DEV_GUIDE.md)
* ADR trước: [`adr-007-error-handling.md`](./adr-007-error-handling.md)

---

> “Không phải ai cũng cần bị giới hạn – nhưng ai cũng cần được bảo vệ khỏi lạm dụng.”
