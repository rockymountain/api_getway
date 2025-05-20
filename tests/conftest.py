import os
import jwt
import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
from app.main import app  # Cập nhật đúng đường dẫn

SECRET_KEY = "test_secret"
ALGORITHM = "HS256"

@pytest.fixture(scope="session", autouse=True)
def override_test_settings():
    original_secret_key = os.environ.get("SECRET_KEY")
    original_algorithm = os.environ.get("ALGORITHM")
    os.environ["SECRET_KEY"] = SECRET_KEY
    os.environ["ALGORITHM"] = ALGORITHM
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
def client():
    with TestClient(app) as c:
        yield c

@pytest.fixture
def jwt_token_with_permission():
    payload = {
        "sub": "user_id_123",
        "email": "test@example.com",
        "permissions": ["read:student_info"],
        "exp": datetime.utcnow() + timedelta(minutes=30),
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return token

@pytest.fixture
def jwt_token_without_permission():
    payload = {
        "sub": "user_id_456",
        "email": "test2@example.com",
        "permissions": ["other:permission"],
        "exp": datetime.utcnow() + timedelta(minutes=30),
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return token