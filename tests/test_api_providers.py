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
    assert duplicate.status_code == 409
    assert duplicate.get_json()["error"] == "E-Mail bereits vergeben."


def test_create_provider_duplicate_name_returns_409(client):
    first = client.post(
        "/api/providers",
        json={
            "name": "FleetOps",
            "email": "fleetops-1@example.com",
            "password": "providerpw",
            "typ": "firma",
        },
    )
    assert first.status_code == 201

    duplicate_name = client.post(
        "/api/providers",
        json={
            "name": "FleetOps",
            "email": "fleetops-2@example.com",
            "password": "providerpw",
            "typ": "firma",
        },
    )
    assert duplicate_name.status_code == 409
    assert duplicate_name.get_json()["error"] == "Anbietername bereits vergeben."
