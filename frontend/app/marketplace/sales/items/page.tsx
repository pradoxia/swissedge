"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { fetchSalesItems, SalesItem, SalesPlatformListing } from "@/lib/api";

const PLATFORM_LABELS: Record<string, string> = {
  ricardo: "Ricardo",
  tutti: "Tutti",
  anibis: "Anibis",
  facebook_marketplace_ch: "Facebook",
};

const PLATFORM_ORDER = ["ricardo", "tutti", "anibis", "facebook_marketplace_ch"];

const STATUS_COLORS: Record<string, string> = {
  needs_info: "text-amber-400 border-amber-400/40",
  draft_ready: "text-cyan-400 border-cyan-400/40",
  ready_to_publish: "text-violet-400 border-violet-400/40",
  published: "text-green-400 border-green-400/40",
  sold: "text-emerald-400 border-emerald-400/40",
  archived: "text-gray-500 border-gray-600",
};

const PLATFORM_STATUS_COLORS: Record<string, string> = {
  not_listed: "text-gray-500 border-gray-700",
  draft: "text-amber-400 border-amber-400/40",
  published: "text-green-400 border-green-400/40",
  sold: "text-emerald-400 border-emerald-400/40",
  archived: "text-gray-600 border-gray-700",
};

function formatDate(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleDateString("de-CH", { day: "2-digit", month: "2-digit", year: "2-digit" }) +
    " " + d.toLocaleTimeString("de-CH", { hour: "2-digit", minute: "2-digit" });
}

function StatusBadge({ status, extraClass = "" }: { status: string; extraClass?: string }) {
  const color = STATUS_COLORS[status] ?? "text-gray-400 border-gray-600";
  return (
    <span className={`px-2 py-0.5 rounded text-xs font-mono font-bold border ${color} ${extraClass}`}>
      {status.toUpperCase().replace(/_/g, " ")}
    </span>
  );
}

function PlatformChip({ listing }: { listing: SalesPlatformListing }) {
  const color = PLATFORM_STATUS_COLORS[listing.status] ?? "text-gray-500 border-gray-700";
  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded border text-xs font-mono ${color}`}>
      {PLATFORM_LABELS[listing.platform] ?? listing.platform}
      <span className="opacity-60">·</span>
      <span className="opacity-80">{listing.status.replace(/_/g, " ")}</span>
    </span>
  );
}

function SalesItemCard({ item }: { item: SalesItem }) {
  const displayTitle = item.title || item.brand_model || "Untitled item";
  const sortedListings = PLATFORM_ORDER
    .map((p) => item.platform_listings.find((l) => l.platform === p))
    .filter((l): l is SalesPlatformListing => l !== undefined);

  return (
    <Link href={`/marketplace/sales/items/${item.id}`} className="block group">
    <div className="glass-panel rounded-lg p-5 flex flex-col gap-3 group-hover:border-cyan-500/30 transition-colors">
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1 min-w-0">
          <p className="text-sm font-bold text-gray-100 font-mono truncate">{displayTitle}</p>
          {item.brand_model && item.title && (
            <p className="text-xs font-mono text-gray-500 mt-0.5 truncate">{item.brand_model}</p>
          )}
        </div>
        <StatusBadge status={item.status} />
      </div>

      <div className="flex flex-wrap gap-x-6 gap-y-1 text-xs font-mono text-gray-400">
        {item.condition && (
          <span><span className="text-gray-600">Condition</span> {item.condition.replace(/_/g, " ")}</span>
        )}
        {item.target_price_chf && (
          <span><span className="text-gray-600">CHF</span> {item.target_price_chf}</span>
        )}
        {item.pickup_location && (
          <span><span className="text-gray-600">Location</span> {item.pickup_location}</span>
        )}
      </div>

      {sortedListings.length > 0 && (
        <div className="flex flex-wrap gap-1.5">
          {sortedListings.map((l) => (
            <PlatformChip key={l.platform} listing={l} />
          ))}
        </div>
      )}

      <div className="flex gap-4 text-xs font-mono text-gray-600 border-t border-gray-800 pt-2 mt-1">
        <span>Created {formatDate(item.created_at)}</span>
        {item.updated_at !== item.created_at && (
          <span>Updated {formatDate(item.updated_at)}</span>
        )}
      </div>
    </div>
    </Link>
  );
}

export default function SalesItemsPage() {
  const [items, setItems] = useState<SalesItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchSalesItems()
      .then(setItems)
      .catch((e: unknown) => setError(e instanceof Error ? e.message : "Failed to load"))
      .finally(() => setLoading(false));
  }, []);

  return (
    <>
      <div className="scan-line"></div>
      <div className="min-h-screen p-8">
        <div className="max-w-5xl mx-auto">
          <div className="mb-2 flex items-center gap-4">
            <Link href="/marketplace/sales" className="text-xs font-mono text-gray-500 hover:text-cyan-400 transition-colors">
              ← MARKETPLACE SALES
            </Link>
          </div>

          <div className="mb-8">
            <h1 className="text-4xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-amber-400 via-cyan-400 to-amber-400 mb-2">
              ITEMS FOR SALE
            </h1>
            <p className="text-gray-500 text-xs font-mono tracking-wider">
              PERSISTED SALES ITEMS // NO AUTO-PUBLISH
            </p>
          </div>

          <div className="glass-panel rounded-lg p-3 mb-8 border-red-500/20">
            <div className="flex flex-wrap gap-6 text-xs font-mono justify-center">
              <div className="flex items-center gap-2">
                <span className="text-gray-500">AUTO-PUBLISH:</span>
                <span className="text-red-400 font-bold">DISABLED</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-gray-500">HUMAN APPROVAL:</span>
                <span className="text-green-400">REQUIRED</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-gray-500">SOURCE:</span>
                <span className="text-cyan-400">GET /api/marketplace/sales/items</span>
              </div>
            </div>
          </div>

          {loading && (
            <div className="text-xs font-mono text-gray-500 text-center py-16">Loading items...</div>
          )}

          {error && (
            <div className="rounded border border-red-500/40 bg-red-500/5 p-4 mb-6">
              <p className="text-xs font-mono text-red-400">
                <span className="font-bold">Error:</span> {error}
              </p>
            </div>
          )}

          {!loading && !error && items.length === 0 && (
            <div className="glass-panel rounded-lg p-16 text-center">
              <p className="text-gray-500 font-mono text-sm">No sales items yet.</p>
              <p className="text-gray-600 font-mono text-xs mt-2">
                Items appear here after they are created via the Telegram bot or API.
              </p>
            </div>
          )}

          {!loading && items.length > 0 && (
            <>
              <div className="flex items-center gap-3 mb-4">
                <span className="text-xs font-mono font-bold text-gray-500 tracking-widest uppercase">
                  {items.length} item{items.length !== 1 ? "s" : ""}
                </span>
                <div className="flex-1 h-px bg-gray-800"></div>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {items.map((item) => (
                  <SalesItemCard key={item.id} item={item} />
                ))}
              </div>
            </>
          )}
        </div>
      </div>
    </>
  );
}
