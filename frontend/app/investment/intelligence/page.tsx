'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import {
  fetchIntelligenceKpis,
  type IntelligenceKpiCaseLink,
  type IntelligenceKpiPackage,
} from '@/lib/api';
import { ErrorBanner, InfoBanner, LoadingState, MetricRow, PageHeader, StatusBadge } from '@/app/components/ui';

function pct(numerator: number, denominator: number): string {
  if (!denominator) return '0%';
  return `${Math.round((numerator / denominator) * 100)}%`;
}

function CaseLinkList({
  title,
  rows,
  empty,
}: {
  title: string;
  rows: IntelligenceKpiCaseLink[];
  empty: string;
}) {
  return (
    <div className="card">
      <div className="section-header" style={{ marginBottom: 12 }}>
        <span className="section-title">{title}</span>
        <div className="section-line" />
      </div>
      {rows.length === 0 ? (
        <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>{empty}</div>
      ) : (
        <div style={{ display: 'grid', gap: 8 }}>
          {rows.map(row => (
            <Link
              key={`${row.case_type}-${row.id}`}
              href={row.href}
              className="card"
              style={{ padding: '10px 12px', textDecoration: 'none', display: 'grid', gap: 6 }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', gap: 10, alignItems: 'flex-start' }}>
                <div style={{ minWidth: 0 }}>
                  <div style={{ fontSize: 13, fontWeight: 650, color: 'var(--text-primary)' }}>{row.title}</div>
                  <div style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-faint)', textTransform: 'uppercase' }}>
                    {row.case_type.replace(/_/g, ' ')}
                  </div>
                </div>
                {row.grade && <StatusBadge value={row.grade} />}
              </div>
              <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                {typeof row.score === 'number' && <span className="status-badge status-badge--readonly">Score {row.score}</span>}
                {typeof row.missing_items === 'number' && <span className="status-badge status-badge--preview">{row.missing_items} missing</span>}
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}

export default function IntelligenceDashboardPage() {
  const [kpis, setKpis] = useState<IntelligenceKpiPackage | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function load() {
    try {
      setLoading(true);
      setError(null);
      setKpis(await fetchIntelligenceKpis());
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load Intelligence KPIs');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void load();
  }, []);

  const evidenceCoverage = kpis
    ? pct(kpis.evidence.evidence_found_total, kpis.evidence.required_resources_total)
    : '0%';

  return (
    <div className="page-container--wide">
      <PageHeader
        title="Intelligence KPIs"
        subtitle="Preparation quality, evidence coverage, documentation gaps, and manual review workload"
        backHref="/"
        backLabel="Mission Control"
        actions={
          <button className="btn btn--secondary btn--sm" onClick={load} disabled={loading}>
            {loading ? 'Loading...' : 'Refresh'}
          </button>
        }
      />

      <InfoBanner variant="guardrail">
        Read-only deterministic dashboard. No AI, evaluator, scanner, crawler, publishing, or automatic case action is triggered here.
        Metrics describe preparation quality and evidence coverage only.
      </InfoBanner>

      <div className="card" style={{ marginBottom: 16, display: 'flex', gap: 8, flexWrap: 'wrap' }}>
        <Link href="/investment/situations" className="btn btn--secondary btn--sm">Open Kanban</Link>
        <Link href="/investment/research" className="btn btn--secondary btn--sm">Open ResearchCases</Link>
        <Link href="/agent-ops" className="btn btn--secondary btn--sm">Open Agent Ops</Link>
        <Link href="/agent-ops#fontana" className="btn btn--secondary btn--sm">Open Fontana</Link>
      </div>

      <InfoBanner variant="info">
        Missing-evidence bottlenecks should be opened from the case links below. Each detail page now includes an Official Source Finder with stored SEC metadata,
        manual locator steps, and copyable queries. SwissEdge does not run those searches automatically.
      </InfoBanner>

      <InfoBanner variant="info">
        Low-quality or incomplete cases should also be compared manually against Historical Cases and processed course patterns.
        Analogues are methodology context only; they do not predict outcomes or evaluate the case.
        <Link href="/investment/historical-cases" className="btn btn--ghost btn--sm" style={{ marginLeft: 8 }}>
          Open Historical Cases
        </Link>
      </InfoBanner>

      {error && <ErrorBanner message={error} />}
      {loading && <LoadingState label="Loading Intelligence KPIs..." />}

      {kpis && (
        <div style={{ display: 'grid', gap: 20 }}>
          <MetricRow items={[
            { label: 'Avg Intelligence Score', value: kpis.intelligence.average_score },
            { label: 'Documentation Quality', value: kpis.documentation.average_documentation_quality },
            { label: 'Evidence Coverage', value: evidenceCoverage },
            { label: 'Missing Evidence Cases', value: kpis.case_counts.missing_evidence },
            { label: 'Manual Review Ready', value: kpis.case_counts.ready_for_manual_review },
            { label: 'Review Pipeline', value: kpis.intelligence.review_pipeline_count },
          ]} />

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: 14 }}>
            <div className="card">
              <div className="section-header" style={{ marginBottom: 12 }}>
                <span className="section-title">Case Counts</span>
                <div className="section-line" />
              </div>
              <MetricRow items={[
                { label: 'ResearchCases', value: kpis.case_counts.research_cases_total },
                { label: 'SpecialSituations', value: kpis.case_counts.special_situations_total },
                { label: 'SEC Detected', value: kpis.case_counts.sec_detected },
                { label: 'Promoted', value: kpis.case_counts.promoted_to_research_case },
              ]} />
            </div>

            <div className="card">
              <div className="section-header" style={{ marginBottom: 12 }}>
                <span className="section-title">Cases By Grade</span>
                <div className="section-line" />
              </div>
              <MetricRow items={[
                { label: 'Manual Review Ready', value: kpis.intelligence.approvable_count },
                { label: 'Useful Incomplete', value: kpis.intelligence.useful_incomplete_count },
                { label: 'Review Pipeline', value: kpis.intelligence.review_pipeline_count },
              ]} />
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: 14 }}>
            <div className="card">
              <div className="section-header" style={{ marginBottom: 12 }}>
                <span className="section-title">Documentation Quality</span>
                <div className="section-line" />
              </div>
              <MetricRow items={[
                { label: 'Good', value: kpis.documentation.good_count },
                { label: 'Needs Links', value: kpis.documentation.needs_links_count },
                { label: 'Needs Resources', value: kpis.documentation.needs_required_resources_count },
                { label: 'Needs Mapping', value: kpis.documentation.needs_evidence_mapping_count },
              ]} />
            </div>

            <div className="card">
              <div className="section-header" style={{ marginBottom: 12 }}>
                <span className="section-title">Evidence Coverage</span>
                <div className="section-line" />
              </div>
              <MetricRow items={[
                { label: 'Required', value: kpis.evidence.required_resources_total },
                { label: 'Missing', value: kpis.evidence.missing_required_resources_total },
                { label: 'Candidates', value: kpis.evidence.candidate_found_total },
                { label: 'Evidence Found', value: kpis.evidence.evidence_found_total },
                { label: 'Rejected', value: kpis.evidence.rejected_total },
                { label: 'Links', value: kpis.evidence.evidence_links_total },
              ]} />
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: 14 }}>
            <div className="card">
              <div className="section-header" style={{ marginBottom: 12 }}>
                <span className="section-title">Agent Workload</span>
                <div className="section-line" />
              </div>
              <MetricRow items={[
                { label: 'Rooms', value: kpis.agent_ops.rooms_count },
                { label: 'Agents', value: kpis.agent_ops.agents_count },
                { label: 'Activity Rows', value: kpis.agent_ops.activity_rows_count },
                { label: 'Diagnostics', value: kpis.agent_ops.diagnostics_count },
                { label: 'MEH Load', value: kpis.agent_ops.missing_evidence_hunter_load },
              ]} />
              <Link href="/agent-ops" className="btn btn--secondary btn--sm" style={{ marginTop: 12 }}>
                Open Agent Ops
              </Link>
              {kpis.agent_ops.rooms.length > 0 && (
                <div style={{ display: 'grid', gap: 6, marginTop: 12 }}>
                  {kpis.agent_ops.rooms.map(room => (
                    <Link key={room.id} href={room.href} className="btn btn--ghost btn--sm">
                      {room.name}
                    </Link>
                  ))}
                </div>
              )}
            </div>

            <div className="card">
              <div className="section-header" style={{ marginBottom: 12 }}>
                <span className="section-title">Operational Bottlenecks</span>
                <div className="section-line" />
              </div>
              {kpis.bottlenecks.length === 0 ? (
                <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>No aggregate bottleneck detected in stored metadata.</div>
              ) : (
                <div style={{ display: 'grid', gap: 8 }}>
                  {kpis.bottlenecks.map(item => (
                    <div key={item.key} style={{ display: 'flex', justifyContent: 'space-between', gap: 8 }}>
                      <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>{item.label}</span>
                      <StatusBadge value={`${item.count}`} />
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: 14 }}>
            <CaseLinkList
              title="Lowest Scoring Cases"
              rows={kpis.intelligence.lowest_scoring_cases}
              empty="No ResearchCases scored yet."
            />
            <CaseLinkList
              title="Cases Needing Manual Work"
              rows={kpis.intelligence.cases_needing_manual_work}
              empty="No manual-work cases detected in stored metadata."
            />
            <CaseLinkList
              title="Missing Evidence Cases"
              rows={kpis.missing_evidence_cases}
              empty="No missing evidence cases detected in stored metadata."
            />
          </div>

          <div className="card">
            <div className="section-header" style={{ marginBottom: 12 }}>
              <span className="section-title">Next Manual Actions</span>
              <div className="section-line" />
            </div>
            {kpis.manual_next_actions.length === 0 ? (
              <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>No manual next action generated from current stored metadata.</div>
            ) : (
              <div style={{ display: 'grid', gap: 8 }}>
                {kpis.manual_next_actions.map(action => (
                  <Link key={`${action.label}-${action.target_href}`} href={action.target_href} className="card" style={{ padding: '10px 12px', textDecoration: 'none' }}>
                    <div style={{ fontWeight: 650, fontSize: 13, color: 'var(--text-primary)' }}>{action.label}</div>
                    <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 3 }}>{action.reason}</div>
                  </Link>
                ))}
              </div>
            )}
          </div>

          <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
            {kpis.guardrails.map(guardrail => (
              <span key={guardrail} className="status-badge status-badge--readonly">{guardrail}</span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
