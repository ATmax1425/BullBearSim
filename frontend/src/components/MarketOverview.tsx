import { MarketCard } from './MarketCard';
import type { SymbolSummary } from '../types';

interface MarketOverviewProps {
  summaries: SymbolSummary[];
  selectedSymbol: string | null;
  onSelectSymbol: (symbol: string) => void;
}

export function MarketOverview({
  summaries,
  selectedSymbol,
  onSelectSymbol,
}: MarketOverviewProps) {
  return (
    <div className="flex flex-nowrap gap-1.5 overflow-x-auto pb-1">
      {summaries.map((s) => (
        <MarketCard
          key={s.symbol}
          summary={s}
          isSelected={s.symbol === selectedSymbol}
          onClick={() => onSelectSymbol(s.symbol)}
        />
      ))}
    </div>
  );
}