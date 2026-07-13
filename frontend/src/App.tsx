import { useMarketData } from './hooks/useMarketData';
import { Header } from './components/Header';
import { SystemStatus } from './components/SystemStatus';
import { MarketOverview } from './components/MarketOverview';
import { SymbolDetail } from './components/SymbolDetail';
import { LivePriceChart } from './components/LivePriceChart';
import { VolumeChart } from './components/VolumeChart';
import { TopMovers } from './components/TopMovers';
import { RecentTickFeed } from './components/RecentTickFeed';
import { StreamMetrics } from './components/StreamMetrics';
import { calcChangeFromChartWindow } from './utils/stats';

export default function App() {
  const {
    symbols,
    recentTicks,
    selectedSymbol,
    connectionStatus,
    totalMessages,
    messagesPerSecond,
    lastTickAge,
    selectSymbol,
    symbolSummaries,
    marketSummary,
    topGainers,
    topLosers,
  } = useMarketData();

  const selectedData = selectedSymbol ? symbols[selectedSymbol] : null;
  const selectedTicks = selectedData?.ticks ?? [];

  const chartChange = selectedTicks.length >= 2
    ? calcChangeFromChartWindow(selectedTicks)
    : null;
  const chartChangePct = chartChange?.percent ?? 0;

  return (
    <div className="min-h-screen bg-gray-950 flex flex-col">
      <Header connectionStatus={connectionStatus} />

      <main className="flex-1 px-4 sm:px-6 py-5 max-w-7xl mx-auto w-full space-y-4">
        <SystemStatus
          connectionStatus={connectionStatus}
          symbolCount={symbolSummaries.length}
          streamRate={messagesPerSecond}
          lastUpdate={marketSummary.lastUpdate}
        />

        <section>
          <h2 className="text-xs font-medium text-gray-500 uppercase tracking-wider mb-2">
            Symbols
          </h2>
          <MarketOverview
            summaries={symbolSummaries}
            selectedSymbol={selectedSymbol}
            onSelectSymbol={selectSymbol}
          />
        </section>

        <SymbolDetail
          symbol={selectedSymbol}
          ticks={selectedTicks}
          changePct={chartChangePct}
        />

        <LivePriceChart
          ticks={selectedTicks}
          symbol={selectedSymbol}
          changePct={chartChangePct}
        />

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          <div className="lg:col-span-2">
            <VolumeChart ticks={selectedTicks} symbol={selectedSymbol} />
          </div>
          <div className="lg:col-span-1">
            <TopMovers gainers={topGainers} losers={topLosers} />
          </div>
        </div>

        <section>
          <h2 className="text-xs font-medium text-gray-500 uppercase tracking-wider mb-2">
            Recent Ticks
          </h2>
          <RecentTickFeed ticks={recentTicks} />
        </section>

        <div className="pt-4 border-t border-gray-800">
          <h3 className="text-xs font-medium text-gray-500 uppercase tracking-wider mb-2">
            Pipeline Status
          </h3>
          <StreamMetrics
            totalMessages={totalMessages}
            mps={messagesPerSecond}
            lastTickAge={lastTickAge}
          />
        </div>
      </main>
    </div>
  );
}