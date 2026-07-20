export function SimulationBadge() {
  return (
    <div className="flex items-center gap-2 px-3 py-2 bg-yellow-500/10 border border-yellow-500/20 rounded-md">
      <span className="text-yellow-400 text-sm leading-none">🟡</span>
      <p className="text-xs text-yellow-400/80">
        <span className="font-medium text-yellow-400">Simulation Mode</span>
        {' — '}Displaying real-time synthetic market data for demonstration purposes.
      </p>
    </div>
  );
}
