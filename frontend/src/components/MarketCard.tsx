import type { SymbolSummary } from '../types';
import { formatChangeShort } from '../utils/format';

interface MarketCardProps {
  summary: SymbolSummary;
  isSelected: boolean;
  onClick: () => void;
}

const directionConfig = {
  up: { dot: 'bg-green-500', text: 'text-green-400' },
  down: { dot: 'bg-red-500', text: 'text-red-400' },
  flat: { dot: 'bg-gray-500', text: 'text-gray-400' },
} as const;

export function MarketCard({ summary, isSelected, onClick }: MarketCardProps) {
  const dc = directionConfig[summary.direction];
  const bg = isSelected ? 'bg-gray-800' : 'bg-gray-900 hover:bg-gray-800/60';

  return (
    <button
      onClick={onClick}
      className={`flex-shrink-0 px-3 py-2 rounded text-left transition-colors ${bg}`}
    >
      <div className="flex items-center gap-2">
        <span className={`inline-block w-1.5 h-1.5 rounded-full ${dc.dot}`} />
        <span className="font-semibold text-sm text-gray-200">{summary.symbol}</span>
        <span className={`text-sm font-mono tabular-nums font-medium ${dc.text}`}>
          {formatChangeShort(summary.changePct)}
        </span>
      </div>
    </button>
  );
}