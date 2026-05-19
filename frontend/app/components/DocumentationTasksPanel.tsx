'use client';

import { KnowledgeInfoButton } from '@/app/components/KnowledgeInfoButton';
import type { DocumentationAgentDocument, DocumentationAgentReport, DocumentationExtractionField, Situation } from '@/lib/api';

function label(value: string): string {
  return value.replaceAll('_', ' ');
}

function knowledgeKeyForDocument(documentKey: string): string | null {
  const knownKeys = new Set([
    'sc_to_i',
    'offer_to_purchase',
    'letter_of_transmittal',
    'press_release',
    'sec_filing_detail',
    'key_exhibits',
  ]);
  return knownKeys.has(documentKey) ? documentKey : null;
}

function knowledgeKeyForPlaybook(playbook: string | null | undefined): string | null {
  if (!playbook) return null;
  const normalized = playbook.toLowerCase().replace(/\.md$/, '');
  if (normalized === 'issuer_tender_offer' || normalized === 'tender_offer') return 'issuer_tender_offer';
  return null;
}

function badgeClass(value: string): string {
  if (value === 'found_metadata') return 'status-badge status-badge--active';
  if (value === 'accepted' || value === 'edited') return 'status-badge status-badge--active';
  if (value === 'needs_manual_check') return 'status-badge status-badge--manual';
  if (value === 'missing') return 'status-badge status-badge--preview';
  if (value === 'draft') return 'status-badge status-badge--manual';
  if (value === 'critical' || value === 'rejected') return 'status-badge status-badge--danger';
  return 'status-badge status-badge--readonly';
}

function secArchiveDirectory(url: string | null | undefined): string | null {
  if (!url) return null;
  const trimmed = url.trim();
  const index = trimmed.lastIndexOf('/');
  if (index <= 'https://'.length) return trimmed;
  return trimmed.slice(0, index + 1);
}

function sourceUrl(doc: DocumentationAgentDocument, fallbackUrl: string | null): string | null {
  const link = [...doc.matched_links, ...doc.suggested_links].find(item => typeof item.url === 'string' && item.url);
  return typeof link?.url === 'string' ? link.url : fallbackUrl;
}

function relatedChecklist(report: DocumentationAgentReport, docKey: string): string | null {
  const item = report.checklist.find(check =>
    check.required_document_keys.includes(docKey) ||
    check.missing_document_keys.includes(docKey) ||
    check.manual_check_document_keys.includes(docKey),
  );
  return item?.label ?? null;
}

function whyItMatters(report: DocumentationAgentReport, docKey: string): string | null {
  const checklist = report.checklist.find(item => item.required_document_keys.includes(docKey));
  if (checklist?.why_it_matters) return checklist.why_it_matters;
  const info = report.required_information.find(item => {
    const docs = item.source_document_keys;
    return Array.isArray(docs) && docs.includes(docKey);
  });
  return typeof info?.why_it_matters === 'string' ? info.why_it_matters : null;
}

function candidateSources(doc: DocumentationAgentDocument): Array<Record<string, unknown>> {
  return [...doc.matched_links, ...doc.suggested_links].filter(link => {
    const status = typeof link.status === 'string' ? link.status : '';
    return status === 'candidate_found' || status === 'manual_review_required' || status === 'suggested';
  });
}

function sourceTitle(link: Record<string, unknown>): string {
  const label = link.label ?? link.title ?? link.source_domain ?? link.url;
  return typeof label === 'string' && label.trim() ? label.trim() : 'Candidate source';
}

function sourceDomain(link: Record<string, unknown>): string | null {
  if (typeof link.source_domain === 'string' && link.source_domain.trim()) return link.source_domain.trim();
  if (typeof link.url !== 'string' || !link.url) return null;
  try {
    return new URL(link.url).hostname;
  } catch {
    return null;
  }
}

function candidateId(link: Record<string, unknown>): string | null {
  const value = link.candidate_source_id ?? link.resource_candidate_id ?? link.id;
  return typeof value === 'string' && value ? value : null;
}

function pendingDocuments(report: DocumentationAgentReport): DocumentationAgentDocument[] {
  const byKey = new Map<string, DocumentationAgentDocument>();

  const addDocument = (doc: DocumentationAgentDocument) => {
    if (doc.status === 'found_metadata') return;
    if (!byKey.has(doc.document_key)) {
      byKey.set(doc.document_key, doc);
    }
  };

  report.critical_missing_documents.forEach(addDocument);
  report.documents_missing.forEach(addDocument);

  return [...byKey.values()];
}

function ExtractionFieldRow({
  field,
  reviewing,
  editing,
  editingValue,
  onReview,
  onStartEdit,
  onCancelEdit,
  onEditValue,
}: {
  field: DocumentationExtractionField;
  reviewing: boolean;
  editing: boolean;
  editingValue: string;
  onReview?: (field: DocumentationExtractionField, status: 'accepted' | 'rejected' | 'edited', value?: string) => void;
  onStartEdit?: (field: DocumentationExtractionField) => void;
  onCancelEdit?: () => void;
  onEditValue?: (value: string) => void;
}) {
  return (
    <div style={{ border: '1px solid var(--border-default)', borderRadius: 6, padding: 10, display: 'grid', gap: 8 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', gap: 10, alignItems: 'flex-start' }}>
        <div style={{ minWidth: 0 }}>
          <div style={{ fontSize: 12, fontWeight: 650, color: 'var(--text-primary)' }}>{field.field_label}</div>
          {editing ? (
            <input
              value={editingValue}
              onChange={event => onEditValue?.(event.target.value)}
              style={{ marginTop: 6, width: '100%', padding: '6px 8px', border: '1px solid var(--border-default)', borderRadius: 6, background: 'var(--bg-subtle)', color: 'var(--text-primary)' }}
            />
          ) : (
            <div style={{ marginTop: 3, fontSize: 12, color: 'var(--text-muted)' }}>{field.extracted_value ?? '-'}</div>
          )}
        </div>
        <span className={badgeClass(field.status)}>{label(field.status)}</span>
      </div>
      {field.source_snippet && (
        <div style={{ fontSize: 11, color: 'var(--text-faint)', lineHeight: 1.45 }}>
          Source snippet: {field.source_snippet}
        </div>
      )}
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
        {editing ? (
          <>
            <button className="btn btn--secondary btn--sm" disabled={reviewing} onClick={() => onReview?.(field, 'edited', editingValue)}>
              Save edit
            </button>
            <button className="btn btn--ghost btn--sm" disabled={reviewing} onClick={onCancelEdit}>
              Cancel
            </button>
          </>
        ) : (
          <>
            <button className="btn btn--secondary btn--sm" disabled={reviewing || field.status === 'accepted'} onClick={() => onReview?.(field, 'accepted')}>
              Accept
            </button>
            <button className="btn btn--secondary btn--sm" disabled={reviewing} onClick={() => onStartEdit?.(field)}>
              Edit
            </button>
            <button className="btn btn--ghost btn--sm" disabled={reviewing || field.status === 'rejected'} onClick={() => onReview?.(field, 'rejected')}>
              Reject
            </button>
          </>
        )}
      </div>
    </div>
  );
}

export function DocumentationTasksPanel({
  report,
  situation,
  onAddSourceLink,
  extractionFields = [],
  extractionError = null,
  readingDraftKey = null,
  reviewingExtractionId = null,
  editingExtractionId = null,
  editingExtractionValue = '',
  onReadAndMapDraft,
  onReviewExtraction,
  onStartEditExtraction,
  onCancelEditExtraction,
  onEditExtractionValue,
}: {
  report: DocumentationAgentReport | null;
  situation: Situation;
  onAddSourceLink?: (task: DocumentationAgentDocument) => void;
  extractionFields?: DocumentationExtractionField[];
  extractionError?: string | null;
  readingDraftKey?: string | null;
  reviewingExtractionId?: string | null;
  editingExtractionId?: string | null;
  editingExtractionValue?: string;
  onReadAndMapDraft?: (task: DocumentationAgentDocument, candidateSourceId: string) => void;
  onReviewExtraction?: (field: DocumentationExtractionField, status: 'accepted' | 'rejected' | 'edited', value?: string) => void;
  onStartEditExtraction?: (field: DocumentationExtractionField) => void;
  onCancelEditExtraction?: () => void;
  onEditExtractionValue?: (value: string) => void;
}) {
  if (!report) {
    return (
      <section className="card" style={{ padding: 18 }}>
        <div className="card-title">Documentation Tasks</div>
        <p className="card-desc" style={{ marginTop: 8 }}>No documentation report available yet.</p>
      </section>
    );
  }

  const tasks = pendingDocuments(report);
  const archiveUrl = secArchiveDirectory(situation.filing_url);
  const playbookTitle = report.applicable_playbooks[0] ? label(report.applicable_playbooks[0]) : label(report.case_type);

  return (
    <section className="card" style={{ padding: 18 }}>
      <div className="card-header" style={{ alignItems: 'flex-start', gap: 12 }}>
        <div>
          <div className="card-title">Documentation Tasks</div>
          <div className="card-desc">Pending documents Dani can collect, link, and later map manually.</div>
        </div>
        <span className="status-badge status-badge--manual">{tasks.length} pending</span>
      </div>

      <div style={{ display: 'grid', gap: 14, marginTop: 14 }}>
        <details style={{ border: '1px solid var(--border-default)', borderRadius: 8, padding: 12, background: 'var(--bg-subtle)' }}>
          <summary style={{ cursor: 'pointer', fontWeight: 650, color: 'var(--text-primary)' }}>
            <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
              Playbook: {playbookTitle}
              <KnowledgeInfoButton
                knowledgeKey={knowledgeKeyForPlaybook(report.applicable_playbooks[0] ?? report.case_type)}
                label={playbookTitle}
              />
            </span>
            <span style={{ marginLeft: 8, fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-faint)' }}>Open guide</span>
          </summary>
          <div style={{ display: 'grid', gap: 12, marginTop: 12 }}>
            <div>
              <div className="section-title" style={{ marginBottom: 6 }}>Course chapters</div>
              <ul style={{ margin: 0, paddingLeft: 18 }}>
                {report.course_chapters.slice(0, 4).map(chapter => (
                  <li key={chapter.chapter_id} style={{ fontSize: 12, color: 'var(--text-muted)' }}>
                    {chapter.title}: {chapter.reason}
                  </li>
                ))}
              </ul>
            </div>
            <div>
              <div className="section-title" style={{ marginBottom: 6 }}>Required information</div>
              <ul style={{ margin: 0, paddingLeft: 18 }}>
                {report.required_information.slice(0, 5).map(item => (
                  <li key={String(item.info_key ?? item.label)} style={{ fontSize: 12, color: 'var(--text-muted)' }}>
                    {String(item.label ?? 'Required information')}
                  </li>
                ))}
              </ul>
            </div>
            <div>
              <div className="section-title" style={{ marginBottom: 6 }}>Checklist focus</div>
              <div style={{ display: 'grid', gap: 6 }}>
                {report.checklist.slice(0, 5).map(item => (
                  <div key={item.key} style={{ display: 'flex', justifyContent: 'space-between', gap: 10, fontSize: 12 }}>
                    <span style={{ color: 'var(--text-muted)' }}>{item.label}</span>
                    <span className={badgeClass(item.status)}>{label(item.status)}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </details>

        <div style={{ padding: 10, border: '1px solid var(--border-default)', borderRadius: 8, fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-faint)', lineHeight: 1.5 }}>
          SwissEdge may store or extract draft information, but Dani must review and approve before anything becomes verified evidence.
        </div>
        {extractionError && (
          <div style={{ padding: 10, border: '1px solid var(--status-preview-border)', borderRadius: 8, color: 'var(--status-preview-text)', fontSize: 12 }}>
            {extractionError}
          </div>
        )}

        {tasks.length === 0 ? (
          <p className="card-desc">No missing or manual-check documents are currently surfaced.</p>
        ) : (
          <div style={{ display: 'grid', gap: 10 }}>
            {tasks.map(doc => {
              const openUrl = sourceUrl(doc, archiveUrl);
              const checklist = relatedChecklist(report, doc.document_key);
              const reason = whyItMatters(report, doc.document_key);
              const candidates = candidateSources(doc);
              const latestCandidate = candidates[0];
              const latestDomain = latestCandidate ? sourceDomain(latestCandidate) : null;
              const latestCandidateId = latestCandidate ? candidateId(latestCandidate) : null;
              const fields = extractionFields.filter(field => field.document_key === doc.document_key);
              const acceptedFields = fields.filter(field => field.status === 'accepted' || field.status === 'edited');
              const draftFields = fields.filter(field => field.status === 'draft');
              const rejectedFields = fields.filter(field => field.status === 'rejected');
              return (
                <div key={doc.document_key} style={{ border: '1px solid var(--border-default)', borderRadius: 8, padding: 12, display: 'grid', gap: 10 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', gap: 12, alignItems: 'flex-start' }}>
                    <div style={{ minWidth: 0 }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 6, minWidth: 0 }}>
                        <span style={{ fontSize: 13, fontWeight: 650, color: 'var(--text-primary)' }}>{doc.label}</span>
                        <KnowledgeInfoButton knowledgeKey={knowledgeKeyForDocument(doc.document_key)} label={doc.label} />
                      </div>
                      <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>
                        {label(doc.importance)} / expected from {doc.source_hint}
                      </div>
                    </div>
                    <span className={badgeClass(doc.status)}>{label(doc.status)}</span>
                  </div>

                  {(reason || checklist) && (
                    <div style={{ fontSize: 12, color: 'var(--text-muted)', lineHeight: 1.45 }}>
                      {reason && <div>{reason}</div>}
                      {checklist && <div style={{ marginTop: 3 }}>Related checklist: {checklist}</div>}
                    </div>
                  )}

                  {latestCandidate && (
                    <div style={{ padding: 8, border: '1px solid var(--border-default)', borderRadius: 6, background: 'var(--bg-subtle)', fontSize: 12, color: 'var(--text-muted)', lineHeight: 1.45 }}>
                      <strong style={{ color: 'var(--text-primary)' }}>Candidate source added — needs review</strong>
                      <div>
                        {candidates.length} candidate source{candidates.length === 1 ? '' : 's'} · {sourceTitle(latestCandidate)}
                        {latestDomain ? ` / ${latestDomain}` : ''} · not verified
                      </div>
                    </div>
                  )}

                  {fields.length > 0 && (
                    <div style={{ display: 'grid', gap: 8 }}>
                      <div className="section-title">Draft extracted fields</div>
                      {acceptedFields.length > 0 && (
                        <div style={{ display: 'grid', gap: 6 }}>
                          <div style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-faint)', textTransform: 'uppercase' }}>Accepted / edited by Dani</div>
                          {acceptedFields.map(field => (
                            <ExtractionFieldRow
                              key={field.id}
                              field={field}
                              reviewing={reviewingExtractionId === field.id}
                              editing={editingExtractionId === field.id}
                              editingValue={editingExtractionValue}
                              onReview={onReviewExtraction}
                              onStartEdit={onStartEditExtraction}
                              onCancelEdit={onCancelEditExtraction}
                              onEditValue={onEditExtractionValue}
                            />
                          ))}
                        </div>
                      )}
                      {draftFields.length > 0 && (
                        <div style={{ display: 'grid', gap: 6 }}>
                          <div style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-faint)', textTransform: 'uppercase' }}>Draft suggestions / not verified</div>
                          {draftFields.map(field => (
                            <ExtractionFieldRow
                              key={field.id}
                              field={field}
                              reviewing={reviewingExtractionId === field.id}
                              editing={editingExtractionId === field.id}
                              editingValue={editingExtractionValue}
                              onReview={onReviewExtraction}
                              onStartEdit={onStartEditExtraction}
                              onCancelEdit={onCancelEditExtraction}
                              onEditValue={onEditExtractionValue}
                            />
                          ))}
                        </div>
                      )}
                      {rejectedFields.length > 0 && (
                        <details>
                          <summary style={{ cursor: 'pointer', fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-faint)' }}>
                            Rejected draft fields ({rejectedFields.length})
                          </summary>
                          <div style={{ display: 'grid', gap: 6, marginTop: 8 }}>
                            {rejectedFields.map(field => (
                              <ExtractionFieldRow
                                key={field.id}
                                field={field}
                                reviewing={reviewingExtractionId === field.id}
                                editing={editingExtractionId === field.id}
                                editingValue={editingExtractionValue}
                                onReview={onReviewExtraction}
                                onStartEdit={onStartEditExtraction}
                                onCancelEdit={onCancelEditExtraction}
                                onEditValue={onEditExtractionValue}
                              />
                            ))}
                          </div>
                        </details>
                      )}
                      <div style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-faint)' }}>
                        Draft values are not verified evidence and do not update accepted case fields automatically.
                      </div>
                    </div>
                  )}

                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
                    {openUrl ? (
                      <a href={openUrl} target="_blank" rel="noreferrer" className="btn btn--secondary btn--sm">
                        {openUrl === archiveUrl ? 'Open SEC directory' : 'Open source'}
                      </a>
                    ) : (
                      <span style={{ alignSelf: 'center', fontSize: 11, color: 'var(--text-faint)' }}>No source URL mapped yet.</span>
                    )}
                    <button
                      type="button"
                      className="btn btn--secondary btn--sm"
                      onClick={() => onAddSourceLink?.(doc)}
                    >
                      Add source link
                    </button>
                    {latestCandidateId && (
                      <button
                        type="button"
                        className="btn btn--secondary btn--sm"
                        disabled={!onReadAndMapDraft || readingDraftKey === `${doc.document_key}:${latestCandidateId}`}
                        onClick={() => onReadAndMapDraft?.(doc, latestCandidateId)}
                      >
                        {readingDraftKey === `${doc.document_key}:${latestCandidateId}` ? 'Reading draft...' : 'Read & map draft'}
                      </button>
                    )}
                    <span style={{ alignSelf: 'center', fontSize: 11, color: 'var(--text-faint)' }}>
                      Opens manual source form below.
                    </span>
                    <span style={{ alignSelf: 'center', fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-faint)' }}>
                      Coming next: Upload document · Mark reviewed manually
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </section>
  );
}
