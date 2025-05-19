# ADR-020: Chiến lược API Lifecycle & Deprecation cho API Gateway (DX VAS)

* **Trạng thái**: Đã chấp thuận ✅
* **Ngày**: 03/06/2025
* **Người đề xuất**: Nguyễn Văn D (API Governance Champion)
* **Bối cảnh**: Dự án Chuyển đổi số VAS

---

## 📌 Bối cảnh

API Gateway đóng vai trò trung tâm tích hợp và phục vụ các client nội bộ, frontend, mobile app, và bên thứ ba. Khi hệ thống phát triển, một số endpoint sẽ cần được:

* **Thêm mới** (với feature mới)
* **Cập nhật** (non-breaking hoặc breaking)
* **Ngừng sử dụng** (deprecated)

Cần có một chiến lược rõ ràng để quản lý **API Lifecycle** giúp:

* Giao tiếp nhất quán về thay đổi với các bên sử dụng API
* Đảm bảo backward compatibility hợp lý
* Tránh phá vỡ client đang dùng version cũ

---

## 🧠 Quyết định

**Áp dụng quy trình quản lý API lifecycle với các trạng thái rõ ràng (experimental, stable, deprecated, retired), kết hợp với versioning, thời gian cảnh báo deprecation rõ ràng, và tài liệu cập nhật tự động.**

---

## 📘 Trạng thái API Lifecycle

| Trạng thái     | Mô tả                                                                    |
| -------------- | ------------------------------------------------------------------------ |
| `experimental` | API thử nghiệm, có thể thay đổi, không khuyến nghị dùng trong production |
| `stable`       | API đã ổn định, backward compatible trong cùng major version             |
| `deprecated`   | API chuẩn bị ngừng dùng, có khuyến cáo thay thế rõ ràng                  |
| `retired`      | API đã bị xoá hoàn toàn (trả 410 Gone hoặc không còn route)              |

* Trạng thái hiển thị trong OpenAPI:

  * `deprecated: true` (chuẩn OpenAPI cho operation/parameter)
  * `x-api-status: experimental|stable|retired` (custom extension cho trạng thái chi tiết hơn)
* Swagger UI / ReDoc có thể hiện thị các trạng thái đặc biệt bằng banner hoặc highlight

---

## 🔀 Quy trình deprecate API

1. **Đánh dấu `deprecated` trong OpenAPI + changelog**
2. **Thông báo qua changelog, Slack nội bộ, email đối tác**
3. **Thời gian duy trì (sunset)**:

   * Ít nhất **90 ngày** kể từ ngày deprecated
4. **Trả header HTTP**:

   ```http
   Deprecation: true
   Sunset: Tue, 10 Sep 2025 00:00:00 GMT
   Link: <https://docs.dxvas.vn/api/v2/students>; rel="successor-version"
   Warning: 299 - "API v1/students sẽ bị ngừng vào ngày 10/09/2025, vui lòng chuyển sang v2"
   ```
5. **Sau khi hết hạn**:

   * Có thể trả `410 Gone` hoặc redirect đến endpoint mới (nếu phù hợp)
   * Gỡ khỏi docs public nhưng vẫn giữ changelog

---

## 📐 Kết hợp versioning

* Tất cả API đều có prefix version: `/api/v1/`, `/api/v2/`
* Khi có breaking change → tạo version mới (v2) song song
* Deprecate version cũ sau khi client đã nâng cấp ổn định

---

## 📚 Tài liệu và thông báo

* Tự động tạo changelog từ Git diff hoặc OpenAPI commit message
* Có `/changelog.md` và `/api/lifecycle.json` mô tả trạng thái theo thời gian
* Trang `/docs/deprecation` liệt kê API sắp bị gỡ
* Gửi thông báo deprecation định kỳ (email, Slack #api-client)

---

## ✅ Lợi ích

* Giao tiếp rõ ràng, tránh phá vỡ hệ thống client đang hoạt động
* Quản lý version hiệu quả, đồng hành cùng phát triển sản phẩm
* Hạn chế technical debt từ API "ma" hoặc không còn duy trì
* Hỗ trợ audit, compliance và cập nhật tài liệu tự động

---

## ❌ Rủi ro & Giải pháp

| Rủi ro                                   | Giải pháp                                                                                                                                                               |
| ---------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Client không biết API bị deprecated      | Gửi email + Slack + log warning + header HTTP rõ ràng                                                                                                                   |
| Team backend gỡ nhầm API còn đang dùng   | API không được retire nếu chưa hết `sunset window` + **thống kê usage qua Cloud Logging/Monitoring**, xuất log request theo path → alert nếu có request sau ngày sunset |
| Không kiểm soát được API "ẩn" trong code | Review OpenAPI + CI fail nếu có route không khai báo + xóa stale route                                                                                                  |

---

## 🔄 Các lựa chọn đã loại bỏ

* **Không versioning**: dễ breaking client, không rollback được
* **Xoá API mà không cảnh báo**: gây outage cho client
* **Chỉ viết deprecation trong changelog**: không đủ visibility cho frontend / mobile / đối tác

---

## 📎 Tài liệu liên quan

* Changelog: [`/docs/changelog.md`](../../docs/changelog.md)
* API Lifecycle JSON: [`/api/lifecycle.json`](../../api/lifecycle.json)
* Dev Guide – API Versioning & Deprecation: [`DEV_GUIDE.md`](../DEV_GUIDE.md)
* ADR liên quan: [`adr-018-api-governance.md`](./adr-018-api-governance.md)

---

> “Không phải API nào cũng sống mãi – hãy quản lý vòng đời API như một công dân có trách nhiệm.”
