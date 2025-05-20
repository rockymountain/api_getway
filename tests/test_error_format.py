import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_error_format_for_not_found(client: AsyncClient):
    """Kiểm tra định dạng lỗi khi gọi đến endpoint không tồn tại."""
    response = await client.get("/api/v1/unknown-endpoint")
    assert response.status_code == 404
    data = response.json()
    assert data["error_code"] == 404
    assert "message" in data
    assert "request_id" in data
    assert "timestamp" in data
