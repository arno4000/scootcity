from __future__ import annotations

from app.extensions import db
from app.utils.time import utcnow


class Ride(db.Model):
    __tablename__ = "ausleihe"

    # Verknuepft User und Fahrzeug in einer Fahrt.
    id = db.Column("ausleihe_id", db.Integer, primary_key=True)
    user_id = db.Column("nutzer_id", db.Integer, db.ForeignKey("nutzer.nutzer_id"))
    vehicle_id = db.Column(
        "fahrzeug_id", db.Integer, db.ForeignKey("fahrzeug.fahrzeug_id")
    )
    start_time = db.Column("startzeit", db.DateTime, default=utcnow)
    end_time = db.Column("endzeit", db.DateTime)
    kilometers = db.Column("kilometer", db.Float, default=0.0)
    cost = db.Column("kosten", db.Float, default=0.0)
    base_rate = db.Column("grundpreis", db.Float, default=0.0)
    per_minute_rate = db.Column("minutenpreis", db.Float, default=0.0)

    # Beziehungen
    user = db.relationship("User", back_populates="rides")
    vehicle = db.relationship("Vehicle", back_populates="rides")
    payments = db.relationship("Payment", back_populates="ride")

    def is_active(self) -> bool:
        return self.end_time is None

    def to_dict(self) -> dict:
        data = {
            "id": self.id,
            "user_id": self.user_id,
            "vehicle_id": self.vehicle_id,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "kilometers": self.kilometers,
            "cost": self.cost,
            "base_rate": self.base_rate,
            "per_minute_rate": self.per_minute_rate,
        }
        return data
