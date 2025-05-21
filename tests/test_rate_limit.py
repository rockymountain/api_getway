# tests/test_rate_limit.py
import pytest
from fastapi.testclient import TestClient

def test_rate_limit_exceeded(client: TestClient, reset_rate_limit_for_client_ip):
    """Mô phỏng việc vượt giới hạn rate limit và kiểm tra phản hồi."""
    # Giả định endpoint này được bảo vệ bởi rate limit và giới hạn được đặt thấp cho môi trường test

    # Gửi nhiều request để kích hoạt rate limit (ví dụ: limit là 3, gửi 5 lần)
    for _ in range(5):
        response = client.get("/api/v1/protected-endpoint")
        if response.status_code == 429:
            break
    else:
        pytest.fail("Rate limit (429) was not triggered sau nhiều request.")

    assert response.status_code == 429
    data = response.json()
    assert data.get("error_code") == 429
    assert "Too Many Requests" in data.get("message", "") or "rate limit" in data.get("message", "").lower()
    assert "request_id" in data
    assert "timestamp" in data
    if "Retry-After" in response.headers:
        assert int(response.headers["Retry-After"]) > 0