import { useReducer, useCallback, useEffect, useMemo, useState } from 'react';
import type { Tick, FeedTick, SymbolData, SymbolSummary } from '../types';
import { calcChange, calcDirection, calcTickDirection } from '../utils/stats';
import { useWebSocket } from './useWebSocket';

export const CHART_WINDOW = 100;
const FEED_SIZE = 50;
// A larger jump between consecutive ticks of a symbol (reconnect, producer
// restart) starts a fresh chart window instead of joining across the gap.
const GAP_RESET_MS = 5000;

interface MarketDataState {
  symbols: Record<string, SymbolData>;
  recentTicks: FeedTick[];
  selectedSymbol: string | null;
  lastTickTimestamp: number | null;
}

type Action =
  | { type: 'TICKS'; ticks: Tick[]; receivedAt: number }
  | { type: 'SELECT_SYMBOL'; symbol: string };

function marketDataReducer(
  state: MarketDataState,
  action: Action,
): MarketDataState {
  switch (action.type) {
    case 'TICKS': {
      const symbols = { ...state.symbols };
      const feed: FeedTick[] = [];

      for (const tick of action.ticks) {
        const prev = symbols[tick.symbol]?.ticks ?? [];
        const last = prev.length > 0 ? prev[prev.length - 1] : undefined;
        const gap = last ? Date.parse(tick.ts) - Date.parse(last.ts) : 0;
        // NaN (unparseable timestamp) compares false here, so it never forces a reset.
        const continues = last !== undefined && !(gap < 0 || gap > GAP_RESET_MS);

        const ticks = continues ? [...prev, tick].slice(-CHART_WINDOW) : [tick];
        symbols[tick.symbol] = { ticks };
        feed.push({
          ...tick,
          direction: continues ? calcTickDirection(tick.price, last.price) : 'flat',
        });
      }

      return {
        symbols,
        recentTicks: [...state.recentTicks, ...feed].slice(-FEED_SIZE),
        selectedSymbol: state.selectedSymbol ?? action.ticks[0]?.symbol ?? null,
        lastTickTimestamp: action.receivedAt,
      };
    }
    case 'SELECT_SYMBOL':
      return { ...state, selectedSymbol: action.symbol };
    default:
      return state;
  }
}

const initialState: MarketDataState = {
  symbols: {},
  recentTicks: [],
  selectedSymbol: null,
  lastTickTimestamp: null,
};

function buildSymbolSummaries(symbols: Record<string, SymbolData>): SymbolSummary[] {
  return Object.entries(symbols).map(([symbol, data]) => {
    const ticks = data.ticks;
    const latest = ticks[ticks.length - 1];
    const first = ticks[0];
    const { absolute: change, percent: changePct } =
      ticks.length >= 2 ? calcChange(latest.price, first.price) : { absolute: 0, percent: 0 };
    return {
      symbol,
      price: latest.price,
      change,
      changePct,
      volume: latest.volume,
      direction: calcDirection(changePct),
    };
  });
}

export function useMarketData() {
  const [state, dispatch] = useReducer(marketDataReducer, initialState);
  const [now, setNow] = useState(() => Date.now());

  const handleTicks = useCallback((ticks: Tick[]) => {
    dispatch({ type: 'TICKS', ticks, receivedAt: Date.now() });
  }, []);

  const { connectionStatus, totalMessages, mps } = useWebSocket(handleTicks);

  useEffect(() => {
    const interval = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(interval);
  }, []);

  const lastTickAge =
    state.lastTickTimestamp != null
      ? Math.max(0, Math.floor((now - state.lastTickTimestamp) / 1000))
      : null;

  const selectSymbol = useCallback((symbol: string) => {
    dispatch({ type: 'SELECT_SYMBOL', symbol });
  }, []);

  const symbolSummaries = useMemo(
    () => buildSymbolSummaries(state.symbols),
    [state.symbols],
  );

  const topGainers = useMemo(
    () =>
      symbolSummaries
        .filter((s) => s.direction === 'up')
        .sort((a, b) => b.changePct - a.changePct)
        .slice(0, 5),
    [symbolSummaries],
  );

  const topLosers = useMemo(
    () =>
      symbolSummaries
        .filter((s) => s.direction === 'down')
        .sort((a, b) => a.changePct - b.changePct)
        .slice(0, 5),
    [symbolSummaries],
  );

  return {
    symbols: state.symbols,
    recentTicks: state.recentTicks,
    selectedSymbol: state.selectedSymbol,
    lastUpdate: state.lastTickTimestamp,
    connectionStatus,
    totalMessages,
    messagesPerSecond: mps,
    lastTickAge,
    selectSymbol,
    symbolSummaries,
    topGainers,
    topLosers,
  };
}
