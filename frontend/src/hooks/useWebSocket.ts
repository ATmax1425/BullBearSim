import { useEffect, useRef, useState } from 'react';
import type { Tick, ConnectionStatus } from '../types';

interface UseWebSocketReturn {
  connectionStatus: ConnectionStatus;
  totalMessages: number;
  mps: number;
}

export function useWebSocket(
  onMessage: (tick: Tick) => void
): UseWebSocketReturn {
  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>('connecting');
  const [totalMessages, setTotalMessages] = useState(0);
  const [mps, setMps] = useState(0);

  const onMessageRef = useRef(onMessage);
  onMessageRef.current = onMessage;

  const totalRef = useRef(0);
  const mpsRef = useRef(0);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimerRef = useRef<ReturnType<typeof setTimeout>>();
  const delayRef = useRef(1000);

  useEffect(() => {
    let mounted = true;

    function connect() {
      const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
      const url = `${protocol}://${window.location.host}/ws`;
      const ws = new WebSocket(url);
      wsRef.current = ws;

      ws.onopen = () => {
        if (!mounted) return;
        setConnectionStatus('connected');
        delayRef.current = 1000;
      };

      ws.onmessage = (event) => {
        if (!mounted) return;
        try {
          const tick: Tick = JSON.parse(event.data);
          totalRef.current++;
          setTotalMessages(totalRef.current);
          mpsRef.current++;
          onMessageRef.current(tick);
        } catch {
          // skip malformed messages
        }
      };

      ws.onclose = () => {
        if (!mounted) return;
        setConnectionStatus('disconnected');
        scheduleReconnect();
      };
    }

    function scheduleReconnect() {
      reconnectTimerRef.current = setTimeout(() => {
        connect();
      }, delayRef.current);
      delayRef.current = Math.min(delayRef.current * 2, 30000);
    }

    connect();

    return () => {
      mounted = false;
      if (wsRef.current) {
        wsRef.current.close();
      }
      if (reconnectTimerRef.current) {
        clearTimeout(reconnectTimerRef.current);
      }
    };
  }, []);

  useEffect(() => {
    const interval = setInterval(() => {
      setMps(mpsRef.current);
      mpsRef.current = 0;
    }, 1000);
    return () => clearInterval(interval);
  }, []);

  return { connectionStatus, totalMessages, mps };
}
