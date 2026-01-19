"""
Load raw Telegram JSON data from the data lake into PostgreSQL.

Creates `raw.telegram_messages` and bulk-loads messages while keeping the
original JSON payload. Requires environment variables for DB connection.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data" / "raw" / "telegram_messages"

load_dotenv()


def get_db_params() -> Dict[str, str]:
    """Read database connection parameters from environment."""
    required = ["DB_HOST", "DB_NAME", "DB_USER", "DB_PASSWORD"]
    missing = [key for key in required if not os.getenv(key)]
    if missing:
        raise ValueError(f"Missing required env vars: {', '.join(missing)}")

    return {
        "host": os.getenv("DB_HOST"),
        "port": int(os.getenv("DB_PORT", "5432")),
        "dbname": os.getenv("DB_NAME"),
        "user": os.getenv("DB_USER"),
        "password": os.getenv("DB_PASSWORD"),
        "schema": os.getenv("DB_SCHEMA", "raw"),
    }


def ensure_schema_and_table(conn, schema: str):
    """Create schema/table if they do not exist."""
    with conn.cursor() as cur:
        cur.execute(f"CREATE SCHEMA IF NOT EXISTS {schema};")
        cur.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {schema}.telegram_messages (
                message_id      BIGINT NOT NULL,
                channel_name    TEXT   NOT NULL,
                message_date    TIMESTAMPTZ,
                message_text    TEXT,
                has_media       BOOLEAN,
                image_path      TEXT,
                views           INTEGER,
                forwards        INTEGER,
                raw_json        JSONB,
                PRIMARY KEY (message_id, channel_name)
            );
            """
        )
    conn.commit()


def iter_message_files(data_dir: Path) -> Iterable[Path]:
    """Yield all JSON files under the partitioned data lake path."""
    if not data_dir.exists():
        return []
    for date_dir in sorted(data_dir.iterdir()):
        if not date_dir.is_dir():
            continue
        for json_file in sorted(date_dir.glob("*.json")):
            yield json_file


def load_json_messages(json_path: Path) -> List[Dict]:
    """Load a list of messages from a JSON file."""
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as exc:  # pragma: no cover - log and skip bad files
        print(f"[WARN] Failed to read {json_path}: {exc}")
        return []


def parse_message(msg: Dict) -> Tuple:
    """Parse a single message dict into DB-ready tuple."""
    msg_date = msg.get("message_date")
    dt: Optional[datetime] = None
    if msg_date:
        try:
            dt = datetime.fromisoformat(msg_date)
        except ValueError:
            dt = None

    return (
        msg.get("message_id"),
        msg.get("channel_name"),
        dt,
        msg.get("message_text") or "",
        bool(msg.get("has_media")),
        msg.get("image_path"),
        msg.get("views"),
        msg.get("forwards"),
        json.dumps(msg, ensure_ascii=False),
    )


def bulk_insert_messages(conn, schema: str, rows: List[Tuple]):
    """Insert rows with upsert protection on (message_id, channel_name)."""
    if not rows:
        return
    insert_sql = f"""
        INSERT INTO {schema}.telegram_messages (
            message_id, channel_name, message_date, message_text,
            has_media, image_path, views, forwards, raw_json
        )
        VALUES %s
        ON CONFLICT (message_id, channel_name) DO NOTHING;
    """
    with conn.cursor() as cur:
        execute_values(cur, insert_sql, rows, page_size=500)
    conn.commit()


def main():
    params = get_db_params()
    schema = params.pop("schema")

    print(f"[INFO] Connecting to Postgres at {params['host']}:{params['port']}")
    conn = psycopg2.connect(**params)
    try:
        ensure_schema_and_table(conn, schema)

        total_rows = 0
        for json_file in iter_message_files(DATA_DIR):
            messages = load_json_messages(json_file)
            rows = [parse_message(m) for m in messages if m.get("message_id") and m.get("channel_name")]
            bulk_insert_messages(conn, schema, rows)
            print(f"[INFO] Loaded {len(rows)} rows from {json_file}")
            total_rows += len(rows)

        print(f"[INFO] Finished loading. Total rows inserted: {total_rows}")
    finally:
        conn.close()
        print("[INFO] Connection closed.")


if __name__ == "__main__":
    main()

