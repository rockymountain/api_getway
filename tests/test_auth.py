import pytest
from httpx import AsyncClient

# Giả sử bạn có một fixture 'client' trong conftest.py
@pytest.mark.asyncio
async def test_health_check_auth_endpoints_exist(client: AsyncClient):
    """Kiểm tra các endpoint auth có tồn tại không (cơ bản, không payload)."""
    response = await client.options("/api/v1/auth/login")
    assert response.status_code != 404
    response = await client.options("/api/v1/auth/refresh")
    assert response.status_code != 404

@pytest.mark.asyncio
async def test_login_with_invalid_google_token_format(client: AsyncClient):
    """Kiểm tra phản hồi khi gửi token Google sai định dạng."""
    response = await client.post("/api/v1/auth/login", json={"code": "invalid"})
    assert response.status_code == 400 or response.status_code == 401
    data = response.json()
    assert "message" in data
    assert "error_code" in data
    assert "request_id" in data
    assert "timestamp" in data
