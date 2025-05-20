def test_rbac_permission_denied(client):
    response = client.get("/api/v1/secure-endpoint", headers={"Authorization": "Bearer fake_token"})
    assert response.status_code == 403
