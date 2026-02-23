def test_create_provider_endpoint_validates_and_returns_token(client):
    payload = {
        "name": "New Provider",
        "email": "new-provider@example.com",
        "password": "providerpw",
        "typ": "firma",
    }
    response = client.post("/api/providers", json=payload)
    assert response.status_code == 201
    data = response.get_json()
    assert data["provider"]["email"] == payload["email"]
    assert data["token"]

    duplicate = client.post("/api/providers", json=payload)
    print(duplicate.status_code)
    assert duplicate.status_code == 409
    assert duplicate.get_json()["error"] == "E-Mail bereits vergeben."
