from __future__ import annotations

import secrets

from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db
from app.utils.time import timenow


class User(db.Model):
    __tablename__ = "nutzer"

    # Basis-Stammdaten
    id = db.Column("nutzer_id", db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    # Passwort wird gehasht gespeichert (nie im Klartext)
    password_hash = db.Column(db.String(255), nullable=False)
    api_token = db.Column(db.String(64), unique=True, index=True)
    created_at = db.Column("erstellt_am", db.DateTime, default=timenow)

    # Beziehungen
    rides = db.relationship("Ride", back_populates="user", lazy="dynamic")
    payment_methods = db.relationship(
        "PaymentMethod", back_populates="user", lazy="dynamic"
    )

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def refresh_api_token(self) -> str:
        # Neuer Token pro Login/Refresh
        token = secrets.token_hex(16)
        self.api_token = token
        return token

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
