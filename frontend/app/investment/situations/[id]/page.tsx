'use client';

import type { CSSProperties } from 'react';
import { useEffect, useMemo, useRef, useState } from 'react';
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
import { EvidenceLinksPanel } from '@/app/components/EvidenceLinksPanel';
import { CaseActivityTimeline } from '@/app/components/CaseActivityTimeline';
import { OfficialSourceFinderPanel } from '@/app/components/OfficialSourceFinderPanel';
import { HistoricalAnaloguesPanel } from '@/app/components/HistoricalAnaloguesPanel';
import { CaseCompletionWorkbench } from '@/app/components/CaseCompletionWorkbench';
import { SecDocumentAcquisitionPanel } from '@/app/components/SecDocumentAcquisitionPanel';
import { DocumentPackagePanel } from '@/app/components/DocumentPackagePanel';
import { DocumentationAgentPanel } from '@/app/components/DocumentationAgentPanel';
import { DocumentationTasksPanel } from '@/app/components/DocumentationTasksPanel';
import { SECTransparencyPanel } from '@/app/components/SECTransparencyPanel';
import { EducationStudyGuidePanel } from '@/app/components/EducationStudyGuidePanel';
import {
  addSituationResource,
  acquireSituationSecDocuments,
  fetchSituationActivityTimeline,
  fetchSituationDocumentationGuide,
  fetchSituationDocumentPackage,
  fetchSituationDocumentationAgentReport,
  fetchSituationDocumentationExtractions,
  fetchSituationEvidenceLinks,
  fetchSituationCompletionWorkbench,
  fetchSituationHistoricalAnalogues,
  fetchSituationOfficialSourceFinder,
  fetchSituationPromotionReadiness,
  fetchSituationSecDocumentAcquisitionPreview,
  fetchSituation,
  promoteSituationToResearchCase,
  readSituationDocumentationSourceDraft,
  reviewDocumentationExtractionField,
  updateSituationResourceCandidate,
  updateSituationWorkflowStatus,
  type MethodologyChecklistItem,
  type MethodologyWorkspace,
  type PromotionReadinessPackage,
  type RequiredResourceItem,
  type ResourceCandidate,
  type Situation,
  type CaseDocumentationGuidePackage,
  type CaseActivityTimelinePackage,
  type CaseCompletionPackage,
  type DocumentPackage,
  type DocumentationAgentDocument,
  type DocumentationAgentReport,
  type DocumentationExtractionField,
  type HistoricalAnaloguesPackage,
  type OfficialSourceFinderPackage,
  type SecDocumentAcquisitionPackage,
  type SituationEvidenceLinksPackage,
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
  ['ready_for_research_case', 'ResearchCase package'],
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

function classificationStrengthLabel(value: unknown): string {
  const normalized = String(value ?? '').toLowerCase();
  if (normalized === 'high') return 'Strong';
  if (normalized === 'medium') return 'Moderate';
  if (normalized === 'low') return 'Weak';
  return 'Needs review';
}

function resourceStatusClass(status: string): string {
  if (status === 'missing') return 'status-badge--preview';
  if (status === 'candidate_found') return 'status-badge--partial';
  if (status === 'evidence_found') return 'status-badge--manual';
  if (status === 'verified') return 'status-badge--active';
  if (status === 'rejected') return 'status-badge--danger';
  return 'status-badge--readonly';
}

function resourceStatusLabel(status: string): string {
  if (status === 'candidate_found') return 'Candidate mapped';
  if (status === 'evidence_found') return 'Mapped for review';
  if (status === 'verified') return 'Manually verified';
  return status.replaceAll('_', ' ');
}

function candidateUrl(candidate: ResourceCandidate): string {
  return candidate.url ?? '';
}

function candidateFilename(candidate: ResourceCandidate): string {
  const title = candidate.original_filename || candidate.title;
  const url = candidateUrl(candidate);
  if (title && title.trim()) return title.trim();
  if (!url) return 'SEC file';
  try {
    const pathname = new URL(url).pathname;
    return decodeURIComponent(pathname.split('/').filter(Boolean).pop() ?? 'SEC file');
  } catch {
    return url.split('/').filter(Boolean).pop() ?? 'SEC file';
  }
}

function secDirectoryFromCandidate(candidate: ResourceCandidate): string | null {
  const url = candidateUrl(candidate);
  if (!url) return null;
  const index = url.lastIndexOf('/');
  return index > 'https://'.length ? url.slice(0, index + 1) : url;
}

function isSecPackageCandidate(candidate: ResourceCandidate): boolean {
  const url = candidateUrl(candidate).toLowerCase();
  const sourceType = candidate.source_type.toLowerCase();
  const domain = String(candidate.source_domain ?? '').toLowerCase();
  return sourceType === 'sec_filing' || domain.includes('sec.gov') || url.includes('sec.gov/archives/');
}

function secFileKind(candidate: ResourceCandidate): string {
  const text = `${candidateFilename(candidate)} ${candidate.title} ${candidate.notes ?? ''}`.toLowerCase();
  if (text.includes('offer') && text.includes('purchase')) return 'Likely Offer to Purchase';
  if (text.includes('transmittal')) return 'Likely Letter of Transmittal';
  if (text.includes('exhibit') || /\bex[-_]?/i.test(text)) return 'Likely exhibit';
  if (text.includes('filingsummary.xml') || text.includes('filing summary')) return 'Filing summary';
  if (text.endsWith('.txt') || text.includes('complete submission')) return 'Complete submission text';
  if (text.includes('index')) return 'SEC index file';
  return 'Candidate SEC file';
}

function secFileRank(candidate: ResourceCandidate): number {
  const kind = secFileKind(candidate);
  if (kind === 'Likely Offer to Purchase') return 0;
  if (kind === 'Likely Letter of Transmittal') return 1;
  if (kind === 'Likely exhibit') return 2;
  if (kind === 'Filing summary') return 3;
  if (kind === 'Complete submission text') return 4;
  if (kind === 'SEC index file') return 8;
  return 6;
}

function caseStatusLabel(status: string, hasResearchCase: boolean): string {
  if (status === 'promoted') return hasResearchCase ? 'Linked to ResearchCase' : 'ResearchCase created';
  if (status === 'documented') return 'Metadata mapped';
  return status.replaceAll('_', ' ');
}

function checklistStatusLabel(status: string): string {
  if (status === 'evidence_found') return 'Mapped for review';
  if (status === 'verified') return 'Manually verified';
  if (status === 'completed') return 'Completed manually';
  return status.replaceAll('_', ' ');
}

function guideQualityLabel(value: string): string {
  if (value === 'good') return 'Structure mapped';
  if (value === 'excellent') return 'Structure check: complete';
  if (value === 'ready') return 'Structure check: complete';
  if (value === 'mostly_ready') return 'Package mapped';
  return value.replaceAll('_', ' ');
}

function promotionReadinessLabel(value: string): string {
  if (value === 'ready_for_manual_promotion') return 'Manual promotion package available';
  if (value === 'ready_for_research_case') return 'ResearchCase package available';
  if (value === 'ready') return 'Manual promotion package available';
  return value.replaceAll('_', ' ');
}

function structureCheckLabel(score: number | null | undefined): string {
  if (score === null || score === undefined) return 'Structure check: not loaded';
  if (score >= 100) return 'Structure check: complete';
  return `Structure check: ${score}/100 structure only`;
}

function groupChecklist(items: MethodologyChecklistItem[]) {
  return items.reduce<Record<string, MethodologyChecklistItem[]>>((groups, item) => {
    const key = item.section || 'General';
    groups[key] = groups[key] ?? [];
    groups[key].push(item);
    return groups;
  }, {});
}

function SituationQuickLinks({
  situation,
  researchCaseId,
}: {
  situation: Situation;
  researchCaseId?: string;
}) {
  const archiveUrl = situation.filing_url
    ? situation.filing_url.slice(0, situation.filing_url.lastIndexOf('/') + 1)
    : null;
  const links = [
    { label: 'Back to Kanban', href: '/investment/situations', external: false },
    { label: 'Evaluation detail', href: `/investment/evaluations/${situation.id}`, external: false },
    ...(researchCaseId ? [{ label: 'ResearchCase', href: `/investment/research/${researchCaseId}`, external: false }] : []),
    ...(situation.filing_url ? [{ label: 'SEC filing', href: situation.filing_url, external: true }] : []),
    ...(archiveUrl ? [{ label: 'SEC archive directory', href: archiveUrl, external: true }] : []),
  ];

  return (
    <SectionCard title="Operational Links">
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))', gap: 8 }}>
        {links.map((link, index) => (
          link.external ? (
            <a key={`${link.href}-${index}`} href={link.href} target="_blank" rel="noreferrer" className="btn btn--secondary btn--sm">
              {link.label}
            </a>
          ) : (
            <Link key={`${link.href}-${index}`} href={link.href} className="btn btn--secondary btn--sm">
              {link.label}
            </Link>
          )
        ))}
      </div>
      <div style={{ marginTop: 8, fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-faint)' }}>
        Links open manually. The UI does not fetch SEC document bodies or crawl linked pages.
      </div>
    </SectionCard>
  );
}

function SituationActivityLog({
  situation,
  workspace,
}: {
  situation: Situation;
  workspace: MethodologyWorkspace | null;
}) {
  const rows = [
    { label: 'Detection created', at: situation.detected_at, detail: situation.filing_type ?? 'official-source signal' },
    { label: 'Situation updated', at: situation.updated_at, detail: situation.status },
    ...((workspace?.resource_candidates ?? []).slice(0, 4).map(candidate => ({
      label: `Resource ${candidate.status}`,
      at: candidate.discovered_at,
      detail: candidate.title,
    }))),
    ...((workspace?.search_suggestions ?? []).slice(0, 3).map(suggestion => ({
      label: 'Search suggestion',
      at: suggestion.created_at,
      detail: suggestion.query,
    }))),
  ]
    .filter(row => row.at)
    .sort((a, b) => String(b.at).localeCompare(String(a.at)))
    .slice(0, 8);

  return (
    <SectionCard title="Case Activity Log">
      {rows.length === 0 ? (
        <InfoBanner variant="info">No stored activity rows are available for this situation yet.</InfoBanner>
      ) : (
        <div style={{ display: 'grid', gap: 8 }}>
          {rows.map((row, index) => (
            <div key={`${row.label}-${row.at}-${index}`} style={{ display: 'flex', gap: 10, alignItems: 'flex-start', padding: '8px 10px', border: '1px solid var(--border-default)', borderRadius: 6 }}>
              <span className="status-dot status-dot--active" style={{ marginTop: 5 }} />
              <div style={{ minWidth: 0 }}>
                <div style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--text-primary)' }}>{row.label}</div>
                <div style={{ fontSize: 12, color: 'var(--text-muted)', wordBreak: 'break-word' }}>
                  {new Date(String(row.at)).toLocaleString('en-CH')} / {row.detail}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </SectionCard>
  );
}

function itemTitle(item: Record<string, unknown>): string {
  const value = item.title ?? item.label ?? item.resource_id ?? item.check_id ?? item.query;
  return typeof value === 'string' && value.trim() ? value : 'Untitled item';
}

function guideTargetFor(label: string): string {
  const normalized = label.toLowerCase();
  if (normalized.includes('sec') || normalized.includes('filing') || normalized.includes('origin')) return 'guide-find-case';
  if (normalized.includes('required resource')) return 'guide-required-resources';
  if (normalized.includes('candidate') || normalized.includes('evidence link') || normalized.includes('evidence present')) return 'guide-evidence-links';
  if (normalized.includes('checklist') || normalized.includes('human review')) return 'guide-checklist';
  if (normalized.includes('search')) return 'guide-search-suggestions';
  if (normalized.includes('researchcase')) return 'guide-researchcase';
  return '';
}

function GuideStatusChip({ label, status }: { label: string; status: string }) {
  const target = guideTargetFor(label);
  if (!target) return <StatusBadge value={status} />;
  return (
    <a href={`#${target}`} style={{ textDecoration: 'none', display: 'inline-flex' }} aria-label={`Jump to ${label} section`}>
      <StatusBadge value={status} />
    </a>
  );
}

function CaseDocumentationGuidePanel({
  guide,
  error,
  onCopy,
  copiedKey,
}: {
  guide: CaseDocumentationGuidePackage | null;
  error: string | null;
  onCopy: (text: string, key: string) => void;
  copiedKey: string | null;
}) {
  if (error) {
    return (
      <SectionCard title="Case Documentation Guide">
        <InfoBanner variant="warning">{error}</InfoBanner>
      </SectionCard>
    );
  }
  if (!guide) return null;

  const missingTotal =
    guide.missing_evidence.missing_required_resources.length +
    guide.missing_evidence.missing_checklist_items.length;

  return (
    <SectionCard title="Case Documentation Guide">
      <div style={{ display: 'grid', gap: 16 }}>
        <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', alignItems: 'center' }}>
          <div style={{ background: 'var(--bg-subtle)', border: '1px solid var(--border-default)', borderRadius: 8, padding: '10px 14px' }}>
            <div style={MONO_LABEL}>Workspace structure</div>
            <div style={{ fontSize: 22, fontWeight: 700 }}>{guide.documentation_quality.score}/100</div>
            <span className="status-badge status-badge--readonly">{guideQualityLabel(guide.documentation_quality.level)}</span>
          </div>
          <div style={{ flex: '1 1 260px', minWidth: 0 }}>
            <div style={{ fontSize: 13, color: 'var(--text-primary)', marginBottom: 4 }}>{guide.documentation_quality.summary}</div>
            <div style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--text-muted)' }}>
              Structure score only · evidence review still required. Derived from current case state · Manual research plan · No document body has been fetched
            </div>
          </div>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: 8 }}>
          {guide.documentation_quality.checks.map(check => (
            <div key={check.label} style={{ border: '1px solid var(--border-default)', borderRadius: 6, padding: '8px 10px' }}>
              <div style={{ fontSize: 12, color: 'var(--text-primary)' }}>{check.label}</div>
              <GuideStatusChip label={check.label} status={check.status} />
            </div>
          ))}
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: 14 }}>
          <div id="guide-find-case" style={{ scrollMarginTop: 80 }}>
            <div style={MONO_LABEL}>How to find this case</div>
            <div style={{ fontSize: 12, color: 'var(--text-muted)', display: 'grid', gap: 4 }}>
              <span>Source: {display(guide.detection_guide.source)}</span>
              <span>CIK: {display(guide.detection_guide.cik)}</span>
              <span>Accession: {display(guide.detection_guide.accession_number)}</span>
              <span>Filing: {display(guide.detection_guide.filing_type)} / {display(guide.detection_guide.filing_date)}</span>
              {guide.detection_guide.filing_url && (
                <a href={guide.detection_guide.filing_url} target="_blank" rel="noreferrer" className="btn btn--secondary btn--sm" style={{ justifySelf: 'start', marginTop: 4 }}>
                  Open SEC filing
                </a>
              )}
            </div>
          </div>
          <div id="guide-checklist" style={{ scrollMarginTop: 80 }}>
            <div style={MONO_LABEL}>Manual verification steps</div>
            <ol style={{ margin: 0, paddingLeft: 18, display: 'grid', gap: 4 }}>
              {guide.detection_guide.manual_verification_steps.map(step => (
                <li key={step} style={{ fontSize: 12, color: 'var(--text-muted)' }}>{step}</li>
              ))}
            </ol>
          </div>
          <div id="guide-researchcase" style={{ scrollMarginTop: 80 }}>
            <div style={MONO_LABEL}>Missing Evidence Hunter</div>
            <div style={{ fontSize: 12, color: 'var(--text-muted)', lineHeight: 1.5 }}>
              <strong style={{ color: 'var(--text-primary)' }}>{guide.research_agent.agent_name}</strong><br />
              {guide.research_agent.current_mission}
              <div style={{ marginTop: 6 }}>Current mode: manual / observer-only</div>
              <div>{guide.research_agent.future_scheduler_note}</div>
            </div>
          </div>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 14 }}>
          <div id="guide-required-resources" style={{ scrollMarginTop: 80 }}>
            <div style={MONO_LABEL}>Missing required resources ({guide.missing_evidence.missing_required_resources.length})</div>
            {guide.missing_evidence.missing_required_resources.length === 0 ? (
              <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>No missing required resources in the derived guide.</div>
            ) : (
              <ul style={{ margin: 0, paddingLeft: 18 }}>
                {guide.missing_evidence.missing_required_resources.slice(0, 6).map((item, index) => (
                  <li key={`${itemTitle(item)}-${index}`} style={{ fontSize: 12, color: 'var(--text-muted)' }}>{itemTitle(item)}</li>
                ))}
              </ul>
            )}
          </div>
          <div>
            <div style={MONO_LABEL}>Missing checklist evidence ({guide.missing_evidence.missing_checklist_items.length})</div>
            {guide.missing_evidence.missing_checklist_items.length === 0 ? (
              <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>No checklist gaps in the derived guide.</div>
            ) : (
              <ul style={{ margin: 0, paddingLeft: 18 }}>
                {guide.missing_evidence.missing_checklist_items.slice(0, 6).map((item, index) => (
                  <li key={`${itemTitle(item)}-${index}`} style={{ fontSize: 12, color: 'var(--text-muted)' }}>{itemTitle(item)}</li>
                ))}
              </ul>
            )}
          </div>
          <div>
            <div style={MONO_LABEL}>Current manual research plan</div>
            <ul style={{ margin: 0, paddingLeft: 18 }}>
              {guide.research_agent.next_manual_actions.slice(0, 5).map(action => (
                <li key={action} style={{ fontSize: 12, color: 'var(--text-muted)' }}>{action}</li>
              ))}
            </ul>
          </div>
        </div>

        <div id="guide-evidence-links" style={{ scrollMarginTop: 80 }}>
          <div style={MONO_LABEL}>Evidence links / resource candidates</div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
            <span className="status-badge status-badge--readonly">Candidate-only: {guide.missing_evidence.candidate_only_resources.length}</span>
            <span className="status-badge status-badge--partial">Mapped for review, not verified: {guide.missing_evidence.evidence_found_not_verified.length}</span>
            <span className="status-badge status-badge--readonly">Rejected: {guide.missing_evidence.rejected_resources.length}</span>
          </div>
        </div>

        <div id="guide-search-suggestions" style={{ scrollMarginTop: 80 }}>
          <div style={MONO_LABEL}>Manual search suggestions</div>
          <div style={{ fontSize: 11, color: 'var(--text-muted)', lineHeight: 1.5, marginBottom: 8 }}>
            Stored prompts for a human researcher. They are not fetched automatically, not evidence, and not verified.
            Paste this into Google, SEC search, or company IR. SwissEdge has not run this search automatically.
            {copiedKey === 'copy-failed' && (
              <span style={{ display: 'block', marginTop: 4, color: '#b45309' }}>Copy failed - select the query text manually.</span>
            )}
          </div>
          {guide.search_plan.copyable_queries.length === 0 ? (
            <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>No stored search suggestions yet.</div>
          ) : (
            <div style={{ display: 'grid', gap: 8 }}>
              {guide.search_plan.copyable_queries.map((query, index) => (
                <div key={`${query}-${index}`} style={{ border: '1px solid var(--border-default)', borderRadius: 6, padding: '8px 10px', display: 'grid', gap: 6 }}>
                  <div style={{ fontSize: 12, color: 'var(--text-primary)', wordBreak: 'break-word' }}>{query}</div>
                  <button className="btn btn--ghost btn--sm" onClick={() => onCopy(query, `guide-query-${index}`)} style={{ justifySelf: 'start' }}>
                    {copiedKey === `guide-query-${index}` ? 'Copied' : 'Copy query'}
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>

        <div>
          <div style={MONO_LABEL}>Derived activity timeline</div>
          <div style={{ display: 'grid', gap: 6 }}>
            {guide.activity_timeline.slice(0, 8).map((event, index) => (
              <div key={`${event.label}-${index}`} style={{ display: 'flex', gap: 8, fontSize: 12, color: 'var(--text-muted)' }}>
                <span className="status-dot status-dot--active" style={{ marginTop: 5 }} />
                <span>{event.timestamp ? new Date(event.timestamp).toLocaleString('en-CH') : 'Current state — timestamp unavailable'} / {event.label}{event.detail ? ` / ${event.detail}` : ''}</span>
              </div>
            ))}
          </div>
        </div>

        <div style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-faint)' }}>
          Missing items: {missingTotal} · Frequent checks planned for future approved sprint · Scheduler disabled in this sprint
        </div>
      </div>
    </SectionCard>
  );
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
                <span className={`status-badge ${resourceStatusClass(r.status)}`}>{resourceStatusLabel(r.status)}</span>
              </td>
              <td style={{ fontSize: 12, color: 'var(--text-muted)' }}>{r.expected_source}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function CandidateCard({
  candidate,
  requiredResources,
  checklist,
  savingCandidateId,
  copiedKey,
  onCopy,
  onPatch,
}: {
  candidate: ResourceCandidate;
  requiredResources: RequiredResourceItem[];
  checklist: MethodologyChecklistItem[];
  savingCandidateId: string | null;
  copiedKey: string | null;
  onCopy: (text: string, key: string) => void;
  onPatch: (candidate: ResourceCandidate, payload: { status?: string; notes?: string; related_resource_ids?: string[]; related_check_ids?: string[] }) => void;
}) {
  return (
    <div
      className="card"
      style={{ padding: '10px 14px', display: 'grid', gap: 10 }}
    >
      <div style={{ display: 'flex', gap: 12, alignItems: 'flex-start' }}>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ fontWeight: 600, fontSize: 13, color: 'var(--text-primary)', marginBottom: 2 }}>{candidate.title}</div>
          <div style={{ fontSize: 11, color: 'var(--text-muted)', wordBreak: 'break-all', marginBottom: 6 }}>{candidate.url}</div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 5 }}>
            <span className={`status-badge ${resourceStatusClass(candidate.status)}`}>{resourceStatusLabel(candidate.status)}</span>
            <span className="status-badge status-badge--readonly">{isSecPackageCandidate(candidate) ? 'Candidate SEC file' : candidate.source_type}</span>
            <span className="status-badge status-badge--manual">Needs review</span>
            <span className="status-badge status-badge--readonly">Not verified</span>
            {candidate.source_domain && <span className="status-badge status-badge--readonly">{candidate.source_domain}</span>}
            {candidate.notes && (
              <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>{candidate.notes}</span>
            )}
          </div>
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 5, flexShrink: 0 }}>
          <a href={candidate.url ?? '#'} target="_blank" rel="noreferrer" className="btn btn--secondary btn--sm">
            Open
          </a>
          <button
            className="btn btn--ghost btn--sm"
            onClick={() => onCopy(candidate.url ?? '', candidate.resource_candidate_id)}
          >
            {copiedKey === candidate.resource_candidate_id ? 'Copied' : 'Copy URL'}
          </button>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
        <select
          value={candidate.related_resource_ids?.[0] ?? ''}
          disabled={savingCandidateId === candidate.resource_candidate_id}
          onChange={e => onPatch(candidate, {
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
          onChange={e => onPatch(candidate, {
            related_check_ids: e.target.value ? [e.target.value] : [],
          })}
          style={{ ...INPUT_STYLE, cursor: 'pointer' }}
        >
          <option value="">Link checklist item</option>
          {checklist.map(item => (
            <option key={item.check_id} value={item.check_id}>{item.title}</option>
          ))}
        </select>
      </div>

      <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
        <button
          className="btn btn--secondary btn--sm"
          disabled={savingCandidateId === candidate.resource_candidate_id || candidate.status === 'candidate_found' || candidate.status === 'evidence_found'}
          onClick={() => onPatch(candidate, { status: 'candidate_found' })}
        >
          Map candidate to required document
        </button>
        <button
          className="btn btn--ghost btn--sm"
          disabled={savingCandidateId === candidate.resource_candidate_id || candidate.status === 'rejected'}
          onClick={() => onPatch(candidate, { status: 'rejected' })}
        >
          Reject
        </button>
      </div>
    </div>
  );
}

function PromotionReadinessPanel({
  readiness,
  loading,
  error,
}: {
  readiness: PromotionReadinessPackage | null;
  loading: boolean;
  error: string | null;
}) {
  const topEvidence = readiness?.supporting_evidence.slice(0, 3) ?? [];
  return (
    <SectionCard title="Manual Promotion Package">
      <div style={{ display: 'grid', gap: 10 }}>
        <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', alignItems: 'center' }}>
          <span className="status-badge status-badge--readonly">
            {readiness ? promotionReadinessLabel(readiness.readiness_level) : 'not loaded'}
          </span>
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: 12, color: 'var(--text-muted)' }}>
            {structureCheckLabel(readiness?.readiness_score)}
          </span>
        </div>
        <div style={{ fontSize: 11, color: 'var(--text-muted)', lineHeight: 1.5 }}>
          Manual package only. This panel does not create a ResearchCase or approve an investment.
        </div>
        {loading && <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>Loading promotion readiness...</div>}
        {error && <InfoBanner variant="warning">{error}</InfoBanner>}
        {readiness && !loading && (
          <>
            {readiness.blocking_reasons.length > 0 && (
              <div>
                <div style={MONO_LABEL}>Blocking reasons</div>
                <ul style={{ margin: 0, paddingLeft: 18 }}>
                  {readiness.blocking_reasons.slice(0, 4).map(reason => (
                    <li key={reason} style={{ fontSize: 12, color: 'var(--text-muted)' }}>{reason}</li>
                  ))}
                </ul>
              </div>
            )}
            {readiness.missing_required_documents.length > 0 && (
              <div>
                <div style={MONO_LABEL}>Missing required documents</div>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 5 }}>
                  {readiness.missing_required_documents.slice(0, 5).map(label => (
                    <span key={label} className="status-badge status-badge--preview">{label}</span>
                  ))}
                </div>
              </div>
            )}
            {topEvidence.length > 0 && (
              <div>
                <div style={MONO_LABEL}>Top mapped metadata links</div>
                <div style={{ display: 'grid', gap: 4 }}>
                  {topEvidence.map((item, index) => (
                    <div key={`${String(item.label ?? 'evidence')}-${index}`} style={{ fontSize: 12, color: 'var(--text-muted)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {String(item.label ?? item.source_type ?? 'Evidence link')}
                    </div>
                  ))}
                </div>
              </div>
            )}
            <div>
              <div style={MONO_LABEL}>Recommended next manual action</div>
              <div style={{ fontSize: 12, color: 'var(--text-primary)' }}>{readiness.recommended_next_step}</div>
            </div>
          </>
        )}
      </div>
    </SectionCard>
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
    task_document_key: '',
    task_checklist_id: '',
    task_source_hint: '',
  });
  const [resourceMessage, setResourceMessage] = useState<string | null>(null);
  const [resourceError, setResourceError] = useState<string | null>(null);
  const [savingResource, setSavingResource] = useState(false);
  const [savingWorkflow, setSavingWorkflow] = useState(false);
  const [promoting, setPromoting] = useState(false);
  const [promotionMessage, setPromotionMessage] = useState<string | null>(null);
  const [savingCandidateId, setSavingCandidateId] = useState<string | null>(null);
  const [evidenceLinks, setEvidenceLinks] = useState<SituationEvidenceLinksPackage | null>(null);
  const [evidenceLinksError, setEvidenceLinksError] = useState<string | null>(null);
  const [documentationGuide, setDocumentationGuide] = useState<CaseDocumentationGuidePackage | null>(null);
  const [documentationGuideError, setDocumentationGuideError] = useState<string | null>(null);
  const [completionWorkbench, setCompletionWorkbench] = useState<CaseCompletionPackage | null>(null);
  const [completionWorkbenchError, setCompletionWorkbenchError] = useState<string | null>(null);
  const [completionWorkbenchLoading, setCompletionWorkbenchLoading] = useState(false);
  const [officialSourceFinder, setOfficialSourceFinder] = useState<OfficialSourceFinderPackage | null>(null);
  const [officialSourceFinderError, setOfficialSourceFinderError] = useState<string | null>(null);
  const [officialSourceFinderLoading, setOfficialSourceFinderLoading] = useState(false);
  const [secDocumentAcquisition, setSecDocumentAcquisition] = useState<SecDocumentAcquisitionPackage | null>(null);
  const [secDocumentAcquisitionError, setSecDocumentAcquisitionError] = useState<string | null>(null);
  const [secDocumentAcquisitionLoading, setSecDocumentAcquisitionLoading] = useState(false);
  const [secDocumentAcquiring, setSecDocumentAcquiring] = useState(false);
  const [documentPackage, setDocumentPackage] = useState<DocumentPackage | null>(null);
  const [documentPackageError, setDocumentPackageError] = useState<string | null>(null);
  const [documentPackageLoading, setDocumentPackageLoading] = useState(false);
  const [documentationAgentReport, setDocumentationAgentReport] = useState<DocumentationAgentReport | null>(null);
  const [documentationAgentReportError, setDocumentationAgentReportError] = useState<string | null>(null);
  const [documentationAgentReportLoading, setDocumentationAgentReportLoading] = useState(false);
  const [documentationExtractions, setDocumentationExtractions] = useState<DocumentationExtractionField[]>([]);
  const [documentationExtractionsError, setDocumentationExtractionsError] = useState<string | null>(null);
  const [readingDraftKey, setReadingDraftKey] = useState<string | null>(null);
  const [reviewingExtractionId, setReviewingExtractionId] = useState<string | null>(null);
  const [editingExtractionId, setEditingExtractionId] = useState<string | null>(null);
  const [editingExtractionValue, setEditingExtractionValue] = useState('');
  const [promotionReadiness, setPromotionReadiness] = useState<PromotionReadinessPackage | null>(null);
  const [promotionReadinessError, setPromotionReadinessError] = useState<string | null>(null);
  const [promotionReadinessLoading, setPromotionReadinessLoading] = useState(false);
  const [historicalAnalogues, setHistoricalAnalogues] = useState<HistoricalAnaloguesPackage | null>(null);
  const [historicalAnaloguesError, setHistoricalAnaloguesError] = useState<string | null>(null);
  const [historicalAnaloguesLoading, setHistoricalAnaloguesLoading] = useState(false);
  const [activityTimeline, setActivityTimeline] = useState<CaseActivityTimelinePackage | null>(null);
  const [activityTimelineError, setActivityTimelineError] = useState<string | null>(null);
  const [activityTimelineLoading, setActivityTimelineLoading] = useState(false);
  const [suggestionsOpen, setSuggestionsOpen] = useState(false);
  const [advancedToolsOpen, setAdvancedToolsOpen] = useState(false);
  const [copiedKey, setCopiedKey] = useState<string | null>(null);
  const manualResourceUrlRef = useRef<HTMLInputElement | null>(null);

  async function load() {
    try {
      setLoading(true);
      setError(null);
      const situationData = await fetchSituation(id);
      setSituation(situationData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load situation');
    } finally {
      setLoading(false);
    }
  }

  async function refreshDocumentationIntakeData() {
    try {
      setEvidenceLinksError(null);
      setDocumentPackageLoading(true);
      setDocumentPackageError(null);
      setDocumentationAgentReportLoading(true);
      setDocumentationAgentReportError(null);
      setDocumentationExtractionsError(null);

      const [linksResult, packageResult, reportResult, extractionsResult] = await Promise.allSettled([
        fetchSituationEvidenceLinks(id),
        fetchSituationDocumentPackage(id),
        fetchSituationDocumentationAgentReport(id),
        fetchSituationDocumentationExtractions(id),
      ]);

      if (linksResult.status === 'fulfilled') {
        setEvidenceLinks(linksResult.value);
      } else {
        setEvidenceLinksError(linksResult.reason instanceof Error ? linksResult.reason.message : 'Failed to load evidence links');
      }
      if (packageResult.status === 'fulfilled') {
        setDocumentPackage(packageResult.value);
      } else {
        setDocumentPackageError(packageResult.reason instanceof Error ? packageResult.reason.message : 'Failed to load document package');
      }
      if (reportResult.status === 'fulfilled') {
        setDocumentationAgentReport(reportResult.value);
      } else {
        setDocumentationAgentReportError(reportResult.reason instanceof Error ? reportResult.reason.message : 'Failed to load documentation agent report');
      }
      if (extractionsResult.status === 'fulfilled') {
        setDocumentationExtractions(extractionsResult.value);
      } else {
        setDocumentationExtractionsError(extractionsResult.reason instanceof Error ? extractionsResult.reason.message : 'Failed to load draft extracted fields');
      }
    } finally {
      setDocumentPackageLoading(false);
      setDocumentationAgentReportLoading(false);
    }
  }

  useEffect(() => {
    async function loadEvidenceLinks() {
      try {
        setEvidenceLinksError(null);
        const linksData = await fetchSituationEvidenceLinks(id);
        setEvidenceLinks(linksData);
      } catch (err) {
        setEvidenceLinksError(err instanceof Error ? err.message : 'Failed to load evidence links');
      }
    }
    async function loadDocumentationGuide() {
      try {
        setDocumentationGuideError(null);
        const guideData = await fetchSituationDocumentationGuide(id);
        setDocumentationGuide(guideData);
      } catch (err) {
        setDocumentationGuideError(err instanceof Error ? err.message : 'Failed to load documentation guide');
      }
    }
    async function loadCompletionWorkbench() {
      try {
        setCompletionWorkbenchLoading(true);
        setCompletionWorkbenchError(null);
        const completionData = await fetchSituationCompletionWorkbench(id);
        setCompletionWorkbench(completionData);
      } catch (err) {
        setCompletionWorkbenchError(err instanceof Error ? err.message : 'Failed to load completion workbench');
      } finally {
        setCompletionWorkbenchLoading(false);
      }
    }
    async function loadOfficialSourceFinder() {
      try {
        setOfficialSourceFinderLoading(true);
        setOfficialSourceFinderError(null);
        const finderData = await fetchSituationOfficialSourceFinder(id);
        setOfficialSourceFinder(finderData);
      } catch (err) {
        setOfficialSourceFinderError(err instanceof Error ? err.message : 'Failed to load official source finder');
      } finally {
        setOfficialSourceFinderLoading(false);
      }
    }
    async function loadSecDocumentAcquisition() {
      try {
        setSecDocumentAcquisitionLoading(true);
        setSecDocumentAcquisitionError(null);
        const preview = await fetchSituationSecDocumentAcquisitionPreview(id);
        setSecDocumentAcquisition(preview);
      } catch (err) {
        setSecDocumentAcquisitionError(err instanceof Error ? err.message : 'Failed to load SEC document acquisition preview');
      } finally {
        setSecDocumentAcquisitionLoading(false);
      }
    }
    async function loadDocumentPackage() {
      try {
        setDocumentPackageLoading(true);
        setDocumentPackageError(null);
        const data = await fetchSituationDocumentPackage(id);
        setDocumentPackage(data);
      } catch (err) {
        setDocumentPackageError(err instanceof Error ? err.message : 'Failed to load document package');
      } finally {
        setDocumentPackageLoading(false);
      }
    }
    async function loadDocumentationAgentReport() {
      try {
        setDocumentationAgentReportLoading(true);
        setDocumentationAgentReportError(null);
        const data = await fetchSituationDocumentationAgentReport(id);
        setDocumentationAgentReport(data);
      } catch (err) {
        setDocumentationAgentReportError(err instanceof Error ? err.message : 'Failed to load documentation agent report');
      } finally {
        setDocumentationAgentReportLoading(false);
      }
    }
    async function loadDocumentationExtractions() {
      try {
        setDocumentationExtractionsError(null);
        const data = await fetchSituationDocumentationExtractions(id);
        setDocumentationExtractions(data);
      } catch (err) {
        setDocumentationExtractionsError(err instanceof Error ? err.message : 'Failed to load draft extracted fields');
      }
    }
    async function loadPromotionReadiness() {
      try {
        setPromotionReadinessLoading(true);
        setPromotionReadinessError(null);
        const data = await fetchSituationPromotionReadiness(id);
        setPromotionReadiness(data);
      } catch (err) {
        setPromotionReadinessError(err instanceof Error ? err.message : 'Failed to load promotion readiness');
      } finally {
        setPromotionReadinessLoading(false);
      }
    }
    async function loadHistoricalAnalogues() {
      try {
        setHistoricalAnaloguesLoading(true);
        setHistoricalAnaloguesError(null);
        const analogueData = await fetchSituationHistoricalAnalogues(id);
        setHistoricalAnalogues(analogueData);
      } catch (err) {
        setHistoricalAnaloguesError(err instanceof Error ? err.message : 'Failed to load historical analogues');
      } finally {
        setHistoricalAnaloguesLoading(false);
      }
    }
    async function loadActivityTimeline() {
      try {
        setActivityTimelineLoading(true);
        setActivityTimelineError(null);
        const timelineData = await fetchSituationActivityTimeline(id);
        setActivityTimeline(timelineData);
      } catch (err) {
        setActivityTimelineError(err instanceof Error ? err.message : 'Failed to load case activity timeline');
      } finally {
        setActivityTimelineLoading(false);
      }
    }
    if (id) load();
    if (id) loadEvidenceLinks();
    if (id) loadDocumentationGuide();
    if (id) loadCompletionWorkbench();
    if (id) loadOfficialSourceFinder();
    if (id) loadSecDocumentAcquisition();
    if (id) loadDocumentPackage();
    if (id) loadDocumentationAgentReport();
    if (id) loadDocumentationExtractions();
    if (id) loadPromotionReadiness();
    if (id) loadHistoricalAnalogues();
    if (id) loadActivityTimeline();
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
  const secPackageCandidates = resourceCandidates
    .filter(isSecPackageCandidate)
    .sort((a, b) => secFileRank(a) - secFileRank(b) || candidateFilename(a).localeCompare(candidateFilename(b)));
  const visibleSecFiles = secPackageCandidates.filter(candidate => secFileRank(candidate) <= 4).slice(0, 5);
  const otherCandidates = resourceCandidates.filter(candidate => !isSecPackageCandidate(candidate));
  const secDirectoryUrl = secPackageCandidates.map(secDirectoryFromCandidate).find(Boolean) ?? situation?.filing_url ?? null;
  const searchSuggestions = workspace?.search_suggestions ?? [];
  const workflowStatus = workspace?.workflow_status ?? (situation?.status === 'detected' ? 'new_detection' : situation?.status ?? 'new_detection');
  const researchCaseId = workspace?.research_case_id;

  async function copyText(text: string, key: string) {
    try {
      if (!navigator.clipboard?.writeText) throw new Error('Clipboard API unavailable');
      await navigator.clipboard.writeText(text);
      setCopiedKey(key);
    } catch {
      setCopiedKey('copy-failed');
    }
    setTimeout(() => setCopiedKey(null), 1500);
  }

  async function handleSecDocumentAcquisition() {
    try {
      setSecDocumentAcquiring(true);
      setSecDocumentAcquisitionError(null);
      const result = await acquireSituationSecDocuments(id);
      setSecDocumentAcquisition(result);
      await load();
    } catch (err) {
      setSecDocumentAcquisitionError(err instanceof Error ? err.message : 'Failed to acquire SEC document metadata');
    } finally {
      setSecDocumentAcquiring(false);
    }
  }

  async function handleAddResource() {
    if (!situation) return;
    setSavingResource(true);
    setResourceMessage(null);
    setResourceError(null);
    try {
      const relatedResourceIds = Array.from(new Set([
        resourceForm.related_resource_id,
        resourceForm.task_document_key,
      ].filter(Boolean)));
      const relatedCheckIds = Array.from(new Set([
        resourceForm.related_check_id,
        resourceForm.task_checklist_id,
      ].filter(Boolean)));
      const result = await addSituationResource(situation.id, {
        title: resourceForm.title,
        url: resourceForm.url,
        source_type: resourceForm.source_type,
        notes: resourceForm.notes || undefined,
        related_resource_ids: relatedResourceIds.length > 0 ? relatedResourceIds : undefined,
        related_check_ids: relatedCheckIds.length > 0 ? relatedCheckIds : undefined,
      });
      setSituation(result.situation);
      setResourceForm({
        title: '',
        url: '',
        source_type: 'other',
        notes: '',
        related_resource_id: '',
        related_check_id: '',
        task_document_key: '',
        task_checklist_id: '',
        task_source_hint: '',
      });
      setResourceMessage(result.created ? 'Candidate source added — needs review.' : 'Candidate source already exists — needs review.');
      await refreshDocumentationIntakeData();
    } catch (err) {
      setResourceError(err instanceof Error ? err.message : 'Failed to add resource');
    } finally {
      setSavingResource(false);
    }
  }

  function sourceTypeForTask(task: DocumentationAgentDocument): string {
    if (task.source_hint === 'SEC') return 'sec_filing';
    if (task.source_hint === 'company_ir') return 'company_ir';
    return 'other';
  }

  function handleTaskAddSourceLink(task: DocumentationAgentDocument) {
    const relatedResource = requiredResources.find(resource => resource.resource_id === task.document_key);
    const relatedChecklist = documentationAgentReport?.checklist.find(item =>
      item.required_document_keys.includes(task.document_key) ||
      item.missing_document_keys.includes(task.document_key) ||
      item.manual_check_document_keys.includes(task.document_key),
    );
    const relatedWorkspaceCheck = relatedChecklist
      ? workspace?.checklist.find(item => item.check_id === relatedChecklist.key)
      : null;

    setAdvancedToolsOpen(true);
    setResourceForm(current => ({
      ...current,
      title: current.title || task.label,
      source_type: current.source_type === 'other' ? sourceTypeForTask(task) : current.source_type,
      related_resource_id: relatedResource?.resource_id ?? current.related_resource_id,
      related_check_id: relatedWorkspaceCheck?.check_id ?? current.related_check_id,
      task_document_key: task.document_key,
      task_checklist_id: relatedChecklist?.key ?? '',
      task_source_hint: task.source_hint,
      notes: current.notes || `Candidate source for ${task.label}. Source hint: ${task.source_hint}. Requires Dani manual review; not verified.`,
    }));

    window.setTimeout(() => {
      document.getElementById('add-resource-manually')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
      manualResourceUrlRef.current?.focus();
    }, 100);
  }

  async function handleReadAndMapDraft(task: DocumentationAgentDocument, candidateSourceId: string) {
    if (!situation) return;
    const key = `${task.document_key}:${candidateSourceId}`;
    setReadingDraftKey(key);
    setDocumentationExtractionsError(null);
    try {
      const rows = await readSituationDocumentationSourceDraft(situation.id, {
        candidate_source_id: candidateSourceId,
        document_key: task.document_key,
      });
      setDocumentationExtractions(current => {
        const retained = current.filter(row => !(row.candidate_source_id === candidateSourceId && row.document_key === task.document_key));
        return [...rows, ...retained];
      });
    } catch (err) {
      setDocumentationExtractionsError(err instanceof Error ? err.message : 'Failed to read and map draft fields');
    } finally {
      setReadingDraftKey(null);
    }
  }

  async function handleReviewExtraction(field: DocumentationExtractionField, status: 'accepted' | 'rejected' | 'edited', value?: string) {
    setReviewingExtractionId(field.id);
    setDocumentationExtractionsError(null);
    try {
      const updated = await reviewDocumentationExtractionField(field.id, {
        status,
        extracted_value: value,
        reviewed_by: 'Dani',
      });
      setDocumentationExtractions(current => current.map(item => item.id === updated.id ? updated : item));
      setEditingExtractionId(null);
      setEditingExtractionValue('');
    } catch (err) {
      setDocumentationExtractionsError(err instanceof Error ? err.message : 'Failed to review draft field');
    } finally {
      setReviewingExtractionId(null);
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
        badge={<StatusBadge value={situation.status} label={caseStatusLabel(situation.status, Boolean(researchCaseId))} />}
        actions={
          <>
            <Link href="/investment/situations" className="btn btn--secondary btn--sm">
              Back to Kanban
            </Link>
            <Link href={`/investment/evaluations/${situation.id}`} className="btn btn--secondary btn--sm">
              Evaluation Detail
            </Link>
          </>
        }
      />

      <InfoBanner variant="guardrail">
        Manual review only · Metadata only · No auto-verification · No investment recommendation.
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
          ['Classification Strength', classificationStrengthLabel(secDetection.detection_confidence)],
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

      <div style={{ marginTop: 16, marginBottom: 16 }}>
        <SituationQuickLinks
          situation={situation}
          researchCaseId={researchCaseId}
        />
      </div>

      <div style={{ marginBottom: 16 }}>
        <SECTransparencyPanel
          situation={situation}
          secDetection={secDetection as Record<string, unknown>}
          documentPackage={documentPackage}
          evidenceLinks={evidenceLinks}
        />
      </div>

      <div style={{ marginBottom: 16 }}>
        <EducationStudyGuidePanel
          situation={situation}
          report={documentationAgentReport}
        />
      </div>

      <DocumentationTasksPanel
        report={documentationAgentReport}
        situation={situation}
        onAddSourceLink={handleTaskAddSourceLink}
        extractionFields={documentationExtractions}
        extractionError={documentationExtractionsError}
        readingDraftKey={readingDraftKey}
        reviewingExtractionId={reviewingExtractionId}
        editingExtractionId={editingExtractionId}
        editingExtractionValue={editingExtractionValue}
        onReadAndMapDraft={handleReadAndMapDraft}
        onReviewExtraction={handleReviewExtraction}
        onStartEditExtraction={(field) => {
          setEditingExtractionId(field.id);
          setEditingExtractionValue(field.extracted_value ?? '');
        }}
        onCancelEditExtraction={() => {
          setEditingExtractionId(null);
          setEditingExtractionValue('');
        }}
        onEditExtractionValue={setEditingExtractionValue}
      />

      <div style={{ marginTop: 16 }}>
        <DocumentationAgentPanel
          report={documentationAgentReport}
          loading={documentationAgentReportLoading}
          error={documentationAgentReportError}
          showGuardrailNote={false}
        />
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: 16, marginTop: 16 }}>
        <DocumentPackagePanel
          packageData={documentPackage}
          loading={documentPackageLoading}
          error={documentPackageError}
        />

        <SectionCard title="Evidence Links / Source Traceability">
          {evidenceLinksError && (
            <InfoBanner variant="warning">{evidenceLinksError}</InfoBanner>
          )}
          <EvidenceLinksPanel
            title="SpecialSituation evidence links"
            links={evidenceLinks?.links ?? []}
            guardrails={[]}
            searchSuggestions={(evidenceLinks?.search_suggestions ?? searchSuggestions).slice(0, 3)}
            emptyText="No stored evidence links are available for this situation yet."
            compact
          />
        </SectionCard>
      </div>

      <details
        open={advancedToolsOpen}
        onToggle={event => setAdvancedToolsOpen(event.currentTarget.open)}
        style={{ marginTop: 16, marginBottom: 20 }}
      >
        <summary style={{ cursor: 'pointer', fontFamily: 'var(--font-mono)', fontSize: 12, color: 'var(--text-muted)', textTransform: 'uppercase' }}>
          Advanced tools
        </summary>
        <div style={{ display: 'grid', gap: 16, marginTop: 14 }}>
          <CaseDocumentationGuidePanel
            guide={documentationGuide}
            error={documentationGuideError}
            onCopy={copyText}
            copiedKey={copiedKey}
          />

          <CaseCompletionWorkbench
            workbench={completionWorkbench}
            loading={completionWorkbenchLoading}
            error={completionWorkbenchError}
          />

          <OfficialSourceFinderPanel
            finder={officialSourceFinder}
            loading={officialSourceFinderLoading}
            error={officialSourceFinderError}
            copiedKey={copiedKey}
            onCopy={copyText}
          />

          <SecDocumentAcquisitionPanel
            packageData={secDocumentAcquisition}
            loading={secDocumentAcquisitionLoading}
            acquiring={secDocumentAcquiring}
            error={secDocumentAcquisitionError}
            copiedKey={copiedKey}
            onCopy={copyText}
            onAcquire={handleSecDocumentAcquisition}
          />

          <HistoricalAnaloguesPanel
            analogues={historicalAnalogues}
            loading={historicalAnaloguesLoading}
            error={historicalAnaloguesError}
          />

          <div>
            {activityTimelineLoading && (
              <InfoBanner variant="info">Loading derived timeline...</InfoBanner>
            )}
            <CaseActivityTimeline
              title="Case Activity Log"
              events={activityTimeline?.events ?? []}
              error={activityTimelineError}
            />
          </div>
        </div>
      </details>

      <PromotionReadinessPanel
        readiness={promotionReadiness}
        loading={promotionReadinessLoading}
        error={promotionReadinessError}
      />

      {!workspace && (
        <InfoBanner variant="warning">
          No methodology workspace attached yet. Run the manual backfill CLI after backend deployment.
        </InfoBanner>
      )}

      {workspace && (
        <>

        <div style={{ display: 'flex', gap: 20, alignItems: 'flex-start', flexWrap: 'wrap' }}>

          {/* LEFT — main content */}
          <div style={{ flex: '1 1 500px', minWidth: 0, display: 'flex', flexDirection: 'column', gap: 20 }}>

            <div id="situation-methodology-checklist" style={{ scrollMarginTop: 80 }}>
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
                            <StatusBadge value={item.status} label={checklistStatusLabel(item.status)} />
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
            </div>

            <div id="situation-required-resources" style={{ scrollMarginTop: 80 }}>
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
            </div>

            <div id="situation-resource-candidates" style={{ scrollMarginTop: 80 }}>
            <SectionCard title="Found / Candidate Resources">
              {resourceCandidates.length === 0 ? (
                <InfoBanner variant="info">
                  No resource candidates stored yet. Run Resource Scout via CLI, or add manually below.
                </InfoBanner>
              ) : (
                <div style={{ display: 'grid', gap: 10 }}>
                  {secPackageCandidates.length > 0 && (
                    <div className="card" style={{ padding: '12px 14px', display: 'grid', gap: 10 }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', gap: 12, alignItems: 'flex-start', flexWrap: 'wrap' }}>
                        <div>
                          <div style={{ fontSize: 13, fontWeight: 700, color: 'var(--text-primary)' }}>SEC filing package</div>
                          <div style={{ marginTop: 4, display: 'flex', flexWrap: 'wrap', gap: 5 }}>
                            <span className="status-badge status-badge--partial">{secPackageCandidates.length} files available</span>
                            <span className="status-badge status-badge--readonly">metadata only</span>
                            <span className="status-badge status-badge--manual">Needs review</span>
                            <span className="status-badge status-badge--readonly">Not verified</span>
                          </div>
                        </div>
                        {secDirectoryUrl && (
                          <a href={secDirectoryUrl} target="_blank" rel="noreferrer" className="btn btn--secondary btn--sm">
                            Open SEC directory
                          </a>
                        )}
                      </div>

                      {visibleSecFiles.length > 0 && (
                        <div style={{ display: 'grid', gap: 6 }}>
                          <div style={MONO_LABEL}>Likely useful files</div>
                          {visibleSecFiles.map(candidate => (
                            <div key={candidate.resource_candidate_id} style={{ display: 'flex', justifyContent: 'space-between', gap: 10, alignItems: 'center', fontSize: 12 }}>
                              <div style={{ minWidth: 0 }}>
                                <span style={{ color: 'var(--text-primary)', fontWeight: 600 }}>{secFileKind(candidate)}</span>
                                <span style={{ color: 'var(--text-muted)' }}> · {candidateFilename(candidate)}</span>
                              </div>
                              {candidate.url && (
                                <a href={candidate.url} target="_blank" rel="noreferrer" className="btn btn--ghost btn--sm">
                                  Open
                                </a>
                              )}
                            </div>
                          ))}
                        </div>
                      )}

                      <details>
                        <summary style={{ cursor: 'pointer', fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--text-muted)' }}>
                          Show all SEC files
                        </summary>
                        <div style={{ display: 'grid', gap: 8, marginTop: 10 }}>
                          {secPackageCandidates.map(candidate => (
                            <CandidateCard
                              key={candidate.resource_candidate_id}
                              candidate={candidate}
                              requiredResources={requiredResources}
                              checklist={workspace.checklist}
                              savingCandidateId={savingCandidateId}
                              copiedKey={copiedKey}
                              onCopy={copyText}
                              onPatch={handleCandidatePatch}
                            />
                          ))}
                        </div>
                      </details>
                    </div>
                  )}

                  {otherCandidates.map(candidate => (
                    <CandidateCard
                      key={candidate.resource_candidate_id}
                      candidate={candidate}
                      requiredResources={requiredResources}
                      checklist={workspace.checklist}
                      savingCandidateId={savingCandidateId}
                      copiedKey={copiedKey}
                      onCopy={copyText}
                      onPatch={handleCandidatePatch}
                    />
                  ))}
                </div>
              )}
            </SectionCard>
            </div>

            <div id="add-resource-manually" style={{ scrollMarginTop: 80 }}>
            <SectionCard title="Add Source Link Manually">
              <div style={{ display: 'grid', gap: 10 }}>
                {resourceForm.task_document_key && (
                  <div style={{ padding: 10, border: '1px solid var(--border-default)', borderRadius: 8, background: 'var(--bg-subtle)' }}>
                    <div style={{ fontSize: 12, fontWeight: 650, color: 'var(--text-primary)' }}>
                      Mapping source link to: {resourceForm.title || resourceForm.task_document_key}
                    </div>
                    <div style={{ marginTop: 4, fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-faint)', lineHeight: 1.5 }}>
                      Document key: {resourceForm.task_document_key}
                      {resourceForm.task_source_hint ? ` · Source hint: ${resourceForm.task_source_hint}` : ''}
                      {resourceForm.task_checklist_id ? ` · Checklist: ${resourceForm.task_checklist_id}` : ''}
                      {' · Candidate only; not read, extracted, or verified.'}
                    </div>
                  </div>
                )}
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
                    id="manual-resource-url"
                    ref={manualResourceUrlRef}
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

          </div>

          {/* RIGHT — sidebar */}
          <div style={{ flex: '0 0 300px', minWidth: 280, display: 'flex', flexDirection: 'column', gap: 16 }}>

            <div id="situation-sec-metadata" style={{ scrollMarginTop: 80 }}>
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
            </div>

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
                  ['Mapped for Review', progress?.evidence_found ?? 0],
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

            <div id="situation-researchcase-promotion" style={{ scrollMarginTop: 80 }}>
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
            </div>

            <div id="situation-search-suggestions" style={{ scrollMarginTop: 80 }}>
            <SectionCard title="Search Suggestions">
              {searchSuggestions.length === 0 ? (
                <InfoBanner variant="info">
                  No stored manual search suggestions yet. These suggestions are prompts for human research only; SwissEdge does not run them automatically.
                </InfoBanner>
              ) : (
                <>
                  <div style={{ fontSize: 11, color: 'var(--text-muted)', lineHeight: 1.5, marginBottom: 8 }}>
                    Stored manual search suggestions. They are not fetched automatically, not evidence, and not verified.
                    Paste this into Google, SEC search, or company IR. SwissEdge has not run this search automatically.
                    {copiedKey === 'copy-failed' && (
                      <span style={{ display: 'block', marginTop: 4, color: '#b45309' }}>Copy failed - select the query text manually.</span>
                    )}
                  </div>
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
                              Manual search suggestion / {suggestion.suggestion_type}
                            </div>
                            <div style={{ fontSize: 12, color: 'var(--text-primary)', wordBreak: 'break-word' }}>{suggestion.query}</div>
                          </div>
                          <button
                            className="btn btn--ghost btn--sm"
                            onClick={() => copyText(suggestion.query, suggestion.suggestion_id)}
                            style={{ flexShrink: 0 }}
                          >
                            {copiedKey === suggestion.suggestion_id ? 'Copied' : 'Copy query'}
                          </button>
                        </div>
                      ))}
                    </div>
                  )}
                </>
              )}
            </SectionCard>
            </div>

          </div>
        </div>
        </>
      )}
    </div>
  );
}
