'use client';

import Link from 'next/link';
import type { HistoricalAnaloguesPackage } from '@/lib/api';
import { InfoBanner, LoadingState, StatusBadge } from '@/app/components/ui';

const labelStyle = {
  fontFamily: 'var(--font-mono)',
  fontSize: 10,
  color: 'var(--text-faint)',
  textTransform: 'uppercase' as const,
  letterSpacing: 0,
};

function PillList({ values }: { values: string[] }) {
  if (!values.length) return <span style={{ color: 'var(--text-faint)' }}>-</span>;
  return (
    <span style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
      {values.map(value => <span key={value} className="status-badge status-badge--readonly">{value}</span>)}
    </span>
  );
}

function EmptyText({ children }: { children: React.ReactNode }) {
  return <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>{children}</div>;
}

export function HistoricalAnaloguesPanel({
  analogues,
  loading = false,
  error,
}: {
  analogues: HistoricalAnaloguesPackage | null;
  loading?: boolean;
  error?: string | null;
}) {
  if (loading) {
    return (
      <div className="card">
        <LoadingState label="Loading historical analogues..." />
      </div>
    );
  }

  if (error) {
    return (
      <div className="card" id="historical-analogues">
        <div className="section-header" style={{ marginBottom: 12 }}>
          <span className="section-title">Historical Analogues & Course Patterns</span>
          <div className="section-line" />
        </div>
        <InfoBanner variant="warning">{error}</InfoBanner>
      </div>
    );
  }

  if (!analogues) {
    return (
      <div className="card" id="historical-analogues">
        <div className="section-header" style={{ marginBottom: 12 }}>
          <span className="section-title">Historical Analogues & Course Patterns</span>
          <div className="section-line" />
        </div>
        <InfoBanner variant="info">No historical analogue package is available for this case yet.</InfoBanner>
      </div>
    );
  }

  return (
    <div className="card" id="historical-analogues">
      <div className="section-header" style={{ marginBottom: 12 }}>
        <span className="section-title">Historical Analogues & Course Patterns</span>
        <div className="section-line" />
        <StatusBadge value="read-only" />
      </div>

      <InfoBanner variant="guardrail">
        Methodology/context aid only. Uses stored safe metadata and processed playbook labels; no raw course materials, AI, external search, outcome prediction, or investment evaluation.
      </InfoBanner>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))', gap: 10, marginTop: 14 }}>
        {([
          ['Company', analogues.case_summary.company_name ?? '-'],
          ['Filing', analogues.case_summary.filing_type ?? '-'],
          ['Situation', analogues.case_summary.situation_type ?? '-'],
          ['Playbook', analogues.case_summary.selected_playbook ?? '-'],
          ['Methodology', analogues.case_summary.methodology_status],
        ] as [string, string][]).map(([label, value]) => (
          <div key={label} style={{ border: '1px solid var(--border-default)', borderRadius: 6, padding: 10, background: 'var(--bg-subtle)' }}>
            <div style={labelStyle}>{label}</div>
            <div style={{ marginTop: 4, fontSize: 13, color: 'var(--text-primary)', wordBreak: 'break-word' }}>{value}</div>
          </div>
        ))}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: 14, marginTop: 16 }}>
        <div>
          <div style={labelStyle}>Relevant course patterns</div>
          <div style={{ display: 'grid', gap: 8, marginTop: 8 }}>
            {analogues.matched_patterns.length === 0 ? (
              <EmptyText>No deterministic pattern matched yet.</EmptyText>
            ) : analogues.matched_patterns.map(pattern => (
              <div key={pattern.pattern_id} style={{ border: '1px solid var(--border-default)', borderRadius: 6, padding: 10 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', gap: 8, alignItems: 'flex-start' }}>
                  <div style={{ fontSize: 13, fontWeight: 650, color: 'var(--text-primary)' }}>{pattern.title}</div>
                  <StatusBadge value={pattern.confidence} />
                </div>
                <div style={{ marginTop: 6, fontSize: 12, color: 'var(--text-muted)' }}>{pattern.similarity_reason}</div>
                <div style={{ marginTop: 8 }}><PillList values={pattern.applies_because.slice(0, 4)} /></div>
                <div style={{ marginTop: 8 }}>
                  <div style={labelStyle}>Manual checks</div>
                  <ul style={{ margin: '6px 0 0', paddingLeft: 18 }}>
                    {pattern.manual_checks.slice(0, 5).map(item => (
                      <li key={item} style={{ fontSize: 12, color: 'var(--text-muted)' }}>{item}</li>
                    ))}
                  </ul>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div>
          <div style={labelStyle}>Similar historical cases</div>
          <div style={{ display: 'grid', gap: 8, marginTop: 8 }}>
            {analogues.historical_case_matches.length === 0 ? (
              <EmptyText>No HistoricalCase rows matched from stored metadata yet.</EmptyText>
            ) : analogues.historical_case_matches.map(match => (
              <Link
                key={match.historical_case_id}
                href={`/investment/historical-cases/${match.historical_case_id}`}
                className="card"
                style={{ padding: 10, textDecoration: 'none', display: 'grid', gap: 6 }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', gap: 8, alignItems: 'flex-start' }}>
                  <div>
                    <div style={{ fontSize: 13, fontWeight: 650, color: 'var(--text-primary)' }}>{match.title}</div>
                    <div style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-faint)' }}>{match.situation_type ?? '-'}</div>
                  </div>
                  <StatusBadge value={`${match.similarity_score}`} />
                </div>
                <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>Why similar: {match.similarity_reasons.join(', ')}</div>
                <div style={{ fontSize: 12, color: 'var(--text-faint)' }}>Different: {match.key_differences.join(', ')}</div>
              </Link>
            ))}
          </div>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: 14, marginTop: 16 }}>
        <div>
          <div style={labelStyle}>Course methodology links</div>
          <div style={{ display: 'grid', gap: 8, marginTop: 8 }}>
            {analogues.course_methodology_links.map(link => (
              <div key={`${link.playbook}-${link.section}`} style={{ border: '1px solid var(--border-default)', borderRadius: 6, padding: 10 }}>
                <div style={{ fontSize: 13, fontWeight: 650, color: 'var(--text-primary)' }}>{link.label}</div>
                <div style={{ marginTop: 4, fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-faint)' }}>{link.playbook} / {link.section}</div>
                <div style={{ marginTop: 6, fontSize: 12, color: 'var(--text-muted)' }}>{link.safe_summary}</div>
              </div>
            ))}
          </div>
        </div>

        <div>
          <div style={labelStyle}>Manual comparison checklist</div>
          <div style={{ display: 'grid', gap: 8, marginTop: 8 }}>
            {analogues.comparison_checklist.map(item => (
              <div key={`${item.label}-${item.status}`} style={{ border: '1px solid var(--border-default)', borderRadius: 6, padding: 10 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', gap: 8, alignItems: 'flex-start' }}>
                  <div style={{ fontSize: 13, fontWeight: 650, color: 'var(--text-primary)' }}>{item.label}</div>
                  <StatusBadge value={item.status} />
                </div>
                <div style={{ marginTop: 6, fontSize: 12, color: 'var(--text-muted)' }}>{item.why_it_matters}</div>
                <div style={{ marginTop: 8 }}><PillList values={[...item.related_required_resource_ids, ...item.related_check_ids]} /></div>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginTop: 16 }}>
        {[...analogues.warnings, ...analogues.guardrails].map(item => (
          <span key={item} className="status-badge status-badge--readonly">{item}</span>
        ))}
      </div>
    </div>
  );
}
