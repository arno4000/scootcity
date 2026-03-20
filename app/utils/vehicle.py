from __future__ import annotations

from typing import Mapping

from app.models import Vehicle


def apply_battery_drain(vehicle: Vehicle, minutes: int, kilometers: float, config: Mapping[str, float]) -> None:
    # Akku-Logik zentral halten, damit sie nicht im Controller dupliziert wird.
    per_km = float(config.get("BATTERY_DRAIN_PER_KM", 1.2))
    per_minute = float(config.get("BATTERY_DRAIN_PER_MINUTE", 0.4))
    min_drain = float(config.get("MIN_BATTERY_DRAIN", 3.0))
    km = kilometers or 0.0
    drain = max(min_drain, (km * per_km) + (minutes * per_minute))
    new_level = max(0.0, vehicle.battery_level - drain)
    vehicle.battery_level = round(new_level, 1)
