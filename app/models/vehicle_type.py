from __future__ import annotations

from app.extensions import db


class VehicleType(db.Model):
    __tablename__ = "fahrzeugtyp"

    # Erweiterbar mit Tarifen.
    id = db.Column("fahrzeugtyp_id", db.Integer, primary_key=True)
    name = db.Column("bezeichnung", db.String(100), unique=True, nullable=False)
    base_rate = db.Column("grundpreis", db.Float, default=1.00)
    per_minute_rate = db.Column("minutenpreis", db.Float, default=0.35)
    is_active = db.Column("ist_aktiv", db.Boolean, default=True)

    vehicles = db.relationship("Vehicle", back_populates="vehicle_type", lazy="dynamic")

    def __repr__(self) -> str:  # pragma: no cover
        return "<VehicleType %s>" % self.name
