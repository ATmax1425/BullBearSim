import psycopg2
import os
from sqlalchemy import create_engine

DB_CONN = {
    "dbname": os.getenv("POSTGRES_DB", "marketdata"),
    "user": os.getenv("POSTGRES_USER", "postgres"),
    "password": os.getenv("POSTGRES_PASSWORD", "postgres"),
    "host": os.getenv("POSTGRES_HOST", "postgres"),
    "port": int(os.getenv("POSTGRES_PORT", 5432)),
}

print(DB_CONN)
DB_URI = (
    f"postgresql+psycopg2://{DB_CONN['user']}:{DB_CONN['password']}"
    f"@{DB_CONN['host']}:{DB_CONN['port']}/{DB_CONN['dbname']}"
)

def get_psql_conn():
    return psycopg2.connect(**DB_CONN)

def get_psql_engine():
    return create_engine(DB_URI)
