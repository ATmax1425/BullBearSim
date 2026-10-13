import json
from datetime import datetime, timezone

import pytest

from helper import parse_tick


def encode(**fields):
    tick = {"ts": "2026-09-07T04:00:00+00:00", "symbol": "TCS", "price": 4200.5, "volume": 1200}
    tick.update(fields)
    return json.dumps(tick).encode()


def test_parses_valid_tick():
    assert parse_tick(encode()) == (
        datetime(2026, 9, 7, 4, 0, tzinfo=timezone.utc), "TCS", 4200.5, 1200,
    )


@pytest.mark.parametrize(
    "raw",
    [
        b"not json",
        b"\xff\xfe",
        b"[]",
        json.dumps({"symbol": "TCS"}).encode(),
        encode(ts="yesterday"),
        encode(ts="2026-09-07T04:00:00"),   # no timezone
        encode(symbol=""),
        encode(symbol=5),
        encode(price="NaN"),
        encode(price=-1),
        encode(volume=1.5),
        encode(volume=-3),
        encode(volume=2**31),
        encode(volume=True),
    ],
)
def test_rejects_malformed_tick(raw):
    assert parse_tick(raw) is None
