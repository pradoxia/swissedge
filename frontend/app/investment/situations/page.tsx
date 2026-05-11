'use client';

import { useCallback, useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import {
  ErrorBanner,
  InfoBanner,
  LoadingState,
  MetricRow,
  PageHeader,
  StatusBadge,
} from '@/app/components/ui';
import { fetchSituations, updateSituationWorkflowStatus, type Situation } from '@/lib/api';

const COLUMNS: {
  key: string;
  label: string;
  statuses: string[];
  description: string;
}[] = [
  { key: 'new_detection',             label: 'New Detections',        statuses: ['new_detection', 'detected'],        description: 'Official-source signals, not yet reviewed' },
  { key: 'triage_needed',             label: 'Needs Triage',          statuses: ['triage_needed'],                    description: 'Require manual classification' },
  { key: 'needs_resources',           label: 'Needs Resources',       statuses: ['needs_resources'],                  description: 'Missing evidence materials' },
  { key: 'checklist_in_progress',     label: 'Checklist In Progress', statuses: ['checklist_in_progress'],            description: 'Evidence gathering underway' },
  { key: 'ready_for_research_case',   label: 'Ready for Research',    statuses: ['ready_for_research_case'],          description: 'Workspace complete, promote when ready' },
  { key: 'promoted_to_research_case', label: 'Promoted',              statuses: ['promoted_to_research_case'],        description: 'Linked to a ResearchCase' },
  { key: 'watchlist',                 label: 'Watchlist',             statuses: ['watchlist'],                        description: 'Monitoring, lower priority' },
  { key: 'ignored',                   label: 'Ignored',               statuses: ['ignored', 'archived'],              description: 'Not relevant or archived' },
];

const WORKFLOW_OPTIONS = COLUMNS.map(col => ({ value: col.key, label: col.label }));
const MAX_VISIBLE = 5;

function workflowFor(s: Situation): string {
  const workflowStatus = (s.methodology_workspace ?? s.evaluation?.methodology_workspace)?.workflow_status as string | undefined;
  return workflowStatus ?? (s.status === 'detected' ? 'new_detection' : s.status);
}

function columnFor(s: Situation): string {
  const effective = workflowFor(s);
  for (const col of COLUMNS) {
    if (col.statuses.includes(effective)) return col.key;
  }
  return 'triage_needed';
}

function filingDate(s: Situation): string {
  const raw = s.evaluation?.sec_detection?.filing_date ?? s.detected_at;
  if (!raw) return '—';
  try {
    return new Date(raw).toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' });
  } catch {
    return raw;
  }
}

function MiniCaseRow({ situation: s }: { situation: Situation }) {
  const [hovered, setHovered] = useState(false);
  const name = s.company_name.length > 34 ? s.company_name.slice(0, 32) + '…' : s.company_name;
  const date = filingDate(s);
  const workspace = s.methodology_workspace ?? (s.evaluation?.methodology_workspace as Situation['methodology_workspace'] | undefined);
  const progress = workspace?.progress;
  const situationType = s.evaluation?.sec_detection?.situation_type ?? s.situation_type;

  return (
    <Link href={`/investment/situations/${s.id}`} style={{ textDecoration: 'none', display: 'block' }}>
      <div
        style={{
          padding: '7px 14px',
          borderBottom: '1px solid var(--border-default)',
          background: hovered ? 'var(--bg-subtle)' : 'transparent',
          transition: 'background 0.1s',
          cursor: 'pointer',
        }}
        onMouseEnter={() => setHovered(true)}
        onMouseLeave={() => setHovered(false)}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', gap: 6, marginBottom: 3 }}>
          <span style={{ fontWeight: 600, fontSize: 12, color: 'var(--text-primary)', lineHeight: 1.3 }}>
            {name}
            {s.ticker && (
              <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-muted)', marginLeft: 5, fontWeight: 400 }}>
                {s.ticker}
              </span>
            )}
          </span>
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-faint)', flexShrink: 0 }}>
            {date}
          </span>
        </div>
        <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap' }}>
          {s.filing_type && (
            <span className="status-badge status-badge--readonly" style={{ fontSize: 9 }}>{s.filing_type}</span>
          )}
          {situationType && (
            <span className="status-badge status-badge--readonly" style={{ fontSize: 9 }}>{situationType}</span>
          )}
          {progress && progress.missing_required_resources > 0 && (
            <span className="status-badge status-badge--preview" style={{ fontSize: 9 }}>{progress.missing_required_resources} missing</span>
          )}
          {progress && progress.evidence_found > 0 && (
            <span className="status-badge status-badge--partial" style={{ fontSize: 9 }}>{progress.evidence_found} evidence</span>
          )}
          {workspace?.research_case_id && (
            <span className="status-badge status-badge--active" style={{ fontSize: 9 }}>RC</span>
          )}
        </div>
      </div>
    </Link>
  );
}

function PhaseCard({
  col,
  cards,
}: {
  col: (typeof COLUMNS)[number];
  cards: Situation[];
}) {
  const visible = cards.slice(0, MAX_VISIBLE);
  const overflow = cards.length - MAX_VISIBLE;

  return (
    <div className="card" style={{ padding: 0, overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
      <div style={{
        padding: '9px 14px',
        background: 'var(--bg-subtle)',
        borderBottom: '1px solid var(--border-default)',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        gap: 8,
      }}>
        <span style={{
          fontFamily: 'var(--font-mono)',
          fontSize: 10,
          fontWeight: 700,
          textTransform: 'uppercase',
          letterSpacing: '0.07em',
          color: 'var(--text-muted)',
        }}>
          {col.label}
        </span>
        {cards.length > 0 && (
          <span style={{
            fontFamily: 'var(--font-mono)',
            fontSize: 11,
            fontWeight: 700,
            color: 'var(--text-primary)',
            background: 'var(--bg-page)',
            border: '1px solid var(--border-default)',
            borderRadius: 4,
            padding: '1px 7px',
          }}>
            {cards.length}
          </span>
        )}
      </div>

      <div style={{
        padding: '4px 14px 5px',
        fontFamily: 'var(--font-mono)',
        fontSize: 10,
        color: 'var(--text-faint)',
        borderBottom: '1px solid var(--border-default)',
      }}>
        {col.description}
      </div>

      {cards.length === 0 ? (
        <div style={{
          padding: '16px 14px',
          textAlign: 'center',
          fontFamily: 'var(--font-mono)',
          fontSize: 11,
          color: 'var(--text-faint)',
          flex: 1,
        }}>
          No cases in this phase.
        </div>
      ) : (
        <div style={{ flex: 1 }}>
          {visible.map(s => (
            <MiniCaseRow key={s.id} situation={s} />
          ))}
          {overflow > 0 && (
            <div style={{ padding: '6px 14px 8px' }}>
              <span style={{
                fontFamily: 'var(--font-mono)',
                fontSize: 10,
                color: 'var(--accent)',
              }}>
                +{overflow} more in this phase
              </span>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function SituationCard({
  situation: s,
  moving,
  onMove,
}: {
  situation: Situation;
  moving: boolean;
  onMove: (situation: Situation, workflowStatus: string) => void;
}) {
  const secDetection = s.evaluation?.sec_detection;
  const workspace = s.methodology_workspace ?? (s.evaluation?.methodology_workspace as Situation['methodology_workspace'] | undefined);
  const hasWorkspace = !!workspace;
  const progress = workspace?.progress;
  const missingRequired = progress?.missing_required_resources ?? 0;
  const candidateResources = progress?.candidate_resources ?? (workspace?.resource_candidates?.filter(item => item.status === 'candidate_found').length ?? 0);
  const evidenceFound = progress?.evidence_found ?? 0;
  const name = s.company_name.length > 38 ? s.company_name.slice(0, 36) + '…' : s.company_name;
  const date = filingDate(s);
  const workflow = workflowFor(s);

  return (
    <Link href={`/investment/situations/${s.id}`} style={{ textDecoration: 'none', display: 'block' }}>
      <div className="card" style={{ padding: '11px 13px', cursor: 'pointer' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 8, marginBottom: 5 }}>
          <div style={{ fontWeight: 600, fontSize: 13, color: 'var(--text-primary)', lineHeight: 1.3 }}>{name}</div>
          <StatusBadge value={workflow} />
        </div>
        {s.ticker && (
          <div style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--text-secondary)', marginBottom: 6 }}>
            {s.ticker}
          </div>
        )}
        <div style={{ display: 'flex', gap: 5, flexWrap: 'wrap', marginBottom: 8 }}>
          {s.filing_type && <span className="status-badge status-badge--readonly" style={{ fontSize: 10 }}>{s.filing_type}</span>}
          {secDetection?.situation_type && <span className="status-badge status-badge--readonly" style={{ fontSize: 10 }}>{secDetection.situation_type}</span>}
          {hasWorkspace && <span className="status-badge status-badge--partial" style={{ fontSize: 10 }}>workspace</span>}
          {s.evaluation?.detected_only === true && <span className="status-badge status-badge--preview" style={{ fontSize: 10 }}>Detected only</span>}
          {workspace?.research_case_id && <span className="status-badge status-badge--active" style={{ fontSize: 10 }}>ResearchCase</span>}
        </div>
        {hasWorkspace && (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 5, marginBottom: 8 }}>
            {([['Missing', missingRequired], ['Candidates', candidateResources], ['Evidence', evidenceFound]] as [string, number][]).map(([label, value]) => (
              <div key={label} style={{ background: 'var(--bg-subtle)', borderRadius: 5, padding: '5px 6px' }}>
                <div style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--text-faint)', textTransform: 'uppercase' }}>{label}</div>
                <div style={{ fontFamily: 'var(--font-mono)', fontSize: 12, color: 'var(--text-primary)' }}>{value}</div>
              </div>
            ))}
          </div>
        )}
        {hasWorkspace && (
          <select
            value={workflow}
            disabled={moving}
            onClick={e => e.stopPropagation()}
            onChange={e => { e.preventDefault(); onMove(s, e.target.value); }}
            style={{
              width: '100%', marginBottom: 8, padding: '5px 7px',
              border: '1px solid var(--border-default)', borderRadius: 6,
              fontFamily: 'var(--font-mono)', fontSize: 11,
              background: 'var(--bg-page)', color: 'var(--text-primary)',
            }}
          >
            {WORKFLOW_OPTIONS.map(option => (
              <option key={option.value} value={option.value}>{option.label}</option>
            ))}
          </select>
        )}
        <div style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--text-faint)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span>{date}</span>
          {s.filing_url && (
            <a href={s.filing_url} target="_blank" rel="noreferrer" onClick={e => e.stopPropagation()} style={{ color: 'var(--accent)', fontSize: 10 }}>
              SEC ↗
            </a>
          )}
        </div>
      </div>
    </Link>
  );
}

const FILTER_INPUT_STYLE = {
  padding: '6px 10px',
  border: '1px solid var(--border-default)',
  borderRadius: 6,
  fontFamily: 'var(--font-mono)',
  fontSize: 12,
  background: 'var(--bg-page)',
  color: 'var(--text-primary)',
  outline: 'none',
} as const;

export default function SpecialSituationsPage() {
  const [situations, setSituations] = useState<Situation[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState('');
  const [filterType, setFilterType] = useState('');
  const [filterFiling, setFilterFiling] = useState('');
  const [hideEmpty, setHideEmpty] = useState(false);
  const [compactView, setCompactView] = useState(true);
  const [lastRefreshed, setLastRefreshed] = useState<Date | null>(null);
  const [movingId, setMovingId] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await fetchSituations();
      setSituations(res.situations);
      setLastRefreshed(new Date());
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load situations');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void Promise.resolve().then(load);
  }, [load]);

  const typeOptions = useMemo(() => {
    const types = new Set(
      situations.map(s => s.situation_type ?? s.v2_situation_type ?? '').filter(Boolean),
    );
    return Array.from(types).sort();
  }, [situations]);

  const filingOptions = useMemo(() => {
    const filings = new Set(situations.map(s => s.filing_type ?? '').filter(Boolean));
    return Array.from(filings).sort();
  }, [situations]);

  const filtered = useMemo(() => {
    return situations.filter(s => {
      if (filterType) {
        const st = s.situation_type ?? s.v2_situation_type ?? '';
        if (st !== filterType) return false;
      }
      if (filterFiling && (s.filing_type ?? '') !== filterFiling) return false;
      if (search) {
        const q = search.toLowerCase();
        if (!s.company_name.toLowerCase().includes(q) && !(s.ticker ?? '').toLowerCase().includes(q)) return false;
      }
      return true;
    });
  }, [situations, filterType, filterFiling, search]);

  const columnMap = useMemo(() => {
    const map: Record<string, Situation[]> = {};
    for (const col of COLUMNS) map[col.key] = [];
    for (const s of filtered) {
      const key = columnFor(s);
      (map[key] ?? map['triage_needed']).push(s);
    }
    return map;
  }, [filtered]);

  const visibleColumns = useMemo(
    () => hideEmpty ? COLUMNS.filter(col => (columnMap[col.key]?.length ?? 0) > 0) : COLUMNS,
    [columnMap, hideEmpty],
  );

  const total = situations.length;
  const newDetections = situations.filter(s => workflowFor(s) === 'new_detection').length;
  const needsResources = situations.filter(s => workflowFor(s) === 'needs_resources').length;
  const readyCount = situations.filter(s => workflowFor(s) === 'ready_for_research_case').length;
  const promotedCount = situations.filter(s => workflowFor(s) === 'promoted_to_research_case').length;
  const watchlistCount = situations.filter(s => workflowFor(s) === 'watchlist').length;

  const hasFilters = !!(search || filterType || filterFiling);

  async function moveSituation(situation: Situation, workflowStatus: string) {
    try {
      setMovingId(situation.id);
      const result = await updateSituationWorkflowStatus(situation.id, workflowStatus);
      setSituations(current => current.map(item => item.id === situation.id ? result.situation : item));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to move situation');
    } finally {
      setMovingId(null);
    }
  }

  return (
    <div className="page-container--wide">
      <PageHeader
        title="Special Situations"
        subtitle="Detection pipeline — official-source signals awaiting human review"
        backHref="/investment/evaluations"
        backLabel="Evaluations Queue"
        actions={
          <button className="btn btn--secondary btn--sm" onClick={load} disabled={loading}>
            {loading ? 'Loading…' : 'Refresh'}
          </button>
        }
      />

      <InfoBanner variant="guardrail">
        Detected does not mean evaluated. These are official-source detections awaiting human review.
        No automated investment decisions are made from this pipeline.
      </InfoBanner>

      {error && <ErrorBanner message={error} />}

      <MetricRow items={[
        { label: 'Total', value: total },
        { label: 'New Detections', value: newDetections },
        { label: 'Needs Resources', value: needsResources },
        { label: 'Ready for Research', value: readyCount },
        { label: 'Promoted', value: promotedCount },
        { label: 'Watchlist', value: watchlistCount },
      ]} />

      {/* Filters + view toggle */}
      <div className="card" style={{ marginBottom: 20 }}>
        <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', alignItems: 'center' }}>
          <input
            type="text"
            placeholder="Search company or ticker…"
            value={search}
            onChange={e => setSearch(e.target.value)}
            style={{ ...FILTER_INPUT_STYLE, minWidth: 200 }}
          />
          {typeOptions.length > 0 && (
            <select value={filterType} onChange={e => setFilterType(e.target.value)} style={FILTER_INPUT_STYLE}>
              <option value="">All situation types</option>
              {typeOptions.map(t => <option key={t} value={t}>{t}</option>)}
            </select>
          )}
          {filingOptions.length > 0 && (
            <select value={filterFiling} onChange={e => setFilterFiling(e.target.value)} style={FILTER_INPUT_STYLE}>
              <option value="">All filing types</option>
              {filingOptions.map(f => <option key={f} value={f}>{f}</option>)}
            </select>
          )}
          {hasFilters && (
            <button
              className="btn btn--ghost btn--sm"
              onClick={() => { setSearch(''); setFilterType(''); setFilterFiling(''); }}
            >
              Clear filters
            </button>
          )}

          <div style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
            <label style={{ display: 'flex', alignItems: 'center', gap: 6, fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--text-muted)', cursor: 'pointer' }}>
              <input
                type="checkbox"
                checked={hideEmpty}
                onChange={e => setHideEmpty(e.target.checked)}
                style={{ cursor: 'pointer' }}
              />
              Hide empty phases
            </label>

            {/* View toggle */}
            <div style={{
              display: 'flex',
              border: '1px solid var(--border-default)',
              borderRadius: 6,
              overflow: 'hidden',
            }}>
              <button
                onClick={() => setCompactView(true)}
                style={{
                  padding: '4px 10px',
                  fontFamily: 'var(--font-mono)',
                  fontSize: 11,
                  border: 'none',
                  borderRight: '1px solid var(--border-default)',
                  background: compactView ? 'var(--bg-subtle)' : 'var(--bg-page)',
                  color: compactView ? 'var(--text-primary)' : 'var(--text-muted)',
                  cursor: 'pointer',
                  fontWeight: compactView ? 700 : 400,
                }}
              >
                Overview
              </button>
              <button
                onClick={() => setCompactView(false)}
                style={{
                  padding: '4px 10px',
                  fontFamily: 'var(--font-mono)',
                  fontSize: 11,
                  border: 'none',
                  background: !compactView ? 'var(--bg-subtle)' : 'var(--bg-page)',
                  color: !compactView ? 'var(--text-primary)' : 'var(--text-muted)',
                  cursor: 'pointer',
                  fontWeight: !compactView ? 700 : 400,
                }}
              >
                Detailed
              </button>
            </div>

            {lastRefreshed && (
              <span style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--text-faint)' }}>
                {lastRefreshed.toLocaleTimeString()}
              </span>
            )}
          </div>
        </div>
      </div>

      {loading ? (
        <LoadingState label="Loading situations…" />
      ) : compactView ? (
        /* ── Compact overview board ── */
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))',
          gap: 14,
        }}>
          {visibleColumns.map(col => (
            <PhaseCard key={col.key} col={col} cards={columnMap[col.key] ?? []} />
          ))}
        </div>
      ) : (
        /* ── Detailed board (horizontal scroll, full cards) ── */
        <div style={{ overflowX: 'auto', paddingBottom: 16 }}>
          <div style={{
            display: 'grid',
            gridTemplateColumns: `repeat(${COLUMNS.length}, 272px)`,
            gap: 10,
            minWidth: `${COLUMNS.length * 282}px`,
          }}>
            {COLUMNS.map(col => {
              const cards = columnMap[col.key] ?? [];
              return (
                <div key={col.key} style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                  <div style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    padding: '7px 12px',
                    background: 'var(--bg-subtle)',
                    border: '1px solid var(--border-default)',
                    borderRadius: 7,
                  }}>
                    <span style={{
                      fontFamily: 'var(--font-mono)',
                      fontSize: 10,
                      fontWeight: 700,
                      textTransform: 'uppercase',
                      color: 'var(--text-muted)',
                      letterSpacing: '0.07em',
                    }}>
                      {col.label}
                    </span>
                    <span style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--text-faint)' }}>
                      {cards.length}
                    </span>
                  </div>
                  {cards.length === 0 ? (
                    <div style={{
                      padding: '20px 12px',
                      textAlign: 'center',
                      fontFamily: 'var(--font-mono)',
                      fontSize: 11,
                      color: 'var(--text-faint)',
                      border: '1px dashed var(--border-default)',
                      borderRadius: 7,
                    }}>
                      No cases in this phase.
                    </div>
                  ) : (
                    cards.map(s => (
                      <SituationCard
                        key={s.id}
                        situation={s}
                        moving={movingId === s.id}
                        onMove={moveSituation}
                      />
                    ))
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}

      <div style={{ marginTop: 24, fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--text-faint)', textAlign: 'right' }}>
        Private research desk — detected does not mean evaluated — no publishing without manual approval
      </div>
    </div>
  );
}
