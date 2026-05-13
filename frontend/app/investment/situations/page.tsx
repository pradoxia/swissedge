'use client';

import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
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

function formatActivityDate(raw: string | null | undefined): string | null {
  if (!raw) return null;
  try {
    return new Date(raw).toLocaleDateString('en-GB', { day: '2-digit', month: 'short' });
  } catch {
    return raw;
  }
}

function latestActivityFor(s: Situation): { title: string; timestamp: string | null; status: 'info' | 'needs_attention' | 'manual_review_required' | 'completed' } {
  const workspace = s.methodology_workspace ?? (s.evaluation?.methodology_workspace as Situation['methodology_workspace'] | undefined);
  const candidates = workspace?.resource_candidates ?? [];
  const latestCandidate = [...candidates]
    .filter(item => item.discovered_at)
    .sort((a, b) => (a.discovered_at ?? '').localeCompare(b.discovered_at ?? ''))
    .at(-1);
  if (latestCandidate) {
    const needsAttention = ['candidate_found', 'rejected'].includes(latestCandidate.status);
    return {
      title: `Resource ${latestCandidate.status.replace(/_/g, ' ')}`,
      timestamp: formatActivityDate(latestCandidate.discovered_at),
      status: needsAttention ? 'manual_review_required' : latestCandidate.status === 'evidence_found' ? 'completed' : 'info',
    };
  }
  const missingResources = workspace?.required_resources?.filter(item => ['missing', 'needs_evidence', 'not_started'].includes(item.status)).length ?? 0;
  const missingChecklist = workspace?.checklist?.filter(item => ['missing', 'needs_evidence', 'not_started', 'open'].includes(item.status)).length ?? 0;
  if (missingResources + missingChecklist > 0) {
    return {
      title: `${missingResources + missingChecklist} documentation gaps`,
      timestamp: formatActivityDate(s.updated_at ?? s.detected_at),
      status: 'needs_attention',
    };
  }
  if (workspace?.research_case_id) {
    return {
      title: 'ResearchCase linked',
      timestamp: formatActivityDate(s.updated_at ?? s.detected_at),
      status: 'completed',
    };
  }
  return {
    title: 'SEC detection created',
    timestamp: formatActivityDate(s.detected_at),
    status: 'info',
  };
}

function documentationSnapshotFor(s: Situation): { level: string; missing: number } {
  const workspace = s.methodology_workspace ?? (s.evaluation?.methodology_workspace as Situation['methodology_workspace'] | undefined);
  const secDetection = s.evaluation?.sec_detection ?? {};
  const hasSecMetadata = !!(s.filing_type || s.filing_url || secDetection.cik || secDetection.accession_number);
  const required = workspace?.required_resources ?? [];
  const checklist = workspace?.checklist ?? [];
  const candidates = workspace?.resource_candidates ?? [];
  const suggestions = workspace?.search_suggestions ?? [];
  const missingResources = required.filter(item => ['missing', 'needs_evidence', 'not_started'].includes(item.status)).length;
  const missingChecklist = checklist.filter(item => ['missing', 'needs_evidence', 'not_started', 'open'].includes(item.status)).length;
  const score =
    (hasSecMetadata ? 20 : 0) +
    (s.filing_url ? 15 : 0) +
    (required.length ? 15 : 0) +
    (candidates.length ? 15 : 0) +
    (checklist.length ? 10 : 0) +
    (candidates.some(item => item.status === 'evidence_found') || s.filing_url ? 10 : 0) +
    (suggestions.length ? 5 : 0) +
    (workspace?.research_case_id ? 5 : 0) +
    (checklist.some(item => item.human_review_required) ? 5 : 0);
  const level = score >= 80 && s.filing_url ? 'good' : score >= 50 ? 'needs evidence' : score >= 25 ? 'needs resources' : 'needs links';
  return { level, missing: missingResources + missingChecklist };
}

function sourceFinderSnapshotFor(s: Situation): { hasSecLink: boolean; missingOfficialDocs: number; queries: number; status: string } {
  const workspace = s.methodology_workspace ?? (s.evaluation?.methodology_workspace as Situation['methodology_workspace'] | undefined);
  const required = workspace?.required_resources ?? [];
  const checklist = workspace?.checklist ?? [];
  const suggestions = workspace?.search_suggestions ?? [];
  const secDetection = s.evaluation?.sec_detection ?? {};
  const hasSecLink = !!(s.filing_url || secDetection.filing_url);
  const missingRequired = required.filter(item => ['missing', 'needs_evidence', 'not_started'].includes(item.status)).length;
  const missingChecklist = checklist.filter(item => ['missing', 'needs_evidence', 'not_started', 'open'].includes(item.status)).length;
  const queries = suggestions.filter(item => !!item.query).length;
  return {
    hasSecLink,
    missingOfficialDocs: missingRequired + missingChecklist,
    queries,
    status: hasSecLink && missingRequired + missingChecklist === 0 ? 'ready' : 'needs work',
  };
}

function patternLabelFor(s: Situation): string {
  const filing = (s.filing_type ?? s.evaluation?.sec_detection?.detected_form_type ?? '').toLowerCase();
  const situationType = (s.evaluation?.sec_detection?.situation_type ?? s.situation_type ?? '').toLowerCase();
  if (filing.includes('sc to-i')) return 'self-tender';
  if (filing.includes('sc to-t')) return 'tender';
  if (filing.includes('form 10') || situationType.includes('spin')) return 'spin-off';
  if (filing.includes('8-k') && (situationType.includes('liquidation') || situationType.includes('dissolution'))) return 'liquidation';
  return 'general';
}

function completionLevelFor(s: Situation): string {
  const workspace = s.methodology_workspace ?? (s.evaluation?.methodology_workspace as Situation['methodology_workspace'] | undefined);
  if (workspace?.research_case_id || workflowFor(s) === 'promoted_to_research_case') return 'promoted';
  const required = workspace?.required_resources ?? [];
  const checklist = workspace?.checklist ?? [];
  const candidates = workspace?.resource_candidates ?? [];
  if (required.some(item => ['missing', 'needs_evidence', 'not_started'].includes(item.status))) return 'needs sources';
  if (
    candidates.some(item => item.status === 'candidate_found') ||
    checklist.some(item => ['missing', 'needs_evidence', 'not_started', 'open'].includes(item.status))
  ) {
    return 'needs mapping';
  }
  if (required.length || checklist.length) return 'ready for review';
  return 'blocked';
}

function MiniCaseRow({ situation: s }: { situation: Situation }) {
  const [hovered, setHovered] = useState(false);
  const name = s.company_name.length > 34 ? s.company_name.slice(0, 32) + '…' : s.company_name;
  const date = filingDate(s);
  const workspace = s.methodology_workspace ?? (s.evaluation?.methodology_workspace as Situation['methodology_workspace'] | undefined);
  const progress = workspace?.progress;
  const situationType = s.evaluation?.sec_detection?.situation_type ?? s.situation_type;
  const pattern = patternLabelFor(s);
  const completion = completionLevelFor(s);

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
          <span className="status-badge status-badge--readonly" style={{ fontSize: 9 }}>Pattern: {pattern}</span>
          <span className="status-badge status-badge--readonly" style={{ fontSize: 9 }}>Completion: {completion}</span>
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
  const [detailsOpen, setDetailsOpen] = useState(false);
  const secDetection = s.evaluation?.sec_detection;
  const workspace = s.methodology_workspace ?? (s.evaluation?.methodology_workspace as Situation['methodology_workspace'] | undefined);
  const hasWorkspace = !!workspace;
  const progress = workspace?.progress;
  const evidenceFound = progress?.evidence_found ?? 0;
  const name = s.company_name.length > 38 ? s.company_name.slice(0, 36) + '…' : s.company_name;
  const date = filingDate(s);
  const workflow = workflowFor(s);
  const documentation = documentationSnapshotFor(s);
  const sourceFinder = sourceFinderSnapshotFor(s);
  const latestActivity = latestActivityFor(s);
  const attention = latestActivity.status === 'needs_attention' || latestActivity.status === 'manual_review_required';
  const pattern = patternLabelFor(s);
  const completion = completionLevelFor(s);

  return (
    <div className="card" style={{ padding: '12px 13px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 8, marginBottom: 5 }}>
          <Link
            href={`/investment/situations/${s.id}`}
            style={{ fontWeight: 600, fontSize: 13, color: 'var(--text-primary)', lineHeight: 1.3, textDecoration: 'none' }}
          >
            {name}
          </Link>
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
          <span className={`status-badge ${documentation.missing > 0 ? 'status-badge--preview' : 'status-badge--readonly'}`} style={{ fontSize: 10 }}>Missing: {documentation.missing}</span>
          <span className="status-badge status-badge--partial" style={{ fontSize: 10 }}>Evidence: {evidenceFound}</span>
          <span className="status-badge status-badge--readonly" style={{ fontSize: 10 }}>Completion: {completion}</span>
          <span className="status-badge status-badge--readonly" style={{ fontSize: 10 }}>Pattern: {pattern}</span>
          {workspace?.research_case_id && <span className="status-badge status-badge--active" style={{ fontSize: 10 }}>ResearchCase</span>}
        </div>
        <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginBottom: 8 }}>
          <Link href={`/investment/situations/${s.id}`} className="btn btn--secondary btn--sm">
            Open case
          </Link>
          {s.filing_url && (
            <a href={s.filing_url} target="_blank" rel="noreferrer" className="btn btn--ghost btn--sm">
              SEC link
            </a>
          )}
          {workspace?.research_case_id && (
            <Link href={`/investment/research/${workspace.research_case_id}`} className="btn btn--ghost btn--sm">
              ResearchCase
            </Link>
          )}
          {hasWorkspace && (
            <button type="button" className="btn btn--ghost btn--sm" onClick={() => setDetailsOpen(open => !open)}>
              {detailsOpen ? 'Hide details' : 'Details'}
            </button>
          )}
        </div>
        {detailsOpen && hasWorkspace && (
          <div style={{ display: 'grid', gap: 5, marginBottom: 8, fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-muted)' }}>
            <span>Docs: {documentation.level}</span>
            <span>Source finder: {sourceFinder.status} / SEC link {sourceFinder.hasSecLink ? 'yes' : 'no'}</span>
            <span>Official docs missing: {sourceFinder.missingOfficialDocs} / Manual queries: {sourceFinder.queries}</span>
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
        <div style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: attention ? '#7a5a00' : 'var(--text-faint)', display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 8 }}>
          <span>{date}</span>
          <span style={{ textAlign: 'right' }}>
            {attention ? 'Attention: ' : 'Latest: '}
            {latestActivity.title}
            {latestActivity.timestamp ? ` · ${latestActivity.timestamp}` : ''}
          </span>
        </div>
      </div>
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
  const [filterWorkflow, setFilterWorkflow] = useState('');
  const [hideEmpty, setHideEmpty] = useState(false);
  const [compactView, setCompactView] = useState(false);
  const [lastRefreshed, setLastRefreshed] = useState<Date | null>(null);
  const [movingId, setMovingId] = useState<string | null>(null);
  const boardRef = useRef<HTMLDivElement | null>(null);

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
      situations.map(s => s.evaluation?.sec_detection?.situation_type ?? s.situation_type ?? s.v2_situation_type ?? '').filter(Boolean),
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
        const st = s.evaluation?.sec_detection?.situation_type ?? s.situation_type ?? s.v2_situation_type ?? '';
        if (st !== filterType) return false;
      }
      if (filterFiling && (s.filing_type ?? '') !== filterFiling) return false;
      if (filterWorkflow && workflowFor(s) !== filterWorkflow) return false;
      if (search) {
        const q = search.toLowerCase();
        if (!s.company_name.toLowerCase().includes(q) && !(s.ticker ?? '').toLowerCase().includes(q)) return false;
      }
      return true;
    });
  }, [situations, filterType, filterFiling, filterWorkflow, search]);

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

  const hasFilters = !!(search || filterType || filterFiling || filterWorkflow);
  const boardColumnCount = visibleColumns.length;

  function scrollBoard(direction: -1 | 1) {
    const el = boardRef.current;
    if (!el) return;
    el.scrollBy({ left: direction * Math.max(320, el.clientWidth * 0.75), behavior: 'smooth' });
  }

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
    <div className="page-container--wide" style={{ maxWidth: 'min(1880px, calc(100vw - 32px))' }}>
      <PageHeader
        title="Kanban — Special Situations"
        subtitle="Mission Control pipeline — official-source signals, evidence gaps, manual movement"
        backHref="/investment/evaluations"
        backLabel="Evaluations Queue"
        actions={
          <button className="btn btn--secondary btn--sm" onClick={load} disabled={loading}>
            {loading ? 'Loading…' : 'Refresh'}
          </button>
        }
      />

      <InfoBanner variant="guardrail">
        Detected does not mean evaluated. Evidence found does not mean verified.
        These are official-source detections awaiting human review.
        No automated investment decisions are made from this pipeline.
      </InfoBanner>

      <InfoBanner variant="info">
        Evaluations = legacy/evaluator review queue. Special Situations Kanban = active SEC-detection workflow.
        Flow: SEC EDGAR Detection -&gt; SpecialSituation -&gt; Kanban evidence mapping -&gt; manual promotion -&gt; ResearchCase -&gt; Evaluation Preparation / Evidence Links / Intelligence Score.
        Promotion is manual; no recommendation, publishing, or ResearchCase creation happens automatically.
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
          <select value={filterWorkflow} onChange={e => setFilterWorkflow(e.target.value)} style={FILTER_INPUT_STYLE}>
            <option value="">All workflow phases</option>
            {WORKFLOW_OPTIONS.map(option => <option key={option.value} value={option.value}>{option.label}</option>)}
          </select>
          {hasFilters && (
            <button
              className="btn btn--ghost btn--sm"
              onClick={() => { setSearch(''); setFilterType(''); setFilterFiling(''); setFilterWorkflow(''); }}
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
                Pipeline
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
      ) : visibleColumns.length === 0 ? (
        <div className="card" style={{ padding: 24, textAlign: 'center' }}>
          <div style={{ fontSize: 14, fontWeight: 700, color: 'var(--text-primary)' }}>No visible phases match the current filters.</div>
          <div style={{ marginTop: 6, fontSize: 12, color: 'var(--text-muted)' }}>
            Hide Empty Phases is on and all filtered columns are empty. Clear filters or turn the toggle off to see every workflow phase.
          </div>
        </div>
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
        /* ── Pipeline board (horizontal scroll; expands on ultrawide screens) ── */
        <div>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 10, marginBottom: 8 }}>
          <div style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--text-faint)' }}>
            Scroll horizontally to move across phases. Use arrows or the visible scrollbar.
          </div>
          <div style={{ display: 'flex', gap: 6 }}>
            <button type="button" className="btn btn--ghost btn--sm" onClick={() => scrollBoard(-1)} aria-label="Scroll left">Scroll left</button>
            <button type="button" className="btn btn--ghost btn--sm" onClick={() => scrollBoard(1)} aria-label="Scroll right">Scroll right</button>
          </div>
        </div>
        <div ref={boardRef} style={{ overflowX: 'scroll', paddingBottom: 16, scrollbarWidth: 'auto' }}>
          <div style={{
            display: 'grid',
            gridTemplateColumns: `repeat(${boardColumnCount}, minmax(260px, 1fr))`,
            gap: 10,
            minWidth: `${boardColumnCount * 270}px`,
          }}>
            {visibleColumns.map(col => {
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
        </div>
      )}

      <div style={{ marginTop: 24, fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--text-faint)', textAlign: 'right' }}>
        Private research desk — detected does not mean evaluated — no publishing without manual approval
      </div>
    </div>
  );
}
