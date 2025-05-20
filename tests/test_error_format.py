def test_error_schema_fields(client):
    response = client.get("/non-existent-endpoint")
    assert response.status_code == 404
    body = response.json()
    assert "error_code" in body
    assert "message" in body
    assert "timestamp" in body
    assert "request_id" in body
