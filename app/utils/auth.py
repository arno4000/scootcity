from __future__ import annotations

from functools import wraps
from typing import Optional, Sequence, Tuple

from flask import abort, flash, redirect, request, session, url_for

from app.models import Provider, User

def _resolve_logged_in_account() -> Tuple[Optional[object], Optional[str]]:
    role = session.get("role")
    account_id = session.get("account_id")
    if not role or not account_id:
        return None, None
    if role == "user":
        return User.query.get(account_id), role
    if role == "provider":
        return Provider.query.get(account_id), role
    return None, None


def login_required(allowed_roles: Optional[Sequence[str]] = None):
    def decorator(view_func):
        @wraps(view_func)
        def wrapped(*args, **kwargs):
            # Session pruefen, sonst Login erzwingen.
            account, role = _resolve_logged_in_account()
            if not account:
                flash("Bitte melden Sie sich zuerst an.", "warning")
                return redirect(url_for("auth.login"))

            if allowed_roles and role not in allowed_roles:
                flash("Sie besitzen keine Berechtigung für diesen Bereich.", "danger")
                return redirect(url_for("user.dashboard" if role == "user" else "provider.dashboard"))

            return view_func(*args, **kwargs)

        return wrapped

    return decorator


def get_current_account() -> Tuple[Optional[object], Optional[str]]:
    return _resolve_logged_in_account()


def resolve_token(token: str) -> Tuple[Optional[object], Optional[str]]:
    if not token:
        return None, None
    user = User.query.filter_by(api_token=token).first()
    if user:
        return user, "user"
    provider = Provider.query.filter_by(api_token=token).first()
    if provider:
        return provider, "provider"
    return None, None


def token_auth_required(allowed_roles: Optional[Sequence[str]] = None):
    def decorator(view_func):
        @wraps(view_func)
        def wrapped(*args, **kwargs):
            # API-Auth: Bearer-Token aus Header ziehen.
            auth_header = request.headers.get("Authorization", "")
            token = auth_header[7:] if auth_header.startswith("Bearer ") else None
            if not token:
                abort(401, description="Bearer Token fehlt")

            account, role = resolve_token(token)
            if not account:
                abort(401, description="Token ist ungültig")

            if allowed_roles and role not in allowed_roles:
                abort(403, description="Keine Berechtigung")

            return view_func(account, role, *args, **kwargs)

        return wrapped

    return decorator


def role_required(allowed_roles: Optional[Sequence[str]] = None):
    def decorator(view_func):
        @wraps(view_func)
        def wrapped(*args, **kwargs):
            account, role = get_current_account()
            if not account:
                return redirect(url_for("auth.login"))
            if allowed_roles and role not in allowed_roles:
                abort(403)
            return view_func(*args, **kwargs)

        return wrapped

    return decorator
