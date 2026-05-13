'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { fetchSituations, archiveSituation, updateSituationStatus, type Situation } from '@/lib/api';
import { PageHeader, StatusBadge, EmptyState, LoadingState, ErrorBanner, InfoBanner, MetricRow } from '@/app/components/ui';

function inferSource(s: Situation): string {
  if (s.filing_url?.includes('sec.gov')) return 'SEC EDGAR';
  if (s.filing_type) return 'SEC Filing';
  return 'Unknown';
}

function fv(value: unknown): string {
  if (value === null || value === undefined) return '—';
  if (typeof value === 'number') return value.toString();
  return String(value);
}

function playbookStatusBadge(status: string | null | undefined): string {
  switch (status) {
    case 'evaluator_ready': return 'status-badge--active';
    case 'partial':         return 'status-badge--preview';
    case 'detection_only':  return 'status-badge--readonly';
    default:                return 'status-badge--readonly';
  }
}

function workflowBadge(status: string | null | undefined): string {
  switch (status) {
    case 'detected':   return 'status-badge--readonly';
    case 'reviewing':  return 'status-badge--partial';
    case 'watchlist':  return 'status-badge--active';
    case 'ignored':    return 'status-badge--readonly';
    case 'archived':   return 'status-badge--readonly';
    default:           return 'status-badge--readonly';
  }
}

function recBadge(rec: string | null | undefined): string {
  switch (rec) {
    case 'DEEP_RESEARCH':          return 'status-badge--manual';
    case 'HUMAN_REVIEW_REQUIRED':  return 'status-badge--preview';
    case 'WATCHLIST':              return 'status-badge--partial';
    case 'PASS':                   return 'status-badge--readonly';
    default:                       return 'status-badge--readonly';
  }
}

export default function EvaluationsPage() {
  const [situations, setSituations] = useState<Situation[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [quickStatusFilter, setQuickStatusFilter] = useState<string>('');
  const [filters, setFilters] = useState({
    evaluator_version: '',
    playbook_status: '',
    recommendation: '',
  });

  const handleStatusChange = async (id: string, status: string, companyName: string) => {
    try {
      await updateSituationStatus(id, status);
      loadSituations();
    } catch (err) {
      alert(`Failed to update status for "${companyName}": ${err instanceof Error ? err.message : 'Unknown error'}`);
    }
  };

  const handleArchive = async (id: string, companyName: string) => {
    if (!confirm(`Archive "${companyName}"? This will hide it from the main list.`)) return;
    try {
      await archiveSituation(id);
      loadSituations();
    } catch (err) {
      alert(`Failed to archive: ${err instanceof Error ? err.message : 'Unknown error'}`);
    }
  };

  async function loadSituations() {
    try {
      setLoading(true);
      setError(null);
      const data = await fetchSituations({
        evaluator_version: filters.evaluator_version || undefined,
        playbook_status: filters.playbook_status || undefined,
        recommendation: filters.recommendation || undefined,
        include_archived: true,
      });
      setSituations(data.situations);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load evaluations');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { loadSituations(); }, [filters]);

  const visibleSituations = quickStatusFilter
    ? situations.filter(s => s.status === quickStatusFilter)
    : situations;

  const statusCounts = {
    all:       situations.length,
    detected:  situations.filter(s => s.status === 'detected').length,
    reviewing: situations.filter(s => s.status === 'reviewing').length,
    watchlist: situations.filter(s => s.status === 'watchlist').length,
    ignored:   situations.filter(s => s.status === 'ignored').length,
    archived:  situations.filter(s => s.status === 'archived').length,
  };

  const prohibitedCount = visibleSituations.reduce(
    (sum, s) => sum + (s.prohibited_inferences_count || 0), 0
  );
  const hrCount = visibleSituations.filter(s => (s.human_review_required_count || 0) > 0).length;

  return (
    <div className="page-container--wide">

      <PageHeader
        title="Evaluations Queue"
        subtitle="SEC EDGAR special situations — review, triage, and watchlist management"
        backHref="/"
        backLabel="Mission Control"
        actions={
          <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
            <Link href="/investment/research" className="btn btn--secondary btn--sm">Research Cases</Link>
            <Link href="/investment/watchlist" className="btn btn--secondary btn--sm">Watchlist</Link>
            <Link href="/investment/radar-status" className="btn btn--secondary btn--sm">Radar Status</Link>
          </div>
        }
      />

      <InfoBanner variant="info">
        Evaluations Queue is the older review queue for evaluator outputs and manually reviewed situations.
        Special Situations Kanban is the active SEC-detection workflow: SEC EDGAR detection -&gt; SpecialSituation -&gt; evidence mapping -&gt; manual promotion -&gt; ResearchCase.
        Detection does not mean evaluated, and ResearchCases are not created automatically from this queue.
      </InfoBanner>

      {/* Summary strip */}
      {!loading && !error && situations.length > 0 && (
        <div className="card" style={{ marginBottom: '24px' }}>
          <MetricRow items={[
            { label: 'Total', value: statusCounts.all },
            { label: 'Detected', value: statusCounts.detected },
            { label: 'Reviewing', value: statusCounts.reviewing },
            { label: 'Watchlist', value: statusCounts.watchlist },
            { label: 'Ignored', value: statusCounts.ignored },
            { label: 'HR Required', value: hrCount },
            { label: 'Prohibited', value: prohibitedCount },
          ]} />
        </div>
      )}

      {/* Alert strip */}
      {!loading && !error && prohibitedCount > 0 && (
        <InfoBanner variant="warning">
          {prohibitedCount} prohibited inference{prohibitedCount !== 1 ? 's' : ''} detected across {visibleSituations.filter(s => (s.prohibited_inferences_count || 0) > 0).length} evaluation{visibleSituations.filter(s => (s.prohibited_inferences_count || 0) > 0).length !== 1 ? 's' : ''}. Manual review required before any action.
        </InfoBanner>
      )}
      {!loading && !error && prohibitedCount === 0 && hrCount > 0 && (
        <InfoBanner variant="info">
          {hrCount} evaluation{hrCount !== 1 ? 's' : ''} flagged for human review.
        </InfoBanner>
      )}

      {/* Quick status filters */}
      {!loading && !error && situations.length > 0 && (
        <div className="filter-group" style={{ marginBottom: '20px' }}>
          {([
            { key: '',          label: 'All',       count: statusCounts.all },
            { key: 'detected',  label: 'Detected',  count: statusCounts.detected },
            { key: 'reviewing', label: 'Reviewing', count: statusCounts.reviewing },
            { key: 'watchlist', label: 'Watchlist', count: statusCounts.watchlist },
            { key: 'ignored',   label: 'Ignored',   count: statusCounts.ignored },
            { key: 'archived',  label: 'Archived',  count: statusCounts.archived },
          ] as { key: string; label: string; count: number }[]).map(({ key, label, count }) => (
            <button
              key={key}
              onClick={() => setQuickStatusFilter(key)}
              className={`filter-btn ${quickStatusFilter === key ? 'filter-btn--active' : ''}`}
            >
              {label} <span style={{ marginLeft: 4, opacity: 0.6 }}>{count}</span>
            </button>
          ))}
        </div>
      )}

      {/* Filters */}
      <div className="card" style={{ marginBottom: '24px' }}>
        <div className="section-header" style={{ marginBottom: '14px' }}>
          <span className="section-title">Filters</span>
          <div className="section-line" />
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '12px' }}>
          {[
            {
              label: 'Evaluator Version', key: 'evaluator_version',
              options: [{ value: '', label: 'All versions' }, { value: 'v1', label: 'v1' }, { value: 'v2', label: 'v2' }],
            },
            {
              label: 'Playbook Status', key: 'playbook_status',
              options: [
                { value: '', label: 'All statuses' },
                { value: 'evaluator_ready', label: 'Evaluator ready' },
                { value: 'partial', label: 'Partial' },
                { value: 'detection_only', label: 'Detection only' },
              ],
            },
            {
              label: 'Recommendation', key: 'recommendation',
              options: [
                { value: '', label: 'All' },
                { value: 'DEEP_RESEARCH', label: 'Deep Research' },
                { value: 'HUMAN_REVIEW_REQUIRED', label: 'Human Review Required' },
                { value: 'WATCHLIST', label: 'Watchlist' },
                { value: 'PASS', label: 'Pass' },
              ],
            },
          ].map(({ label, key, options }) => (
            <div key={key}>
              <label style={{ display: 'block', fontFamily: 'var(--font-mono)', fontSize: '10px', fontWeight: 500, letterSpacing: '0.1em', textTransform: 'uppercase', color: 'var(--text-faint)', marginBottom: '6px' }}>
                {label}
              </label>
              <select
                value={filters[key as keyof typeof filters]}
                onChange={(e) => setFilters({ ...filters, [key]: e.target.value })}
                style={{ width: '100%', padding: '7px 10px', background: 'var(--bg-subtle)', border: '1px solid var(--border-default)', borderRadius: '7px', fontFamily: 'var(--font-mono)', fontSize: '12px', color: 'var(--text-secondary)', outline: 'none' }}
              >
                {options.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
              </select>
            </div>
          ))}
        </div>
      </div>

      {loading && <LoadingState label="Loading evaluations…" />}
      {error && <ErrorBanner message={error} />}

      {!loading && !error && visibleSituations.length === 0 && (
        <EmptyState
          icon="📋"
          title="No evaluations in queue"
          description={quickStatusFilter ? `No evaluations with status "${quickStatusFilter}".` : 'No special situations detected yet. Run SEC EDGAR detection manually to populate the queue.'}
        />
      )}

      {!loading && !error && visibleSituations.length > 0 && (
        <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
          <div style={{ overflowX: 'auto' }}>
            <table className="data-table">
              <thead>
                <tr>
                  <th>Company</th>
                  <th>Ticker</th>
                  <th>Filing</th>
                  <th>Source</th>
                  <th>Ver</th>
                  <th>Playbook</th>
                  <th>Playbook Status</th>
                  <th>Status</th>
                  <th>Recommendation</th>
                  <th>Conf</th>
                  <th style={{ textAlign: 'center' }}>HR</th>
                  <th style={{ textAlign: 'center' }}>Risk</th>
                  <th style={{ textAlign: 'center' }}>Proh</th>
                  <th style={{ textAlign: 'center' }}>Miss</th>
                  <th>Methodology</th>
                  <th style={{ textAlign: 'center' }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {visibleSituations.map((situation) => (
                  <tr key={situation.id}>
                    <td>
                      <Link
                        href={`/investment/evaluations/${situation.id}`}
                        style={{ color: 'var(--text-primary)', fontWeight: 500, textDecoration: 'none', display: 'block', maxWidth: 200, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}
                        title={situation.company_name}
                      >
                        {situation.company_name}
                      </Link>
                    </td>
                    <td style={{ color: 'var(--text-muted)' }}>{fv(situation.ticker)}</td>
                    <td style={{ color: 'var(--text-muted)' }}>{fv(situation.filing_type)}</td>
                    <td style={{ color: 'var(--text-faint)' }}>{inferSource(situation)}</td>
                    <td>
                      <span className={`status-badge ${situation.evaluator_version === 'v2' ? 'status-badge--partial' : 'status-badge--readonly'}`}>
                        {fv(situation.evaluator_version)}
                      </span>
                    </td>
                    <td style={{ color: 'var(--text-muted)', maxWidth: 140, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {fv(situation.selected_playbook)}
                    </td>
                    <td>
                      <span className={`status-badge ${playbookStatusBadge(situation.playbook_status)}`}>
                        {fv(situation.playbook_status)}
                      </span>
                    </td>
                    <td>
                      <span className={`status-badge ${workflowBadge(situation.status)}`}>
                        {fv(situation.status)}
                      </span>
                    </td>
                    <td>
                      <span className={`status-badge ${recBadge(situation.recommendation)}`}>
                        {fv(situation.recommendation)}
                      </span>
                    </td>
                    <td style={{ color: 'var(--text-muted)' }}>{fv(situation.evaluator_confidence)}</td>
                    <td style={{ textAlign: 'center', color: 'var(--text-muted)' }}>{fv(situation.human_review_required_count)}</td>
                    <td style={{ textAlign: 'center', color: 'var(--text-muted)' }}>{fv(situation.risk_flags_count)}</td>
                    <td style={{ textAlign: 'center' }}>
                      {(situation.prohibited_inferences_count ?? 0) > 0
                        ? <span style={{ color: '#8b2020', fontWeight: 600 }}>{situation.prohibited_inferences_count}</span>
                        : <span style={{ color: 'var(--text-faint)' }}>0</span>
                      }
                    </td>
                    <td style={{ textAlign: 'center', color: 'var(--text-muted)' }}>{fv(situation.missing_documents_count)}</td>
                    <td>
                      <Link href={`/investment/situations/${situation.id}`} className="btn btn--secondary btn--sm">
                        Workspace
                      </Link>
                    </td>
                    <td>
                      <div style={{ display: 'flex', gap: '4px', justifyContent: 'center' }}>
                        {situation.status !== 'reviewing' && situation.status !== 'archived' && (
                          <button
                            onClick={() => handleStatusChange(situation.id, 'reviewing', situation.company_name)}
                            className="btn btn--secondary btn--sm"
                            title="Mark as reviewing"
                          >Review</button>
                        )}
                        {situation.status !== 'watchlist' && situation.status !== 'archived' && (
                          <button
                            onClick={() => handleStatusChange(situation.id, 'watchlist', situation.company_name)}
                            className="btn btn--secondary btn--sm"
                            title="Add to watchlist"
                          >Watch</button>
                        )}
                        {situation.status !== 'ignored' && situation.status !== 'archived' && (
                          <button
                            onClick={() => handleStatusChange(situation.id, 'ignored', situation.company_name)}
                            className="btn btn--ghost btn--sm"
                            title="Ignore this evaluation"
                          >Ignore</button>
                        )}
                        {situation.status !== 'archived' && (
                          <button
                            onClick={() => handleArchive(situation.id, situation.company_name)}
                            className="btn btn--ghost btn--sm"
                            title="Archive this evaluation"
                          >Archive</button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div style={{ padding: '10px 16px', borderTop: '1px solid var(--border-subtle)', fontFamily: 'var(--font-mono)', fontSize: '11px', color: 'var(--text-faint)' }}>
            {visibleSituations.length} evaluation{visibleSituations.length !== 1 ? 's' : ''} — detected does not mean evaluated
          </div>
        </div>
      )}
    </div>
  );
}
