export interface Tick {
  ts: string;
  symbol: string;
  price: number;
  volume: number;
}

export type Direction = 'up' | 'down' | 'flat';

/** A tick in the recent-ticks feed, with its move versus the same symbol's previous tick. */
export interface FeedTick extends Tick {
  direction: Direction;
}

export interface SymbolData {
  ticks: Tick[];
}

export interface SymbolSummary {
  symbol: string;
  price: number;
  change: number;
  changePct: number;
  volume: number;
  direction: Direction;
}

export type ConnectionStatus = 'connecting' | 'connected' | 'reconnecting';
