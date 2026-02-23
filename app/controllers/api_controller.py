from __future__ import annotations

import math

from flask import Blueprint, current_app, jsonify, render_template, request

from app.extensions import db
from app.models import Payment, PaymentMethod, Provider, Ride, User, Vehicle, VehicleType
from app.utils.auth import role_required, token_auth_required
from app.utils.db import get_or_404
from app.utils.qr import build_vehicle_qr_payload, generate_qr_png
from app.utils.vehicle import apply_battery_drain
from app.api_spec import SPEC
from app.utils.time import as_utc, utcnow


api_bp = Blueprint("api", __name__)


STATUS_MAP = {
    "available": "verfuegbar",
    "in_use": "in_benutzung",
    "maintenance": "wartung",
    "disabled": "deaktiviert",
    "verfuegbar": "verfuegbar",
    "in_benutzung": "in_benutzung",
    "wartung": "wartung",
    "deaktiviert": "deaktiviert",
}


def _normalize_status(status: str | None) -> str | None:
    if status is None:
        return None
    return STATUS_MAP.get(status, status)


@api_bp.route("/token", methods=["POST"])
def issue_token():
    payload = request.get_json(silent=True) or request.form
    email = (payload.get("email") or "").strip().lower()
    password = payload.get("password") or ""
    account_type = payload.get("account_type", "user")

    if account_type == "provider":
        account = Provider.query.filter_by(email=email).first()
    else:
        account = User.query.filter_by(email=email).first()

    if not account or not account.check_password(password):
        return jsonify({"error": "Ungültige Zugangsdaten"}), 401

    token = account.refresh_api_token()
    db.session.commit()
    return jsonify({"token": token, "role": account_type})


@api_bp.route("/users", methods=["POST"])
def create_user():
    payload = request.get_json(silent=True) or {}
    name = (payload.get("name") or "").strip()
    email = (payload.get("email") or "").strip().lower()
    password = payload.get("password") or ""

    if not all([name, email, password]):
        return jsonify({"error": "Name, Email und Passwort sind Pflichtfelder."}), 400
    if User.query.filter_by(email=email).first():
        return jsonify({"error": "E-Mail bereits vergeben."}), 409

    user = User(name=name, email=email)
    user.set_password(password)
    user.refresh_api_token()
    db.session.add(user)
    db.session.commit()
    return jsonify({"user": user.to_dict(), "token": user.api_token}), 201


@api_bp.route("/providers", methods=["POST"])
def create_provider():
    payload = request.get_json(silent=True) or {}
    name = (payload.get("name") or "").strip()
    email = (payload.get("email") or "").strip().lower()
    password = payload.get("password") or ""
    provider_type = payload.get("typ", "firma")

    if not all([name, email, password]):
        return jsonify({"error": "Name, Email und Passwort sind Pflichtfelder."}), 400
    if Provider.query.filter_by(email=email).first():
        return jsonify({"error": "E-Mail bereits vergeben."}), 409

    provider = Provider(name=name, email=email, typ=provider_type)
    provider.set_password(password)
    provider.refresh_api_token()
    db.session.add(provider)
    db.session.commit()
    return jsonify({"provider": provider.to_dict(), "token": provider.api_token}), 201


@api_bp.route("/vehicles", methods=["GET"])
@token_auth_required()
def list_vehicles(account, role):
    query = Vehicle.query
    status = _normalize_status(request.args.get("status"))

    if role == "provider":
        query = query.filter_by(provider_id=account.id)
    elif status:
        query = query.filter_by(status=status)
    else:
        query = query.filter_by(status="verfuegbar")

    vehicles = [vehicle.to_dict() for vehicle in query.all()]
    return jsonify({"data": vehicles})


@api_bp.route("/vehicles", methods=["POST"])
@token_auth_required(["provider"])
def create_vehicle_api(account, role):
    payload = request.get_json(silent=True) or {}
    vehicle_type_name = payload.get("vehicle_type", "E-Scooter")
    status = _normalize_status(payload.get("status")) or "verfuegbar"
    battery_level = float(payload.get("battery_level", 100))
    gps_lat = payload.get("gps_lat")
    gps_long = payload.get("gps_long")
    qr_code = (payload.get("qr_code") or "").strip()

    if not qr_code:
        return jsonify({"error": "QR-Code ist Pflicht."}), 400

    vehicle_type = VehicleType.query.filter_by(name=vehicle_type_name).first()
    if not vehicle_type:
        vehicle_type = VehicleType(name=vehicle_type_name)
        db.session.add(vehicle_type)

    vehicle = Vehicle(
        provider_id=account.id,
        vehicle_type=vehicle_type,
        status=status,
        battery_level=battery_level,
        gps_lat=gps_lat or current_app.config["DEFAULT_LAT"],
        gps_long=gps_long or current_app.config["DEFAULT_LONG"],
        qr_code=qr_code,
    )
    db.session.add(vehicle)
    db.session.commit()
    return jsonify(vehicle.to_dict()), 201


@api_bp.route("/vehicles/<int:vehicle_id>", methods=["GET"])
@token_auth_required()
def vehicle_detail(account, role, vehicle_id: int):
    vehicle = get_or_404(Vehicle, vehicle_id)
    if role == "provider" and vehicle.provider_id != account.id:
        return jsonify({"error": "Keine Berechtigung"}), 403
    return jsonify(vehicle.to_dict())


@api_bp.route("/vehicles/<int:vehicle_id>", methods=["PATCH", "PUT"])
@token_auth_required(["provider"])
def update_vehicle_api(account, role, vehicle_id: int):
    vehicle = get_or_404(Vehicle, vehicle_id)
    if vehicle.provider_id != account.id:
        return jsonify({"error": "Keine Berechtigung"}), 403

    payload = request.get_json(silent=True) or {}
    if "vehicle_type" in payload:
        vehicle_type_name = payload["vehicle_type"]
        vehicle_type = VehicleType.query.filter_by(name=vehicle_type_name).first()
        if not vehicle_type:
            vehicle_type = VehicleType(name=vehicle_type_name)
            db.session.add(vehicle_type)
        vehicle.vehicle_type = vehicle_type
    if "status" in payload:
        vehicle.status = _normalize_status(payload["status"]) or vehicle.status
    if "battery_level" in payload:
        vehicle.battery_level = float(payload["battery_level"])
    if "gps_lat" in payload:
        vehicle.gps_lat = float(payload["gps_lat"])
    if "gps_long" in payload:
        vehicle.gps_long = float(payload["gps_long"])
    db.session.commit()
    return jsonify(vehicle.to_dict())


@api_bp.route("/vehicles/<int:vehicle_id>", methods=["DELETE"])
@token_auth_required(["provider"])
def delete_vehicle_api(account, role, vehicle_id: int):
    vehicle = get_or_404(Vehicle, vehicle_id)
    if vehicle.provider_id != account.id:
        return jsonify({"error": "Keine Berechtigung"}), 403
    db.session.delete(vehicle)
    db.session.commit()
    return jsonify({"status": "deleted"})


@api_bp.route("/rides", methods=["GET"])
@token_auth_required(["user"])
def ride_list(account, role):
    rides = [ride.to_dict() for ride in account.rides.order_by(Ride.start_time.desc()).all()]
    return jsonify({"data": rides})


@api_bp.route("/rides/start", methods=["POST"])
@token_auth_required(["user"])
def start_ride_api(account, role):
    payload = request.get_json(silent=True) or {}
    vehicle_id = payload.get("vehicle_id")
    try:
        vehicle_id_int = int(vehicle_id)
    except (TypeError, ValueError):
        vehicle_id_int = None
    if not vehicle_id_int:
        return jsonify({"error": "vehicle_id ist erforderlich."}), 400
    vehicle = db.session.get(Vehicle, vehicle_id_int)
    if not vehicle or vehicle.status != "verfuegbar":
        return jsonify({"error": "Fahrzeug nicht verfügbar."}), 400

    active_ride = Ride.query.filter_by(user_id=account.id, end_time=None).first()
    if active_ride:
        return jsonify({"error": "Bereits eine aktive Fahrt vorhanden."}), 409

    base_rate = (
        vehicle.vehicle_type.base_rate
        if vehicle.vehicle_type and vehicle.vehicle_type.base_rate is not None
        else current_app.config["BASE_RATE"]
    )
    per_minute_rate = (
        vehicle.vehicle_type.per_minute_rate
        if vehicle.vehicle_type and vehicle.vehicle_type.per_minute_rate is not None
        else current_app.config["PER_MINUTE_RATE"]
    )
    ride = Ride(
        user_id=account.id,
        vehicle_id=vehicle.id,
        base_rate=base_rate,
        per_minute_rate=per_minute_rate,
    )
    vehicle.status = "in_benutzung"
    vehicle.gps_lat = current_app.config["DEFAULT_LAT"]
    vehicle.gps_long = current_app.config["DEFAULT_LONG"]
    db.session.add(ride)
    db.session.commit()
    return jsonify(ride.to_dict()), 201


@api_bp.route("/rides/<int:ride_id>/end", methods=["POST"])
@token_auth_required(["user"])
def end_ride_api(account, role, ride_id: int):
    ride = get_or_404(Ride, ride_id)
    if ride.user_id != account.id or not ride.end_time is None:
        return jsonify({"error": "Diese Fahrt kann nicht beendet werden."}), 400

    payload = request.get_json(silent=True) or {}
    kilometers = float(payload.get("kilometers", 0) or 0)
    payment_method_id = payload.get("payment_method_id")
    payment_method = None
    if payment_method_id:
        payment_method = (
            PaymentMethod.query.filter_by(
                id=payment_method_id, user_id=account.id, is_active=True
            ).first()
        )

    now = utcnow()
    start_time = as_utc(ride.start_time) or now
    minutes = max(1, math.ceil((now - start_time).total_seconds() / 60))
    base_rate = ride.base_rate or current_app.config["BASE_RATE"]
    per_minute_rate = ride.per_minute_rate or current_app.config["PER_MINUTE_RATE"]
    cost = base_rate + minutes * per_minute_rate

    ride.end_time = now
    ride.kilometers = kilometers
    ride.cost = round(cost, 2)
    ride.vehicle.status = "verfuegbar"
    apply_battery_drain(ride.vehicle, minutes, kilometers, current_app.config)

    if payment_method:
        payment = Payment(
            ride_id=ride.id,
            payment_method_id=payment_method.id,
            amount=ride.cost,
            status="bezahlt",
        )
        db.session.add(payment)

    db.session.commit()
    return jsonify(ride.to_dict())


@api_bp.route("/payment-methods", methods=["GET"])
@token_auth_required(["user"])
def list_payment_methods_api(account, role):
    methods = [
        {
            "id": method.id,
            "type": method.method_type,
            "details": method.details,
            "created_at": method.created_at.isoformat() if method.created_at else None,
            "is_active": method.is_active,
        }
        for method in account.payment_methods.filter_by(is_active=True)
        .order_by(PaymentMethod.created_at.desc())
        .all()
    ]
    return jsonify({"data": methods})


@api_bp.route("/payment-methods", methods=["POST"])
@token_auth_required(["user"])
def create_payment_method_api(account, role):
    payload = request.get_json(silent=True) or {}
    method_type = payload.get("method_type", "Kreditkarte")
    details = (payload.get("details") or "").strip()
    if not details:
        return jsonify({"error": "Details sind erforderlich."}), 400
    method = PaymentMethod(user_id=account.id, method_type=method_type, details=details)
    db.session.add(method)
    db.session.commit()
    return (
        jsonify(
            {
                "id": method.id,
                "type": method.method_type,
                "details": method.details,
                "created_at": method.created_at.isoformat() if method.created_at else None,
                "is_active": method.is_active,
            }
        ),
        201,
    )


@api_bp.route("/payment-methods/<int:method_id>", methods=["DELETE"])
@token_auth_required(["user"])
def delete_payment_method_api(account, role, method_id: int):
    method = get_or_404(PaymentMethod, method_id)
    if method.user_id != account.id:
        return jsonify({"error": "Keine Berechtigung"}), 403
    if not method.is_active:
        return jsonify({"status": "already_inactive"})
    method.is_active = False
    db.session.commit()
    return jsonify({"status": "archived"})


@api_bp.route("/vehicle-types", methods=["GET"])
@token_auth_required()
def list_vehicle_types(account, role):
    types = [
        vt.name
        for vt in VehicleType.query.filter_by(is_active=True)
        .order_by(VehicleType.name)
        .all()
    ]
    return jsonify({"data": types})


@api_bp.route("/vehicle-types", methods=["POST"])
@token_auth_required(["provider"])
def create_vehicle_type_api(account, role):
    payload = request.get_json(silent=True) or {}
    name = (payload.get("name") or "").strip()
    if not name:
        return jsonify({"error": "Name ist erforderlich."}), 400
    if VehicleType.query.filter_by(name=name).first():
        return jsonify({"error": "Fahrzeugtyp existiert bereits."}), 409
    vt = VehicleType(name=name)
    db.session.add(vt)
    db.session.commit()
    return jsonify({"name": vt.name}), 201


@api_bp.route("/openapi.json")
def openapi_document():
    return jsonify(SPEC)


@api_bp.route("/docs")
@role_required(["provider"])
def swagger_ui():
    return render_template("api/docs.html")


@api_bp.route("/vehicles/<int:vehicle_id>/qr")
@token_auth_required()
def vehicle_qr(account, role, vehicle_id: int):
    vehicle = get_or_404(Vehicle, vehicle_id)
    if role == "provider" and vehicle.provider_id != account.id:
        return jsonify({"error": "Keine Berechtigung"}), 403
    if role == "user" and vehicle.status != "verfuegbar":
        return jsonify({"error": "Fahrzeug nicht verfügbar"}), 403
    qr_data = build_vehicle_qr_payload(
        current_app.config["BASE_URL"], vehicle.id, vehicle.qr_code
    )
    png = generate_qr_png(qr_data)
    return current_app.response_class(png, mimetype="image/png")
