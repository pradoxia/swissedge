'use client';

import type { DocumentationAgentReport } from '@/lib/api';

function label(value: string): string {
  return value.replaceAll('_', ' ');
}

function statusLabel(value: string): string {
  if (value === 'mostly_documented') return 'Metadata mapped';
  if (value === 'ready_for_manual_review') return 'Manual review package available';
  if (value === 'useful_incomplete') return 'Needs documentation review';
  if (value === 'found_metadata') return 'Metadata mapped';
  if (value === 'needs_manual_check') return 'Needs manual check';
  return label(value);
}

function badgeClass(value: string): string {
  if (value === 'ready_for_manual_review') return 'status-badge status-badge--manual';
  if (value === 'mostly_documented') return 'status-badge status-badge--partial';
  if (value === 'useful_incomplete') return 'status-badge status-badge--preview';
  if (value === 'blocked') return 'status-badge status-badge--danger';
  if (value === 'found_metadata') return 'status-badge status-badge--readonly';
  if (value === 'needs_manual_check') return 'status-badge status-badge--manual';
  if (value === 'missing') return 'status-badge status-badge--preview';
  return 'status-badge status-badge--readonly';
}

export function DocumentationAgentPanel({
  report,
  loading,
  error,
  showGuardrailNote = true,
}: {
  report: DocumentationAgentReport | null;
  loading: boolean;
  error: string | null;
  showGuardrailNote?: boolean;
}) {
  const checklistReady = report?.checklist.filter(item => item.status === 'ready_for_manual_review').length ?? 0;
  const checklistTotal = report?.checklist.length ?? 0;

  return (
    <section className="card" style={{ padding: 18 }}>
      <div className="card-header" style={{ alignItems: 'flex-start', gap: 12 }}>
        <div>
          <div className="card-title">Case Diagnostic Summary</div>
          <div className="card-desc">Compact diagnostic summary. Documentation Tasks is the working area.</div>
        </div>
        {report && <span className={badgeClass(report.documentation_status)}>{statusLabel(report.documentation_status)}</span>}
      </div>

      {loading && <p className="card-desc" style={{ marginTop: 12 }}>Loading documentation report...</p>}
      {error && <p style={{ marginTop: 12, fontSize: 12, color: 'var(--status-error-text)' }}>{error}</p>}
      {!loading && !error && !report && (
        <p className="card-desc" style={{ marginTop: 12 }}>No documentation report available yet.</p>
      )}

      {report && !loading && (
        <div style={{ display: 'grid', gap: 12, marginTop: 14 }}>
          <div style={{ padding: 12, border: '1px solid var(--border-default)', borderRadius: 8, background: 'var(--bg-subtle)' }}>
            <div style={{ fontFamily: 'var(--font-mono)', fontSize: 10, textTransform: 'uppercase', color: 'var(--text-faint)', marginBottom: 4 }}>
              Next best action
            </div>
            <div style={{ fontSize: 13, fontWeight: 650, color: 'var(--text-primary)', lineHeight: 1.45 }}>
              {report.next_best_action}
            </div>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
            <div className="metric-pill"><span className="metric-value">{report.documents_found.length}</span><span className="metric-label">Found metadata</span></div>
            <div className="metric-pill"><span className="metric-value">{report.documents_missing.length}</span><span className="metric-label">Needs Dani review</span></div>
            <div className="metric-pill"><span className="metric-value">{report.critical_missing_documents.length}</span><span className="metric-label">Critical missing</span></div>
            <div className="metric-pill"><span className="metric-value">{report.missing_skills.length}</span><span className="metric-label">System skill gaps</span></div>
            <div className="metric-pill"><span className="metric-value">{checklistReady}/{checklistTotal}</span><span className="metric-label">Checklist items</span></div>
          </div>

          <details>
            <summary style={{ cursor: 'pointer', fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--text-muted)' }}>
              Diagnostic metadata
            </summary>
            <div style={{ display: 'grid', gap: 10, marginTop: 10 }}>
              <div style={{ fontSize: 12, color: 'var(--text-muted)', lineHeight: 1.5 }}>{report.summary}</div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginBottom: 8 }}>
                {report.applicable_playbooks.slice(0, 3).map(playbook => (
                  <span key={playbook} className="status-badge status-badge--readonly">{label(playbook)}</span>
                ))}
              </div>
              <ul style={{ margin: 0, paddingLeft: 18, display: 'grid', gap: 4 }}>
                {report.course_chapters.slice(0, 3).map(chapter => (
                  <li key={chapter.chapter_id} style={{ fontSize: 12, color: 'var(--text-muted)' }}>
                    {chapter.title}
                  </li>
                ))}
              </ul>
              <div style={{ display: 'grid', gap: 6 }}>
                {report.checklist.slice(0, 5).map(item => (
                  <div key={item.key} style={{ display: 'flex', justifyContent: 'space-between', gap: 10, alignItems: 'center', fontSize: 12 }}>
                    <span style={{ color: 'var(--text-muted)' }}>{item.label}</span>
                    <span className={badgeClass(item.status)}>{statusLabel(item.status)}</span>
                  </div>
                ))}
              </div>
            </div>
          </details>

          {showGuardrailNote && (
            <div style={{ padding: 10, border: '1px solid var(--border-default)', borderRadius: 8, fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-faint)', lineHeight: 1.5 }}>
              Guardrails: metadata-only, not verified, not investment advice. No scan, no live AI, no auto-promotion, and no auto-verification.
            </div>
          )}
        </div>
      )}
    </section>
  );
}
