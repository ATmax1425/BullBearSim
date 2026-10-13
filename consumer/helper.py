import json
import logging
import math
import os
import time
from datetime import datetime
from typing import Optional, Tuple

import psycopg2
from psycopg2.extras import execute_values

log = logging.getLogger("consumer")

DB_CONN = {
    "dbname": os.getenv("POSTGRES_DB", "marketdata"),
    "user": os.getenv("POSTGRES_USER", "postgres"),
    "password": os.environ.get("POSTGRES_PASSWORD"),
    "host": os.getenv("POSTGRES_HOST", "postgres"),
    "port": int(os.getenv("POSTGRES_PORT", 5432)),
}

INSERT_SQL = """
    INSERT INTO ticks (ts, symbol, price, volume)
    VALUES %s
    ON CONFLICT (ts, symbol) DO NOTHING
"""

INT32_MAX = 2**31 - 1

Row = Tuple[datetime, str, float, int]


def get_psql_conn():
    return psycopg2.connect(**DB_CONN)


def parse_tick(raw: bytes) -> Optional[Row]:
    """Decode and validate one Kafka message; return None if it is malformed."""
    try:
        data = json.loads(raw.decode("utf-8"))
        ts = datetime.fromisoformat(data["ts"])
        symbol = data["symbol"]
        price = float(data["price"])
        volume = data["volume"]
    except (UnicodeDecodeError, ValueError, TypeError, KeyError, AttributeError):
        return None

    if ts.tzinfo is None:
        return None
    if not isinstance(symbol, str) or not symbol:
        return None
    if not math.isfinite(price) or price <= 0:
        return None
    if isinstance(volume, bool) or not isinstance(volume, int) or not 0 <= volume <= INT32_MAX:
        return None
    return (ts, symbol, price, volume)


class TickWriter:
    """Writes batches to TimescaleDB, reconnecting until the write succeeds."""

    def __init__(self) -> None:
        self._conn = None

    def _connection(self):
        if self._conn is None or self._conn.closed:
            self._conn = get_psql_conn()
        return self._conn

    def _reset(self) -> None:
        if self._conn is not None:
            try:
                self._conn.close()
            except Exception:
                pass
        self._conn = None

    def write(self, rows: list) -> None:
        delay = 1
        while True:
            try:
                conn = self._connection()
                try:
                    with conn.cursor() as cur:
                        execute_values(cur, INSERT_SQL, rows)
                    conn.commit()
                except psycopg2.DatabaseError as exc:
                    if isinstance(exc, psycopg2.OperationalError):
                        raise
                    # A bad row rejected by the database: skip it, keep the rest.
                    conn.rollback()
                    log.error("Batch insert failed (%s); retrying row by row", exc)
                    self._write_rows_individually(conn, rows)
                return
            except (psycopg2.OperationalError, psycopg2.InterfaceError) as exc:
                log.warning("DB unavailable (%s), retrying in %ss", exc, delay)
                self._reset()
                time.sleep(delay)
                delay = min(delay * 2, 30)

    def _write_rows_individually(self, conn, rows: list) -> None:
        for row in rows:
            try:
                with conn.cursor() as cur:
                    execute_values(cur, INSERT_SQL, [row])
                conn.commit()
            except psycopg2.DatabaseError as exc:
                if isinstance(exc, psycopg2.OperationalError):
                    raise
                conn.rollback()
                log.error("Dropping row %r: %s", row, exc)

    def close(self) -> None:
        self._reset()
