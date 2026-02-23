from types import SimpleNamespace

from app.utils.vehicle import apply_battery_drain


def test_apply_battery_drain_respects_minimum_and_caps_at_zero():
    vehicle = SimpleNamespace(battery_level=50.0)
    config = {
        "BATTERY_DRAIN_PER_KM": 2.0,
        "BATTERY_DRAIN_PER_MINUTE": 0.5,
        "MIN_BATTERY_DRAIN": 5.0,
    }

    apply_battery_drain(vehicle, minutes=1, kilometers=0.5, config=config)
    assert vehicle.battery_level == 45.0  # Mindestverbrauch greift

    apply_battery_drain(vehicle, minutes=400, kilometers=120, config=config)
    assert vehicle.battery_level == 0.0
