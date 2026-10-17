"""
Backfill TimescaleDB with simulated historical ticks.

Uses the same simulation engine and symbols as the live producer, stepping
every --step seconds during IST market hours on weekdays.

Postgres is only reachable on the internal Docker network, so run this
inside the consumer image (which has psycopg2 and the DB settings):

    docker compose run --rm -v "$PWD:/repo" -w /repo consumer \
        python dev/generate_historical_data.py --days 7

Re-running is safe: existing (ts, symbol) rows are skipped.
"""

import argparse
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "app"))
sys.path.insert(0, str(REPO_ROOT / "consumer"))

from psycopg2.extras import execute_values  # noqa: E402

from helper import INSERT_SQL, get_psql_conn  # noqa: E402
from simulation import IST, MARKET_CLOSE, MARKET_OPEN, MarketSimulator  # noqa: E402


def generate_historical_data(days: int, step_seconds: int, seed: int | None) -> None:
    sim = MarketSimulator(seed=seed)
    conn = get_psql_conn()

    today = datetime.now(IST).date()
    start_day = today - timedelta(days=days)
    step = timedelta(seconds=step_seconds)
    total = 0

    try:
        day = start_day
        while day < today:
            if day.weekday() < 5:
                ts = datetime.combine(day, MARKET_OPEN, tzinfo=IST)
                end = datetime.combine(day, MARKET_CLOSE, tzinfo=IST)
                rows = []
                while ts <= end:
                    ts_utc = ts.astimezone(timezone.utc)
                    for symbol, price, volume in sim.step(ts_utc, dt=step_seconds):
                        rows.append((ts_utc, symbol, price, volume))
                    ts += step

                with conn.cursor() as cur:
                    execute_values(cur, INSERT_SQL, rows, page_size=1000)
                conn.commit()
                total += len(rows)
                print(f"Inserted {len(rows)} rows for {day}")
            day += timedelta(days=1)
    finally:
        conn.close()

    print(f"Historical data generation completed ({total} rows).")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--days", type=int, default=7,
                        help="number of past days to generate (retention is 30 days)")
    parser.add_argument("--step", type=int, default=60,
                        help="seconds between generated ticks")
    parser.add_argument("--seed", type=int, default=None, help="random seed")
    args = parser.parse_args()
    generate_historical_data(args.days, args.step, args.seed)


if __name__ == "__main__":
    main()
