import psycopg2

DB_CONN = {
    "dbname": "marketdata",
    "user": "postgres",
    "password": "postgres",
    "host": "localhost",
    "port": 5432,
}

def get_psql_conn():
    conn = psycopg2.connect(**DB_CONN)
    return conn