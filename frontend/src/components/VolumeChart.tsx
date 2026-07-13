import { Bar } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
} from 'chart.js';
import { formatTime } from '../utils/format';
import { formatIndianVolume } from '../utils/format';
import type { Tick } from '../types';

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip);

interface VolumeChartProps {
  ticks: Tick[];
  symbol: string | null;
}

export function VolumeChart({ ticks, symbol }: VolumeChartProps) {
  const data = {
    labels: ticks.map((t) => formatTime(t.ts)),
    datasets: [
      {
        label: 'Volume',
        data: ticks.map((t) => t.volume),
        backgroundColor: '#6366f1',
        borderColor: '#6366f1',
        borderWidth: 1,
        borderRadius: 2,
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
            ctx.parsed.y != null ? formatIndianVolume(ctx.parsed.y) : '',
        },
      },
    },
    scales: {
      x: {
        ticks: { maxTicksLimit: 10, color: '#6b7280', font: { size: 11 } },
        grid: { color: '#1f2937' },
      },
      y: {
        beginAtZero: true,
        ticks: {
          color: '#6b7280',
          font: { size: 11 },
          maxTicksLimit: 6,
          callback: (value: string | number) =>
            typeof value === 'number' ? formatIndianVolume(value) : value,
        },
        grid: { color: '#1f2937' },
      },
    },
  };

  return (
    <div className="bg-gray-900 border border-gray-800/40 rounded-lg p-4 h-full flex flex-col">
      <h2 className="text-sm font-medium text-gray-400 mb-3 flex-none">
        {symbol ? (
          <span>
            <span className="text-white font-semibold">{symbol}</span> Volume
          </span>
        ) : (
          'Volume'
        )}
      </h2>
      <div className="flex-1 min-h-0">
        <Bar data={data} options={options} />
      </div>
    </div>
  );
}