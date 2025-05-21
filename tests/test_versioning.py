from fastapi.testclient import TestClient

# Đảm bảo API Gateway của bạn thực sự có endpoint /api/v1/health
def test_versioned_endpoint_exists(client: TestClient):
    \"\"\"Kiểm tra endpoint với prefix /api/v1 tồn tại.\"\"\"
    response = client.get("/api/v1/health")
    assert response.status_code != 404

def test_version_prefix_required(client: TestClient):
    \"\"\"Kiểm tra rằng không có prefix version thì bị từ chối.\"\"\"
    response = client.get("/health")
    assert response.status_code in [404, 400]