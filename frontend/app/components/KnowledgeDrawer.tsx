'use client';

import { useEffect, useState } from 'react';
import { fetchKnowledgeEntry, type KnowledgeEntry } from '@/lib/api';

function label(value: string): string {
  return value.replaceAll('_', ' ');
}

function ListBlock({ title, items }: { title: string; items: string[] }) {
  if (items.length === 0) return null;
  return (
    <section style={{ display: 'grid', gap: 6 }}>
      <div className="section-title">{title}</div>
      <ul style={{ margin: 0, paddingLeft: 18, display: 'grid', gap: 4 }}>
        {items.map(item => <li key={item} style={{ fontSize: 12, color: 'var(--text-muted)' }}>{item}</li>)}
      </ul>
    </section>
  );
}

export function KnowledgeDrawer({
  knowledgeKey,
  onClose,
}: {
  knowledgeKey: string | null;
  onClose: () => void;
}) {
  const [entry, setEntry] = useState<KnowledgeEntry | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      if (!knowledgeKey) return;
      setLoading(true);
      setError(null);
      setEntry(null);
      try {
        const data = await fetchKnowledgeEntry(knowledgeKey);
        if (!cancelled) setEntry(data);
      } catch (err) {
        if (!cancelled) setError(err instanceof Error ? err.message : 'Failed to load knowledge entry');
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    load();
    return () => {
      cancelled = true;
    };
  }, [knowledgeKey]);

  if (!knowledgeKey) return null;

  return (
    <div style={{ position: 'fixed', inset: 0, zIndex: 80, pointerEvents: 'none' }}>
      <button
        type="button"
        aria-label="Close knowledge drawer backdrop"
        onClick={onClose}
        style={{ position: 'absolute', inset: 0, border: 0, background: 'rgba(15, 23, 42, 0.28)', pointerEvents: 'auto' }}
      />
      <aside
        role="dialog"
        aria-modal="true"
        aria-label="Knowledge drawer"
        style={{
          position: 'absolute',
          right: 0,
          top: 0,
          bottom: 0,
          width: 'min(440px, 100vw)',
          background: 'var(--bg-surface)',
          borderLeft: '1px solid var(--border-default)',
          boxShadow: 'var(--shadow-lg)',
          padding: 18,
          overflowY: 'auto',
          pointerEvents: 'auto',
          display: 'grid',
          alignContent: 'start',
          gap: 14,
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', gap: 12, alignItems: 'flex-start' }}>
          <div>
            <div style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-faint)', textTransform: 'uppercase' }}>
              Knowledge Base
            </div>
            <h2 style={{ margin: '4px 0 0', fontSize: 20, color: 'var(--text-primary)' }}>
              {entry?.title ?? 'Loading...'}
            </h2>
          </div>
          <button type="button" className="btn btn--ghost btn--sm" onClick={onClose}>Close</button>
        </div>

        {loading && <p className="card-desc">Loading knowledge entry...</p>}
        {error && <div style={{ color: 'var(--status-error-text)', fontSize: 12 }}>{error}</div>}
        {!loading && !error && !entry && <p className="card-desc">No knowledge entry available.</p>}

        {entry && (
          <>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
              <span className="status-badge status-badge--readonly">{label(entry.type)}</span>
              {entry.badges.map(badge => <span key={badge} className="status-badge status-badge--manual">{badge}</span>)}
            </div>

            <div style={{ padding: 10, border: '1px solid var(--border-default)', borderRadius: 8, fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-faint)' }}>
              Guidance only · Not evidence · Not verified · Not investment advice
            </div>

            <section style={{ display: 'grid', gap: 6 }}>
              <div className="section-title">Summary</div>
              <p style={{ margin: 0, fontSize: 13, color: 'var(--text-muted)', lineHeight: 1.5 }}>{entry.summary}</p>
            </section>

            <section style={{ display: 'grid', gap: 6 }}>
              <div className="section-title">Why It Matters</div>
              <p style={{ margin: 0, fontSize: 13, color: 'var(--text-muted)', lineHeight: 1.5 }}>{entry.why_it_matters}</p>
            </section>

            <section style={{ display: 'grid', gap: 8 }}>
              <div className="section-title">Where It Usually Appears</div>
              <ListBlock title="Primary sources" items={entry.where_it_usually_appears.primary_sources} />
              <ListBlock title="Secondary sources" items={entry.where_it_usually_appears.secondary_sources} />
              {entry.where_it_usually_appears.source_notes && (
                <div style={{ fontSize: 12, color: 'var(--text-faint)' }}>{entry.where_it_usually_appears.source_notes}</div>
              )}
            </section>

            <ListBlock title="Typical Sections" items={entry.typical_sections} />
            <ListBlock title="Search Terms" items={entry.search_terms} />

            {entry.helps_complete_fields.length > 0 && (
              <section style={{ display: 'grid', gap: 6 }}>
                <div className="section-title">Helps Complete Fields</div>
                {entry.helps_complete_fields.map(field => (
                  <div key={field.field_key} style={{ display: 'flex', justifyContent: 'space-between', gap: 10, fontSize: 12, color: 'var(--text-muted)' }}>
                    <span>{field.label}</span>
                    <span className="status-badge status-badge--readonly">{field.importance}</span>
                  </div>
                ))}
              </section>
            )}

            <details>
              <summary style={{ cursor: 'pointer', fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--text-muted)' }}>Course references</summary>
              <div style={{ display: 'grid', gap: 8, marginTop: 8 }}>
                {entry.course_references.map(ref => (
                  <div key={`${ref.chapter_id}-${ref.relevance}`} style={{ fontSize: 12, color: 'var(--text-muted)' }}>
                    <strong style={{ color: 'var(--text-primary)' }}>{ref.title}</strong> / {ref.relevance}<br />{ref.reason}
                  </div>
                ))}
              </div>
            </details>

            <details>
              <summary style={{ cursor: 'pointer', fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--text-muted)' }}>Course examples</summary>
              <div style={{ display: 'grid', gap: 8, marginTop: 8 }}>
                {entry.course_examples.map(example => (
                  <div key={example.label} style={{ fontSize: 12, color: 'var(--text-muted)' }}>
                    <strong style={{ color: 'var(--text-primary)' }}>{example.label}</strong> / {example.example_type}<br />{example.text}
                  </div>
                ))}
              </div>
            </details>

            <details>
              <summary style={{ cursor: 'pointer', fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--text-muted)' }}>Common mistakes</summary>
              <div style={{ marginTop: 8 }}><ListBlock title="Watch For" items={entry.common_mistakes} /></div>
            </details>

            <details>
              <summary style={{ cursor: 'pointer', fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--text-muted)' }}>Manual verification checklist</summary>
              <div style={{ marginTop: 8 }}><ListBlock title="Manual Checks" items={entry.manual_verification_checklist} /></div>
            </details>

            {entry.related_entries.length > 0 && (
              <details>
                <summary style={{ cursor: 'pointer', fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--text-muted)' }}>Related entries</summary>
                <div style={{ display: 'grid', gap: 6, marginTop: 8 }}>
                  {entry.related_entries.map(item => (
                    <div key={`${item.knowledge_key}-${item.relation}`} style={{ fontSize: 12, color: 'var(--text-muted)' }}>
                      {item.label} / {label(item.relation)}
                    </div>
                  ))}
                </div>
              </details>
            )}

            <div style={{ padding: 10, border: '1px solid var(--border-default)', borderRadius: 8, fontSize: 12, color: 'var(--text-muted)' }}>
              {entry.guardrail}
            </div>
          </>
        )}
      </aside>
    </div>
  );
}
