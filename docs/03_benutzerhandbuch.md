# 3 Benutzerhandbuch

Dieses Kapitel beschreibt den Zugriff über den Browser und führt Schritt für Schritt durch die wichtigsten Bedienabläufe. Die Anwendung steht nach Deployment via Docker Compose unter der im Projekt gesetzten `BASE_URL` zur Verfügung (Standard `http://localhost:8000`).

## 3.1 Zugang & Anmeldung

1. **Registrierung**: Über den Link „Registrieren“ wählen Nutzer:innen die Rolle *Fahrer:in* (`nutzer`) oder *Verleihanbieter* (`verleihanbieter`). Eine gültige E-Mail-Adresse, ein eindeutiger Benutzername sowie ein Passwort sind Pflicht.
2. **Login**: Nach erfolgreicher Registrierung führt der Button „Anmelden“ zum Login-Formular. Nach Eingabe von E-Mail und Passwort wird die Session initialisiert und die Rolle hinterlegt.
3. **Abmelden**: Oben rechts im Menü befindet sich „Logout“. Damit wird die Session invalidiert.

## 3.2 Fahrer-Dashboard

Nach dem Login mit der Rolle *Fahrer:in* erscheint das Dashboard mit drei Abschnitten:

- **Verfügbare Fahrzeuge**: Liste aller Fahrzeuge im Status „verfügbar“ inkl. Akku-Stand, Provider und Typ. Der Button „Fahrt starten“ öffnet das Startformular.
- **Aktive Fahrt**: Falls eine Fahrt läuft, zeigt der Block Startzeit und Fahrzeugdaten. Über „Fahrt beenden“ werden Kilometer erfasst und die Kosten berechnet.
- **Zahlungsmittel & Historie**: Nutzer:innen hinterlegen Kreditkarten/Payment-Token. Ein Eintrag kann deaktiviert werden (Soft Delete), bleibt jedoch für die Historie sichtbar. Die Ride-Liste zeigt abgeschlossene Fahrten inkl. Kosten.

### Fahrten starten

1. Fahrzeug aus der Liste auswählen und „Fahrt starten“ klicken.
2. Optional QR-Code scannen (z.B. direkt am Scooter); der Link `/unlock/<fahrzeug_id>` öffnet das Startformular und übernimmt den Fahrzeugkontext.
3. Bei erfolgreichem Start wechselt der Status auf `in_benutzung`. Fahrer:innen sehen nun die aktive Fahrt.

### Fahrten beenden

1. Im Bereich „Aktive Fahrt“ auf „Fahrt beenden“ klicken.
2. Gefahrene Kilometer erfassen. Die App berechnet Kosten aus Basispreis und Minutenpreis gemäss Tarif und reduziert den Akku automatisch anhand der Parameter `BATTERY_DRAIN_PER_KM` bzw. `BATTERY_DRAIN_PER_MINUTE`.
3. Optional Payment bestätigen, damit ein Transaktionseintrag erstellt wird.

## 3.3 Anbieter-Dashboard

Verleihanbieter erhalten nach dem Login Zugriff auf eine Übersicht zu ihrer Flotte:

- **Flottenliste**: Tabelle aller registrierten Fahrzeuge mit Status, Standort (Koordinaten), Akku-Ladung, Typ. Über „Bearbeiten“ lassen sich Daten anpassen, „Deaktivieren“ setzt den Status auf `wartung`.
- **Neues Fahrzeug**: Formular zur Erfassung inkl. Auswahl des Fahrzeugtyps (standardmässig E-Scooter oder E-Bike). Nach dem Speichern erzeugt das System automatisch einen QR-Code.
- **QR-Codes & Sharing**: Für jedes Fahrzeug wird ein QR-Code im Dashboard angezeigt; die zugehörige Unlock-URL kann über den User-Bereich geöffnet und verteilt werden.

### Typische Aufgaben

1. **Fahrzeug anlegen**: „Neues Fahrzeug“ öffnen → Pflichtfelder ausfüllen → Speichern. Das Fahrzeug erscheint sofort in der Flottenliste und für Fahrer:innen (Status „verfügbar“).
2. **Wartung planen**: In der Flottenliste auf „Bearbeiten“ klicken, Status auf „Wartung“ setzen. Das Fahrzeug verschwindet daraufhin aus der Fahrer-Liste.
3. **QR-Code nutzen**: QR-Code im Dashboard anzeigen und den enthaltenen Unlock-Link am Fahrzeug bereitstellen.

## 3.4 Troubleshooting & Support

- **Login schlägt fehl**: E-Mail/Passwort und gewählte Rolle (`nutzer`/`verleihanbieter`) prüfen.
- **Fahrt lässt sich nicht starten**: Prüfen, ob das Fahrzeug noch den Status „verfügbar“ hat oder bereits durch einen anderen Nutzer belegt ist.
- **QR-Link öffnet Startformular nicht**: BASE_URL sowie Port im Deployment kontrollieren. Links funktionieren nur, wenn der Browser Zugriff auf die App-URL hat.
- **Keine Zahlungsmittel sichtbar**: Nach dem Hinzufügen eines Zahlungsmittels Seite neu laden. Soft gelöschte Zahlungsmittel sind deaktiviert und bleiben nur für die Historie erhalten.

Weitere technische Details zur Architektur und API sind in den folgenden Kapiteln dokumentiert; für Endanwender:innen genügt das hier beschriebene Vorgehen.
