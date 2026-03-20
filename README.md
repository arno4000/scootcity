# ScootCity

E-Scooter Sharing Plattform gebaut mit Flask und MariaDB.

## Überblick

ScootCity ist eine Webanwendung für E-Scooter-Sharing mit zwei Benutzertypen:
- **Nutzer**: Können verfügbare Fahrzeuge finden, ausleihen und Fahrten durchführen
- **Verleihanbieter**: Verwalten ihre Fahrzeugflotten, tracken Status und Batteriestand

Die Anwendung folgt dem MVC-Paradigma mit SQLAlchemy (Models), Flask Blueprints (Controllers) und Jinja Templates (Views).

## Features

- Registrierung und Login für Nutzer und Verleihanbieter
- Fahrzeugverwaltung mit Echtzeitstatus, Batterie und GPS-Position
- QR-Code-basiertes Entsperren von Fahrzeugen
- Automatische Kostenberechnung und Zahlungsabwicklung
- REST API mit Token-Authentifizierung und Swagger-Dokumentation
- Stored Procedures für kritische Geschäftslogik (Fahrt starten/beenden)

## Installation

```bash
# Virtual Environment erstellen
python -m venv .venv
source .venv/bin/activate

# Abhängigkeiten installieren
pip install -r requirements.txt

# Datenbank initialisieren
mysql -u root -p < db/schema.sql

# Entwicklungsserver starten
flask --app run.py run --debug
```

Die Anwendung ist dann unter `http://localhost:5000` erreichbar.

## API

Die REST API ist unter `/api` verfügbar. Swagger-Dokumentation: `http://localhost:5000/api/docs`

Wichtigste Endpunkte:
- `POST /api/token` - Authentifizierung
- `GET /api/vehicles` - Verfügbare Fahrzeuge
- `POST /api/rides/start` - Fahrt starten
- `POST /api/rides/{id}/end` - Fahrt beenden

## Tests

```bash
pytest
```

## Technologie-Stack

- **Backend**: Flask (Python 3.12)
- **Datenbank**: MariaDB
- **ORM**: SQLAlchemy
- **Frontend**: Bootstrap + Jinja2
- **Containerisierung**: Docker + Docker Compose
