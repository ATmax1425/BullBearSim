import { useReducer, useCallback, useEffect, useRef, useMemo } from 'react';
import type { Tick, SymbolData, SymbolSummary, MarketSummary, ConnectionStatus } from '../types';
import { calcChange, calcDirection } from '../utils/stats';
import { useWebSocket } from './useWebSocket';

interface MarketDataState {
  symbols: Record<string, SymbolData>;
  recentTicks: Tick[];
  selectedSymbol: string | null;
  lastTickTimestamp: number | null;
  totalMessages: number;
  connectionStatus: ConnectionStatus;
  messagesPerSecond: number;
  lastTickAge: number | null;
}

type Action =
  | { type: 'TICK'; tick: Tick }
  | { type: 'SELECT_SYMBOL'; symbol: string }
  | { type: 'SET_CONNECTION_STATUS'; status: ConnectionStatus }
  | { type: 'SET_MPS'; mps: number }
  | { type: 'SET_TOTAL'; total: number }
  | { type: 'TICK_AGE'; age: number | null };

function marketDataReducer(
  state: MarketDataState,
  action: Action,
): MarketDataState {
  switch (action.type) {
    case 'TICK': {
      const { tick } = action;
      const existing = state.symbols[tick.symbol];
      const newTicks = [...(existing?.ticks ?? []), tick].slice(-100);
      const newSymbols = {
        ...state.symbols,
        [tick.symbol]: {
          ticks: newTicks,
          firstPrice: existing?.firstPrice ?? tick.price,
        },
      };
      const newRecent = [...state.recentTicks, tick].slice(-50);
      const selectedSymbol = state.selectedSymbol ?? tick.symbol;
      return {
        ...state,
        symbols: newSymbols,
        recentTicks: newRecent,
        selectedSymbol,
        lastTickTimestamp: Date.now(),
      };
    }
    case 'SELECT_SYMBOL':
      return { ...state, selectedSymbol: action.symbol };
    case 'SET_CONNECTION_STATUS':
      return { ...state, connectionStatus: action.status };
    case 'SET_MPS':
      return { ...state, messagesPerSecond: action.mps };
    case 'SET_TOTAL':
      return { ...state, totalMessages: action.total };
    case 'TICK_AGE':
      return { ...state, lastTickAge: action.age };
    default:
      return state;
  }
}

const initialState: MarketDataState = {
  symbols: {},
  recentTicks: [],
  selectedSymbol: null,
  lastTickTimestamp: null,
  connectionStatus: 'connecting',
  totalMessages: 0,
  messagesPerSecond: 0,
  lastTickAge: null,
};

function buildSymbolSummaries(symbols: Record<string, SymbolData>): SymbolSummary[] {
  return Object.entries(symbols).map(([symbol, data]) => {
    const ticks = data.ticks;
    const latest = ticks.length > 0 ? ticks[ticks.length - 1] : null;
    const first = ticks.length > 0 ? ticks[0] : null;
    const price = latest?.price ?? 0;
    const volume = latest?.volume ?? 0;
    let change = 0;
    let changePct = 0;
    if (first && latest && ticks.length >= 2) {
      const result = calcChange(latest.price, first.price);
      change = result.absolute;
      changePct = result.percent;
    }
    return {
      symbol,
      price,
      change,
      changePct,
      volume,
      direction: calcDirection(changePct),
    };
  });
}

function buildMarketSummary(
  summaries: SymbolSummary[],
  streamRate: number,
  lastTickTimestamp: number | null,
  connectionStatus: ConnectionStatus,
): MarketSummary {
  const advancing = summaries.filter((s) => s.direction === 'up').length;
  const declining = summaries.filter((s) => s.direction === 'down').length;
  const lastUpdate =
    lastTickTimestamp != null ? new Date(lastTickTimestamp).toISOString() : null;
  return {
    total: summaries.length,
    advancing,
    declining,
    streamRate,
    lastUpdate,
    connectionStatus,
  };
}

export function useMarketData() {
  const [state, dispatch] = useReducer(marketDataReducer, initialState);
  const lastTickTimestampRef = useRef<number | null>(null);

  const handleTick = useCallback((tick: Tick) => {
    dispatch({ type: 'TICK', tick });
  }, []);

  const { connectionStatus, totalMessages, mps } = useWebSocket(handleTick);

  useEffect(() => {
    dispatch({ type: 'SET_CONNECTION_STATUS', status: connectionStatus });
  }, [connectionStatus]);

  useEffect(() => {
    dispatch({ type: 'SET_TOTAL', total: totalMessages });
  }, [totalMessages]);

  useEffect(() => {
    dispatch({ type: 'SET_MPS', mps });
  }, [mps]);

  useEffect(() => {
    lastTickTimestampRef.current = state.lastTickTimestamp;
  }, [state.lastTickTimestamp]);

  useEffect(() => {
    const interval = setInterval(() => {
      if (lastTickTimestampRef.current != null) {
        const age = Math.floor(
          (Date.now() - lastTickTimestampRef.current) / 1000,
        );
        dispatch({ type: 'TICK_AGE', age });
      }
    }, 1000);
    return () => clearInterval(interval);
  }, []);

  const selectSymbol = useCallback((symbol: string) => {
    dispatch({ type: 'SELECT_SYMBOL', symbol });
  }, []);

  const symbolSummaries = useMemo(
    () => buildSymbolSummaries(state.symbols),
    [state.symbols],
  );

  const marketSummary = useMemo(
    () =>
      buildMarketSummary(
        symbolSummaries,
        state.messagesPerSecond,
        state.lastTickTimestamp,
        state.connectionStatus,
      ),
    [symbolSummaries, state.messagesPerSecond, state.lastTickTimestamp, state.connectionStatus],
  );

  const topGainers = useMemo(
    () =>
      [...symbolSummaries]
        .filter((s) => s.direction === 'up')
        .sort((a, b) => b.changePct - a.changePct)
        .slice(0, 5),
    [symbolSummaries],
  );

  const topLosers = useMemo(
    () =>
      [...symbolSummaries]
        .filter((s) => s.direction === 'down')
        .sort((a, b) => a.changePct - b.changePct)
        .slice(0, 5),
    [symbolSummaries],
  );

  return {
    ...state,
    selectSymbol,
    symbolSummaries,
    marketSummary,
    topGainers,
    topLosers,
  };
}