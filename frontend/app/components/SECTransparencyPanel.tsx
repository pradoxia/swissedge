'use client';

import type { DocumentPackage, Situation, SituationEvidenceLinksPackage } from '@/lib/api';

function label(value: string): string {
  return value.replaceAll('_', ' ');
}

function archiveDirectory(url: string | null | undefined): string | null {
  if (!url) return null;
  const index = url.lastIndexOf('/');
  return index > 'https://'.length ? url.slice(0, index + 1) : url;
}

function hasDocument(packageData: DocumentPackage | null, key: string): boolean {
  return Boolean(packageData?.documents.some(item =>
    item.document_key === key && ['found', 'needs_manual_check', 'suggested'].includes(item.status),
  ));
}

function strengthLabel(value: unknown): string {
  const normalized = String(value ?? '').toLowerCase();
  if (normalized === 'high') return 'Strong';
  if (normalized === 'medium') return 'Moderate';
  if (normalized === 'low') return 'Weak';
  return 'Needs review';
}

function transparencyLevel(yesCount: number, total: number): 'Strong' | 'Partial' | 'Weak' | 'Missing' {
  if (yesCount === 0) return 'Missing';
  if (yesCount >= total - 1) return 'Strong';
  if (yesCount >= Math.ceil(total / 2)) return 'Partial';
  return 'Weak';
}

function reviewStatus(reviewComplete: boolean): string {
  return reviewComplete ? 'Manual review recorded' : 'Needs Dani review';
}

function CheckRow({ label, value }: { label: string; value: boolean }) {
  return (
    <div style={{ display: 'flex', justifyContent: 'space-between', gap: 10, fontSize: 12 }}>
      <span style={{ color: 'var(--text-muted)' }}>{label}</span>
      <span className={`status-badge ${value ? 'status-badge--active' : 'status-badge--readonly'}`}>
        {value ? 'yes' : 'no'}
      </span>
    </div>
  );
}

export function SECTransparencyPanel({
  situation,
  secDetection,
  documentPackage,
  evidenceLinks,
}: {
  situation: Situation;
  secDetection: Record<string, unknown>;
  documentPackage: DocumentPackage | null;
  evidenceLinks: SituationEvidenceLinksPackage | null;
}) {
  const filingUrl = typeof secDetection.filing_url === 'string' ? secDetection.filing_url : situation.filing_url;
  const traceabilityChecks = [
    ['Official SEC filing', Boolean(filingUrl)],
    ['CIK', Boolean(secDetection.cik)],
    ['Accession', Boolean(secDetection.accession_number)],
    ['Filing date', Boolean(secDetection.filing_date || situation.detected_at)],
    ['Filing type', Boolean(secDetection.detected_form_type || situation.filing_type)],
    ['SEC directory', Boolean(archiveDirectory(filingUrl))],
    ['Expected documents identified', Boolean(documentPackage?.documents.length)],
  ] as const;
  const reviewChecks = [
    ['Exhibits reviewed', hasDocument(documentPackage, 'key_exhibits')],
    ['Amendments checked', hasDocument(documentPackage, 'amendments')],
    ['Verified evidence', Boolean(evidenceLinks?.links.some(link => link.verified))],
  ] as const;
  const yesCount = traceabilityChecks.filter(([, value]) => value).length;
  const level = transparencyLevel(yesCount, traceabilityChecks.length);
  const reviewComplete = reviewChecks.every(([, value]) => value);

  return (
    <section className="card" style={{ padding: 16, display: 'grid', gap: 12 }}>
      <div className="card-header" style={{ alignItems: 'flex-start', gap: 12 }}>
        <div>
          <div className="card-title">SEC Transparency</div>
          <div className="card-desc">Traceability to official SEC metadata and source package.</div>
        </div>
        <span className="status-badge status-badge--manual">SEC traceability: {level}</span>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: 8 }}>
        <div className="metric-pill">
          <span className="metric-value">{strengthLabel(secDetection.detection_confidence)}</span>
          <span className="metric-label">Classification Strength</span>
        </div>
        <div className="metric-pill">
          <span className="metric-value">{label(String(secDetection.detected_form_type ?? situation.filing_type ?? 'unknown'))}</span>
          <span className="metric-label">SEC signal</span>
        </div>
        <div className="metric-pill">
          <span className="metric-value">{level}</span>
          <span className="metric-label">SEC Traceability</span>
        </div>
        <div className="metric-pill">
          <span className="metric-value">{reviewStatus(reviewComplete)}</span>
          <span className="metric-label">Review Status</span>
        </div>
      </div>

      <div style={{ display: 'grid', gap: 6 }}>
        {[...traceabilityChecks, ...reviewChecks].map(([itemLabel, value]) => (
          <CheckRow key={itemLabel} label={itemLabel} value={value} />
        ))}
      </div>

      <div style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-faint)', lineHeight: 1.5 }}>
        Classification Strength explains why metadata supports the case type. SEC Transparency measures traceability to official SEC sources. Review Status shows what Dani has reviewed or accepted. None of these means investment approval.
      </div>
    </section>
  );
}
