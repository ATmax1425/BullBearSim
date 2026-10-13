import math
from datetime import datetime, timedelta, timezone

import pytest

from simulation import IST, MAX_LOG_DEVIATION, SYMBOLS, MarketSimulator, session_multipliers

BASE = {cfg.symbol: cfg.base_price for cfg in SYMBOLS}
MONDAY = datetime(2026, 9, 7, tzinfo=IST)


def run(sim, days, dt):
    """Step the simulator; return each symbol's min/max price ratio to base."""
    ts = MONDAY.astimezone(timezone.utc)
    lo = {s: math.inf for s in BASE}
    hi = {s: 0.0 for s in BASE}
    for _ in range(int(days * 86400 / dt)):
        for symbol, price, volume in sim.step(ts, dt=dt):
            ratio = price / BASE[symbol]
            lo[symbol] = min(lo[symbol], ratio)
            hi[symbol] = max(hi[symbol], ratio)
            assert volume >= 1
        ts += timedelta(seconds=dt)
    return lo, hi


@pytest.mark.parametrize("seed", [1, 2, 3])
def test_prices_stay_near_base_for_a_month(seed):
    lo, hi = run(MarketSimulator(seed=seed), days=30, dt=10)
    for symbol in BASE:
        assert 0.75 < lo[symbol] and hi[symbol] < 1.35, symbol
    # Indices are the least volatile instruments.
    assert 0.85 < lo["NIFTY"] and hi["NIFTY"] < 1.15


def test_prices_never_leave_safety_band():
    sim = MarketSimulator(seed=0)
    sim.prices = {s: p * 10 for s, p in BASE.items()}  # start far out of range
    ts = MONDAY.astimezone(timezone.utc)
    for symbol, price, _ in sim.step(ts):
        assert abs(math.log(price / BASE[symbol])) <= MAX_LOG_DEVIATION + 1e-3


def test_intraday_move_is_realistic():
    sim = MarketSimulator(seed=7)
    ts = MONDAY.replace(hour=9, minute=15).astimezone(timezone.utc)
    start = dict(sim.prices)
    for _ in range(6 * 3600 + 15 * 60):
        sim.step(ts)
        ts += timedelta(seconds=1)
    assert abs(math.log(sim.prices["NIFTY"] / start["NIFTY"])) < 0.05


def test_seed_is_deterministic():
    ts = MONDAY.astimezone(timezone.utc)
    a, b = MarketSimulator(seed=42), MarketSimulator(seed=42)
    for _ in range(100):
        assert a.step(ts) == b.step(ts)


@pytest.mark.parametrize(
    "ist_time, expected",
    [
        ((2026, 9, 7, 9, 30), (1.50, 1.50)),    # Monday opening
        ((2026, 9, 7, 12, 0), (0.70, 0.70)),    # lunch
        ((2026, 9, 7, 15, 0), (1.30, 1.40)),    # closing session
        ((2026, 9, 7, 20, 0), (0.30, 0.20)),    # after hours
        ((2026, 9, 12, 11, 0), (0.20, 0.10)),   # Saturday
    ],
)
def test_session_multipliers(ist_time, expected):
    ts = datetime(*ist_time, tzinfo=IST).astimezone(timezone.utc)
    assert session_multipliers(ts) == expected
