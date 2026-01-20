import os

import psycopg2
from dotenv import load_dotenv


def main() -> None:
    load_dotenv()

    host = os.getenv("DB_HOST", "localhost")
    port = int(os.getenv("DB_PORT", "5432"))
    dbname = os.getenv("DB_NAME", "telegram_warehouse")
    user = os.getenv("DB_USER", "postgres")
    password = os.getenv("DB_PASSWORD", "postgres")

    conn = psycopg2.connect(
        host=host, port=port, dbname=dbname, user=user, password=password
    )
    cur = conn.cursor()

    cur.execute(
        """
        select table_schema
        from information_schema.tables
        where table_name = 'fct_messages'
        order by table_schema
        """
    )
    schemas = [r[0] for r in cur.fetchall()]
    print("Schemas containing fct_messages:", schemas)

    cur.execute(
        """
        select table_schema, table_name
        from information_schema.tables
        where table_name in ('fct_messages', 'dim_channels', 'dim_dates')
        order by table_schema, table_name
        """
    )
    print("Core tables found:")
    for schema, table in cur.fetchall():
        print(f" - {schema}.{table}")

    cur.close()
    conn.close()


if __name__ == "__main__":
    main()


