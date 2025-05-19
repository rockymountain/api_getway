# ADR-022: Observability cho tích hợp bên thứ ba (Third-Party Integrations)

* **Trạng thái**: Đã chấp thuận ✅
* **Ngày**: 04/06/2025
* **Người đề xuất**: Nguyễn Thanh H (SRE + Partner Engineering)
* **Bối cảnh**: Dự án Chuyển đổi số VAS

---

## 📌 Bối cảnh

API Gateway của DX VAS tích hợp với nhiều bên thứ ba như:

* Zalo Notification API
* Google OAuth
* CRM hệ thống đối tác

Những tích hợp này nằm ngoài quyền kiểm soát trực tiếp của đội ngũ DX, nhưng có tác động quan trọng đến trải nghiệm người dùng. Vì vậy, cần có **chiến lược observability riêng cho third-party** nhằm:

* Giám sát độ trễ, tần suất lỗi, thông lượng
* Hiểu được lý do và nguồn lỗi (do đối tác, gateway hay timeout)
* Phản ứng kịp thời khi đối tác thay đổi API hoặc có outage

---

## 🧠 Quyết định

**Thiết lập observability tầng tích hợp bên thứ ba qua centralized logging, metric chuẩn hóa, cảnh báo theo error rate + timeout, dashboard theo endpoint và health check chủ động.**

---

## 🔍 Thành phần chính của chiến lược

### 1. Logging chuẩn hoá khi gọi đối tác

* Mỗi request outbound tới hệ thống bên thứ ba sẽ log:

  * URL, method
  * Status code (của đối tác)
  * Error message (nếu có, chỉ ghi phần ngắn gọn, không log toàn bộ body để tránh lộ thông tin nhạy cảm)
  * Thời gian thực thi (latency)
  * request\_id + trace\_id
* Mẫu log chuẩn:

  ```json
  {
    "type": "third_party_call",
    "partner": "zalo",
    "url": "https://api.zalo.me/...",
    "status": 500,
    "latency_ms": 1234,
    "error": "upstream timeout",
    "request_id": "abc-xyz-123"
  }
  ```

### 2. Metric & Dashboard theo partner

* Metric gửi lên Cloud Monitoring:

  * `third_party_latency{partner="zalo"}`
  * `third_party_error_rate{partner="crm"}`
  * `third_party_success_count{partner="oauth"}`
  * `third_party_5xx_count`, `third_party_4xx_count`
* Có dashboard:

  * Tổng quan theo ngày
  * Breakdown theo partner
  * Alert channel riêng: `#infra-partner-alerts`

### 3. Timeout & Retry riêng cho từng partner

* Timeout default: 3s (hoặc theo SLA đối tác cụ thể)
* Retry: chỉ cho phép với GET/idempotent method
* Sử dụng retry có backoff + circuit breaker nếu partner lỗi liên tục

### 4. Circuit Breaker cho bên thứ ba

* Nếu 50% request lỗi trong 2 phút:

  * Đóng circuit trong 5 phút → trả fallback hoặc 503
* Giúp bảo vệ hệ thống khỏi cascade failure do đối tác gặp sự cố

### 5. Cảnh báo + phản ứng

* Nếu:

  * `error_rate > 10%` trong 5 phút
  * `latency > 1000ms` liên tục
* Thì:

  * Gửi Slack + email alert
  * Tạm disable integration nếu có switch/toggle (flags)
  * Ghi issue "Partner degraded" trong hệ thống nội bộ

### 6. Truy xuất (trace) và correlation ID

* Mỗi call đi từ user request → third-party đều có `trace_id`
* Cho phép truy vấn log từ người dùng đến lỗi bên ngoài
* Hỗ trợ debugging liên dịch vụ / liên hệ với đối tác dễ dàng

### 7. Health Check chủ động với đối tác (synthetic probes)

* Nếu partner có endpoint `/health` hoặc `/ping` → gọi định kỳ (1–5 phút/lần)
* Log kết quả và gắn tag `synthetic_check=true`
* Cảnh báo sớm nếu partner mất kết nối hoặc có lỗi trước khi ảnh hưởng người dùng thật

---

## ✅ Lợi ích

* Hiểu rõ nguyên nhân lỗi liên quan bên thứ ba
* Tăng khả năng phòng ngừa và phản ứng chủ động
* Bảo vệ backend nội bộ khỏi lỗi lan từ dịch vụ bên ngoài
* Giúp thống kê SLA thực tế của tích hợp external
* Có thể phát hiện sự cố trước khi người dùng phản ánh

---

## ❌ Rủi ro & Giải pháp

| Rủi ro                                                | Giải pháp                                                           |
| ----------------------------------------------------- | ------------------------------------------------------------------- |
| Ghi log quá chi tiết gây overload hoặc rò rỉ nhạy cảm | Chỉ log error ngắn gọn, masking token, sampling success logs        |
| Sai timeout dẫn đến retry lỗi                         | Tinh chỉnh timeout riêng cho từng partner dựa trên quan sát thực tế |
| Không alert kịp thời khi partner down                 | Tích hợp synthetic check + metric alert + check manual mỗi sáng     |

---

## 🔄 Các lựa chọn đã loại bỏ

* **Không log riêng cho call external**: khó truy vấn + không rõ nguyên nhân lỗi
* **Chỉ dùng metric chung (latency/error)**: không thể phân biệt lỗi do ai
* **Luôn retry mọi call lỗi**: gây thắt cổ chai và cascade failure

---

## 📎 Tài liệu liên quan

* Logging structure: [`utils/logging_third_party.py`](../../utils/logging_third_party.py)
* Monitoring config: [`infra/observability/third_party_alert.yaml`](../../infra/observability/third_party_alert.yaml)
* Dev Guide – Partner Integration: [`DEV_GUIDE.md`](../DEV_GUIDE.md)
* ADR liên quan: [`adr-005-observability.md`](./adr-005-observability.md)

---

> “Tích hợp bên ngoài là mắt xích yếu nhất – hãy đo lường và bảo vệ nó đúng cách.”
