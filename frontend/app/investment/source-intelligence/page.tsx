'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import {
  fetchSourceIntelligenceSuggestions,
  reviewSourceIntelligenceSuggestion,
  type SourceIntelligenceSuggestionRecord,
} from '@/lib/api';
import { PageHeader, StatusBadge, EmptyState, LoadingState, ErrorBanner, InfoBanner } from '@/app/components/ui';

const ACTION_LABELS: Record<string, string> = {
  add: 'Add source',
  update_priority: 'Update priority',
  deactivate: 'Deactivate',
};

const selectStyle: React.CSSProperties = {
  padding: '7px 10px',
  background: 'var(--bg-subtle)',
  border: '1px solid var(--border-default)',
  borderRadius: '7px',
  fontFamily: 'var(--font-mono)',
  fontSize: '12px',
  color: 'var(--text-secondary)',
  outline: 'none',
};

export default function SourceIntelligenceQueuePage() {
  const [suggestions, setSuggestions] = useState<SourceIntelligenceSuggestionRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filterStatus, setFilterStatus] = useState('');
  const [filterAction, setFilterAction] = useState('');
  const [reviewMsg, setReviewMsg] = useState<string | null>(null);

  async function load() {
    try {
      setLoading(true);
      setError(null);
      const data = await fetchSourceIntelligenceSuggestions({
        status: filterStatus || undefined,
        action: filterAction || undefined,
      });
      setSuggestions(data.suggestions);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load suggestions');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { load(); }, [filterStatus, filterAction]);

  async function handleReview(suggestionId: string, status: 'approved' | 'rejected') {
    setReviewMsg(null);
    try {
      await reviewSourceIntelligenceSuggestion(suggestionId, status);
      setReviewMsg(`Proposal ${status}.`);
      await load();
    } catch (err) {
      setReviewMsg(err instanceof Error ? err.message : 'Review failed');
    }
  }

  const proposed = suggestions.filter(s => s.status === 'proposed');
  const reviewed = suggestions.filter(s => s.status !== 'proposed');

  return (
    <div className="page-container">

      <PageHeader
        title="Source Intelligence Queue"
        subtitle="Manual approval queue — approved proposals are not applied automatically."
        backHref="/investment/research"
        backLabel="Research Cases"
        actions={
          <div style={{ display: 'flex', gap: '8px' }}>
            <Link href="/investment/historical-cases" className="btn btn--secondary btn--sm">Historical Cases</Link>
          </div>
        }
      />

      {/* Filters */}
      <div className="card" style={{ marginBottom: '24px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px', flexWrap: 'wrap' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <label style={{ fontFamily: 'var(--font-mono)', fontSize: '10px', color: 'var(--text-faint)', textTransform: 'uppercase', letterSpacing: '0.1em' }}>Status</label>
            <select value={filterStatus} onChange={e => setFilterStatus(e.target.value)} style={selectStyle}>
              <option value="">All</option>
              <option value="proposed">proposed</option>
              <option value="approved">approved</option>
              <option value="rejected">rejected</option>
            </select>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <label style={{ fontFamily: 'var(--font-mono)', fontSize: '10px', color: 'var(--text-faint)', textTransform: 'uppercase', letterSpacing: '0.1em' }}>Action</label>
            <select value={filterAction} onChange={e => setFilterAction(e.target.value)} style={selectStyle}>
              <option value="">All</option>
              <option value="add">add</option>
              <option value="update_priority">update_priority</option>
              <option value="deactivate">deactivate</option>
            </select>
          </div>
          {reviewMsg && (
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: '11px', color: 'var(--text-secondary)' }}>{reviewMsg}</span>
          )}
        </div>
      </div>

      {loading && <LoadingState label="Loading proposals…" />}
      {error && <ErrorBanner message={error} />}

      {!loading && !error && suggestions.length === 0 && (
        <EmptyState icon="📡" title="No proposals in queue" />
      )}

      {/* Pending */}
      {proposed.length > 0 && (
        <div style={{ marginBottom: '24px' }}>
          <div className="section-header" style={{ marginBottom: '12px' }}>
            <span className="section-title">Pending Review ({proposed.length})</span>
            <div className="section-line" />
          </div>
          <div style={{ display: 'grid', gap: '8px' }}>
            {proposed.map(p => (
              <div key={p.id} className="card">
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap', marginBottom: '6px' }}>
                  <span className="status-badge status-badge--readonly">
                    {ACTION_LABELS[p.action] ?? p.action}
                  </span>
                  <span style={{ fontFamily: 'var(--font-mono)', fontSize: '13px', color: 'var(--text-primary)', fontWeight: 500 }}>
                    {p.proposed_name || '—'}
                  </span>
                  {p.proposed_source_type && (
                    <span style={{ fontFamily: 'var(--font-mono)', fontSize: '11px', color: 'var(--text-faint)' }}>
                      {p.proposed_source_type}
                    </span>
                  )}
                  <StatusBadge value={p.status} />
                </div>
                {p.rationale && (
                  <p style={{ fontFamily: 'var(--font-sans)', fontSize: '12px', color: 'var(--text-secondary)', margin: '0 0 8px' }}>
                    {p.rationale}
                  </p>
                )}
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flexWrap: 'wrap' }}>
                  {p.research_case_id && (
                    <Link href={`/investment/research/${p.research_case_id}`} style={{ fontFamily: 'var(--font-mono)', fontSize: '11px', color: 'var(--text-secondary)', textDecoration: 'none' }}>
                      → Research Case
                    </Link>
                  )}
                  {p.historical_case_id && (
                    <Link href={`/investment/historical-cases/${p.historical_case_id}`} style={{ fontFamily: 'var(--font-mono)', fontSize: '11px', color: 'var(--text-secondary)', textDecoration: 'none' }}>
                      → Historical Case
                    </Link>
                  )}
                  <div style={{ display: 'flex', gap: '8px', marginLeft: 'auto' }}>
                    <button onClick={() => handleReview(p.id, 'approved')} className="btn btn--secondary btn--sm">
                      Approve
                    </button>
                    <button onClick={() => handleReview(p.id, 'rejected')} className="btn btn--ghost btn--sm">
                      Reject
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Reviewed */}
      {reviewed.length > 0 && (
        <div style={{ marginBottom: '24px' }}>
          <div className="section-header" style={{ marginBottom: '12px' }}>
            <span className="section-title">Reviewed ({reviewed.length})</span>
            <div className="section-line" />
          </div>
          <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
            <table className="data-table">
              <thead>
                <tr>
                  <th>Action</th>
                  <th>Name</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {reviewed.map(p => (
                  <tr key={p.id}>
                    <td style={{ color: 'var(--text-faint)' }}>{ACTION_LABELS[p.action] ?? p.action}</td>
                    <td style={{ color: p.status === 'rejected' ? 'var(--text-faint)' : 'var(--text-primary)', textDecoration: p.status === 'rejected' ? 'line-through' : 'none' }}>
                      {p.proposed_name || '—'}
                    </td>
                    <td><StatusBadge value={p.status} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      <InfoBanner variant="guardrail">
        Guardrail: approved proposals are not applied to investment_sources. Application to the global source registry requires a separate manual sprint.
      </InfoBanner>

    </div>
  );
}
