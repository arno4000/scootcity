# 2 Anforderungen

Die Applikation erfüllt alle Muss-Punkte der Aufgabenstellung und erweitert sie an sinnvollen Stellen. Die Anforderungen lassen sich wie folgt gliedern.

## 2.1 Funktionale Anforderungen

| ID | Beschreibung | Kriterien / Akzeptanz | Status |
| --- | --- | --- | --- |
| F1 | Benutzer- & Anbieter-Accounts | Registrierung mit eindeutiger E-Mail, Passwort-Hashing, Session-Login für Rollen `nutzer` und `verleihanbieter`. | Erfüllt |
| F2 | Fahrzeugverwaltung | Anbieter können Fahrzeuge inkl. Standort, Status, Akku, Typ verwalten und QR-Codes generieren. Änderungen wirken sich sofort auf Dashboard & API aus. | Erfüllt |
| F3 | Fahrten-Lifecycle | Fahrer:innen sehen verfügbare Fahrzeuge, starten Fahrten (Statuswechsel auf `in_use`), erfassen Kilometer/Dauer und beenden Fahrten mit Kostenberechnung inkl. Akku-Drain. | Erfüllt |
| F4 | Zahlungsmittel & Abrechnung | Nutzer:innen legen Zahlungsmittel an/entfernen sie (Soft Delete); abgeschlossene Fahrten erzeugen Payments mit Basis- und Minutenpreis. | Erfüllt |
| F5 | REST-API | JSON-Endpunkte für Accountanlage, Token, Fahrzeug-CRUD, Fahrtstart/-ende sowie Zahlungsmittel. Auth via Bearer-Token, dokumentiert unter `/api/docs`. | Erfüllt |
| F6 | Provider- & User-Dashboards | Getrennte UIs für Fahrer:innen und Anbieter mit KPI-Übersichten und direkten Aktionen (z.B. Ride starten, Status ändern) ohne API-Kenntnisse. | Erfüllt |

## 2.2 Nicht-funktionale Anforderungen

| ID | Beschreibung | Kriterien / Akzeptanz | Status |
| --- | --- | --- | --- |
| NF1 | Technologie-Stack | Flask (Python 3.11), SQLAlchemy, MariaDB, Gunicorn; UI mit Bootstrap für responsives Verhalten. | Erfüllt |
| NF2 | Deployment & Betrieb | Docker Compose startet DB + App; `scripts/init_db.py` setzt Schema, Views, Stored Procedures und Seed-Daten automatisiert auf. | Erfüllt |
| NF3 | Security & Compliance | Passwort-Hashing, Session mit IDs/Rollen, Bearer-Token für API, Konfiguration via Umgebungsvariablen. | Erfüllt |
| NF4 | Erweiterbarkeit | Fahrzeugtypen separat modelliert, klare Blueprint-Trennung (Auth/User/Provider/API) für spätere Module oder Fahrzeugarten. | Erfüllt |
| NF5 | Verfügbarkeit & Monitoring | Konfigurierbare Tarife/Parameter in `app/config.py`, Logging via Flask/Gunicorn-Stdout, Abgriff über Docker möglich. | Erfüllt |
| NF6 | Dokumentation & Tests | README, Swagger, ERM, Architektur-Doku vorhanden; manuelle Tests (Registrierung, Fahrten, API) dokumentieren Qualitätsnachweis. | Erfüllt |
