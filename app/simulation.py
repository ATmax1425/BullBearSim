"""
Synthetic market simulation used by the tick producer.

Each symbol's log-price follows a mean-reverting (Ornstein-Uhlenbeck) walk
around its base price, driven by four components:

  * market factor  - shared noise plus a slowly changing trend drift
  * sector factor  - noise shared by symbols in the same sector
  * idiosyncratic  - per-symbol noise
  * mean reversion - pulls the price back toward its base price

All rates are expressed per second, so the simulator can be stepped at any
interval (1s for the live producer, 60s for historical backfill).
"""

import math
import random
from dataclasses import dataclass
from datetime import datetime, time
from enum import Enum
from typing import List, Optional, Tuple
from zoneinfo import ZoneInfo


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
    volatility: float      # idiosyncratic noise, std-dev of log-return per second
    base_volume: int
    volume_std: int
    sector: Sector


SYMBOLS: List[SymbolConfig] = [
    SymbolConfig("NIFTY",     24500.0, 0.00002, 100000, 20000, Sector.INDEX),
    SymbolConfig("BANKNIFTY", 54000.0, 0.00003,  60000, 12000, Sector.INDEX),
    SymbolConfig("RELIANCE",   2900.0, 0.00007, 800000, 160000, Sector.ENERGY),
    SymbolConfig("HDFCBANK",   1800.0, 0.00007, 500000, 100000, Sector.BANKING),
    SymbolConfig("ICICIBANK",  1300.0, 0.00008, 600000, 120000, Sector.BANKING),
    SymbolConfig("SBIN",        800.0, 0.00010, 350000,  70000, Sector.BANKING),
    SymbolConfig("TCS",        4200.0, 0.00007, 300000,  60000, Sector.IT),
    SymbolConfig("INFY",       1600.0, 0.00008, 450000,  90000, Sector.IT),
    SymbolConfig("HINDUNILVR", 2500.0, 0.00005, 200000,  40000, Sector.FMCG),
    SymbolConfig("NESTLEIND",  2200.0, 0.00005, 150000,  30000, Sector.FMCG),
    SymbolConfig("BRITANNIA",  5000.0, 0.00007, 100000,  20000, Sector.FMCG),
]

MARKET_SIGMA = 0.00004     # market-wide noise per second
SECTOR_SIGMA = 0.000025    # sector noise per second

# Pull toward base price. Gives a stationary spread of roughly +/-2-5% around
# the base price; half-life of a deviation is about 8 days.
MEAN_REVERSION = 1e-6      # per second

# Hard safety band on the deviation from base price (log space, ~ -26%/+35%).
MAX_LOG_DEVIATION = 0.30


# ---------------------------------------------------------------------------
# Market Session — volatility & volume multipliers based on IST time
# ---------------------------------------------------------------------------

SESSION_OPENING       = time(10, 0)
SESSION_MID_MORNING   = time(11, 30)
SESSION_LUNCH         = time(13, 0)
SESSION_AFTERNOON     = time(14, 45)


def session_multipliers(ts: datetime) -> Tuple[float, float]:
    """Return (volatility_multiplier, volume_multiplier) for the given timestamp."""
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
# Market Trend Engine — market phases with smoothly changing drift
# ---------------------------------------------------------------------------

class Trend(Enum):
    BULLISH = "bullish"
    NEUTRAL = "neutral"
    BEARISH = "bearish"


class TrendEngine:
    MIN_AGE = 300.0            # minimum seconds before the phase can change
    TRANSITION_RATE = 0.003    # chance of a phase change per second after MIN_AGE
    SMOOTHING = 120.0          # seconds for drift to move ~63% toward its target
    DRIFT_RANGE = (0.000002, 0.000004)   # |drift| per second while trending

    def __init__(self, rng: random.Random) -> None:
        self._rng = rng
        self.state = Trend.NEUTRAL
        self.drift = 0.0
        self._target = 0.0
        self._age = 0.0

    def _choose_next(self, current: Trend) -> Trend:
        if current == Trend.BULLISH:
            return Trend.NEUTRAL if self._rng.random() < 0.9 else Trend.BEARISH
        if current == Trend.BEARISH:
            return Trend.NEUTRAL if self._rng.random() < 0.9 else Trend.BULLISH
        return self._rng.choice([Trend.BULLISH, Trend.BEARISH])

    def update(self, dt: float) -> None:
        self._age += dt
        p_change = 1.0 - (1.0 - self.TRANSITION_RATE) ** dt
        if self._age > self.MIN_AGE and self._rng.random() < p_change:
            self.state = self._choose_next(self.state)
            self._age = 0.0
            magnitude = self._rng.uniform(*self.DRIFT_RANGE)
            if self.state == Trend.BULLISH:
                self._target = magnitude
            elif self.state == Trend.BEARISH:
                self._target = -magnitude
            else:
                self._target = 0.0

        alpha = 1.0 - math.exp(-dt / self.SMOOTHING)
        self.drift += (self._target - self.drift) * alpha


# ---------------------------------------------------------------------------
# Simulator
# ---------------------------------------------------------------------------

class MarketSimulator:
    def __init__(
        self,
        symbols: List[SymbolConfig] = SYMBOLS,
        seed: Optional[int] = None,
    ) -> None:
        self.symbols = symbols
        self.rng = random.Random(seed)
        self.trend = TrendEngine(self.rng)
        self.prices: dict[str, float] = {
            cfg.symbol: cfg.base_price * (1 + self.rng.uniform(-0.005, 0.005))
            for cfg in symbols
        }

    def _volume(
        self, cfg: SymbolConfig, z: float, vol_volume_mult: float, dt: float
    ) -> int:
        base = cfg.base_volume * vol_volume_mult
        std = cfg.volume_std * vol_volume_mult
        # Bigger moves (in standard deviations) trade more volume.
        spike = base * 0.25 * min(abs(z), 4.0)
        if self.rng.random() < 0.02:
            spike += base * self.rng.uniform(1, 4)
        per_second = max(1.0, self.rng.gauss(base + spike, std))
        return max(1, int(per_second * dt))

    def step(self, ts: datetime, dt: float = 1.0) -> List[Tuple[str, float, int]]:
        """Advance the market by dt seconds; return (symbol, price, volume) per symbol."""
        vol_mult, vol_volume_mult = session_multipliers(ts)
        self.trend.update(dt)

        sqrt_dt = math.sqrt(dt)
        market = (
            self.trend.drift * vol_mult * dt
            + self.rng.gauss(0, MARKET_SIGMA * vol_mult) * sqrt_dt
        )
        sectors = {
            s: self.rng.gauss(0, SECTOR_SIGMA * vol_mult) * sqrt_dt for s in Sector
        }
        reversion = 1.0 - math.exp(-MEAN_REVERSION * dt)

        out = []
        for cfg in self.symbols:
            idio = self.rng.gauss(0, cfg.volatility * vol_mult) * sqrt_dt
            deviation = math.log(self.prices[cfg.symbol] / cfg.base_price)
            log_return = market + sectors[cfg.sector] + idio - deviation * reversion

            deviation = max(
                -MAX_LOG_DEVIATION,
                min(MAX_LOG_DEVIATION, deviation + log_return),
            )
            self.prices[cfg.symbol] = cfg.base_price * math.exp(deviation)

            sigma = math.sqrt(
                MARKET_SIGMA ** 2 + SECTOR_SIGMA ** 2 + cfg.volatility ** 2
            ) * vol_mult * sqrt_dt
            z = log_return / sigma if sigma > 0 else 0.0
            volume = self._volume(cfg, z, vol_volume_mult, dt)

            out.append((cfg.symbol, round(self.prices[cfg.symbol], 2), volume))
        return out
