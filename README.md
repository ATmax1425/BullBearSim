# Real-Time Stock Market Streaming

Production-style real-time data engineering pipeline for ingesting, processing, and visualizing market data.
The active pipeline is:

`app/app.py` -> Kafka -> `consumer/consumer_to_db.py` -> TimescaleDB (PostgreSQL)

## Architecture

- Kafka carries live tick events between services
- The producer in `app/app.py` generates market ticks
- The consumer in `consumer/consumer_to_db.py` writes rows into TimescaleDB
- Docker Compose manages the core services
- Nginx fronts the deployed dashboard stack
- Grafana is used for visualization and monitoring

## Design Goals

- Build a decoupled, event-driven pipeline for real-time market data
- Ensure scalability via Kafka-based ingestion and consumer isolation
- Optimize storage for time-series queries using TimescaleDB
- Enable observability through Grafana dashboards
- Support both local development and production deployment setups

## Tech Stack

- Python
- Apache Kafka
- TimescaleDB / PostgreSQL
- Docker Compose
- Nginx
- Grafana

## Project Structure

```text
├── app/
│   ├── app.py
│   ├── Dockerfile
│   └── requirements.txt
├── consumer/
│   ├── consumer_to_db.py
│   ├── helper.py
│   ├── Dockerfile
│   └── requirements.txt
├── dev/
│   ├── generate_historical_data.py
│   └── nginx_local.conf
├── docker-compose.yml
├── init.sql
├── nginx.conf
└── .env.example
```

## Features

- Event-driven pipeline using Kafka for decoupled ingestion and processing
- Real-time data persistence optimized for time-series workloads (TimescaleDB)
- Containerized microservices architecture via Docker Compose
- Reverse proxy setup with Nginx for secure and structured routing
- Grafana dashboards for real-time visualization and monitoring
- Development utilities for local testing and historical data simulation

## Getting Started

### 1. Configure environment

Create a `.env` file from `.env.example` and fill in the required values.

### 2. Start the stack

```bash
docker compose up -d
```

### 3. Run the pipeline locally

```bash
python app/app.py
python consumer/consumer_to_db.py
```

## Development Utilities

The `dev/` folder contains local-only helpers that are not part of the core runtime pipeline:

- `dev/generate_historical_data.py` seeds historical tick data into TimescaleDB for testing and dashboard backfills
- `dev/nginx_local.conf` provides a simplified Nginx config for local development

## Deployment Notes

- `docker-compose.yml` defines Kafka, TimescaleDB, Grafana, the producer, the consumer, and Nginx
- `init.sql` sets up the database schema and retention policy
- `nginx.conf` is the active reverse proxy configuration used in deployment
