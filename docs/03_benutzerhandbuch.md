# 3 Benutzerhandbuch

Dieses Kapitel beschreibt den Zugriff über den Browser und führt Schritt für Schritt durch die wichtigsten Bedienabläufe. Die Anwendung steht nach Deployment via Docker Compose unter der im Projekt gesetzten `BASE_URL` zur Verfügung (Standard `http://localhost:8000`).

## 3.1 Zugang & Anmeldung

1. **Registrierung**: Über den Link „Registrieren“ wählen Nutzer:innen die Rolle *Fahrer:in* (`nutzer`) oder *Verleihanbieter* (`verleihanbieter`). Eine gültige E-Mail-Adresse, ein eindeutiger Benutzername sowie ein Passwort sind Pflicht.
2. **Login**: Nach erfolgreicher Registrierung führt der Button „Anmelden“ zum Login-Formular. Nach Eingabe von E-Mail und Passwort wird die Session initialisiert und die Rolle hinterlegt.
3. **Passwortänderung**: Passwörter können im Profilbereich geändert werden. Dazu muss das bisherige Passwort bestätigt werden.
4. **Abmelden**: Oben rechts im Menü befindet sich „Logout“. Damit wird die Session invalidiert.

## 3.2 Fahrer-Dashboard

Nach dem Login mit der Rolle *Fahrer:in* erscheint das Dashboard mit drei Abschnitten:

- **Verfügbare Fahrzeuge**: Karte/Liste aller Fahrzeuge im Status „verfügbar“ inkl. Akku-Stand, Standort und Typ. Der Button „Fahrt starten“ öffnet das Startformular.
- **Aktive Fahrt**: Falls eine Fahrt läuft, zeigt der Block Startzeit, Fahrzeug-ID und laufende Kosten. Über „Fahrt beenden“ werden Kilometer und Fahrtdauer erfasst und die Kosten berechnet.
- **Zahlungsmittel & Historie**: Nutzer:innen hinterlegen Kreditkarten/Payment-Token. Ein Eintrag kann deaktiviert werden (Soft Delete), bleibt jedoch für die Historie sichtbar. Die Ride-Liste zeigt abgeschlossene Fahrten inkl. Kosten.

### Fahrten starten

1. Fahrzeug aus der Liste auswählen und „Fahrt starten“ klicken.
2. Optional QR-Code scannen (z.B. direkt am Scooter); der Link `/unlock/<fahrzeug_id>` öffnet das Startformular und übernimmt den Fahrzeugkontext.
3. Bei erfolgreichem Start wechselt der Status auf `in_use`. Fahrer:innen sehen nun die aktive Fahrt.

### Fahrten beenden

1. Im Bereich „Aktive Fahrt“ auf „Fahrt beenden“ klicken.
2. Kilometerstand sowie Fahrtdauer bestätigen. Die App berechnet Basispreis und Minutenpreis gemäss Tarifen (`BASE_RATE`, `PER_MINUTE_RATE`) und reduziert den Akku automatisch anhand der Parameter `BATTERY_DRAIN_PER_KM` bzw. `BATTERY_DRAIN_PER_MINUTE`.
3. Optional Payment bestätigen, damit ein Transaktionseintrag erstellt wird.

## 3.3 Anbieter-Dashboard

Verleihanbieter erhalten nach dem Login Zugriff auf eine Übersicht zu ihrer Flotte:

- **Flottenliste**: Tabelle aller registrierten Fahrzeuge mit Status, Standort (Koordinaten), Akku-Ladung, Typ. Über „Bearbeiten“ lassen sich Daten anpassen, „Deaktivieren“ setzt den Status auf `maintenance`.
- **Neues Fahrzeug**: Formular zur Erfassung inkl. Auswahl des Fahrzeugtyps (standardmässig E-Scooter oder E-Bike). Nach dem Speichern erzeugt das System automatisch einen QR-Code.
- **QR-Codes & Sharing**: Klick auf ein Fahrzeug zeigt den QR-Code als PNG und die zugehörige Unlock-URL. Diese kann gedruckt oder elektronisch verteilt werden.
- **Ride-Monitoring**: Liste laufender Fahrten mit Startzeit, Fahrer, Fahrzeug. Damit behalten Anbieter ihre Flotte im Blick.

### Typische Aufgaben

1. **Fahrzeug anlegen**: „Neues Fahrzeug“ öffnen → Pflichtfelder ausfüllen → Speichern. Das Fahrzeug erscheint sofort in der Flottenliste und für Fahrer:innen (Status „verfügbar“).
2. **Wartung planen**: In der Flottenliste auf „Bearbeiten“ klicken, Status auf „Wartung“ setzen. Das Fahrzeug verschwindet daraufhin aus der Fahrer-Liste.
3. **QR-Code exportieren**: Im Fahrzeug-Detailansicht den QR-Code herunterladen oder kopieren und physisch am Scooter anbringen.

## 3.4 Troubleshooting & Support

- **Login schlägt fehl**: Passwort zurücksetzen und sicherstellen, dass keine Tippfehler in der E-Mail-Adresse vorkommen.
- **Fahrt lässt sich nicht starten**: Prüfen, ob das Fahrzeug noch den Status „verfügbar“ hat oder bereits durch einen anderen Nutzer belegt ist.
- **QR-Link öffnet Startformular nicht**: BASE_URL sowie Port im Deployment kontrollieren. Links funktionieren nur, wenn der Browser Zugriff auf die App-URL hat.
- **Keine Zahlungsmittel sichtbar**: Nach dem Hinzufügen eines Zahlungsmittels Seite neu laden. Soft gelöschte Zahlungsmittel werden als deaktiviert markiert, können aber reaktiviert werden.

Weitere technische Details zur Architektur und API sind in den folgenden Kapiteln dokumentiert; für Endanwender:innen genügt das hier beschriebene Vorgehen.
