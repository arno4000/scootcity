from __future__ import annotations

from flask import Blueprint, redirect, render_template, request, session, url_for, flash

from app.extensions import db
from app.models import Provider, User


auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm", "")

        if not name or not email or not password:
            flash("Alle Felder sind Pflichtfelder.", "danger")
            return render_template("auth/register.html")

        if password != confirm:
            flash("Passwörter stimmen nicht überein.", "danger")
            return render_template("auth/register.html")

        if User.query.filter_by(email=email).first():
            flash("E-Mail ist bereits registriert.", "danger")
            return render_template("auth/register.html")

        user = User(name=name, email=email)
        user.set_password(password)
        user.refresh_api_token()
        db.session.add(user)
        db.session.commit()
        flash("Registrierung erfolgreich. Bitte melden Sie sich an.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/register.html")


@auth_bp.route("/provider/register", methods=["GET", "POST"])
def provider_register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm", "")
        provider_type = request.form.get("typ", "firma")

        if not name or not email or not password:
            flash("Alle Felder sind Pflichtfelder.", "danger")
            return render_template("auth/provider_register.html")

        if password != confirm:
            flash("Passwörter stimmen nicht überein.", "danger")
            return render_template("auth/provider_register.html")

        if Provider.query.filter_by(email=email).first():
            flash("E-Mail ist bereits vergeben.", "danger")
            return render_template("auth/provider_register.html")

        provider = Provider(name=name, email=email, typ=provider_type)
        provider.set_password(password)
        provider.refresh_api_token()
        db.session.add(provider)
        db.session.commit()
        flash("Verleihanbieter erfolgreich registriert.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/provider_register.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        account_type = request.form.get("account_type", "user")

        if account_type == "provider":
            account = Provider.query.filter_by(email=email).first()
        else:
            account = User.query.filter_by(email=email).first()

        if not account or not account.check_password(password):
            flash("Ungültige Anmeldedaten.", "danger")
        else:
            session.clear()
            session["account_id"] = account.id
            session["role"] = account_type
            session["name"] = account.name
            flash("Willkommen zurück!", "success")
            if account_type == "provider":
                return redirect(url_for("provider.dashboard"))
            return redirect(url_for("user.dashboard"))

    return render_template("auth/login.html")


@auth_bp.route("/logout")
def logout():
    session.clear()
    flash("Sie wurden abgemeldet.", "info")
    return redirect(url_for("user.landing"))
