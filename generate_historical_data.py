import random
from datetime import datetime, timedelta, time
from dateutil.relativedelta import relativedelta

from helper import get_psql_conn

SYMBOLS = ["NIFTY", "BANKNIFTY", "RELIANCE", "TCS", "INFY"]

MARKET_OPEN = time(9, 15)
MARKET_CLOSE = time(15, 30)

def generate_historical_data(start_date, end_date, delta_seconds=1):
    conn = get_psql_conn()
    cur = conn.cursor()

    prices = {s: 100.0 + random.uniform(-10, 10) for s in SYMBOLS}
    vols = {s: 0.01 for s in SYMBOLS}

    current_day = start_date
    while current_day <= end_date:
        if current_day.weekday() >= 5:
            current_day += timedelta(days=1)
            continue

        ts = datetime.combine(current_day, MARKET_OPEN)
        market_end = datetime.combine(current_day, MARKET_CLOSE)
        delta = timedelta(seconds=delta_seconds)

        while ts <= market_end:
            market_factor = random.gauss(0, 0.001)
            for s in SYMBOLS:
                if random.random() < 0.05:
                    vols[s] = max(0.001, vols[s] * random.uniform(0.5, 1.5))

                drift = 0.0002
                indiv_move = random.gauss(drift, vols[s])
                delta_price = market_factor + indiv_move
                old_price = prices[s]
                prices[s] = max(1, prices[s] * (1 + delta_price))

                volume = max(1, int(random.gauss(100 + abs(prices[s] - old_price) * 5000, 30)))

                cur.execute(
                    "INSERT INTO ticks (ts, symbol, price, volume) VALUES (%s, %s, %s, %s)",
                    (ts.isoformat(), s, round(prices[s], 2), volume)
                )
            ts += delta

        conn.commit()
        print(f"Inserted data for {current_day}")
        current_day += timedelta(days=1)

    cur.close()
    conn.close()
    print("Historical data generation completed.")

if __name__ == "__main__":
    end = datetime.now()
    start = end - relativedelta(months=1)
    generate_historical_data(start, end, delta_seconds=60)
