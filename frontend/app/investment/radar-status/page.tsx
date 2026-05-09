'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import {
  fetchAgent,
  fetchSources,
  fetchCronUpcoming,
} from '@/lib/api';

// Never render a raw object into JSX. Converts any value to a display string.
function safeText(value: unknown, fallback = '—'): string {
  if (value === null || value === undefined) return fallback;
  if (typeof value === 'string') return value || fallback;
  if (typeof value === 'number' || typeof value === 'boolean') return String(value);
  if (typeof value === 'object') {
    try { return JSON.stringify(value); } catch { return '[object]'; }
  }
  return fallback;
}

function safeStr(value: unknown): string {
  return safeText(value, '');
}

function safeArr<T>(value: unknown): T[] {
  return Array.isArray(value) ? value : [];
}

function formatDate(iso: unknown): string {
  const s = safeText(iso);
  if (s === '—') return '—';
  try {
    return new Date(s).toLocaleString('en-CH', {
      timeZone: 'Europe/Zurich',
      year: 'numeric', month: '2-digit', day: '2-digit',
      hour: '2-digit', minute: '2-digit',
    });
  } catch {
    return s;
  }
}

function durationLabel(ms: unknown): string {
  const n = typeof ms === 'number' ? ms : null;
  if (!n) return '—';
  if (n < 1000) return `${n}ms`;
  const s = Math.round(n / 100) / 10;
  if (s < 60) return `${s}s`;
  return `${Math.floor(s / 60)}m ${Math.round(s % 60)}s`;
}

function statusBadgeClass(status: unknown): string {
  const s = safeStr(status).toLowerCase();
  if (s === 'success')                  return 'status-badge status-badge--active';
  if (s === 'failed' || s === 'error')  return 'status-badge status-badge--preview';
  if (s === 'running')                  return 'status-badge status-badge--partial';
  return 'status-badge status-badge--readonly';
}

function StatusBadge({ status }: { status: unknown }) {
  return (
    <span className={statusBadgeClass(status)}>
      {safeStr(status).toUpperCase() || '?'}
    </span>
  );
}

function StatusDot({ status }: { status: unknown }) {
  const s = safeStr(status).toLowerCase();
  const cls =
    s === 'success' ? 'status-dot status-dot--active' :
    s === 'failed' || s === 'error' ? 'status-dot status-dot--warning' :
    s === 'running' ? 'status-dot status-dot--active' :
    'status-dot status-dot--muted';
  return <span className={cls} style={{ marginRight: '8px' }} />;
}

function Row({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div style={{ display: 'flex', justifyContent: 'space-between', fontFamily: 'var(--font-mono)', fontSize: '12px' }}>
      <span style={{ color: 'var(--text-muted)' }}>{label}</span>
      <span style={{ color: 'var(--text-secondary)', textAlign: 'right', marginLeft: '16px', maxWidth: '220px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{value}</span>
    </div>
  );
}

function friendlySchedule(cron: string): string {
  const p = cron.trim().split(/\s+/);
  if (p.length < 5) return cron;
  const [min, hour, , , dow] = p;
  if (min === '0' && hour === '*/6') return 'Every 6 hours';
  if (min === '0' && hour === '*/12') return 'Every 12 hours';
  if (min === '0' && hour === '*/4') return 'Every 4 hours';
  if (min === '0' && hour === '*/2') return 'Every 2 hours';
  if (min === '*/30' && hour === '*') return 'Every 30 minutes';
  if (min === '*/15' && hour === '*') return 'Every 15 minutes';
  if (/^\d+$/.test(min) && /^\d+$/.test(hour)) {
    const h = hour.padStart(2, '0');
    const m = min.padStart(2, '0');
    if (dow === '*') return `Daily at ${h}:${m}`;
    const days: Record<string, string> = { '1':'Mon','2':'Tue','3':'Wed','4':'Thu','5':'Fri','6':'Sat','0':'Sun' };
    if (days[dow]) return `${days[dow]} at ${h}:${m}`;
  }
  if (/^\d+$/.test(min) && hour.startsWith('*/')) {
    const interval = hour.slice(2);
    return `Every ${interval}h at minute ${min}`;
  }
  return cron;
}

function normalizeApiCalls(value: unknown): Record<string, unknown>[] {
  if (Array.isArray(value)) return value.filter((v): v is Record<string, unknown> => v !== null && typeof v === 'object');
  if (value !== null && typeof value === 'object') return [value as Record<string, unknown>];
  return [];
}

function numberText(value: unknown): string {
  return typeof value === 'number' ? value.toLocaleString('en-CH') : safeText(value);
}

export default function RadarStatusPage() {
  const [agentRaw, setAgentRaw] = useState<unknown>(null);
  const [sourcesRaw, setSourcesRaw] = useState<unknown>(null);
  const [cronRaw, setCronRaw] = useState<unknown>(null);
  const [loadingAgent, setLoadingAgent] = useState(true);
  const [loadingSources, setLoadingSources] = useState(true);
  const [loadingCron, setLoadingCron] = useState(true);
  const [agentError, setAgentError] = useState<string | null>(null);
  const [sourcesError, setSourcesError] = useState<string | null>(null);
  const [cronError, setCronError] = useState<string | null>(null);

  useEffect(() => {
    fetchAgent('investment_scanner')
      .then((d) => setAgentRaw(d))
      .catch((e) => setAgentError(String(e?.message ?? e ?? 'Failed')))
      .finally(() => setLoadingAgent(false));

    fetchSources()
      .then((d) => setSourcesRaw(d))
      .catch((e) => setSourcesError(String(e?.message ?? e ?? 'Failed')))
      .finally(() => setLoadingSources(false));

    fetchCronUpcoming(3)
      .then((d) => setCronRaw(d))
      .catch((e) => setCronError(String(e?.message ?? e ?? 'Failed')))
      .finally(() => setLoadingCron(false));
  }, []);

  // ── Normalise agent ────────────────────────────────────────────────────────
  const agent = agentRaw && typeof agentRaw === 'object' ? agentRaw as Record<string, unknown> : null;
  const agentStats = agent?.stats && typeof agent.stats === 'object' ? agent.stats as Record<string, unknown> : {};
  const recentRuns = safeArr<Record<string, unknown>>(agent?.recent_runs);
  const lastRun = recentRuns[0] ?? null;
  const lastSuccess = recentRuns.find(r => safeStr(r?.status).toLowerCase() === 'success') ?? null;
  const lastFailed = recentRuns.find(r => {
    const s = safeStr(r?.status).toLowerCase();
    return s === 'failed' || s === 'error';
  }) ?? null;
  const lastRunApiCalls = normalizeApiCalls(lastRun?.api_calls_made);
  const lastSecCall = lastRunApiCalls.find(call => safeStr(call.source) === 'sec_edgar') ?? null;
  const lastFunnel = lastSecCall?.diagnostics && typeof lastSecCall.diagnostics === 'object'
    ? lastSecCall.diagnostics as Record<string, unknown>
    : null;
  const lastFunnelByForm = lastFunnel?.by_form && typeof lastFunnel.by_form === 'object'
    ? lastFunnel.by_form as Record<string, Record<string, unknown>>
    : {};
  const lastForms = safeArr<string>(lastFunnel?.forms_searched);

  // ── Normalise sources ──────────────────────────────────────────────────────
  const sourcesObj = sourcesRaw && typeof sourcesRaw === 'object' ? sourcesRaw as Record<string, unknown> : null;
  const sourcesList = safeArr<Record<string, unknown>>(sourcesObj?.sources);
  const totalSources = typeof sourcesObj?.count === 'number' ? sourcesObj.count : sourcesList.length;
  const activeSources = sourcesList.filter(s => s?.active === true).length;

  // ── Normalise cron ─────────────────────────────────────────────────────────
  const cronObj = cronRaw && typeof cronRaw === 'object' ? cronRaw as Record<string, unknown> : null;
  const allCronEntries = safeArr<Record<string, unknown>>(cronObj?.entries);

  function eventInfo(command: string): { label: string; type: string; color: string } {
    if (command.includes('/api/investment/scan'))       return { label: 'SEC EDGAR scan',       type: 'SCAN',    color: 'status-badge status-badge--manual' };
    if (command.includes('/api/investment/follow-up'))  return { label: 'Watchlist follow-up',  type: 'FOLLOW',  color: 'status-badge status-badge--partial' };
    if (command.includes('/api/marketplace'))           return { label: 'Marketplace check',    type: 'MARKET',  color: 'status-badge status-badge--preview' };
    if (command.includes('/api/health'))                return { label: 'Health check',         type: 'HEALTH',  color: 'status-badge status-badge--active' };
    return                                                       { label: 'SwissEdge job',       type: 'JOB',     color: 'status-badge status-badge--readonly' };
  }

  function getDayKey(iso: unknown): string {
    const s = safeStr(iso);
    if (!s) return '';
    try {
      return new Date(s).toLocaleDateString('en-CA', { timeZone: 'Europe/Zurich' });
    } catch { return ''; }
  }

  function formatTimeOnly(iso: unknown): string {
    const s = safeStr(iso);
    if (!s) return '—';
    try {
      return new Date(s).toLocaleTimeString('en-CH', {
        timeZone: 'Europe/Zurich',
        hour: '2-digit', minute: '2-digit',
      });
    } catch { return s; }
  }

  const nowZurich = new Date().toLocaleDateString('en-CA', { timeZone: 'Europe/Zurich' });
  const tomorrowZurich = new Date(Date.now() + 86400000).toLocaleDateString('en-CA', { timeZone: 'Europe/Zurich' });

  const calendarGroups: Map<string, Array<{ entry: Record<string, unknown>; info: ReturnType<typeof eventInfo> }>> = new Map();
  for (const entry of allCronEntries) {
    const key = getDayKey(entry.scheduled_at);
    if (!key) continue;
    const info = eventInfo(safeStr(entry.command));
    if (!calendarGroups.has(key)) calendarGroups.set(key, []);
    calendarGroups.get(key)!.push({ entry, info });
  }
  const sortedDayKeys = Array.from(calendarGroups.keys()).sort();

  function dayLabel(key: string): string {
    if (key === nowZurich) return 'Today';
    if (key === tomorrowZurich) return 'Tomorrow';
    try {
      return new Date(key + 'T12:00:00').toLocaleDateString('en-CH', { weekday: 'long', month: 'short', day: 'numeric' });
    } catch { return key; }
  }

  // ── Debug info ─────────────────────────────────────────────────────────────
  const debugLines = [
    `agent: ${loadingAgent ? 'loading' : agentError ? `ERR: ${agentError}` : `ok (runs=${recentRuns.length})`}`,
    `sources: ${loadingSources ? 'loading' : sourcesError ? `ERR: ${sourcesError}` : `ok (${totalSources} total)`}`,
    `cron: ${loadingCron ? 'loading' : cronError ? `ERR: ${cronError}` : `ok (${allCronEntries.length} entries, ${sortedDayKeys.length} days)`}`,
  ];

  return (
    <div className="page-container--wide">

      <div className="mb-8 animate-fade-in" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <Link href="/" className="nav-back">← Mission Control</Link>
        <div style={{ display: 'flex', alignItems: 'center', gap: '24px' }}>
          <Link href="/investment/evaluations" className="nav-back" style={{ marginBottom: 0 }}>Evaluations</Link>
          <Link href="/investment/sources" className="nav-back" style={{ marginBottom: 0 }}>Sources</Link>
        </div>
      </div>

      <div className="page-header animate-fade-in">
        <h1 className="page-title">Investment Radar Status</h1>
        <p className="page-subtitle">Scanner observability · read-only view</p>
      </div>

      <div className="card card-accent mb-6 animate-fade-in-1" style={{ borderLeftColor: 'var(--status-preview-border)' }}>
        <p className="card-desc" style={{ color: 'var(--status-preview-text)', marginBottom: 6 }}>
          Current scanner reality: scheduled scans use the hardcoded SEC EDGAR adapter. The Source Registry is visible here for operations context, but active/inactive source toggles do not control scanner coverage yet.
        </p>
        <p className="card-desc">
          This page is read-only and only reports stored run diagnostics. It does not trigger scans or change cron.
        </p>
      </div>

      {/* Summary cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8 animate-fade-in-1">
        <div className="card" style={{ padding: '16px' }}>
          <div className="metric-pill">
            <span className="metric-label">Scanner Status</span>
            {loadingAgent ? (
              <span className="metric-value">…</span>
            ) : agentError ? (
              <span className="metric-value" style={{ color: 'var(--status-error-text)' }}>Error</span>
            ) : (
              <span className="metric-value" style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <StatusDot status={agent?.current_status} />
                {safeStr(agent?.current_status).toUpperCase() || 'UNKNOWN'}
              </span>
            )}
          </div>
        </div>

        <div className="card" style={{ padding: '16px' }}>
          <div className="metric-pill">
            <span className="metric-label">Total Runs</span>
            {loadingAgent ? (
              <span className="metric-value">…</span>
            ) : (
              <span className="metric-value">{safeText(agentStats?.total_runs)}</span>
            )}
          </div>
        </div>

        <div className="card" style={{ padding: '16px' }}>
          <div className="metric-pill">
            <span className="metric-label">Failed Runs</span>
            {loadingAgent ? (
              <span className="metric-value">…</span>
            ) : (
              <span className="metric-value" style={Number(agentStats?.failed_runs ?? 0) > 0 ? { color: 'var(--status-error-text)' } : undefined}>
                {safeText(agentStats?.failed_runs)}
              </span>
            )}
          </div>
        </div>

        <div className="card" style={{ padding: '16px' }}>
          <div className="metric-pill">
            <span className="metric-label">Active Sources</span>
            {loadingSources ? (
              <span className="metric-value">…</span>
            ) : sourcesError ? (
              <span className="metric-value" style={{ color: 'var(--status-error-text)' }}>Error</span>
            ) : (
              <span className="metric-value">
                {activeSources}<span style={{ color: 'var(--text-muted)', fontSize: '13px' }}> / {totalSources}</span>
              </span>
            )}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8 animate-fade-in-1">

        {/* Last Run Details */}
        <div className="card">
          <div className="section-header" style={{ marginBottom: '16px' }}>
            <span className="section-title">Last Scanner Run</span>
            <div className="section-line"></div>
          </div>
          {loadingAgent ? (
            <div className="loading-state" style={{ padding: '8px 0' }}>
              <div className="loading-spinner"></div>
              <span>Loading…</span>
            </div>
          ) : agentError ? (
            <p style={{ fontFamily: 'var(--font-mono)', fontSize: '12px', color: 'var(--status-error-text)' }}>{agentError}</p>
          ) : !lastRun ? (
            <p style={{ fontFamily: 'var(--font-mono)', fontSize: '12px', color: 'var(--text-muted)' }}>No runs recorded yet.</p>
          ) : (
            <dl style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <dt style={{ fontFamily: 'var(--font-mono)', fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.08em' }}>Status</dt>
                <dd style={{ margin: 0 }}><StatusBadge status={lastRun.status} /></dd>
              </div>
              <Row label="Started" value={formatDate(lastRun.started_at)} />
              <Row label="Duration" value={durationLabel(lastRun.duration_ms)} />
              <Row label="Task" value={safeText(lastRun.task_name)} />
              {lastRun.output_summary !== undefined && lastRun.output_summary !== null && (
                <div style={{ marginTop: '8px', padding: '10px 12px', background: 'var(--bg-subtle)', borderRadius: '8px', fontFamily: 'var(--font-mono)', fontSize: '11px', color: 'var(--text-secondary)', lineHeight: 1.6, wordBreak: 'break-word', border: '1px solid var(--border-subtle)' }}>
                  {safeText(lastRun.output_summary)}
                </div>
              )}
              {lastRun.error_message !== undefined && lastRun.error_message !== null && (
                <div style={{ marginTop: '8px', padding: '10px 12px', background: 'var(--status-error-bg)', borderRadius: '8px', fontFamily: 'var(--font-mono)', fontSize: '11px', color: 'var(--status-error-text)', lineHeight: 1.6, wordBreak: 'break-word', border: '1px solid var(--status-error-border)' }}>
                  {safeText(lastRun.error_message)}
                </div>
              )}
            </dl>
          )}
        </div>

        {/* Last Success / Last Failure */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div className="card">
            <div className="section-header" style={{ marginBottom: '12px' }}>
              <span className="section-title">Last Successful Scan</span>
              <div className="section-line"></div>
            </div>
            {loadingAgent ? (
              <div className="loading-state" style={{ padding: '8px 0' }}>
                <div className="loading-spinner"></div>
                <span>Loading…</span>
              </div>
            ) : !lastSuccess ? (
              <p style={{ fontFamily: 'var(--font-mono)', fontSize: '12px', color: 'var(--text-muted)' }}>No successful run in recent history.</p>
            ) : (
              <dl style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                <Row label="Completed" value={formatDate(lastSuccess.finished_at)} />
                <Row label="Duration" value={durationLabel(lastSuccess.duration_ms)} />
                {lastSuccess.database_records_created != null && (
                  <Row label="Records created" value={safeText(lastSuccess.database_records_created)} />
                )}
              </dl>
            )}
          </div>

          <div className="card">
            <div className="section-header" style={{ marginBottom: '12px' }}>
              <span className="section-title">Last Scan Error</span>
              <div className="section-line"></div>
            </div>
            {loadingAgent ? (
              <div className="loading-state" style={{ padding: '8px 0' }}>
                <div className="loading-spinner"></div>
                <span>Loading…</span>
              </div>
            ) : !lastFailed ? (
              <p style={{ fontFamily: 'var(--font-mono)', fontSize: '12px', color: 'var(--text-muted)' }}>No failures in recent history.</p>
            ) : (
              <dl style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                <Row label="When" value={formatDate(lastFailed.started_at)} />
                {lastFailed.error_message != null && (
                  <div style={{ marginTop: '6px', padding: '10px 12px', background: 'var(--status-error-bg)', borderRadius: '8px', fontFamily: 'var(--font-mono)', fontSize: '11px', color: 'var(--status-error-text)', lineHeight: 1.6, wordBreak: 'break-word', border: '1px solid var(--status-error-border)' }}>
                    {safeText(lastFailed.error_message)}
                  </div>
                )}
              </dl>
            )}
          </div>
        </div>
      </div>

      {/* Scanner Funnel Diagnostics */}
      <div className="card mb-6 animate-fade-in-2" style={{ padding: 0, overflow: 'hidden' }}>
        <div style={{ padding: '20px 24px 16px', borderBottom: '1px solid var(--border-subtle)' }}>
          <div className="section-header" style={{ marginBottom: 0 }}>
            <span className="section-title">Scanner Funnel Diagnostics</span>
            <div className="section-line"></div>
          </div>
        </div>
        <div style={{ padding: '20px 24px' }}>
          {loadingAgent ? (
            <div className="loading-state">
              <div className="loading-spinner"></div>
              <span>Loading…</span>
            </div>
          ) : agentError ? (
            <p style={{ fontFamily: 'var(--font-mono)', fontSize: '12px', color: 'var(--status-error-text)' }}>{agentError}</p>
          ) : !lastRun ? (
            <p style={{ fontFamily: 'var(--font-mono)', fontSize: '12px', color: 'var(--text-muted)' }}>No scanner run is available yet.</p>
          ) : !lastFunnel ? (
            <div style={{ padding: '12px 14px', borderRadius: '8px', background: 'var(--bg-subtle)', border: '1px solid var(--border-subtle)' }}>
              <p className="card-desc" style={{ color: 'var(--text-secondary)' }}>
                No funnel payload is available for the latest run. Older runs only recorded total filings returned and records created.
              </p>
            </div>
          ) : (
            <>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                <div className="card" style={{ padding: '14px' }}>
                  <div className="metric-pill">
                    <span className="metric-value">{numberText(lastFunnel.raw_hits_total)}</span>
                    <span className="metric-label">Raw SEC Hits</span>
                  </div>
                </div>
                <div className="card" style={{ padding: '14px' }}>
                  <div className="metric-pill">
                    <span className="metric-value">{numberText(lastFunnel.parsed_filings_total)}</span>
                    <span className="metric-label">Parsed Filings</span>
                  </div>
                </div>
                <div className="card" style={{ padding: '14px' }}>
                  <div className="metric-pill">
                    <span className="metric-value">{numberText(lastFunnel.classified_candidates_count)}</span>
                    <span className="metric-label">Classified</span>
                  </div>
                </div>
                <div className="card" style={{ padding: '14px' }}>
                  <div className="metric-pill">
                    <span className="metric-value">{numberText(lastFunnel.created_count)}</span>
                    <span className="metric-label">Created</span>
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                    <Row label="Adapter" value={safeText(lastFunnel.adapter_name)} />
                    <Row label="Source registry used" value={lastFunnel.source_registry_used === true ? 'yes' : 'no'} />
                    <Row label="Hours back" value={safeText(lastFunnel.hours_back)} />
                    <Row label="Limit / form" value={safeText(lastFunnel.query_limit_per_form)} />
                    <Row label="Skipped unclassified" value={numberText(lastFunnel.skipped_unclassified_count)} />
                    <Row label="Skipped duplicates" value={numberText(lastFunnel.skipped_duplicate_count)} />
                    <Row label="Evaluated" value={numberText(lastFunnel.evaluated_count)} />
                    <Row label="Evaluation errors" value={numberText(lastFunnel.evaluation_error_count)} />
                  </div>
                  {lastForms.length > 0 && (
                    <div style={{ marginTop: '12px', padding: '10px 12px', background: 'var(--bg-subtle)', borderRadius: '8px', fontFamily: 'var(--font-mono)', fontSize: '11px', color: 'var(--text-secondary)', lineHeight: 1.6, border: '1px solid var(--border-subtle)' }}>
                      Forms searched: {lastForms.join(', ')}
                    </div>
                  )}
                </div>

                <div style={{ overflowX: 'auto' }}>
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>Form</th>
                        <th>Raw</th>
                        <th>Parsed</th>
                        <th>Classified</th>
                      </tr>
                    </thead>
                    <tbody>
                      {Object.entries(lastFunnelByForm).map(([form, stats]) => (
                        <tr key={form}>
                          <td>{form}</td>
                          <td>{numberText(stats.raw_hits)}</td>
                          <td>{numberText(stats.parsed_filings)}</td>
                          <td>{numberText(stats.classified_filings)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </>
          )}
        </div>
      </div>

      {/* Investment Radar Calendar */}
      <div className="card mb-6 animate-fade-in-2" style={{ padding: 0, overflow: 'hidden' }}>
        <div style={{ padding: '20px 24px 16px', borderBottom: '1px solid var(--border-subtle)', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div className="section-header" style={{ marginBottom: 0 }}>
            <span className="section-title">Investment Radar Calendar</span>
            <div className="section-line"></div>
          </div>
          {!loadingCron && !cronError && (
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: '11px', color: 'var(--text-muted)' }}>
              {safeText(cronObj?.timezone, 'Europe/Zurich')} · {allCronEntries.length} events
            </span>
          )}
        </div>
        <div style={{ padding: '20px 24px' }}>
          {loadingCron ? (
            <div className="loading-state">
              <div className="loading-spinner"></div>
              <span>Loading…</span>
            </div>
          ) : cronError ? (
            <p style={{ fontFamily: 'var(--font-mono)', fontSize: '12px', color: 'var(--status-error-text)' }}>{cronError}</p>
          ) : sortedDayKeys.length === 0 ? (
            <p style={{ fontFamily: 'var(--font-mono)', fontSize: '12px', color: 'var(--text-muted)' }}>No upcoming scheduled events in the next 3 days.</p>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
              {sortedDayKeys.map((dayKey) => {
                const events = calendarGroups.get(dayKey)!;
                const isToday = dayKey === nowZurich;
                return (
                  <div key={dayKey}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '8px' }}>
                      <span style={{ fontFamily: 'var(--font-mono)', fontSize: '11px', fontWeight: 700, letterSpacing: '0.1em', textTransform: 'uppercase', color: isToday ? 'var(--text-primary)' : 'var(--text-muted)' }}>
                        {dayLabel(dayKey)}
                      </span>
                      <div style={{ flex: 1, height: '1px', background: 'var(--border-subtle)' }}></div>
                      <span style={{ fontFamily: 'var(--font-mono)', fontSize: '11px', color: 'var(--text-faint)' }}>{dayKey}</span>
                    </div>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                      {events.map(({ entry, info }, i) => (
                        <div key={i} style={{ display: 'flex', alignItems: 'center', gap: '12px', padding: '8px 12px', borderRadius: '8px', background: 'var(--bg-subtle)', border: '1px solid var(--border-subtle)' }}>
                          <span style={{ fontFamily: 'var(--font-mono)', fontSize: '13px', fontWeight: 600, color: 'var(--text-primary)', width: '48px', flexShrink: 0 }}>
                            {formatTimeOnly(entry.scheduled_at)}
                          </span>
                          <span style={{ fontFamily: 'var(--font-mono)', fontSize: '12px', color: 'var(--text-secondary)', flex: 1 }}>{info.label}</span>
                          <span className={info.color} style={{ flexShrink: 0 }}>{info.type}</span>
                          <span style={{ fontFamily: 'var(--font-mono)', fontSize: '11px', color: 'var(--text-faint)', flexShrink: 0 }} className="hidden md:block">
                            {friendlySchedule(safeStr(entry.schedule))}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>

      {/* Recent Runs Table */}
      <div className="card mb-6 animate-fade-in-2" style={{ padding: 0, overflow: 'hidden' }}>
        <div style={{ padding: '20px 24px 16px', borderBottom: '1px solid var(--border-subtle)' }}>
          <div className="section-header" style={{ marginBottom: 0 }}>
            <span className="section-title">Recent Scanner Runs</span>
            <div className="section-line"></div>
            {!loadingAgent && recentRuns.length > 0 && (
              <span className="section-count">{recentRuns.length}</span>
            )}
          </div>
        </div>
        <div style={{ overflowX: 'auto' }}>
          {loadingAgent ? (
            <div className="loading-state" style={{ padding: '24px' }}>
              <div className="loading-spinner"></div>
              <span>Loading…</span>
            </div>
          ) : agentError ? (
            <p style={{ padding: '16px 24px', fontFamily: 'var(--font-mono)', fontSize: '12px', color: 'var(--status-error-text)' }}>{agentError}</p>
          ) : recentRuns.length === 0 ? (
            <p style={{ padding: '16px 24px', fontFamily: 'var(--font-mono)', fontSize: '12px', color: 'var(--text-muted)' }}>No runs recorded yet.</p>
          ) : (
            <table className="data-table">
              <thead>
                <tr>
                  <th>Status</th>
                  <th>Started (CET)</th>
                  <th>Duration</th>
                  <th>Task</th>
                  <th>Records</th>
                  <th>Trigger</th>
                </tr>
              </thead>
              <tbody>
                {recentRuns.map((run, i) => (
                  <tr key={safeStr(run.id) || i}>
                    <td><StatusBadge status={run.status} /></td>
                    <td>{formatDate(run.started_at)}</td>
                    <td>{durationLabel(run.duration_ms)}</td>
                    <td style={{ maxWidth: '160px' }} className="truncate">{safeText(run.task_name)}</td>
                    <td>{run.database_records_created != null ? safeText(run.database_records_created) : '—'}</td>
                    <td>{safeText(run.trigger_source)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>

      {/* Sources Summary */}
      <div className="card mb-6 animate-fade-in-3" style={{ padding: 0, overflow: 'hidden' }}>
        <div style={{ padding: '20px 24px 16px', borderBottom: '1px solid var(--border-subtle)' }}>
          <div className="section-header" style={{ marginBottom: 0 }}>
            <span className="section-title">Source Registry Summary</span>
            <div className="section-line"></div>
          </div>
        </div>
        <div style={{ padding: '20px 24px' }}>
          {loadingSources ? (
            <div className="loading-state">
              <div className="loading-spinner"></div>
              <span>Loading…</span>
            </div>
          ) : sourcesError ? (
            <p style={{ fontFamily: 'var(--font-mono)', fontSize: '12px', color: 'var(--status-error-text)' }}>{sourcesError}</p>
          ) : sourcesList.length === 0 ? (
            <p style={{ fontFamily: 'var(--font-mono)', fontSize: '12px', color: 'var(--text-muted)' }}>No sources registered.</p>
          ) : (
            <>
              <div style={{ marginBottom: '16px', padding: '10px 12px', background: 'var(--bg-subtle)', borderRadius: '8px', border: '1px solid var(--border-subtle)' }}>
                <p className="card-desc">
                  Registry state is shown for reference. Current scanner runs do not read this table; coverage remains the hardcoded SEC EDGAR adapter until source-driven intake is implemented.
                </p>
              </div>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                <div className="card" style={{ padding: '14px' }}>
                  <div className="metric-pill">
                    <span className="metric-value">{totalSources}</span>
                    <span className="metric-label">Total</span>
                  </div>
                </div>
                <div className="card" style={{ padding: '14px' }}>
                  <div className="metric-pill">
                    <span className="metric-value">{activeSources}</span>
                    <span className="metric-label">Active</span>
                  </div>
                </div>
                <div className="card" style={{ padding: '14px' }}>
                  <div className="metric-pill">
                    <span className="metric-value">{totalSources - activeSources}</span>
                    <span className="metric-label">Inactive</span>
                  </div>
                </div>
                <div className="card" style={{ padding: '14px' }}>
                  <div className="metric-pill">
                    <span className="metric-value">{sourcesList.filter(s => s?.requires_api_key === true).length}</span>
                    <span className="metric-label">Require API Key</span>
                  </div>
                </div>
              </div>
              <div style={{ overflowX: 'auto' }}>
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Name</th>
                      <th>Type</th>
                      <th>Priority</th>
                      <th>Last Checked</th>
                      <th>State</th>
                    </tr>
                  </thead>
                  <tbody>
                    {sourcesList.map((src, i) => (
                      <tr key={safeStr(src.id) || i}>
                        <td style={{ maxWidth: '200px' }} className="truncate">{safeText(src.name)}</td>
                        <td>{safeText(src.source_type)}</td>
                        <td>{safeText(src.priority)}</td>
                        <td>{formatDate(src.last_checked)}</td>
                        <td>
                          <span className={src.active === true ? 'status-badge status-badge--active' : 'status-badge status-badge--readonly'}>
                            {src.active === true ? 'ACTIVE' : 'INACTIVE'}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <div style={{ textAlign: 'right', marginTop: '12px' }}>
                <Link href="/investment/sources" className="nav-back" style={{ marginBottom: 0 }}>Manage sources →</Link>
              </div>
            </>
          )}
        </div>
      </div>

      {/* Debug panel */}
      <details className="mb-4 animate-fade-in-4">
        <summary style={{ fontFamily: 'var(--font-mono)', fontSize: '11px', color: 'var(--text-faint)', cursor: 'pointer', userSelect: 'none' }}>debug info</summary>
        <div style={{ marginTop: '4px', paddingLeft: '8px' }}>
          {debugLines.map((line, i) => (
            <div key={i} style={{ fontFamily: 'var(--font-mono)', fontSize: '11px', color: 'var(--text-faint)' }}>{line}</div>
          ))}
        </div>
      </details>

      <div style={{ textAlign: 'center', fontFamily: 'var(--font-mono)', fontSize: '11px', color: 'var(--text-faint)', marginTop: '16px', marginBottom: '32px' }} className="animate-fade-in-4">
        READ-ONLY VIEW — NO SCANS ARE TRIGGERED FROM THIS PAGE
      </div>

    </div>
  );
}
