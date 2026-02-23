from __future__ import annotations

import os
import time
from pathlib import Path

import pymysql
from sqlalchemy.engine import make_url

SCHEMA_PATH = Path("db/schema.sql")
RETRIES = int(os.environ.get("DB_INIT_RETRIES", 10))
SLEEP = int(os.environ.get("DB_INIT_SLEEPTIME", 3))


def parse_db_config(url_str: str) -> dict:
    # DATABASE_URL zerlegen, damit PyMySQL connecten kann.
    url = make_url(url_str)
    return {
        "host": url.host or "localhost",
        "port": url.port or 3306,
        "user": url.username or "root",
        "password": url.password or "",
        "database": url.database,
    }


def wait_for_connection(cfg: dict) -> pymysql.connections.Connection:
    # DB kann beim Container-Start kurz brauchen.
    for attempt in range(RETRIES):
        try:
            conn = pymysql.connect(
                host=cfg["host"],
                port=int(cfg["port"]),
                user=cfg["user"],
                password=cfg["password"],
                autocommit=True,
                client_flag=pymysql.constants.CLIENT.MULTI_STATEMENTS,
            )
            return conn
        except pymysql.err.OperationalError:
            if attempt == RETRIES - 1:
                raise
            time.sleep(SLEEP)
    raise RuntimeError("Unable to connect to MariaDB")


def database_exists(conn, database: str) -> bool:
    with conn.cursor() as cursor:
        cursor.execute("SHOW DATABASES LIKE %s", (database,))
        return cursor.fetchone() is not None


def table_exists(conn, database: str, table: str) -> bool:
    with conn.cursor() as cursor:
        cursor.execute(
            """
            SELECT COUNT(*)
            FROM information_schema.tables
            WHERE table_schema=%s AND table_name=%s
            """,
            (database, table),
        )
        return cursor.fetchone()[0] > 0


def run_schema(conn, schema_path: Path) -> None:
    # SQL-Script in einzelne Statements splitten und ausfuehren.
    script = schema_path.read_text(encoding="utf-8")
    with conn.cursor() as cursor:
        for statement in split_statements(script):
            if statement:
                cursor.execute(statement)


def split_statements(script: str):
    delimiter = ";"
    statement_lines: list[str] = []
    for line in script.splitlines():
        stripped = line.strip()
        if not stripped:
            statement_lines.append(line)
            continue
        if stripped.startswith("--") or stripped.startswith("#"):
            continue
        if stripped.upper().startswith("DELIMITER "):
            delimiter = stripped.split()[1]
            continue
        statement_lines.append(line)
        candidate = "\n".join(statement_lines).strip()
        if delimiter and candidate.endswith(delimiter):
            yield candidate[: -len(delimiter)].strip()
            statement_lines = []
    if statement_lines:
        candidate = "\n".join(statement_lines).strip()
        if candidate:
            yield candidate


def ensure_vehicle_type_table(conn, database: str) -> None:
    # Sicherheitsnetz fuer Fahrzeugtypen (falls Schema alt ist).
    with conn.cursor() as cursor:
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{database}`")
        cursor.execute(f"USE `{database}`")
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS fahrzeugtyp (
                fahrzeugtyp_id INT AUTO_INCREMENT PRIMARY KEY,
                bezeichnung VARCHAR(100) NOT NULL UNIQUE,
                grundpreis DECIMAL(8,2) NOT NULL DEFAULT 1.00,
                minutenpreis DECIMAL(8,2) NOT NULL DEFAULT 0.35,
                ist_aktiv TINYINT(1) NOT NULL DEFAULT 1
            ) ENGINE=InnoDB;
            """
        )
        cursor.executemany(
            "INSERT IGNORE INTO fahrzeugtyp (bezeichnung, grundpreis, minutenpreis) VALUES (%s, %s, %s)",
            [("E-Scooter", 1.00, 0.35), ("E-Bike", 1.50, 0.45)],
        )


def main() -> None:
    # Entry point fuer Container-Startup.
    db_url = os.environ.get("DATABASE_URL")
    if not db_url or not SCHEMA_PATH.exists():
        return
    cfg = parse_db_config(db_url)
    conn = wait_for_connection(cfg)
    db_exists = database_exists(conn, cfg["database"])
    if not db_exists or not table_exists(conn, cfg["database"], "nutzer"):
        schema_path = SCHEMA_PATH
        run_schema(conn, schema_path)
    ensure_vehicle_type_table(conn, cfg["database"])


if __name__ == "__main__":
    main()
