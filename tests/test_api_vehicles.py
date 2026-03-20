import pytest

from app.extensions import db
from app.models import Provider, Vehicle, VehicleType
from tests.helpers import auth_header


# T09 – Fahrzeugliste nach Rolle und Status
def test_vehicle_listing_filters_by_role_and_status(
    app, client, user, provider, vehicle_type
):
    with app.app_context():
        vt = db.session.get(VehicleType, vehicle_type)
        other_provider = Provider(name="Second", email="second@example.com", typ="firma")
        other_provider.set_password("secret456")
        other_provider.refresh_api_token()
        db.session.add(other_provider)
        db.session.flush()

        vehicles = [
            Vehicle(
                provider_id=provider["id"],
                vehicle_type=vt,
                status="verfuegbar",
                battery_level=92,
                qr_code="qr-001",
            ),
            Vehicle(
                provider_id=provider["id"],
                vehicle_type=vt,
                status="wartung",
                battery_level=50,
                qr_code="qr-002",
            ),
            Vehicle(
                provider_id=other_provider.id,
                vehicle_type=vt,
                status="verfuegbar",
                battery_level=66,
                qr_code="qr-003",
            ),
        ]
        db.session.add_all(vehicles)
        db.session.commit()
        other_token = other_provider.api_token

    user_response = client.get("/api/vehicles", headers=auth_header(user["token"]))
    assert user_response.status_code == 200
    user_data = user_response.get_json()["data"]
    assert {vehicle["status"] for vehicle in user_data} == {"verfuegbar"}
    assert len(user_data) == 2  # beide verfügbaren Fahrzeuge, unabhängig vom Anbieter

    provider_response = client.get(
        "/api/vehicles", headers=auth_header(provider["token"])
    )
    assert provider_response.status_code == 200
    provider_data = provider_response.get_json()["data"]
    assert len(provider_data) == 2
    assert {vehicle["provider_id"] for vehicle in provider_data} == {provider["id"]}

    maintenance_response = client.get(
        "/api/vehicles?status=wartung", headers=auth_header(user["token"])
    )
    assert maintenance_response.status_code == 200
    maintenance_data = maintenance_response.get_json()["data"]
    assert len(maintenance_data) == 1
    assert maintenance_data[0]["status"] == "wartung"

    other_provider_response = client.get(
        "/api/vehicles", headers=auth_header(other_token)
    )
    assert other_provider_response.status_code == 200
    other_data = other_provider_response.get_json()["data"]
    assert len(other_data) == 1
    assert other_data[0]["provider_id"] == other_provider.id


# T10 – Fahrzeug anlegen inkl. neuem Typ
def test_provider_can_create_vehicle_via_api(app, client, provider):
    payload = {
        "vehicle_type": "Cargo-Bike",
        "status": "verfuegbar",
        "battery_level": 88,
        "gps_lat": 47.39,
        "gps_long": 8.51,
        "qr_code": "cargo-qr",
    }
    response = client.post(
        "/api/vehicles", headers=auth_header(provider["token"]), json=payload
    )
    assert response.status_code == 201
    data = response.get_json()
    assert data["vehicle_type"] == "Cargo-Bike"
    assert data["status"] == "verfuegbar"
    assert data["battery_level"] == pytest.approx(88.0)
    with app.app_context():
        created = db.session.get(Vehicle, data["id"])
        assert created.qr_code == "cargo-qr"
        assert created.vehicle_type.name == "Cargo-Bike"
