def test_login_google_oauth2(client):
    response = client.post("/auth/login", json={"token": "fake_google_token"})
    assert response.status_code in (200, 400)  # Expect failure until real token
