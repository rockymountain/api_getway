# ADR-005: Thiết kế chiến lược Observability cho API Gateway (DX VAS)

* **Trạng thái**: Đã chấp thuận ✅
* **Ngày**: 19/05/2025
* **Người đề xuất**: Trần Thị B (DevOps)
* **Bối cảnh**: Dự án Chuyển đổi số VAS

---

## 📌 Bối cảnh

API Gateway là điểm trung tâm xử lý xác thực, phân quyền, định tuyến và forward request đến backend. Vì đây là thành phần “single entry point”, việc **theo dõi, cảnh báo và truy vết lỗi (observability)** là rất quan trọng:

* Ghi nhận đầy đủ log của request và lỗi
* Theo dõi độ trễ, tần suất lỗi, request rate
* Hỗ trợ phân tích khi có sự cố hoặc phản hồi chậm từ backend
* Hỗ trợ tracing khi hệ thống mở rộng ra nhiều microservice

---

## 🧠 Quyết định

**Áp dụng mô hình Observability dựa trên Logging + Metrics + Tracing, tích hợp với Google Cloud Logging, Monitoring và OpenTelemetry.**

---

## 🔍 Chiến lược triển khai

### 1. Logging (Structured)

* Dùng `python-json-logger` để log ra định dạng JSON
* Log các thông tin sau với mỗi request:

  * `timestamp`, `request_id`, `correlation_id`, `method`, `path`, `user_id`, `status_code`, `latency_ms`
  * Nếu lỗi: log cả `error_code`, `permission_required`, `reason`
* `correlation_id` được tạo nếu chưa có, và được truyền giữa các hệ thống nếu cần tách biệt với `request_id`
* Log gửi lên **Google Cloud Logging** tự động qua Cloud Run

### 2. Metrics

* Dùng `Prometheus FastAPI Instrumentator` hoặc middleware custom

  * Ưu tiên dùng **OpenTelemetry Metrics API** nếu đã tích hợp tracing để thống nhất pipeline export lên Cloud Monitoring
* Các metrics cần thu thập:

  * `request_count` theo path/method/status
  * `request_latency_ms`
  * `error_count`
  * `auth_failures`, `rbac_denied`

### 3. Tracing (Distributed Tracing)

* Dùng OpenTelemetry để gắn `trace_id`, `span_id`, `correlation_id`
* Forward trace context theo chuẩn W3C: `traceparent`, `tracestate`
* Mọi request đến backend (SIS, CRM...) sẽ giữ nguyên trace context qua header
* Tích hợp Google Cloud Trace hoặc Jaeger để theo dõi toàn bộ lifecycle của request

### 4. Alerting

* Thiết lập cảnh báo qua Cloud Monitoring:

  * Error rate > 5% trong 5 phút
  * Latency trung bình > 1000ms
  * Số request 4xx/5xx tăng đột biến
  * Sử dụng CPU > 85% hoặc Memory > 80% trên Cloud Run > 5 phút
* Gửi alert qua email, Slack (Webhook), Google Chat

---

## ✅ Lợi ích

* Theo dõi sức khỏe hệ thống real-time
* Dễ truy tìm nguyên nhân sự cố với trace-id hoặc correlation\_id
* Phát hiện nhanh các bottleneck hoặc cấu hình sai
* Giúp frontend/dev/qa debug hiệu quả hơn và rút ngắn thời gian phản hồi

---

## ❌ Rủi ro & Giải pháp

| Rủi ro                        | Giải pháp                                                 |
| ----------------------------- | --------------------------------------------------------- |
| Quá nhiều log không cần thiết | Dùng log level phù hợp: `INFO`, `WARNING`, `ERROR`        |
| Tăng độ trễ do log hoặc trace | Log async, sampling tracing (ví dụ 10%) nếu cần           |
| Alert false-positive          | Đặt ngưỡng thông minh, cooldown và alert condition cụ thể |

---

## 🔄 Các lựa chọn đã loại bỏ

* **Không log structured**: Khó filter và phân tích sau này
* **Chỉ log lỗi, không log thành công**: Thiếu baseline và khó xác định vấn đề theo chiều dọc
* **Push metrics thủ công bằng script**: Không phù hợp với Cloud-native pipeline và không thống nhất với tracing

---

## 📎 Tài liệu liên quan

* Dev Guide – Observability section: [`DEV_GUIDE.md`](../DEV_GUIDE.md)
* Middleware log & metrics: [`utils/logging.py`](../../utils/logging.py), `metrics.py`
* OpenTelemetry docs: [https://opentelemetry.io/](https://opentelemetry.io/)
* W3C Trace Context: [https://www.w3.org/TR/trace-context/](https://www.w3.org/TR/trace-context/)
* ADR trước: [`adr-004-api-versioning.md`](./adr-004-api-versioning.md)

---

> “Bạn không thể khắc phục điều bạn không đo lường – hãy quan sát mọi thứ có ý nghĩa.”
