export interface Tick {
  ts: string;
  symbol: string;
  price: number;
  volume: number;
}

export interface SymbolData {
  ticks: Tick[];
  firstPrice: number | null;
}

export interface SymbolSummary {
  symbol: string;
  price: number;
  change: number;
  changePct: number;
  volume: number;
  direction: 'up' | 'down' | 'flat';
}

export interface MarketSummary {
  total: number;
  advancing: number;
  declining: number;
  streamRate: number;
  lastUpdate: string | null;
  connectionStatus: ConnectionStatus;
}

export type ConnectionStatus = 'connecting' | 'connected' | 'disconnected';
