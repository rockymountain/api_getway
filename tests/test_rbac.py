import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_rbac_permission_denied(client: AsyncClient):
    """Kiểm tra khi user không có quyền truy cập endpoint bảo vệ."""
    headers = {"Authorization": "Bearer dummy_token_with_no_permission"}
    response = await client.get("/api/v1/protected-resource", headers=headers)
    assert response.status_code == 403
    data = response.json()
    assert data["error_code"] == 403
    assert "message" in data
    assert "request_id" in data
    assert "timestamp" in data
