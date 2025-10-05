-- Create table for ticks
CREATE TABLE IF NOT EXISTS ticks (
    ts TIMESTAMPTZ NOT NULL,
    symbol TEXT NOT NULL,
    price DOUBLE PRECISION NOT NULL,
    volume INT NOT NULL
);

-- Convert to hypertable
SELECT create_hypertable('ticks', 'ts', if_not_exists => TRUE);

-- Add a retention policy to drop data older than 30 days
SELECT add_retention_policy('ticks', INTERVAL '30 days', if_not_exists => TRUE);
