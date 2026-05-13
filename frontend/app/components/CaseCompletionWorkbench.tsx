'use client';

import type { CaseCompletionPackage } from '@/lib/api';
import { InfoBanner, LoadingState, StatusBadge } from '@/app/components/ui';

const labelStyle = {
  fontFamily: 'var(--font-mono)',
  fontSize: 10,
  color: 'var(--text-faint)',
  textTransform: 'uppercase' as const,
  letterSpacing: 0,
};

function formatLabel(value: string): string {
  return value.replace(/_/g, ' ');
}

function goToAnchor(anchor: string) {
  if (typeof document === 'undefined') return;
  const target = document.querySelector(anchor);
  target?.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function ImprovementPills({ values }: { values: string[] }) {
  return (
    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
      {values.map(value => (
        <span key={value} className="status-badge status-badge--readonly">{formatLabel(value)}</span>
      ))}
    </div>
  );
}

export function CaseCompletionWorkbench({
  workbench,
  loading = false,
  error,
}: {
  workbench: CaseCompletionPackage | null;
  loading?: boolean;
  error?: string | null;
}) {
  if (loading) {
    return (
      <div className="card" id="case-completion-workbench">
        <LoadingState label="Loading Case Completion Workbench..." />
      </div>
    );
  }

  if (error) {
    return (
      <div className="card" id="case-completion-workbench">
        <div className="section-header" style={{ marginBottom: 12 }}>
          <span className="section-title">Case Completion Workbench</span>
          <div className="section-line" />
        </div>
        <InfoBanner variant="warning">{error}</InfoBanner>
      </div>
    );
  }

  if (!workbench) {
    return (
      <div className="card" id="case-completion-workbench">
        <div className="section-header" style={{ marginBottom: 12 }}>
          <span className="section-title">Case Completion Workbench</span>
          <div className="section-line" />
        </div>
        <InfoBanner variant="info">No completion workbench package is available for this case yet.</InfoBanner>
      </div>
    );
  }

  const summaryRows = [
    ['Missing resources', workbench.summary.missing_required_resources],
    ['Candidates to review', workbench.summary.candidate_sources_to_review],
    ['Checklist gaps', workbench.summary.checklist_items_needing_evidence],
    ['Evidence not verified', workbench.summary.evidence_found_not_verified],
    ['Rejected/noisy', workbench.summary.rejected_or_noisy_sources],
  ] as const;

  return (
    <div className="card" id="case-completion-workbench">
      <div className="section-header" style={{ marginBottom: 12 }}>
        <span className="section-title">Case Completion Workbench</span>
        <div className="section-line" />
        <StatusBadge value={workbench.completion_level} />
      </div>

      <InfoBanner variant="guardrail">
        Manual checklist for completing documentation, evidence mapping, and review readiness. No auto-fix, auto-evaluation, publishing, or source verification runs here.
      </InfoBanner>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: 10, marginTop: 14 }}>
        <div style={{ border: '1px solid var(--border-default)', borderRadius: 6, padding: 10, background: 'var(--bg-subtle)' }}>
          <div style={labelStyle}>Completion score</div>
          <div style={{ marginTop: 4, fontFamily: 'var(--font-mono)', fontSize: 24, color: 'var(--text-primary)' }}>{workbench.completion_score}/100</div>
        </div>
        {summaryRows.map(([label, value]) => (
          <div key={label} style={{ border: '1px solid var(--border-default)', borderRadius: 6, padding: 10, background: 'var(--bg-subtle)' }}>
            <div style={labelStyle}>{label}</div>
            <div style={{ marginTop: 4, fontFamily: 'var(--font-mono)', fontSize: 18, color: 'var(--text-primary)' }}>{value}</div>
          </div>
        ))}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: 14, marginTop: 16 }}>
        <div>
          <div style={labelStyle}>Next manual actions</div>
          <div style={{ display: 'grid', gap: 8, marginTop: 8 }}>
            {workbench.next_manual_actions.slice(0, 5).map(action => (
              <div key={action.id} style={{ border: '1px solid var(--border-default)', borderRadius: 6, padding: 10 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', gap: 8 }}>
                  <div style={{ fontSize: 13, fontWeight: 650, color: 'var(--text-primary)' }}>{action.label}</div>
                  <StatusBadge value={action.priority} />
                </div>
                <div style={{ marginTop: 6, fontSize: 12, color: 'var(--text-muted)' }}>{action.description}</div>
                <div style={{ marginTop: 8 }}><ImprovementPills values={action.improves} /></div>
                <button type="button" className="btn btn--ghost btn--sm" onClick={() => goToAnchor(action.target_anchor)} style={{ marginTop: 8 }}>
                  Open section
                </button>
              </div>
            ))}
          </div>
        </div>

        <div>
          <div style={labelStyle}>Blocking items</div>
          <div style={{ display: 'grid', gap: 8, marginTop: 8 }}>
            {workbench.blocking_items.length === 0 ? (
              <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>No blocking items detected from stored metadata.</div>
            ) : workbench.blocking_items.slice(0, 6).map(item => (
              <div key={item.id} style={{ border: '1px solid var(--border-default)', borderRadius: 6, padding: 10 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', gap: 8 }}>
                  <div style={{ fontSize: 13, fontWeight: 650, color: 'var(--text-primary)' }}>{item.label}</div>
                  <StatusBadge value={item.severity} />
                </div>
                <div style={{ marginTop: 6, fontSize: 12, color: 'var(--text-muted)' }}>{item.reason}</div>
                <button type="button" className="btn btn--ghost btn--sm" onClick={() => goToAnchor(item.anchor)} style={{ marginTop: 8 }}>
                  Open section
                </button>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 14, marginTop: 16 }}>
        {([
          ['Detection', workbench.score_improvement_plan.detection],
          ['Structuring', workbench.score_improvement_plan.structuring],
          ['Risk Discipline', workbench.score_improvement_plan.risk_discipline],
        ] as [string, string[]][]).map(([title, items]) => (
          <div key={title} style={{ border: '1px solid var(--border-default)', borderRadius: 6, padding: 10 }}>
            <div style={labelStyle}>{title} improvement plan</div>
            <ul style={{ margin: '8px 0 0', paddingLeft: 18 }}>
              {items.map(item => <li key={item} style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 4 }}>{item}</li>)}
            </ul>
          </div>
        ))}
      </div>

      <div style={{ marginTop: 16 }}>
        <div style={labelStyle}>Section status</div>
        <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginTop: 8 }}>
          {workbench.section_status.map(item => (
            <button key={`${item.section}-${item.anchor}`} type="button" className="status-badge status-badge--readonly" onClick={() => goToAnchor(item.anchor)}>
              {item.section}: {formatLabel(item.status)}
            </button>
          ))}
        </div>
      </div>

      <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginTop: 16 }}>
        {workbench.guardrails.map(item => (
          <span key={item} className="status-badge status-badge--readonly">{item}</span>
        ))}
      </div>
    </div>
  );
}
