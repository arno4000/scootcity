import pytest

from app.extensions import db
from app.models import PaymentMethod, Ride, Vehicle
from tests.helpers import auth_header


def test_start_and_end_ride_flow(app, client, user, provider, vehicle):
    headers = auth_header(user["token"])

    start_resp = client.post(
        "/api/rides/start", headers=headers, json={"vehicle_id": vehicle}
    )
    assert start_resp.status_code == 201
    ride_data = start_resp.get_json()
    ride_id = ride_data["id"]
    assert ride_data["vehicle_id"] == vehicle

    with app.app_context():
        vehicle_obj = db.session.get(Vehicle, vehicle)
        assert vehicle_obj.status == "in_benutzung"

    payment_resp = client.post(
        "/api/payment-methods",
        headers=headers,
        json={"method_type": "Mastercard", "details": "****1111"},
    )
    payment_method_id = payment_resp.get_json()["id"]

    end_resp = client.post(
        f"/api/rides/{ride_id}/end",
        headers=headers,
        json={"kilometers": 2, "payment_method_id": payment_method_id},
    )
    assert end_resp.status_code == 200
    finished = end_resp.get_json()
    assert finished["end_time"] is not None
    assert finished["cost"] == pytest.approx(2.22)

    with app.app_context():
        vehicle_obj = db.session.get(Vehicle, vehicle)
        assert vehicle_obj.status == "verfuegbar"
        assert vehicle_obj.battery_level == 97.0

        ride_obj = db.session.get(Ride, ride_id)
        assert ride_obj.cost == pytest.approx(2.22)
        payment = db.session.get(PaymentMethod, payment_method_id)
        assert payment.is_active is True


def test_start_ride_rejects_unavailable_vehicle(app, client, user, provider, vehicle):
    headers = auth_header(user["token"])

    client.post("/api/rides/start", headers=headers, json={"vehicle_id": vehicle})

    second_attempt = client.post(
        "/api/rides/start", headers=headers, json={"vehicle_id": vehicle}
    )
    assert second_attempt.status_code == 400
    assert "nicht verfügbar" in second_attempt.get_json()["error"]
