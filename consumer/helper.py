import psycopg2
import os

DB_CONN = {
    "dbname": os.getenv("POSTGRES_DB", "marketdata"),
    "user": os.getenv("POSTGRES_USER", "postgres"),
    "password": os.getenv("POSTGRES_PASSWORD", "postgres"),
    "host": os.getenv("POSTGRES_HOST", "postgres"),
    "port": int(os.getenv("POSTGRES_PORT", 5432)),
}

DB_URI = (
    f"postgresql+psycopg2://{DB_CONN['user']}:{DB_CONN['password']}"
    f"@{DB_CONN['host']}:{DB_CONN['port']}/{DB_CONN['dbname']}"
)

def get_psql_conn():
    return psycopg2.connect(**DB_CONN)


def safe_batch_insert(conn, cur, batch):
    try:
        cur.executemany(
            """
            INSERT INTO ticks (ts, symbol, price, volume)
            VALUES (%s,%s,%s,%s)
            ON CONFLICT (ts, symbol) DO NOTHING
            """,
            batch
        )
        conn.commit()
        return conn, cur
    except psycopg2.OperationalError as e:
        print(f"DB error, reconnecting: {e}")
        try:
            conn.rollback()
        except Exception:
            pass

        conn = get_psql_conn()
        cur = conn.cursor()

        cur.executemany(
            """
            INSERT INTO ticks (ts, symbol, price, volume)
            VALUES (%s,%s,%s,%s)
            ON CONFLICT (ts, symbol) DO NOTHING
            """,
            batch
        )
        conn.commit()
        return conn, cur
