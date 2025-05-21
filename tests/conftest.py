# conftest.py – Fixture và cấu hình test cho API Gateway DX VAS

import os
import jwt
import pytest
import redis
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
from app.main import app  # Đảm bảo đường dẫn đúng

SECRET_KEY = "test_secret"
ALGORITHM = "HS256"

# Redis cấu hình cho môi trường test
TEST_REDIS_HOST = os.environ.get("TEST_REDIS_HOST", "localhost")
TEST_REDIS_PORT = int(os.environ.get("TEST_REDIS_PORT", 6379))
TEST_REDIS_DB = int(os.environ.get("TEST_REDIS_DB", 1))  # Redis DB riêng cho test

@pytest.fixture(scope="session")
def test_redis_client():
    """Tạo Redis client cho test."""
    try:
        r = redis.Redis(host=TEST_REDIS_HOST, port=TEST_REDIS_PORT, db=TEST_REDIS_DB, decode_responses=True)
        r.ping()
        yield r
    except redis.exceptions.ConnectionError as e:
        pytest.skip(f"Redis test không kết nối được: {e}")

@pytest.fixture(scope="session", autouse=True)
def override_test_settings():
    original_secret_key = os.environ.get("SECRET_KEY")
    original_algorithm = os.environ.get("ALGORITHM")

    os.environ["SECRET_KEY"] = SECRET_KEY
    os.environ["ALGORITHM"] = ALGORITHM
    os.environ["REDIS_HOST"] = TEST_REDIS_HOST
    os.environ["REDIS_PORT"] = str(TEST_REDIS_PORT)
    os.environ["REDIS_DB"] = str(TEST_REDIS_DB)

    yield

    if original_secret_key is None:
        del os.environ["SECRET_KEY"]
    else:
        os.environ["SECRET_KEY"] = original_secret_key

    if original_algorithm is None:
        del os.environ["ALGORITHM"]
    else:
        os.environ["ALGORITHM"] = original_algorithm

@pytest.fixture(scope="module")
def client(override_test_settings):
    with TestClient(app) as c:
        yield c

@pytest.fixture
def reset_rate_limit_for_client_ip(client: TestClient, test_redis_client: redis.Redis):
    """Reset key rate limit trong Redis cho client test."""
    mock_client_ip = "testclient"
    pattern = f"*:{mock_client_ip}:*"
    for key in test_redis_client.scan_iter(pattern):
        print(f"Deleting rate limit key: {key}")
        test_redis_client.delete(key)
    yield

@pytest.fixture
def jwt_token_with_permission():
    payload = {
        "sub": "user_id_123",
        "email": "test@example.com",
        "permissions": ["read:student_info"],
        "exp": datetime.utcnow() + timedelta(minutes=30),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

@pytest.fixture
def jwt_token_without_permission():
    payload = {
        "sub": "user_id_456",
        "email": "test2@example.com",
        "permissions": ["other:permission"],
        "exp": datetime.utcnow() + timedelta(minutes=30),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

# Lưu ý Quan trọng CUỐI CÙNG cho conftest.py:

# KEY PATTERN CHO RATE LIMIT TRONG reset_rate_limit_for_client_ip:
# Cách xác minh:
#   Chạy API Gateway của bạn với thư viện rate limit đã được cấu hình.
#   Thực hiện một vài request để trigger rate limit.
#   Sử dụng redis-cli và lệnh MONITOR để xem chính xác các lệnh được gửi đến Redis, hoặc dùng KEYS "*pattern*" để tìm các key liên quan đến rate limit.
#   Quan sát xem thư viện rate limit (ví dụ: slowapi, fastapi-limiter) tạo ra các key với cấu trúc như thế nào. Chúng thường bao gồm identifier (IP, user ID), scope của rule, và có thể cả timestamp của window.
# Cố gắng làm cho pattern trong reset_rate_limit_for_client_ip càng cụ thể càng tốt để nó chỉ xóa đúng các key rate limit của mock_client_ip cho các endpoint đang được test, mà không ảnh hưởng đến các key khác (ngay cả trong cùng DB test).
# Ví dụ (giả định cho fastapi-limiter): Nếu key có dạng fastapi-limiter:{identifier}:{path_or_scope_name}:{window_start_time}, và bạn muốn reset cho tất cả các window của một path cụ thể: pattern = f"fastapi-limiter:{mock_client_ip}:/api/v1/protected-endpoint:*".