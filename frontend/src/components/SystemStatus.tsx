import type { ConnectionStatus } from '../types';

interface SystemStatusProps {
  connectionStatus: ConnectionStatus;
  symbolCount: number;
  streamRate: number;
  lastUpdate: string | null;
}

const statusConfig = {
  connected: { color: 'bg-green-500', label: 'Live' },
  connecting: { color: 'bg-yellow-500', label: 'Connecting...' },
  disconnected: { color: 'bg-red-500', label: 'Disconnected' },
} as const;

export function SystemStatus({
  connectionStatus,
  symbolCount,
  streamRate,
  lastUpdate,
}: SystemStatusProps) {
  const sc = statusConfig[connectionStatus];

  return (
    <div className="flex items-center gap-4 text-xs text-gray-500">
      <div className="flex items-center gap-1.5">
        <span className={`inline-block w-2 h-2 rounded-full ${sc.color}`} />
        <span className="font-medium text-gray-400">{sc.label}</span>
      </div>
      <span className="text-gray-700">|</span>
      <span className="tabular-nums">
        <span className="text-gray-400 font-medium">{symbolCount}</span> symbols
      </span>
      <span className="text-gray-700 hidden sm:inline">|</span>
      <span className="tabular-nums hidden sm:inline">
        <span className="text-gray-400 font-medium">{streamRate}/s</span> stream
      </span>
      <span className="text-gray-700 hidden md:inline">|</span>
      <span className="tabular-nums hidden md:inline">
        <span className="text-gray-400 font-medium">Updated</span>{' '}
        {lastUpdate
          ? new Date(lastUpdate).toLocaleTimeString('en-IN', { hour12: false })
          : '—'}
      </span>
    </div>
  );
}