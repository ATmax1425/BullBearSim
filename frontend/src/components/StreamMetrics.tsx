interface StreamMetricsProps {
  totalMessages: number;
  mps: number;
  lastTickAge: number | null;
}

export function StreamMetrics({
  totalMessages,
  mps,
  lastTickAge,
}: StreamMetricsProps) {
  const items = [
    { label: 'Total Messages', value: totalMessages.toLocaleString() },
    { label: 'Stream Rate', value: `${mps}/s` },
    { label: 'Last Tick', value: lastTickAge !== null ? `${lastTickAge}s ago` : '—' },
  ];

  return (
    <div className="flex items-center gap-6 text-xs text-gray-500">
      {items.map((item) => (
        <div key={item.label} className="flex items-center gap-1.5">
          <span className="font-medium text-gray-500">{item.label}:</span>
          <span className="font-mono tabular-nums text-gray-400">{item.value}</span>
        </div>
      ))}
    </div>
  );
}