"use client";

import { useState } from "react";
import Link from "next/link";

const API_BASE_URL = process.env.NEXT_PUBLIC_SWISSEDGE_API_BASE_URL || "http://localhost:8000";

interface ListingDraft {
  title: string;
  description: string;
  category_suggestion?: string;
}

interface CapabilityCard {
  title: string;
  status: string;
  statusColor: string;
  endpoint: string | null;
  notes: string[];
}

const capabilities: CapabilityCard[] = [
  { title: "Listing Generator", status: "ACTIVE", statusColor: "text-green-400", endpoint: "POST /api/marketplace/generate-listing", notes: ["Generates Hochdeutsch listing descriptions via AI", "Output is a draft — no publishing", "Human approval required before use"] },
  { title: "Price Assistant", status: "ACTIVE", statusColor: "text-green-400", endpoint: "POST /api/marketplace/get-price", notes: ["Compares prices on Tutti.ch", "Returns price range and comparable listings", "Read-only — no data written"] },
  { title: "Comparable Search", status: "PARTIAL", statusColor: "text-amber-400", endpoint: "POST /api/marketplace/search", notes: ["Tutti.ch live scraper — may return empty results", "Scraper currently blocked by 403 / anti-bot", "Read-only — no mutation"] },
  { title: "Draft Review", status: "MANUAL", statusColor: "text-cyan-400", endpoint: null, notes: ["All generated listings require manual review", "Copy-paste workflow — no direct publish API", "Phase 2: direct Tutti adapter publish (not implemented)"] },
  { title: "Safety Guard", status: "ACTIVE", statusColor: "text-green-400", endpoint: null, notes: ["PII filter on all outgoing Telegram messages", "Blocks: phone numbers, addresses, IBAN, email", "Non-negotiable — always active regardless of trust score"] },
];

function StatusBadge({ status, colorClass }: { status: string; colorClass: string }) {
  return <span className={`px-2 py-0.5 rounded text-xs font-mono font-bold border border-current ${colorClass}`}>{status}</span>;
}

function SectionLabel({ label }: { label: string }) {
  return (
    <div className="flex items-center gap-3 mb-4">
      <span className="text-xs font-mono font-bold text-gray-500 tracking-widest uppercase">{label}</span>
      <div className="flex-1 h-px bg-gray-800"></div>
    </div>
  );
}

type CopyState = "idle" | "copied" | "failed";

function robustCopy(text: string): Promise<"copied" | "failed"> {
  if (typeof navigator !== "undefined" && navigator.clipboard && navigator.clipboard.writeText) {
    return navigator.clipboard.writeText(text).then(() => "copied" as const).catch(() => execCommandCopy(text));
  }
  return Promise.resolve(execCommandCopy(text));
}

function execCommandCopy(text: string): "copied" | "failed" {
  try {
    const ta = document.createElement("textarea");
    ta.value = text;
    ta.style.position = "fixed";
    ta.style.opacity = "0";
    document.body.appendChild(ta);
    ta.focus();
    ta.select();
    const ok = document.execCommand("copy");
    document.body.removeChild(ta);
    return ok ? "copied" : "failed";
  } catch {
    return "failed";
  }
}

function CopyButton({ text, label = "copy" }: { text: string; label?: string }) {
  const [state, setState] = useState<CopyState>("idle");
  const handleCopy = async () => {
    const result = await robustCopy(text);
    setState(result);
    setTimeout(() => setState("idle"), 2500);
  };
  const display = state === "copied" ? "copied" : state === "failed" ? "failed" : label;
  const color = state === "copied" ? "text-green-400 border-green-400/50" : state === "failed" ? "text-red-400 border-red-400/50" : "text-gray-500 border-gray-700 hover:text-cyan-400 hover:border-cyan-400/50";
  return (
    <button onClick={handleCopy} className={"text-xs font-mono px-2 py-0.5 rounded border transition-colors " + color}>
      {display}
    </button>
  );
}

function buildFullText(draft: ListingDraft, price: string, location: string): string {
  const parts: string[] = [];
  parts.push("Titel: " + draft.title);
  parts.push("");
  parts.push(draft.description);
  if (draft.category_suggestion) parts.push("", "Kategorie: " + draft.category_suggestion);
  if (price) parts.push("Preis: CHF " + price);
  if (location) parts.push("Abholung: " + location);
  return parts.join("\n");
}

function FullCopyBlock({ draft, price, location }: { draft: ListingDraft; price: string; location: string }) {
  const [state, setState] = useState<CopyState>("idle");
  const [showManual, setShowManual] = useState(false);
  const fullText = buildFullText(draft, price, location);

  const handleCopy = async () => {
    const result = await robustCopy(fullText);
    if (result === "copied") {
      setState("copied");
      setShowManual(false);
      setTimeout(() => setState("idle"), 2500);
    } else {
      setState("failed");
      setShowManual(true);
    }
  };

  const btnColor =
    state === "copied" ? "border-green-400/60 text-green-400 bg-green-500/10" :
    state === "failed" ? "border-red-400/60 text-red-400 bg-red-500/10" :
    "border-cyan-500/40 text-cyan-400 bg-cyan-500/10 hover:bg-cyan-500/20 hover:border-cyan-400";

  return (
    <div className="rounded border border-gray-700 bg-gray-900/50 p-4">
      <div className="flex items-center gap-3 flex-wrap">
        <button
          onClick={handleCopy}
          className={"px-4 py-1.5 rounded text-sm font-mono font-bold border transition-all " + btnColor}
        >
          {state === "copied" ? "Copied" : state === "failed" ? "Copy failed — select manually" : "Copy full listing"}
        </button>
        <span className="text-xs font-mono text-gray-600">title + description + category + price + location</span>
      </div>
      {showManual && (
        <div className="mt-3">
          <p className="text-xs font-mono text-amber-400 mb-2">Clipboard unavailable — select all and copy manually:</p>
          <textarea
            readOnly
            value={fullText}
            rows={8}
            onClick={(e) => (e.target as HTMLTextAreaElement).select()}
            className="w-full bg-gray-950 border border-gray-700 rounded px-3 py-2 text-sm text-gray-300 font-mono focus:outline-none focus:border-amber-500/60 resize-none"
          />
        </div>
      )}
    </div>
  );
}

function ManualPublishChecklist() {
  const items = [
    "Review generated title — edit if needed before pasting",
    "Review generated description — check for accuracy and tone",
    "Verify price — confirm it matches your target",
    "Copy title + description into Tutti.ch or Ricardo manually",
    "Do not publish without completing this review",
  ];
  return (
    <div className="rounded border border-gray-800 bg-gray-900/30 p-4">
      <span className="text-xs font-mono font-bold text-gray-500 tracking-widest uppercase">Manual Publish Checklist</span>
      <ul className="mt-3 space-y-2">
        {items.map((item, i) => (
          <li key={i} className="flex items-start gap-2 text-xs font-mono text-gray-400">
            <span className="text-gray-600 mt-0.5 shrink-0">[ ]</span>
            <span>{item}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}


interface PriceResearchProps {
  itemDescription: string;
  brand: string;
  category: string;
  condition: string;
  price: string;
}

function buildSearchPhrase(item: string, brand: string): string {
  return [brand, item].filter(Boolean).join(" ").trim();
}

function ManualPriceResearch({ itemDescription, brand, category, condition, price }: PriceResearchProps) {
  const base = buildSearchPhrase(itemDescription, brand);
  const condSuffix = condition !== "Gut" ? " " + condition : "";
  const phrases = [
    { platform: "Ricardo.ch", phrase: (base + condSuffix).trim() },
    { platform: "Tutti.ch", phrase: (base + condSuffix).trim() },
    { platform: "Toppreise.ch", phrase: base },
    { platform: "Digitec / Galaxus", phrase: base },
  ];
  const [low, setLow] = useState("");
  const [typical, setTypical] = useState("");
  const [high, setHigh] = useState("");
  const [notes, setNotes] = useState("");
  const lowN = parseFloat(low);
  const typN = parseFloat(typical);
  const highN = parseFloat(high);
  const hasRange = !isNaN(lowN) && !isNaN(typN) && !isNaN(highN) && lowN > 0 && typN > 0 && highN > 0;
  const conservative = hasRange ? Math.round(lowN * 0.95) : null;
  const fair = hasRange ? Math.round(typN * 0.9) : null;
  const optimistic = hasRange ? Math.round(highN * 0.85) : null;
  const ic = "w-full bg-gray-900 border border-gray-700 rounded px-3 py-2 text-sm text-gray-200 font-mono placeholder-gray-600 focus:outline-none focus:border-cyan-500/60 transition-colors";
  const lc = "block text-xs font-mono text-gray-500 mb-1 uppercase tracking-wider";
  const checklist = [
    "Search Ricardo active listings with the phrase above",
    "Check Ricardo sold / completed listings if accessible",
    "Compare Tutti.ch and Anibis.ch active listings",
    "Check new retail price on Toppreise.ch / Digitec / Galaxus",
    "Adjust asking price based on condition and urgency",
  ];
  if (!itemDescription.trim()) return null;
  return (
    <div className="glass-panel rounded-lg p-6 mb-10">
      <div className="flex items-start justify-between mb-4">
        <div>
          <h2 className="text-base font-bold text-gray-100">Manual Price Research</h2>
          <p className="text-xs font-mono text-gray-600 mt-0.5">Manual research only — no scraping, no API calls, no auto-pricing.</p>
        </div>
        <span className="px-2 py-0.5 rounded text-xs font-mono font-bold border border-current text-cyan-400">MANUAL</span>
      </div>
      <div className="mb-6">
        <span className="text-xs font-mono font-bold text-gray-500 tracking-widest uppercase">Suggested Search Phrases</span>
        <div className="mt-3 space-y-2">
          {phrases.map((p) => (
            <div key={p.platform} className="flex items-center gap-3 bg-gray-900 rounded border border-gray-800 px-3 py-2">
              <span className="text-xs font-mono text-gray-500 w-36 shrink-0">{p.platform}</span>
              <span className="text-sm font-mono text-gray-200 flex-1">{p.phrase || "—"}</span>
              {p.phrase && <CopyButton text={p.phrase} />}
            </div>
          ))}
        </div>
        <p className="mt-2 text-xs font-mono text-gray-600">Phrases update live from the form fields above.</p>
      </div>
      <div className="mb-6">
        <span className="text-xs font-mono font-bold text-gray-500 tracking-widest uppercase">Research Checklist</span>
        <ul className="mt-3 space-y-2">
          {checklist.map((item, i) => (
            <li key={i} className="flex items-start gap-2 text-xs font-mono text-gray-400">
              <span className="text-gray-600 mt-0.5 shrink-0">[ ]</span>
              <span>{item}</span>
            </li>
          ))}
        </ul>
      </div>
      <div className="mb-4">
        <span className="text-xs font-mono font-bold text-gray-500 tracking-widest uppercase">Observed Market Prices (CHF)</span>
        <div className="mt-3 grid grid-cols-1 md:grid-cols-3 gap-3">
          <div>
            <label className={lc}>Lowest comparable</label>
            <input type="number" min="0" step="1" value={low} onChange={(e) => setLow(e.target.value)} placeholder="0" className={ic} />
          </div>
          <div>
            <label className={lc}>Typical comparable</label>
            <input type="number" min="0" step="1" value={typical} onChange={(e) => setTypical(e.target.value)} placeholder="0" className={ic} />
          </div>
          <div>
            <label className={lc}>Highest comparable</label>
            <input type="number" min="0" step="1" value={high} onChange={(e) => setHigh(e.target.value)} placeholder="0" className={ic} />
          </div>
        </div>
        <div className="mt-3">
          <label className={lc}>Research notes</label>
          <textarea value={notes} onChange={(e) => setNotes(e.target.value)} rows={2} placeholder="e.g. Ricardo has 3 active at 80-120 CHF, Tutti blocked..." className={ic + " resize-none"} />
        </div>
      </div>
      {hasRange && (
        <div className="rounded border border-gray-700 bg-gray-900/50 p-4">
          <span className="text-xs font-mono font-bold text-gray-500 tracking-widest uppercase">Suggested Asking Range</span>
          <div className="mt-3 grid grid-cols-3 gap-3">
            <div className="text-center">
              <p className="text-xs font-mono text-gray-500 mb-1">Conservative</p>
              <p className="text-lg font-bold font-mono text-amber-400">CHF {conservative}</p>
              <p className="text-xs font-mono text-gray-600">~5% below lowest</p>
            </div>
            <div className="text-center">
              <p className="text-xs font-mono text-gray-500 mb-1">Fair</p>
              <p className="text-lg font-bold font-mono text-cyan-400">CHF {fair}</p>
              <p className="text-xs font-mono text-gray-600">~10% below typical</p>
            </div>
            <div className="text-center">
              <p className="text-xs font-mono text-gray-500 mb-1">Optimistic</p>
              <p className="text-lg font-bold font-mono text-green-400">CHF {optimistic}</p>
              <p className="text-xs font-mono text-gray-600">~15% below highest</p>
            </div>
          </div>
          <p className="mt-3 text-xs font-mono text-gray-600">Manual helper only — final price decision remains human. Not financial advice.</p>
        </div>
      )}
      {price && !hasRange && (
        <p className="text-xs font-mono text-gray-600">Target price from form: CHF {price} — fill observed prices above to see suggested range.</p>
      )}
    </div>
  );
}

interface RicardoDraftProps {
  draft: ListingDraft;
  condition: string;
  price: string;
  location: string;
  details: string;
}

function buildRicardoPayload(draft: ListingDraft, condition: string, price: string, location: string, details: string): string {
  const fieldLines: string[] = [];
  fieldLines.push("TITEL: " + draft.title.slice(0, 60));
  fieldLines.push("");
  fieldLines.push("BESCHREIBUNG:");
  fieldLines.push(draft.description.slice(0, 2000));
  if (draft.category_suggestion) fieldLines.push("", "KATEGORIE: " + draft.category_suggestion);
  fieldLines.push("ZUSTAND: " + condition);
  fieldLines.push("VERKAUFSMODUS: Festpreis");
  if (price) fieldLines.push("PREIS CHF: " + price);
  if (location) fieldLines.push("STANDORT: " + location);
  if (details) fieldLines.push("", "ZUBEHOER / NOTIZEN: " + details);
  return fieldLines.join("\n");
}

function RicardoDraftPanel({ draft, condition, price, location, details }: RicardoDraftProps) {
  const [payloadState, setPayloadState] = useState<CopyState>("idle");
  const [showManualPayload, setShowManualPayload] = useState(false);
  const payload = buildRicardoPayload(draft, condition, price, location, details);

  const titleField = draft.title.slice(0, 60);
  const descField = draft.description.slice(0, 2000);
  const titleWarning = draft.title.length > 60;
  const descWarning = draft.description.length > 2000;

  const handleCopyPayload = async () => {
    const result = await robustCopy(payload);
    if (result === "copied") {
      setPayloadState("copied");
      setShowManualPayload(false);
      setTimeout(() => setPayloadState("idle"), 2500);
    } else {
      setPayloadState("failed");
      setShowManualPayload(true);
    }
  };

  const payloadBtnColor =
    payloadState === "copied" ? "border-green-400/60 text-green-400 bg-green-500/10" :
    payloadState === "failed" ? "border-red-400/60 text-red-400 bg-red-500/10" :
    "border-amber-500/40 text-amber-400 bg-amber-500/10 hover:bg-amber-500/20 hover:border-amber-400";

  const checklist = [
    "Open Ricardo.ch and start a new listing",
    "Paste title (Titel) — max 60 characters",
    "Paste description (Beschreibung) — max 2000 characters",
    "Choose category (Kategorie) manually in Ricardo",
    "Add real item photos — must show actual condition",
    "Verify condition (Zustand) matches real item state",
    "Check defects and accessories are accurately listed",
    "Confirm price (Preis) before publishing",
    "Publish manually only after completing this review",
  ];

  const fieldRow = (label: string, value: string, warn?: boolean) => (
    <div className="bg-gray-900 rounded border border-gray-800 p-4">
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <span className="text-xs font-mono text-gray-500 uppercase tracking-wider">{label}</span>
          {warn && <span className="text-xs font-mono text-amber-400">(truncated)</span>}
        </div>
        <CopyButton text={value} />
      </div>
      <p className="text-sm text-gray-200 font-mono whitespace-pre-wrap leading-relaxed">{value}</p>
    </div>
  );

  return (
    <div className="mt-6 rounded border border-amber-500/20 bg-amber-500/3 p-5 space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <span className="text-xs font-mono font-bold text-amber-400 tracking-widest uppercase">Ricardo-Ready Draft</span>
          <p className="text-xs font-mono text-gray-600 mt-0.5">Phase 1 — copy fields manually into Ricardo</p>
        </div>
        <span className="text-xs font-mono text-red-400 border border-red-500/30 px-2 py-0.5 rounded">NOT PUBLISHED</span>
      </div>

      <div className="flex flex-wrap gap-3 text-xs font-mono">
        <span className="text-red-400">NO CREDENTIALS STORED</span>
        <span className="text-red-400">NO RICARDO API CALLS</span>
        <span className="text-red-400">NO AUTO-PUBLISH</span>
        <span className="text-amber-400">PHOTOS: SHOW REAL CONDITION</span>
      </div>

      <div className="space-y-3">
        {fieldRow("Titel (max 60 chars)", titleField, titleWarning)}
        {fieldRow("Beschreibung (max 2000 chars)", descField, descWarning)}
        {draft.category_suggestion && fieldRow("Kategorie (suggestion)", draft.category_suggestion)}
        {fieldRow("Zustand", condition)}
        {fieldRow("Verkaufsmodus", "Festpreis")}
        {price && fieldRow("Preis CHF", price)}
        {location && fieldRow("Standort", location)}
        {details && fieldRow("Zubehoer / Notizen", details)}
      </div>

      <div className="rounded border border-gray-700 bg-gray-900/50 p-4">
        <div className="flex items-center gap-3 flex-wrap">
          <button
            onClick={handleCopyPayload}
            className={"px-4 py-1.5 rounded text-sm font-mono font-bold border transition-all " + payloadBtnColor}
          >
            {payloadState === "copied" ? "Copied" : payloadState === "failed" ? "Copy failed — select manually" : "Copy Ricardo payload"}
          </button>
          <span className="text-xs font-mono text-gray-600">all fields as plain text</span>
        </div>
        {showManualPayload && (
          <div className="mt-3">
            <p className="text-xs font-mono text-amber-400 mb-2">Clipboard unavailable — select all and copy manually:</p>
            <textarea
              readOnly
              value={payload}
              rows={10}
              onClick={(e) => (e.target as HTMLTextAreaElement).select()}
              className="w-full bg-gray-950 border border-gray-700 rounded px-3 py-2 text-sm text-gray-300 font-mono focus:outline-none focus:border-amber-500/60 resize-none"
            />
          </div>
        )}
      </div>

      <div className="rounded border border-gray-800 bg-gray-900/30 p-4">
        <span className="text-xs font-mono font-bold text-gray-500 tracking-widest uppercase">Manual Publish Checklist — Ricardo</span>
        <ul className="mt-3 space-y-2">
          {checklist.map((item, i) => (
            <li key={i} className="flex items-start gap-2 text-xs font-mono text-gray-400">
              <span className="text-gray-600 mt-0.5 shrink-0">[ ]</span>
              <span>{item}</span>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
function ListingGeneratorForm() {
  const [itemDescription, setItemDescription] = useState("");
  const [brand, setBrand] = useState("");
  const [category, setCategory] = useState("");
  const [condition, setCondition] = useState("Gut");
  const [details, setDetails] = useState("");
  const [price, setPrice] = useState("");
  const [location, setLocation] = useState("");
  const [loading, setLoading] = useState(false);
  const [draft, setDraft] = useState<ListingDraft | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setDraft(null);
    setError(null);
    const parts: string[] = [itemDescription];
    if (details) parts.push("Details: " + details);
    if (location) parts.push("Standort: " + location);
    const fullDescription = parts.join(". ");
    try {
      const res = await fetch(API_BASE_URL + "/api/marketplace/generate-listing", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          item_description: fullDescription,
          brand: brand || "",
          condition,
          category: category || "",
          price: price ? parseFloat(price) : 0,
        }),
      });
      if (!res.ok) {
        const body = await res.json().catch(() => ({ detail: res.statusText }));
        throw new Error(body.detail ?? "HTTP " + res.status);
      }
      setDraft(await res.json());
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  };

  const ic = "w-full bg-gray-900 border border-gray-700 rounded px-3 py-2 text-sm text-gray-200 font-mono placeholder-gray-600 focus:outline-none focus:border-cyan-500/60 transition-colors";
  const lc = "block text-xs font-mono text-gray-500 mb-1 uppercase tracking-wider";

  return (
    <div className="glass-panel rounded-lg p-6 mb-10">
      <div className="flex items-start justify-between mb-5">
        <div>
          <h2 className="text-base font-bold text-gray-100">Listing Generator</h2>
          <p className="text-xs font-mono text-gray-600 mt-0.5">POST /api/marketplace/generate-listing</p>
        </div>
        <StatusBadge status="ACTIVE" colorClass="text-green-400" />
      </div>
      <div className="mb-4 flex flex-wrap gap-4 text-xs font-mono">
        <span className="text-red-400">NO AUTO-PUBLISH</span>
        <span className="text-amber-400">HUMAN APPROVAL REQUIRED</span>
        <span className="text-green-400">DRAFT ONLY</span>
        <span className="text-cyan-400">HOCHDEUTSCH</span>
      </div>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className={lc}>Item title / name *</label>
            <input type="text" required value={itemDescription} onChange={(e) => setItemDescription(e.target.value)} placeholder="z.B. iPhone 13, Rennvelo Trek, Sofa" className={ic} />
          </div>
          <div>
            <label className={lc}>Brand / Model</label>
            <input type="text" value={brand} onChange={(e) => setBrand(e.target.value)} placeholder="z.B. Apple, Trek, IKEA" className={ic} />
          </div>
          <div>
            <label className={lc}>Category</label>
            <input type="text" value={category} onChange={(e) => setCategory(e.target.value)} placeholder="z.B. Elektronik, Sport, Moebel" className={ic} />
          </div>
          <div>
            <label className={lc}>Condition</label>
            <select value={condition} onChange={(e) => setCondition(e.target.value)} className={ic}>
              <option value="Neuwertig">Neuwertig</option>
              <option value="Sehr gut">Sehr gut</option>
              <option value="Gut">Gut</option>
              <option value="In Ordnung">In Ordnung</option>
              <option value="Defekt">Defekt</option>
            </select>
          </div>
          <div>
            <label className={lc}>Target price CHF (optional)</label>
            <input type="number" min="0" step="0.01" value={price} onChange={(e) => setPrice(e.target.value)} placeholder="0" className={ic} />
          </div>
          <div>
            <label className={lc}>Pickup / location notes (optional)</label>
            <input type="text" value={location} onChange={(e) => setLocation(e.target.value)} placeholder="z.B. Zuerich Oerlikon, Versand moeglich" className={ic} />
          </div>
        </div>
        <div>
          <label className={lc}>Key details / notes</label>
          <textarea value={details} onChange={(e) => setDetails(e.target.value)} rows={3} placeholder="Wichtige Merkmale, Zubehoer, Besonderheiten..." className={ic + " resize-none"} />
        </div>
        <div className="flex items-center gap-4">
          <button type="submit" disabled={loading || !itemDescription.trim()} className="px-5 py-2 rounded text-sm font-mono font-bold bg-cyan-500/10 border border-cyan-500/40 text-cyan-400 hover:bg-cyan-500/20 hover:border-cyan-400 transition-all disabled:opacity-40 disabled:cursor-not-allowed">
            {loading ? "Generating..." : "Generate draft listing"}
          </button>
          <span className="text-xs font-mono text-gray-600">Language: Hochdeutsch (fixed)</span>
        </div>
      </form>
      {error && (
        <div className="mt-5 rounded border border-red-500/40 bg-red-500/5 p-4">
          <p className="text-xs font-mono text-red-400"><span className="font-bold">Error:</span> {error}</p>
        </div>
      )}
      <ManualPriceResearch itemDescription={itemDescription} brand={brand} category={category} condition={condition} price={price} />
      {draft && (
        <div className="mt-6 space-y-4">
          <div className="flex items-center gap-3 mb-2">
            <span className="text-xs font-mono font-bold text-amber-400 tracking-widest uppercase">Draft Result</span>
            <div className="flex-1 h-px bg-gray-800"></div>
            <span className="text-xs font-mono text-red-400 border border-red-500/30 px-2 py-0.5 rounded">NOT PUBLISHED</span>
          </div>

          <FullCopyBlock draft={draft} price={price} location={location} />

          <div className="space-y-3">
            <div className="bg-gray-900 rounded border border-gray-800 p-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-mono text-gray-500 uppercase tracking-wider">Title</span>
                <CopyButton text={draft.title} />
              </div>
              <p className="text-sm text-gray-100 font-mono">{draft.title}</p>
            </div>
            <div className="bg-gray-900 rounded border border-gray-800 p-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-mono text-gray-500 uppercase tracking-wider">Description</span>
                <CopyButton text={draft.description} />
              </div>
              <p className="text-sm text-gray-300 font-mono whitespace-pre-wrap leading-relaxed">{draft.description}</p>
            </div>
            {draft.category_suggestion && (
              <div className="bg-gray-900 rounded border border-gray-800 p-4">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-mono text-gray-500 uppercase tracking-wider">Category suggestion</span>
                  <CopyButton text={draft.category_suggestion!} />
                </div>
                <p className="text-sm text-gray-300 font-mono">{draft.category_suggestion}</p>
              </div>
            )}
          </div>

          <ManualPublishChecklist />

          <RicardoDraftPanel draft={draft} condition={condition} price={price} location={location} details={details} />

          <p className="text-xs font-mono text-gray-600">Draft only — review carefully before copying to Tutti.ch or Ricardo. No data was published or saved.</p>
        </div>
      )}
    </div>
  );
}


interface PriceSource {
  name: string;
  purpose: string;
  categories: string;
}

interface PriceSourceGroup {
  group: string;
  sources: PriceSource[];
}

const priceSourceGroups: PriceSourceGroup[] = [
  {
    group: "Selling Platforms",
    sources: [
      { name: "Tutti.ch", purpose: "List and browse CH second-hand", categories: "general" },
      { name: "Ricardo.ch", purpose: "Auction and fixed-price CH marketplace", categories: "general" },
      { name: "Anibis.ch", purpose: "CH classifieds — furniture, vehicles, misc", categories: "furniture / general" },
      { name: "Facebook Marketplace", purpose: "Local buyer network", categories: "general" },
    ],
  },
  {
    group: "Price Comparison",
    sources: [
      { name: "Toppreise.ch", purpose: "CH price comparison engine — retail reference", categories: "electronics / household" },
    ],
  },
  {
    group: "Retail Reference Prices",
    sources: [
      { name: "Digitec", purpose: "Electronics retail reference price", categories: "electronics" },
      { name: "Galaxus", purpose: "Broad retail — electronics, sport, household", categories: "electronics / household / sport" },
      { name: "Brack.ch", purpose: "Electronics and office retail", categories: "electronics" },
      { name: "Microspot / Interdiscount", purpose: "Electronics retail reference", categories: "electronics" },
      { name: "Fust", purpose: "Appliances and electronics retail", categories: "electronics / appliances" },
      { name: "MediaMarkt Schweiz", purpose: "Consumer electronics retail", categories: "electronics" },
      { name: "IKEA Schweiz", purpose: "Furniture retail reference price", categories: "furniture" },
      { name: "Decathlon Schweiz", purpose: "Sport equipment retail reference", categories: "sport" },
      { name: "Ochsner Sport", purpose: "Sport and outdoor retail reference", categories: "sport" },
      { name: "Jumbo / Coop Bau+Hobby", purpose: "Tools and garden retail reference", categories: "tools / garden" },
      { name: "Hornbach Schweiz", purpose: "Building materials and tools retail", categories: "tools / construction" },
    ],
  },
  {
    group: "Second-Hand Comparables",
    sources: [
      { name: "Tutti.ch", purpose: "Search active listings for comparable items", categories: "general" },
      { name: "Ricardo.ch", purpose: "Check sold and active auction prices", categories: "general" },
      { name: "Anibis.ch", purpose: "CH classifieds price reference", categories: "furniture / general" },
      { name: "Facebook Marketplace", purpose: "Local resale price benchmarks", categories: "general" },
    ],
  },
];

function PriceSourceDirectory() {
  return (
    <div className="glass-panel rounded-lg p-6 mb-10">
      <div className="flex items-start justify-between mb-4">
        <div>
          <h2 className="text-base font-bold text-gray-100">Price Source Directory</h2>
          <p className="text-xs font-mono text-gray-600 mt-0.5">Manual reference only — no scraping or API calls</p>
        </div>
        <span className="px-2 py-0.5 rounded text-xs font-mono font-bold border border-current text-cyan-400">MANUAL</span>
      </div>
      <div className="space-y-6">
        {priceSourceGroups.map((grp) => (
          <div key={grp.group}>
            <div className="flex items-center gap-3 mb-3">
              <span className="text-xs font-mono font-bold text-gray-500 tracking-widest uppercase">{grp.group}</span>
              <div className="flex-1 h-px bg-gray-800"></div>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
              {grp.sources.map((src, i) => (
                <div key={src.name + i} className="flex items-start gap-3 bg-gray-900 rounded border border-gray-800 px-3 py-2">
                  <div className="flex-1 min-w-0">
                    <span className="text-sm font-mono font-bold text-gray-200">{src.name}</span>
                    <p className="text-xs font-mono text-gray-500 mt-0.5 leading-snug">{src.purpose}</p>
                  </div>
                  <span className="text-xs font-mono text-gray-600 shrink-0 mt-0.5">{src.categories}</span>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
      <p className="mt-4 text-xs font-mono text-gray-600">Manual reference list only — no scraping or API calls from this section.</p>
    </div>
  );
}

function SalesIntakePipeline() {
  const stages = [
    {
      label: "Photo Received",
      what: "Dani sends item photo via Telegram",
      actor: "Dani",
      actorColor: "text-cyan-400",
      automation: "Manual now",
      autoColor: "text-amber-400",
      icon: "📷",
    },
    {
      label: "Needs Info",
      what: "Bot asks minimal follow-up questions: condition, brand, target price, pickup location",
      actor: "SwissEdge",
      actorColor: "text-violet-400",
      automation: "Planned",
      autoColor: "text-gray-500",
      icon: "❓",
    },
    {
      label: "Draft Ready",
      what: "AI generates Hochdeutsch listing draft and price range estimate",
      actor: "SwissEdge",
      actorColor: "text-violet-400",
      automation: "Active (web form)",
      autoColor: "text-green-400",
      icon: "📝",
    },
    {
      label: "Ready to Publish",
      what: "Dani reviews draft, title, price and confirms before any publish action",
      actor: "Dani",
      actorColor: "text-cyan-400",
      automation: "Manual now",
      autoColor: "text-amber-400",
      icon: "✅",
    },
    {
      label: "Published Manually",
      what: "Dani copies draft to Tutti.ch / Ricardo manually. Direct API publish in Phase 2.",
      actor: "Dani",
      actorColor: "text-cyan-400",
      automation: "Manual now / Phase 2",
      autoColor: "text-amber-400",
      icon: "🚀",
    },
    {
      label: "Buyer Question",
      what: "Incoming buyer questions are routed to Dani with AI-suggested reply options",
      actor: "Dani + SwissEdge",
      actorColor: "text-cyan-400",
      automation: "Planned",
      autoColor: "text-gray-500",
      icon: "💬",
    },
    {
      label: "Sold",
      what: "Item marked sold. Dani confirms. SwissEdge archives listing and logs completion.",
      actor: "Dani",
      actorColor: "text-cyan-400",
      automation: "Planned",
      autoColor: "text-gray-500",
      icon: "🏷️",
    },
    {
      label: "Archived",
      what: "Unsold or expired listings archived. Notes saved for future reference.",
      actor: "SwissEdge",
      actorColor: "text-violet-400",
      automation: "Planned",
      autoColor: "text-gray-500",
      icon: "📦",
    },
  ];

  return (
    <div className="glass-panel rounded-lg p-6 mb-10">
      <div className="flex items-start justify-between mb-5">
        <div>
          <h2 className="text-base font-bold text-gray-100">Sales Intake Pipeline</h2>
          <p className="text-xs font-mono text-gray-600 mt-0.5">Design reference — no automation active yet</p>
        </div>
        <span className="px-2 py-0.5 rounded text-xs font-mono font-bold border border-current text-gray-500">DESIGN</span>
      </div>

      <div className="space-y-2 mb-8">
        {stages.map((stage, i) => (
          <div key={stage.label} className="flex items-start gap-3 bg-gray-900 rounded border border-gray-800 px-4 py-3">
            <div className="flex items-center gap-2 w-6 shrink-0 mt-0.5">
              <span className="text-xs font-mono text-gray-600">{i + 1}</span>
            </div>
            <span className="text-lg shrink-0">{stage.icon}</span>
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 flex-wrap mb-0.5">
                <span className="text-sm font-mono font-bold text-gray-200">{stage.label}</span>
                <span className={"text-xs font-mono " + stage.actorColor}>{stage.actor}</span>
              </div>
              <p className="text-xs font-mono text-gray-500 leading-snug">{stage.what}</p>
            </div>
            <span className={"text-xs font-mono shrink-0 mt-0.5 " + stage.autoColor}>{stage.automation}</span>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">

        <div className="rounded border border-violet-500/20 bg-violet-500/5 p-4">
          <span className="text-xs font-mono font-bold text-violet-400 tracking-widest uppercase">Future Telegram Flow</span>
          <ul className="mt-3 space-y-2">
            {[
              "Send product photo to SwissEdge bot",
              "Bot asks missing details (condition, price, location)",
              "Bot prepares platform-specific listing drafts",
              "Dani approves draft before any publish action",
              "Buyer questions routed to Dani with suggested replies",
              "Alerts: draft ready, publish pending, buyer question, sold",
            ].map((step, i) => (
              <li key={i} className="flex items-start gap-2 text-xs font-mono text-gray-400">
                <span className="text-violet-600 shrink-0 mt-0.5">{i + 1}.</span>
                <span>{step}</span>
              </li>
            ))}
          </ul>
        </div>

        <div className="rounded border border-red-500/20 bg-red-500/5 p-4">
          <span className="text-xs font-mono font-bold text-red-400 tracking-widest uppercase">Guardrails</span>
          <ul className="mt-3 space-y-2">
            {[
              ["No auto-publish — human confirmation required for every listing", "text-red-400"],
              ["Human confirmation required before any publish action", "text-red-400"],
              ["AI images must not misrepresent item condition", "text-amber-400"],
              ["Buyer replies require Dani approval at first", "text-amber-400"],
              ["PII guard active on all outgoing Telegram messages", "text-green-400"],
              ["No meeting or pickup arranged without Dani confirmation", "text-amber-400"],
            ].map(([rule, color], i) => (
              <li key={i} className="flex items-start gap-2 text-xs font-mono">
                <span className={"shrink-0 mt-0.5 " + color}>!</span>
                <span className="text-gray-400">{rule}</span>
              </li>
            ))}
          </ul>
        </div>

      </div>
    </div>
  );
}
export default function MarketplacePage() {
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
            <h1 className="text-4xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-amber-400 via-cyan-400 to-amber-400 mb-2">MARKETPLACE SALES ASSISTANT</h1>
            <p className="text-gray-500 text-xs font-mono tracking-wider">DRAFT-ONLY WORKFLOW // NO AUTO-PUBLISHING</p>
          </div>
          <div className="glass-panel rounded-lg p-3 mb-10 border-red-500/20">
            <div className="flex flex-wrap gap-6 text-xs font-mono justify-center">
              <div className="flex items-center gap-2"><span className="text-gray-500">AUTO-PUBLISH:</span><span className="text-red-400 font-bold">DISABLED</span></div>
              <div className="flex items-center gap-2"><span className="text-gray-500">HUMAN APPROVAL:</span><span className="text-green-400">REQUIRED</span></div>
              <div className="flex items-center gap-2"><span className="text-gray-500">PII SAFETY GUARD:</span><span className="text-green-400">ACTIVE</span></div>
              <div className="flex items-center gap-2"><span className="text-gray-500">PUBLISH API:</span><span className="text-amber-400">PHASE 2</span></div>
            </div>
          </div>
          <div className="glass-panel rounded-lg p-4 mb-8 border-cyan-500/20">
            <div className="flex items-center justify-between">
              <div>
                <span className="text-xs font-mono font-bold text-gray-500 tracking-widest uppercase">Persisted Items</span>
                <p className="text-xs font-mono text-gray-600 mt-0.5">Items created via Telegram or API, tracked across platforms</p>
              </div>
              <Link
                href="/marketplace/sales/items"
                className="px-4 py-1.5 rounded text-sm font-mono font-bold bg-cyan-500/10 border border-cyan-500/40 text-cyan-400 hover:bg-cyan-500/20 hover:border-cyan-400 transition-all whitespace-nowrap"
              >
                Items for Sale →
              </Link>
            </div>
          </div>
          <SectionLabel label="Sales Intake Pipeline" />
          <SalesIntakePipeline />
          <SectionLabel label="Listing Generator" />
          <ListingGeneratorForm />
          <SectionLabel label="Price Source Directory" />
          <PriceSourceDirectory />
          <SectionLabel label="Capabilities" />
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-10">
            {capabilities.map((cap) => (
              <div key={cap.title} className="glass-panel rounded-lg p-5">
                <div className="flex items-start justify-between mb-3">
                  <h2 className="text-base font-bold text-gray-100">{cap.title}</h2>
                  <StatusBadge status={cap.status} colorClass={cap.statusColor} />
                </div>
                {cap.endpoint && <div className="mb-3"><span className="text-xs font-mono text-gray-600 bg-gray-900 px-2 py-0.5 rounded">{cap.endpoint}</span></div>}
                <ul className="space-y-1">
                  {cap.notes.map((note, i) => (
                    <li key={i} className="text-xs text-gray-400 font-mono flex items-start gap-2">
                      <span className="text-gray-600 mt-0.5">-</span><span>{note}</span>
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
          <SectionLabel label="Current Workflow" />
          <div className="glass-panel rounded-lg p-5 mb-10">
            <ol className="space-y-3">
              {[
                "Fill in item details in the Listing Generator form above",
                "AI generates Hochdeutsch listing draft (generate-listing endpoint)",
                "Review draft title and description carefully",
                "Copy listing text into Tutti.ch manually (direct publish: Phase 2)",
                "Price Assistant and Comparable Search available via Telegram or future sprint",
              ].map((step, i) => (
                <li key={i} className="flex items-start gap-3 text-xs font-mono text-gray-400">
                  <span className="text-cyan-600 font-bold w-4 shrink-0">{i + 1}.</span><span>{step}</span>
                </li>
              ))}
            </ol>
          </div>
          <div className="glass-panel rounded-lg p-4 border-amber-500/20">
            <div className="flex items-center justify-between text-xs font-mono">
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 bg-amber-400 rounded-full"></div>
                <span className="text-gray-400">MARKETPLACE STATUS:</span>
                <span className="text-amber-400">DRAFT-ONLY</span>
              </div>
              <div className="text-gray-600">ADAPTER: TUTTI.CH // PUBLISH: MANUAL // SCRAPER: PARTIAL</div>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}