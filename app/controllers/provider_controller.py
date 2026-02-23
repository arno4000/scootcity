from __future__ import annotations

from base64 import b64encode

from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for

from app.extensions import db
from app.models import Provider, Vehicle, VehicleType
from app.utils.auth import get_current_account, login_required
from app.utils.qr import build_vehicle_qr_payload, generate_qr_png


provider_bp = Blueprint("provider", __name__, url_prefix="/provider")


@provider_bp.route("/dashboard")
@login_required(["provider"])
def dashboard():
    # Flotten-Uebersicht inkl. QR-Codes fuer die UI.
    provider, _ = get_current_account()
    vehicles = provider.vehicles.order_by(Vehicle.created_at.desc()).all()
    qr_codes = {}
    for vehicle in vehicles:
        payload = build_vehicle_qr_payload(
            current_app.config["BASE_URL"], vehicle.id, vehicle.qr_code
        )
        qr_codes[vehicle.id] = b64encode(generate_qr_png(payload)).decode("ascii")
    return render_template("provider/dashboard.html", provider=provider, vehicles=vehicles, qr_codes=qr_codes)


@provider_bp.route("/vehicles/new", methods=["GET", "POST"])
@login_required(["provider"])
def create_vehicle():
    provider, _ = get_current_account()
    vehicle_types = _get_vehicle_types()
    # Default-Typ bestimmen, damit das Formular nicht leer wirkt.
    if "E-Scooter" in vehicle_types:
        default_type = "E-Scooter"
    elif vehicle_types:
        default_type = vehicle_types[0]
    else:
        default_type = "E-Scooter"
    selected_type = request.form.get("vehicle_type", default_type)
    if request.method == "POST":
        vehicle_type_name = selected_type
        status = request.form.get("status", "verfuegbar")
        battery = float(request.form.get("battery_level", 100) or 100)
        lat = float(request.form.get("gps_lat", 0) or 0)
        long = float(request.form.get("gps_long", 0) or 0)
        qr_code = request.form.get("qr_code", "").strip()

        if not qr_code:
            flash("QR-Code wird benötigt.", "danger")
        else:
            vehicle_type = VehicleType.query.filter_by(name=vehicle_type_name).first()
            if not vehicle_type:
                vehicle_type = VehicleType(name=vehicle_type_name)
                db.session.add(vehicle_type)
            vehicle = Vehicle(
                provider_id=provider.id,
                vehicle_type=vehicle_type,
                status=status,
                battery_level=battery,
                gps_lat=lat,
                gps_long=long,
                qr_code=qr_code,
            )
            db.session.add(vehicle)
            db.session.commit()
            flash("Fahrzeug erfolgreich hinzugefügt.", "success")
            return redirect(url_for("provider.dashboard"))

    return render_template(
        "provider/vehicle_form.html",
        provider=provider,
        vehicle_types=vehicle_types,
        selected_type=selected_type,
    )


@provider_bp.route("/vehicle-types", methods=["POST"])
@login_required(["provider"])
def add_vehicle_type():
    # Kleines Admin-Feature: Typenliste erweitern.
    name = request.form.get("new_vehicle_type", "").strip()
    if not name:
        flash("Bitte einen Fahrzeugtyp eingeben.", "danger")
        return redirect(url_for("provider.create_vehicle"))
    existing = VehicleType.query.filter_by(name=name).first()
    if existing:
        flash("Fahrzeugtyp existiert bereits.", "warning")
    else:
        vt = VehicleType(name=name)
        db.session.add(vt)
        db.session.commit()
        flash("Fahrzeugtyp gespeichert.", "success")
    return redirect(url_for("provider.create_vehicle"))


@provider_bp.route("/vehicles/<int:vehicle_id>/update", methods=["POST"])
@login_required(["provider"])
def update_vehicle(vehicle_id: int):
    provider, _ = get_current_account()
    vehicle = Vehicle.query.get_or_404(vehicle_id)
    if vehicle.provider_id != provider.id:
        flash("Keine Berechtigung für dieses Fahrzeug.", "danger")
        return redirect(url_for("provider.dashboard"))

    new_type = request.form.get("vehicle_type")
    if new_type:
        existing_type = VehicleType.query.filter_by(name=new_type).first()
        if not existing_type:
            existing_type = VehicleType(name=new_type)
            db.session.add(existing_type)
        vehicle.vehicle_type = existing_type

    vehicle.status = request.form.get("status", vehicle.status)
    vehicle.battery_level = float(request.form.get("battery_level", vehicle.battery_level) or vehicle.battery_level)
    vehicle.gps_lat = float(request.form.get("gps_lat", vehicle.gps_lat) or vehicle.gps_lat)
    vehicle.gps_long = float(request.form.get("gps_long", vehicle.gps_long) or vehicle.gps_long)
    db.session.commit()
    flash("Fahrzeug aktualisiert.", "success")
    return redirect(url_for("provider.dashboard"))


def _get_vehicle_types() -> list[str]:
    # Defaults einfuegen, falls in der DB noch nichts ist.
    types = [
        vt.name
        for vt in VehicleType.query.filter_by(is_active=True)
        .order_by(VehicleType.name)
        .all()
    ]
    defaults = ["E-Scooter", "E-Bike"]
    for default in defaults:
        if default not in types:
            types.append(default)
    return sorted(types)
