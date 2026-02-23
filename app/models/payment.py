from __future__ import annotations

from datetime import datetime

from app.extensions import db


class PaymentMethod(db.Model):
    __tablename__ = "zahlungsmittel"

    # Zahlungsmittel pro User (soft-delete via is_active).
    id = db.Column("zahlungsmittel_id", db.Integer, primary_key=True)
    user_id = db.Column("nutzer_id", db.Integer, db.ForeignKey("nutzer.nutzer_id"))
    method_type = db.Column("typ", db.String(50), nullable=False)
    details = db.Column(db.String(255), nullable=False)
    is_active = db.Column("ist_aktiv", db.Boolean, default=True)
    created_at = db.Column("erstellt_am", db.DateTime, default=datetime.utcnow)

    # Beziehungen
    user = db.relationship("User", back_populates="payment_methods")
    payments = db.relationship("Payment", back_populates="payment_method")


class Payment(db.Model):
    __tablename__ = "zahlung"

    # Eine Zahlung gehoert immer zu genau einer Ausleihe.
    id = db.Column("zahlung_id", db.Integer, primary_key=True)
    ride_id = db.Column(
        "ausleihe_id", db.Integer, db.ForeignKey("ausleihe.ausleihe_id")
    )
    payment_method_id = db.Column(
        "zahlungsmittel_id", db.Integer, db.ForeignKey("zahlungsmittel.zahlungsmittel_id")
    )
    timestamp = db.Column("zeitpunkt", db.DateTime, default=datetime.utcnow)
    amount = db.Column("betrag", db.Float, nullable=False)
    status = db.Column(db.String(50), default="offen")

    ride = db.relationship("Ride", back_populates="payments")
    payment_method = db.relationship("PaymentMethod", back_populates="payments")

    def to_dict(self) -> dict:
        data = {
            "id": self.id,
            "ride_id": self.ride_id,
            "amount": self.amount,
            "status": self.status,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }
        return data
