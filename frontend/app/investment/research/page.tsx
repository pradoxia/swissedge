'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import {
  fetchResearchCases,
  fetchSituations,
  createResearchCaseFromSituation,
  type ResearchCase,
  type Situation,
} from '@/lib/api';
import { PageHeader, StatusBadge, EmptyState, LoadingState, ErrorBanner, InfoBanner } from '@/app/components/ui';

const STATUSES = ['detected', 'brief_generated', 'under_investigation', 'documented', 'archived', 'published'];
const READINESS = ['monitor', 'not_actionable', 'needs_more_work', 'candidate'];

function safeStr(v: unknown): string {
  if (typeof v === 'string') return v;
  return '';
}

export default function ResearchListPage() {
  const [cases, setCases] = useState<ResearchCase[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState('');
  const [readinessFilter, setReadinessFilter] = useState('');

  const [situations, setSituations] = useState<Situation[]>([]);
  const [showCreate, setShowCreate] = useState(false);
  const [selectedSituationId, setSelectedSituationId] = useState('');
  const [createNotes, setCreateNotes] = useState('');
  const [createReadiness, setCreateReadiness] = useState('');
  const [creating, setCreating] = useState(false);
  const [createError, setCreateError] = useState<string | null>(null);

  async function loadCases() {
    try {
      setLoading(true);
      setError(null);
      const data = await fetchResearchCases({
        status: statusFilter || undefined,
        investment_readiness: readinessFilter || undefined,
      });
      setCases(data.research_cases);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load research cases');
    } finally {
      setLoading(false);
    }
  }

  async function loadSituations() {
    try {
      const data = await fetchSituations({ include_archived: false });
      setSituations(data.situations);
    } catch {
      // non-fatal
    }
  }

  useEffect(() => { loadCases(); }, [statusFilter, readinessFilter]);

  async function handleCreate() {
    if (!selectedSituationId) return;
    setCreating(true);
    setCreateError(null);
    try {
      await createResearchCaseFromSituation(selectedSituationId, {
        notes: createNotes || undefined,
        investment_readiness: createReadiness || undefined,
      });
      setShowCreate(false);
      setSelectedSituationId('');
      setCreateNotes('');
      setCreateReadiness('');
      loadCases();
    } catch (err) {
      setCreateError(err instanceof Error ? err.message : 'Failed to create research case');
    } finally {
      setCreating(false);
    }
  }

  const counts: Record<string, number> = { all: cases.length };
  for (const s of STATUSES) counts[s] = cases.filter(c => c.status === s).length;

  const selectStyle: React.CSSProperties = {
    width: '100%',
    padding: '7px 10px',
    background: 'var(--bg-subtle)',
    border: '1px solid var(--border-default)',
    borderRadius: '7px',
    fontFamily: 'var(--font-mono)',
    fontSize: '12px',
    color: 'var(--text-secondary)',
    outline: 'none',
  };

  const labelStyle: React.CSSProperties = {
    display: 'block',
    fontFamily: 'var(--font-mono)',
    fontSize: '10px',
    fontWeight: 500,
    letterSpacing: '0.1em',
    textTransform: 'uppercase',
    color: 'var(--text-faint)',
    marginBottom: '6px',
  };

  return (
    <div className="page-container">

      <PageHeader
        title="Research Cases"
        subtitle="Private research workspace for detected special situations."
        backHref="/investment/evaluations"
        backLabel="Evaluations Queue"
        actions={
          <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
            <Link href="/investment/research-inbox" className="btn btn--secondary btn--sm">Research Inbox</Link>
            <button
              onClick={() => { setShowCreate(v => !v); if (!situations.length) loadSituations(); }}
              className="btn btn--primary btn--sm"
            >
              + Create from evaluation
            </button>
          </div>
        }
      />

      <InfoBanner variant="guardrail">
        Research only — educational analysis. Not financial advice.
      </InfoBanner>

      {/* Create panel */}
      {showCreate && (
        <div className="card" style={{ marginBottom: '24px' }}>
          <div className="section-header" style={{ marginBottom: '14px' }}>
            <span className="section-title">Create Research Case from Situation</span>
            <div className="section-line" />
          </div>
          <div style={{ display: 'grid', gap: '12px' }}>
            <div>
              <label style={labelStyle}>Situation</label>
              <select value={selectedSituationId} onChange={e => setSelectedSituationId(e.target.value)} style={selectStyle}>
                <option value="">— select a situation —</option>
                {situations.map(s => (
                  <option key={s.id} value={s.id}>
                    {s.company_name} ({safeStr(s.filing_type) || safeStr(s.situation_type) || 'unknown'}) — {s.status}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label style={labelStyle}>Initial Readiness (optional)</label>
              <select value={createReadiness} onChange={e => setCreateReadiness(e.target.value)} style={selectStyle}>
                <option value="">— leave blank —</option>
                {READINESS.map(r => <option key={r} value={r}>{r}</option>)}
              </select>
            </div>
            <div>
              <label style={labelStyle}>Notes (optional)</label>
              <textarea
                value={createNotes}
                onChange={e => setCreateNotes(e.target.value)}
                rows={2}
                style={{ ...selectStyle, resize: 'vertical' }}
                placeholder="Initial observation…"
              />
            </div>
            {createError && <ErrorBanner message={createError} />}
            <div style={{ display: 'flex', gap: '8px' }}>
              <button
                onClick={handleCreate}
                disabled={creating || !selectedSituationId}
                className="btn btn--primary btn--sm"
              >
                {creating ? 'Creating…' : 'Create Case'}
              </button>
              <button onClick={() => setShowCreate(false)} className="btn btn--ghost btn--sm">
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Status filter tabs */}
      {!loading && !error && (
        <div className="filter-group" style={{ marginBottom: '20px' }}>
          <button
            onClick={() => setStatusFilter('')}
            className={`filter-btn ${statusFilter === '' ? 'filter-btn--active' : ''}`}
          >
            All <span style={{ marginLeft: 4, opacity: 0.6 }}>{counts.all}</span>
          </button>
          {STATUSES.map(s => counts[s] ? (
            <button
              key={s}
              onClick={() => setStatusFilter(s === statusFilter ? '' : s)}
              className={`filter-btn ${statusFilter === s ? 'filter-btn--active' : ''}`}
            >
              {s.replace(/_/g, ' ')} <span style={{ marginLeft: 4, opacity: 0.6 }}>{counts[s]}</span>
            </button>
          ) : null)}
          <select
            value={readinessFilter}
            onChange={e => setReadinessFilter(e.target.value)}
            style={{ ...selectStyle, width: 'auto', marginLeft: '8px' }}
          >
            <option value="">All readiness</option>
            {READINESS.map(r => <option key={r} value={r}>{r.replace(/_/g, ' ')}</option>)}
          </select>
        </div>
      )}

      {loading && <LoadingState label="Loading research cases…" />}
      {error && <ErrorBanner message={error} />}

      {!loading && !error && cases.length === 0 && (
        <EmptyState
          icon="🔬"
          title="No research cases"
          description={statusFilter ? `No cases with status "${statusFilter}".` : 'Create one from an existing evaluation using the button above.'}
        />
      )}

      {!loading && !error && cases.length > 0 && (
        <div style={{ display: 'grid', gap: '8px' }}>
          {cases.map(rc => (
            <Link
              key={rc.id}
              href={`/investment/research/${rc.id}`}
              style={{ textDecoration: 'none' }}
            >
              <div className="card" style={{ cursor: 'pointer', transition: 'border-color 0.15s' }}>
                <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: '16px' }}>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap', marginBottom: '6px', alignItems: 'center' }}>
                      <StatusBadge value={rc.status} />
                      {rc.investment_readiness && <StatusBadge value={rc.investment_readiness} />}
                      {rc.brief && <span className="status-badge status-badge--partial">has brief</span>}
                    </div>
                    <div style={{ fontFamily: 'var(--font-mono)', fontSize: '11px', color: 'var(--text-faint)', marginBottom: '4px' }}>
                      Case {rc.id.slice(0, 8).toUpperCase()}
                      {rc.situation_id && <span> — Situation {rc.situation_id.slice(0, 8).toUpperCase()}</span>}
                    </div>
                    {rc.notes && (
                      <p style={{ fontFamily: 'var(--font-sans)', fontSize: '12px', color: 'var(--text-secondary)', margin: 0, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                        {rc.notes}
                      </p>
                    )}
                  </div>
                  <div style={{ textAlign: 'right', flexShrink: 0 }}>
                    <div style={{ fontFamily: 'var(--font-mono)', fontSize: '11px', color: 'var(--text-faint)', marginBottom: '4px' }}>
                      {rc.tasks.length}T · {rc.documents.length}D · {rc.sources.length}S
                    </div>
                    <div style={{ fontFamily: 'var(--font-mono)', fontSize: '11px', color: 'var(--text-faint)' }}>
                      {new Date(rc.created_at).toLocaleDateString('en-CH', { day: '2-digit', month: 'short', year: '2-digit' })}
                    </div>
                  </div>
                </div>
              </div>
            </Link>
          ))}
        </div>
      )}

      <div style={{ marginTop: '32px', fontFamily: 'var(--font-mono)', fontSize: '11px', color: 'var(--text-faint)', textAlign: 'center' }}>
        Private research desk — no publishing without manual approval
      </div>

    </div>
  );
}
