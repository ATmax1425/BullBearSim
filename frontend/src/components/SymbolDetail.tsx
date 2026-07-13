import type { Tick } from '../types';
import {
  formatIndianPrice,
  formatChangeShort,
  formatIndianVolume,
  formatTimeShort,
} from '../utils/format';

interface SymbolDetailProps {
  symbol: string | null;
  ticks: Tick[];
  changePct: number;
}

export function SymbolDetail({ symbol, ticks, changePct }: SymbolDetailProps) {
  const latest = ticks.length > 0 ? ticks[ticks.length - 1] : null;
  const isUp = changePct >= 0;

  return (
    <div className="bg-gray-900 rounded-lg p-4 min-h-[4.5rem] flex items-center">
      {symbol && latest ? (
        <div className="flex items-baseline gap-4 flex-wrap w-full">
          <h2 className="text-lg font-bold text-white">{symbol}</h2>
          <span className="text-2xl font-mono font-bold text-white tabular-nums">
            {formatIndianPrice(latest.price)}
          </span>
          <span
            className={`text-base font-mono font-medium tabular-nums ${
              isUp ? 'text-green-400' : 'text-red-400'
            }`}
          >
            {formatChangeShort(changePct)}
          </span>
          <span className="text-sm text-gray-500 tabular-nums">
            Vol: {formatIndianVolume(latest.volume)}
          </span>
          <span className="text-xs text-gray-600 tabular-nums">
            {formatTimeShort(latest.ts)}
          </span>
        </div>
      ) : (
        <div className="text-sm text-gray-500">Waiting for data...</div>
      )}
    </div>
  );
}