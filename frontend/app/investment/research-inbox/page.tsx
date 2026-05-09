'use client';

import { useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import {
  fetchResearchCases,
  fetchSituations,
  type ResearchCase,
  type Situation,
} from '@/lib/api';

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

function hasSecUrl(url: string | null | undefined): boolean {
  return Boolean(url && url.toLowerCase().includes('sec.gov'));
}

function briefString(rc: ResearchCase, key: string): string {
  const value = rc.brief?.[key];
  return typeof value === 'string' ? value.trim() : '';
}

function hasV2Metadata(rc: ResearchCase): boolean {
  return Boolean(
    rc.source_origin_name ||
      rc.investment_source_id ||
      rc.intake_method ||
      rc.connector_key ||
      rc.intake_event_id ||
      rc.evidence_level ||
      rc.official_source_status ||
      rc.methodology_status ||
      rc.playbook_used ||
      rc.checklist_used ||
      rc.course_reference ||
      rc.duplicate_status ||
      rc.next_follow_up_at ||
      rc.discarded_reason,
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
    rc,
    situation,
    bucket: deriveBucket(rc, officialSource, legacyMissingV2),
    sourceOrigin,
    intakeMethod: rc.intake_method ?? 'legacy/manual',
    evidence,
    officialSource,
    methodology,
    legacyMissingV2,
    openTaskCount,
    taskCount: rc.tasks.length,
    docCount: rc.documents.length,
    sourceCount: rc.sources.length,
    warnings,
  };
}

function Badge({ children, className = '' }: { children: React.ReactNode; className?: string }) {
  return (
    <span className={`inline-flex items-center rounded-full border px-2 py-0.5 text-[11px] font-medium ${className}`}>
      {children}
    </span>
  );
}

function evidenceBadgeClass(value: string): string {
  if (['official_filing', 'official_primary', 'official_secondary'].includes(value)) {
    return 'border-green-200 bg-green-50 text-green-700';
  }
  if (value === 'trusted_external' || value === 'mixed') return 'border-blue-200 bg-blue-50 text-blue-700';
  if (value === 'external_unverified') return 'border-amber-200 bg-amber-50 text-amber-800';
  return 'border-slate-200 bg-slate-100 text-slate-500';
}

function officialSourceBadgeClass(value: string): string {
  if (['likely_official', 'official_attached'].includes(value)) {
    return 'border-green-200 bg-green-50 text-green-700';
  }
  if (value === 'official_pending_review') return 'border-amber-200 bg-amber-50 text-amber-800';
  return 'border-slate-200 bg-slate-100 text-slate-500';
}

function methodologyBadgeClass(value: string): string {
  if (['evaluator_ready', 'partial', 'legacy'].includes(value)) {
    return 'border-slate-200 bg-slate-50 text-slate-600';
  }
  if (value === 'human_review_required') return 'border-violet-200 bg-violet-50 text-violet-700';
  return 'border-slate-200 bg-slate-100 text-slate-500';
}

function EmptyState({ title, description }: { title: string; description: string }) {
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-10 text-center shadow-sm">
      <p className="text-sm font-semibold text-slate-700">{title}</p>
      <p className="mt-2 text-sm text-slate-500">{description}</p>
    </div>
  );
}

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
      all: rows.length,
      new_detected: 0,
      needs_official_source: 0,
      needs_enrichment: 0,
      ready_for_deep_research: 0,
      monitoring: 0,
      documented: 0,
      archived_discarded: 0,
      legacy_missing_v2: 0,
    };
    for (const row of rows) {
      counts[row.bucket] += 1;
      if (row.legacyMissingV2) counts.legacy_missing_v2 += 1;
    }
    return counts;
  }, [rows]);

  const filteredRows = rows.filter(row => {
    if (bucketFilter === 'legacy_missing_v2') {
      if (!row.legacyMissingV2) return false;
    } else if (bucketFilter !== 'all' && row.bucket !== bucketFilter) {
      return false;
    }
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
    <div className="min-h-screen bg-slate-50 p-6 text-slate-900 md:p-8">
      <div className="max-w-7xl mx-auto">
        <div className="mb-8 flex items-center justify-between text-sm">
          <Link href="/" className="font-medium text-slate-500 hover:text-slate-900">
            Mission Control
          </Link>
          <div className="flex items-center gap-5">
            <Link href="/investment/research" className="font-medium text-slate-500 hover:text-slate-900">
              Research Cases
            </Link>
            <Link href="/investment/evaluations" className="font-medium text-slate-500 hover:text-slate-900">
              Evaluations
            </Link>
            <Link href="/investment/internal-audit" className="font-medium text-slate-500 hover:text-slate-900">
              Internal Audit
            </Link>
            <Link href="/investment/radar-status" className="font-medium text-slate-500 hover:text-slate-900">
              Radar Status
            </Link>
          </div>
        </div>

        <div className="mb-6">
          <h1 className="mb-2 text-3xl font-semibold tracking-tight text-slate-950">
            Research Inbox
          </h1>
          <p className="max-w-3xl text-sm leading-6 text-slate-600">
            Source-driven intake is not wired yet. This inbox currently shows existing ResearchCases and labels missing V2 metadata as legacy/manual.
          </p>
        </div>

        <div className="mb-6 rounded-lg border border-amber-200 bg-amber-50/80 p-4 shadow-sm">
          <p className="mb-1 text-sm font-semibold text-amber-950">V2 transition notice</p>
          <p className="text-sm leading-6 text-amber-900">
            Source-driven intake is not active yet. SEC-to-ResearchCase automation is not active yet. This page is read-only and current cases may still originate from the Evaluations/SpecialSituation flow.
          </p>
          <p className="mt-2 text-xs leading-5 text-amber-800">
            No scans, AI previews, status changes, source toggles, publishing, or cron actions are triggered from this page.
          </p>
        </div>

        {!loading && !error && rows.length > 0 && (
          <div className="mb-6 grid grid-cols-2 gap-3 md:grid-cols-5">
            <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
              <div className="text-xl font-semibold text-slate-950">{rows.length}</div>
              <div className="mt-1 text-xs font-medium uppercase tracking-wide text-slate-500">Cases</div>
            </div>
            <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
              <div className="text-xl font-semibold text-slate-950">{bucketCounts.legacy_missing_v2}</div>
              <div className="mt-1 text-xs font-medium uppercase tracking-wide text-slate-500">Legacy</div>
            </div>
            <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
              <div className="text-xl font-semibold text-slate-950">{totalOpenTasks}</div>
              <div className="mt-1 text-xs font-medium uppercase tracking-wide text-slate-500">Open tasks</div>
            </div>
            <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
              <div className="text-xl font-semibold text-slate-950">{totalDocs}</div>
              <div className="mt-1 text-xs font-medium uppercase tracking-wide text-slate-500">Docs</div>
            </div>
            <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
              <div className="text-xl font-semibold text-slate-950">{totalSources}</div>
              <div className="mt-1 text-xs font-medium uppercase tracking-wide text-slate-500">Sources</div>
            </div>
          </div>
        )}

        <div className="mb-6 rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
          <div className="mb-4 flex flex-wrap gap-2">
            {BUCKETS.map(bucket => {
              const active = bucketFilter === bucket.key;
              return (
                <button
                  key={bucket.key}
                  onClick={() => setBucketFilter(bucket.key)}
                  className={`rounded-full px-3 py-1.5 text-xs font-medium transition-colors ${
                    active
                      ? 'bg-slate-900 text-white shadow-sm'
                      : 'bg-slate-100 text-slate-600 hover:bg-slate-200 hover:text-slate-900'
                  }`}
                >
                  {bucket.label}
                  <span className={active ? 'ml-2 text-slate-300' : 'ml-2 text-slate-400'}>{bucketCounts[bucket.key]}</span>
                </button>
              );
            })}
          </div>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div>
              <label className="mb-1 block text-xs font-medium uppercase tracking-wide text-slate-500">Readiness</label>
              <select
                value={readinessFilter}
                onChange={e => setReadinessFilter(e.target.value)}
                className="w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm text-slate-700 shadow-sm focus:border-slate-500 focus:outline-none"
              >
                <option value="">All readiness</option>
                {READINESS.map(r => <option key={r} value={r}>{r}</option>)}
              </select>
            </div>
            <div>
              <label className="mb-1 block text-xs font-medium uppercase tracking-wide text-slate-500">Status</label>
              <select
                value={statusFilter}
                onChange={e => setStatusFilter(e.target.value)}
                className="w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm text-slate-700 shadow-sm focus:border-slate-500 focus:outline-none"
              >
                <option value="">All statuses</option>
                {STATUSES.map(s => <option key={s} value={s}>{s}</option>)}
              </select>
            </div>
            <label className="flex items-center gap-2 text-sm text-slate-600">
              <input type="checkbox" checked={hasOpenTasks} onChange={e => setHasOpenTasks(e.target.checked)} className="accent-slate-700" />
              Has open tasks
            </label>
            <label className="flex items-center gap-2 text-sm text-slate-600">
              <input type="checkbox" checked={hasDocuments} onChange={e => setHasDocuments(e.target.checked)} className="accent-slate-700" />
              Has documents
            </label>
            <label className="flex items-center gap-2 text-sm text-slate-600">
              <input type="checkbox" checked={hasSources} onChange={e => setHasSources(e.target.checked)} className="accent-slate-700" />
              Has sources
            </label>
            <label className="flex items-center gap-2 text-sm text-slate-600">
              <input type="checkbox" checked={legacyOnly} onChange={e => setLegacyOnly(e.target.checked)} className="accent-slate-700" />
              Legacy / missing V2 metadata
            </label>
          </div>
        </div>

        {loading && (
          <div className="rounded-lg border border-slate-200 bg-white p-8 text-center shadow-sm">
            <div className="mb-4 inline-block h-8 w-8 animate-spin rounded-full border-2 border-slate-300 border-t-slate-700"></div>
            <p className="text-sm text-slate-500">Loading research inbox...</p>
          </div>
        )}

        {error && (
          <div className="mb-6 rounded-lg border border-red-200 bg-red-50 p-4 shadow-sm">
            <p className="text-sm text-red-700">Error: {error}</p>
          </div>
        )}

        {!loading && !error && rows.length === 0 && (
          <EmptyState
            title="No ResearchCases yet."
            description="Create one from an existing evaluation. Source-driven intake is unavailable in this sprint."
          />
        )}

        {!loading && !error && rows.length > 0 && filteredRows.length === 0 && (
          <EmptyState
            title="No cases match selected filters."
            description="Clear filters or check archived/discarded and legacy/manual cases."
          />
        )}

        {!loading && !error && filteredRows.length > 0 && (
          <div className="overflow-hidden rounded-lg border border-slate-200 bg-white shadow-sm">
            <div className="overflow-x-auto">
              <table className="min-w-full border-separate border-spacing-0">
                <thead className="border-b border-slate-200 bg-slate-100">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">Case</th>
                    <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">Company / ticker</th>
                    <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">Situation / linked situation</th>
                    <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">Source origin</th>
                    <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">Intake method</th>
                    <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">Evidence</th>
                    <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">Official source</th>
                    <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">Methodology</th>
                    <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">Readiness</th>
                    <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">Status / bucket</th>
                    <th className="px-4 py-3 text-center text-xs font-semibold uppercase tracking-wide text-slate-500">Tasks</th>
                    <th className="px-4 py-3 text-center text-xs font-semibold uppercase tracking-wide text-slate-500">Docs</th>
                    <th className="px-4 py-3 text-center text-xs font-semibold uppercase tracking-wide text-slate-500">Sources</th>
                    <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">Updated</th>
                    <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {filteredRows.map(row => {
                    const situationLabel = row.situation
                      ? `${safeText(row.situation.situation_type, safeText(row.situation.filing_type, 'linked situation'))}`
                      : row.rc.situation_id
                        ? 'linked situation'
                        : 'manual case';
                    const bucketLabel = BUCKETS.find(b => b.key === row.bucket)?.label ?? row.bucket;
                    return (
                      <tr key={row.rc.id} className="align-top transition-colors hover:bg-slate-50">
                        <td className="px-4 py-4 text-sm">
                          <Link href={`/investment/research/${row.rc.id}`} className="font-semibold text-slate-900 hover:text-slate-700 hover:underline">
                            Case {row.rc.id.slice(0, 8).toUpperCase()}
                          </Link>
                          {row.warnings.length > 0 && (
                            <div className="mt-2 flex flex-wrap gap-1">
                              {row.warnings.slice(0, 3).map(w => (
                                <Badge key={w} className="border-amber-200 bg-amber-50 text-amber-800">{w}</Badge>
                              ))}
                            </div>
                          )}
                        </td>
                        <td className="px-4 py-4 text-sm text-slate-700">
                          <div className="max-w-[180px] truncate" title={row.situation?.company_name ?? undefined}>
                            {safeText(row.situation?.company_name, 'unknown')}
                          </div>
                          <div className="text-xs text-slate-400">{safeText(row.situation?.ticker)}</div>
                        </td>
                        <td className="px-4 py-4 text-sm text-slate-600">
                          <div className="max-w-[170px] truncate">{situationLabel}</div>
                          {row.rc.situation_id ? (
                            <Link href={`/investment/evaluations/${row.rc.situation_id}`} className="text-xs font-medium text-slate-500 hover:text-slate-900">
                              {row.rc.situation_id.slice(0, 8).toUpperCase()} →
                            </Link>
                          ) : (
                            <span className="text-xs text-slate-400">no linked situation</span>
                          )}
                        </td>
                        <td className="px-4 py-4 text-sm text-slate-600">{row.sourceOrigin}</td>
                        <td className="px-4 py-4 text-sm text-slate-500">{row.intakeMethod}</td>
                        <td className="px-4 py-4">
                          <Badge className={evidenceBadgeClass(row.evidence)}>
                            {row.evidence}
                          </Badge>
                        </td>
                        <td className="px-4 py-4">
                          <Badge className={officialSourceBadgeClass(row.officialSource)}>
                            {row.officialSource}
                          </Badge>
                        </td>
                        <td className="px-4 py-4">
                          <Badge className={methodologyBadgeClass(row.methodology)}>
                            {row.methodology}
                          </Badge>
                          {(row.rc.playbook_used || row.rc.checklist_used) && (
                            <div className="mt-1 max-w-[160px] truncate text-[11px] text-slate-400">
                              {row.rc.playbook_used ?? row.rc.checklist_used}
                            </div>
                          )}
                        </td>
                        <td className="px-4 py-4">
                          <Badge className={row.rc.investment_readiness ? READINESS_BADGE[row.rc.investment_readiness] ?? 'border-slate-200 bg-slate-100 text-slate-500' : 'border-slate-200 bg-slate-100 text-slate-500'}>
                            {safeText(row.rc.investment_readiness, 'none')}
                          </Badge>
                        </td>
                        <td className="px-4 py-4 text-sm">
                          <div className="mb-1 text-slate-600">{row.rc.status}</div>
                          <Badge className={BUCKET_BADGE[row.bucket]}>{bucketLabel}</Badge>
                          {row.rc.duplicate_status && (
                            <div className="mt-1">
                              <Badge className="border-slate-200 bg-slate-50 text-slate-500">{row.rc.duplicate_status}</Badge>
                            </div>
                          )}
                        </td>
                        <td className="px-4 py-4 text-center text-sm text-slate-600">
                          <span className={row.openTaskCount > 0 ? 'font-semibold text-slate-900' : 'text-slate-400'}>{row.openTaskCount}</span>
                          <span className="text-slate-400"> / {row.taskCount}</span>
                        </td>
                        <td className="px-4 py-4 text-center text-sm text-slate-600">{row.docCount}</td>
                        <td className="px-4 py-4 text-center text-sm text-slate-600">{row.sourceCount}</td>
                        <td className="px-4 py-4 text-sm text-slate-500">
                          <div>{formatDate(row.rc.updated_at)}</div>
                          {row.rc.next_follow_up_at && (
                            <div className="mt-1 text-[11px] text-slate-400">
                              Follow-up {formatDate(row.rc.next_follow_up_at)}
                            </div>
                          )}
                        </td>
                        <td className="px-4 py-4 text-sm">
                          <div className="flex flex-col gap-1">
                            <Link href={`/investment/research/${row.rc.id}`} className="font-medium text-slate-900 hover:text-slate-600">
                              Open ResearchCase
                            </Link>
                            {row.rc.situation_id && (
                              <Link href={`/investment/evaluations/${row.rc.situation_id}`} className="text-slate-500 hover:text-slate-900">
                                Open Evaluation
                              </Link>
                            )}
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
            <div className="border-t border-slate-200 bg-slate-50 px-4 py-3">
              <p className="text-xs text-slate-500">
                Showing {filteredRows.length} of {rows.length} ResearchCases.
              </p>
            </div>
          </div>
        )}

        <div className="mt-6 text-center text-xs text-slate-500">
          Read-only inbox — no scans, AI previews, source toggles, publishing, or cron actions are triggered from this page.
        </div>
      </div>
    </div>
  );
}
