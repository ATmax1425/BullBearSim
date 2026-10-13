import { formatTime, formatIndianPrice, formatIndianVolume } from '../utils/format';
import type { Direction, FeedTick } from '../types';

interface RecentTickFeedProps {
  ticks: FeedTick[];
}

const priceColor: Record<Direction, string> = {
  up: 'text-green-400',
  down: 'text-red-400',
  flat: 'text-gray-300',
};

export function RecentTickFeed({ ticks }: RecentTickFeedProps) {
  const reversed = [...ticks].reverse();

  return (
    <div className="bg-gray-900 border border-gray-800/40 rounded-lg p-4">
      <h2 className="text-sm font-medium text-gray-400 mb-3">Recent Ticks</h2>
      <div className="max-h-56 overflow-y-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-gray-500 border-b border-gray-800 text-xs">
              <th className="text-left pb-2 pr-3 font-medium">Time (IST)</th>
              <th className="text-left pb-2 pr-3 font-medium">Symbol</th>
              <th className="text-right pb-2 pr-3 font-medium">Price</th>
              <th className="text-right pb-2 font-medium">Volume</th>
            </tr>
          </thead>
          <tbody>
            {reversed.map((tick) => (
              <tr
                key={`${tick.ts}-${tick.symbol}`}
                className="border-b border-gray-800/30 text-gray-300"
              >
                <td className="py-1.5 pr-3 font-mono text-xs text-gray-500 tabular-nums">
                  {formatTime(tick.ts)}
                </td>
                <td className="py-1.5 pr-3 font-semibold text-sm">{tick.symbol}</td>
                <td
                  className={`py-1.5 pr-3 text-right font-mono text-sm tabular-nums ${priceColor[tick.direction]}`}
                >
                  {formatIndianPrice(tick.price)}
                </td>
                <td className="py-1.5 text-right font-mono text-xs text-gray-400 tabular-nums">
                  {formatIndianVolume(tick.volume)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
