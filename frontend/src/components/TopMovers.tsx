import type { SymbolSummary } from '../types';
import { formatIndianPrice, formatChangeShort } from '../utils/format';

interface TopMoversProps {
  gainers: SymbolSummary[];
  losers: SymbolSummary[];
}

function MoversList({
  title,
  items,
  up,
}: {
  title: string;
  items: SymbolSummary[];
  up: boolean;
}) {
  if (items.length === 0) return null;

  return (
    <div>
      <h3 className="text-xs font-medium text-gray-500 mb-2 uppercase tracking-wider">
        {title}
      </h3>
      <div className="space-y-1">
        {items.map((s) => (
          <div
            key={s.symbol}
            className="flex items-center justify-between py-1.5 px-2.5 rounded bg-gray-800/40"
          >
            <span className="font-semibold text-sm text-gray-200 w-20">
              {s.symbol}
            </span>
            <span className="font-mono text-sm text-gray-300 flex-1 text-right tabular-nums">
              {formatIndianPrice(s.price)}
            </span>
            <span
              className={`font-mono text-sm font-medium w-[5.5rem] text-right tabular-nums ${
                up ? 'text-green-400' : 'text-red-400'
              }`}
            >
              {formatChangeShort(s.changePct)}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

export function TopMovers({ gainers, losers }: TopMoversProps) {
  return (
    <div className="bg-gray-900 border border-gray-800/40 rounded-lg p-4 h-full flex flex-col">
      <h2 className="text-sm font-medium text-gray-400 mb-3 flex-none">Top Movers</h2>
      <div className="flex-1 overflow-y-auto min-h-0 space-y-5">
        <MoversList title="Gainers" items={gainers} up={true} />
        <MoversList title="Losers" items={losers} up={false} />
      </div>
    </div>
  );
}