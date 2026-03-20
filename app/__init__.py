import click
from flask import Flask

from .config import Config
from .extensions import db
from .models import *  # noqa: F401,F403 ensures models registered


def create_app(config_class: type[Config] = Config) -> Flask:
    # Application-Factory: hier haengt alles zusammen.
    app = Flask(__name__)
    app.config.from_object(config_class)

    # DB an Flask binden.
    db.init_app(app)

    from .controllers.auth_controller import auth_bp
    from .controllers.user_controller import user_bp
    from .controllers.provider_controller import provider_bp
    from .controllers.api_controller import api_bp

    # Blueprints sauber trennen nach Funktion.
    app.register_blueprint(auth_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(provider_bp)
    app.register_blueprint(api_bp, url_prefix="/api")

    @app.cli.command("init-db")
    def init_db_command() -> None:
        """Create all tables based on the SQLAlchemy metadata."""
        with app.app_context():
            db.create_all()
        click.echo("MariaDB schema created")

    return app
