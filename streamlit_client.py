"""
Fixed Streamlit WebSocket Client
- Creates chart containers once
- Updates in place (no duplicate headers)
- Keeps last MAX_POINTS ticks per symbol
"""

import streamlit as st
import asyncio
import websockets
import json
import pandas as pd
import traceback
from collections import defaultdict, deque

from consumer.helper import get_psql_conn

WS_URL = "ws://localhost:8000/ws"
MAX_POINTS = 30  # cap chart length

st.title("📈 Real-Time Stock Ticks (Kafka → FastAPI → Streamlit)")
st.subheader("Live Prices")

# -----------------------------
# State initialization
# -----------------------------
if "buffers" not in st.session_state:
    st.session_state.buffers = defaultdict(lambda: deque(maxlen=MAX_POINTS))

if "charts" not in st.session_state:
    st.session_state.charts = {}


conn = get_psql_conn()
cur = conn.cursor

# -----------------------------
# Async WebSocket loop
# -----------------------------
async def run_ws():
    while True:
        try:
            async with websockets.connect(WS_URL) as ws:
                st.success("✅ Connected to WebSocket")
                while True:
                    msg = await ws.recv()
                    data = json.loads(msg)
                    symbol = data["symbol"]

                    # Ensure timestamp is datetime
                    data["ts"] = pd.to_datetime(data["ts"])

                    # Append to symbol-specific buffer
                    st.session_state.buffers[symbol].append(data)

                    # Convert buffer to DataFrame
                    df = pd.DataFrame(st.session_state.buffers[symbol])

                    # Create placeholder once per symbol
                    if symbol not in st.session_state.charts:
                        st.session_state.charts[symbol] = st.empty()

                    # Update chart inside placeholder
                    st.session_state.charts[symbol].line_chart(
                        df.set_index("ts")[["price"]],
                        height=200
                    )

        except Exception as e:
            st.error("⚠️ WebSocket disconnected/crashed")
            st.code("".join(traceback.format_exception(type(e), e, e.__traceback__)))
            await asyncio.sleep(5)

# -----------------------------
# Run safely inside Streamlit
# -----------------------------
if "ws_task" not in st.session_state:
    st.session_state.ws_task = asyncio.run(run_ws())
