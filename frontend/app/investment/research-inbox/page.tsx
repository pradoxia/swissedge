'use client';

import { useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import {
  fetchResearchCases,
  fetchSituations,
  type ResearchCase,
  type Situation,
} from '@/lib/api';
import { PageHeader, MetricRow, LoadingState, ErrorBanner, InfoBanner } from '@/app/components/ui';

type BucketKey =
  | 'all'
  | 'new_detected'
  | 'needs_official_source'
  | 'needs_enrichment'
  | 'ready_for_deep_research'
  | 'monitoring'
  | 'documented'
  | 'archived_discarded'
  | 'legacy_missing_v2';

interface InboxRow {
  rc: ResearchCase;
  situation: Situation | null;
  bucket: BucketKey;
  sourceOrigin: string;
  intakeMethod: string;
  evidence: string;
  officialSource: string;
  methodology: string;
  legacyMissingV2: boolean;
  openTaskCount: number;
  taskCount: number;
  docCount: number;
  sourceCount: number;
  warnings: string[];
}

const BUCKETS: { key: BucketKey; label: string }[] = [
  { key: 'all', label: 'All' },
  { key: 'new_detected', label: 'New / Detected' },
  { key: 'needs_official_source', label: 'Needs official source' },
  { key: 'needs_enrichment', label: 'Needs enrichment' },
  { key: 'ready_for_deep_research', label: 'Ready for deep research' },
  { key: 'monitoring', label: 'Monitoring' },
  { key: 'documented', label: 'Documented' },
  { key: 'archived_discarded', label: 'Archived / discarded' },
  { key: 'legacy_missing_v2', label: 'Legacy / missing V2 metadata' },
];

const READINESS = ['monitor', 'not_actionable', 'needs_more_work', 'candidate'];
const STATUSES = ['detected', 'brief_generated', 'under_investigation', 'documented', 'archived', 'published'];

// Inline badge classes for semantic status fields (not buy/sell — informational only)
const BUCKET_BADGE: Record<BucketKey, string> = {
  all: 'border-slate-200 bg-slate-50 text-slate-600',
  new_detected: 'border-sky-200 bg-sky-50 text-sky-700',
  needs_official_source: 'border-amber-200 bg-amber-50 text-amber-800',
  needs_enrichment: 'border-violet-200 bg-violet-50 text-violet-700',
  ready_for_deep_research: 'border-emerald-200 bg-emerald-50 text-emerald-700',
  monitoring: 'border-blue-200 bg-blue-50 text-blue-700',
  documented: 'border-green-200 bg-green-50 text-green-700',
  archived_discarded: 'border-slate-200 bg-slate-100 text-slate-500',
  legacy_missing_v2: 'border-amber-200 bg-amber-50 text-amber-800',
};

const READINESS_BADGE: Record<string, string> = {
  monitor: 'border-blue-200 bg-blue-50 text-blue-700',
  not_actionable: 'border-slate-200 bg-slate-100 text-slate-500',
  needs_more_work: 'border-violet-200 bg-violet-50 text-violet-700',
  candidate: 'border-emerald-200 bg-emerald-50 text-emerald-700',
};

function safeText(value: unknown, fallback = '-'): string {
  if (value === null || value === undefined || value === '') return fallback;
  if (typeof value === 'string') return value;
  if (typeof value === 'number' || typeof value === 'boolean') return String(value);
  return fallback;
}

function formatDate(value: string | null | undefined): string {
  if (!value) return '-';
  try {
    return new Date(value).toLocaleString('en-CH', { year: '2-digit', month: 'short', day: '2-digit', hour: '2-digit', minute: '2-digit' });
  } catch {
    return value;
  }
}

function hasSecUrl(url: string | null | undefined): boolean {
  return Boolean(url && url.toLowerCase().includes('sec.gov'));
}

function briefString(rc: ResearchCase, key: string): string {
  const value = rc.brief?.[key];
  return typeof value === 'string' ? value.trim() : '';
}

function hasV2Metadata(rc: ResearchCase): boolean {
  return Boolean(
    rc.source_origin_name || rc.investment_source_id || rc.intake_method || rc.connector_key ||
    rc.intake_event_id || rc.evidence_level || rc.official_source_status || rc.methodology_status ||
    rc.playbook_used || rc.checklist_used || rc.course_reference || rc.duplicate_status ||
    rc.next_follow_up_at || rc.discarded_reason,
  );
}

function deriveSourceOrigin(rc: ResearchCase, situation: Situation | null): string {
  if (rc.source_origin_name?.trim()) return rc.source_origin_name.trim();
  const linkedSource = rc.sources.find(s => s.source_name?.trim());
  if (linkedSource) return linkedSource.source_name;
  if (situation?.filing_url || situation?.filing_type) return 'legacy/evaluation';
  return 'legacy/manual';
}

function deriveEvidence(rc: ResearchCase, situation: Situation | null): string {
  if (rc.evidence_level) return rc.evidence_level;
  if (situation?.filing_url || situation?.filing_type) return 'official_filing';
  if (rc.documents.some(d => d.doc_type === 'sec_filing' || hasSecUrl(d.url))) return 'official_filing';
  if (rc.documents.length > 0 || rc.sources.length > 0) return 'unknown';
  return 'unknown';
}

function deriveOfficialSource(rc: ResearchCase, situation: Situation | null): string {
  if (rc.official_source_status) return rc.official_source_status;
  if (hasSecUrl(situation?.filing_url)) return 'likely_official';
  if (rc.documents.some(d => d.doc_type === 'sec_filing' || hasSecUrl(d.url))) return 'likely_official';
  return 'unknown';
}

function deriveMethodology(rc: ResearchCase): string {
  if (rc.methodology_status) return rc.methodology_status;
  if (rc.playbook_used || rc.checklist_used || rc.course_reference) return 'partial';
  if (briefString(rc, 'methodology_reference') || rc.playbook_version) return 'legacy';
  return 'missing';
}

function deriveBucket(rc: ResearchCase, officialSource: string, legacyMissingV2: boolean): BucketKey {
  if (rc.status === 'archived') return 'archived_discarded';
  if (rc.status === 'documented') return 'documented';
  if (rc.investment_readiness === 'candidate') return 'ready_for_deep_research';
  if (rc.investment_readiness === 'monitor') return 'monitoring';
  if (
    ['unknown', 'official_missing', 'official_needed', 'official_pending_review'].includes(officialSource) &&
    (rc.sources.length > 0 || rc.documents.length === 0)
  ) return 'needs_official_source';
  if (rc.investment_readiness === 'needs_more_work') return 'needs_enrichment';
  if (rc.status === 'detected') return 'new_detected';
  if (legacyMissingV2) return 'legacy_missing_v2';
  return 'needs_enrichment';
}

function buildInboxRow(rc: ResearchCase, situation: Situation | null): InboxRow {
  const legacyMissingV2 = !hasV2Metadata(rc);
  const sourceOrigin = deriveSourceOrigin(rc, situation);
  const evidence = deriveEvidence(rc, situation);
  const officialSource = deriveOfficialSource(rc, situation);
  const methodology = deriveMethodology(rc);
  const openTaskCount = rc.tasks.filter(t => t.status === 'open').length;
  const warnings: string[] = [];

  if (legacyMissingV2) warnings.push('legacy/manual');
  if (['unknown', 'official_missing', 'official_needed'].includes(officialSource)) warnings.push('official source unknown');
  if (['missing', 'unknown', 'human_review_required'].includes(methodology)) warnings.push('methodology missing');
  if (rc.documents.length === 0) warnings.push('no docs');
  if (rc.sources.length === 0) warnings.push('no sources');

  return {
    rc, situation,
    bucket: deriveBucket(rc, officialSource, legacyMissingV2),
    sourceOrigin, intakeMethod: rc.intake_method ?? 'legacy/manual',
    evidence, officialSource, methodology, legacyMissingV2,
    openTaskCount, taskCount: rc.tasks.length, docCount: rc.documents.length, sourceCount: rc.sources.length,
    warnings,
  };
}

function InlineBadge({ children, className = '' }: { children: React.ReactNode; className?: string }) {
  return (
    <span className={`inline-flex items-center rounded-full border px-2 py-0.5 text-[11px] font-medium ${className}`}>
      {children}
    </span>
  );
}

function evidenceBadgeClass(value: string): string {
  if (['official_filing', 'official_primary', 'official_secondary'].includes(value)) return 'border-green-200 bg-green-50 text-green-700';
  if (value === 'trusted_external' || value === 'mixed') return 'border-blue-200 bg-blue-50 text-blue-700';
  if (value === 'external_unverified') return 'border-amber-200 bg-amber-50 text-amber-800';
  return 'border-slate-200 bg-slate-100 text-slate-500';
}

function officialSourceBadgeClass(value: string): string {
  if (['likely_official', 'official_attached'].includes(value)) return 'border-green-200 bg-green-50 text-green-700';
  if (value === 'official_pending_review') return 'border-amber-200 bg-amber-50 text-amber-800';
  return 'border-slate-200 bg-slate-100 text-slate-500';
}

function methodologyBadgeClass(value: string): string {
  if (['evaluator_ready', 'partial', 'legacy'].includes(value)) return 'border-slate-200 bg-slate-50 text-slate-600';
  if (value === 'human_review_required') return 'border-violet-200 bg-violet-50 text-violet-700';
  return 'border-slate-200 bg-slate-100 text-slate-500';
}

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

export default function ResearchInboxPage() {
  const [researchCases, setResearchCases] = useState<ResearchCase[]>([]);
  const [situations, setSituations] = useState<Situation[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [bucketFilter, setBucketFilter] = useState<BucketKey>('all');
  const [readinessFilter, setReadinessFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [hasOpenTasks, setHasOpenTasks] = useState(false);
  const [hasDocuments, setHasDocuments] = useState(false);
  const [hasSources, setHasSources] = useState(false);
  const [legacyOnly, setLegacyOnly] = useState(false);

  useEffect(() => {
    async function load() {
      try {
        setLoading(true);
        setError(null);
        const [casesData, situationsData] = await Promise.all([
          fetchResearchCases(),
          fetchSituations({ include_archived: true }),
        ]);
        setResearchCases(casesData.research_cases);
        setSituations(situationsData.situations);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load research inbox');
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  const situationById = useMemo(() => {
    const map = new Map<string, Situation>();
    for (const situation of situations) map.set(situation.id, situation);
    return map;
  }, [situations]);

  const rows = useMemo(() => (
    researchCases.map(rc => buildInboxRow(rc, rc.situation_id ? situationById.get(rc.situation_id) ?? null : null))
  ), [researchCases, situationById]);

  const bucketCounts = useMemo(() => {
    const counts: Record<BucketKey, number> = {
      all: rows.length, new_detected: 0, needs_official_source: 0, needs_enrichment: 0,
      ready_for_deep_research: 0, monitoring: 0, documented: 0, archived_discarded: 0, legacy_missing_v2: 0,
    };
    for (const row of rows) {
      counts[row.bucket] += 1;
      if (row.legacyMissingV2) counts.legacy_missing_v2 += 1;
    }
    return counts;
  }, [rows]);

  const filteredRows = rows.filter(row => {
    if (bucketFilter === 'legacy_missing_v2') { if (!row.legacyMissingV2) return false; }
    else if (bucketFilter !== 'all' && row.bucket !== bucketFilter) return false;
    if (readinessFilter && row.rc.investment_readiness !== readinessFilter) return false;
    if (statusFilter && row.rc.status !== statusFilter) return false;
    if (hasOpenTasks && row.openTaskCount === 0) return false;
    if (hasDocuments && row.docCount === 0) return false;
    if (hasSources && row.sourceCount === 0) return false;
    if (legacyOnly && !row.legacyMissingV2) return false;
    return true;
  });

  const totalOpenTasks = rows.reduce((sum, row) => sum + row.openTaskCount, 0);
  const totalDocs = rows.reduce((sum, row) => sum + row.docCount, 0);
  const totalSources = rows.reduce((sum, row) => sum + row.sourceCount, 0);

  return (
    <div className="page-container--wide">

      <PageHeader
        title="Research Inbox"
        subtitle="Source-driven intake view — no scans, AI previews, status changes, or cron actions triggered here."
        backHref="/investment/research"
        backLabel="Research Cases"
        actions={
          <div style={{ display: 'flex', gap: '8px' }}>
            <Link href="/investment/evaluations" className="btn btn--secondary btn--sm">Evaluations</Link>
            <Link href="/investment/radar-status" className="btn btn--secondary btn--sm">Radar Status</Link>
          </div>
        }
      />

      <InfoBanner variant="warning">
        V2 transition: source-driven intake and SEC-to-ResearchCase automation are not active yet. Cases shown originate from the Evaluations/SpecialSituation flow.
      </InfoBanner>

      {/* Stats */}
      {!loading && !error && rows.length > 0 && (
        <div className="card" style={{ marginBottom: '24px' }}>
          <MetricRow items={[
            { label: 'Cases', value: rows.length },
            { label: 'Legacy', value: bucketCounts.legacy_missing_v2 },
            { label: 'Open Tasks', value: totalOpenTasks },
            { label: 'Docs', value: totalDocs },
            { label: 'Sources', value: totalSources },
          ]} />
        </div>
      )}

      {/* Filters */}
      <div className="card" style={{ marginBottom: '24px' }}>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', marginBottom: '16px' }}>
          {BUCKETS.map(bucket => {
            const active = bucketFilter === bucket.key;
            return (
              <button
                key={bucket.key}
                onClick={() => setBucketFilter(bucket.key)}
                className={`filter-btn ${active ? 'filter-btn--active' : ''}`}
              >
                {bucket.label}
                <span style={{ marginLeft: 4, opacity: 0.6 }}>{bucketCounts[bucket.key]}</span>
              </button>
            );
          })}
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))', gap: '12px', alignItems: 'center' }}>
          <div>
            <label style={{ display: 'block', fontFamily: 'var(--font-mono)', fontSize: '10px', textTransform: 'uppercase', letterSpacing: '0.1em', color: 'var(--text-faint)', marginBottom: '6px' }}>Readiness</label>
            <select value={readinessFilter} onChange={e => setReadinessFilter(e.target.value)} style={selectStyle}>
              <option value="">All readiness</option>
              {READINESS.map(r => <option key={r} value={r}>{r}</option>)}
            </select>
          </div>
          <div>
            <label style={{ display: 'block', fontFamily: 'var(--font-mono)', fontSize: '10px', textTransform: 'uppercase', letterSpacing: '0.1em', color: 'var(--text-faint)', marginBottom: '6px' }}>Status</label>
            <select value={statusFilter} onChange={e => setStatusFilter(e.target.value)} style={selectStyle}>
              <option value="">All statuses</option>
              {STATUSES.map(s => <option key={s} value={s}>{s}</option>)}
            </select>
          </div>
          <label style={{ display: 'flex', alignItems: 'center', gap: '6px', fontFamily: 'var(--font-mono)', fontSize: '11px', color: 'var(--text-secondary)', cursor: 'pointer' }}>
            <input type="checkbox" checked={hasOpenTasks} onChange={e => setHasOpenTasks(e.target.checked)} />
            Has open tasks
          </label>
          <label style={{ display: 'flex', alignItems: 'center', gap: '6px', fontFamily: 'var(--font-mono)', fontSize: '11px', color: 'var(--text-secondary)', cursor: 'pointer' }}>
            <input type="checkbox" checked={hasDocuments} onChange={e => setHasDocuments(e.target.checked)} />
            Has documents
          </label>
          <label style={{ display: 'flex', alignItems: 'center', gap: '6px', fontFamily: 'var(--font-mono)', fontSize: '11px', color: 'var(--text-secondary)', cursor: 'pointer' }}>
            <input type="checkbox" checked={hasSources} onChange={e => setHasSources(e.target.checked)} />
            Has sources
          </label>
          <label style={{ display: 'flex', alignItems: 'center', gap: '6px', fontFamily: 'var(--font-mono)', fontSize: '11px', color: 'var(--text-secondary)', cursor: 'pointer' }}>
            <input type="checkbox" checked={legacyOnly} onChange={e => setLegacyOnly(e.target.checked)} />
            Legacy / missing V2
          </label>
        </div>
      </div>

      {loading && <LoadingState label="Loading research inbox…" />}
      {error && <ErrorBanner message={error} />}

      {!loading && !error && rows.length === 0 && (
        <div className="empty-state">
          <div className="empty-state-title">No ResearchCases yet</div>
          <div className="empty-state-desc">Create one from an existing evaluation. Source-driven intake is unavailable in this sprint.</div>
        </div>
      )}

      {!loading && !error && rows.length > 0 && filteredRows.length === 0 && (
        <div className="empty-state">
          <div className="empty-state-title">No cases match selected filters</div>
          <div className="empty-state-desc">Clear filters or check archived/discarded and legacy/manual cases.</div>
        </div>
      )}

      {!loading && !error && filteredRows.length > 0 && (
        <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
          <div style={{ overflowX: 'auto' }}>
            <table className="data-table">
              <thead>
                <tr>
                  <th>Case</th>
                  <th>Company / Ticker</th>
                  <th>Situation / Linked</th>
                  <th>Source Origin</th>
                  <th>Intake</th>
                  <th>Evidence</th>
                  <th>Official Source</th>
                  <th>Methodology</th>
                  <th>Readiness</th>
                  <th>Status / Bucket</th>
                  <th style={{ textAlign: 'center' }}>Tasks</th>
                  <th style={{ textAlign: 'center' }}>Docs</th>
                  <th style={{ textAlign: 'center' }}>Src</th>
                  <th>Updated</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {filteredRows.map(row => {
                  const situationLabel = row.situation
                    ? safeText(row.situation.situation_type, safeText(row.situation.filing_type, 'linked'))
                    : row.rc.situation_id ? 'linked' : 'manual';
                  const bucketLabel = BUCKETS.find(b => b.key === row.bucket)?.label ?? row.bucket;
                  return (
                    <tr key={row.rc.id}>
                      <td>
                        <Link href={`/investment/research/${row.rc.id}`} style={{ fontWeight: 500, color: 'var(--text-primary)', textDecoration: 'none' }}>
                          {row.rc.id.slice(0, 8).toUpperCase()}
                        </Link>
                        {row.warnings.length > 0 && (
                          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '3px', marginTop: '4px' }}>
                            {row.warnings.slice(0, 3).map(w => (
                              <InlineBadge key={w} className="border-amber-200 bg-amber-50 text-amber-800">{w}</InlineBadge>
                            ))}
                          </div>
                        )}
                      </td>
                      <td>
                        <div style={{ maxWidth: 160, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', color: 'var(--text-primary)' }} title={row.situation?.company_name ?? undefined}>
                          {safeText(row.situation?.company_name, 'unknown')}
                        </div>
                        <div style={{ fontFamily: 'var(--font-mono)', fontSize: '11px', color: 'var(--text-faint)' }}>{safeText(row.situation?.ticker)}</div>
                      </td>
                      <td>
                        <div style={{ maxWidth: 140, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', color: 'var(--text-muted)' }}>{situationLabel}</div>
                        {row.rc.situation_id ? (
                          <Link href={`/investment/evaluations/${row.rc.situation_id}`} style={{ fontFamily: 'var(--font-mono)', fontSize: '11px', color: 'var(--text-faint)', textDecoration: 'none' }}>
                            {row.rc.situation_id.slice(0, 8).toUpperCase()} →
                          </Link>
                        ) : (
                          <span style={{ fontFamily: 'var(--font-mono)', fontSize: '11px', color: 'var(--text-faint)' }}>no situation</span>
                        )}
                      </td>
                      <td style={{ color: 'var(--text-muted)' }}>{row.sourceOrigin}</td>
                      <td style={{ color: 'var(--text-faint)' }}>{row.intakeMethod}</td>
                      <td><InlineBadge className={evidenceBadgeClass(row.evidence)}>{row.evidence}</InlineBadge></td>
                      <td><InlineBadge className={officialSourceBadgeClass(row.officialSource)}>{row.officialSource}</InlineBadge></td>
                      <td>
                        <InlineBadge className={methodologyBadgeClass(row.methodology)}>{row.methodology}</InlineBadge>
                        {(row.rc.playbook_used || row.rc.checklist_used) && (
                          <div style={{ maxWidth: 140, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', fontFamily: 'var(--font-mono)', fontSize: '10px', color: 'var(--text-faint)', marginTop: 3 }}>
                            {row.rc.playbook_used ?? row.rc.checklist_used}
                          </div>
                        )}
                      </td>
                      <td>
                        <InlineBadge className={row.rc.investment_readiness ? READINESS_BADGE[row.rc.investment_readiness] ?? 'border-slate-200 bg-slate-100 text-slate-500' : 'border-slate-200 bg-slate-100 text-slate-500'}>
                          {safeText(row.rc.investment_readiness, 'none')}
                        </InlineBadge>
                      </td>
                      <td>
                        <div style={{ color: 'var(--text-muted)', marginBottom: 3 }}>{row.rc.status}</div>
                        <InlineBadge className={BUCKET_BADGE[row.bucket]}>{bucketLabel}</InlineBadge>
                        {row.rc.duplicate_status && (
                          <div style={{ marginTop: 3 }}>
                            <InlineBadge className="border-slate-200 bg-slate-50 text-slate-500">{row.rc.duplicate_status}</InlineBadge>
                          </div>
                        )}
                      </td>
                      <td style={{ textAlign: 'center', color: 'var(--text-muted)' }}>
                        <span style={{ fontWeight: row.openTaskCount > 0 ? 600 : 400, color: row.openTaskCount > 0 ? 'var(--text-primary)' : 'var(--text-faint)' }}>{row.openTaskCount}</span>
                        <span style={{ color: 'var(--text-faint)' }}> / {row.taskCount}</span>
                      </td>
                      <td style={{ textAlign: 'center', color: 'var(--text-muted)' }}>{row.docCount}</td>
                      <td style={{ textAlign: 'center', color: 'var(--text-muted)' }}>{row.sourceCount}</td>
                      <td style={{ color: 'var(--text-faint)' }}>
                        <div>{formatDate(row.rc.updated_at)}</div>
                        {row.rc.next_follow_up_at && (
                          <div style={{ fontFamily: 'var(--font-mono)', fontSize: '10px', color: 'var(--text-faint)', marginTop: 2 }}>
                            Follow-up {formatDate(row.rc.next_follow_up_at)}
                          </div>
                        )}
                      </td>
                      <td>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                          <Link href={`/investment/research/${row.rc.id}`} className="btn btn--secondary btn--sm">Open Case</Link>
                          {row.rc.situation_id && (
                            <Link href={`/investment/evaluations/${row.rc.situation_id}`} className="btn btn--ghost btn--sm">Evaluation</Link>
                          )}
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
          <div style={{ padding: '10px 16px', borderTop: '1px solid var(--border-subtle)', fontFamily: 'var(--font-mono)', fontSize: '11px', color: 'var(--text-faint)' }}>
            Showing {filteredRows.length} of {rows.length} ResearchCases — read-only inbox
          </div>
        </div>
      )}

    </div>
  );
}
