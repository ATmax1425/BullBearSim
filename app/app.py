import os
import json
import random
import asyncio
from enum import Enum
from dataclasses import dataclass
from zoneinfo import ZoneInfo
from aiokafka import AIOKafkaProducer
from datetime import datetime, timezone, time
from typing import List, Tuple


KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP", "kafka:9092")
TOPIC_TICKS = "ticks"

IST = ZoneInfo("Asia/Kolkata")
MARKET_OPEN = time(9, 15)
MARKET_CLOSE = time(15, 30)


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

class Sector(Enum):
    INDEX   = "index"
    BANKING = "banking"
    IT      = "it"
    ENERGY  = "energy"
    FMCG    = "fmcg"


@dataclass
class SymbolConfig:
    symbol: str
    base_price: float
    volatility: float
    base_volume: int
    volume_std: int
    sector: Sector


SYMBOLS: List[SymbolConfig] = [
    SymbolConfig("NIFTY",     24500.0, 0.0004, 100000, 20000, Sector.INDEX),
    SymbolConfig("BANKNIFTY", 54000.0, 0.0005,  60000, 12000, Sector.INDEX),
    SymbolConfig("RELIANCE",   2900.0, 0.0006, 800000, 160000, Sector.ENERGY),
    SymbolConfig("HDFCBANK",   1800.0, 0.0007, 500000, 100000, Sector.BANKING),
    SymbolConfig("ICICIBANK",  1300.0, 0.0008, 600000, 120000, Sector.BANKING),
    SymbolConfig("SBIN",        800.0, 0.0010, 350000,  70000, Sector.BANKING),
    SymbolConfig("TCS",        4200.0, 0.0006, 300000,  60000, Sector.IT),
    SymbolConfig("INFY",       1600.0, 0.0008, 450000,  90000, Sector.IT),
    SymbolConfig("HINDUNILVR", 2500.0, 0.0005, 200000,  40000, Sector.FMCG),
    SymbolConfig("NESTLEIND",  2200.0, 0.0005, 150000,  30000, Sector.FMCG),
    SymbolConfig("BRITANNIA",  5000.0, 0.0009, 100000,  20000, Sector.FMCG),
]


# ---------------------------------------------------------------------------
# Market Session — volatility & volume multipliers based on IST time
# ---------------------------------------------------------------------------

SESSION_OPENING       = time(10, 0)
SESSION_MID_MORNING   = time(11, 30)
SESSION_LUNCH         = time(13, 0)
SESSION_AFTERNOON     = time(14, 45)


def session_multipliers(ts: datetime) -> Tuple[float, float]:
    """Return (volatility_multiplier, volume_multiplier) for the given UTC timestamp."""
    ist = ts.astimezone(IST)
    t = ist.time()

    # Weekends — very quiet
    if ist.weekday() >= 5:
        return (0.20, 0.10)

    # Outside market hours — low activity
    if t < MARKET_OPEN or t > MARKET_CLOSE:
        return (0.30, 0.20)

    if t < SESSION_OPENING:
        return (1.50, 1.50)
    if t < SESSION_MID_MORNING:
        return (1.00, 1.00)
    if t < SESSION_LUNCH:
        return (0.70, 0.70)
    if t < SESSION_AFTERNOON:
        return (1.00, 1.00)
    return (1.30, 1.40)


# ---------------------------------------------------------------------------
# Market Trend Engine — mean-reverting sentiment that influences all symbols
# ---------------------------------------------------------------------------

class Trend(Enum):
    BULLISH = "bullish"
    NEUTRAL = "neutral"
    BEARISH = "bearish"


class TrendEngine:
    MIN_AGE = 300          # minimum ticks before trend can change
    TRANSITION_P = 0.003   # probability of transition per tick after min age

    def __init__(self) -> None:
        self.state = Trend.NEUTRAL
        self.drift = 0.0
        self._tick = 0
        self._start = 0

    def _choose_next(self, current: Trend) -> Trend:
        if current == Trend.BULLISH:
            return Trend.NEUTRAL if random.random() < 0.9 else Trend.BEARISH
        if current == Trend.BEARISH:
            return Trend.NEUTRAL if random.random() < 0.9 else Trend.BULLISH
        return random.choice([Trend.BULLISH, Trend.BEARISH])

    def update(self) -> None:
        self._tick += 1
        age = self._tick - self._start

        if age > self.MIN_AGE and random.random() < self.TRANSITION_P:
            self.state = self._choose_next(self.state)
            self._start = self._tick

        if self.state == Trend.BULLISH:
            self.drift = random.uniform(0.0001, 0.0003)
        elif self.state == Trend.BEARISH:
            self.drift = random.uniform(-0.0003, -0.0001)
        else:
            self.drift = random.uniform(-0.00005, 0.00005)


# ---------------------------------------------------------------------------
# Sector Correlation Engine — adds shared noise within each sector
# ---------------------------------------------------------------------------

class SectorEngine:
    def __init__(self) -> None:
        self.factors: dict[str, float] = {}

    def update(self) -> None:
        self.factors = {s.value: random.gauss(0, 0.00015) for s in Sector}


# ---------------------------------------------------------------------------
# Volume Generator
# ---------------------------------------------------------------------------

def generate_volume(cfg: SymbolConfig, delta: float, vol_mult: float) -> int:
    base = cfg.base_volume * vol_mult
    std = cfg.volume_std * vol_mult
    spike = abs(delta) * base * 50

    if random.random() < 0.02:
        spike *= random.uniform(3, 8)

    return max(1, int(random.gauss(base + spike, std)))


# ---------------------------------------------------------------------------
# Main Producer Loop
# ---------------------------------------------------------------------------

async def tick_producer() -> None:
    print("Starting tick producer...")
    producer = AIOKafkaProducer(bootstrap_servers=KAFKA_BOOTSTRAP)
    await producer.start()
    print("Producer started")

    prices: dict[str, float] = {
        cfg.symbol: cfg.base_price * (1 + random.uniform(-0.005, 0.005))
        for cfg in SYMBOLS
    }

    trend = TrendEngine()
    sector = SectorEngine()

    try:
        while True:
            ts = datetime.now(timezone.utc)
            vol_mult, vol_volume_mult = session_multipliers(ts)

            trend.update()
            sector.update()

            market_factor = random.gauss(trend.drift, 0.0002)

            for cfg in SYMBOLS:
                sector_factor = sector.factors[cfg.sector.value]
                indiv_noise = random.gauss(0, cfg.volatility * vol_mult)
                delta = market_factor + sector_factor + indiv_noise

                old = prices[cfg.symbol]
                prices[cfg.symbol] = max(0.01, old * (1 + delta))

                volume = generate_volume(cfg, delta, vol_volume_mult)

                msg = {
                    "ts": ts.isoformat(),
                    "symbol": cfg.symbol,
                    "price": round(prices[cfg.symbol], 2),
                    "volume": volume,
                }
                await producer.send_and_wait(TOPIC_TICKS, json.dumps(msg).encode())

            await asyncio.sleep(1)
    finally:
        await producer.stop()


async def main() -> None:
    await asyncio.gather(tick_producer())


if __name__ == "__main__":
    asyncio.run(main())
