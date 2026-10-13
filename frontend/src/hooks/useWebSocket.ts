import { useEffect, useRef, useState } from 'react';
import type { Tick, ConnectionStatus } from '../types';

// Ticks arrive ~11/s; hand them to React in batches to limit re-renders.
const FLUSH_INTERVAL_MS = 250;

interface UseWebSocketReturn {
  connectionStatus: ConnectionStatus;
  totalMessages: number;
  mps: number;
}

function isTick(value: unknown): value is Tick {
  if (typeof value !== 'object' || value === null) return false;
  const t = value as Record<string, unknown>;
  return (
    typeof t.ts === 'string' &&
    typeof t.symbol === 'string' &&
    typeof t.price === 'number' &&
    Number.isFinite(t.price) &&
    typeof t.volume === 'number'
  );
}

export function useWebSocket(
  onTicks: (ticks: Tick[]) => void
): UseWebSocketReturn {
  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>('connecting');
  const [totalMessages, setTotalMessages] = useState(0);
  const [mps, setMps] = useState(0);

  const onTicksRef = useRef(onTicks);
  onTicksRef.current = onTicks;

  const bufferRef = useRef<Tick[]>([]);
  const totalRef = useRef(0);
  const mpsRef = useRef(0);

  useEffect(() => {
    let mounted = true;
    let ws: WebSocket | null = null;
    let reconnectTimer: ReturnType<typeof setTimeout> | undefined;
    let delay = 1000;

    function connect() {
      const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
      ws = new WebSocket(`${protocol}://${window.location.host}/ws`);

      ws.onopen = () => {
        if (!mounted) return;
        setConnectionStatus('connected');
        delay = 1000;
      };

      ws.onmessage = (event) => {
        if (!mounted) return;
        let tick: unknown;
        try {
          tick = JSON.parse(event.data);
        } catch {
          return; // skip malformed messages
        }
        if (!isTick(tick)) return;
        totalRef.current++;
        mpsRef.current++;
        bufferRef.current.push(tick);
      };

      ws.onclose = () => {
        if (!mounted) return;
        setConnectionStatus('reconnecting');
        reconnectTimer = setTimeout(connect, delay);
        delay = Math.min(delay * 2, 30000);
      };
    }

    connect();

    const flushTimer = setInterval(() => {
      if (bufferRef.current.length === 0) return;
      const batch = bufferRef.current;
      bufferRef.current = [];
      setTotalMessages(totalRef.current);
      onTicksRef.current(batch);
    }, FLUSH_INTERVAL_MS);

    const mpsTimer = setInterval(() => {
      setMps(mpsRef.current);
      mpsRef.current = 0;
    }, 1000);

    return () => {
      mounted = false;
      ws?.close();
      clearTimeout(reconnectTimer);
      clearInterval(flushTimer);
      clearInterval(mpsTimer);
    };
  }, []);

  return { connectionStatus, totalMessages, mps };
}
