from __future__ import annotations

from typing import Mapping

from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from app.extensions import db
from app.models import Payment, PaymentMethod, Ride, Vehicle
from app.utils.time import as_local_time, timenow
from app.utils.vehicle import apply_battery_drain


class RideFlowError(Exception):
    pass


def _should_use_stored_procedures() -> bool:
    bind = db.session.get_bind()
    if bind is None:
        return False
    return bind.dialect.name in {"mysql", "mariadb"}


def _is_missing_procedure(exc: DBAPIError) -> bool:
    message = str(getattr(exc, "orig", exc)).lower()
    return "procedure" in message and "does not exist" in message


def _is_nullable_payment_procedure_bug(exc: DBAPIError) -> bool:
    message = str(getattr(exc, "orig", exc)).lower()
    return "zahlungsmittel_id" in message and "cannot be null" in message


def _db_error_message(exc: DBAPIError, fallback: str) -> str:
    message = str(getattr(exc, "orig", exc)).lower()
    if "fahrzeug nicht verfuegbar" in message:
        return "Fahrzeug nicht verfügbar."
    return fallback


def _start_ride_orm(user_id: int, vehicle: Vehicle, config: Mapping[str, float]) -> Ride:
    base_rate = (
        vehicle.vehicle_type.base_rate
        if vehicle.vehicle_type and vehicle.vehicle_type.base_rate is not None
        else config["BASE_RATE"]
    )
    per_minute_rate = (
        vehicle.vehicle_type.per_minute_rate
        if vehicle.vehicle_type and vehicle.vehicle_type.per_minute_rate is not None
        else config["PER_MINUTE_RATE"]
    )
    ride = Ride(
        user_id=user_id,
        vehicle_id=vehicle.id,
        base_rate=base_rate,
        per_minute_rate=per_minute_rate,
    )
    vehicle.status = "in_benutzung"
    vehicle.gps_lat = config["DEFAULT_LAT"]
    vehicle.gps_long = config["DEFAULT_LONG"]
    db.session.add(ride)
    return ride


def start_ride_flow(user_id: int, vehicle: Vehicle, config: Mapping[str, float]) -> Ride:
    if _should_use_stored_procedures():
        try:
            db.session.execute(
                text("CALL sp_fahrt_starten(:nutzer_id, :fahrzeug_id)"),
                {"nutzer_id": user_id, "fahrzeug_id": vehicle.id},
            )
            ride_id = db.session.execute(text("SELECT LAST_INSERT_ID()")).scalar()
            ride = db.session.get(Ride, int(ride_id)) if ride_id else None
            if ride is None:
                ride = (
                    Ride.query.filter_by(user_id=user_id, vehicle_id=vehicle.id, end_time=None)
                    .order_by(Ride.id.desc())
                    .first()
                )
            if ride is None:
                raise RideFlowError("Fahrt konnte nicht gestartet werden.")

            # GPS bleibt App-seitig gesetzt, weil es aus Config stammt.
            db.session.refresh(vehicle)
            vehicle.gps_lat = config["DEFAULT_LAT"]
            vehicle.gps_long = config["DEFAULT_LONG"]
            db.session.commit()
            return ride
        except DBAPIError as exc:
            db.session.rollback()
            if _is_missing_procedure(exc):
                ride = _start_ride_orm(user_id, vehicle, config)
                db.session.commit()
                return ride
            raise RideFlowError(_db_error_message(exc, "Fahrt konnte nicht gestartet werden.")) from exc

    ride = _start_ride_orm(user_id, vehicle, config)
    db.session.commit()
    return ride


def _end_ride_orm(
    ride: Ride,
    kilometers: float,
    payment_method: PaymentMethod | None,
    config: Mapping[str, float],
) -> Ride:
    now = timenow()
    start_time = as_local_time(ride.start_time) or now
    minutes = _minutes_floor(start_time, now)
    base_rate = ride.base_rate or config["BASE_RATE"]
    per_minute_rate = ride.per_minute_rate or config["PER_MINUTE_RATE"]
    cost = base_rate + minutes * per_minute_rate

    ride.end_time = now
    ride.kilometers = kilometers
    ride.cost = round(cost, 2)
    ride.vehicle.status = "verfuegbar"
    apply_battery_drain(ride.vehicle, minutes, kilometers, config)

    if payment_method:
        payment = Payment(
            ride_id=ride.id,
            payment_method_id=payment_method.id,
            amount=ride.cost,
            status="bezahlt",
        )
        db.session.add(payment)
    return ride


def _minutes_floor(start_time, end_time) -> int:
    if not start_time or not end_time:
        return 1
    delta_seconds = max(0, int((end_time - start_time).total_seconds()))
    return max(1, delta_seconds // 60)


def end_ride_flow(
    ride: Ride,
    kilometers: float,
    payment_method: PaymentMethod | None,
    config: Mapping[str, float],
) -> Ride:
    if _should_use_stored_procedures():
        try:
            db.session.execute(
                text(
                    "CALL sp_fahrt_beenden(:ausleihe_id, :kilometer, :zahlungsmittel_id)"
                ),
                {
                    "ausleihe_id": ride.id,
                    "kilometer": kilometers,
                    "zahlungsmittel_id": payment_method.id if payment_method else None,
                },
            )
            db.session.refresh(ride)
            db.session.refresh(ride.vehicle)
            start_time = as_local_time(ride.start_time)
            end_time = as_local_time(ride.end_time)
            minutes = _minutes_floor(start_time, end_time)
            apply_battery_drain(ride.vehicle, minutes, kilometers, config)
            db.session.commit()
            return ride
        except DBAPIError as exc:
            db.session.rollback()
            # Migration-safe fallback fuer bestehende alte Procedure-Versionen.
            if _is_missing_procedure(exc) or (
                payment_method is None and _is_nullable_payment_procedure_bug(exc)
            ):
                ride = _end_ride_orm(ride, kilometers, payment_method, config)
                db.session.commit()
                return ride
            raise RideFlowError(_db_error_message(exc, "Fahrt konnte nicht beendet werden.")) from exc

    ride = _end_ride_orm(ride, kilometers, payment_method, config)
    db.session.commit()
    return ride
