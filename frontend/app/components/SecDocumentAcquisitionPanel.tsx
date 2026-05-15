'use client';

import type { SecDocumentAcquisitionPackage } from '@/lib/api';
import { InfoBanner, LoadingState, StatusBadge } from '@/app/components/ui';

const labelStyle = {
  fontFamily: 'var(--font-mono)',
  fontSize: 10,
  color: 'var(--text-faint)',
  textTransform: 'uppercase' as const,
  letterSpacing: 0,
};

function valueText(value: string | null | undefined) {
  return value && value.trim() ? value : '-';
}

function MetaItem({ label, value }: { label: string; value: string | null | undefined }) {
  return (
    <div style={{ border: '1px solid var(--border-default)', borderRadius: 6, padding: 10, background: 'var(--bg-subtle)' }}>
      <div style={labelStyle}>{label}</div>
      <div style={{ marginTop: 4, fontSize: 13, color: 'var(--text-primary)', wordBreak: 'break-word' }}>{valueText(value)}</div>
    </div>
  );
}

export function SecDocumentAcquisitionPanel({
  packageData,
  loading = false,
  acquiring = false,
  error,
  copiedKey,
  onCopy,
  onAcquire,
}: {
  packageData: SecDocumentAcquisitionPackage | null;
  loading?: boolean;
  acquiring?: boolean;
  error?: string | null;
  copiedKey?: string | null;
  onCopy: (text: string, key: string) => void;
  onAcquire: () => void;
}) {
  const copyFailed = copiedKey === 'copy-failed';

  if (loading) {
    return (
      <div className="card">
        <LoadingState label="Loading SEC document acquisition preview..." />
      </div>
    );
  }

  if (!packageData) {
    return (
      <div className="card" id="sec-document-acquisition">
        <div className="section-header" style={{ marginBottom: 12 }}>
          <span className="section-title">SEC EDGAR Document Acquisition</span>
          <div className="section-line" />
        </div>
        <InfoBanner variant={error ? 'warning' : 'info'}>
          {error ?? 'No SEC document acquisition preview is available for this case yet.'}
        </InfoBanner>
      </div>
    );
  }

  const ids = packageData.available_identifiers;

  return (
    <div className="card" id="sec-document-acquisition">
      <div className="section-header" style={{ marginBottom: 12 }}>
        <span className="section-title">SEC EDGAR Document Acquisition</span>
        <div className="section-line" />
        <StatusBadge value="manual" />
      </div>

      <InfoBanner variant="guardrail">
        SEC documents are acquired as official source candidates. Evidence remains unverified until manual review. This button only uses SEC EDGAR metadata and does not evaluate, publish, promote, or run a scanner.
      </InfoBanner>

      {error && <div style={{ marginTop: 12 }}><InfoBanner variant="warning">{error}</InfoBanner></div>}

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(170px, 1fr))', gap: 10, marginTop: 14 }}>
        <MetaItem label="Company" value={ids.company_name} />
        <MetaItem label="Ticker" value={ids.ticker} />
        <MetaItem label="CIK" value={ids.cik} />
        <MetaItem label="Accession" value={ids.accession_number} />
        <MetaItem label="Filing type" value={ids.filing_type} />
        <MetaItem label="Filing date" value={ids.filing_date} />
      </div>

      {ids.filing_url && (
        <div style={{ marginTop: 12 }}>
          <a href={ids.filing_url} target="_blank" rel="noreferrer" className="btn btn--secondary btn--sm">
            Open stored SEC link
          </a>
        </div>
      )}

      {packageData.missing_identifiers.length > 0 && (
        <div style={{ marginTop: 14 }}>
          <div style={labelStyle}>Missing identifiers</div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginTop: 8 }}>
            {packageData.missing_identifiers.map(item => <span key={item} className="status-badge status-badge--preview">{item}</span>)}
          </div>
        </div>
      )}

      <div style={{ marginTop: 16, display: 'flex', gap: 10, flexWrap: 'wrap', alignItems: 'center' }}>
        <button type="button" className="btn btn--primary btn--sm" onClick={onAcquire} disabled={acquiring}>
          {acquiring ? 'Acquiring...' : 'Acquire SEC Documents'}
        </button>
        <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>
          Manual trigger only. Stores metadata/candidates, not verified evidence.
        </span>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: 14, marginTop: 16 }}>
        <div>
          <div style={labelStyle}>Likely official document targets</div>
          <div style={{ display: 'grid', gap: 8, marginTop: 8 }}>
            {packageData.likely_document_targets.map(target => (
              <div key={`${target.label}-${target.expected_doc_type}`} style={{ border: '1px solid var(--border-default)', borderRadius: 6, padding: 10 }}>
                <div style={{ fontSize: 13, fontWeight: 650, color: 'var(--text-primary)' }}>{target.label}</div>
                <div style={{ marginTop: 4, fontSize: 12, color: 'var(--text-muted)' }}>{target.reason}</div>
                <div style={{ marginTop: 6 }}><StatusBadge value={target.expected_doc_type} /></div>
              </div>
            ))}
          </div>
        </div>

        <div>
          <div style={labelStyle}>Acquired / official metadata</div>
          <div style={{ display: 'grid', gap: 8, marginTop: 8 }}>
            {packageData.acquired_documents.length === 0 && packageData.official_links.length === 0 ? (
              <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>No document metadata acquired yet.</div>
            ) : [...packageData.acquired_documents, ...packageData.official_links].map((doc, index) => (
              <div key={`${doc.url}-${index}`} style={{ border: '1px solid var(--border-default)', borderRadius: 6, padding: 10 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', gap: 8 }}>
                  <div style={{ minWidth: 0, fontSize: 13, fontWeight: 650, color: 'var(--text-primary)', overflowWrap: 'anywhere' }}>{doc.title}</div>
                  <StatusBadge value={doc.verified ? 'verified' : 'not verified'} />
                </div>
                <a href={doc.url} target="_blank" rel="noreferrer" style={{ display: 'block', marginTop: 6, fontSize: 12, color: 'var(--accent-cyan)', wordBreak: 'break-word' }}>
                  {doc.url}
                </a>
                <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginTop: 6 }}>
                  <StatusBadge value={doc.doc_type} />
                  <StatusBadge value={doc.acquisition_status} />
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div style={{ marginTop: 16 }}>
        <div style={labelStyle}>Manual locator steps</div>
        <div style={{ display: 'grid', gap: 8, marginTop: 8 }}>
          {packageData.manual_locator_steps.map(step => (
            <div key={step.step} style={{ display: 'grid', gridTemplateColumns: '32px 1fr', gap: 10, border: '1px solid var(--border-default)', borderRadius: 6, padding: 10 }}>
              <div style={{ fontFamily: 'var(--font-mono)', color: 'var(--text-primary)' }}>{step.step}</div>
              <div>
                <div style={{ fontSize: 13, fontWeight: 650, color: 'var(--text-primary)' }}>{step.title}</div>
                <div style={{ marginTop: 4, fontSize: 12, color: 'var(--text-muted)' }}>{step.description}</div>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div style={{ marginTop: 16 }}>
        <div style={labelStyle}>Copyable SEC queries</div>
        <div style={{ marginTop: 4, fontSize: 12, color: copyFailed ? '#b45309' : 'var(--text-muted)' }}>
          {copyFailed ? 'Copy failed - select the query text manually.' : 'Paste this into SEC EDGAR search. SwissEdge has not run this search automatically.'}
        </div>
        <div style={{ display: 'grid', gap: 8, marginTop: 8 }}>
          {packageData.copyable_queries.map((query, index) => {
            const key = `sec-acquisition-query-${index}`;
            return (
              <div key={key} style={{ border: '1px solid var(--border-default)', borderRadius: 6, padding: 10 }}>
                <div style={{ fontFamily: 'var(--font-mono)', fontSize: 12, color: 'var(--text-primary)', wordBreak: 'break-word' }}>{query.query}</div>
                <div style={{ marginTop: 6, fontSize: 12, color: 'var(--text-muted)' }}>{query.purpose}</div>
                <button type="button" className="btn btn--secondary btn--sm" style={{ marginTop: 8 }} onClick={() => onCopy(query.query, key)}>
                  {copiedKey === key ? 'Copied' : 'Copy query'}
                </button>
              </div>
            );
          })}
        </div>
      </div>

      {(packageData.warnings.length > 0 || packageData.manual_next_steps.length > 0) && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: 12, marginTop: 16 }}>
          <InfoBanner variant="warning">{packageData.warnings.length ? packageData.warnings.join(' ') : 'No acquisition warnings.'}</InfoBanner>
          <InfoBanner variant="info">{packageData.manual_next_steps.join(' ')}</InfoBanner>
        </div>
      )}

      <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginTop: 16 }}>
        {packageData.guardrails.map(guardrail => <span key={guardrail} className="status-badge status-badge--readonly">{guardrail}</span>)}
      </div>
    </div>
  );
}
