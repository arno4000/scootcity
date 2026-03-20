from __future__ import annotations

from flask import abort

from app.extensions import db


def get_or_404(model, pk):
    """SQLAlchemy Session.get wrapper that mimics Flask-SQLAlchemy get_or_404."""
    instance = db.session.get(model, pk)
    if instance is None:
        abort(404)
    return instance
