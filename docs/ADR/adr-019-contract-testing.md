# ADR-019: Chiến lược Contract Testing cho API Gateway (DX VAS)

* **Trạng thái**: Đã chấp thuận ✅
* **Ngày**: 02/06/2025
* **Người đề xuất**: Nguyễn Ngọc L (Quality Engineering Lead)
* **Bối cảnh**: Dự án Chuyển đổi số VAS

---

## 📌 Bối cảnh

API Gateway của DX VAS phục vụ nhiều frontend (web, mobile), cũng như tích hợp với bên thứ ba. Khi backend hoặc gateway thay đổi, có nguy cơ phá vỡ hợp đồng (contract) giữa producer (backend) và consumer (client). Vì vậy, cần chiến lược **contract testing** để:

* Đảm bảo mọi thay đổi vẫn tương thích với client đã tồn tại
* Giảm lỗi tích hợp khó debug
* Tự tin triển khai backend và gateway độc lập

---

## 🧠 Quyết định

**Áp dụng chiến lược contract testing dựa trên Pact cho các API nội bộ và bên ngoài, tích hợp kiểm tra tự động trong CI/CD, đồng bộ với OpenAPI Schema.**

---

## 🤝 Thành phần chính

### 1. Phân vai trò contract

* **Producer**: API Gateway (hoặc các backend service được proxy qua)
* **Consumer**: Frontend app, mobile app, external integrators (CRM, Zalo...)
* **Người chịu trách nhiệm tạo contract test phía consumer**: team frontend hoặc tích hợp bên thứ ba, theo hướng dẫn và checklist được cung cấp trong `DEV_GUIDE.md` hoặc `CONTRIBUTING.md`

### 2. Sử dụng Pact để ghi và kiểm tra contract

* Frontend ghi lại **pact file** (expectations)
* Backend/Gateway verify các pact file đó (Pact Provider Verification)
* Pact file lưu trong repo (giai đoạn đầu) hoặc publish lên **Pact Broker** (self-host hoặc SaaS)

### 3. Ánh xạ với OpenAPI

* Pact contract test tập trung vào tương tác cụ thể
* OpenAPI là định nghĩa toàn bộ interface → sync định kỳ để đảm bảo alignment
* Có thể dùng `swagger-mock-validator` hoặc `schemathesis` để kiểm tra contract test có khớp schema
* **Bước này được thực hiện trong CI sau khi pact file được tạo, trước bước provider verification** để sớm phát hiện bất đồng giữa contract và schema chuẩn

### 4. Tích hợp CI/CD

* Mỗi khi backend/gateway cập nhật → CI job thực thi verify contract từ frontend
* Nếu fail → chặn merge / deploy
* Các môi trường `dev`, `staging` được verify với các bản pact gần nhất
* Pact broker dùng tag theo version (v1.0.0, staging, prod) để kiểm soát vòng đời contract

### 5. Consumer-driven Contract

* Hỗ trợ frontend tạo pact từ test/unit hoặc Postman → publish lên broker
* Backend/gateway verify lại expectation đó theo từng release
* Đảm bảo backward compatibility chủ động từ consumer phía client

### 6. Tổ chức repo & versioning

* Pact files được lưu riêng trong folder `/contracts`
* Đặt tên theo: `consumer-provider-version.json`
* Gắn version git hash / release tag để trace được
* **Lưu ý**: khi số lượng consumer tăng, việc lưu pact trong repo có thể gây nặng → ưu tiên nâng cấp lên Pact Broker để quản lý hiệu quả hơn
* Tự động dọn các pact file cũ sau X ngày nếu không dùng

### 7. Triển khai ban đầu

* Áp dụng cho các module ổn định trước (auth, rbac, profile)
* Lưu pact file trong Git repo (giai đoạn đầu)
* Kế hoạch nâng cấp lên **Pact Broker** (GCP VM hoặc Docker hosted)

---

## ✅ Lợi ích

* Phát hiện sớm lỗi giao tiếp giữa frontend ↔ backend
* Dễ CI/CD độc lập giữa team mà vẫn đảm bảo tương thích
* Rút ngắn thời gian debug lỗi tích hợp
* Tăng độ tin cậy khi refactor hoặc thay đổi schema backend

---

## ❌ Rủi ro & Giải pháp

| Rủi ro                                           | Giải pháp                                                  |
| ------------------------------------------------ | ---------------------------------------------------------- |
| Pact file lỗi thời không phản ánh client thực tế | Đồng bộ từ test thật + hạn sử dụng + cleanup tự động       |
| Contract test giả định behavior không thực tế    | Tạo pact từ test thật hoặc Postman collection thực tế      |
| Khó duy trì khi có nhiều consumer                | Tự động hoá broker + tagging + phân quyền truy cập rõ ràng |

---

## 🔄 Các lựa chọn đã loại bỏ

* **Chỉ kiểm tra schema (OpenAPI)**: Không kiểm tra dynamic behavior / payload thực tế
* **Test end-to-end thủ công**: Mất thời gian, khó scale
* **Không test gì cả**: Dễ gây lỗi breaking production

---

## 📎 Tài liệu liên quan

* Pact documentation: [https://docs.pact.io/](https://docs.pact.io/)
* Folder contract: [`/contracts`](../../contracts)
* CI: [`.github/workflows/contract-test.yml`](../../.github/workflows/contract-test.yml)
* ADR liên quan: [`adr-018-api-governance.md`](./adr-018-api-governance.md)

---

> “Contract là lời hứa giữa các hệ thống – test để lời hứa không bị phá vỡ.”
