import psycopg2
from sqlalchemy import create_engine

DB_CONN = {
    "dbname": "marketdata",
    "user": "postgres",
    "password": "postgres",
    "host": "localhost",
    "port": 5432,
}
DB_URI = "postgresql+psycopg2://postgres:postgres@localhost:5432/marketdata"

def get_psql_conn():
    conn = psycopg2.connect(**DB_CONN)
    return conn

def get_psql_engine():
    engine = create_engine(DB_URI)
    return engine
