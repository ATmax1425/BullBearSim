import { formatTime } from '../utils/format';

interface SystemStatusProps {
  symbolCount: number;
  streamRate: number;
  lastUpdate: number | null;
}

export function SystemStatus({
  symbolCount,
  streamRate,
  lastUpdate,
}: SystemStatusProps) {
  return (
    <div className="flex items-center gap-4 text-xs text-gray-500">
      <span className="tabular-nums">
        <span className="text-gray-400 font-medium">{symbolCount}</span> symbols
      </span>
      <span className="text-gray-700">|</span>
      <span className="tabular-nums">
        <span className="text-gray-400 font-medium">{streamRate}/s</span> stream
      </span>
      <span className="text-gray-700 hidden sm:inline">|</span>
      <span className="tabular-nums hidden sm:inline">
        <span className="text-gray-400 font-medium">Updated</span>{' '}
        {lastUpdate != null ? `${formatTime(lastUpdate)} IST` : '—'}
      </span>
    </div>
  );
}
