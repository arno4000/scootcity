from datetime import timedelta

import pytest

from app.extensions import db
from app.models import Payment, PaymentMethod, Ride, Vehicle
from app.utils.time import timenow
from tests.helpers import auth_header


# T05 – Fahrt starten und beenden mit Zahlungsmittel
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


# T06 – Fahrtstart bei belegtem Fahrzeug
def test_start_ride_rejects_unavailable_vehicle(app, client, user, provider, vehicle):
    headers = auth_header(user["token"])

    client.post("/api/rides/start", headers=headers, json={"vehicle_id": vehicle})

    second_attempt = client.post(
        "/api/rides/start", headers=headers, json={"vehicle_id": vehicle}
    )
    assert second_attempt.status_code == 400
    assert "nicht verfügbar" in second_attempt.get_json()["error"]


# T07 – Fahrtende ohne Zahlungsmittel
def test_end_ride_without_payment_method_fails(app, client, user, provider, vehicle):
    headers = auth_header(user["token"])
    start_resp = client.post(
        "/api/rides/start", headers=headers, json={"vehicle_id": vehicle}
    )
    ride_id = start_resp.get_json()["id"]

    # Attempting to end ride without payment method should fail
    end_resp = client.post(
        f"/api/rides/{ride_id}/end",
        headers=headers,
        json={"kilometers": 1.2},
    )
    assert end_resp.status_code == 400
    assert "payment_method_id ist erforderlich" in end_resp.get_json()["error"]

    # Ride should still be active
    with app.app_context():
        ride_obj = db.session.get(Ride, ride_id)
        assert ride_obj.end_time is None


# T08 – Abrechnung mit Minutenrundung
def test_end_ride_uses_full_minutes_flooring_in_sqlite_fallback(
    app, client, user, provider, vehicle
):
    headers = auth_header(user["token"])
    
    # Create a payment method first
    payment_resp = client.post(
        "/api/payment-methods",
        headers=headers,
        json={"method_type": "Visa", "details": "****9999"},
    )
    payment_method_id = payment_resp.get_json()["id"]
    
    start_resp = client.post(
        "/api/rides/start", headers=headers, json={"vehicle_id": vehicle}
    )
    ride_id = start_resp.get_json()["id"]

    with app.app_context():
        ride = db.session.get(Ride, ride_id)
        ride.start_time = timenow() - timedelta(seconds=61)
        db.session.commit()

    end_resp = client.post(
        f"/api/rides/{ride_id}/end",
        headers=headers,
        json={"kilometers": 0, "payment_method_id": payment_method_id},
    )
    assert end_resp.status_code == 200
    finished = end_resp.get_json()
    assert finished["cost"] == pytest.approx(2.22)
