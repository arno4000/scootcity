from __future__ import annotations

from base64 import b64encode

from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from sqlalchemy import func

from app.extensions import db
from app.models import PaymentMethod, Ride, User, Vehicle
from app.utils.auth import get_current_account, login_required
from app.utils.db import get_or_404
from app.utils.qr import build_vehicle_qr_payload, generate_qr_png
from app.utils.ride_flow import RideFlowError, end_ride_flow, start_ride_flow


user_bp = Blueprint("user", __name__)


@user_bp.route("/")
def landing():
    return render_template("user/landing.html")


@user_bp.route("/dashboard")
@login_required(["user"])
def dashboard():
    # Dashboard-Daten zusammenziehen, damit die View schlank bleibt.
    account, _ = get_current_account()
    available_vehicles = (
        Vehicle.query.filter_by(status="verfuegbar")
        .order_by(Vehicle.battery_level.desc(), Vehicle.created_at.desc())
        .limit(8)
        .all()
    )
    qr_codes = {}
    for vehicle in available_vehicles:
        # QR direkt als Base64 fuer die UI vorbereiten.
        payload = build_vehicle_qr_payload(
            current_app.config["BASE_URL"], vehicle.id, vehicle.qr_code
        )
        qr_codes[vehicle.id] = b64encode(generate_qr_png(payload)).decode("ascii")
    active_ride = Ride.query.filter_by(user_id=account.id, end_time=None).first()
    payment_methods = (
        account.payment_methods.filter_by(is_active=True)
        .order_by(PaymentMethod.created_at.desc())
        .all()
    )
    recent_rides = (
        Ride.query.filter_by(user_id=account.id)
        .order_by(Ride.start_time.desc())
        .limit(5)
        .all()
    )
    total_kilometers = (
        db.session.query(func.coalesce(func.sum(Ride.kilometers), 0.0))
        .filter(Ride.user_id == account.id)
        .scalar()
    )
    total_kilometers = total_kilometers or 0.0
    total_spent = (
        db.session.query(func.coalesce(func.sum(Ride.cost), 0.0))
        .filter(Ride.user_id == account.id)
        .scalar()
    )
    total_spent = total_spent or 0.0
    stats = {
        "rides": Ride.query.filter_by(user_id=account.id).count(),
        "kilometers": round(total_kilometers, 1),
        "spent": round(total_spent, 2),
    }
    return render_template(
        "user/dashboard.html",
        user=account,
        available_vehicles=available_vehicles,
        active_ride=active_ride,
        payment_methods=payment_methods,
        recent_rides=recent_rides,
        stats=stats,
        vehicle_qr_codes=qr_codes,
    )


@user_bp.route("/rides/start", methods=["POST"])
@login_required(["user"])
def start_ride():
    account, _ = get_current_account()
    vehicle_id = request.form.get("vehicle_id")
    try:
        vehicle_pk = int(vehicle_id)
    except (TypeError, ValueError):
        vehicle_pk = None
    vehicle = db.session.get(Vehicle, vehicle_pk) if vehicle_pk else None
    if not vehicle or vehicle.status != "verfuegbar":
        flash("Fahrzeug kann nicht gebucht werden.", "danger")
        return redirect(url_for("user.dashboard"))

    active_ride = Ride.query.filter_by(user_id=account.id, end_time=None).first()
    if active_ride:
        flash("Sie haben bereits eine laufende Fahrt.", "warning")
        return redirect(url_for("user.dashboard"))

    try:
        start_ride_flow(account.id, vehicle, current_app.config)
    except RideFlowError as exc:
        flash(str(exc), "danger")
        return redirect(url_for("user.dashboard"))
    flash("Fahrt gestartet.", "success")
    return redirect(url_for("user.dashboard"))
    

@user_bp.route("/unlock/<int:vehicle_id>", methods=["GET", "POST"])
def unlock_vehicle(vehicle_id: int):
    vehicle = get_or_404(Vehicle, vehicle_id)
    qr_code = request.args.get("code")
    if qr_code and vehicle.qr_code != qr_code:
        flash("Ungültiger QR-Code.", "danger")
        return redirect(url_for("user.landing"))

    account, role = get_current_account()

    if request.method == "POST":
        # Unlock ist nur fuer Fahrer gedacht.
        if role != "user":
            flash("Bitte als Fahrer anmelden.", "warning")
            return redirect(url_for("auth.login"))
        if vehicle.status != "verfuegbar":
            flash("Fahrzeug ist aktuell nicht verfügbar.", "danger")
            return redirect(url_for("user.dashboard"))
        active_ride = Ride.query.filter_by(user_id=account.id, end_time=None).first()
        if active_ride:
            flash("Sie haben bereits eine laufende Fahrt.", "warning")
            return redirect(url_for("user.dashboard"))
        try:
            start_ride_flow(account.id, vehicle, current_app.config)
        except RideFlowError as exc:
            flash(str(exc), "danger")
            return redirect(url_for("user.dashboard"))
        flash("Fahrt gestartet.", "success")
        return redirect(url_for("user.dashboard"))

    return render_template("user/unlock.html", vehicle=vehicle, qr_code=qr_code, account=account, role=role)


@user_bp.route("/rides/<int:ride_id>/end", methods=["POST"])
@login_required(["user"])
def end_ride(ride_id: int):
    account, _ = get_current_account()
    ride = get_or_404(Ride, ride_id)
    if ride.user_id != account.id or not ride.is_active():
        flash("Diese Fahrt kann nicht beendet werden.", "danger")
        return redirect(url_for("user.dashboard"))

    kilometers = float(request.form.get("kilometers", 0) or 0)
    payment_method_id = request.form.get("payment_method_id")
    payment_method = None
    if payment_method_id:
        payment_method = (
            PaymentMethod.query.filter_by(
                id=payment_method_id, user_id=account.id, is_active=True
            ).first()
        )

    try:
        end_ride_flow(ride, kilometers, payment_method, current_app.config)
    except RideFlowError as exc:
        flash(str(exc), "danger")
        return redirect(url_for("user.dashboard"))
    flash("Fahrt beendet und Kosten berechnet.", "success")
    return redirect(url_for("user.dashboard"))


@user_bp.route("/rides/history")
@login_required(["user"])
def ride_history():
    account, _ = get_current_account()
    rides = (
        Ride.query.filter_by(user_id=account.id)
        .order_by(Ride.start_time.desc())
        .all()
    )
    return render_template("user/ride_history.html", rides=rides)


@user_bp.route("/payment-methods", methods=["GET", "POST"])
@login_required(["user"])
def payment_methods():
    account, _ = get_current_account()
    if request.method == "POST":
        method_type = request.form.get("method_type", "Kreditkarte")
        details = request.form.get("details", "").strip()
        redirect_target = request.form.get("next")
        if not details:
            flash("Bitte geben Sie Details zum Zahlungsmittel ein.", "danger")
        else:
            method = PaymentMethod(user_id=account.id, method_type=method_type, details=details)
            db.session.add(method)
            db.session.commit()
            flash("Zahlungsmittel gespeichert.", "success")
            endpoint = "user.dashboard" if redirect_target == "dashboard" else "user.payment_methods"
            return redirect(url_for(endpoint))

    methods = (
        account.payment_methods.filter_by(is_active=True)
        .order_by(PaymentMethod.created_at.desc())
        .all()
    )
    return render_template("user/payment_methods.html", payment_methods=methods)


@user_bp.route("/payment-methods/<int:method_id>/delete", methods=["POST"])
@login_required(["user"])
def delete_payment_method(method_id: int):
    account, _ = get_current_account()
    redirect_target = request.form.get("next")
    method = get_or_404(PaymentMethod, method_id)
    if method.user_id != account.id:
        flash("Keine Berechtigung dieses Zahlungsmittel zu entfernen.", "danger")
        return redirect(url_for("user.payment_methods"))
    if not method.is_active:
        flash("Zahlungsmittel wurde bereits entfernt.", "info")
    else:
        method.is_active = False
        db.session.commit()
        flash("Zahlungsmittel entfernt (nur noch für Historie sichtbar).", "success")

    endpoint = "user.dashboard" if redirect_target == "dashboard" else "user.payment_methods"
    return redirect(url_for(endpoint))
