from app.utils.qr import build_vehicle_qr_payload


def test_build_vehicle_qr_payload_strips_trailing_slashes():
    payload = build_vehicle_qr_payload("http://localhost:5000/", 42, "unlock-me")
    assert payload == "http://localhost:5000/unlock/42?code=unlock-me"
