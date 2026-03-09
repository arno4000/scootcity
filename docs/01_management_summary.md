# 1 Management Summary

ScootCity digitalisiert den in der Aufgabenstellung beschriebenen E-Scooter-Verleih für Städte. Die Praxisarbeit liefert eine einheitliche Plattform, auf der Verleihanbieter ihre Flotten in Echtzeit verwalten und Fahrer:innen Fahrzeuge bequem per Browser oder REST-API buchen, fahren und abrechnen können.

## Kernergebnisse

- **Funktionsumfang**: Registrierung und Login für Fahrer:innen sowie Anbieter, QR-gestützte Fahrten, automatische Kosten- und Akku-Berechnung und ein Payment-Flow mit gepflegten Zahlungsmitteln erfüllen sämtliche Muss-Anforderungen.
- **API & Automatisierung**: Eine tokenbasierte REST-API (Swagger-Doku unter `/api/docs`) deckt Fahrzeugmanagement, Fahrten und Payments ab und ermöglicht Integrationen mit Drittsystemen wie Anbieter-Tools oder mobilen Apps.
- **Transparente Betriebsdaten**: Stored Procedures im Schema (`db/schema.sql`) sichern Kernabläufe wie Ride-Start/-Ende direkt auf SQL-Ebene ab.
- **Nachweis Tests**: Die automatisierten Pytest-Fälle decken zentrale Use Cases (Registrierung, Fahrtenfluss, API-Zugriff) reproduzierbar ab.

## Infrastruktur & Bereitstellung

Die Lösung basiert auf Python 3.11, Flask, SQLAlchemy und MariaDB. Gunicorn dient als Applikationsserver, die Weboberfläche nutzt Bootstrap, und Token-Handling geschieht über eigene Utility-Module. Ein Docker-Setup (`compose.yml`) startet sowohl die MariaDB (lscr.io/linuxserver/mariadb) als auch den Applikationscontainer (Image `kubierend/scootcity`). Beim Container-Start initiiert `docker-entrypoint.sh` das Schema automatisch über `scripts/init_db.py`, inklusive Standardfahrzeugtypen (E-Scooter/E-Bike) und Stored Procedures. Damit ist die Applikation reproduzierbar aufsetzbar und kann auf jedem Host mit Docker in wenigen Minuten bereitgestellt werden.

## Mehrwert für das Projekt

- **Zentralisierte Plattform**: Anbieter- und Fahrerprozesse laufen in einer gemeinsamen Lösung, wodurch doppelte Erfassung entfällt und historische Daten konsistent bleiben.
- **Erweiterbarkeit**: Architektur nach MVC, modulare Blueprints und ein separates Fahrzeugtyp-Table erlauben, zusätzliche Fahrzeugklassen oder externe Clients rasch anzubinden.
- **Skalierbarkeit & Betrieb**: Containerisierung sowie Konfigurationsparameter (Tarife, BASE_URL, SECRET_KEY) erleichtern Migration in Cloud- oder On-Prem-Umgebungen und unterstützen automatisiertes Deployment.

## Risiken & Empfehlungen

- **Single-DB-Abhängigkeit**: In der aktuellen Fassung läuft eine einzelne MariaDB-Instanz ohne Replikation. Für den produktiven Dauerbetrieb sollte ein verwalteter Datenbankdienst mit Backups eingeplant werden.
- **Performance-Nachweis**: Es existieren bisher nur funktionale Tests. Belastungstests (z.B. 500 gleichzeitige Fahrten) stehen noch aus und sollten vor einer öffentlichen Lancierung erfolgen.
- **Security-Hardening**: Die Token-Authentisierung erfüllt die Mindestanforderung. Mittelfristig empfiehlt sich ein Secrets-Management (z.B. Vault) und HTTPS-Termination via Nginx oder Cloud-Proxy, damit Schlüssel nicht im Compose-File verbleiben.
