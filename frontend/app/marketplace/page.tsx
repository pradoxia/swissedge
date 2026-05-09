import Link from "next/link";

export default function MarketplaceHubPage() {
  return (
    <>
      <div className="scan-line"></div>
      <div className="min-h-screen p-8">
        <div className="max-w-5xl mx-auto">

          <div className="mb-2 flex items-center gap-4">
            <Link href="/" className="text-xs font-mono text-gray-500 hover:text-cyan-400 transition-colors">
              ← MISSION CONTROL
            </Link>
          </div>

          <div className="mb-8">
            <h1 className="text-4xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-amber-400 via-cyan-400 to-amber-400 mb-2">
              MARKETPLACE ASSISTANT
            </h1>
            <p className="text-gray-500 text-xs font-mono tracking-wider">
              SELL AND BUY // HUMAN-IN-THE-LOOP // NO AUTO-PUBLISHING
            </p>
          </div>

          <div className="glass-panel rounded-lg p-3 mb-10 border-amber-500/20">
            <div className="flex flex-wrap gap-6 text-xs font-mono justify-center">
              <div className="flex items-center gap-2"><span className="text-gray-500">AUTO-PUBLISH:</span><span className="text-red-400 font-bold">DISABLED</span></div>
              <div className="flex items-center gap-2"><span className="text-gray-500">HUMAN CONFIRMATION:</span><span className="text-green-400">REQUIRED</span></div>
              <div className="flex items-center gap-2"><span className="text-gray-500">BUYER REPLIES:</span><span className="text-amber-400">DANI APPROVAL FIRST</span></div>
              <div className="flex items-center gap-2"><span className="text-gray-500">IMAGE ENHANCEMENT:</span><span className="text-amber-400">NO MISREPRESENTATION</span></div>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-10">

            <Link href="/marketplace/sales" className="glass-panel rounded-lg p-6 hover:border-amber-400/50 transition-all duration-300 group">
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-center gap-3">
                  <span className="text-3xl">🏷️</span>
                  <div>
                    <h2 className="text-lg font-bold text-gray-100 group-hover:text-amber-400 transition-colors">Sales Automation</h2>
                    <p className="text-xs font-mono text-gray-500 mt-0.5">ACTIVE</p>
                  </div>
                </div>
                <span className="px-2 py-0.5 rounded text-xs font-mono font-bold border border-current text-amber-400">PARTIAL</span>
              </div>
              <ul className="space-y-1 mb-4">
                {[
                  "Sell household items with assisted AI drafts",
                  "Listing Generator — Hochdeutsch, Tutti.ch ready",
                  "Manual Price Research workflow",
                  "Draft review and copy-to-clipboard UX",
                  "Telegram photo → draft pipeline (coming)",
                  "Buyer question routing to Dani (coming)",
                ].map((f, i) => (
                  <li key={i} className="text-xs font-mono text-gray-400 flex items-start gap-2">
                    <span className="text-amber-600 mt-0.5 shrink-0">+</span><span>{f}</span>
                  </li>
                ))}
              </ul>
              <div className="h-0.5 bg-gray-800 rounded-full overflow-hidden">
                <div className="h-full bg-amber-400 w-1/2 transition-all duration-500"></div>
              </div>
            </Link>

            <Link href="/marketplace/buying" className="glass-panel rounded-lg p-6 hover:border-gray-500/50 transition-all duration-300 group opacity-60">
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-center gap-3">
                  <span className="text-3xl">🔍</span>
                  <div>
                    <h2 className="text-lg font-bold text-gray-100 group-hover:text-gray-300 transition-colors">Buying / Price Research</h2>
                    <p className="text-xs font-mono text-gray-500 mt-0.5">PARKED</p>
                  </div>
                </div>
                <span className="px-2 py-0.5 rounded text-xs font-mono font-bold border border-current text-gray-500">LATER</span>
              </div>
              <ul className="space-y-1 mb-4">
                {[
                  "Price hunting and comparable research",
                  "Purchase opportunity alerts",
                  "No scraping or API calls — manual references only",
                  "Intentionally deferred — sales workflow is priority",
                ].map((f, i) => (
                  <li key={i} className="text-xs font-mono text-gray-500 flex items-start gap-2">
                    <span className="text-gray-600 mt-0.5 shrink-0">-</span><span>{f}</span>
                  </li>
                ))}
              </ul>
              <div className="h-0.5 bg-gray-800 rounded-full overflow-hidden">
                <div className="h-full bg-gray-600 w-1/4 transition-all duration-500"></div>
              </div>
            </Link>

          </div>

          <div className="glass-panel rounded-lg p-4 border-amber-500/20">
            <div className="flex items-center justify-between text-xs font-mono">
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 bg-amber-400 rounded-full"></div>
                <span className="text-gray-400">MARKETPLACE STATUS:</span>
                <span className="text-amber-400">SALES-FIRST // BUYING PARKED</span>
              </div>
              <div className="text-gray-600">PLATFORM: TUTTI.CH // PUBLISH: MANUAL</div>
            </div>
          </div>

        </div>
      </div>
    </>
  );
}