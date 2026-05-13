'use client';

import type { EvidenceLink, SearchSuggestion } from '@/lib/api';

function label(value: string): string {
  return value.replace(/_/g, ' ').replace(/\b\w/g, char => char.toUpperCase());
}

function badgeClass(value: string): string {
  if (value === 'evidence_found' || value === 'verified') return 'status-badge status-badge--active';
  if (value === 'candidate_found' || value === 'metadata_only') return 'status-badge status-badge--partial';
  if (value === 'rejected') return 'status-badge status-badge--danger';
  return 'status-badge status-badge--readonly';
}

export function EvidenceLinksPanel({
  title = 'Evidence Links',
  links,
  guardrails,
  searchSuggestions = [],
  emptyText = 'No evidence links are stored yet.',
}: {
  title?: string;
  links: EvidenceLink[];
  guardrails: string[];
  searchSuggestions?: SearchSuggestion[];
  emptyText?: string;
}) {
  return (
    <div style={{ display: 'grid', gap: 12 }}>
      <div style={{ border: '1px solid var(--border-default)', borderRadius: 6, padding: '10px 12px', background: 'var(--bg-subtle)' }}>
        <div style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--text-muted)' }}>
          Traceability only — no AI evaluation, no recommendation, no publishing.
        </div>
        <div style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-faint)', marginTop: 4 }}>
          Links are metadata-only. No document body has been fetched. Evidence found does not mean verified.
        </div>
      </div>

      <div style={{ display: 'flex', justifyContent: 'space-between', gap: 12, alignItems: 'center', flexWrap: 'wrap' }}>
        <div>
          <div style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-faint)', textTransform: 'uppercase' }}>
            {title}
          </div>
          <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>{links.length} stored link{links.length === 1 ? '' : 's'}</div>
        </div>
      </div>

      {links.length === 0 ? (
        <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>{emptyText}</div>
      ) : (
        <div style={{ display: 'grid', gap: 8 }}>
          {links.map(link => (
            <div key={link.id} className="card" style={{ padding: '10px 12px', display: 'grid', gap: 8 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', gap: 12, alignItems: 'flex-start' }}>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ fontSize: 13, fontWeight: 650, color: 'var(--text-primary)' }}>{link.label}</div>
                  <div style={{ fontSize: 11, color: 'var(--text-muted)', wordBreak: 'break-all', marginTop: 2 }}>
                    {link.url ?? 'No stored URL; metadata only'}
                  </div>
                </div>
                {link.url && (
                  <a href={link.url} target="_blank" rel="noreferrer" className="btn btn--secondary btn--sm" style={{ flexShrink: 0 }}>
                    Open ↗
                  </a>
                )}
              </div>
              <div style={{ display: 'flex', gap: 5, flexWrap: 'wrap' }}>
                <span className="status-badge status-badge--readonly">{label(link.source_type)}</span>
                <span className="status-badge status-badge--readonly">{label(link.origin)}</span>
                <span className={badgeClass(link.status)}>{label(link.status)}</span>
                {link.metadata_only && <span className="status-badge status-badge--preview">Metadata only</span>}
                {!link.verified && <span className="status-badge status-badge--preview">Not verified</span>}
              </div>
              {(link.linked_required_resource_ids.length > 0 || link.linked_checklist_item_ids.length > 0) && (
                <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>
                  {link.linked_required_resource_ids.length > 0 && (
                    <div>Required resources: {link.linked_required_resource_ids.join(', ')}</div>
                  )}
                  {link.linked_checklist_item_ids.length > 0 && (
                    <div>Checklist items: {link.linked_checklist_item_ids.join(', ')}</div>
                  )}
                </div>
              )}
              {(link.accession_number || link.cik || link.filing_date || link.notes) && (
                <div style={{ fontSize: 11, color: 'var(--text-faint)' }}>
                  {link.accession_number && <span>Accession: {link.accession_number} </span>}
                  {link.cik && <span>CIK: {link.cik} </span>}
                  {link.filing_date && <span>Filed: {link.filing_date} </span>}
                  {link.notes && <div style={{ marginTop: 3 }}>{link.notes}</div>}
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {searchSuggestions.length > 0 && (
        <div style={{ borderTop: '1px solid var(--border-default)', paddingTop: 10 }}>
          <div style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-faint)', textTransform: 'uppercase', marginBottom: 6 }}>
            Manual search suggestions without stored links
          </div>
          <div style={{ fontSize: 11, color: 'var(--text-muted)', lineHeight: 1.5, marginBottom: 8 }}>
            Stored research prompts only. They are not fetched automatically, verified evidence, or proof that a search was performed.
          </div>
          <div style={{ display: 'grid', gap: 6 }}>
            {searchSuggestions.slice(0, 6).map(suggestion => (
              <div key={suggestion.suggestion_id} style={{ border: '1px solid var(--border-default)', borderRadius: 6, padding: '8px 10px' }}>
                <div style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-faint)', textTransform: 'uppercase', marginBottom: 3 }}>
                  Manual search suggestion
                </div>
                <div style={{ fontSize: 12, color: 'var(--text-primary)', wordBreak: 'break-word' }}>
                  {suggestion.query}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      <div style={{ display: 'flex', gap: 5, flexWrap: 'wrap' }}>
        {guardrails.map(guardrail => (
          <span key={guardrail} className="status-badge status-badge--readonly">{guardrail}</span>
        ))}
      </div>
    </div>
  );
}
