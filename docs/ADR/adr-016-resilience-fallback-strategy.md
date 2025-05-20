# ADR-016: Chiến lược Resilience và Fallback cho API Gateway (DX VAS)

* **Trạng thái**: Đã chấp thuận ✅
* **Ngày**: 30/05/2025
* **Người đề xuất**: Trần Quốc H (Backend Lead)
* **Bối cảnh**: Dự án Chuyển đổi số VAS

---

## 📌 Bối cảnh

API Gateway là điểm trung tâm điều phối request từ frontend đến các backend như SIS, CRM, LMS. Một số backend có thể tạm thời chậm, lỗi, hoặc không sẵn sàng. Để duy trì trải nghiệm người dùng và độ ổn định hệ thống, cần xây dựng **chiến lược resilience và fallback rõ ràng** tại gateway.

---

## 🧠 Quyết định

**Áp dụng chiến lược Resilience & Fallback tại API Gateway với các kỹ thuật: timeout, retry có kiểm soát, circuit breaker, và graceful fallback logic cho từng nhóm API.**

---

## 🛡 Thành phần của chiến lược

### 1. Timeout chuẩn hóa

* Áp dụng timeout tối đa cho request outbound tới backend (qua httpx):

  * `connect_timeout = 1s`
  * `read_timeout = 3s`
* Có thể override theo backend đặc biệt (ví dụ: CRM sync 5s)

### 2. Retry có kiểm soát (idempotent only)

* Áp dụng retry với method `GET`, `HEAD` nếu lỗi là network error hoặc 5xx (trừ 501)
* Sử dụng thư viện [`tenacity`](https://tenacity.readthedocs.io/) hoặc logic retry tích hợp trong httpx
* Số lần retry: tối đa 2
* Delay giữa lần retry: exponential backoff (e.g., 100ms, 300ms)

### 3. Circuit Breaker (sơ khởi)

* Nếu 50% request tới backend A lỗi trong vòng 1 phút → **đóng circuit trong 2 phút**
* Trong thời gian đóng: trả lỗi fallback (503 + message chuẩn hóa)
* Sau thời gian đó: thử 1 request → nếu thành công → mở lại circuit
* Cơ chế này được thực hiện tạm thời qua Redis hoặc memory (FastAPI middleware)
* **Hướng nâng cấp**: sử dụng thư viện như [`pybreaker`](https://pypi.org/project/pybreaker/) hoặc dịch vụ chuyên biệt (Cloud Trace + metric-based circuit breaker) để hỗ trợ lưu trạng thái resilient theo vùng/lifecycle container

### 4. Graceful Fallback

* Cho một số API phụ trợ (non-critical), trả về dữ liệu default/cached nếu backend lỗi:

  * Ví dụ: `/profile/avatar` → fallback URL ảnh mặc định
  * `/recommendation` → trả danh sách trống hoặc thông báo "Đang tải..."
* Khi dùng fallback/cached, **có header `X-Fallback: true` và thông báo rõ ràng trên giao diện người dùng** để minh bạch và giảm nhầm lẫn
* Không áp dụng fallback cho API cập nhật dữ liệu (PUT/POST quan trọng)

### 5. Logging & Metric

* Log riêng khi retry, timeout, hoặc circuit breaker được kích hoạt
* Metric quan trọng:

  * `gateway_backend_latency_ms`
  * `gateway_backend_error_rate`
  * `circuit_open_count`
* Tích hợp cảnh báo nếu:

  * Latency tăng > 300% baseline
  * Circuit breaker kích hoạt > 5 lần/phút

### 6. Kiểm thử resilience tự động

* Sử dụng `chaos testing` đơn giản với mô phỏng backend lỗi (return 503)
* Kiểm tra hệ thống có:

  * Trả đúng fallback/error
  * Không retry quá giới hạn
  * Log đủ thông tin để debug

---

## ✅ Lợi ích

* Giảm downtime khi backend gặp sự cố
* Bảo vệ người dùng khỏi lỗi lan rộng
* Cải thiện hiệu năng tổng thể bằng cách giới hạn retry quá mức
* Dễ quan sát và kiểm thử hành vi resilience qua log/metrics

---

## ❌ Rủi ro & Giải pháp

| Rủi ro                                    | Giải pháp                                                                            |
| ----------------------------------------- | ------------------------------------------------------------------------------------ |
| Circuit breaker kích hoạt sai             | Tuning threshold hợp lý + window sliding + test offline trước                        |
| Fallback không phù hợp với business logic | Chỉ dùng fallback cho endpoint rõ ràng là non-critical và hiển thị rõ với người dùng |
| Retry gây quá tải backend                 | Áp dụng retry cho idempotent API + exponential backoff + giới hạn tối đa 2 lần       |

---

## 🔄 Các lựa chọn đã loại bỏ

* **Không retry hoặc fallback**: gây lỗi toàn bộ hệ thống frontend nếu 1 backend gặp sự cố
* **Retry tất cả method (POST/PUT)**: nguy cơ lặp thao tác, sai dữ liệu
* **Dùng service mesh (Istio)**: quá phức tạp với kiến trúc Cloud Run hiện tại

---

## 📎 Tài liệu liên quan

* Middleware circuit breaker: [`utils/circuit_breaker.py`](../../utils/circuit_breaker.py)
* Dev Guide – Resilience & Fault Tolerance: [`DEV_GUIDE.md`](../DEV_GUIDE.md)
* ADR liên quan: [`adr-005-observability.md`](./adr-005-observability.md)

---

> “Không hệ thống nào tránh được lỗi – resilience là cách chúng ta ứng xử khi lỗi xảy ra.”
