'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { fetchSituations, updateSituationStatus, type Situation } from '@/lib/api';
import { PageHeader, StatusBadge, EmptyState, LoadingState, ErrorBanner } from '@/app/components/ui';

function fv(value: unknown): string {
  if (value === null || value === undefined) return '—';
  if (typeof value === 'number') return value.toString();
  return String(value);
}

function recBadge(rec: string | null | undefined): string {
  switch (rec) {
    case 'DEEP_RESEARCH':         return 'status-badge--manual';
    case 'HUMAN_REVIEW_REQUIRED': return 'status-badge--preview';
    case 'WATCHLIST':             return 'status-badge--partial';
    case 'PASS':                  return 'status-badge--readonly';
    default:                      return 'status-badge--readonly';
  }
}

export default function WatchlistPage() {
  const [situations, setSituations] = useState<Situation[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function load() {
    try {
      setLoading(true);
      setError(null);
      const data = await fetchSituations({ include_archived: false });
      setSituations(data.situations.filter(s => s.status === 'watchlist'));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load watchlist');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { load(); }, []);

  const handleStatusChange = async (id: string, status: string, companyName: string) => {
    try {
      await updateSituationStatus(id, status);
      load();
    } catch (err) {
      alert(`Failed to update status for "${companyName}": ${err instanceof Error ? err.message : 'Unknown error'}`);
    }
  };

  return (
    <div className="page-container--wide">

      <PageHeader
        title="Watchlist"
        subtitle="Situations under active monitoring. Legacy surface: day-to-day triage now lives in the Research Inbox."
        backHref="/investment/research-inbox"
        backLabel="Research Inbox"
        actions={
          <div style={{ display: 'flex', gap: '8px' }}>
            <Link href="/investment/research-inbox" className="btn btn--secondary btn--sm">Research Inbox</Link>
            <Link href="/investment/research" className="btn btn--secondary btn--sm">Research Cases</Link>
          </div>
        }
      />

      {loading && <LoadingState label="Loading watchlist…" />}
      {error && <ErrorBanner message={error} />}

      {!loading && !error && situations.length === 0 && (
        <EmptyState
          icon="👁"
          title="No situations on watchlist"
          description="Move situations to watchlist from the Kanban or the case workbench."
        />
      )}

      {!loading && !error && situations.length > 0 && (
        <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
          <div style={{ overflowX: 'auto' }}>
            <table className="data-table">
              <thead>
                <tr>
                  <th>Company</th>
                  <th>Ticker</th>
                  <th>Filing</th>
                  <th>Playbook</th>
                  <th>Recommendation</th>
                  <th>Confidence</th>
                  <th>Detected</th>
                  <th style={{ textAlign: 'center' }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {situations.map(s => (
                  <tr key={s.id}>
                    <td>
                      <Link
                        href={`/investment/situations/${s.id}`}
                        style={{ color: 'var(--text-primary)', fontWeight: 500, textDecoration: 'none', display: 'block', maxWidth: 200, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}
                        title={s.company_name}
                      >
                        {s.company_name}
                      </Link>
                    </td>
                    <td style={{ color: 'var(--text-muted)' }}>{fv(s.ticker)}</td>
                    <td style={{ color: 'var(--text-muted)' }}>{fv(s.filing_type)}</td>
                    <td style={{ color: 'var(--text-muted)', maxWidth: 140, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{fv(s.selected_playbook)}</td>
                    <td>
                      <span className={`status-badge ${recBadge(s.recommendation)}`}>
                        {fv(s.recommendation)}
                      </span>
                    </td>
                    <td style={{ color: 'var(--text-muted)' }}>{fv(s.evaluator_confidence)}</td>
                    <td style={{ color: 'var(--text-muted)' }}>
                      {s.detected_at ? new Date(s.detected_at).toLocaleDateString('en-CH', { day: '2-digit', month: 'short', year: '2-digit' }) : '—'}
                    </td>
                    <td>
                      <div style={{ display: 'flex', gap: '4px', justifyContent: 'center' }}>
                        <button
                          onClick={() => handleStatusChange(s.id, 'reviewing', s.company_name)}
                          className="btn btn--secondary btn--sm"
                          title="Move to reviewing"
                        >Review</button>
                        <button
                          onClick={() => handleStatusChange(s.id, 'ignored', s.company_name)}
                          className="btn btn--ghost btn--sm"
                          title="Ignore this situation"
                        >Ignore</button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div style={{ padding: '10px 16px', borderTop: '1px solid var(--border-subtle)', fontFamily: 'var(--font-mono)', fontSize: '11px', color: 'var(--text-faint)' }}>
            {situations.length} situation{situations.length !== 1 ? 's' : ''} on watchlist
          </div>
        </div>
      )}

    </div>
  );
}