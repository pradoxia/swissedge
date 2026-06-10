'use client';

import { useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import {
  createCuratedIntake,
  fetchResearchInbox,
  recordResearchInboxDecision,
  updateResearchInboxPriceContext,
  type DecisionOutcome,
  type PriceContextStatus,
  type ResearchInboxItem,
  type ResearchInboxQueue,
} from '@/lib/api';
import { PageHeader, LoadingState, ErrorBanner, InfoBanner } from '@/app/components/ui';

type FilterKey = 'all' | 'candidate_only' | 'needs_evidence' | 'open_watchlist';
type DecisionForm = {
  outcome: DecisionOutcome;
  reason: string;
  author: string;
};
type PriceForm = {
  ticker: string;
  offer_price: string;
  offer_price_source: string;
  latest_close_price: string;
  latest_close_date: string;
  currency: string;
  spread_status: PriceContextStatus | '';
  status_reason: string;
};
type CuratedForm = {
  url: string;
  source_name: string;
  ticker: string;
  company_name: string;
  situation_type: string;
  title: string;
  summary: string;
  notes: string;
  source_published_at: string;
  submitted_by: string;
  source_tier: string;
  source_confidence: string;
};

const FILTERS: { key: FilterKey; label: string }[] = [
  { key: 'all', label: 'All' },
  { key: 'candidate_only', label: 'Candidate-only' },
  { key: 'needs_evidence', label: 'Needs evidence' },
  { key: 'open_watchlist', label: 'Watchlist / Open' },
];

const DECISION_LABELS: Record<DecisionOutcome, string> = {
  CANDIDATE: 'Candidate',
  WATCHLIST: 'Watchlist',
  REJECT: 'Reject',
  NEED_MORE_EVIDENCE: 'Need more evidence',
};

const DECISION_OPTIONS: DecisionOutcome[] = ['CANDIDATE', 'WATCHLIST', 'REJECT', 'NEED_MORE_EVIDENCE'];
const PRICE_STATUS_OPTIONS: Array<PriceContextStatus | ''> = [
  '',
  'not_applicable',
  'missing_offer_price',
  'missing_market_price',
  'stale_price',
];

function formatDate(value: string | null): string {
  if (!value) return 'unknown';
  try {
    return new Date(value).toLocaleString('en-CH', {
      year: '2-digit',
      month: 'short',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    });
  } catch {
    return value;
  }
}

function badgeClass(item: ResearchInboxItem): string {
  if (item.candidate_only) return 'border-amber-200 bg-amber-50 text-amber-800';
  if (item.entity_type === 'research_case') return 'border-blue-200 bg-blue-50 text-blue-700';
  return 'border-slate-200 bg-slate-50 text-slate-600';
}

function hasEvidenceNeed(item: ResearchInboxItem): boolean {
  return item.blocker_summary !== 'No blocker summary available.';
}

function spreadText(item: ResearchInboxItem): string {
  const context = item.price_context;
  if (!context) return 'unknown';
  if (context.spread_status !== 'available') return context.spread_status;
  return context.estimated_spread_pct ? `${context.estimated_spread_pct}%` : 'available';
}

function itemKey(item: ResearchInboxItem): string {
  return `${item.entity_type}-${item.id}`;
}

function priceFormFromItem(item: ResearchInboxItem): PriceForm {
  const context = item.price_context;
  return {
    ticker: context?.ticker ?? item.ticker ?? '',
    offer_price: context?.offer_price ?? '',
    offer_price_source: context?.offer_price_source ?? '',
    latest_close_price: context?.latest_close_price ?? '',
    latest_close_date: context?.latest_close_date ?? '',
    currency: '',
    spread_status: context?.spread_status === 'not_applicable' ? 'not_applicable' : '',
    status_reason: context?.status_reason ?? '',
  };
}

function matchesFilter(item: ResearchInboxItem, filter: FilterKey): boolean {
  if (filter === 'candidate_only') return item.candidate_only;
  if (filter === 'needs_evidence') return hasEvidenceNeed(item);
  if (filter === 'open_watchlist') {
    return ['watchlist', 'detected', 'reviewing', 'under_investigation', 'in_progress'].includes(item.status)
      || ['watchlist', 'in_progress'].includes(item.phase);
  }
  return true;
}

function InlineBadge({ children, className = '' }: { children: React.ReactNode; className?: string }) {
  return (
    <span className={`inline-flex items-center rounded-full border px-2 py-0.5 text-[11px] font-medium ${className}`}>
      {children}
    </span>
  );
}

export default function ResearchInboxPage() {
  const [queue, setQueue] = useState<ResearchInboxQueue | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<FilterKey>('all');
  const [decisionForms, setDecisionForms] = useState<Record<string, DecisionForm>>({});
  const [priceForms, setPriceForms] = useState<Record<string, PriceForm>>({});
  const [curatedForm, setCuratedForm] = useState<CuratedForm>({
    url: '',
    source_name: '',
    ticker: '',
    company_name: '',
    situation_type: '',
    title: '',
    summary: '',
    notes: '',
    source_published_at: '',
    submitted_by: 'Dani',
    source_tier: '',
    source_confidence: '',
  });
  const [savingDecision, setSavingDecision] = useState<string | null>(null);
  const [savingPrice, setSavingPrice] = useState<string | null>(null);
  const [savingCurated, setSavingCurated] = useState(false);
  const [decisionMessage, setDecisionMessage] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      try {
        setLoading(true);
        setError(null);
        setQueue(await fetchResearchInbox());
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load research inbox');
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  function formFor(item: ResearchInboxItem): DecisionForm {
    return decisionForms[itemKey(item)] ?? { outcome: 'CANDIDATE', reason: '', author: 'Dani' };
  }

  function priceFormFor(item: ResearchInboxItem): PriceForm {
    return priceForms[itemKey(item)] ?? priceFormFromItem(item);
  }

  function updateDecisionForm(item: ResearchInboxItem, patch: Partial<DecisionForm>) {
    const key = itemKey(item);
    setDecisionForms(current => ({
      ...current,
      [key]: { ...formFor(item), ...patch },
    }));
  }

  function updatePriceForm(item: ResearchInboxItem, patch: Partial<PriceForm>) {
    const key = itemKey(item);
    setPriceForms(current => ({
      ...current,
      [key]: { ...priceFormFor(item), ...patch },
    }));
  }

  async function submitDecision(item: ResearchInboxItem) {
    const key = itemKey(item);
    const form = formFor(item);
    try {
      setSavingDecision(key);
      setDecisionMessage(null);
      setError(null);
      await recordResearchInboxDecision({
        target_type: item.entity_type,
        target_id: item.id,
        outcome: form.outcome,
        reason: form.reason,
        author: form.author || 'Dani',
      });
      setDecisionForms(current => ({
        ...current,
        [key]: { outcome: 'CANDIDATE', reason: '', author: form.author || 'Dani' },
      }));
      setQueue(await fetchResearchInbox());
      setDecisionMessage('Manual decision recorded.');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to record decision');
    } finally {
      setSavingDecision(null);
    }
  }

  async function submitPriceContext(item: ResearchInboxItem) {
    const key = itemKey(item);
    const form = priceFormFor(item);
    try {
      setSavingPrice(key);
      setDecisionMessage(null);
      setError(null);
      await updateResearchInboxPriceContext({
        target_type: item.entity_type,
        target_id: item.id,
        ticker: form.ticker,
        offer_price: form.offer_price,
        offer_price_source: form.offer_price_source,
        latest_close_price: form.latest_close_price,
        latest_close_date: form.latest_close_date,
        currency: form.currency,
        spread_status: form.spread_status,
        status_reason: form.status_reason,
      });
      setQueue(await fetchResearchInbox());
      setPriceForms(current => {
        const next = { ...current };
        delete next[key];
        return next;
      });
      setDecisionMessage('Manual price context updated.');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update price context');
    } finally {
      setSavingPrice(null);
    }
  }

  function updateCuratedForm(patch: Partial<CuratedForm>) {
    setCuratedForm(current => ({ ...current, ...patch }));
  }

  async function submitCuratedIntake() {
    try {
      setSavingCurated(true);
      setDecisionMessage(null);
      setError(null);
      await createCuratedIntake(curatedForm);
      setQueue(await fetchResearchInbox());
      setCuratedForm({
        url: '',
        source_name: '',
        ticker: '',
        company_name: '',
        situation_type: '',
        title: '',
        summary: '',
        notes: '',
        source_published_at: '',
        submitted_by: curatedForm.submitted_by || 'Dani',
        source_tier: '',
        source_confidence: '',
      });
      setDecisionMessage('Curated source added as candidate-only manual intake.');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to add curated source');
    } finally {
      setSavingCurated(false);
    }
  }

  const items = queue?.items ?? [];
  const counts = useMemo(() => {
    const base: Record<FilterKey, number> = {
      all: items.length,
      candidate_only: 0,
      needs_evidence: 0,
      open_watchlist: 0,
    };
    for (const item of items) {
      if (matchesFilter(item, 'candidate_only')) base.candidate_only += 1;
      if (matchesFilter(item, 'needs_evidence')) base.needs_evidence += 1;
      if (matchesFilter(item, 'open_watchlist')) base.open_watchlist += 1;
    }
    return base;
  }, [items]);

  const filteredItems = items.filter(item => matchesFilter(item, filter));

  return (
    <div className="page-container--wide">
      <PageHeader
        title="Research Inbox"
        subtitle="Unified manual queue for detected situations and open ResearchCases."
        backHref="/investment/research"
        backLabel="Research Cases"
        actions={
          <div style={{ display: 'flex', gap: '8px' }}>
            <Link href="/investment/situations" className="btn btn--secondary btn--sm">Situations</Link>
            <Link href="/investment/watchlist" className="btn btn--secondary btn--sm">Watchlist</Link>
          </div>
        }
      />

      <InfoBanner variant="warning">
        Manual-only foundation: this page does not trigger scans, AI previews, promotion, rejection, discard, publication, or automated conclusions.
      </InfoBanner>
      {decisionMessage && <InfoBanner>{decisionMessage}</InfoBanner>}

      <div className="card" style={{ marginBottom: '20px' }}>
        <h2 style={{ fontSize: '14px', marginBottom: '10px' }}>Add curated source</h2>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: 8, marginBottom: 10 }}>
          <input
            value={curatedForm.url}
            onChange={event => updateCuratedForm({ url: event.target.value })}
            placeholder="URL"
            style={{ width: '100%' }}
          />
          <input
            value={curatedForm.source_name}
            onChange={event => updateCuratedForm({ source_name: event.target.value })}
            placeholder="Source name"
            style={{ width: '100%' }}
          />
          <input
            value={curatedForm.ticker}
            onChange={event => updateCuratedForm({ ticker: event.target.value })}
            placeholder="Ticker"
            style={{ width: '100%' }}
          />
          <input
            value={curatedForm.company_name}
            onChange={event => updateCuratedForm({ company_name: event.target.value })}
            placeholder="Company name"
            style={{ width: '100%' }}
          />
          <input
            value={curatedForm.situation_type}
            onChange={event => updateCuratedForm({ situation_type: event.target.value })}
            placeholder="Situation type"
            style={{ width: '100%' }}
          />
          <input
            value={curatedForm.title}
            onChange={event => updateCuratedForm({ title: event.target.value })}
            placeholder="Title"
            style={{ width: '100%' }}
          />
          <input
            value={curatedForm.source_published_at}
            onChange={event => updateCuratedForm({ source_published_at: event.target.value })}
            placeholder="Source date"
            type="date"
            style={{ width: '100%' }}
          />
          <input
            value={curatedForm.submitted_by}
            onChange={event => updateCuratedForm({ submitted_by: event.target.value })}
            placeholder="Submitted by"
            style={{ width: '100%' }}
          />
          <input
            value={curatedForm.source_tier}
            onChange={event => updateCuratedForm({ source_tier: event.target.value })}
            placeholder="Source tier"
            style={{ width: '100%' }}
          />
          <input
            value={curatedForm.source_confidence}
            onChange={event => updateCuratedForm({ source_confidence: event.target.value })}
            placeholder="Source confidence"
            style={{ width: '100%' }}
          />
        </div>
        <div style={{ display: 'grid', gap: 8, marginBottom: 10 }}>
          <textarea
            value={curatedForm.summary}
            onChange={event => updateCuratedForm({ summary: event.target.value })}
            placeholder="Summary"
            rows={2}
            style={{ width: '100%', resize: 'vertical' }}
          />
          <textarea
            value={curatedForm.notes}
            onChange={event => updateCuratedForm({ notes: event.target.value })}
            placeholder="Notes"
            rows={2}
            style={{ width: '100%', resize: 'vertical' }}
          />
        </div>
        <button
          className="btn btn--secondary btn--sm"
          onClick={submitCuratedIntake}
          disabled={
            savingCurated
            || !curatedForm.url.trim()
            || !curatedForm.source_name.trim()
            || !curatedForm.situation_type.trim()
            || (!curatedForm.title.trim() && !curatedForm.summary.trim())
            || !curatedForm.submitted_by.trim()
          }
        >
          {savingCurated ? 'Adding...' : 'Add curated source'}
        </button>
        <div style={{ marginTop: 8, fontFamily: 'var(--font-mono)', fontSize: '11px', color: 'var(--text-faint)' }}>
          Manual intake creates candidate-only unverified source context. It does not fetch the URL or create a ResearchCase.
        </div>
      </div>

      <div className="card" style={{ marginBottom: '20px' }}>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
          {FILTERS.map(option => (
            <button
              key={option.key}
              onClick={() => setFilter(option.key)}
              className={`filter-btn ${filter === option.key ? 'filter-btn--active' : ''}`}
            >
              {option.label}
              <span style={{ marginLeft: 4, opacity: 0.6 }}>{counts[option.key]}</span>
            </button>
          ))}
        </div>
      </div>

      {loading && <LoadingState label="Loading research inbox..." />}
      {error && <ErrorBanner message={error} />}

      {!loading && !error && filteredItems.length === 0 && (
        <div className="empty-state">
          <div className="empty-state-title">No inbox items match this filter</div>
          <div className="empty-state-desc">The unified queue will show detected situations and open ResearchCases when present.</div>
        </div>
      )}

      {!loading && !error && filteredItems.length > 0 && (
        <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
          <div style={{ overflowX: 'auto' }}>
            <table className="data-table">
              <thead>
                <tr>
                  <th>Item</th>
                  <th>Type</th>
                  <th>Source / Form</th>
                  <th>Status / Phase</th>
                  <th>Evidence / Blocker</th>
                  <th>Estimated spread %</th>
                  <th>Latest decision</th>
                  <th>Created / Detected</th>
                  <th>Next Action</th>
                  <th>Record decision</th>
                </tr>
              </thead>
              <tbody>
                {filteredItems.map(item => {
                  const form = formFor(item);
                  const key = itemKey(item);
                  return (
                  <tr key={key}>
                    <td>
                      <Link href={item.detail_href} style={{ color: 'var(--text-primary)', fontWeight: 600, textDecoration: 'none' }}>
                        {item.title}
                      </Link>
                      <div style={{ fontFamily: 'var(--font-mono)', fontSize: '11px', color: 'var(--text-faint)', marginTop: 3 }}>
                        {item.ticker ?? 'ticker unknown'} · {item.id.slice(0, 8).toUpperCase()}
                      </div>
                    </td>
                    <td>
                      <InlineBadge className={badgeClass(item)}>
                        {item.candidate_only ? 'candidate-only' : item.entity_type}
                      </InlineBadge>
                    </td>
                    <td style={{ color: 'var(--text-muted)' }}>{item.source_context || 'unknown'}</td>
                    <td>
                      <div style={{ color: 'var(--text-muted)' }}>{item.status || 'unknown'}</div>
                      <div style={{ fontFamily: 'var(--font-mono)', fontSize: '11px', color: 'var(--text-faint)' }}>{item.phase || 'unknown'}</div>
                    </td>
                    <td style={{ maxWidth: 300, color: hasEvidenceNeed(item) ? 'var(--text-primary)' : 'var(--text-faint)' }}>
                      {item.blocker_summary}
                    </td>
                    <td>
                      <div style={{ fontFamily: 'var(--font-mono)', fontSize: '12px', color: 'var(--text-muted)' }}>
                        {spreadText(item)}
                      </div>
                      <div style={{ fontFamily: 'var(--font-mono)', fontSize: '10px', color: 'var(--text-faint)', marginTop: 2 }}>
                        {item.price_context?.latest_close_date ? `close ${item.price_context.latest_close_date}` : 'price context unknown'}
                      </div>
                      <div style={{ display: 'grid', gap: 5, marginTop: 8, minWidth: 230 }}>
                        <input
                          value={priceFormFor(item).ticker}
                          onChange={event => updatePriceForm(item, { ticker: event.target.value })}
                          placeholder="Ticker"
                          style={{ width: '100%' }}
                        />
                        <input
                          value={priceFormFor(item).offer_price}
                          onChange={event => updatePriceForm(item, { offer_price: event.target.value })}
                          placeholder="Offer price"
                          style={{ width: '100%' }}
                        />
                        <input
                          value={priceFormFor(item).offer_price_source}
                          onChange={event => updatePriceForm(item, { offer_price_source: event.target.value })}
                          placeholder="Offer price source"
                          style={{ width: '100%' }}
                        />
                        <input
                          value={priceFormFor(item).latest_close_price}
                          onChange={event => updatePriceForm(item, { latest_close_price: event.target.value })}
                          placeholder="Latest close price"
                          style={{ width: '100%' }}
                        />
                        <input
                          value={priceFormFor(item).latest_close_date}
                          onChange={event => updatePriceForm(item, { latest_close_date: event.target.value })}
                          placeholder="Latest close date"
                          type="date"
                          style={{ width: '100%' }}
                        />
                        <input
                          value={priceFormFor(item).currency}
                          onChange={event => updatePriceForm(item, { currency: event.target.value })}
                          placeholder="Currency"
                          style={{ width: '100%' }}
                        />
                        <select
                          value={priceFormFor(item).spread_status}
                          onChange={event => updatePriceForm(item, { spread_status: event.target.value as PriceContextStatus | '' })}
                          style={{ width: '100%' }}
                        >
                          <option value="">Auto status</option>
                          {PRICE_STATUS_OPTIONS.filter(Boolean).map(status => (
                            <option key={status} value={status}>{status}</option>
                          ))}
                        </select>
                        <textarea
                          value={priceFormFor(item).status_reason}
                          onChange={event => updatePriceForm(item, { status_reason: event.target.value })}
                          placeholder="Status reason"
                          rows={2}
                          style={{ width: '100%', resize: 'vertical' }}
                        />
                        <button
                          className="btn btn--secondary btn--sm"
                          onClick={() => submitPriceContext(item)}
                          disabled={savingPrice === key}
                        >
                          {savingPrice === key ? 'Updating...' : 'Update price context'}
                        </button>
                      </div>
                    </td>
                    <td style={{ maxWidth: 260 }}>
                      {item.latest_decision ? (
                        <>
                          <InlineBadge className="border-emerald-200 bg-emerald-50 text-emerald-700">
                            {DECISION_LABELS[item.latest_decision.outcome]}
                          </InlineBadge>
                          <div style={{ color: 'var(--text-muted)', fontSize: '12px', marginTop: 6 }}>
                            {item.latest_decision.reason}
                          </div>
                          <div style={{ fontFamily: 'var(--font-mono)', fontSize: '10px', color: 'var(--text-faint)', marginTop: 4 }}>
                            {item.latest_decision.author} · {formatDate(item.latest_decision.created_at)}
                          </div>
                        </>
                      ) : (
                        <span style={{ color: 'var(--text-faint)' }}>No decision recorded</span>
                      )}
                    </td>
                    <td style={{ color: 'var(--text-faint)' }}>
                      <div>{formatDate(item.detected_at)}</div>
                      <div style={{ fontFamily: 'var(--font-mono)', fontSize: '10px' }}>created {formatDate(item.created_at)}</div>
                    </td>
                    <td>
                      <div style={{ marginBottom: 6, color: 'var(--text-muted)' }}>{item.next_action}</div>
                      <Link href={item.detail_href} className="btn btn--secondary btn--sm">Open</Link>
                    </td>
                    <td style={{ minWidth: 260 }}>
                      <div style={{ display: 'grid', gap: 6 }}>
                        <select
                          value={form.outcome}
                          onChange={event => updateDecisionForm(item, { outcome: event.target.value as DecisionOutcome })}
                          style={{ width: '100%' }}
                        >
                          {DECISION_OPTIONS.map(outcome => (
                            <option key={outcome} value={outcome}>{DECISION_LABELS[outcome]}</option>
                          ))}
                        </select>
                        <textarea
                          value={form.reason}
                          onChange={event => updateDecisionForm(item, { reason: event.target.value })}
                          placeholder="Reason"
                          rows={2}
                          style={{ width: '100%', resize: 'vertical' }}
                        />
                        <input
                          value={form.author}
                          onChange={event => updateDecisionForm(item, { author: event.target.value })}
                          placeholder="Author"
                          style={{ width: '100%' }}
                        />
                        <button
                          className="btn btn--secondary btn--sm"
                          onClick={() => submitDecision(item)}
                          disabled={savingDecision === key || !form.reason.trim() || !form.author.trim()}
                        >
                          {savingDecision === key ? 'Recording...' : 'Record decision'}
                        </button>
                      </div>
                    </td>
                  </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
          <div style={{ padding: '10px 16px', borderTop: '1px solid var(--border-subtle)', fontFamily: 'var(--font-mono)', fontSize: '11px', color: 'var(--text-faint)' }}>
            Showing {filteredItems.length} of {items.length} queue items. Decision records are manual audit context and do not change item status.
          </div>
        </div>
      )}

      {queue && queue.deferred_decisions.length > 0 && (
        <div className="card" style={{ marginTop: '20px' }}>
          <h2 style={{ fontSize: '14px', marginBottom: '10px' }}>Deferred decision work</h2>
          <ul style={{ margin: 0, paddingLeft: '18px', color: 'var(--text-muted)', fontSize: '13px' }}>
            {queue.deferred_decisions.map(item => <li key={item}>{item}</li>)}
          </ul>
        </div>
      )}
    </div>
  );
}
