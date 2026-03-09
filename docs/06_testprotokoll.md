# 6 Testprotokoll

Die wichtigsten funktionalen Anforderungen werden automatisiert mit Pytest überprüft. Testlauf erfolgte lokal mit Python 3.12 / pytest 8.2.1 über den Befehl:

```bash
pytest
```

Ergebnis Gesamtsuite: **18 Tests, alle bestanden**.

| ID | Testfall | Schritte (kurz) | Erwartetes Ergebnis | Tatsächliches Ergebnis | Status |
| --- | --- | --- | --- | --- | --- |
| T01 | API-Token (Erfolg/Fehler) | API-Client -> `POST /api/token` mit korrekten und falschen Login-Daten | Bei korrekten Daten wird Token geliefert, bei falschen Daten 401 | Token bei korrekten Daten erhalten, falsches Passwort sauber abgelehnt | OK |
| T02 | Registrierung Fahrer:in + Duplikat E-Mail | API-Client -> `POST /api/users` zweimal mit gleicher E-Mail | Erster Aufruf erstellt Account, zweiter Aufruf wird blockiert | Erstregistrierung erfolgreich, Duplikat mit Konfliktmeldung abgewiesen | OK |
| T03 | Registrierung Fahrer:in ohne Pflichtfeld | API-Client -> `POST /api/users` ohne vollständige Felder | Request wird als ungültig abgewiesen | 400 mit Pflichtfeld-Fehlermeldung | OK |
| T04 | Registrierung Fahrer:in mit dupliziertem Namen | API-Client -> zwei User mit gleichem Namen, unterschiedlicher E-Mail | Zweiter User mit gleichem Namen wird blockiert | Konflikt für zweiten Datensatz korrekt erkannt | OK |
| T05 | Zahlungsmittel anlegen, anzeigen, archivieren | API-Client -> Zahlungsmittel erstellen -> Liste abrufen -> löschen -> Liste prüfen | Zahlungsmittel erscheint in Liste und verschwindet nach Soft-Delete | Anlage, Anzeige und Archivierung funktionieren durchgängig | OK |
| T06 | Registrierung Anbieter + Duplikat E-Mail | API-Client -> `POST /api/providers` zweimal mit gleicher E-Mail | Erster Aufruf erstellt Anbieter, zweiter wird blockiert | Erstregistrierung erfolgreich, Duplikat-E-Mail abgewiesen | OK |
| T07 | Registrierung Anbieter mit dupliziertem Namen | API-Client -> zwei Anbieter mit gleichem Namen, unterschiedlicher E-Mail | Zweiter Anbieter mit gleichem Namen wird blockiert | Konflikt für zweiten Datensatz korrekt erkannt | OK |
| T08 | Fahrt starten und beenden mit Zahlungsmittel | API-Client -> Fahrt starten -> Zahlungsmittel wählen -> Fahrt beenden | Ride-Flow inkl. Statuswechsel, Kosten, Akku und Zahlung funktioniert | Start/Ende erfolgreich, Kosten und Akku korrekt berechnet, Zahlung erstellt | OK |
| T09 | Fahrtstart bei belegtem Fahrzeug | API-Client -> Fahrzeug starten -> zweiten Startversuch auf gleichem Fahrzeug ausführen | Zweiter Startversuch wird abgelehnt | Fahrzeugverfügbarkeit wird korrekt erzwungen | OK |
| T10 | Fahrtende ohne Zahlungsmittel | API-Client -> Fahrt starten -> Fahrt ohne `payment_method_id` beenden | Fahrt kann beendet werden, ohne Zahlungseintrag zu erzwingen | Ride erfolgreich beendet, kein Payment-Datensatz erstellt | OK |
| T11 | Minutenberechnung im Fallback-Pfad | Testumgebung -> Ride-Startzeit auf 61 Sekunden setzen -> Fahrt beenden | Abrechnung zählt 61 Sekunden als 1 volle Minute | Kosten entsprechen 1-Minuten-Logik wie in der SQL-Prozedur | OK |
| T12 | Fahrzeugliste nach Rolle und Status | API-Client -> Listenabfragen als User und Provider inkl. Statusfilter | User sieht verfügbare Fahrzeuge, Provider nur eigene, Statusfilter greift | Rollen- und Statusfilter liefern korrekte Datensätze | OK |
| T13 | Fahrzeug anlegen inkl. neuem Typ | API-Client -> neues Fahrzeug mit neuem Fahrzeugtyp erstellen | Fahrzeug und Typ werden sauber persistiert | Fahrzeug inkl. Typ und QR-Code in DB vorhanden | OK |
| T14 | Web-Login Fahrer:in | Browser -> Login mit Fahrer-Konto | Weiterleitung ins Fahrer-Dashboard, Session aktiv | Redirect und Session-Werte korrekt gesetzt | OK |
| T15 | Web-Login Anbieter | Browser -> Login mit Anbieter-Konto | Weiterleitung ins Anbieter-Dashboard, Session aktiv | Redirect und Session-Werte korrekt gesetzt | OK |
| T16 | Web-Registrierung Anbieter mit dupliziertem Namen | Browser -> Anbieter-Registrierung mit bereits vergebenem Namen | Formular wird nicht gespeichert, Fehlermeldung erscheint | Duplikatname korrekt blockiert und Meldung angezeigt | OK |
| T17 | QR-URL-Aufbau ohne Doppel-Slash | Utility-Test -> `BASE_URL` mit Trailing Slash verarbeiten | QR-Payload enthält saubere Unlock-URL ohne `//` | URL wird korrekt normalisiert | OK |
| T18 | Batterie-Drain Mindestwert und Untergrenze | Utility-Test -> Akkuverbrauch mit kleinem und extrem großem Wert berechnen | Mindestverbrauch greift, Akku fällt nie unter 0 | 1. Schritt Mindestverbrauch aktiv, 2. Schritt korrekt auf 0 begrenzt | OK |

Hinweis: Last- und Ausfallsicherheitstests (z. B. 500 gleichzeitige Ausleihen) sind weiterhin nicht Teil dieses Umfangs und müssten separat geplant werden.
