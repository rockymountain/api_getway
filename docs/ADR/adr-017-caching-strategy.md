# ADR-017: Chiến lược Caching cho API Gateway (DX VAS)

* **Trạng thái**: Đã chấp thuận ✅
* **Ngày**: 31/05/2025
* **Người đề xuất**: Nguyễn Thị T (Backend Architect)
* **Bối cảnh**: Dự án Chuyển đổi số VAS

---

## 📌 Bối cảnh

API Gateway xử lý lượng lớn request đến các backend (SIS, CRM, LMS...). Nhiều endpoint có dữ liệu ổn định trong thời gian ngắn (profile, config, avatar, dropdown lists...). Nếu không có cache, hệ thống sẽ:

* Lãng phí tài nguyên backend với request lặp lại
* Gây độ trễ không cần thiết
* Làm giảm khả năng mở rộng của toàn hệ thống

Cần có chiến lược caching hợp lý ở gateway nhằm tăng hiệu suất và giảm tải.

---

## 🧠 Quyết định

**Áp dụng chiến lược caching theo tầng tại API Gateway gồm in-memory (short-term) và Redis (shared), kết hợp cache header chuẩn để tận dụng CDN tương lai.**

---

## 🔧 Thành phần của chiến lược

### 1. In-memory cache (local, short-lived)

* Dùng `lru_cache` hoặc `cachetools.TTLCache`
* Dành cho các endpoint rất nhẹ, dữ liệu không thay đổi thường xuyên:

  * `/config/options`
  * `/profile/avatar`
* TTL: 30s–60s
* **Lưu ý:** Cloud Run có thể chạy nhiều instance → mỗi instance có cache riêng biệt → in-memory cache **không đồng bộ giữa các instance** → chấp nhận cache không nhất quán tạm thời để đổi lấy tốc độ và giảm tải Redis

### 2. Redis cache (shared, medium-lived)

* Dành cho các dữ liệu chia sẻ giữa nhiều instance:

  * `/user/profile`
  * `/school/calendar`
* TTL: 5 phút (tuỳ loại)
* Key convention: `cache:{env}:{path}:{user_id}` hoặc `cache:calendar:school_id`
* **Cache invalidation:**

  * Khi có PUT/POST cập nhật, xóa key cụ thể hoặc theo pattern
  * Có thể dùng pub/sub của Redis để các instance được thông báo và xóa cache local liên quan
  * Cần phối hợp logic để tránh race-condition giữa cache và write-through

### 3. HTTP cache header chuẩn (Cache-Control)

* Trả header `Cache-Control: public, max-age=60` cho endpoint phù hợp
* Hỗ trợ tương lai tích hợp CDN / API Gateway layer (Cloud CDN)
* Tuỳ theo `auth`/`public`, quyết định private/public cache được hay không

### 4. Cache fallback (tùy chọn resilience)

* Nếu backend lỗi, có thể dùng dữ liệu cache cũ (expired nhưng còn usable)
* Áp dụng cho dữ liệu không critical (ví dụ: avatar, menu)
* Gắn header `X-Cache-Fallback: true` để frontend biết là dữ liệu không mới nhất

### 5. Bypass cache khi cần

* Cho phép client gửi `Cache-Control: no-cache` hoặc `X-Bypass-Cache: true`
* Hữu ích khi admin cần force reload dữ liệu hoặc debug

### 6. Giảm hiện tượng cache stampede

* Khi nhiều request cùng đến key vừa hết hạn:

  * Dùng lock nhẹ (Redis SETNX) để chỉ cho 1 request refresh từ backend
  * Các request khác có thể:

    * Chờ (spin lock, TTL timeout)
    * Hoặc dùng lại giá trị cache cũ thêm 1–2s nữa nếu còn usable
* Chiến lược này giảm nguy cơ backend bị đánh hội đồng do cache miss đồng loạt

### 7. Logging và metrics

* Ghi log `cache_hit`, `cache_miss`, `cache_expired`
* Metric:

  * `cache_hit_ratio`
  * `redis_cache_latency`
  * `cache_fallback_count`
* Alert nếu:

  * Cache hit rate < 60% trong 5 phút
  * Redis latency > 100ms

---

## ✅ Lợi ích

* Giảm tải đáng kể cho backend
* Cải thiện tốc độ phản hồi cho user
* Tăng khả năng chịu lỗi và ổn định trong thời gian backend gián đoạn
* Chuẩn bị cho CDN/API caching nếu scale lớn hơn

---

## ❌ Rủi ro & Giải pháp

| Rủi ro                              | Giải pháp                                                                            |
| ----------------------------------- | ------------------------------------------------------------------------------------ |
| Cache stale gây nhầm lẫn người dùng | TTL ngắn + cho phép bypass + hiển thị rõ fallback khi có                             |
| Dữ liệu private bị cache sai        | Phân biệt cache theo user\_id / scope rõ ràng + không dùng public cache nếu cần auth |
| Redis down → toàn bộ cache mất      | Cho phép fallback in-memory + degrade mềm nếu cần                                    |
| Cache stampede khi cache hết hạn    | Dùng locking hoặc grace window để giảm hiệu ứng herd                                 |

---

## 🔄 Các lựa chọn đã loại bỏ

* **Không cache gì cả**: Gây quá tải backend, tăng độ trễ
* **Chỉ dùng CDN layer (Cloud CDN)**: Không xử lý được cache theo user\_id hoặc auth scope
* **Cache toàn bộ response mọi thứ**: Dễ gây lỗi logic, stale data khó debug

---

## 📎 Tài liệu liên quan

* Cache middleware: [`utils/cache.py`](../../utils/cache.py)
* Dev Guide – Performance & Caching: [`DEV_GUIDE.md`](../DEV_GUIDE.md)
* ADR liên quan: [`adr-016-resilience-fallback-strategy.md`](./adr-016-resilience-fallback-strategy.md)

---

> “Cache tốt không chỉ giúp tăng tốc – mà còn là một lớp resilience cho hệ thống.”
