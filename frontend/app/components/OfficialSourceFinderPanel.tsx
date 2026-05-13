'use client';

import type { OfficialSourceFinderPackage } from '@/lib/api';
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

function PillList({ values }: { values: string[] }) {
  if (!values.length) return <span style={{ color: 'var(--text-faint)' }}>-</span>;
  return (
    <span style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
      {values.map(value => <span key={value} className="status-badge status-badge--readonly">{value}</span>)}
    </span>
  );
}

export function OfficialSourceFinderPanel({
  finder,
  loading = false,
  error,
  copiedKey,
  onCopy,
}: {
  finder: OfficialSourceFinderPackage | null;
  loading?: boolean;
  error?: string | null;
  copiedKey?: string | null;
  onCopy: (text: string, key: string) => void;
}) {
  if (loading) {
    return (
      <div className="card">
        <LoadingState label="Loading Official Source Finder..." />
      </div>
    );
  }

  if (error) {
    return (
      <div className="card">
        <div className="section-header" style={{ marginBottom: 12 }}>
          <span className="section-title">Official Source Finder</span>
          <div className="section-line" />
        </div>
        <InfoBanner variant="warning">{error}</InfoBanner>
      </div>
    );
  }

  if (!finder) {
    return (
      <div className="card">
        <div className="section-header" style={{ marginBottom: 12 }}>
          <span className="section-title">Official Source Finder</span>
          <div className="section-line" />
        </div>
        <InfoBanner variant="info">No official-source finder package is available for this case yet.</InfoBanner>
      </div>
    );
  }

  const ctx = finder.source_context;

  return (
    <div className="card" id="official-source-finder">
      <div className="section-header" style={{ marginBottom: 12 }}>
        <span className="section-title">Official Source Finder</span>
        <div className="section-line" />
        <StatusBadge value="manual" />
      </div>

      <InfoBanner variant="guardrail">
        Manual official-source workbench only. SwissEdge did not run these searches, fetch SEC documents, crawl websites, download PDFs, or verify candidate sources.
      </InfoBanner>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(170px, 1fr))', gap: 10, marginTop: 14 }}>
        <MetaItem label="Source" value={ctx.source} />
        <MetaItem label="Company" value={ctx.company_name} />
        <MetaItem label="Ticker" value={ctx.ticker} />
        <MetaItem label="CIK" value={ctx.cik} />
        <MetaItem label="Accession" value={ctx.accession_number} />
        <MetaItem label="Filing type" value={ctx.filing_type} />
        <MetaItem label="Filing date" value={ctx.filing_date} />
        <MetaItem label="Playbook" value={ctx.selected_playbook} />
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: 10, marginTop: 14 }}>
        <MetaItem label="Official links" value={String(finder.coverage.stored_official_links_count)} />
        <MetaItem label="Missing official docs" value={String(finder.coverage.missing_required_documents_count)} />
        <MetaItem label="Manual queries" value={String(finder.coverage.manual_queries_count)} />
        <MetaItem label="Candidate sources" value={String(finder.coverage.candidate_sources_count)} />
      </div>

      {ctx.stored_filing_url && (
        <div style={{ marginTop: 14 }}>
          <a href={ctx.stored_filing_url} target="_blank" rel="noreferrer" className="btn btn--secondary btn--sm">
            Open stored SEC link
          </a>
        </div>
      )}

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: 14, marginTop: 16 }}>
        <div>
          <div style={labelStyle}>Official links already stored</div>
          <div style={{ display: 'grid', gap: 8, marginTop: 8 }}>
            {finder.official_links.length === 0 ? (
              <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>No stored official links yet.</div>
            ) : finder.official_links.map((link, index) => (
              <div key={`${link.url}-${index}`} style={{ border: '1px solid var(--border-default)', borderRadius: 6, padding: 10 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', gap: 8 }}>
                  <div style={{ fontSize: 13, fontWeight: 650, color: 'var(--text-primary)' }}>{link.label}</div>
                  <StatusBadge value={link.verified ? 'verified' : 'not verified'} />
                </div>
                {link.url && (
                  <a href={link.url} target="_blank" rel="noreferrer" style={{ display: 'block', marginTop: 6, fontSize: 12, color: 'var(--accent-cyan)', wordBreak: 'break-word' }}>
                    {link.url}
                  </a>
                )}
                <div style={{ marginTop: 6, fontSize: 12, color: 'var(--text-muted)' }}>{link.notes ?? 'Metadata-only link.'}</div>
                <div style={{ marginTop: 6 }}><PillList values={link.supports} /></div>
              </div>
            ))}
          </div>
        </div>

        <div>
          <div style={labelStyle}>Missing official document targets</div>
          <div style={{ display: 'grid', gap: 8, marginTop: 8 }}>
            {finder.missing_document_targets.length === 0 ? (
              <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>No missing official document target detected from stored workspace metadata.</div>
            ) : finder.missing_document_targets.map(target => (
              <div key={`${target.title}-${target.required_resource_id ?? target.checklist_item_id}`} style={{ border: '1px solid var(--border-default)', borderRadius: 6, padding: 10 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', gap: 8 }}>
                  <div style={{ fontSize: 13, fontWeight: 650, color: 'var(--text-primary)' }}>{target.title}</div>
                  <StatusBadge value={target.priority} />
                </div>
                <div style={{ marginTop: 6, fontSize: 12, color: 'var(--text-muted)' }}>{target.why_needed}</div>
                <div style={{ marginTop: 8 }}><PillList values={target.where_to_search} /></div>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div style={{ marginTop: 16 }}>
        <div style={labelStyle}>Manual locator steps</div>
        <div style={{ display: 'grid', gap: 8, marginTop: 8 }}>
          {finder.manual_locator_steps.map(step => (
            <div key={step.step} style={{ display: 'grid', gridTemplateColumns: '32px 1fr', gap: 10, border: '1px solid var(--border-default)', borderRadius: 6, padding: 10 }}>
              <div style={{ fontFamily: 'var(--font-mono)', color: 'var(--text-primary)' }}>{step.step}</div>
              <div>
                <div style={{ fontSize: 13, fontWeight: 650, color: 'var(--text-primary)' }}>{step.title}</div>
                <div style={{ marginTop: 4, fontSize: 12, color: 'var(--text-muted)' }}>{step.description}</div>
                {(step.supports_required_resources.length > 0 || step.supports_checklist_items.length > 0) && (
                  <div style={{ marginTop: 8, display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                    <PillList values={[...step.supports_required_resources, ...step.supports_checklist_items]} />
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>

      <div style={{ marginTop: 16 }}>
        <div style={labelStyle}>Copyable manual queries</div>
        <div style={{ display: 'grid', gap: 8, marginTop: 8 }}>
          {finder.copyable_queries.length === 0 ? (
            <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>No stored manual queries yet.</div>
          ) : finder.copyable_queries.map((query, index) => {
            const key = `official-source-query-${index}`;
            return (
              <div key={key} style={{ border: '1px solid var(--border-default)', borderRadius: 6, padding: 10 }}>
                <div style={{ fontFamily: 'var(--font-mono)', fontSize: 12, color: 'var(--text-primary)', wordBreak: 'break-word' }}>{query.query}</div>
                <div style={{ marginTop: 6, fontSize: 12, color: 'var(--text-muted)' }}>{query.purpose}</div>
                <div style={{ marginTop: 6, fontSize: 12, color: 'var(--text-faint)' }}>Use in: {query.where_to_use}. Not executed by SwissEdge.</div>
                <div style={{ marginTop: 8, display: 'flex', gap: 8, flexWrap: 'wrap', alignItems: 'center' }}>
                  <button type="button" className="btn btn--secondary btn--sm" onClick={() => onCopy(query.query, key)}>
                    {copiedKey === key ? 'Copied' : 'Copy query'}
                  </button>
                  <PillList values={[...query.supports_required_resources, ...query.supports_checklist_items]} />
                </div>
              </div>
            );
          })}
        </div>
      </div>

      <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginTop: 16 }}>
        {finder.guardrails.map(guardrail => <span key={guardrail} className="status-badge status-badge--readonly">{guardrail}</span>)}
      </div>
    </div>
  );
}
