# ScootCity – E-Scooter Sharing Plattform

Webanwendung als Praxisarbeit für DBWE. Die App nutzt Flask (Python 3.11+) mit einer MariaDB-Datenbank und hält sich an das MVC-Paradigma (Modelle = SQLAlchemy-Modelle, Controller = Flask Blueprints, Views = Jinja-Templates).

## Anforderungen & Features

- Registrierung & Login für Fahrer (`nutzer`) und Verleihanbieter (`verleihanbieter`) mit eindeutiger E-Mail; Fahrer zusätzlich mit eindeutigem Benutzernamen.
- Verwaltung von Fahrzeugflotten inklusive Status, Akku und Position.
- Fahrer-Dashboard mit Fahrzeugbuchung, Beenden von Fahrten inkl. Kostenberechnung und Payment Flow.
- Speicherung aller Fachobjekte gemäss ERM (`erm.mmd`).
- REST-API für Maschinenzugriff (Token-basierte Authentisierung, JSON Responses).
- Ride-Start und Ride-Ende nutzen auf MariaDB/MySQL aktiv die Stored Procedures `sp_fahrt_starten` und `sp_fahrt_beenden` (mit ORM-Fallback für Nicht-MySQL-Testumgebungen).
- Zahlungsmittel können von Nutzern entfernt werden, bleiben aber für die Backend-Historie archiviert.
- Provider-Dashboard zeigt echte QR-Codes (PNG) zur Scooter-Ausweisung; Fahrende können QR-Links über `/unlock/<id>` öffnen und Batteriestände sinken automatisch anhand Fahrzeit/Kilometern.

## Installation

1. **Repo klonen & Abhängigkeiten installieren**
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
2. **MariaDB vorbereiten & mit Inhalt füllen**
   ```bash
   mysql -u root -p < db/schema.sql
   ```
   Das Skript legt die komplette Struktur inkl. Views, Stored Procedures sowie Beispieldaten an. Zugriff erfolgt über `mysql+pymysql://root:sml12345@localhost/scooter_plattform`.
3. **Schema (falls nötig) erneut erzeugen**
   ```bash
   flask --app run.py init-db
   ```
4. **Dev-Server starten**
   ```bash
   flask --app run.py run --debug
   ```

## REST API (Auszug)

- `POST /api/users` / `POST /api/providers` – Accounts anlegen (liefert direkt API-Token).
- `POST /api/token` – JSON `{ "email": "...", "password": "...", "account_type": "user|provider" }` → `{ "token": "..." }`
- `GET|POST /api/vehicles` + `PATCH|DELETE /api/vehicles/<id>` – Provider können ihre Flotte verwalten, Clients lesen verfügbare Fahrzeuge.
- `GET /api/rides`, `POST /api/rides/start`, `POST /api/rides/<id>/end` – Fahrten auflisten bzw. starten/beenden inkl. Kostenberechnung.
- `GET|POST /api/payment-methods`, `DELETE /api/payment-methods/<id>` – Zahlungsmittel via API pflegen.
- **Swagger UI** unter `http://localhost:5000/api/docs` zeigt alle Endpunkte samt JSON-Schemas.

## Tests / Manuelle Checks

1. Registrierung Fahrer+Provider, anschliessender Login.
2. Provider fügt Fahrzeug hinzu, Statuswechsel.
3. Fahrer legt Zahlungsmittel an, startet Fahrt, beendet Fahrt mit Kosten- und Payment-Erfassung.
4. API-Token anfordern (`curl -X POST http://localhost:5000/api/token -d '{"email":"..."}' -H 'Content-Type: application/json'`).
5. Mit Token Fahrzeuge abrufen (`curl -H 'Authorization: Bearer <token>' http://localhost:5000/api/vehicles`).

## Architekturüberblick

- **Models** (`app/models/*`): SQLAlchemy-Klassen für alle Tabellen aus dem ERM.
- **Controllers** (`app/controllers/*`): Trennen Auth, User-, Provider- und API-Logik.
- **Views** (`app/templates/*` + `app/static/*`): Bootstrap/Jinja UI.
- **Konfiguration** (`app/config.py`): DB-URI, Tarifparameter, Defaults.
- **Utils** (`app/utils/auth.py`): Session- und Token-Handling.
