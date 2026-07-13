import { formatTimeShort } from '../utils/format';
import { formatIndianPrice, formatIndianVolume } from '../utils/format';
import type { Tick } from '../types';

interface RecentTickFeedProps {
  ticks: Tick[];
}

function calcDirection(tick: Tick, prevTick: Tick | undefined): 'up' | 'down' | 'flat' {
  if (!prevTick) return 'flat';
  const diff = tick.price - prevTick.price;
  if (diff > 0.01) return 'up';
  if (diff < -0.01) return 'down';
  return 'flat';
}

export function RecentTickFeed({ ticks }: RecentTickFeedProps) {
  const reversed = [...ticks].reverse();

  return (
    <div className="bg-gray-900 border border-gray-800/40 rounded-lg p-4">
      <h2 className="text-sm font-medium text-gray-400 mb-3">Recent Ticks</h2>
      <div className="max-h-56 overflow-y-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-gray-500 border-b border-gray-800 text-xs">
              <th className="text-left pb-2 pr-3 font-medium">Time</th>
              <th className="text-left pb-2 pr-3 font-medium">Symbol</th>
              <th className="text-right pb-2 pr-3 font-medium">Price</th>
              <th className="text-right pb-2 font-medium">Volume</th>
            </tr>
          </thead>
          <tbody>
            {reversed.map((tick, i) => {
              const prevTick = i < reversed.length - 1 ? reversed[i + 1] : undefined;
              const dir = calcDirection(tick, prevTick);
              const dirColor =
                dir === 'up'
                  ? 'text-green-400'
                  : dir === 'down'
                    ? 'text-red-400'
                    : 'text-gray-300';

              return (
                <tr
                  key={`${tick.ts}-${tick.symbol}-${i}`}
                  className="border-b border-gray-800/30 text-gray-300"
                >
                  <td className="py-1.5 pr-3 font-mono text-xs text-gray-500 tabular-nums">
                    {formatTimeShort(tick.ts)}
                  </td>
                  <td className="py-1.5 pr-3 font-semibold text-sm">{tick.symbol}</td>
                  <td className={`py-1.5 pr-3 text-right font-mono text-sm tabular-nums ${dirColor}`}>
                    {formatIndianPrice(tick.price)}
                  </td>
                  <td className="py-1.5 text-right font-mono text-xs text-gray-400 tabular-nums">
                    {formatIndianVolume(tick.volume)}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}