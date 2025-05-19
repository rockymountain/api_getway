**Tài liệu Dev Guide – Từ 0 đến Hero – Dự án Chuyển đổi số VAS**

---

## **I. Mục tiêu của tài liệu**

Hướng dẫn chi tiết dành cho developer mới bắt đầu tham gia vào hệ thống DX VAS, bao gồm quy trình thiết lập môi trường, coding convention, làm việc nhóm, testing, CI/CD, bảo mật và vận hành. Tài liệu này giúp đảm bảo mọi thành viên đều có thể làm việc hiệu quả và thống nhất.

---

## **II. Thiết lập môi trường phát triển**

### **1. Công cụ cần cài đặt**

* Python >= 3.10
* Docker & Docker Compose
* Git
* PostgreSQL client (psql hoặc DBeaver)
* Redis client (redis-cli hoặc TablePlus)
* VSCode hoặc PyCharm

### **2. Clone dự án và cấu hình ban đầu**

```bash
git clone https://github.com/vas-org/api-gateway.git
cd api-gateway
cp .env.example .env
```

#### **Pre-commit hooks (Legendary Touch)**

```bash
pip install pre-commit
pre-commit install
```

File `.pre-commit-config.yaml` nên bao gồm:

```yaml
repos:
  - repo: https://github.com/psf/black
    rev: stable
    hooks:
      - id: black
  - repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
      - id: flake8
  - repo: https://github.com/PyCQA/isort
    rev: 5.12.0
    hooks:
      - id: isort
```

### **3. (Tùy chọn) Tạo môi trường ảo nếu không dùng Docker**

```bash
python -m venv venv
source venv/bin/activate  # Trên Windows: .\venv\Scripts\activate
pip install -r requirements.txt
```

Nếu có file riêng `requirements-dev.txt`:

```bash
pip install -r requirements-dev.txt
```

### **4. Chạy dự án local bằng Docker Compose**

```bash
docker-compose up --build
```

Truy cập FastAPI docs tại `http://localhost:8000/docs`

### **5. prestart.sh (Legendary Touch)**

File `prestart.sh`:

```bash
#!/bin/bash
# ./wait-for-postgres.sh $DB_HOST $DB_PORT --timeout=30
alembic upgrade head
exec uvicorn app.main:app --host 0.0.0.0 --port 8080
```

Nên được gọi từ Dockerfile như sau:

```Dockerfile
CMD ["/bin/bash", "prestart.sh"]
```

---

## **III. Cấu trúc dự án (Backend)**

```
auth/
rbac/
notify/
utils/
  ├── db.py
  ├── cache.py
  ├── exceptions.py
  ├── logging.py
  └── security.py
migrations/
  ├── versions/
  ├── env.py
  └── script.py.mako
main.py
config.py
prestart.sh
alembic.ini
requirements.in
requirements.txt
requirements-dev.txt
Dockerfile
docker-compose.yml
.pre-commit-config.yaml
.gitignore
README.md
```

---

## **(các mục còn lại giữ nguyên như phiên bản trước)**

*(Phần còn lại không thay đổi, đã đạt cấp độ “Legendary Hero”).*
