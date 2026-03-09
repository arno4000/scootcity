# 5 Systemarchitektur

```mermaid
%%{init: {'theme': 'default'}}%%
erDiagram
    direction LR

    VERLEIHANBIETER {
        int anbieter_id PK
        string name UK
        string email UK
        string password_hash
        string typ
        string api_token UK
        datetime erstellt_am
    }

    FAHRZEUG {
        int fahrzeug_id PK
        int anbieter_id FK
        int fahrzeugtyp_id FK
        enum status
        decimal akku_status
        decimal gps_lat
        decimal gps_long
        string qr_code UK
        datetime erstellt_am
    }

    NUTZER {
        int nutzer_id PK
        string name UK
        string email UK
        string password_hash
        string api_token UK
        datetime erstellt_am
    }

    FAHRZEUGTYP {
        int fahrzeugtyp_id PK
        string bezeichnung UK
        decimal grundpreis
        decimal minutenpreis
        boolean ist_aktiv
    }

    AUSLEIHE {
        int ausleihe_id PK
        int nutzer_id FK
        int fahrzeug_id FK
        datetime startzeit
        datetime endzeit
        decimal kilometer
        decimal kosten
        decimal grundpreis
        decimal minutenpreis
    }

    ZAHLUNGSMITTEL {
        int zahlungsmittel_id PK
        int nutzer_id FK
        string typ
        string details
        boolean ist_aktiv
        datetime erstellt_am
    }

    ZAHLUNG {
        int zahlung_id PK
        int ausleihe_id FK
        int zahlungsmittel_id FK
        datetime zeitpunkt
        decimal betrag
        string status
    }

    VERLEIHANBIETER ||--o{ FAHRZEUG : besitzt
    FAHRZEUGTYP ||--o{ FAHRZEUG : klassifiziert
    FAHRZEUG ||--o{ AUSLEIHE : wird_genutzt_in
    NUTZER ||--o{ AUSLEIHE : taetigt
    NUTZER ||--o{ ZAHLUNGSMITTEL : hinterlegt
    ZAHLUNGSMITTEL ||--o{ ZAHLUNG : wird_verwendet_fuer
    AUSLEIHE ||--o{ ZAHLUNG : hat
```

## 5.1 Datenmodell (ERM)

Das Mermaid-Diagramm entspricht `erm.mmd` und bildet alle Kernobjekte ab:

- **Verleihanbieter** besitzen beliebig viele Fahrzeuge. Attribute wie `typ` (Firma/Privat) steuern Workflows.
- **Fahrzeuge** enthalten den Fahrzeugtyp (z.B. E-Scooter), Status, Akku und GPS. Sie verweisen auf einen Anbieter und generieren QR-Codes für das Unlocking.
- **Nutzer** (Fahrer:innen) besitzen mehrere Ausleihen und Zahlungsmittel.
- **Ausleihen** verknüpfen Nutzer und Fahrzeuge; sie speichern Start-/Endzeit, Kilometer, Kosten und historische Tarife.
- **Zahlungsmittel** gehören zu einem Nutzer und enthalten anonymisierte Details. Mehrere Zahlungen können dasselbe Zahlungsmittel verwenden.
- **Zahlungen** referenzieren Ausleihe und Zahlungsmittel und dokumentieren Betrag sowie Status (`bezahlt`, `offen`, etc.).

Die Kardinalitäten sichern Geschäftsregeln: Ein Fahrzeug kann gleichzeitig nur in einer Ausleihe sein, Zahlungen gehören genau zu einer Ausleihe, Nutzer dürfen mehrere Zahlungsmittel hinterlegen. Das Schema ist normalisiert und verhindert doppelte Datenhaltung.

## 5.2 Systemarchitektur (MVC)

```mermaid
flowchart LR
    subgraph Client
        Browser
        APIClient
    end
    subgraph FlaskApp[Flask / Gunicorn]
        direction TB
        ViewLayer[Jinja2 Views\napp/templates]
        ControllerLayer[Controller / Blueprints\napp/controllers/*]
        ModelLayer[Modelle & Services\napp/models/* + utils]
    end
    subgraph MariaDB
        DB[(Schema\nTables,\nStored Procedures)]
    end
    Browser -->|HTML/JS| ViewLayer
    APIClient -->|JSON| ControllerLayer
    ViewLayer --> ControllerLayer
    ControllerLayer --> ModelLayer
    ModelLayer --> DB
    DB --> ModelLayer
    ControllerLayer --> ViewLayer
```

Die Darstellung zeigt den klassischen MVC-Aufbau: Die Blueprints bilden die Controller-Schicht, rufen Modelle sowie Utilities auf und liefern Daten an Jinja-Views oder JSON-Antworten. Clients greifen entweder via Browser (HTML) oder API-Client (JSON) darauf zu. MariaDB stellt persistente Daten bereit; Stored Procedures ergänzen die Business-Logik auf Datenbankseite.

Für den Fahrten-Lifecycle werden die Stored Procedures auch tatsächlich genutzt: `start_ride` und `end_ride` rufen auf MariaDB/MySQL direkt `CALL sp_fahrt_starten(...)` bzw. `CALL sp_fahrt_beenden(...)` auf. Für SQLite-Testläufe existiert bewusst ein ORM-Fallback, damit automatisierte Tests ohne MariaDB weiterhin ausführbar bleiben.

## 5.3 Komponentenübersicht

```mermaid
graph TD
    subgraph Web
        A[Auth Controller]
        U[User Controller]
        P[Provider Controller]
    end
    subgraph API
        API[API Controller]
        Spec[OpenAPI Spec]
    end
    subgraph Services
        Utils[Auth, RideFlow, Vehicle, Time Utils]
        QR[QR Generator]
    end
    subgraph Data
        Models[SQLAlchemy Models]
        Schema[db/schema.sql]
    end
    A --> Models
    U --> Models
    P --> Models
    API --> Models
    Models --> Schema
    API --> Spec
    U --> Utils
    P --> Utils
    U --> QR
    P --> QR
```

Die Komponenten interagieren wie folgt:

- Die drei Web-Controller bedienen die Browser-UI.
- `api_controller` stellt JSON-Endpunkte bereit und nutzt die OpenAPI-Spezifikation.
- Utilities (Auth, RideFlow, Vehicle, Time, QR) kapseln wiederverwendbare Logik.
- Modelle greifen auf das SQL-Schema zu; Stored Procedures leben in `db/schema.sql`.

## 5.4 Sequenzdiagramme wesentlicher Abläufe

### 5.4.1 Fahrt starten

```mermaid
sequenceDiagram
    participant User as Fahrer:in
    participant UI as User Controller
    participant Model as Ride/Vehicle Model
    participant DB as MariaDB

    User->>UI: Formular "Fahrt starten"
    UI->>Model: Prüfe aktive Fahrt / Fahrzeugstatus
    Model->>DB: SELECT rides, vehicles
    DB-->>Model: Resultate
    UI->>Model: start_ride_flow(user, vehicle)
    Model->>DB: CALL sp_fahrt_starten(user, vehicle)
    Model->>DB: UPDATE vehicle.gps_(lat,long)
    DB-->>Model: Commit
    Model-->>UI: ride_id, Status
    UI-->>User: Erfolgsmeldung + Aktive Fahrt
```

### 5.4.2 Fahrt beenden inkl. Payment

```mermaid
sequenceDiagram
    participant User as Fahrer:in
    participant UI as User Controller
    participant Model as Ride/Payment Model
    participant Util as apply_battery_drain
    participant DB as MariaDB

    User->>UI: Formular "Fahrt beenden" (km, Payment)
    UI->>Model: lade Ride, PaymentMethod
    Model->>DB: SELECT ride/payment
    DB-->>Model: Daten
    UI->>Model: end_ride_flow(ride, km, payment)
    Model->>DB: CALL sp_fahrt_beenden(ride, km, payment)
    Model->>Util: apply_battery_drain(vehicle, minuten, km)
    Util-->>Model: aktualisierte Batterie
    Model->>DB: UPDATE vehicle.akku_status
    DB-->>Model: Commit
    Model-->>UI: Ride inkl. Kosten
    UI-->>User: Bestätigung + neue Statistik
```

### 5.4.3 Fahrzeug per API anlegen

```mermaid
sequenceDiagram
    participant Provider as Provider (API Client)
    participant API as /api/vehicles POST
    participant Model as Vehicle Model
    participant DB as MariaDB

    Provider->>API: JSON (Token, Fahrzeugdaten)
    API->>Model: validate + create Vehicle
    Model->>DB: INSERT vehicle
    DB-->>Model: Fahrzeug-ID
    Model-->>API: Vehicle-Objekt
    API-->>Provider: 201 Created + JSON
```

## 5.5 Deployment- und Infrastrukturübersicht

```mermaid
flowchart LR
    subgraph Host
        subgraph Compose["Docker Compose"]
            App["Container: scootcity-app<br/>Gunicorn + Flask"]
            DB["Container: mariadb-dbwe<br/>MariaDB + Volume db/data"]
        end
    end
    Dev["Entwicklungsrechner / CI"] -->|docker build/push| App
    App -->|SQLAlchemy| DB
    UserBrowser[[Browser]] -->|HTTP 8000| App
    ProviderClient[[API Client]] -->|HTTP JSON /api| App
```

`docker-entrypoint.sh` initialisiert beim Start das Schema via `scripts/init_db.py`. Konfiguration (DB-URL, Tarife, BASE_URL, Secret Key) erfolgt über Environment-Variablen bzw. `compose.yml`. Die Container sind entkoppelt, sodass MariaDB durch einen Managed Service ersetzt werden könnte. Gunicorn kann über zusätzliche Worker skaliert werden; Logs laufen über stdout und lassen sich via `docker logs` sammeln.

## 5.6 Abweichungen & Technologiebegründung

Die Aufgabenstellung erlaubt mehrere relationale DB-Systeme. Im Unterricht wurde vor allem **MSSQL** behandelt, in diesem Projekt kam jedoch **MariaDB** zum Einsatz. Gründe:

- **Konsistenz mit dem Stack**: MariaDB passt nahtlos zur Python/Flask-Umgebung (SQLAlchemy + PyMySQL) und reduziert Konfigurationsaufwand.
- **Docker-Support**: Für MariaDB existieren schlanke, gut dokumentierte Container-Images; das Setup ist lokal und im Deployment identisch reproduzierbar.
- **Kosten/Nutzung**: MariaDB ist Open-Source und in der Praxis häufig im Web-Stack anzutreffen, was Betrieb und Hosting vereinfacht.
- **Abgrenzung zu MSSQL**: MSSQL wäre möglich, würde aber zusätzliche Treiber/Tooling benötigen und die Installationshürde erhöhen, ohne einen funktionalen Mehrwert für die Anforderungen zu liefern.
