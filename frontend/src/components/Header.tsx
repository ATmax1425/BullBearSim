import type { ConnectionStatus } from '../types';

interface HeaderProps {
  connectionStatus: ConnectionStatus;
}

const statusConfig = {
  connected: { color: 'bg-green-500', label: 'Live', pulse: true },
  connecting: { color: 'bg-yellow-500', label: 'Connecting...', pulse: true },
  disconnected: { color: 'bg-red-500', label: 'Disconnected', pulse: false },
} as const;

export function Header({ connectionStatus }: HeaderProps) {
  const sc = statusConfig[connectionStatus];

  return (
    <header className="flex items-center justify-between px-4 sm:px-6 py-4 bg-gray-900 border-b border-gray-800">
      <div className="flex items-center gap-3">
        <h1 className="text-base font-bold text-white tracking-tight">StockStream</h1>
        <span className="text-xs text-gray-600 hidden sm:inline">
          Kafka · TimescaleDB · WebSocket · React · Chart.js
        </span>
      </div>
      <div className="flex items-center gap-2 bg-gray-950/50 rounded-md px-3 py-1.5">
        <span
          className={`inline-block w-2 h-2 rounded-full ${sc.color} ${sc.pulse ? 'animate-pulse' : ''}`}
        />
        <span className="text-xs font-medium text-gray-400">{sc.label}</span>
      </div>
    </header>
  );
}