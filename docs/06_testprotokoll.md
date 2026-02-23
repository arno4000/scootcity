# 6 Testprotokoll

Die folgenden Testfälle wurden manuell durchgeführt. Ziel ist der Nachweis der wichtigsten funktionalen Anforderungen und der API-Fähigkeit. Tests wurden in der lokalen Docker-Umgebung mit Standard-Konfiguration (Port 8000, MariaDB in Compose) ausgeführt.

| ID | Testfall | Schritte (kurz) | Erwartetes Ergebnis | Tatsächliches Ergebnis | Status |
| --- | --- | --- | --- | --- | --- |
| T01 | Registrierung Fahrer:in | Browser → Registrieren → Rolle Fahrer:in → Formular senden | Account wird erstellt, Login möglich | Erfolgreich, Account angelegt | OK |
| T02 | Registrierung Anbieter | Browser → Anbieter registrieren → Formular senden | Anbieter-Account wird erstellt | Erfolgreich, Account angelegt | OK |
| T03 | Login Fahrer:in | Browser → Login → E-Mail/Passwort | Weiterleitung ins Fahrer-Dashboard | Erfolgreich, Dashboard sichtbar | OK |
| T04 | Login Anbieter | Browser → Login → Anbieter auswählen → E-Mail/Passwort | Weiterleitung ins Anbieter-Dashboard | Erfolgreich, Dashboard sichtbar | OK |
| T05 | Fahrzeug anlegen | Anbieter-Dashboard → Neues Fahrzeug → QR-Code & Pflichtfelder | Fahrzeug erscheint in Flottenliste | Erfolgreich, Fahrzeug sichtbar | OK |
| T06 | Fahrt starten | Fahrer-Dashboard → verfügbares Fahrzeug → „Fahrt starten“ | Status = `in_use`, aktive Fahrt sichtbar | Erfolgreich, aktive Fahrt sichtbar | OK |
| T07 | Fahrt beenden + Kosten | Aktive Fahrt → km erfassen → „Fahrt beenden“ | Kosten berechnet, Fahrzeug wieder `available` | Erfolgreich, Kosten angezeigt | OK |
| T08 | Zahlungsmittel anlegen | Fahrer-Dashboard → Zahlungsmittel hinzufügen | Zahlungsmittel in Liste sichtbar | Erfolgreich, aktiv gelistet | OK |
| T09 | Zahlungsmittel löschen (Soft) | Zahlungsmittel → Löschen | Zahlungsmittel wird inaktiv | Erfolgreich, nicht mehr aktiv | OK |
| T10 | API-Token beziehen | `POST /api/token` mit User-Creds | Token wird ausgegeben | Erfolgreich, Token erhalten | OK |
| T11 | API Fahrzeuge lesen | `GET /api/vehicles` mit Bearer-Token | JSON-Liste verfügbarer Fahrzeuge | Erfolgreich, Daten erhalten | OK |
| T12 | API Fahrt starten/beenden | `POST /api/rides/start` → `POST /api/rides/<id>/end` | Ride wird angelegt und abgeschlossen | Erfolgreich, Ride-Objekt zurück | OK |

Hinweis: Last- und Ausfallsicherheitstests (z.B. 500 gleichzeitige Ausleihen) sind im Rahmen der Praxisarbeit nicht durchgeführt worden und würden für eine produktive Einführung separat geplant.
