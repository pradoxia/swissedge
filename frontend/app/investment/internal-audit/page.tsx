'use client';

import { useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import {
  fetchResearchCases,
  fetchSources,
  fetchAgent,
  type ResearchCase,
  type InvestmentSource,
  type AgentDetail,
} from '@/lib/api';

// ── Audit helpers ─────────────────────────────────────────────────────────────

function hasV2Metadata(rc: ResearchCase): boolean {
  return Boolean(
    rc.source_origin_name || rc.investment_source_id || rc.intake_method ||
    rc.connector_key || rc.intake_event_id || rc.evidence_level ||
    rc.official_source_status || rc.methodology_status ||
    rc.playbook_used || rc.checklist_used || rc.course_reference ||
    rc.duplicate_status || rc.next_follow_up_at || rc.discarded_reason,
  );
}

function isMissingMethodology(rc: ResearchCase): boolean {
  const s = rc.methodology_status;
  return (!s || s === 'unknown') && !rc.playbook_used && !rc.checklist_used && !rc.course_reference;
}

function isMissingOfficialSource(rc: ResearchCase): boolean {
  const s = rc.official_source_status;
  return !s || s === 'unknown';
}

// ── Types ─────────────────────────────────────────────────────────────────────

interface AuditFinding {
  id: string;
  finding: string;
  severity: 'high' | 'medium' | 'low' | 'info';
  count: number | null;
  whyItMatters: string;
  nextAction: string;
}

interface CaseWarning {
  rc: ResearchCase;
  missingV2: boolean;
  missingMethodology: boolean;
  missingOfficialSource: boolean;
  noTasks: boolean;
  noDocs: boolean;
  noSources: boolean;
  isHighSeverity: boolean;
}

// ── UI primitives ─────────────────────────────────────────────────────────────

function SeverityBadge({ severity }: { severity: AuditFinding['severity'] }) {
  const cls = {
    high:   'border-red-200 bg-red-50 text-red-700',
    medium: 'border-amber-200 bg-amber-50 text-amber-800',
    low:    'border-slate-200 bg-slate-100 text-slate-500',
    info:   'border-blue-200 bg-blue-50 text-blue-700',
  }[severity];
  return (
    <span className={`inline-flex items-center rounded-full border px-2 py-0.5 text-[11px] font-medium ${cls}`}>
      {severity.toUpperCase()}
    </span>
  );
}

function StatCard({ value, label, highlight = false }: { value: number; label: string; highlight?: boolean }) {
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
      <div className={`text-xl font-semibold ${highlight && value > 0 ? 'text-amber-700' : 'text-slate-950'}`}>
        {value}
      </div>
      <div className="mt-1 text-xs font-medium uppercase tracking-wide text-slate-500">{label}</div>
    </div>
  );
}

function EmptyState({ title, description }: { title: string; description: string }) {
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-8 text-center shadow-sm">
      <p className="text-sm font-semibold text-slate-700">{title}</p>
      <p className="mt-1 text-sm text-slate-500">{description}</p>
    </div>
  );
}

// ── Page ──────────────────────────────────────────────────────────────────────

export default function InternalAuditPage() {
  const [cases, setCases] = useState<ResearchCase[]>([]);
  const [sources, setSources] = useState<InvestmentSource[]>([]);
  const [scannerAgent, setScannerAgent] = useState<AgentDetail | null>(null);
  const [scannerError, setScannerError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      try {
        setLoading(true);
        setError(null);
        const [casesData, sourcesData] = await Promise.all([
          fetchResearchCases(),
          fetchSources(),
        ]);
        setCases(casesData.research_cases);
        setSources(sourcesData.sources);

        try {
          const agent = await fetchAgent('investment_scanner');
          setScannerAgent(agent);
        } catch (e) {
          setScannerError(e instanceof Error ? e.message : 'unavailable');
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load audit data');
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  // ── Case-level warnings ──
  const caseWarnings = useMemo<CaseWarning[]>(() =>
    cases.map(rc => {
      const missingV2 = !hasV2Metadata(rc);
      const missingMethodology = isMissingMethodology(rc);
      const missingOfficialSource = isMissingOfficialSource(rc);
      const noTasks = rc.tasks.length === 0;
      const noDocs = rc.documents.length === 0;
      const noSources = rc.sources.length === 0;
      const isHighSeverity = rc.investment_readiness === 'candidate' && (missingMethodology || missingOfficialSource);
      return { rc, missingV2, missingMethodology, missingOfficialSource, noTasks, noDocs, noSources, isHighSeverity };
    }),
  [cases]);

  // ── Summary counts ──
  const counts = useMemo(() => ({
    total: cases.length,
    missingV2: caseWarnings.filter(w => w.missingV2).length,
    missingMethodology: caseWarnings.filter(w => w.missingMethodology).length,
    missingOfficialSource: caseWarnings.filter(w => w.missingOfficialSource).length,
    noTasks: caseWarnings.filter(w => w.noTasks).length,
    noDocs: caseWarnings.filter(w => w.noDocs).length,
    noSources: caseWarnings.filter(w => w.noSources).length,
    highSeverity: caseWarnings.filter(w => w.isHighSeverity).length,
    archivedNoReason: cases.filter(rc => rc.status === 'archived' && !rc.discarded_reason).length,
    activeSources: sources.filter(s => s.active).length,
    totalSources: sources.length,
  }), [cases, sources, caseWarnings]);

  // ── Scanner diagnostics: look for source_registry_used in last run's api_calls_made ──
  const scannerDiagnostics = useMemo(() => {
    if (!scannerAgent?.recent_runs?.length) return null;
    const lastRun = scannerAgent.recent_runs[0];
    if (!lastRun.api_calls_made) return null;
    const calls = Array.isArray(lastRun.api_calls_made)
      ? lastRun.api_calls_made
      : [lastRun.api_calls_made];
    for (const call of calls) {
      if (call && typeof call === 'object' && 'source_registry_used' in call) {
        return {
          source_registry_used: call.source_registry_used,
          run_at: lastRun.finished_at,
        };
      }
    }
    return null;
  }, [scannerAgent]);

  // ── Audit findings ──
  const findings = useMemo<AuditFinding[]>(() => [
    {
      id: 'missing_v2',
      finding: 'ResearchCases missing all V2 metadata',
      severity: 'medium',
      count: counts.missingV2,
      whyItMatters: 'These cases have no source origin, intake method, or evidence level. They cannot be triaged accurately by the Research Inbox.',
      nextAction: 'Populate via source-driven intake in a future sprint. Legacy cases remain valid but should be monitored.',
    },
    {
      id: 'missing_methodology',
      finding: 'ResearchCases missing methodology reference',
      severity: counts.highSeverity > 0 ? 'high' : 'medium',
      count: counts.missingMethodology,
      whyItMatters: 'Cases without playbook, checklist, or methodology status are not grounded in course methodology. Candidate cases need methodology to be research-ready.',
      nextAction: 'Attach playbook, checklist, or methodology status manually or via Course Methodology Agent in a future sprint.',
    },
    {
      id: 'missing_official_source',
      finding: 'ResearchCases missing official source status',
      severity: 'medium',
      count: counts.missingOfficialSource,
      whyItMatters: 'Without a known official-source status, it is unclear whether the case has verifiable primary evidence.',
      nextAction: 'Set official_source_status manually or via Official Source Verification Agent.',
    },
    {
      id: 'no_tasks',
      finding: 'ResearchCases with no tasks',
      severity: 'medium',
      count: counts.noTasks,
      whyItMatters: 'Cases without tasks have no defined next verification steps.',
      nextAction: 'Add verification tasks for active cases. Archive cases that are no longer being investigated.',
    },
    {
      id: 'no_docs',
      finding: 'ResearchCases with no documents',
      severity: 'medium',
      count: counts.noDocs,
      whyItMatters: 'Cases without document metadata have no recorded primary or secondary evidence.',
      nextAction: 'Attach document URLs (metadata only) for SEC filings, press releases, or news articles.',
    },
    {
      id: 'no_sources',
      finding: 'ResearchCases with no recorded sources',
      severity: 'medium',
      count: counts.noSources,
      whyItMatters: 'Cases without recorded sources cannot be traced to a signal origin.',
      nextAction: 'Record the source that surfaced this case, even if it is a manual note.',
    },
    {
      id: 'candidate_no_methodology',
      finding: 'Candidate cases missing methodology',
      severity: 'high',
      count: counts.highSeverity,
      whyItMatters: 'A case marked candidate for deep research should be grounded in course methodology. Without it, the readiness label is unverified.',
      nextAction: 'Attach playbook and methodology status before treating a case as research-ready.',
    },
    {
      id: 'archived_no_reason',
      finding: 'Archived cases without discarded_reason',
      severity: 'low',
      count: counts.archivedNoReason,
      whyItMatters: 'Archived cases without a reason are harder to audit and learn from over time.',
      nextAction: 'Add a short discarded_reason note when archiving a case.',
    },
    {
      id: 'source_registry_not_wired',
      finding: 'Source registry not wired into scanner execution',
      severity: 'info',
      count: null,
      whyItMatters: 'investment_sources rows exist but the scanner does not use them. Source registry toggles affect only the registry table, not scanner behavior.',
      nextAction: 'Wire investment_sources into the SEC EDGAR intake path in a future sprint.',
    },
    {
      id: 'scanner_diagnostics',
      finding: 'Scanner source_registry_used diagnostics',
      severity: 'info',
      count: null,
      whyItMatters: 'Scanner diagnostics should record whether the source registry drove the scan.',
      nextAction: scannerAgent
        ? (scannerDiagnostics
          ? 'Diagnostics available — see Architecture Warnings section below.'
          : 'Last scanner run has no source_registry_used field in diagnostics.')
        : 'Scanner diagnostics unavailable — check Radar Status for scanner observability.',
    },
  ], [counts, scannerAgent, scannerDiagnostics]);

  const flaggedCases = caseWarnings.filter(w =>
    w.missingV2 || w.missingMethodology || w.missingOfficialSource || w.noTasks || w.noDocs || w.noSources,
  );

  return (
    <div className="min-h-screen bg-slate-50 p-6 text-slate-900 md:p-8">
      <div className="max-w-7xl mx-auto">

        {/* Nav */}
        <div className="mb-8 flex items-center justify-between text-sm">
          <Link href="/" className="font-medium text-slate-500 hover:text-slate-900">
            Mission Control
          </Link>
          <div className="flex items-center gap-5">
            <Link href="/investment/research-inbox" className="font-medium text-slate-500 hover:text-slate-900">
              Research Inbox
            </Link>
            <Link href="/investment/research" className="font-medium text-slate-500 hover:text-slate-900">
              Research Cases
            </Link>
            <Link href="/investment/radar-status" className="font-medium text-slate-500 hover:text-slate-900">
              Radar Status
            </Link>
          </div>
        </div>

        {/* Header */}
        <div className="mb-6">
          <h1 className="mb-2 text-3xl font-semibold tracking-tight text-slate-950">Internal Audit</h1>
          <p className="max-w-3xl text-sm leading-6 text-slate-600">
            Read-only architecture and data-quality checks for Investment Platform V2.
            Findings are computed client-side from existing API data.
          </p>
        </div>

        {/* Guardrail banner */}
        <div className="mb-6 rounded-lg border border-slate-200 bg-slate-100 p-4 shadow-sm">
          <p className="text-sm text-slate-600">
            This page does not mutate data, trigger scans, call AI, change cron, or alter sources.
            All checks are read-only client-side computations over existing ResearchCase and InvestmentSource data.
          </p>
        </div>

        {/* Loading */}
        {loading && (
          <div className="rounded-lg border border-slate-200 bg-white p-8 text-center shadow-sm">
            <div className="mb-4 inline-block h-8 w-8 animate-spin rounded-full border-2 border-slate-300 border-t-slate-700" />
            <p className="text-sm text-slate-500">Loading audit data...</p>
          </div>
        )}

        {/* Error */}
        {error && (
          <div className="mb-6 rounded-lg border border-red-200 bg-red-50 p-4 shadow-sm">
            <p className="text-sm text-red-700">Error: {error}</p>
          </div>
        )}

        {!loading && !error && (
          <>
            {/* Summary cards */}
            <div className="mb-6 grid grid-cols-2 gap-3 sm:grid-cols-4 lg:grid-cols-7">
              <StatCard value={counts.total} label="Total cases" />
              <StatCard value={counts.missingV2} label="Missing V2 metadata" highlight />
              <StatCard value={counts.missingMethodology} label="Missing methodology" highlight />
              <StatCard value={counts.missingOfficialSource} label="No official source" highlight />
              <StatCard value={counts.noTasks} label="No tasks" highlight />
              <StatCard value={counts.noDocs} label="No documents" highlight />
              <StatCard value={counts.noSources} label="No sources" highlight />
            </div>

            {/* Architecture warnings */}
            <div className="mb-6 space-y-3">
              <div className="rounded-lg border border-amber-200 bg-amber-50 p-4 shadow-sm">
                <p className="mb-1 text-sm font-semibold text-amber-950">Source registry not wired into scanner</p>
                <p className="text-sm leading-6 text-amber-900">
                  <code className="rounded bg-amber-100 px-1 text-xs">investment_sources</code> has{' '}
                  {counts.activeSources} active source(s) of {counts.totalSources} total, but the scanner does not read
                  from this registry. Current scanner uses a hardcoded{' '}
                  <code className="rounded bg-amber-100 px-1 text-xs">SECEdgarAdapter</code>.
                  Source registry toggles affect only the registry table — not scanner behavior — until the V2 intake path is wired.
                </p>
              </div>

              <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
                <p className="mb-1 text-sm font-semibold text-slate-800">Scanner diagnostics</p>
                {scannerError && (
                  <p className="text-sm text-slate-500">
                    Scanner agent unavailable on this page ({scannerError}). Check{' '}
                    <Link href="/investment/radar-status" className="underline hover:text-slate-900">Radar Status</Link>{' '}
                    for scanner observability.
                  </p>
                )}
                {!scannerError && !scannerAgent && (
                  <p className="text-sm text-slate-500">Scanner agent data unavailable.</p>
                )}
                {scannerAgent && !scannerDiagnostics && (
                  <p className="text-sm text-slate-500">
                    Scanner agent found ({scannerAgent.stats.total_runs} total runs, last:{' '}
                    {scannerAgent.stats.last_run
                      ? new Date(scannerAgent.stats.last_run).toLocaleString('en-CH')
                      : 'never'}
                    ). Latest run has no{' '}
                    <code className="rounded bg-slate-100 px-1 text-xs">source_registry_used</code> field in diagnostics.
                  </p>
                )}
                {scannerAgent && scannerDiagnostics && (
                  <p className="text-sm text-slate-700">
                    Latest scanner run:{' '}
                    <code className="rounded bg-slate-100 px-1 text-xs">
                      source_registry_used = {String(scannerDiagnostics.source_registry_used)}
                    </code>
                    {scannerDiagnostics.run_at && (
                      <span className="text-slate-500">
                        {' '}· run at {new Date(scannerDiagnostics.run_at).toLocaleString('en-CH')}
                      </span>
                    )}
                  </p>
                )}
              </div>
            </div>

            {/* Audit findings table */}
            <div className="mb-6 overflow-hidden rounded-lg border border-slate-200 bg-white shadow-sm">
              <div className="border-b border-slate-200 bg-slate-50 px-4 py-3">
                <p className="text-sm font-semibold text-slate-800">Audit Findings</p>
              </div>
              <div className="overflow-x-auto">
                <table className="min-w-full border-separate border-spacing-0">
                  <thead className="border-b border-slate-200 bg-slate-100">
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">Finding</th>
                      <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">Severity</th>
                      <th className="px-4 py-3 text-center text-xs font-semibold uppercase tracking-wide text-slate-500">Count</th>
                      <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">Why it matters</th>
                      <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">Suggested next action</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {findings.map(f => (
                      <tr key={f.id} className="align-top hover:bg-slate-50">
                        <td className="px-4 py-3 text-sm font-medium text-slate-800">{f.finding}</td>
                        <td className="px-4 py-3"><SeverityBadge severity={f.severity} /></td>
                        <td className="px-4 py-3 text-center text-sm">
                          {f.count !== null ? (
                            <span className={f.count > 0 && f.severity !== 'info' ? 'font-semibold text-amber-700' : 'text-slate-600'}>
                              {f.count}
                            </span>
                          ) : (
                            <span className="text-slate-400">—</span>
                          )}
                        </td>
                        <td className="max-w-xs px-4 py-3 text-sm text-slate-600">{f.whyItMatters}</td>
                        <td className="max-w-xs px-4 py-3 text-sm text-slate-500">{f.nextAction}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Case-level warnings */}
            <div className="mb-6">
              <div className="mb-3">
                <p className="text-sm font-semibold text-slate-800">
                  Case-level Warnings — {flaggedCases.length} of {cases.length} cases flagged
                </p>
              </div>

              {flaggedCases.length === 0 ? (
                <EmptyState
                  title="No case-level warnings."
                  description="All cases pass the current data-quality checks."
                />
              ) : (
                <div className="overflow-hidden rounded-lg border border-slate-200 bg-white shadow-sm">
                  <div className="overflow-x-auto">
                    <table className="min-w-full border-separate border-spacing-0">
                      <thead className="border-b border-slate-200 bg-slate-100">
                        <tr>
                          <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">Case</th>
                          <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">Status / readiness</th>
                          <th className="px-4 py-3 text-center text-xs font-semibold uppercase tracking-wide text-slate-500">V2 missing</th>
                          <th className="px-4 py-3 text-center text-xs font-semibold uppercase tracking-wide text-slate-500">Methodology</th>
                          <th className="px-4 py-3 text-center text-xs font-semibold uppercase tracking-wide text-slate-500">Official src</th>
                          <th className="px-4 py-3 text-center text-xs font-semibold uppercase tracking-wide text-slate-500">Tasks</th>
                          <th className="px-4 py-3 text-center text-xs font-semibold uppercase tracking-wide text-slate-500">Docs</th>
                          <th className="px-4 py-3 text-center text-xs font-semibold uppercase tracking-wide text-slate-500">Sources</th>
                          <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">Action</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-100">
                        {flaggedCases.map(w => (
                          <tr
                            key={w.rc.id}
                            className={`align-middle hover:bg-slate-50 ${w.isHighSeverity ? 'bg-red-50/40' : ''}`}
                          >
                            <td className="px-4 py-3 text-sm font-mono font-semibold text-slate-800">
                              {w.rc.id.slice(0, 8).toUpperCase()}
                            </td>
                            <td className="px-4 py-3 text-sm">
                              <div className="text-slate-700">{w.rc.status}</div>
                              <div className="text-xs text-slate-400">{w.rc.investment_readiness ?? '—'}</div>
                            </td>
                            <td className="px-4 py-3 text-center text-xs">
                              {w.missingV2
                                ? <span className="font-medium text-amber-600">missing</span>
                                : <span className="text-slate-300">ok</span>}
                            </td>
                            <td className="px-4 py-3 text-center text-xs">
                              {w.missingMethodology
                                ? <span className={`font-medium ${w.isHighSeverity ? 'text-red-600' : 'text-amber-600'}`}>missing</span>
                                : <span className="text-slate-300">ok</span>}
                            </td>
                            <td className="px-4 py-3 text-center text-xs">
                              {w.missingOfficialSource
                                ? <span className="font-medium text-amber-600">unknown</span>
                                : <span className="text-slate-300">ok</span>}
                            </td>
                            <td className="px-4 py-3 text-center text-sm">
                              {w.noTasks
                                ? <span className="font-semibold text-amber-600">0</span>
                                : <span className="text-slate-600">{w.rc.tasks.length}</span>}
                            </td>
                            <td className="px-4 py-3 text-center text-sm">
                              {w.noDocs
                                ? <span className="font-semibold text-amber-600">0</span>
                                : <span className="text-slate-600">{w.rc.documents.length}</span>}
                            </td>
                            <td className="px-4 py-3 text-center text-sm">
                              {w.noSources
                                ? <span className="font-semibold text-amber-600">0</span>
                                : <span className="text-slate-600">{w.rc.sources.length}</span>}
                            </td>
                            <td className="px-4 py-3 text-sm">
                              <Link
                                href={`/investment/research/${w.rc.id}`}
                                className="font-medium text-slate-700 hover:text-slate-900 hover:underline"
                              >
                                Open →
                              </Link>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                  <div className="border-t border-slate-200 bg-slate-50 px-4 py-3">
                    <p className="text-xs text-slate-500">
                      {flaggedCases.length} case(s) with at least one data-quality warning. Links open the ResearchCase workspace.
                    </p>
                  </div>
                </div>
              )}
            </div>

            <div className="mt-6 text-center text-xs text-slate-500">
              Read-only audit — no mutations, scans, AI calls, cron changes, or source toggles are triggered from this page.
            </div>
          </>
        )}
      </div>
    </div>
  );
}
