def test_issue_token_success_and_failure(client, user):
    response = client.post(
        "/api/token",
        json={"email": user["email"], "password": "secret123", "account_type": "user"},
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data["role"] == "user"
    assert data["token"]
    assert len(data["token"]) == 32

    bad_credentials = client.post(
        "/api/token",
        json={"email": user["email"], "password": "wrong", "account_type": "user"},
    )
    assert bad_credentials.status_code == 401
    assert "token" not in bad_credentials.get_json()


def test_create_user_endpoint_enforces_required_fields(client):
    payload = {"name": "New Driver", "email": "new@example.com", "password": "pw12345"}
    response = client.post("/api/users", json=payload)
    assert response.status_code == 201
    data = response.get_json()
    assert data["user"]["email"] == payload["email"]
    assert data["token"]

    duplicate = client.post("/api/users", json=payload)
    assert duplicate.status_code == 409
    assert duplicate.get_json()["error"] == "E-Mail bereits vergeben."


def test_create_user_missing_field_returns_400(client):
    response = client.post("/api/users", json={"name": "No Mail"})
    assert response.status_code == 400
    assert "Pflichtfelder" in response.get_json()["error"]
