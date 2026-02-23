from __future__ import annotations

from app.extensions import db
from app.utils.time import utcnow


class Vehicle(db.Model):
    __tablename__ = "fahrzeug"

    # Stammdaten
    id = db.Column("fahrzeug_id", db.Integer, primary_key=True)
    provider_id = db.Column(
        "anbieter_id", db.Integer, db.ForeignKey("verleihanbieter.anbieter_id")
    )
    vehicle_type_id = db.Column(
        "fahrzeugtyp_id",
        db.Integer,
        db.ForeignKey("fahrzeugtyp.fahrzeugtyp_id"),
        nullable=False,
    )
    status = db.Column(db.String(50), default="verfuegbar")
    battery_level = db.Column("akku_status", db.Float, default=100.0)
    gps_lat = db.Column(db.Float, default=0.0)
    gps_long = db.Column(db.Float, default=0.0)
    # QR-Code dient als eindeutiger Unlock-Schluessel
    qr_code = db.Column(db.String(120), unique=True, nullable=False)
    created_at = db.Column("erstellt_am", db.DateTime, default=utcnow)

    # Beziehungen
    provider = db.relationship("Provider", back_populates="vehicles")
    vehicle_type = db.relationship("VehicleType", back_populates="vehicles")
    rides = db.relationship("Ride", back_populates="vehicle", lazy="dynamic")

    def to_dict(self) -> dict:
        vehicle_type_name = self.vehicle_type.name if self.vehicle_type else None
        data = {
            "id": self.id,
            "provider_id": self.provider_id,
            "vehicle_type": vehicle_type_name,
            "vehicle_type_id": self.vehicle_type_id,
            "status": self.status,
            "battery_level": self.battery_level,
            "gps_lat": self.gps_lat,
            "gps_long": self.gps_long,
            "qr_code": self.qr_code,
        }
        return data
