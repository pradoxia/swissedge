'use client';

import type { CSSProperties } from 'react';
import { useEffect, useMemo, useState } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import {
  ErrorBanner,
  InfoBanner,
  LoadingState,
  PageHeader,
  SectionCard,
  StatusBadge,
} from '@/app/components/ui';
import {
  addSituationResource,
  fetchSituation,
  promoteSituationToResearchCase,
  updateSituationResourceCandidate,
  updateSituationWorkflowStatus,
  type MethodologyChecklistItem,
  type MethodologyWorkspace,
  type RequiredResourceItem,
  type ResourceCandidate,
  type Situation,
} from '@/lib/api';

const MONO_LABEL: CSSProperties = {
  fontFamily: 'var(--font-mono)',
  fontSize: 10,
  textTransform: 'uppercase',
  letterSpacing: '0.06em',
  color: 'var(--text-faint)',
  marginBottom: 3,
};

const INPUT_STYLE: CSSProperties = {
  width: '100%',
  padding: '7px 10px',
  border: '1px solid var(--border-default)',
  borderRadius: 6,
  fontFamily: 'var(--font-mono)',
  fontSize: 12,
  background: 'var(--bg-subtle)',
  color: 'var(--text-primary)',
  outline: 'none',
  boxSizing: 'border-box',
};

const WORKFLOW_OPTIONS = [
  ['new_detection', 'New Detection'],
  ['triage_needed', 'Triage Needed'],
  ['needs_resources', 'Needs Resources'],
  ['checklist_in_progress', 'Checklist In Progress'],
  ['ready_for_research_case', 'Ready for ResearchCase'],
  ['watchlist', 'Watchlist'],
  ['ignored', 'Ignored'],
] as const;

const SOURCE_TYPES = [
  'sec_filing',
  'company_ir',
  'press_release',
  'transaction_page',
  'offer_document',
  'pdf_link',
  'news',
  'market_data_reference',
  'other',
];

function display(value: unknown): string {
  if (value === null || value === undefined || value === '') return '-';
  return String(value);
}

function resourceStatusClass(status: string): string {
  if (status === 'missing') return 'status-badge--preview';
  if (status === 'candidate_found') return 'status-badge--partial';
  if (status === 'evidence_found' || status === 'verified') return 'status-badge--active';
  if (status === 'rejected') return 'status-badge--danger';
  return 'status-badge--readonly';
}

function groupChecklist(items: MethodologyChecklistItem[]) {
  return items.reduce<Record<string, MethodologyChecklistItem[]>>((groups, item) => {
    const key = item.section || 'General';
    groups[key] = groups[key] ?? [];
    groups[key].push(item);
    return groups;
  }, {});
}

function ResourceTable({ resources }: { resources: RequiredResourceItem[] }) {
  if (resources.length === 0) return null;
  return (
    <div style={{ overflowX: 'auto' }}>
      <table className="data-table">
        <thead>
          <tr>
            <th>Resource</th>
            <th>Source</th>
            <th>Status</th>
            <th>Expected From</th>
          </tr>
        </thead>
        <tbody>
          {resources.map(r => (
            <tr key={r.resource_id}>
              <td>
                <div style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{r.title}</div>
                <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 2 }}>{r.description}</div>
              </td>
              <td style={{ color: 'var(--text-muted)' }}>{r.source_type}</td>
              <td>
                <span className={`status-badge ${resourceStatusClass(r.status)}`}>{r.status}</span>
              </td>
              <td style={{ fontSize: 12, color: 'var(--text-muted)' }}>{r.expected_source}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default function SpecialSituationMethodologyPage() {
  const params = useParams();
  const id = params.id as string;
  const [situation, setSituation] = useState<Situation | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [resourceForm, setResourceForm] = useState({
    title: '',
    url: '',
    source_type: 'other',
    notes: '',
    related_resource_id: '',
    related_check_id: '',
  });
  const [resourceMessage, setResourceMessage] = useState<string | null>(null);
  const [resourceError, setResourceError] = useState<string | null>(null);
  const [savingResource, setSavingResource] = useState(false);
  const [savingWorkflow, setSavingWorkflow] = useState(false);
  const [promoting, setPromoting] = useState(false);
  const [promotionMessage, setPromotionMessage] = useState<string | null>(null);
  const [savingCandidateId, setSavingCandidateId] = useState<string | null>(null);
  const [suggestionsOpen, setSuggestionsOpen] = useState(false);
  const [copiedKey, setCopiedKey] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      try {
        setLoading(true);
        setError(null);
        setSituation(await fetchSituation(id));
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load situation');
      } finally {
        setLoading(false);
      }
    }
    if (id) load();
  }, [id]);

  const workspace = (situation?.methodology_workspace ?? situation?.evaluation?.methodology_workspace ?? null) as MethodologyWorkspace | null;
  const secDetection = situation?.evaluation?.sec_detection ?? {};
  const checklistGroups = useMemo(
    () => groupChecklist(workspace?.checklist ?? []),
    [workspace],
  );
  const progress = workspace?.progress;
  const requiredResources = workspace?.required_resources ?? [];
  const requiredOnly = requiredResources.filter(r => r.required_or_optional === 'required');
  const optionalOnly = requiredResources.filter(r => r.required_or_optional !== 'required');
  const resourceCandidates = workspace?.resource_candidates ?? [];
  const searchSuggestions = workspace?.search_suggestions ?? [];
  const workflowStatus = workspace?.workflow_status ?? (situation?.status === 'detected' ? 'new_detection' : situation?.status ?? 'new_detection');
  const researchCaseId = workspace?.research_case_id;

  function copyText(text: string, key: string) {
    navigator.clipboard.writeText(text).catch(() => {});
    setCopiedKey(key);
    setTimeout(() => setCopiedKey(null), 1500);
  }

  async function handleAddResource() {
    if (!situation) return;
    setSavingResource(true);
    setResourceMessage(null);
    setResourceError(null);
    try {
      const result = await addSituationResource(situation.id, {
        title: resourceForm.title,
        url: resourceForm.url,
        source_type: resourceForm.source_type,
        notes: resourceForm.notes || undefined,
        related_resource_ids: resourceForm.related_resource_id ? [resourceForm.related_resource_id] : undefined,
        related_check_ids: resourceForm.related_check_id ? [resourceForm.related_check_id] : undefined,
      });
      setSituation(result.situation);
      setResourceForm({ title: '', url: '', source_type: 'other', notes: '', related_resource_id: '', related_check_id: '' });
      setResourceMessage(result.created ? 'Resource candidate added.' : 'Resource candidate already exists.');
    } catch (err) {
      setResourceError(err instanceof Error ? err.message : 'Failed to add resource');
    } finally {
      setSavingResource(false);
    }
  }

  async function handleWorkflowChange(nextStatus: string) {
    if (!situation) return;
    setSavingWorkflow(true);
    setError(null);
    try {
      const result = await updateSituationWorkflowStatus(situation.id, nextStatus);
      setSituation(result.situation);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update workflow status');
    } finally {
      setSavingWorkflow(false);
    }
  }

  async function handleCandidatePatch(
    candidate: ResourceCandidate,
    payload: {
      status?: string;
      notes?: string;
      related_resource_ids?: string[];
      related_check_ids?: string[];
    },
  ) {
    if (!situation) return;
    setSavingCandidateId(candidate.resource_candidate_id);
    setResourceError(null);
    try {
      const result = await updateSituationResourceCandidate(situation.id, candidate.resource_candidate_id, payload);
      setSituation(result.situation);
    } catch (err) {
      setResourceError(err instanceof Error ? err.message : 'Failed to update resource candidate');
    } finally {
      setSavingCandidateId(null);
    }
  }

  async function handlePromote() {
    if (!situation) return;
    const confirmed = window.confirm(
      'This will create a ResearchCase for deeper analysis. It will not evaluate, recommend, or publish.',
    );
    if (!confirmed) return;
    setPromoting(true);
    setPromotionMessage(null);
    setError(null);
    try {
      const result = await promoteSituationToResearchCase(situation.id, {
        initial_status: 'under_investigation',
      });
      setPromotionMessage(result.created ? 'ResearchCase created.' : 'ResearchCase already existed.');
      setSituation({
        ...situation,
        methodology_workspace: {
          ...workspace!,
          research_case_id: result.research_case.id,
          workflow_status: 'promoted_to_research_case',
        },
        evaluation: {
          ...situation.evaluation,
          methodology_workspace: {
            ...(situation.evaluation?.methodology_workspace ?? workspace ?? {}),
            research_case_id: result.research_case.id,
            workflow_status: 'promoted_to_research_case',
          },
        },
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to promote situation');
    } finally {
      setPromoting(false);
    }
  }

  if (loading) return <div className="page-container--wide"><LoadingState label="Loading methodology workspace..." /></div>;
  if (error || !situation) {
    return (
      <div className="page-container--wide">
        <ErrorBanner message={error ?? 'Situation not found'} />
        <Link href="/investment/situations" className="nav-back">Back to situations</Link>
      </div>
    );
  }

  return (
    <div className="page-container--wide">
      <PageHeader
        title={situation.company_name}
        subtitle="Methodology workspace"
        backHref="/investment/situations"
        backLabel="Special Situations"
        badge={<StatusBadge value={situation.status} />}
        actions={
          <Link href={`/investment/evaluations/${situation.id}`} className="btn btn--secondary btn--sm">
            Evaluation Detail
          </Link>
        }
      />

      <InfoBanner variant="guardrail">
        Detected does not mean evaluated. Checklist attached does not mean verified. Resource listed does not mean evidence accepted. Final verification remains human-reviewed.
      </InfoBanner>

      {error && <ErrorBanner message={error} />}

      {/* Compact top summary strip */}
      <div className="card" style={{ padding: '14px 18px', display: 'flex', flexWrap: 'wrap', gap: '14px 32px', alignItems: 'flex-start' }}>
        {([
          ['Ticker', situation.ticker],
          ['Type', secDetection.situation_type ?? situation.situation_type],
          ['Subtype', secDetection.subtype],
          ['Filing', secDetection.detected_form_type ?? situation.filing_type],
          ['Filing Date', secDetection.filing_date],
          ['Playbook', secDetection.selected_playbook ?? situation.selected_playbook],
          ['Confidence', secDetection.detection_confidence],
        ] as [string, unknown][]).map(([label, value]) => (
          <div key={label}>
            <div style={MONO_LABEL}>{label}</div>
            <div style={{ fontSize: 13, color: 'var(--text-primary)' }}>{display(value)}</div>
          </div>
        ))}
        {situation.filing_url && (
          <div style={{ marginLeft: 'auto', alignSelf: 'center' }}>
            <a href={situation.filing_url} target="_blank" rel="noreferrer" className="btn btn--secondary btn--sm">
              SEC Filing ↗
            </a>
          </div>
        )}
      </div>

      {!workspace && (
        <InfoBanner variant="warning">
          No methodology workspace attached yet. Run the manual backfill CLI after backend deployment.
        </InfoBanner>
      )}

      {workspace && (
        <div style={{ display: 'flex', gap: 20, alignItems: 'flex-start', flexWrap: 'wrap' }}>

          {/* LEFT — main content */}
          <div style={{ flex: '1 1 500px', minWidth: 0, display: 'flex', flexDirection: 'column', gap: 20 }}>

            <SectionCard title="Methodology Checklist">
              <div style={{ display: 'grid', gap: 18 }}>
                {Object.entries(checklistGroups).map(([section, items]) => (
                  <div key={section}>
                    <div className="section-header" style={{ marginBottom: 8 }}>
                      <span className="section-title">{section}</span>
                      <div className="section-line" />
                    </div>
                    <div style={{ display: 'grid', gap: 8 }}>
                      {items.map(item => (
                        <div key={item.check_id} className="card" style={{ padding: '10px 14px' }}>
                          <div style={{ display: 'flex', justifyContent: 'space-between', gap: 12, alignItems: 'flex-start' }}>
                            <div style={{ flex: 1, minWidth: 0 }}>
                              <div style={{ fontWeight: 600, fontSize: 13, color: 'var(--text-primary)', marginBottom: 2 }}>{item.title}</div>
                              <div style={{ fontSize: 12, color: 'var(--text-muted)', lineHeight: 1.5 }}>{item.description}</div>
                            </div>
                            <StatusBadge value={item.status} />
                          </div>
                          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 5, marginTop: 8 }}>
                            {item.required_evidence_types.map(et => (
                              <span key={et} className="status-badge status-badge--readonly">{et}</span>
                            ))}
                            {item.human_review_required && (
                              <span className="status-badge status-badge--preview">Human review</span>
                            )}
                          </div>
                          {item.notes && (
                            <div style={{ marginTop: 6, fontSize: 12, color: 'var(--text-secondary)' }}>{item.notes}</div>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </SectionCard>

            <SectionCard title="Required Resources">
              {requiredResources.length === 0 ? (
                <InfoBanner variant="info">No resources defined for this template.</InfoBanner>
              ) : (
                <div style={{ display: 'grid', gap: 14 }}>
                  {requiredOnly.length > 0 && (
                    <div>
                      <div style={{ ...MONO_LABEL, marginBottom: 8 }}>Required ({requiredOnly.length})</div>
                      <ResourceTable resources={requiredOnly} />
                    </div>
                  )}
                  {optionalOnly.length > 0 && (
                    <div>
                      <div style={{ ...MONO_LABEL, marginBottom: 8 }}>Optional ({optionalOnly.length})</div>
                      <ResourceTable resources={optionalOnly} />
                    </div>
                  )}
                </div>
              )}
            </SectionCard>

            <SectionCard title="Found / Candidate Resources">
              {resourceCandidates.length === 0 ? (
                <InfoBanner variant="info">
                  No resource candidates stored yet. Run Resource Scout via CLI, or add manually below.
                </InfoBanner>
              ) : (
                <div style={{ display: 'grid', gap: 8 }}>
                  {resourceCandidates.map(candidate => (
                    <div
                      key={candidate.resource_candidate_id}
                      className="card"
                      style={{ padding: '10px 14px', display: 'grid', gap: 10 }}
                    >
                      <div style={{ display: 'flex', gap: 12, alignItems: 'flex-start' }}>
                        <div style={{ flex: 1, minWidth: 0 }}>
                          <div style={{ fontWeight: 600, fontSize: 13, color: 'var(--text-primary)', marginBottom: 2 }}>{candidate.title}</div>
                          <div style={{ fontSize: 11, color: 'var(--text-muted)', wordBreak: 'break-all', marginBottom: 6 }}>{candidate.url}</div>
                          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 5 }}>
                            <span className={`status-badge ${resourceStatusClass(candidate.status)}`}>{candidate.status}</span>
                            <span className="status-badge status-badge--readonly">{candidate.source_type}</span>
                            <span className="status-badge status-badge--readonly">{candidate.confidence}</span>
                            <span className="status-badge status-badge--readonly">{candidate.source_domain}</span>
                            {candidate.notes && (
                              <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>{candidate.notes}</span>
                            )}
                          </div>
                        </div>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: 5, flexShrink: 0 }}>
                          <a href={candidate.url} target="_blank" rel="noreferrer" className="btn btn--secondary btn--sm">
                            Open ↗
                          </a>
                          <button
                            className="btn btn--ghost btn--sm"
                            onClick={() => copyText(candidate.url, candidate.resource_candidate_id)}
                          >
                            {copiedKey === candidate.resource_candidate_id ? 'Copied' : 'Copy URL'}
                          </button>
                        </div>
                      </div>

                      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
                        <select
                          value={candidate.related_resource_ids?.[0] ?? ''}
                          disabled={savingCandidateId === candidate.resource_candidate_id}
                          onChange={e => handleCandidatePatch(candidate, {
                            related_resource_ids: e.target.value ? [e.target.value] : [],
                          })}
                          style={{ ...INPUT_STYLE, cursor: 'pointer' }}
                        >
                          <option value="">Link required resource</option>
                          {requiredResources.map(resource => (
                            <option key={resource.resource_id} value={resource.resource_id}>{resource.title}</option>
                          ))}
                        </select>
                        <select
                          value={candidate.related_check_ids?.[0] ?? ''}
                          disabled={savingCandidateId === candidate.resource_candidate_id}
                          onChange={e => handleCandidatePatch(candidate, {
                            related_check_ids: e.target.value ? [e.target.value] : [],
                          })}
                          style={{ ...INPUT_STYLE, cursor: 'pointer' }}
                        >
                          <option value="">Link checklist item</option>
                          {workspace.checklist.map(item => (
                            <option key={item.check_id} value={item.check_id}>{item.title}</option>
                          ))}
                        </select>
                      </div>

                      <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                        <button
                          className="btn btn--secondary btn--sm"
                          disabled={savingCandidateId === candidate.resource_candidate_id || candidate.status === 'evidence_found'}
                          onClick={() => handleCandidatePatch(candidate, { status: 'evidence_found' })}
                        >
                          Mark evidence found
                        </button>
                        <button
                          className="btn btn--ghost btn--sm"
                          disabled={savingCandidateId === candidate.resource_candidate_id || candidate.status === 'rejected'}
                          onClick={() => handleCandidatePatch(candidate, { status: 'rejected' })}
                        >
                          Reject
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </SectionCard>

            <SectionCard title="Add Resource Manually">
              <div style={{ display: 'grid', gap: 10 }}>
                <div>
                  <div style={MONO_LABEL}>Title</div>
                  <input
                    value={resourceForm.title}
                    onChange={e => setResourceForm({ ...resourceForm, title: e.target.value })}
                    placeholder="Optional; generated from domain if blank"
                    style={INPUT_STYLE}
                  />
                </div>
                <div>
                  <div style={MONO_LABEL}>URL</div>
                  <input
                    value={resourceForm.url}
                    onChange={e => setResourceForm({ ...resourceForm, url: e.target.value })}
                    placeholder="https://..."
                    style={INPUT_STYLE}
                  />
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
                  <div>
                    <div style={MONO_LABEL}>Source Type</div>
                    <select
                      value={resourceForm.source_type}
                      onChange={e => setResourceForm({ ...resourceForm, source_type: e.target.value })}
                      style={{ ...INPUT_STYLE, cursor: 'pointer' }}
                    >
                      {SOURCE_TYPES.map(type => (
                        <option key={type} value={type}>{type}</option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <div style={MONO_LABEL}>Notes (optional)</div>
                    <input
                      value={resourceForm.notes}
                      onChange={e => setResourceForm({ ...resourceForm, notes: e.target.value })}
                      placeholder="Brief note"
                      style={INPUT_STYLE}
                    />
                  </div>
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
                  <div>
                    <div style={MONO_LABEL}>Related Required Resource</div>
                    <select
                      value={resourceForm.related_resource_id}
                      onChange={e => setResourceForm({ ...resourceForm, related_resource_id: e.target.value })}
                      style={{ ...INPUT_STYLE, cursor: 'pointer' }}
                    >
                      <option value="">None</option>
                      {requiredResources.map(resource => (
                        <option key={resource.resource_id} value={resource.resource_id}>{resource.title}</option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <div style={MONO_LABEL}>Related Checklist Item</div>
                    <select
                      value={resourceForm.related_check_id}
                      onChange={e => setResourceForm({ ...resourceForm, related_check_id: e.target.value })}
                      style={{ ...INPUT_STYLE, cursor: 'pointer' }}
                    >
                      <option value="">None</option>
                      {workspace.checklist.map(item => (
                        <option key={item.check_id} value={item.check_id}>{item.title}</option>
                      ))}
                    </select>
                  </div>
                </div>
              </div>
              <div style={{ marginTop: 12, display: 'flex', gap: 10, alignItems: 'center', flexWrap: 'wrap' }}>
                <button
                  className="btn btn--secondary btn--sm"
                  onClick={handleAddResource}
                  disabled={savingResource || !resourceForm.url}
                >
                  {savingResource ? 'Adding...' : 'Add candidate'}
                </button>
                {resourceMessage && <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>{resourceMessage}</span>}
                {resourceError && <span style={{ fontSize: 12, color: '#8b2020' }}>{resourceError}</span>}
              </div>
            </SectionCard>

          </div>

          {/* RIGHT — sidebar */}
          <div style={{ flex: '0 0 300px', minWidth: 280, display: 'flex', flexDirection: 'column', gap: 16 }}>

            <SectionCard title="Detection">
              <div style={{ display: 'grid', gap: 10 }}>
                {([
                  ['Detected', situation.detected_at ? new Date(situation.detected_at).toLocaleString() : null],
                  ['CIK', secDetection.cik],
                  ['Accession', secDetection.accession_number],
                  ['Signal', secDetection.detected_form_type ?? situation.filing_type],
                  ['Template', secDetection.selected_playbook ?? situation.selected_playbook],
                ] as [string, unknown][]).map(([label, value]) => (
                  <div key={label}>
                    <div style={MONO_LABEL}>{label}</div>
                    <div style={{ fontSize: 12, color: 'var(--text-primary)', wordBreak: 'break-all' }}>{display(value)}</div>
                  </div>
                ))}
                {workspace.requires_course_review && (
                  <div style={{ marginTop: 2, padding: '5px 8px', background: 'var(--bg-subtle)', borderRadius: 4 }}>
                    <span style={{ fontSize: 11, fontFamily: 'var(--font-mono)', color: 'var(--text-faint)', textTransform: 'uppercase' }}>
                      Requires course review
                    </span>
                  </div>
                )}
              </div>
            </SectionCard>

            <SectionCard title="Workflow">
              <div style={MONO_LABEL}>Move to</div>
              <select
                value={workflowStatus}
                disabled={savingWorkflow}
                onChange={e => handleWorkflowChange(e.target.value)}
                style={{ ...INPUT_STYLE, cursor: 'pointer' }}
              >
                {WORKFLOW_OPTIONS.map(([value, label]) => (
                  <option key={value} value={value}>{label}</option>
                ))}
              </select>
              <div style={{ marginTop: 8, fontSize: 11, color: 'var(--text-muted)' }}>
                Movement is manual and does not evaluate or publish the situation.
              </div>
            </SectionCard>

            <SectionCard title="Progress">
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
                {([
                  ['Total Checks', progress?.total_checks ?? 0],
                  ['Evidence Found', progress?.evidence_found ?? 0],
                  ['Verified', progress?.verified_checks ?? 0],
                  ['Missing Required', progress?.missing_required_resources ?? 0],
                  ['Candidates', progress?.candidate_resources ?? resourceCandidates.filter(item => item.status === 'candidate_found').length],
                  ['Human Review', progress?.human_review_required_count ?? workspace.checklist.filter(item => item.human_review_required).length],
                ] as [string, number][]).map(([label, value]) => (
                  <div key={label} style={{ background: 'var(--bg-subtle)', borderRadius: 6, padding: '8px 10px' }}>
                    <div style={MONO_LABEL}>{label}</div>
                    <div style={{ fontSize: 20, fontWeight: 700, color: 'var(--text-primary)' }}>{value}</div>
                  </div>
                ))}
              </div>
              <div style={{ marginTop: 10, fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-faint)' }}>
                {workspace.template_key} / v{workspace.template_version}
              </div>
            </SectionCard>

            <SectionCard title="Next Actions">
              <div style={{ display: 'grid', gap: 6 }}>
                <div style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 4 }}>
                  Automation is not running. All actions are manual / CLI-only.
                </div>
                <button className="btn btn--secondary btn--sm" disabled>Resource Scout — run via CLI</button>
                {researchCaseId ? (
                  <Link href={`/investment/research/${researchCaseId}`} className="btn btn--secondary btn--sm">
                    Open ResearchCase
                  </Link>
                ) : (
                  <button
                    className="btn btn--secondary btn--sm"
                    disabled={promoting || !workspace}
                    onClick={handlePromote}
                  >
                    {promoting ? 'Promoting...' : 'Promote to ResearchCase'}
                  </button>
                )}
                {promotionMessage && (
                  <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>{promotionMessage}</div>
                )}
              </div>
            </SectionCard>

            <SectionCard title="Search Suggestions">
              {searchSuggestions.length === 0 ? (
                <InfoBanner variant="info">
                  Run Resource Scout v1 via CLI to generate search queries.
                </InfoBanner>
              ) : (
                <>
                  <button
                    className="btn btn--ghost btn--sm"
                    onClick={() => setSuggestionsOpen(!suggestionsOpen)}
                    style={{ marginBottom: 8, width: '100%', textAlign: 'left' }}
                  >
                    {suggestionsOpen ? '▲ Hide' : '▶ Show'} {searchSuggestions.length} quer{searchSuggestions.length === 1 ? 'y' : 'ies'}
                  </button>
                  {suggestionsOpen && (
                    <div style={{ display: 'grid', gap: 6 }}>
                      {searchSuggestions.map(suggestion => (
                        <div
                          key={suggestion.suggestion_id}
                          className="card"
                          style={{ padding: '8px 10px', display: 'flex', alignItems: 'flex-start', gap: 8 }}
                        >
                          <div style={{ flex: 1, minWidth: 0 }}>
                            <div style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-faint)', textTransform: 'uppercase', marginBottom: 2 }}>
                              {suggestion.suggestion_type}
                            </div>
                            <div style={{ fontSize: 12, color: 'var(--text-primary)', wordBreak: 'break-word' }}>{suggestion.query}</div>
                          </div>
                          <button
                            className="btn btn--ghost btn--sm"
                            onClick={() => copyText(suggestion.query, suggestion.suggestion_id)}
                            style={{ flexShrink: 0 }}
                          >
                            {copiedKey === suggestion.suggestion_id ? '✓' : 'Copy'}
                          </button>
                          <a
                            className="btn btn--secondary btn--sm"
                            href={`https://www.google.com/search?q=${encodeURIComponent(suggestion.query)}`}
                            target="_blank"
                            rel="noreferrer"
                            style={{ flexShrink: 0 }}
                          >
                            Search ↗
                          </a>
                        </div>
                      ))}
                    </div>
                  )}
                </>
              )}
            </SectionCard>

          </div>
        </div>
      )}
    </div>
  );
}
