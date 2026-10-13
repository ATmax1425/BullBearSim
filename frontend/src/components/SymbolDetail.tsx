import type { Tick } from '../types';
import {
  formatIndianPrice,
  formatChangeShort,
  formatIndianVolume,
  formatTime,
} from '../utils/format';
import { calcDirection, directionTextColor } from '../utils/stats';

interface SymbolDetailProps {
  symbol: string | null;
  ticks: Tick[];
  changePct: number;
}

export function SymbolDetail({ symbol, ticks, changePct }: SymbolDetailProps) {
  const latest = ticks.length > 0 ? ticks[ticks.length - 1] : null;
  const changeColor = directionTextColor[calcDirection(changePct)];

  return (
    <div className="bg-gray-900 rounded-lg p-4 min-h-[4.5rem] flex items-center">
      {symbol && latest ? (
        <div className="flex items-baseline gap-4 flex-wrap w-full">
          <h2 className="text-lg font-bold text-white">{symbol}</h2>
          <span className="text-2xl font-mono font-bold text-white tabular-nums">
            {formatIndianPrice(latest.price)}
          </span>
          <span
            className={`text-base font-mono font-medium tabular-nums ${changeColor}`}
            title="Change over the chart window"
          >
            {formatChangeShort(changePct)}
          </span>
          <span className="text-sm text-gray-500 tabular-nums">
            Vol: {formatIndianVolume(latest.volume)}
          </span>
          <span className="text-xs text-gray-600 tabular-nums">
            {formatTime(latest.ts)} IST
          </span>
        </div>
      ) : (
        <div className="text-sm text-gray-500">Waiting for data...</div>
      )}
    </div>
  );
}
