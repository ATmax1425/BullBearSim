import dash
from dash import dcc, html, Output, Input
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import pandas as pd
import asyncio
import websockets
import json
import re
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

def resample_data(df, timeframe="1m"):
    if df.empty:
        return df

    df = df.copy()
    df['ts'] = pd.to_datetime(df['ts'])
    df.set_index('ts', inplace=True)

    freq = TIMEFRAME_MAP.get(timeframe, "1min")
    df_resampled = df['price'].resample(freq).last()
    df_resampled = df_resampled.reset_index()
    return df_resampled

# -----------------------------
# Dash App Setup
# -----------------------------
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

MAX_BARS = 200 
SYMBOLS = ["NIFTY", "BANKNIFTY", "RELIANCE", "TCS", "INFY"]
TIMEFRAME = ['1m', '2m', '5m', '10m', '15m', '30m', '1h', '2h', '5h', '6h', '12h', "1d"]

TIMEFRAME_MAP = {
    "1m": "1min",
    "2m": "2min",
    "5m": "5min",
    "10m": "10min",
    "15m": "15min",
    "30m": "30min",
    "1h": "1h",
    "2h": "2h",
    "5h": "5h",
    "6h": "6h",
    "12h": "12h",
    "1d": "1D",
}

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
                value=[SYMBOLS[0]],
                inline=True
            ),
            html.Label("Select the timeframe"),
            dcc.Dropdown(
                id="timeframe-dropdown",
                options=[{"label": i, "value": i} for i in TIMEFRAME],
                value="1m",
            )
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

def get_required_ticks(timeframe, max_bars=MAX_BARS):
    m = re.match(r"(\d+)([mhd])", timeframe)
    if not m:
        return max_bars * 10

    n, unit = int(m.group(1)), m.group(2)

    unit_map = {"m": 1, "h": 60, "d": 1440}
    minutes = n * unit_map[unit]

    ticks_per_candle = minutes * 60  

    return max_bars * ticks_per_candle

# -----------------------------
# Callbacks for each graph
# -----------------------------
@app.callback(
    Output("charts-container", "children"),
    [Input("symbol-checklist", "value"),
     Input("timeframe-dropdown", "value"),
     Input("interval-component", "n_intervals")
    ]
)
def update_charts(selected_symbols, timeframe,  n):
    charts = []
    tf = timeframe[0] if isinstance(timeframe, list) else timeframe
    required_ticks = get_required_ticks(tf)
    for sym in selected_symbols:
        if sym not in buffers or len(buffers[sym]) == 0:
            continue
        df = pd.DataFrame(buffers[sym]).tail(required_ticks)

        df_resampled = resample_data(df, tf)

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df_resampled["ts"],
            y=df_resampled["price"],
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
