# 6 Testprotokoll

Die wichtigsten funktionalen Anforderungen werden automatisiert mit Pytest überprüft. Testlauf erfolgte lokal mit Python 3.12 / pytest 8.2.1 über den Befehl:

```bash
PYTHONPATH=. pytest
```

Ergebnis: **13 Tests, alle bestanden**.

| ID | Testfall | Durchführung | Erwartetes Ergebnis | Tatsächliches Ergebnis | Status |
| --- | --- | --- | --- | --- | --- |
| T01 | Registrierung Fahrer:in | `pytest tests/test_api_auth.py::test_create_user_endpoint_enforces_required_fields` | `POST /api/users` legt Account an und liefert Token, Duplikate werden abgewiesen | 201 + Token bei Erstregistrierung, 409 bei erneuter Verwendung der E-Mail | OK (automatisiert) |
| T02 | Registrierung Anbieter | `pytest tests/test_api_providers.py::test_create_provider_endpoint_validates_and_returns_token` | `POST /api/providers` erstellt Anbieter inkl. API-Token | Anbieter wird persistiert und liefert Token, Duplikate ergeben 409 | OK (automatisiert) |
| T03 | Login Fahrer:in | `pytest tests/test_auth_web.py::test_user_login_flow_creates_session` | `POST /auth/login` leitet ins Fahrer-Dashboard um, Session enthält Nutzer-ID | Redirect auf `/dashboard`, Session `role=user`, `account_id` gesetzt | OK (automatisiert) |
| T04 | Login Anbieter | `pytest tests/test_auth_web.py::test_provider_login_redirects_to_provider_dashboard` | Provider-Login führt zum Dashboard `/provider/dashboard` | Redirect erfolgt, Session `role=provider`, ID gesetzt | OK (automatisiert) |
| T05 | Fahrzeug anlegen | `pytest tests/test_api_vehicles.py::test_provider_can_create_vehicle_via_api` | Anbieter kann via API ein Fahrzeug + Fahrzeugtyp anlegen | Response 201, Datensatz mit QR-Code `cargo-qr` in DB angelegt | OK (automatisiert) |
| T06 | Fahrt starten | `pytest tests/test_api_rides.py::test_start_and_end_ride_flow` (Startteil) | `POST /api/rides/start` erzeugt Fahrt und setzt Fahrzeug `in_benutzung` | Reise-ID wird geliefert, Fahrzeugstatus wechselt zu `in_benutzung` | OK (automatisiert) |
| T07 | Fahrt beenden + Kosten | `pytest tests/test_api_rides.py::test_start_and_end_ride_flow` (Endteil) | `POST /api/rides/<id>/end` berechnet Kosten und setzt Fahrzeug frei | Kosten = 2.22 CHF, Akku sinkt auf 97 %, Fahrzeug wieder `verfuegbar` | OK (automatisiert) |
| T08 | Zahlungsmittel anlegen | `pytest tests/test_api_payment_methods.py::test_payment_method_create_list_and_delete_flow` (Anlage) | `POST /api/payment-methods` legt Methode an und taucht in Liste auf | 201, Liste enthält neues Zahlungsmittel | OK (automatisiert) |
| T09 | Zahlungsmittel löschen (Soft) | `pytest tests/test_api_payment_methods.py::test_payment_method_create_list_and_delete_flow` (Archiv) | `DELETE /api/payment-methods/<id>` markiert Methode als inaktiv | API antwortet `archived`, Liste danach leer | OK (automatisiert) |
| T10 | API-Token beziehen | `pytest tests/test_api_auth.py::test_issue_token_success_and_failure` | `POST /api/token` liefert Token bei korrekten Daten, sonst 401 | Token wird ausgegeben, falsches Passwort führt zu 401 | OK (automatisiert) |
| T11 | API Fahrzeuge lesen | `pytest tests/test_api_vehicles.py::test_vehicle_listing_filters_by_role_and_status` | Provider sieht nur eigene Fahrzeuge; Fahrer:innen sehen verfügbare | API liefert gefilterte Listen je Rolle, Statusfilter `wartung` funktioniert | OK (automatisiert) |
| T12 | API Fahrt starten/beenden (Doppelschutz) | `pytest tests/test_api_rides.py::test_start_ride_rejects_unavailable_vehicle` | Zweiter Startversuch mit belegtem Fahrzeug wird blockiert | API liefert 400 „Fahrzeug nicht verfügbar“ | OK (automatisiert) |

Hinweis: Last- und Ausfallsicherheitstests (z. B. 500 gleichzeitige Ausleihen) sind weiterhin nicht Teil dieses Umfangs und müssten separat geplant werden.
