import pytest
from sqlalchemy.pool import StaticPool

from app import create_app
from app.config import Config
from app.extensions import db
from app.models import Provider, User, Vehicle, VehicleType


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite://"
    SQLALCHEMY_ENGINE_OPTIONS = {
        "poolclass": StaticPool,
        "connect_args": {"check_same_thread": False},
    }
    SECRET_KEY = "tests-keep-me"


@pytest.fixture
def app():
    app = create_app(TestConfig)
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def user(app):
    with app.app_context():
        user = User(name="Driver One", email="driver@example.com")
        user.set_password("secret123")
        user.refresh_api_token()
        db.session.add(user)
        db.session.commit()
        return {"id": user.id, "email": user.email, "token": user.api_token}


@pytest.fixture
def provider(app):
    with app.app_context():
        provider = Provider(name="Provider AG", email="provider@example.com", typ="firma")
        provider.set_password("verysecret")
        provider.refresh_api_token()
        db.session.add(provider)
        db.session.commit()
        return {"id": provider.id, "email": provider.email, "token": provider.api_token}


@pytest.fixture
def vehicle_type(app):
    with app.app_context():
        vt = VehicleType(name="E-Scooter", base_rate=1.8, per_minute_rate=0.42)
        db.session.add(vt)
        db.session.commit()
        return vt.id


@pytest.fixture
def vehicle(app, provider, vehicle_type):
    with app.app_context():
        vt = db.session.get(VehicleType, vehicle_type)
        vehicle = Vehicle(
            provider_id=provider["id"],
            vehicle_type=vt,
            status="verfuegbar",
            battery_level=100.0,
            gps_lat=47.0,
            gps_long=8.0,
            qr_code="qr-base",
        )
        db.session.add(vehicle)
        db.session.commit()
        return vehicle.id
