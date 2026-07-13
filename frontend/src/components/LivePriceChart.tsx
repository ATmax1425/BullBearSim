import { Line } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Filler,
} from 'chart.js';
import { formatTime } from '../utils/format';
import { formatIndianPrice, formatChangeShort } from '../utils/format';
import type { Tick } from '../types';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Filler,
);

interface LivePriceChartProps {
  ticks: Tick[];
  symbol: string | null;
  changePct: number;
}

export function LivePriceChart({ ticks, symbol, changePct }: LivePriceChartProps) {
  const isUp = changePct >= 0;
  const lineColor = ticks.length > 1 ? (isUp ? '#22c55e' : '#ef4444') : '#3b82f6';
  const fillColor = ticks.length > 1
    ? (isUp ? 'rgba(34, 197, 94, 0.08)' : 'rgba(239, 68, 68, 0.08)')
    : 'rgba(59, 130, 246, 0.1)';

  const data = {
    labels: ticks.map((t) => formatTime(t.ts)),
    datasets: [
      {
        label: 'Price',
        data: ticks.map((t) => t.price),
        borderColor: lineColor,
        backgroundColor: fillColor,
        fill: true,
        tension: 0.1,
        pointRadius: 0,
        borderWidth: 2,
      },
    ],
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    animation: false as const,
    plugins: {
      legend: { display: false },
      tooltip: {
        callbacks: {
          label: (ctx: { parsed: { y: number | null } }) =>
            ctx.parsed.y != null ? formatIndianPrice(ctx.parsed.y) : '',
        },
      },
    },
    scales: {
      x: {
        ticks: { maxTicksLimit: 10, color: '#6b7280', font: { size: 11 } },
        grid: { color: '#1f2937' },
      },
      y: {
        ticks: {
          color: '#6b7280',
          font: { size: 11 },
          maxTicksLimit: 8,
          callback: (value: string | number) =>
            typeof value === 'number' ? formatIndianPrice(value) : value,
        },
        grid: { color: '#1f2937' },
      },
    },
  };

  const latestPrice = ticks.length > 0 ? ticks[ticks.length - 1].price : null;

  return (
    <div className="bg-gray-900 border border-gray-800/40 rounded-lg p-4">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-3">
          <h2 className="text-sm font-medium text-gray-400">
            {symbol ? (
              <span className="flex items-center gap-2">
                <span className="text-white font-semibold">{symbol}</span>
                {latestPrice != null && (
                  <span className="font-mono text-white tabular-nums">
                    {formatIndianPrice(latestPrice)}
                  </span>
                )}
                <span
                  className={`font-mono text-sm font-medium tabular-nums ${
                    changePct >= 0 ? 'text-green-400' : 'text-red-400'
                  }`}
                >
                  {formatChangeShort(changePct)}
                </span>
              </span>
            ) : (
              'Price Chart'
            )}
          </h2>
        </div>
        {ticks.length > 0 && (
          <span className="text-xs text-gray-600 tabular-nums">
            {ticks.length} ticks · {formatTime(ticks[0].ts)} – {formatTime(ticks[ticks.length - 1].ts)}
          </span>
        )}
      </div>
      <div className="h-80">
        <Line data={data} options={options} />
      </div>
    </div>
  );
}