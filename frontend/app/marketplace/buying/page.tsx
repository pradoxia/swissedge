import Link from "next/link";

export default function MarketplaceBuyingPage() {
  return (
    <>
      <div className="scan-line"></div>
      <div className="min-h-screen p-8">
        <div className="max-w-5xl mx-auto">

          <div className="mb-2 flex items-center gap-4">
            <Link href="/marketplace" className="text-xs font-mono text-gray-500 hover:text-cyan-400 transition-colors">
              ← MARKETPLACE
            </Link>
          </div>

          <div className="mb-8">
            <h1 className="text-4xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-gray-400 via-gray-300 to-gray-400 mb-2">
              BUYING / PRICE RESEARCH
            </h1>
            <p className="text-gray-500 text-xs font-mono tracking-wider">
              PARKED // SALES WORKFLOW IS PRIORITY
            </p>
          </div>

          <div className="glass-panel rounded-lg p-8 mb-8 border-gray-700/40 text-center">
            <div className="text-5xl mb-4">🔍</div>
            <h2 className="text-xl font-bold text-gray-300 mb-3">Coming Later</h2>
            <p className="text-sm font-mono text-gray-500 max-w-lg mx-auto mb-6 leading-relaxed">
              Buying / price hunting research is intentionally deferred. The sales workflow (listing generation,
              draft review, Telegram alerts) is the current priority. Buying tools will be added once sales is
              stable end-to-end.
            </p>
            <div className="space-y-2 text-xs font-mono text-gray-600 mb-6">
              <p>No scraping — all price research will remain manual reference only</p>
              <p>No external API calls from this section</p>
              <p>No auto-purchasing — human decision required for every acquisition</p>
            </div>
            <div className="flex flex-col gap-2 text-xs font-mono text-gray-500 max-w-sm mx-auto">
              <span className="text-gray-600 uppercase tracking-widest text-xs mb-1">Planned features</span>
              {[
                "Price alert watchlist for target items",
                "Comparable research workflow",
                "Purchase opportunity notes",
                "Source directory for buying research",
              ].map((f, i) => (
                <div key={i} className="flex items-start gap-2 text-left">
                  <span className="text-gray-700 shrink-0">-</span><span>{f}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="text-center">
            <Link href="/marketplace/sales" className="inline-block px-5 py-2 rounded text-sm font-mono font-bold bg-amber-500/10 border border-amber-500/40 text-amber-400 hover:bg-amber-500/20 hover:border-amber-400 transition-all">
              Go to Sales Automation →
            </Link>
          </div>

        </div>
      </div>
    </>
  );
}