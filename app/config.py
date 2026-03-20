import os


class Config:
    # Zentrale Defaults; in Prod via ENV ueberschreibbar.
    SECRET_KEY = os.environ.get("SECRET_KEY", "super-secret-change-me")
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        "mysql+pymysql://root:sml12345@localhost/scooter_plattform",
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    BASE_URL = os.environ.get("BASE_URL", "http://0.0.0.0:5000")
    BASE_RATE = float(os.environ.get("BASE_RATE", 1.5))
    PER_MINUTE_RATE = float(os.environ.get("PER_MINUTE_RATE", 0.35))
    DEFAULT_LAT = 47.3769
    DEFAULT_LONG = 8.5417
    BATTERY_DRAIN_PER_KM = float(os.environ.get("BATTERY_DRAIN_PER_KM", 1.2))
    BATTERY_DRAIN_PER_MINUTE = float(os.environ.get("BATTERY_DRAIN_PER_MINUTE", 0.4))
    MIN_BATTERY_DRAIN = float(os.environ.get("MIN_BATTERY_DRAIN", 3.0))
