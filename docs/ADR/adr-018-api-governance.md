# ADR-018: Chiến lược API Governance cho API Gateway (DX VAS)

* **Trạng thái**: Đã chấp thuận ✅
* **Ngày**: 01/06/2025
* **Người đề xuất**: Nguyễn Minh Q (Tech Lead Backend)
* **Bối cảnh**: Dự án Chuyển đổi số VAS

---

## 📌 Bối cảnh

API Gateway là điểm truy cập chính cho toàn bộ frontend và third-party tích hợp. Việc phát triển API mới và duy trì API cũ cần có một hệ thống governance rõ ràng để:

* Đảm bảo chất lượng và tính nhất quán của API
* Dễ dàng mở rộng và duy trì lâu dài
* Hạn chế rủi ro gây lỗi khi nhiều team cùng phát triển
* Đảm bảo backward compatibility và tài liệu rõ ràng

---

## 🧠 Quyết định

**Áp dụng chiến lược API Governance chuẩn hóa dựa trên OpenAPI 3.1, kết hợp quy ước đặt tên, kiểm tra schema linting CI, versioning rõ ràng, tự động hoá tài liệu và tuân thủ nguyên tắc thiết kế API hiện đại.**

---

## 📏 Thành phần của chiến lược

### 1. Sử dụng OpenAPI 3.1 (YAML)

* Mỗi module (auth, user, rbac...) có một file schema OpenAPI riêng
* Các schema riêng có thể sử dụng `$ref` để liên kết giữa các phần tử (components) hoặc được **tổng hợp lại bằng tool như `redocly bundle` để tạo schema toàn cục** cho API Gateway
* Tích hợp với Swagger UI & ReDoc từ FastAPI `/docs`, `/redoc`
* Tự động xuất ra từ code (Pydantic model + route) và chỉnh thủ công khi cần override

### 2. Lint & validate OpenAPI trong CI

* Sử dụng `speccy`, `openapi-cli`, `redocly lint` hoặc `oas-tools` để kiểm tra:

  * Tên path, tag, description đầy đủ
  * Thiếu type, enum, example, status code
  * Duplicate path hoặc thiếu version prefix
* Hỗ trợ quy tắc linting **tuỳ chỉnh nội bộ** nếu team có yêu cầu riêng (ví dụ: yêu cầu tất cả response đều có `trace_id`)
* CI chặn merge nếu có lỗi OpenAPI lint nghiêm trọng

### 3. Quy ước đặt tên & cấu trúc

* Path dạng RESTful chuẩn:

  * `GET /students/{id}`
  * `POST /students`
  * `GET /schools/{school_id}/classes`
* Đặt tên schema theo PascalCase: `StudentProfile`, `CreateTeacherRequest`
* Enum rõ ràng, type cụ thể, ví dụ:

  ```yaml
  status:
    type: string
    enum: [active, inactive, locked]
  ```

### 4. Versioning API

* Dùng prefix `/api/v1/`, `/api/v2/`
* Không thay đổi hành vi breaking trong cùng 1 version
* Khi nâng version:

  * Tạo route mới song song (v2)
  * V2 có thể reuse schema nhưng cần override lại OpenAPI description rõ ràng

### 5. Tự động hoá tài liệu & changelog

* Sử dụng `redocly`, `docusaurus` hoặc `sphinx` để publish API docs
* Mỗi API schema thay đổi → update changelog.md (semi-auto script hoặc git diff)
* Có trang public hoặc nội bộ cho tài liệu kỹ thuật REST API

### 6. Review & phê duyệt schema

* Bất kỳ API mới hoặc thay đổi API đều cần review bởi API Lead hoặc Backend Tech Lead
* Checklist review:

  * RESTful design
  * Tên chuẩn, status code hợp lý
  * Trả lỗi đúng format (có message + code + trace\_id)
  * Có mô tả (`description`) và ví dụ (`example`) trong response

### 7. API Design Principles (tham chiếu từ DEV\_GUIDE.md)

* Stateless: mỗi request phải đủ thông tin để xử lý độc lập
* Idempotent: các method như `PUT`, `DELETE` phải idempotent
* Sử dụng đúng HTTP verbs (GET, POST, PUT, DELETE...)
* Hỗ trợ phân trang (`limit`, `offset`), lọc (`filter[]`) và sắp xếp (`sort_by`) theo quy ước
* Trả lỗi rõ ràng và có chuẩn hóa JSON

---

## ✅ Lợi ích

* API rõ ràng, dễ hiểu và dễ duy trì
* Giảm lỗi khi các team frontend/backend phối hợp
* Giúp dễ dàng mở rộng API trong tương lai mà không phá vỡ client cũ
* Hỗ trợ frontend, mobile, bên thứ ba tích hợp API dễ hơn
* Tài liệu kỹ thuật luôn cập nhật, nhất quán với codebase

---

## ❌ Rủi ro & Giải pháp

| Rủi ro                        | Giải pháp                                                      |
| ----------------------------- | -------------------------------------------------------------- |
| Schema không đồng bộ với code | Tự động xuất OpenAPI từ FastAPI + kiểm tra CI                  |
| API vỡ backward compatibility | Kiểm tra schema diff + version rõ ràng + test tự động contract |
| Team chưa quen governance     | Checklist, training, example schema + CI lint giúp enforce     |

---

## 🔄 Các lựa chọn đã loại bỏ

* **Không versioning**: Dẫn đến breaking changes không kiểm soát được
* **Viết tài liệu API bằng tay hoàn toàn**: Không đảm bảo sync với code, lỗi dễ xảy ra
* **Không enforce lint/check OpenAPI**: Gây lỗi khi phát hành hoặc tích hợp

---

## 📎 Tài liệu liên quan

* OpenAPI schema: [`schemas/openapi/`](../../schemas/openapi/)
* CI Linting: [`.github/workflows/api-lint.yml`](../../.github/workflows/api-lint.yml)
* Dev Guide – API Standards & Design Principles: [`DEV_GUIDE.md`](../DEV_GUIDE.md)
* ADR liên quan: [`adr-014-multi-env-config.md`](./adr-014-multi-env-config.md)

---

> “API không chỉ là một điểm kết nối – nó là giao diện chính giữa con người và hệ thống.”
