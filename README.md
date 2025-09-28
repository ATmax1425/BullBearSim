# 📈 Real-Time Stock Market Streaming

End-to-end data engineering project for streaming, storing, and visualizing live stock market data.  
Built to showcase real-time pipelines with **Kafka**, **FastAPI**, **TimescaleDB**, and **Streamlit**.

---

## 🚀 Features
- Real-time stock price streaming via **Kafka**
- WebSocket API with **FastAPI**
- Persistent storage in **TimescaleDB** (with 30-day retention policy)
- **Dash dashboard** for:
  - Live tick charting
  - Historical queries from DB

---

## 🛠️ Tech Stack
- **Python** (producer, consumer, backend, dashboard)
- **Apache Kafka** (event streaming backbone)
- **FastAPI** (WebSocket server)
- **TimescaleDB/Postgres** (time-series storage)
- **Dash** (data visualization)
- **Docker Compose** (containerized setup)

---

## 📂 Project Structure


├── app.py # FastAPI WebSocket server
├── consumer_to_db.py # Kafka consumer → DB writer
├── dash_client.py → Dash Client (Main UI)
├── docker-compose.yml # Infra setup: Kafka + TimescaleDB
├── helper.py # Utility functions
├── init.sql # DB retention policy (30 days)
├── streamlit_client.py # Streamlit frontend (Legacy UI)
└── .gitignore


---

## ⚡ Getting Started

### 1. Clone the repo
```bash
git clone https://github.com/ATmax1425/realtime-stock-streaming.git
cd realtime-stock-streaming

docker-compose up -d

python producer.py

python consumer_to_db.py

python dash_client.py

Planned features:

🛒 Trading simulator (buy/sell)

📰 IPO analysis & sentiment tracking

📢 Alerts & notifications
