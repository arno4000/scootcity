-- ScootCity Datenbankschema (deutsche Bezeichnungen)
-- Ausführen mit: mysql -u root -p < db/schema.sql

DROP DATABASE IF EXISTS scooter_plattform;
CREATE DATABASE scooter_plattform CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE scooter_plattform;

SET NAMES utf8mb4;

-- ---------------------------------------------------------------------------
-- Tabellen löschen (Reihenfolge wegen FK beachten)
-- ---------------------------------------------------------------------------
DROP TABLE IF EXISTS zahlung;
DROP TABLE IF EXISTS zahlungsmittel;
DROP TABLE IF EXISTS ausleihe;
DROP TABLE IF EXISTS fahrzeug;
DROP TABLE IF EXISTS fahrzeugtyp;
DROP TABLE IF EXISTS verleihanbieter;
DROP TABLE IF EXISTS nutzer;

-- ---------------------------------------------------------------------------
-- Nutzer
-- ---------------------------------------------------------------------------
CREATE TABLE nutzer (
    nutzer_id      INT AUTO_INCREMENT PRIMARY KEY,
    name           VARCHAR(120) NOT NULL UNIQUE,
    email          VARCHAR(120) NOT NULL UNIQUE,
    password_hash  VARCHAR(255) NOT NULL,
    api_token      VARCHAR(64) UNIQUE,
    erstellt_am    DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------------
-- Verleihanbieter
-- ---------------------------------------------------------------------------
CREATE TABLE verleihanbieter (
    anbieter_id    INT AUTO_INCREMENT PRIMARY KEY,
    name           VARCHAR(150) NOT NULL UNIQUE,
    email          VARCHAR(120) NOT NULL UNIQUE,
    password_hash  VARCHAR(255) NOT NULL,
    typ            VARCHAR(50) NOT NULL DEFAULT 'firma',
    api_token      VARCHAR(64) UNIQUE,
    erstellt_am    DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------------
-- Fahrzeugtyp (Erweiterbarkeit + Tarife)
-- ---------------------------------------------------------------------------
CREATE TABLE fahrzeugtyp (
    fahrzeugtyp_id INT AUTO_INCREMENT PRIMARY KEY,
    bezeichnung    VARCHAR(100) NOT NULL UNIQUE,
    grundpreis     DECIMAL(8,2) NOT NULL DEFAULT 1.00,
    minutenpreis   DECIMAL(8,2) NOT NULL DEFAULT 0.35,
    ist_aktiv      TINYINT(1) NOT NULL DEFAULT 1
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------------
-- Fahrzeug
-- ---------------------------------------------------------------------------
CREATE TABLE fahrzeug (
    fahrzeug_id     INT AUTO_INCREMENT PRIMARY KEY,
    anbieter_id     INT NOT NULL,
    fahrzeugtyp_id  INT NOT NULL,
    status ENUM('verfuegbar','in_benutzung','wartung','deaktiviert')
           NOT NULL DEFAULT 'verfuegbar',
    akku_status     DECIMAL(5,2) NOT NULL DEFAULT 100.0,
    gps_lat         DECIMAL(10,6) DEFAULT NULL,
    gps_long        DECIMAL(10,6) DEFAULT NULL,
    qr_code         VARCHAR(120) NOT NULL UNIQUE,
    erstellt_am     DATETIME DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_fahrzeug_anbieter FOREIGN KEY (anbieter_id)
        REFERENCES verleihanbieter(anbieter_id) ON DELETE CASCADE,

    CONSTRAINT fk_fahrzeug_typ FOREIGN KEY (fahrzeugtyp_id)
        REFERENCES fahrzeugtyp(fahrzeugtyp_id) ON DELETE RESTRICT,

    INDEX idx_fahrzeug_status (status)
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------------
-- Ausleihe (speichert Tarife historisch)
-- ---------------------------------------------------------------------------
CREATE TABLE ausleihe (
    ausleihe_id     INT AUTO_INCREMENT PRIMARY KEY,
    nutzer_id       INT NOT NULL,
    fahrzeug_id     INT NOT NULL,
    startzeit       DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    endzeit         DATETIME DEFAULT NULL,
    kilometer       DECIMAL(6,2) DEFAULT 0,
    kosten          DECIMAL(8,2) DEFAULT 0,
    grundpreis      DECIMAL(8,2) NOT NULL DEFAULT 0,
    minutenpreis    DECIMAL(8,2) NOT NULL DEFAULT 0,

    CONSTRAINT fk_ausleihe_nutzer FOREIGN KEY (nutzer_id)
        REFERENCES nutzer(nutzer_id) ON DELETE CASCADE,

    CONSTRAINT fk_ausleihe_fahrzeug FOREIGN KEY (fahrzeug_id)
        REFERENCES fahrzeug(fahrzeug_id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------------
-- Zahlungsmittel
-- ---------------------------------------------------------------------------
CREATE TABLE zahlungsmittel (
    zahlungsmittel_id INT AUTO_INCREMENT PRIMARY KEY,
    nutzer_id         INT NOT NULL,
    typ               VARCHAR(50) NOT NULL,
    details           VARCHAR(255) NOT NULL,
    ist_aktiv         TINYINT(1) NOT NULL DEFAULT 1,
    erstellt_am       DATETIME DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_zahlungsmittel_nutzer FOREIGN KEY (nutzer_id)
        REFERENCES nutzer(nutzer_id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------------
-- Zahlung (mehrere pro Ausleihe möglich)
-- ---------------------------------------------------------------------------
CREATE TABLE zahlung (
    zahlung_id        INT AUTO_INCREMENT PRIMARY KEY,
    ausleihe_id       INT NOT NULL,
    zahlungsmittel_id INT NOT NULL,
    zeitpunkt         DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    betrag            DECIMAL(8,2) NOT NULL,
    status ENUM('offen','bezahlt','fehlgeschlagen','erstattet','storniert')
           NOT NULL DEFAULT 'offen',

    CONSTRAINT fk_zahlung_ausleihe FOREIGN KEY (ausleihe_id)
        REFERENCES ausleihe(ausleihe_id) ON DELETE CASCADE,

    CONSTRAINT fk_zahlung_mittel FOREIGN KEY (zahlungsmittel_id)
        REFERENCES zahlungsmittel(zahlungsmittel_id) ON DELETE RESTRICT
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------------
-- Basisdaten
-- ---------------------------------------------------------------------------
INSERT INTO fahrzeugtyp (bezeichnung, grundpreis, minutenpreis)
VALUES
    ('E-Scooter', 1.00, 0.35),
    ('E-Bike',    1.50, 0.45);

INSERT INTO nutzer (name, email, password_hash)
VALUES
    ('Mina Meier', 'mina@example.com', 'hash1'),
    ('Max Maurer', 'max@example.com', 'hash2');

INSERT INTO verleihanbieter (name, email, password_hash)
VALUES
    ('Swift Mobility AG', 'contact@swiftmobility.ch', 'hash3'),
    ('RideOn GmbH', 'hello@rideon.ch', 'hash4');

INSERT INTO fahrzeug (anbieter_id, fahrzeugtyp_id, status, akku_status, gps_lat, gps_long, qr_code)
VALUES
    (1, 1, 'verfuegbar', 91.5, 47.376900, 8.541700, 'SC-1001'),
    (1, 2, 'verfuegbar', 82.0, 47.372000, 8.530000, 'EB-2001');

-- ---------------------------------------------------------------------------
-- Stored Procedure: Fahrt starten
-- ---------------------------------------------------------------------------
DELIMITER $$

CREATE PROCEDURE sp_fahrt_starten(
    IN p_nutzer_id INT,
    IN p_fahrzeug_id INT
)
BEGIN
    DECLARE v_status VARCHAR(20);
    DECLARE v_grundpreis DECIMAL(8,2);
    DECLARE v_minutenpreis DECIMAL(8,2);

    SELECT f.status, t.grundpreis, t.minutenpreis
    INTO v_status, v_grundpreis, v_minutenpreis
    FROM fahrzeug f
    JOIN fahrzeugtyp t ON t.fahrzeugtyp_id = f.fahrzeugtyp_id
    WHERE f.fahrzeug_id = p_fahrzeug_id
    FOR UPDATE;

    IF v_status <> 'verfuegbar' THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Fahrzeug nicht verfuegbar';
    END IF;

    INSERT INTO ausleihe (nutzer_id, fahrzeug_id, grundpreis, minutenpreis)
    VALUES (p_nutzer_id, p_fahrzeug_id, v_grundpreis, v_minutenpreis);

    UPDATE fahrzeug
    SET status = 'in_benutzung'
    WHERE fahrzeug_id = p_fahrzeug_id;
END $$

-- ---------------------------------------------------------------------------
-- Stored Procedure: Fahrt beenden
-- ---------------------------------------------------------------------------
CREATE PROCEDURE sp_fahrt_beenden(
    IN p_ausleihe_id INT,
    IN p_kilometer DECIMAL(6,2),
    IN p_zahlungsmittel_id INT
)
BEGIN
    DECLARE v_start DATETIME;
    DECLARE v_fahrzeug_id INT;
    DECLARE v_grundpreis DECIMAL(8,2);
    DECLARE v_minutenpreis DECIMAL(8,2);
    DECLARE v_minuten INT;
    DECLARE v_kosten DECIMAL(8,2);

    SELECT startzeit, fahrzeug_id, grundpreis, minutenpreis
    INTO v_start, v_fahrzeug_id, v_grundpreis, v_minutenpreis
    FROM ausleihe
    WHERE ausleihe_id = p_ausleihe_id
    FOR UPDATE;

    SET v_minuten = TIMESTAMPDIFF(MINUTE, v_start, NOW());
    IF v_minuten < 1 THEN
        SET v_minuten = 1;
    END IF;

    SET v_kosten = ROUND(v_grundpreis + v_minuten * v_minutenpreis, 2);

    UPDATE ausleihe
    SET endzeit = NOW(),
        kilometer = p_kilometer,
        kosten = v_kosten
    WHERE ausleihe_id = p_ausleihe_id;

    UPDATE fahrzeug
    SET status = 'verfuegbar'
    WHERE fahrzeug_id = v_fahrzeug_id;

    IF p_zahlungsmittel_id IS NOT NULL THEN
        INSERT INTO zahlung (ausleihe_id, zahlungsmittel_id, betrag, status)
        VALUES (p_ausleihe_id, p_zahlungsmittel_id, v_kosten, 'bezahlt');
    END IF;
END $$

DELIMITER ;

-- Ende
