'use client';

import { useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import {
  fetchResearchInbox,
  type ResearchInboxItem,
  type ResearchInboxQueue,
} from '@/lib/api';
import { PageHeader, LoadingState, ErrorBanner, InfoBanner } from '@/app/components/ui';

type FilterKey = 'all' | 'candidate_only' | 'needs_evidence' | 'open_watchlist';

const FILTERS: { key: FilterKey; label: string }[] = [
  { key: 'all', label: 'All' },
  { key: 'candidate_only', label: 'Candidate-only' },
  { key: 'needs_evidence', label: 'Needs evidence' },
  { key: 'open_watchlist', label: 'Watchlist / Open' },
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
        Manual-only foundation: this page does not trigger scans, AI previews, promotion, rejection, discard, publication, or recommendations.
      </InfoBanner>

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
                  <th>Created / Detected</th>
                  <th>Next Action</th>
                </tr>
              </thead>
              <tbody>
                {filteredItems.map(item => (
                  <tr key={`${item.entity_type}-${item.id}`}>
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
                    </td>
                    <td style={{ color: 'var(--text-faint)' }}>
                      <div>{formatDate(item.detected_at)}</div>
                      <div style={{ fontFamily: 'var(--font-mono)', fontSize: '10px' }}>created {formatDate(item.created_at)}</div>
                    </td>
                    <td>
                      <div style={{ marginBottom: 6, color: 'var(--text-muted)' }}>{item.next_action}</div>
                      <Link href={item.detail_href} className="btn btn--secondary btn--sm">Open</Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div style={{ padding: '10px 16px', borderTop: '1px solid var(--border-subtle)', fontFamily: 'var(--font-mono)', fontSize: '11px', color: 'var(--text-faint)' }}>
            Showing {filteredItems.length} of {items.length} queue items. Reject and reasoned deferral decisions remain deferred until M3B audit logging.
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
