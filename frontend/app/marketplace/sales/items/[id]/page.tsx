"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { use } from "react";
import { fetchSalesItem, generatePlatformDrafts, SalesItem, SalesPlatformListing } from "@/lib/api";

const PLATFORM_ORDER = ["ricardo", "tutti", "anibis", "facebook_marketplace_ch"];
const PLATFORM_LABELS: Record<string, string> = {
  ricardo: "Ricardo",
  tutti: "Tutti",
  anibis: "Anibis",
  facebook_marketplace_ch: "Facebook",
};

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

type Tab = "intake" | "ricardo" | "tutti" | "anibis" | "facebook_marketplace_ch" | "photos";

function formatDate(iso: string): string {
  const d = new Date(iso);
  return (
    d.toLocaleDateString("de-CH", { day: "2-digit", month: "2-digit", year: "2-digit" }) +
    " " +
    d.toLocaleTimeString("de-CH", { hour: "2-digit", minute: "2-digit" })
  );
}

function StatusBadge({ status }: { status: string }) {
  const color = STATUS_COLORS[status] ?? "text-gray-400 border-gray-600";
  return (
    <span className={`px-2 py-0.5 rounded text-xs font-mono font-bold border ${color}`}>
      {status.toUpperCase().replace(/_/g, " ")}
    </span>
  );
}

type CopyState = "idle" | "copied" | "failed";

function CopyButton({ text }: { text: string }) {
  const [state, setState] = useState<CopyState>("idle");
  const handle = async () => {
    try {
      await navigator.clipboard.writeText(text);
      setState("copied");
    } catch {
      setState("failed");
    }
    setTimeout(() => setState("idle"), 2000);
  };
  const color =
    state === "copied"
      ? "text-green-400 border-green-400/50"
      : state === "failed"
      ? "text-red-400 border-red-400/50"
      : "text-gray-500 border-gray-700 hover:text-cyan-400 hover:border-cyan-400/50";
  return (
    <button
      onClick={handle}
      className={`text-xs font-mono px-2 py-0.5 rounded border transition-colors ${color}`}
    >
      {state === "copied" ? "copied" : state === "failed" ? "failed" : "copy"}
    </button>
  );
}

function Field({ label, value }: { label: string; value: string }) {
  return (
    <div className="bg-gray-900 rounded border border-gray-800 p-3">
      <div className="flex items-center justify-between mb-1.5">
        <span className="text-xs font-mono text-gray-500 uppercase tracking-wider">{label}</span>
        <CopyButton text={value} />
      </div>
      <p className="text-sm font-mono text-gray-200 whitespace-pre-wrap leading-relaxed">{value}</p>
    </div>
  );
}

function IntakeTab({ item }: { item: SalesItem }) {
  const rows: [string, string | null][] = [
    ["Title", item.title],
    ["Brand / Model", item.brand_model],
    ["Category", item.category],
    ["Condition", item.condition],
    ["Target price CHF", item.target_price_chf],
    ["Pickup location", item.pickup_location],
    ["Shipping policy", item.shipping_policy],
    ["Description", item.description],
    ["Internal notes", item.internal_notes],
    ["Created from", item.created_from],
  ];
  const present = rows.filter(([, v]) => v != null && v !== "");
  if (present.length === 0) {
    return (
      <p className="text-xs font-mono text-gray-500 py-8 text-center">No intake fields filled yet.</p>
    );
  }
  return (
    <div className="space-y-3">
      {present.map(([label, value]) => (
        <Field key={label} label={label} value={value!} />
      ))}
      <div className="flex gap-6 text-xs font-mono text-gray-600 pt-2">
        <span>Created {formatDate(item.created_at)}</span>
        <span>Updated {formatDate(item.updated_at)}</span>
      </div>
    </div>
  );
}

function PlatformTab({ listing, platform }: { listing: SalesPlatformListing | undefined; platform: string }) {
  const statusColor =
    PLATFORM_STATUS_COLORS[listing?.status ?? "not_listed"] ?? "text-gray-500 border-gray-700";

  if (!listing) {
    return (
      <p className="text-xs font-mono text-gray-500 py-8 text-center">No listing record found.</p>
    );
  }

  const fields: [string, string | null][] = [
    ["Title", listing.title],
    ["Description", listing.description],
    ["Category suggestion", listing.category_suggestion],
    ["Price CHF", listing.price_chf],
    ["Publish URL", listing.publish_url],
    ["Published at", listing.published_at ? formatDate(listing.published_at) : null],
    ["Sold at", listing.sold_at ? formatDate(listing.sold_at) : null],
    ["Archived at", listing.archived_at ? formatDate(listing.archived_at) : null],
  ];
  const present = fields.filter(([, v]) => v != null && v !== "");

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3">
        <span className="text-xs font-mono text-gray-500">Platform status:</span>
        <span className={`px-2 py-0.5 rounded text-xs font-mono font-bold border ${statusColor}`}>
          {listing.status.toUpperCase().replace(/_/g, " ")}
        </span>
      </div>

      {present.length === 0 ? (
        <div className="rounded border border-gray-800 bg-gray-900/40 p-6 text-center">
          <p className="text-xs font-mono text-gray-500">No draft data yet for this platform.</p>
          <p className="text-xs font-mono text-gray-600 mt-1">
            Click &ldquo;Generate platform drafts&rdquo; above to populate listing fields.
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {present.map(([label, value]) => (
            <Field key={label} label={label} value={value!} />
          ))}
        </div>
      )}

      <div className="flex gap-6 text-xs font-mono text-gray-600 pt-1 border-t border-gray-800">
        <span>Record created {formatDate(listing.created_at)}</span>
        <span>Updated {formatDate(listing.updated_at)}</span>
      </div>

      <div className="rounded border border-red-500/20 bg-red-500/5 px-4 py-2">
        <p className="text-xs font-mono text-red-400">
          NO AUTO-PUBLISH — manual copy and review required before listing on this platform.
        </p>
      </div>
    </div>
  );
}

function PhotosTab() {
  return (
    <div className="rounded border border-gray-700 bg-gray-900/40 p-10 text-center">
      <p className="text-sm font-mono text-gray-400 mb-2">Photo storage is planned.</p>
      <p className="text-xs font-mono text-gray-600">
        Telegram / photo ingestion not implemented yet.
      </p>
    </div>
  );
}

export default function SalesItemDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const [item, setItem] = useState<SalesItem | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<Tab>("intake");
  const [generating, setGenerating] = useState(false);
  const [generateError, setGenerateError] = useState<string | null>(null);

  useEffect(() => {
    fetchSalesItem(id)
      .then(setItem)
      .catch((e: unknown) => setError(e instanceof Error ? e.message : "Failed to load"))
      .finally(() => setLoading(false));
  }, [id]);

  const handleGenerateDrafts = async () => {
    if (
      !window.confirm(
        "Generate platform draft copy for all 4 platforms?\n\n" +
          "• Generates draft text only\n" +
          "• Saves to SwissEdge\n" +
          "• Does NOT publish anywhere"
      )
    )
      return;
    setGenerating(true);
    setGenerateError(null);
    try {
      const updated = await generatePlatformDrafts(id);
      setItem(updated);
    } catch (e: unknown) {
      setGenerateError(e instanceof Error ? e.message : "Generation failed");
    } finally {
      setGenerating(false);
    }
  };

  const tabs: { key: Tab; label: string }[] = [
    { key: "intake", label: "Intake" },
    { key: "ricardo", label: "Ricardo" },
    { key: "tutti", label: "Tutti" },
    { key: "anibis", label: "Anibis" },
    { key: "facebook_marketplace_ch", label: "Facebook" },
    { key: "photos", label: "Photos" },
  ];

  return (
    <>
      <div className="scan-line"></div>
      <div className="min-h-screen p-8">
        <div className="max-w-4xl mx-auto">
          <div className="mb-2 flex items-center gap-4">
            <Link
              href="/marketplace/sales/items"
              className="text-xs font-mono text-gray-500 hover:text-cyan-400 transition-colors"
            >
              ← ITEMS FOR SALE
            </Link>
          </div>

          {loading && (
            <div className="text-xs font-mono text-gray-500 text-center py-24">Loading...</div>
          )}

          {error && (
            <div className="rounded border border-red-500/40 bg-red-500/5 p-4 mt-6">
              <p className="text-xs font-mono text-red-400">
                <span className="font-bold">Error:</span> {error}
              </p>
            </div>
          )}

          {item && (
            <>
              <div className="mb-6">
                <div className="flex items-start justify-between gap-4 mb-2">
                  <h1 className="text-3xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-amber-400 via-cyan-400 to-amber-400">
                    {item.title || item.brand_model || "Untitled item"}
                  </h1>
                  <StatusBadge status={item.status} />
                </div>
                <div className="flex flex-wrap gap-x-6 gap-y-1 text-xs font-mono text-gray-400">
                  {item.brand_model && item.title && (
                    <span>
                      <span className="text-gray-600">Brand</span> {item.brand_model}
                    </span>
                  )}
                  {item.category && (
                    <span>
                      <span className="text-gray-600">Category</span> {item.category}
                    </span>
                  )}
                  {item.condition && (
                    <span>
                      <span className="text-gray-600">Condition</span>{" "}
                      {item.condition.replace(/_/g, " ")}
                    </span>
                  )}
                  {item.target_price_chf && (
                    <span>
                      <span className="text-gray-600">CHF</span> {item.target_price_chf}
                    </span>
                  )}
                  {item.pickup_location && (
                    <span>
                      <span className="text-gray-600">Location</span> {item.pickup_location}
                    </span>
                  )}
                </div>
              </div>

              <div className="glass-panel rounded-lg p-4 mb-6 flex items-start justify-between gap-4 flex-wrap">
                <div className="space-y-1">
                  <p className="text-xs font-mono font-bold text-gray-300">Generate platform drafts</p>
                  <p className="text-xs font-mono text-gray-600">Generates draft copy only · Saves to SwissEdge · Does not publish anywhere</p>
                  {generateError && (
                    <p className="text-xs font-mono text-red-400 mt-1">
                      <span className="font-bold">Error:</span> {generateError}
                    </p>
                  )}
                </div>
                <button
                  onClick={handleGenerateDrafts}
                  disabled={generating}
                  className="px-4 py-1.5 rounded text-sm font-mono font-bold bg-violet-500/10 border border-violet-500/40 text-violet-400 hover:bg-violet-500/20 hover:border-violet-400 transition-all disabled:opacity-40 disabled:cursor-not-allowed whitespace-nowrap shrink-0"
                >
                  {generating ? "Generating..." : "Generate platform drafts"}
                </button>
              </div>

              <div className="flex gap-1 flex-wrap mb-6">
                {tabs.map((t) => {
                  const isActive = activeTab === t.key;
                  const platformListing = PLATFORM_ORDER.includes(t.key)
                    ? item.platform_listings.find((l) => l.platform === t.key)
                    : undefined;
                  const plStatus = platformListing?.status;
                  const dot =
                    plStatus && plStatus !== "not_listed"
                      ? plStatus === "published" || plStatus === "sold"
                        ? "bg-green-400"
                        : "bg-amber-400"
                      : null;

                  return (
                    <button
                      key={t.key}
                      onClick={() => setActiveTab(t.key)}
                      className={`flex items-center gap-1.5 px-3 py-1.5 rounded text-xs font-mono font-bold border transition-all ${
                        isActive
                          ? "bg-cyan-500/15 border-cyan-500/50 text-cyan-400"
                          : "bg-gray-900 border-gray-700 text-gray-500 hover:text-gray-300 hover:border-gray-600"
                      }`}
                    >
                      {dot && <span className={`w-1.5 h-1.5 rounded-full ${dot} shrink-0`} />}
                      {t.label}
                    </button>
                  );
                })}
              </div>

              <div className="glass-panel rounded-lg p-6">
                {activeTab === "intake" && <IntakeTab item={item} />}
                {(activeTab === "ricardo" ||
                  activeTab === "tutti" ||
                  activeTab === "anibis" ||
                  activeTab === "facebook_marketplace_ch") && (
                  <PlatformTab
                    platform={activeTab}
                    listing={item.platform_listings.find((l) => l.platform === activeTab)}
                  />
                )}
                {activeTab === "photos" && <PhotosTab />}
              </div>
            </>
          )}
        </div>
      </div>
    </>
  );
}
