'use client';

import type { DocumentPackage, DocumentPackageItem } from '@/lib/api';

function readinessLabel(value: string): string {
  return value.replaceAll('_', ' ');
}

function statusClass(status: string): string {
  if (status === 'found') return 'status-badge status-badge--active';
  if (status === 'suggested') return 'status-badge status-badge--partial';
  if (status === 'missing') return 'status-badge status-badge--preview';
  if (status === 'needs_manual_check') return 'status-badge status-badge--manual';
  return 'status-badge status-badge--readonly';
}

function linkLabel(link: Record<string, unknown>): string {
  const value = link.label ?? link.title ?? link.url ?? link.expected_doc_type;
  return typeof value === 'string' && value ? value : 'Suggested link';
}

function DocumentRow({ item }: { item: DocumentPackageItem }) {
  const links = [...item.matched_links, ...item.suggested_links].slice(0, 2);
  return (
    <div style={{ display: 'grid', gap: 6, padding: '10px 0', borderTop: '1px solid var(--border-subtle)' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', gap: 12, alignItems: 'flex-start' }}>
        <div>
          <div style={{ fontSize: 13, color: 'var(--text-primary)', fontWeight: 600 }}>{item.label}</div>
          <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>{item.priority} / {item.source_hint}</div>
        </div>
        <span className={statusClass(item.status)}>{item.status.replaceAll('_', ' ')}</span>
      </div>
      {links.length > 0 && (
        <div style={{ display: 'grid', gap: 4 }}>
          {links.map((link, index) => (
            <div key={`${item.document_key}-${index}`} style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--text-muted)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
              {linkLabel(link)}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export function DocumentPackagePanel({
  packageData,
  loading,
  error,
}: {
  packageData: DocumentPackage | null;
  loading: boolean;
  error: string | null;
}) {
  const required = packageData?.documents.filter(item => item.priority === 'required') ?? [];
  const recommended = packageData?.documents.filter(item => item.priority === 'recommended') ?? [];
  const topActions = packageData?.manual_next_actions.slice(0, 4) ?? [];

  return (
    <section className="card" style={{ padding: 18 }}>
      <div className="card-header" style={{ alignItems: 'flex-start', gap: 12 }}>
        <div>
          <div className="card-title">Document Package</div>
          <div className="card-desc">Expected, found, missing, and manual-check documents. Ready for manual evaluation does not mean investment approval.</div>
        </div>
        {packageData && <span className="status-badge status-badge--readonly">{readinessLabel(packageData.readiness_level)}</span>}
      </div>

      {loading && <p className="card-desc" style={{ marginTop: 12 }}>Loading document package...</p>}
      {error && <p style={{ marginTop: 12, fontSize: 12, color: 'var(--status-error-text)' }}>{error}</p>}
      {packageData && !loading && (
        <div style={{ display: 'grid', gap: 14, marginTop: 14 }}>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <div className="metric-pill"><span className="metric-value">{packageData.summary.required_found}</span><span className="metric-label">Required found</span></div>
            <div className="metric-pill"><span className="metric-value">{packageData.summary.required_missing}</span><span className="metric-label">Required missing</span></div>
            <div className="metric-pill"><span className="metric-value">{packageData.summary.recommended_missing}</span><span className="metric-label">Recommended missing</span></div>
            <div className="metric-pill"><span className="metric-value">{packageData.summary.manual_actions_count}</span><span className="metric-label">Manual actions</span></div>
          </div>

          {packageData.warnings.length > 0 && (
            <div style={{ padding: 10, border: '1px solid var(--status-preview-border)', borderRadius: 8, color: 'var(--status-preview-text)', fontSize: 12 }}>
              {packageData.warnings[0]}
            </div>
          )}

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <div className="section-title" style={{ marginBottom: 4 }}>Required</div>
              {required.map(item => <DocumentRow key={item.document_key} item={item} />)}
            </div>
            <div>
              <div className="section-title" style={{ marginBottom: 4 }}>Recommended</div>
              {recommended.slice(0, 6).map(item => <DocumentRow key={item.document_key} item={item} />)}
            </div>
          </div>

          {topActions.length > 0 && (
            <div>
              <div className="section-title" style={{ marginBottom: 8 }}>Manual next actions</div>
              <div style={{ display: 'grid', gap: 6 }}>
                {topActions.map(action => (
                  <div key={action} style={{ fontSize: 12, color: 'var(--text-muted)' }}>{action}</div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </section>
  );
}
