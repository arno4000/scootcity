# 4 API-Dokumentation

Die REST-API stellt alle Kernprozesse der Plattform für Maschinenzugriff bereit. Standard-Basis-URL ist `https://<host>/api`. Clients senden JSON und erwarten JSON als Antwort. Fehlermeldungen enthalten mindestens ein Feld `error` sowie einen passenden HTTP-Status.

## 4.1 Authentisierung

1. **Token beziehen** via `POST /api/token` mit E-Mail, Passwort und optional `account_type` (`user` oder `provider`).
2. **Bearer-Header setzen**: `Authorization: Bearer <token>`.
3. Tokens können jederzeit über denselben Endpoint erneuert werden.

| Methode | Endpoint | Auth | Beschreibung | Request-Body | Response |
| --- | --- | --- | --- | --- | --- |
| POST | `/api/token` | keine | Liefert ein Bearer-Token für User oder Provider. | `{ "email": "...", "password": "...", "account_type": "user\|provider" }` | `200 OK` mit `{ "token": "...", "role": "user" }`; `401` bei ungültigen Daten. |

## 4.2 Account-Anlage

| Methode | Endpoint | Auth | Beschreibung | Request-Body | Response |
| --- | --- | --- | --- | --- | --- |
| POST | `/api/users` | keine | Erstellt einen Fahrer:innen-Account inkl. Initial-Token. | `{ "name": "...", "email": "...", "password": "..." }` | `201 Created`, liefert `user`-Objekt + `token`. |
| POST | `/api/providers` | keine | Erstellt einen Verleihanbieter mit optionalem Feld `typ`. | `{ "name": "...", "email": "...", "password": "...", "typ": "firma\|privat" }` | `201 Created`, liefert `provider`-Objekt + `token`. |

## 4.3 Fahrzeuge

| Methode | Endpoint | Auth | Beschreibung | Request-Parameter | Response |
| --- | --- | --- | --- | --- | --- |
| GET | `/api/vehicles` | Bearer (User/Provider) | Liefert Fahrzeuge. Provider sehen nur eigene, User sehen standardmässig `status=available`. Query `?status=<status>` filtert zusätzlich. | Query `status` optional. | Liste von Vehicle-Objekten. |
| POST | `/api/vehicles` | Bearer (Provider) | Legt Fahrzeug an. QR-Code ist Pflicht; Koordinaten optional (Default aus Config). | `{ "vehicle_type": "E-Scooter", "status": "available", "battery_level": 95, "gps_lat": 47.37, "gps_long": 8.54, "qr_code": "XYZ123" }` | `201 Created`, Vehicle-Objekt. |
| GET | `/api/vehicles/<id>` | Bearer (User/Provider) | Detail eines Fahrzeugs. Provider dürfen nur eigene sehen; User nur, wenn Fahrzeug verfügbar. | Pfadparameter `<id>`. | Vehicle-Objekt. |
| PATCH/PUT | `/api/vehicles/<id>` | Bearer (Provider) | Aktualisiert Status, Typ, Akku oder Koordinaten. | Teilobjekt, z.B. `{ "status": "maintenance" }`. | Aktualisiertes Vehicle. |
| DELETE | `/api/vehicles/<id>` | Bearer (Provider) | Entfernt ein Fahrzeug dauerhaft. | – | `{ "status": "deleted" }`. |
| GET | `/api/vehicles/<id>/qr` | Bearer (User/Provider) | Liefert QR-Code-PNG für Unlock-Link. User erhalten nur Codes für verfügbare Fahrzeuge. | – | Binary `image/png`. |

## 4.4 Fahrten

| Methode | Endpoint | Auth | Beschreibung | Request-Body | Response |
| --- | --- | --- | --- | --- | --- |
| GET | `/api/rides` | Bearer (User) | Listet Fahrten des eingeloggten Fahrers absteigend nach Startzeit. | – | `{ "data": [ ... ] }`. |
| POST | `/api/rides/start` | Bearer (User) | Startet eine Fahrt. Es darf nur eine aktive Fahrt pro User existieren. | `{ "vehicle_id": 42 }` | `201 Created`, Ride-Objekt. |
| POST | `/api/rides/<id>/end` | Bearer (User) | Beendet eine Fahrt, berechnet Kosten und setzt Fahrzeug auf `available`. Optional Payment-Methode übergeben. | `{ "kilometers": 3.5, "payment_method_id": 7 }` | Ride-Objekt mit `cost`, `end_time`. |

## 4.5 Zahlungsmittel & Payments

| Methode | Endpoint | Auth | Beschreibung | Request-Body | Response |
| --- | --- | --- | --- | --- | --- |
| GET | `/api/payment-methods` | Bearer (User) | Liefert aktive Zahlungsmittel sortiert nach Erstellungsdatum. | – | `{ "data": [ { "id": ..., "type": "...", "details": "...", "is_active": true } ] }`. |
| POST | `/api/payment-methods` | Bearer (User) | Legt ein Zahlungsmittel an. `details` ist Pflicht. | `{ "method_type": "Kreditkarte", "details": "Visa **** 4242" }` | `201 Created`, Objekt wie oben. |
| DELETE | `/api/payment-methods/<id>` | Bearer (User) | Markiert Zahlungsmittel als inaktiv (Soft Delete). | – | `{ "status": "archived" }`. |

Sobald eine Fahrt mit `payment_method_id` beendet wird, legt das System automatisch einen Payment-Eintrag mit Status `settled` an. Dieser ist Bestandteil der Ride-Daten (`ride["payments"]`).

## 4.6 Fahrzeugtypen

| Methode | Endpoint | Auth | Beschreibung | Request-Body | Response |
| --- | --- | --- | --- | --- | --- |
| GET | `/api/vehicle-types` | Bearer (User/Provider) | Listet alle Fahrzeugtypen (z.B. E-Scooter, E-Bike). | – | `{ "data": ["E-Bike", "E-Scooter", ...] }`. |
| POST | `/api/vehicle-types` | Bearer (Provider) | Legt einen neuen Typ an; Name muss eindeutig sein. | `{ "name": "Cargo-Bike" }` | `201 Created`, `{ "name": "Cargo-Bike" }`. |

## 4.7 Dokumentation & Tools

- **Swagger UI**: `GET /api/docs` (nur für eingeloggte Provider im Browser zugänglich) zeigt alle Endpunkte samt Schemas.
- **OpenAPI JSON**: `GET /api/openapi.json` liefert das vollständige JSON-Dokument, nutzbar für Code-Generatoren oder Postman-Import.

## 4.8 Beispiel-Workflow (curl)

```bash
# Token für Fahrer holen
curl -s -X POST https://host/api/token \
  -H "Content-Type: application/json" \
  -d '{ "email": "anna@example.com", "password": "secret", "account_type": "user" }'

# Fahrzeuge abrufen
curl -s https://host/api/vehicles \
  -H "Authorization: Bearer <TOKEN>"

# Fahrt starten
curl -s -X POST https://host/api/rides/start \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{ "vehicle_id": 5 }'
```

Alle weiteren Details (z.B. Feldbeschreibungen) sind im OpenAPI-Dokument hinterlegt und können direkt aus der Anwendung exportiert werden.
