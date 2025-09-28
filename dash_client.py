import dash
from dash import dcc, html, Output, Input
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import pandas as pd
import asyncio
import websockets
import json
from threading import Thread
from helper import get_psql_engine

# -----------------------------
# Database connection
# -----------------------------


def get_historical_data(symbol, limit=200):
    """Fetch historical stock data from TimescaleDB"""
    engine = get_psql_engine()
    query = """
        SELECT ts, price
        FROM ticks
        WHERE symbol = %s
        ORDER BY ts DESC
        LIMIT %s
    """
    df = pd.read_sql_query(query, engine, params=(symbol, limit))
    return df.sort_values("ts")

# -----------------------------
# Dash App Setup
# -----------------------------
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

SYMBOLS = ["NIFTY", "BANKNIFTY", "RELIANCE", "TCS", "INFY"]

app.layout = dbc.Container([
    dbc.Row([
        dbc.Col(html.H1("📈 Real-time Stock Dashboard"), width=12)
    ]),
    dbc.Row([
        dbc.Col([
            html.Label("Select Stocks to View:"),
            dcc.Checklist(
                id="symbol-checklist",
                options=[{"label": sym, "value": sym} for sym in SYMBOLS],
                value=[SYMBOLS[0]],  # default selection
                inline=True
            ),
        ], width=12),
    ], className="mb-3"),
    html.Div(id="charts-container"),
    dcc.Interval(id="interval-component", interval=1000, n_intervals=0)
], fluid=True)

# -----------------------------
# Shared live data storage
# -----------------------------
buffers = {sym: [] for sym in SYMBOLS}

for sym in buffers:
    df_hist = get_historical_data(sym, limit=200)
    buffers[sym] = df_hist.to_dict("records")

# -----------------------------
# WebSocket listener
# -----------------------------
WS_URL = "ws://localhost:8000/ws"

async def ws_listener():
    async with websockets.connect(WS_URL) as websocket:
        async for message in websocket:
            data = json.loads(message)
            sym = data["symbol"]
            if sym in buffers:
                buffers[sym].append({"ts": data["ts"], "price": data["price"]})
                if len(buffers[sym]) > 200:
                    buffers[sym] = buffers[sym][-200:]

# Run listener in background
def start_ws_loop():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(ws_listener())

Thread(target=start_ws_loop, daemon=True).start()

# -----------------------------
# Callbacks for each graph
# -----------------------------
@app.callback(
    Output("charts-container", "children"),
    [Input("symbol-checklist", "value"),
        Input("interval-component", "n_intervals")]
)
def update_charts(selected_symbols, n):
    charts = []
    for sym in selected_symbols:
        if sym not in buffers or len(buffers[sym]) == 0:
            continue
        df = pd.DataFrame(buffers[sym]).tail(200)
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df["ts"],
            y=df["price"],
            mode="lines+markers",
            name=sym
        ))
        fig.update_layout(title=f"{sym} Price", xaxis_title="Time", yaxis_title="Price")
        charts.append(html.Div([
            html.H4(f"Chart for {sym}"),
            dcc.Graph(
                id=f"graph-{sym}",
                figure=fig
            )
        ], style={"margin-bottom": "30px", "display": "grid"}))
    return charts

# -----------------------------
if __name__ == "__main__":
    app.run(debug=True)
