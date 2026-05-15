const API_BASE_URL = process.env.NEXT_PUBLIC_SWISSEDGE_API_BASE_URL || 'http://localhost:8000';

export interface Situation {
  id: string;
  company_name: string;
  ticker: string | null;
  filing_type: string | null;
  filing_url: string | null;
  detected_at: string | null;
  status: string;
  situation_type?: string | null;
  evaluator_version?: string;
  v2_situation_type?: string | null;
  v2_subtype?: string | null;
  selected_playbook?: string | null;
  playbook_status?: string | null;
  recommendation?: string | null;
  evaluator_confidence?: string | null;
  human_review_required_count?: number;
  risk_flags_count?: number;
  prohibited_inferences_count?: number;
  missing_documents_count?: number;
  fallback_occurred?: boolean;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  evaluation?: any;
  methodology_workspace?: MethodologyWorkspace | null;
  notes?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
}

export interface MethodologyChecklistItem {
  check_id: string;
  section: string;
  title: string;
  description: string;
  required_evidence_types: string[];
  status: string;
  human_review_required: boolean;
  notes: string | null;
  evidence_refs: string[];
}

export interface RequiredResourceItem {
  resource_id: string;
  title: string;
  description: string;
  source_type: string;
  required_or_optional: string;
  expected_source: string;
  related_check_ids: string[];
  status: string;
}

export interface ResourceCandidate {
  resource_candidate_id: string;
  title: string;
  url: string;
  source_type: string;
  source_domain: string;
  status: string;
  confidence: string;
  related_resource_ids: string[];
  related_check_ids: string[];
  discovered_by: string;
  discovered_at: string;
  notes: string | null;
}

export interface SearchSuggestion {
  suggestion_id: string;
  query: string;
  suggestion_type: string;
  status: string;
  discovered_by: string;
  created_at: string;
}

export interface EvidenceLink {
  id: string;
  label: string;
  url: string | null;
  source_type: string;
  origin: string;
  filing_type: string | null;
  accession_number: string | null;
  cik: string | null;
  company_name: string | null;
  filing_date: string | null;
  status: string;
  linked_required_resource_ids: string[];
  linked_checklist_item_ids: string[];
  metadata_only: boolean;
  verified: boolean;
  notes: string | null;
}

export interface SituationEvidenceLinksPackage {
  situation_id: string;
  company_name: string;
  ticker: string | null;
  sec_detection: Record<string, unknown>;
  links: EvidenceLink[];
  required_resource_links: Array<{
    resource_id: string | null;
    title: string | null;
    status: string;
    links: EvidenceLink[];
  }>;
  checklist_links: Array<{
    check_id: string | null;
    title: string | null;
    status: string;
    links: EvidenceLink[];
  }>;
  search_suggestions: SearchSuggestion[];
  guardrails: string[];
}

export interface ResearchCaseEvidenceLinksPackage {
  research_case_id: string;
  case_title: string | null;
  origin: {
    intake_method: string | null;
    situation_id: string | null;
    source: string;
  };
  links: EvidenceLink[];
  source_links: EvidenceLink[];
  document_links: EvidenceLink[];
  snapshot_links: EvidenceLink[];
  guardrails: string[];
}

export interface CaseDocumentationGuidePackage {
  case_id: string;
  case_type: 'special_situation' | 'research_case';
  title: string;
  documentation_quality: {
    level: 'good' | 'needs_links' | 'needs_required_resources' | 'needs_evidence_mapping' | 'needs_manual_review';
    score: number;
    summary: string;
    checks: Array<{ label: string; status: 'ok' | 'needs_work' }>;
  };
  detection_guide: {
    source: string;
    company_name: string | null;
    ticker: string | null;
    cik: string | null;
    accession_number: string | null;
    filing_type: string | null;
    filing_date: string | null;
    detected_at: string | null;
    situation_type: string | null;
    selected_playbook: string | null;
    detection_confidence: string | null;
    filing_url: string | null;
    manual_verification_steps: string[];
  };
  missing_evidence: {
    missing_required_resources: Array<Record<string, unknown>>;
    missing_checklist_items: Array<Record<string, unknown>>;
    candidate_only_resources: Array<Record<string, unknown>>;
    evidence_found_not_verified: Array<Record<string, unknown>>;
    rejected_resources: Array<Record<string, unknown>>;
  };
  research_agent: {
    agent_name: string;
    agent_key: string;
    mode: string;
    current_mission: string;
    last_activity: string | null;
    next_manual_actions: string[];
    future_scheduler_note: string;
  };
  search_plan: {
    stored_search_suggestions: Array<Record<string, unknown>>;
    manual_search_steps: string[];
    copyable_queries: string[];
  };
  quick_links: Array<{
    label: string;
    url: string;
    source_type: string;
    metadata_only: boolean;
  }>;
  activity_timeline: Array<{
    label: string;
    timestamp: string | null;
    detail: string | null;
    derived: boolean;
  }>;
  guardrails: string[];
}

export interface OfficialSourceFinderPackage {
  case_id: string;
  case_type: 'special_situation' | 'research_case';
  source_context: {
    source: string;
    company_name: string | null;
    ticker: string | null;
    cik: string | null;
    accession_number: string | null;
    filing_type: string | null;
    filing_date: string | null;
    situation_type: string | null;
    selected_playbook: string | null;
    stored_filing_url: string | null;
  };
  official_links: Array<{
    label: string;
    url: string | null;
    link_type: string;
    metadata_only: boolean;
    verified: boolean;
    supports: string[];
    notes: string | null;
  }>;
  manual_locator_steps: Array<{
    step: number;
    title: string;
    description: string;
    link_url: string | null;
    supports_required_resources: string[];
    supports_checklist_items: string[];
  }>;
  missing_document_targets: Array<{
    title: string;
    required_resource_id: string | null;
    checklist_item_id: string | null;
    priority: 'high' | 'medium' | 'low';
    why_needed: string;
    where_to_search: string[];
    manual_queries: string[];
  }>;
  copyable_queries: Array<{
    query: string;
    purpose: string;
    where_to_use: string;
    supports_required_resources: string[];
    supports_checklist_items: string[];
    not_executed_by_swissedge: boolean;
  }>;
  coverage: {
    stored_official_links_count: number;
    missing_required_documents_count: number;
    manual_queries_count: number;
    candidate_sources_count: number;
    evidence_found_count: number;
  };
  guardrails: string[];
}

export interface HistoricalAnaloguesPackage {
  case_id: string;
  case_type: 'special_situation' | 'research_case';
  case_summary: {
    company_name: string | null;
    ticker: string | null;
    filing_type: string | null;
    situation_type: string | null;
    selected_playbook: string | null;
    methodology_status: string;
  };
  matched_patterns: Array<{
    pattern_id: string;
    title: string;
    source: string;
    similarity_reason: string;
    applies_because: string[];
    manual_checks: string[];
    risk_notes: string[];
    confidence: 'high' | 'medium' | 'low';
    not_evaluation: boolean;
  }>;
  historical_case_matches: Array<{
    historical_case_id: string;
    title: string;
    situation_type: string | null;
    similarity_score: number;
    similarity_reasons: string[];
    key_differences: string[];
    manual_comparison_steps: string[];
    source: string;
    not_evaluation: boolean;
  }>;
  course_methodology_links: Array<{
    label: string;
    playbook: string;
    section: string;
    safe_summary: string;
    human_review_required: boolean;
  }>;
  comparison_checklist: Array<{
    label: string;
    status: string;
    why_it_matters: string;
    related_required_resource_ids: string[];
    related_check_ids: string[];
  }>;
  warnings: string[];
  guardrails: string[];
}

export interface SecDocumentAcquisitionPackage {
  case_id: string;
  case_type: 'special_situation' | 'research_case';
  mode: string;
  available_identifiers: {
    filing_url: string | null;
    cik: string | null;
    accession_number: string | null;
    filing_type: string | null;
    filing_date: string | null;
    company_name: string | null;
    ticker: string | null;
  };
  missing_identifiers: string[];
  official_links: Array<{
    title: string;
    url: string;
    doc_type: string;
    accession_number: string | null;
    form_type: string | null;
    acquisition_status: string;
    human_review_required: boolean;
    verified: boolean;
  }>;
  likely_document_targets: Array<{
    label: string;
    expected_doc_type: string;
    reason: string;
  }>;
  manual_locator_steps: Array<{
    step: number;
    title: string;
    description: string;
    link_url: string | null;
  }>;
  copyable_queries: Array<{
    query: string;
    purpose: string;
    where_to_use: string;
    not_executed_by_swissedge: boolean;
  }>;
  acquired_documents: Array<{
    title: string;
    url: string;
    doc_type: string;
    accession_number: string | null;
    form_type: string | null;
    acquisition_status: string;
    human_review_required: boolean;
    verified: boolean;
  }>;
  stored_records: Array<Record<string, unknown>>;
  warnings: string[];
  manual_next_steps: string[];
  guardrails: string[];
}

export interface CaseCompletionPackage {
  case_id: string;
  case_type: 'special_situation' | 'research_case';
  completion_level: 'blocked' | 'needs_sources' | 'needs_evidence_mapping' | 'ready_for_manual_review' | 'promoted';
  completion_score: number;
  summary: {
    missing_required_resources: number;
    candidate_sources_to_review: number;
    checklist_items_needing_evidence: number;
    evidence_found_not_verified: number;
    rejected_or_noisy_sources: number;
    manual_review_required: boolean;
    research_case_exists: boolean;
  };
  blocking_items: Array<{
    id: string;
    label: string;
    reason: string;
    severity: 'high' | 'medium' | 'low';
    related_section: string;
    anchor: string;
  }>;
  next_manual_actions: Array<{
    id: string;
    label: string;
    description: string;
    priority: 'high' | 'medium' | 'low';
    action_type: string;
    manual_only: boolean;
    improves: string[];
    target_anchor: string;
  }>;
  score_improvement_plan: {
    detection: string[];
    structuring: string[];
    risk_discipline: string[];
  };
  section_status: Array<{
    section: string;
    status: 'ok' | 'needs_work' | 'missing';
    anchor: string;
  }>;
  guardrails: string[];
}

export interface CaseActivityEvent {
  id: string;
  timestamp: string | null;
  timestamp_label: string;
  event_type:
    | 'detection'
    | 'workspace'
    | 'resource_candidate'
    | 'search_suggestion'
    | 'evidence_mapping'
    | 'promotion'
    | 'research_case'
    | 'task'
    | 'source'
    | 'document'
    | 'agent_activity'
    | 'quality_signal'
    | 'current_state';
  title: string;
  description: string;
  origin: string;
  agent_key: string | null;
  agent_name: string | null;
  related_entity_type: string;
  related_entity_id: string | null;
  status: 'info' | 'needs_attention' | 'evidence_found' | 'rejected' | 'manual_review_required' | 'completed';
  link_url: string | null;
  metadata_only: boolean;
}

export interface CaseActivityTimelinePackage {
  case_id: string;
  case_type: 'special_situation' | 'research_case';
  title: string;
  events: CaseActivityEvent[];
  summary: {
    total_events: number;
    needs_attention: number;
    agent_events: number;
    metadata_only: boolean;
    derived_only: boolean;
  };
  guardrails: string[];
}

export interface MethodologyWorkspace {
  template_key: string;
  template_version: string;
  source: string;
  requires_course_review: boolean;
  workflow_status?: string;
  research_case_id?: string;
  checklist: MethodologyChecklistItem[];
  required_resources: RequiredResourceItem[];
  resource_candidates?: ResourceCandidate[];
  search_suggestions?: SearchSuggestion[];
  progress: {
    total_checks: number;
    verified_checks: number;
    evidence_found: number;
    missing_required_resources: number;
    candidate_resources?: number;
    human_review_required_count?: number;
  };
}

export async function addSituationResource(
  situationId: string,
  payload: {
    title?: string;
    url: string;
    source_type: string;
    notes?: string;
    related_resource_ids?: string[];
    related_check_ids?: string[];
  },
): Promise<{ situation: Situation; created: boolean; existing: boolean }> {
  const response = await fetch(`${API_BASE_URL}/api/investment/situations/${situationId}/resources`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    const body = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(typeof body?.detail === 'string' ? body.detail : `HTTP ${response.status}`);
  }
  return response.json();
}

export async function updateSituationWorkflowStatus(
  situationId: string,
  workflowStatus: string,
): Promise<{ situation: Situation; valid_workflow_statuses: string[] }> {
  const response = await fetch(`${API_BASE_URL}/api/investment/situations/${situationId}/workflow-status`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ workflow_status: workflowStatus }),
  });
  if (!response.ok) {
    const body = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(typeof body?.detail === 'string' ? body.detail : `HTTP ${response.status}`);
  }
  return response.json();
}

export async function updateSituationResourceCandidate(
  situationId: string,
  resourceCandidateId: string,
  payload: {
    status?: string;
    notes?: string;
    related_resource_ids?: string[];
    related_check_ids?: string[];
  },
): Promise<{ situation: Situation; candidate: ResourceCandidate; valid_resource_statuses: string[] }> {
  const response = await fetch(
    `${API_BASE_URL}/api/investment/situations/${situationId}/resources/${resourceCandidateId}`,
    {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    },
  );
  if (!response.ok) {
    const body = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(typeof body?.detail === 'string' ? body.detail : `HTTP ${response.status}`);
  }
  return response.json();
}

export async function promoteSituationToResearchCase(
  situationId: string,
  payload?: {
    title?: string;
    initial_status?: string;
    notes?: string;
  },
): Promise<{ created: boolean; research_case: ResearchCase }> {
  const response = await fetch(`${API_BASE_URL}/api/investment/situations/${situationId}/promote-to-research-case`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload ?? {}),
  });
  if (!response.ok) {
    const body = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(typeof body?.detail === 'string' ? body.detail : `HTTP ${response.status}`);
  }
  return response.json();
}

export interface SituationsResponse {
  count: number;
  situations: Situation[];
}

export async function fetchSituations(params?: {
  evaluator_version?: string;
  playbook_status?: string;
  recommendation?: string;
  include_archived?: boolean;
}): Promise<SituationsResponse> {
  const url = new URL(`${API_BASE_URL}/api/investment/situations`);

  if (params?.evaluator_version) {
    url.searchParams.append('evaluator_version', params.evaluator_version);
  }
  if (params?.playbook_status) {
    url.searchParams.append('playbook_status', params.playbook_status);
  }
  if (params?.recommendation) {
    url.searchParams.append('recommendation', params.recommendation);
  }
  if (params?.include_archived !== undefined) {
    url.searchParams.append('include_archived', params.include_archived.toString());
  }

  const response = await fetch(url.toString());

  if (!response.ok) {
    throw new Error(`Failed to fetch situations: ${response.statusText}`);
  }

  return response.json();
}

export async function archiveSituation(id: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/investment/situations/${id}`, {
    method: 'PATCH',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ status: 'archived' }),
  });

  if (!response.ok) {
    throw new Error(`Failed to archive situation: ${response.statusText}`);
  }
}

export async function updateSituationStatus(id: string, status: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/investment/situations/${id}`, {
    method: 'PATCH',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ status }),
  });

  if (!response.ok) {
    throw new Error(`Failed to update status: ${response.statusText}`);
  }
}

export async function saveNotes(id: string, notes: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/investment/situations/${id}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ notes }),
  });

  if (!response.ok) {
    throw new Error(`Failed to save notes: ${response.statusText}`);
  }
}

export async function fetchSituation(id: string): Promise<Situation> {
  const response = await fetch(`${API_BASE_URL}/api/investment/situations/${id}`);

  if (!response.ok) {
    throw new Error(`Failed to fetch situation: ${response.statusText}`);
  }

  return response.json();
}

export async function fetchSituationEvidenceLinks(id: string): Promise<SituationEvidenceLinksPackage> {
  const response = await fetch(`${API_BASE_URL}/api/investment/situations/${id}/evidence-links`);

  if (!response.ok) {
    throw new Error(`Failed to fetch situation evidence links: ${response.statusText}`);
  }

  return response.json();
}

export async function fetchSituationDocumentationGuide(id: string): Promise<CaseDocumentationGuidePackage> {
  const response = await fetch(`${API_BASE_URL}/api/investment/situations/${id}/documentation-guide`);
  if (!response.ok) throw new Error(`Failed to fetch situation documentation guide: ${response.statusText}`);
  return response.json();
}

export async function fetchSituationOfficialSourceFinder(id: string): Promise<OfficialSourceFinderPackage> {
  const response = await fetch(`${API_BASE_URL}/api/investment/situations/${id}/official-source-finder`);
  if (!response.ok) throw new Error(`Failed to fetch situation official source finder: ${response.statusText}`);
  return response.json();
}

export async function fetchSituationHistoricalAnalogues(id: string): Promise<HistoricalAnaloguesPackage> {
  const response = await fetch(`${API_BASE_URL}/api/investment/situations/${id}/historical-analogues`);
  if (!response.ok) throw new Error(`Failed to fetch situation historical analogues: ${response.statusText}`);
  return response.json();
}

export async function fetchSituationCompletionWorkbench(id: string): Promise<CaseCompletionPackage> {
  const response = await fetch(`${API_BASE_URL}/api/investment/situations/${id}/completion-workbench`);
  if (!response.ok) throw new Error(`Failed to fetch situation completion workbench: ${response.statusText}`);
  return response.json();
}

export async function fetchSituationSecDocumentAcquisitionPreview(id: string): Promise<SecDocumentAcquisitionPackage> {
  const response = await fetch(`${API_BASE_URL}/api/investment/situations/${id}/sec-document-acquisition-preview`);
  if (!response.ok) throw new Error(`Failed to fetch SEC document acquisition preview: ${response.statusText}`);
  return response.json();
}

export async function acquireSituationSecDocuments(id: string): Promise<SecDocumentAcquisitionPackage> {
  const response = await fetch(`${API_BASE_URL}/api/investment/situations/${id}/sec-document-acquisition`, { method: 'POST' });
  if (!response.ok) throw new Error(`Failed to acquire SEC documents: ${response.statusText}`);
  return response.json();
}

export async function fetchSituationActivityTimeline(id: string): Promise<CaseActivityTimelinePackage> {
  const response = await fetch(`${API_BASE_URL}/api/investment/situations/${id}/activity-timeline`);
  if (!response.ok) throw new Error(`Failed to fetch situation activity timeline: ${response.statusText}`);
  return response.json();
}

export interface IntelligenceKpiCaseLink {
  id: string;
  case_type: 'research_case' | 'special_situation';
  title: string;
  href: string;
  score?: number;
  grade?: string;
  missing_items?: number;
}

export interface IntelligenceKpiPackage {
  generated_at: string;
  case_counts: {
    research_cases_total: number;
    special_situations_total: number;
    sec_detected: number;
    promoted_to_research_case: number;
    ready_for_manual_review: number;
    missing_evidence: number;
  };
  intelligence: {
    average_score: number;
    approvable_count: number;
    useful_incomplete_count: number;
    review_pipeline_count: number;
    lowest_scoring_cases: IntelligenceKpiCaseLink[];
    cases_needing_manual_work: IntelligenceKpiCaseLink[];
  };
  documentation: {
    average_documentation_quality: number;
    good_count: number;
    needs_links_count: number;
    needs_required_resources_count: number;
    needs_evidence_mapping_count: number;
  };
  evidence: {
    required_resources_total: number;
    missing_required_resources_total: number;
    candidate_found_total: number;
    evidence_found_total: number;
    rejected_total: number;
    evidence_links_total: number;
  };
  agent_ops: {
    rooms_count: number;
    agents_count: number;
    activity_rows_count: number;
    diagnostics_count: number;
    missing_evidence_hunter_load: number;
    rooms: Array<{ id: string; key: string; name: string; href: string }>;
  };
  bottlenecks: Array<{ key: string; label: string; severity: string; count: number }>;
  manual_next_actions: Array<{ label: string; reason: string; target_href: string }>;
  missing_evidence_cases: IntelligenceKpiCaseLink[];
  guardrails: string[];
}

export interface FontanaDiagnosticReport {
  title: string;
  mode: 'deterministic_observer';
  generated_at: string;
  summary: string;
  system_health: string[];
  case_bottlenecks: string[];
  evidence_gaps: string[];
  agent_ops_findings: string[];
  recommended_manual_next_steps: string[];
  suggested_future_sprints: string[];
  guardrails: string[];
}

export interface DaniWeberProcessImprovement {
  id: string;
  title: string;
  category: 'ADD_SOURCE' | 'IMPROVE_DOCUMENTATION_WORKFLOW' | 'IMPROVE_DETECTION_RULE' | 'IMPROVE_AGENT_SKILL' | 'FIX_BOTTLENECK' | 'ADD_KPI';
  evidence: string;
  recommendation: string;
  expected_impact: string;
  requires_dani_approval: boolean;
  auto_apply: boolean;
}

export interface DaniWeberMetrics {
  generated_at: string;
  mode: 'deterministic_read_only';
  total_special_situations: number;
  by_workflow_phase: Record<string, number>;
  by_situation_type: Record<string, number>;
  research_case_statuses: Record<string, number>;
  promotion_rate_to_research_case: {
    promoted_count: number;
    total_special_situations: number;
    rate_percent: number;
  };
  documentation_blockers: {
    missing_required_resources: number;
    checklist_blocked_items: number;
    human_review_required_items: number;
    rejected_resource_candidates: number;
  };
  missing_resource_frequency: Array<{ key: string; count: number }>;
  candidate_source_coverage: {
    required_resources_total: number;
    resource_candidates_total: number;
    candidate_found_total: number;
    coverage_percent: number;
    by_source_type: Array<{ key: string; count: number }>;
  };
  cases_stuck_by_phase: Array<{
    phase: string;
    count: number;
    cases: Array<{ id: string; title: string; href: string }>;
  }>;
  low_priority_or_noise_count: number;
  top_bottlenecks: Array<{ id: string; title: string; count: number; severity: string }>;
  recommended_process_improvements: DaniWeberProcessImprovement[];
  guardrails: string[];
}

export interface ExecutiveReviewFinding {
  id: string;
  coo_observation: string;
  cto_interpretation: string;
  product_area: string;
  severity: 'info' | 'warning' | 'critical';
  evidence: string;
  recommended_action: string;
  requires_dani_approval: boolean;
  auto_apply: boolean;
}

export interface ExecutiveReviewAction {
  id: string;
  title: string;
  product_area?: string;
  source?: string;
  category?: string;
  evidence: string;
  recommended_action?: string;
  reason?: string;
  requires_dani_approval: boolean;
  auto_apply: boolean;
}

export interface ExecutiveReviewPackage {
  generated_at: string;
  coo_summary: string;
  cto_summary: string;
  joint_findings: ExecutiveReviewFinding[];
  joint_recommendations: ExecutiveReviewAction[];
  pending_approval_items: ExecutiveReviewAction[];
  guardrails: string[];
  next_sprint_candidates: ExecutiveReviewAction[];
}

export async function fetchIntelligenceKpis(): Promise<IntelligenceKpiPackage> {
  const response = await fetch(`${API_BASE_URL}/api/investment/intelligence/kpis`);
  if (!response.ok) throw new Error(`Failed to fetch Intelligence KPIs: ${response.statusText}`);
  return response.json();
}

export async function fetchFontanaReport(): Promise<FontanaDiagnosticReport> {
  const response = await fetch(`${API_BASE_URL}/api/investment/intelligence/fontana-report`);
  if (!response.ok) throw new Error(`Failed to fetch Fontana report: ${response.statusText}`);
  return response.json();
}

export async function fetchDaniWeberMetrics(): Promise<DaniWeberMetrics> {
  const response = await fetch(`${API_BASE_URL}/api/investment/executive/dani-weber-metrics`);
  if (!response.ok) throw new Error(`Failed to fetch Dani Weber metrics: ${response.statusText}`);
  return response.json();
}

export async function fetchExecutiveReview(): Promise<ExecutiveReviewPackage> {
  const response = await fetch(`${API_BASE_URL}/api/investment/executive/review`);
  if (!response.ok) throw new Error(`Failed to fetch Executive Review: ${response.statusText}`);
  return response.json();
}

export interface V2PreviewResult {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  result: any;
  usage: {
    model?: string;
    input_tokens?: number;
    output_tokens?: number;
    provider?: string;
  };
  evaluator_version: string;
  fallback_occurred: boolean;
  daily_limit: {
    used: number;
    limit: number;
    remaining: number;
  };
}

export async function runV2Preview(situation: Situation): Promise<V2PreviewResult> {
  const body = {
    company: situation.company_name,
    ticker: situation.ticker ?? null,
    filing_type: situation.filing_type!,
    date: situation.detected_at!,
    url: situation.filing_url!,
    summary: situation.evaluation?.summary ?? '',
    situation_type: situation.situation_type ?? null,
    save_to_db: false,
  };

  const response = await fetch(`${API_BASE_URL}/api/investment/evaluate-v2`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });

  if (!response.ok) {
    const detail = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(detail.detail ?? `HTTP ${response.status}`);
  }

  return response.json();
}

export interface Agent {
  agent_name: string;
  display_name: string;
  purpose: string;
  runtime: string;
  current_status: string;
  total_runs: number;
  failed_runs: number;
  last_run: string | null;
  warnings?: string[];
  recommended_next_action?: string;
}

export interface AgentsResponse {
  count: number;
  agents: Agent[];
}

export async function fetchAgents(): Promise<AgentsResponse> {
  const response = await fetch(`${API_BASE_URL}/api/observability/agents`);

  if (!response.ok) {
    throw new Error(`Failed to fetch agents: ${response.statusText}`);
  }

  return response.json();
}

export interface AgentDetail {
  agent_name: string;
  display_name: string;
  purpose: string;
  runtime: string;
  current_status: string;
  module: string;
  owner: string;
  instructions: string;
  permissions: string;
  human_approval_rules: string;
  model?: string;
  tools?: string[];
  cost_metric: string;
  success_metric: string;
  failure_modes?: string[];
  outcome_score_definition: string;
  warnings?: string[];
  recommended_next_action?: string;
  stats: {
    total_runs: number;
    failed_runs: number;
    last_run: string | null;
    total_cost_usd: number;
    total_input_tokens: number;
    total_output_tokens: number;
  };
  last_outcome?: string | null;
  last_error?: string | null;
  recent_runs: AgentRun[];
  recent_ai_usage: AiUsage[];
}

export interface AgentRun {
  id: string;
  agent_name: string;
  agent_type: string;
  runtime: string;
  trigger_source: string;
  task_name: string;
  input_summary?: string;
  output_summary?: string;
  status: string;
  started_at: string | null;
  finished_at: string | null;
  duration_ms?: number;
  model_used?: string;
  input_tokens?: number;
  output_tokens?: number;
  estimated_cost_usd?: number;
  error_message?: string;
  human_approval_required?: boolean;
  human_approved?: boolean;
  final_outcome?: string;
  outcome_score?: number;
  api_calls_made?: Array<Record<string, unknown>> | Record<string, unknown> | null;
  database_records_created?: Record<string, unknown> | null;
}

export interface AiUsage {
  id: string;
  agent_name: string;
  provider: string;
  model: string;
  prompt_name?: string;
  input_tokens: number;
  output_tokens: number;
  total_tokens: number;
  estimated_cost_usd?: number;
  created_at: string | null;
}

export async function fetchAgent(agent_name: string): Promise<AgentDetail> {
  const response = await fetch(`${API_BASE_URL}/api/observability/agents/${agent_name}`);

  if (!response.ok) {
    throw new Error(`Failed to fetch agent: ${response.statusText}`);
  }

  return response.json();
}

export interface InvestmentSource {
  id: string;
  name: string;
  url: string;
  source_type: string | null;
  active: boolean;
  check_frequency_hours: number;
  last_checked: string | null;
  last_success: string | null;
  last_error: string | null;
  description: string | null;
  market: string | null;
  jurisdiction: string | null;
  priority: number;
  requires_api_key: boolean;
  access_method: string | null;
  query_template: string | null;
  notes: string | null;
}

export interface SourcesResponse {
  count: number;
  sources: InvestmentSource[];
}

export async function fetchSources(activeOnly?: boolean): Promise<SourcesResponse> {
  const url = new URL(`${API_BASE_URL}/api/investment/sources`);
  if (activeOnly) url.searchParams.append('active_only', 'true');

  const response = await fetch(url.toString());
  if (!response.ok) {
    throw new Error(`Failed to fetch sources: ${response.statusText}`);
  }
  return response.json();
}

export async function toggleSourceActive(id: string, active: boolean): Promise<InvestmentSource> {
  const response = await fetch(`${API_BASE_URL}/api/investment/sources/${id}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ active }),
  });
  if (!response.ok) {
    throw new Error(`Failed to update source: ${response.statusText}`);
  }
  return response.json();
}

export interface CronEntry {
  schedule: string;
  command: string;
  source: string;
  user: string | null;
  scheduled_at: string;
}

export interface CronUpcomingResponse {
  timezone: string;
  window_days: number;
  window_start: string;
  window_end: string;
  count: number;
  entries: CronEntry[];
  sources_checked: string[];
  note: string;
}

export async function fetchCronUpcoming(days = 3): Promise<CronUpcomingResponse> {
  const response = await fetch(`${API_BASE_URL}/api/observability/cron/upcoming?days=${days}`);
  if (!response.ok) {
    throw new Error(`Failed to fetch cron schedule: ${response.statusText}`);
  }
  return response.json();
}

export interface SalesPlatformListing {
  id: string;
  item_id: string;
  platform: string;
  status: string;
  title: string | null;
  description: string | null;
  category_suggestion: string | null;
  price_chf: string | null;
  publish_url: string | null;
  published_at: string | null;
  sold_at: string | null;
  archived_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface SalesItemPhoto {
  id: string;
  item_id: string;
  photo_type: string;
  telegram_file_id: string | null;
  local_path: string | null;
  storage_url: string | null;
  caption: string | null;
  is_primary: boolean;
  sort_order: number;
  created_at: string;
}

export interface SalesItem {
  id: string;
  title: string | null;
  brand_model: string | null;
  category: string | null;
  condition: string | null;
  description: string | null;
  internal_notes: string | null;
  target_price_chf: string | null;
  pickup_location: string | null;
  shipping_policy: string | null;
  status: string;
  needs_action_reason: string | null;
  created_from: string | null;
  telegram_chat_id: string | null;
  telegram_message_id: string | null;
  created_at: string;
  updated_at: string;
  photos: SalesItemPhoto[];
  platform_listings: SalesPlatformListing[];
}

export async function fetchSalesItems(params?: {
  status?: string;
  limit?: number;
  offset?: number;
}): Promise<SalesItem[]> {
  const url = new URL(`${API_BASE_URL}/api/marketplace/sales/items`);
  if (params?.status) url.searchParams.append('status', params.status);
  if (params?.limit !== undefined) url.searchParams.append('limit', String(params.limit));
  if (params?.offset !== undefined) url.searchParams.append('offset', String(params.offset));

  const response = await fetch(url.toString());
  if (!response.ok) {
    throw new Error(`Failed to fetch sales items: ${response.statusText}`);
  }
  return response.json();
}

export async function fetchSalesItem(id: string): Promise<SalesItem> {
  const response = await fetch(`${API_BASE_URL}/api/marketplace/sales/items/${id}`);
  if (!response.ok) {
    throw new Error(`Failed to fetch sales item: ${response.statusText}`);
  }
  return response.json();
}

export async function generatePlatformDrafts(id: string): Promise<SalesItem> {
  const response = await fetch(
    `${API_BASE_URL}/api/marketplace/sales/items/${id}/generate-platform-drafts`,
    { method: 'POST' },
  );
  if (!response.ok) {
    const body = await response.json().catch(() => ({ detail: response.statusText }));
    const detail = body?.detail;
    if (detail && typeof detail === 'object' && detail.missing_fields) {
      throw new Error(`Missing fields: ${(detail.missing_fields as string[]).join(', ')}`);
    }
    throw new Error(typeof detail === 'string' ? detail : `HTTP ${response.status}`);
  }
  return response.json();
}

// ── Investment Research Cases ─────────────────────────────────────────────────

export interface ResearchTask {
  id: string;
  research_case_id: string;
  description: string;
  status: string;
  priority: number;
  source: string | null;
  notes: string | null;
  created_at: string;
  resolved_at: string | null;
}

export interface ResearchDocument {
  id: string;
  research_case_id: string | null;
  historical_case_id: string | null;
  doc_type: string | null;
  url: string;
  title: string | null;
  retrieved_at: string | null;
  summary: string | null;
  added_by: string | null;
  created_at: string;
}

export interface ResearchSource {
  id: string;
  research_case_id: string | null;
  historical_case_id: string | null;
  investment_source_id: string | null;
  source_name: string;
  source_url: string | null;
  signal_quality: string;
  notes: string | null;
  created_at: string;
}

export interface ResearchCase {
  id: string;
  situation_id: string | null;
  status: string;
  brief: Record<string, unknown> | null;
  brief_version: string | null;
  playbook_version: string | null;
  model_used: string | null;
  run_id: string | null;
  notes: string | null;
  disclaimer: string;
  investment_readiness: string | null;
  source_origin_name: string | null;
  investment_source_id: string | null;
  intake_method: string | null;
  connector_key: string | null;
  intake_event_id: string | null;
  evidence_level: string | null;
  official_source_status: string | null;
  methodology_status: string | null;
  playbook_used: string | null;
  checklist_used: string | null;
  course_reference: string | null;
  duplicate_status: string | null;
  next_follow_up_at: string | null;
  discarded_reason: string | null;
  created_at: string;
  updated_at: string;
  tasks: ResearchTask[];
  documents: ResearchDocument[];
  sources: ResearchSource[];
}

export interface EvaluationPrepAction {
  label: string;
  reason: string;
  priority: 'high' | 'medium' | 'low';
  manual_only: boolean;
}

export interface EvaluationPrepBucket {
  total: number;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  missing: any[];
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  candidate_found: any[];
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  evidence_found: any[];
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  verified: any[];
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  rejected: any[];
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  human_review_required: any[];
}

export interface EvaluationPrepPackage {
  research_case_id: string;
  case_title: string | null;
  status: string;
  investment_readiness: string | null;
  origin: {
    intake_method: string | null;
    situation_id: string | null;
    source: string;
  };
  readiness: {
    level: 'not_ready' | 'needs_more_evidence' | 'ready_for_manual_evaluation';
    score: number;
    blocking_reasons: string[];
    warnings: string[];
  };
  required_resources: EvaluationPrepBucket;
  checklist: EvaluationPrepBucket;
  source_quality: {
    official_sources_count: number;
    metadata_only_sources_count: number;
    manual_sources_count: number;
    issues: string[];
  };
  evidence_links_summary?: {
    total_links: number;
    sec_links: number;
    manual_links: number;
    research_source_links: number;
    research_document_links: number;
    metadata_only_links: number;
    missing_link_items: string[];
  } | null;
  suggested_next_actions: EvaluationPrepAction[];
  guardrails: string[];
}

export interface IntelligenceScoreComponent {
  key: 'detection' | 'structuring' | 'risk_discipline';
  label: string;
  score: number;
  max_score: number;
  signals: string[];
  gaps: string[];
}

export interface IntelligenceScorePackage {
  research_case_id: string;
  total_score: number;
  grade: 'APPROVABLE' | 'USEFUL_INCOMPLETE' | 'REVIEW_PIPELINE';
  grade_explanation: string;
  components: IntelligenceScoreComponent[];
  evaluation_prep_summary: {
    level: string;
    score: number;
    blocking_reasons: string[];
    warnings: string[];
    required_resources_total: number;
    required_resources_missing: number;
    checklist_total: number;
    checklist_missing: number;
  };
  evidence_links_summary: {
    total_links: number;
    sec_links: number;
    manual_links: number;
    research_source_links: number;
    research_document_links: number;
    metadata_only_links: number;
    missing_link_items: string[];
  };
  strengths: string[];
  warnings: string[];
  suggested_next_actions: string[];
  guardrails: string[];
}

export type OperationalViewLabel = 'candidate' | 'watchlist' | 'reject' | 'insufficient_information';
export type OperationalViewConfidence = 'low' | 'medium' | 'high';

export interface OperationalViewPackage {
  research_case_id: string;
  operational_view: OperationalViewLabel;
  confidence: OperationalViewConfidence;
  rationale: string[];
  blockers: string[];
  what_would_change_view: string[];
  next_manual_actions: string[];
  guardrails: string[];
  not_investment_advice: boolean;
  final_decision_by_dani: boolean;
}

export interface ResearchCasesResponse {
  count: number;
  research_cases: ResearchCase[];
}

export async function fetchResearchCases(params?: {
  status?: string;
  investment_readiness?: string;
  situation_id?: string;
}): Promise<ResearchCasesResponse> {
  const url = new URL(`${API_BASE_URL}/api/investment/research-cases`);
  if (params?.status) url.searchParams.append('status', params.status);
  if (params?.investment_readiness) url.searchParams.append('investment_readiness', params.investment_readiness);
  if (params?.situation_id) url.searchParams.append('situation_id', params.situation_id);
  const response = await fetch(url.toString());
  if (!response.ok) throw new Error(`Failed to fetch research cases: ${response.statusText}`);
  return response.json();
}

export async function fetchResearchCase(id: string): Promise<ResearchCase> {
  const response = await fetch(`${API_BASE_URL}/api/investment/research-cases/${id}`);
  if (!response.ok) throw new Error(`Failed to fetch research case: ${response.statusText}`);
  return response.json();
}

export async function fetchResearchCaseEvaluationPrep(id: string): Promise<EvaluationPrepPackage> {
  const response = await fetch(`${API_BASE_URL}/api/investment/research-cases/${id}/evaluation-prep`);
  if (!response.ok) throw new Error(`Failed to fetch evaluation preparation: ${response.statusText}`);
  return response.json();
}

export async function fetchResearchCaseEvidenceLinks(id: string): Promise<ResearchCaseEvidenceLinksPackage> {
  const response = await fetch(`${API_BASE_URL}/api/investment/research-cases/${id}/evidence-links`);
  if (!response.ok) throw new Error(`Failed to fetch research traceability: ${response.statusText}`);
  return response.json();
}

export async function fetchResearchCaseIntelligenceScore(id: string): Promise<IntelligenceScorePackage> {
  const response = await fetch(`${API_BASE_URL}/api/investment/research-cases/${id}/intelligence-score`);
  if (!response.ok) throw new Error(`Failed to fetch intelligence score: ${response.statusText}`);
  return response.json();
}

export async function fetchResearchCaseOperationalView(id: string): Promise<OperationalViewPackage> {
  const response = await fetch(`${API_BASE_URL}/api/investment/research-cases/${id}/operational-view`);
  if (!response.ok) throw new Error(`Failed to fetch operational view: ${response.statusText}`);
  return response.json();
}

export async function fetchResearchCaseDocumentationGuide(id: string): Promise<CaseDocumentationGuidePackage> {
  const response = await fetch(`${API_BASE_URL}/api/investment/research-cases/${id}/documentation-guide`);
  if (!response.ok) throw new Error(`Failed to fetch research case documentation guide: ${response.statusText}`);
  return response.json();
}

export async function fetchResearchCaseOfficialSourceFinder(id: string): Promise<OfficialSourceFinderPackage> {
  const response = await fetch(`${API_BASE_URL}/api/investment/research-cases/${id}/official-source-finder`);
  if (!response.ok) throw new Error(`Failed to fetch research case official source finder: ${response.statusText}`);
  return response.json();
}

export async function fetchResearchCaseHistoricalAnalogues(id: string): Promise<HistoricalAnaloguesPackage> {
  const response = await fetch(`${API_BASE_URL}/api/investment/research-cases/${id}/historical-analogues`);
  if (!response.ok) throw new Error(`Failed to fetch research case historical analogues: ${response.statusText}`);
  return response.json();
}

export async function fetchResearchCaseCompletionWorkbench(id: string): Promise<CaseCompletionPackage> {
  const response = await fetch(`${API_BASE_URL}/api/investment/research-cases/${id}/completion-workbench`);
  if (!response.ok) throw new Error(`Failed to fetch research case completion workbench: ${response.statusText}`);
  return response.json();
}

export async function fetchResearchCaseSecDocumentAcquisitionPreview(id: string): Promise<SecDocumentAcquisitionPackage> {
  const response = await fetch(`${API_BASE_URL}/api/investment/research-cases/${id}/sec-document-acquisition-preview`);
  if (!response.ok) throw new Error(`Failed to fetch research case SEC document acquisition preview: ${response.statusText}`);
  return response.json();
}

export async function acquireResearchCaseSecDocuments(id: string): Promise<SecDocumentAcquisitionPackage> {
  const response = await fetch(`${API_BASE_URL}/api/investment/research-cases/${id}/sec-document-acquisition`, { method: 'POST' });
  if (!response.ok) throw new Error(`Failed to acquire research case SEC documents: ${response.statusText}`);
  return response.json();
}

export async function fetchResearchCaseActivityTimeline(id: string): Promise<CaseActivityTimelinePackage> {
  const response = await fetch(`${API_BASE_URL}/api/investment/research-cases/${id}/activity-timeline`);
  if (!response.ok) throw new Error(`Failed to fetch research case activity timeline: ${response.statusText}`);
  return response.json();
}

export async function createResearchCaseFromSituation(
  situationId: string,
  opts?: { notes?: string; investment_readiness?: string },
): Promise<ResearchCase> {
  const url = new URL(`${API_BASE_URL}/api/investment/research-cases/from-situation/${situationId}`);
  if (opts?.notes) url.searchParams.append('notes', opts.notes);
  if (opts?.investment_readiness) url.searchParams.append('investment_readiness', opts.investment_readiness);
  const response = await fetch(url.toString(), { method: 'POST' });
  if (!response.ok) {
    const body = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(typeof body?.detail === 'string' ? body.detail : `HTTP ${response.status}`);
  }
  return response.json();
}

export async function updateResearchCase(
  id: string,
  payload: {
    status?: string;
    notes?: string;
    investment_readiness?: string;
    brief?: Record<string, unknown>;
    brief_version?: string;
    playbook_version?: string;
    model_used?: string;
  },
): Promise<ResearchCase> {
  const response = await fetch(`${API_BASE_URL}/api/investment/research-cases/${id}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    const body = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(typeof body?.detail === 'string' ? body.detail : `HTTP ${response.status}`);
  }
  return response.json();
}

export async function addResearchTask(
  researchCaseId: string,
  payload: { description: string; priority?: number; notes?: string },
): Promise<ResearchTask> {
  const response = await fetch(`${API_BASE_URL}/api/investment/research-cases/${researchCaseId}/tasks`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    const body = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(typeof body?.detail === 'string' ? body.detail : `HTTP ${response.status}`);
  }
  return response.json();
}

export async function updateResearchTask(
  taskId: string,
  payload: { status?: string; notes?: string },
): Promise<ResearchTask> {
  const response = await fetch(`${API_BASE_URL}/api/investment/research-tasks/${taskId}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    const body = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(typeof body?.detail === 'string' ? body.detail : `HTTP ${response.status}`);
  }
  return response.json();
}

export async function addResearchDocument(
  researchCaseId: string,
  payload: { url: string; title?: string; doc_type?: string; summary?: string; added_by?: string },
): Promise<ResearchDocument> {
  const response = await fetch(`${API_BASE_URL}/api/investment/research-cases/${researchCaseId}/documents`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    const body = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(typeof body?.detail === 'string' ? body.detail : `HTTP ${response.status}`);
  }
  return response.json();
}

export async function addResearchSource(
  researchCaseId: string,
  payload: { source_name: string; source_url?: string; signal_quality: string; notes?: string },
): Promise<ResearchSource> {
  const response = await fetch(`${API_BASE_URL}/api/investment/research-cases/${researchCaseId}/sources`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    const body = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(typeof body?.detail === 'string' ? body.detail : `HTTP ${response.status}`);
  }
  return response.json();
}

export interface BriefPreviewSections {
  executive_summary: string;
  situation_type: string;
  why_interesting: string;
  methodology_reference: string;
  company_context: string;
  board_management: string;
  key_documents: string;
  timeline: string;
  risk_analysis: string;
  verify_before_investing: string;
  missing_information: string;
  source_intelligence: string;
  investment_readiness_note: string;
  public_summary_draft: string;
}

export interface BriefPreviewResult {
  saved_to_db: boolean;
  preview: BriefPreviewSections;
  source_context_used: string[];
  warnings: string[];
  disclaimer: string;
  usage: {
    provider?: string;
    model?: string;
    input_tokens?: number;
    output_tokens?: number;
  };
}

export async function generateBriefPreview(researchCaseId: string): Promise<BriefPreviewResult> {
  const response = await fetch(
    `${API_BASE_URL}/api/investment/research-cases/${researchCaseId}/generate-brief-preview`,
    { method: 'POST' },
  );
  if (!response.ok) {
    const body = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(typeof body?.detail === 'string' ? body.detail : `HTTP ${response.status}`);
  }
  return response.json();
}

export interface QualityChecklist {
  brief_completeness: boolean;
  missing_information_noted: boolean;
  key_risks_identified: boolean;
  documents_attached: boolean;
  tasks_open: boolean;
  sources_recorded: boolean;
  disclaimer_present: boolean;
  no_buy_sell_language: boolean;
  readiness_label_valid: boolean;
}

export interface QualityPreviewResult {
  saved_to_db: boolean;
  quality_checklist: QualityChecklist;
  suggested_status: string;
  suggested_readiness: string;
  rationale: string;
  warnings: string[];
  disclaimer: string;
  usage: {
    provider?: string;
    model?: string;
    input_tokens?: number;
    output_tokens?: number;
  };
}

export async function generateQualityPreview(researchCaseId: string): Promise<QualityPreviewResult> {
  const response = await fetch(
    `${API_BASE_URL}/api/investment/research-cases/${researchCaseId}/quality-preview`,
    { method: 'POST' },
  );
  if (!response.ok) {
    const body = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(typeof body?.detail === 'string' ? body.detail : `HTTP ${response.status}`);
  }
  return response.json();
}

export async function updateResearchDocument(
  researchCaseId: string,
  documentId: string,
  payload: { title?: string; doc_type?: string; summary?: string },
): Promise<ResearchDocument> {
  const response = await fetch(
    `${API_BASE_URL}/api/investment/research-cases/${researchCaseId}/documents/${documentId}`,
    {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    },
  );
  if (!response.ok) {
    const body = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(typeof body?.detail === 'string' ? body.detail : `HTTP ${response.status}`);
  }
  return response.json();
}

export async function updateResearchSource(
  researchCaseId: string,
  sourceId: string,
  payload: { signal_quality?: string; notes?: string },
): Promise<ResearchSource> {
  const response = await fetch(
    `${API_BASE_URL}/api/investment/research-cases/${researchCaseId}/sources/${sourceId}`,
    {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    },
  );
  if (!response.ok) {
    const body = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(typeof body?.detail === 'string' ? body.detail : `HTTP ${response.status}`);
  }
  return response.json();
}

export interface DocumentAnalysisPreviewResult {
  saved_to_db: false;
  document_id: string;
  analysis: {
    summary: string;
    key_points: string[];
    risks: string[];
    timeline_items: string[];
    missing_information: string;
    suggested_research_tasks: string[];
    source_usefulness: string;
  };
  warnings: string[];
  disclaimer: string;
  usage: {
    provider?: string;
    model?: string;
    input_tokens?: number;
    output_tokens?: number;
  };
}

export async function generateDocumentAnalysisPreview(documentId: string): Promise<DocumentAnalysisPreviewResult> {
  const response = await fetch(
    `${API_BASE_URL}/api/investment/research-documents/${documentId}/analysis-preview`,
    { method: 'POST' },
  );
  if (!response.ok) {
    const body = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(typeof body?.detail === 'string' ? body.detail : `HTTP ${response.status}`);
  }
  return response.json();
}

export interface SourceScoreItem {
  source_id: string;
  source_name: string;
  signal_quality: string;
  usefulness_reason: string;
  suggested_follow_up: string;
}

export interface SourceIntelligenceSuggestion {
  action: 'add' | 'update_priority' | 'deactivate';
  source_name: string;
  source_type: string;
  reason: string;
  evidence_from_case: string;
  confidence: 'high' | 'medium' | 'low';
  manual_review_required: true;
}

export interface SourceIntelligencePreviewResult {
  saved_to_db: false;
  research_case_id: string;
  source_scores: SourceScoreItem[];
  suggestions: SourceIntelligenceSuggestion[];
  warnings: string[];
  disclaimer: string;
  usage: {
    provider?: string;
    model?: string;
    input_tokens?: number;
    output_tokens?: number;
  };
}

export async function generateSourceIntelligencePreview(researchCaseId: string): Promise<SourceIntelligencePreviewResult> {
  const response = await fetch(
    `${API_BASE_URL}/api/investment/research-cases/${researchCaseId}/source-intelligence-preview`,
    { method: 'POST' },
  );
  if (!response.ok) {
    const body = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(typeof body?.detail === 'string' ? body.detail : `HTTP ${response.status}`);
  }
  return response.json();
}

// ── Phase 4A — Source Intelligence Approval Queue ─────────────────────────────

export interface SourceIntelligenceSuggestionRecord {
  id: string;
  research_case_id: string | null;
  historical_case_id: string | null;
  action: string;
  proposed_name: string | null;
  proposed_source_type: string | null;
  rationale: string;
  status: 'proposed' | 'approved' | 'rejected';
  created_at: string;
  reviewed_at: string | null;
}

export interface SuggestionsQueueResponse {
  count: number;
  suggestions: SourceIntelligenceSuggestionRecord[];
}

export async function saveSourceIntelligenceSuggestions(
  researchCaseId: string,
  suggestions: SourceIntelligenceSuggestion[],
): Promise<SourceIntelligenceSuggestionRecord[]> {
  const response = await fetch(
    `${API_BASE_URL}/api/investment/research-cases/${researchCaseId}/source-intelligence-suggestions`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ suggestions }),
    },
  );
  if (!response.ok) {
    const body = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(typeof body?.detail === 'string' ? body.detail : `HTTP ${response.status}`);
  }
  return response.json();
}

export async function fetchSourceIntelligenceSuggestions(params?: {
  research_case_id?: string;
  historical_case_id?: string;
  status?: string;
  action?: string;
}): Promise<SuggestionsQueueResponse> {
  const url = new URL(`${API_BASE_URL}/api/investment/source-intelligence-suggestions`);
  if (params?.research_case_id) url.searchParams.append('research_case_id', params.research_case_id);
  if (params?.historical_case_id) url.searchParams.append('historical_case_id', params.historical_case_id);
  if (params?.status) url.searchParams.append('status', params.status);
  if (params?.action) url.searchParams.append('action', params.action);
  const response = await fetch(url.toString());
  if (!response.ok) throw new Error(`Failed to fetch suggestions: ${response.statusText}`);
  return response.json();
}

export async function reviewSourceIntelligenceSuggestion(
  suggestionId: string,
  status: 'approved' | 'rejected',
): Promise<SourceIntelligenceSuggestionRecord> {
  const response = await fetch(
    `${API_BASE_URL}/api/investment/source-intelligence-suggestions/${suggestionId}`,
    {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status }),
    },
  );
  if (!response.ok) {
    const body = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(typeof body?.detail === 'string' ? body.detail : `HTTP ${response.status}`);
  }
  return response.json();
}

// ── Phase 4B — Historical Cases ───────────────────────────────────────────────

export interface HistoricalCase {
  id: string;
  company_name: string;
  situation_type: string;
  event_date_approx: string | null;
  seed_notes: string | null;
  course_chapter_ref: number | null;
  reconstruction: Record<string, unknown> | null;
  status: string;
  linked_situation_id: string | null;
  disclaimer: string;
  created_at: string;
  updated_at: string;
}

export interface HistoricalCasesResponse {
  count: number;
  historical_cases: HistoricalCase[];
}

export async function fetchHistoricalCases(params?: {
  status?: string;
  situation_type?: string;
}): Promise<HistoricalCasesResponse> {
  const url = new URL(`${API_BASE_URL}/api/investment/historical-cases`);
  if (params?.status) url.searchParams.append('status', params.status);
  if (params?.situation_type) url.searchParams.append('situation_type', params.situation_type);
  const response = await fetch(url.toString());
  if (!response.ok) throw new Error(`Failed to fetch historical cases: ${response.statusText}`);
  return response.json();
}

export async function fetchHistoricalCase(id: string): Promise<HistoricalCase> {
  const response = await fetch(`${API_BASE_URL}/api/investment/historical-cases/${id}`);
  if (!response.ok) throw new Error(`Failed to fetch historical case: ${response.statusText}`);
  return response.json();
}

export async function createHistoricalCase(payload: {
  company_name: string;
  situation_type: string;
  event_date_approx?: string;
  seed_notes?: string;
  course_chapter_ref?: number;
}): Promise<HistoricalCase> {
  const response = await fetch(`${API_BASE_URL}/api/investment/historical-cases`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    const body = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(typeof body?.detail === 'string' ? body.detail : `HTTP ${response.status}`);
  }
  return response.json();
}

export async function updateHistoricalCase(
  id: string,
  payload: {
    status?: string;
    seed_notes?: string;
    event_date_approx?: string;
    course_chapter_ref?: number;
    reconstruction?: Record<string, unknown>;
  },
): Promise<HistoricalCase> {
  const response = await fetch(`${API_BASE_URL}/api/investment/historical-cases/${id}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    const body = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(typeof body?.detail === 'string' ? body.detail : `HTTP ${response.status}`);
  }
  return response.json();
}

// ── Phase 4C — Historical Case Source Intelligence Preview ───────────────────

export interface HistoricalCaseSourceIntelligencePreviewResult {
  saved_to_db: false;
  historical_case_id: string;
  source_scores: SourceScoreItem[];
  suggestions: SourceIntelligenceSuggestion[];
  warnings: string[];
  disclaimer: string;
  usage: {
    provider?: string;
    model?: string;
    input_tokens?: number;
    output_tokens?: number;
  };
}

export async function generateHistoricalCaseSourceIntelligencePreview(
  historicalCaseId: string,
): Promise<HistoricalCaseSourceIntelligencePreviewResult> {
  const response = await fetch(
    `${API_BASE_URL}/api/investment/historical-cases/${historicalCaseId}/source-intelligence-preview`,
    { method: 'POST' },
  );
  if (!response.ok) {
    const body = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(typeof body?.detail === 'string' ? body.detail : `HTTP ${response.status}`);
  }
  return response.json();
}

export async function saveHistoricalCaseSourceIntelligenceSuggestions(
  historicalCaseId: string,
  suggestions: SourceIntelligenceSuggestion[],
): Promise<SourceIntelligenceSuggestionRecord[]> {
  const response = await fetch(
    `${API_BASE_URL}/api/investment/historical-cases/${historicalCaseId}/source-intelligence-suggestions`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ suggestions }),
    },
  );
  if (!response.ok) {
    const body = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(typeof body?.detail === 'string' ? body.detail : `HTTP ${response.status}`);
  }
  return response.json();
}

// ── Phase 5 — Public Article Drafts ──────────────────────────────────────────

export interface PublicArticleDraft {
  id: string;
  research_case_id: string;
  status: 'draft' | 'in_review' | 'approved' | 'archived';
  title: string | null;
  content: string;
  readiness_label: string;
  disclaimer: string;
  disclaimer_present: boolean;
  buy_sell_language_check: boolean;
  tags: Record<string, unknown> | null;
  created_at: string;
  approved_at: string | null;
  published_at: string | null;
  validation_warnings: string[];
}

export interface PublicDraftsResponse {
  count: number;
  public_drafts: PublicArticleDraft[];
}

export async function createPublicDraftFromResearchCase(researchCaseId: string): Promise<PublicArticleDraft> {
  const response = await fetch(
    `${API_BASE_URL}/api/investment/research-cases/${researchCaseId}/public-draft`,
    { method: 'POST' },
  );
  if (!response.ok) {
    const body = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(typeof body?.detail === 'string' ? body.detail : `HTTP ${response.status}`);
  }
  return response.json();
}

export async function fetchPublicDrafts(params?: {
  status?: string;
  research_case_id?: string;
}): Promise<PublicDraftsResponse> {
  const url = new URL(`${API_BASE_URL}/api/investment/public-drafts`);
  if (params?.status) url.searchParams.append('status', params.status);
  if (params?.research_case_id) url.searchParams.append('research_case_id', params.research_case_id);
  const response = await fetch(url.toString());
  if (!response.ok) throw new Error(`Failed to fetch public drafts: ${response.statusText}`);
  return response.json();
}

export async function fetchPublicDraft(id: string): Promise<PublicArticleDraft> {
  const response = await fetch(`${API_BASE_URL}/api/investment/public-drafts/${id}`);
  if (!response.ok) throw new Error(`Failed to fetch public draft: ${response.statusText}`);
  return response.json();
}

export async function updatePublicDraft(
  id: string,
  payload: {
    status?: 'draft' | 'in_review' | 'approved' | 'archived';
    title?: string;
    content?: string;
    readiness_label?: string;
    disclaimer?: string;
    tags?: Record<string, unknown>;
  },
): Promise<PublicArticleDraft> {
  const response = await fetch(`${API_BASE_URL}/api/investment/public-drafts/${id}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    const body = await response.json().catch(() => ({ detail: response.statusText }));
    if (body?.detail?.validation_warnings) {
      throw new Error((body.detail.validation_warnings as string[]).join(' '));
    }
    throw new Error(typeof body?.detail === 'string' ? body.detail : `HTTP ${response.status}`);
  }
  return response.json();
}

export async function fetchPublicDraftMarkdown(id: string): Promise<{ markdown: string }> {
  const response = await fetch(`${API_BASE_URL}/api/investment/public-drafts/${id}/markdown`);
  if (!response.ok) throw new Error(`Failed to fetch public draft markdown: ${response.statusText}`);
  return response.json();
}

// ── Agent Ops ────────────────────────────────────────────────────────────────

export interface AgentOpsRoom {
  id: string;
  key: string;
  name: string;
  description: string | null;
  status: string;
  display_order: number;
  created_at?: string | null;
  updated_at?: string | null;
}

export interface AgentOpsAgent {
  id: string;
  key: string;
  name: string;
  room_id?: string;
  room_key: string | null;
  role: string | null;
  status: string;
  implementation_status: string;
  autonomy_level: string;
  guardrails: string[] | Record<string, unknown> | string | null;
  created_at?: string | null;
  updated_at?: string | null;
}

export interface AgentOpsActivity {
  id: string;
  agent_id: string | null;
  agent_key: string | null;
  room_id: string | null;
  room_key: string | null;
  activity_type: string;
  title: string;
  summary: string | null;
  severity: string;
  status: string;
  related_entity_type: string | null;
  related_entity_id: string | null;
  metadata?: Record<string, unknown> | null;
  created_at: string | null;
}

export interface AgentOpsDiagnostic {
  id: string;
  agent_id: string | null;
  agent_key: string | null;
  room_id: string | null;
  room_key: string | null;
  severity: string;
  diagnostic_type: string;
  title: string;
  description: string | null;
  evidence?: Record<string, unknown> | null;
  related_entity_type: string | null;
  related_entity_id: string | null;
  created_at: string | null;
}

export type AgentOpsProposalStatus =
  | 'proposed'
  | 'accepted'
  | 'rejected'
  | 'deferred'
  | 'implemented'
  | 'archived';

export interface AgentOpsProposal {
  id: string;
  source_diagnostic_id: string | null;
  agent_id: string | null;
  agent_key: string | null;
  room_id: string | null;
  room_key: string | null;
  title: string;
  problem_statement: string;
  proposed_change: string;
  expected_benefit: string | null;
  risk_level: string;
  status: AgentOpsProposalStatus;
  reviewer_note: string | null;
  reviewed_by: string | null;
  reviewed_at: string | null;
  created_at: string | null;
  updated_at: string | null;
}

export interface AgentOpsRoomsResponse {
  count: number;
  rooms: AgentOpsRoom[];
}

export interface AgentOpsAgentsResponse {
  count: number;
  agents: AgentOpsAgent[];
}

export interface AgentOpsActivityResponse {
  count: number;
  items: AgentOpsActivity[];
}

export interface AgentOpsDiagnosticsResponse {
  count: number;
  items: AgentOpsDiagnostic[];
}

export interface AgentOpsProposalsResponse {
  count: number;
  items: AgentOpsProposal[];
}

type AgentOpsListParams = {
  room_key?: string;
  agent_key?: string;
  severity?: string;
  status?: string;
  diagnostic_type?: string;
  risk_level?: string;
  related_entity_type?: string;
  related_entity_id?: string;
  limit?: number;
};

function agentOpsUrl(path: string, params?: Record<string, string | number | undefined>) {
  const url = new URL(`${API_BASE_URL}/api/agent-ops${path}`);
  for (const [key, value] of Object.entries(params ?? {})) {
    if (value !== undefined && value !== '') url.searchParams.append(key, String(value));
  }
  return url;
}

async function parseAgentOpsError(response: Response, fallback: string): Promise<Error> {
  const body = await response.json().catch(() => null);
  const detail = body?.detail;
  if (typeof detail === 'string') return new Error(detail);
  return new Error(`${fallback}: HTTP ${response.status}`);
}

export async function fetchAgentOpsRooms(params?: { status?: string }): Promise<AgentOpsRoomsResponse> {
  const response = await fetch(agentOpsUrl('/rooms', params).toString());
  if (!response.ok) throw await parseAgentOpsError(response, 'Failed to fetch Agent Ops rooms');
  return response.json();
}

export async function fetchAgentOpsAgents(params?: {
  room_key?: string;
  status?: string;
  implementation_status?: string;
}): Promise<AgentOpsAgentsResponse> {
  const response = await fetch(agentOpsUrl('/agents', params).toString());
  if (!response.ok) throw await parseAgentOpsError(response, 'Failed to fetch Agent Ops agents');
  return response.json();
}

export async function fetchAgentOpsActivity(params?: AgentOpsListParams): Promise<AgentOpsActivityResponse> {
  const response = await fetch(agentOpsUrl('/activity', params).toString());
  if (!response.ok) throw await parseAgentOpsError(response, 'Failed to fetch Agent Ops activity');
  return response.json();
}

export async function fetchAgentOpsDiagnostics(params?: AgentOpsListParams): Promise<AgentOpsDiagnosticsResponse> {
  const response = await fetch(agentOpsUrl('/diagnostics', params).toString());
  if (!response.ok) throw await parseAgentOpsError(response, 'Failed to fetch Agent Ops diagnostics');
  return response.json();
}

export async function fetchAgentOpsProposals(params?: {
  status?: string;
  risk_level?: string;
  room_key?: string;
  agent_key?: string;
  limit?: number;
}): Promise<AgentOpsProposalsResponse> {
  const response = await fetch(agentOpsUrl('/proposals', params).toString());
  if (!response.ok) throw await parseAgentOpsError(response, 'Failed to fetch Agent Ops proposals');
  return response.json();
}

export async function updateAgentOpsProposal(
  id: string,
  payload: { status: AgentOpsProposalStatus; reviewer_note?: string },
): Promise<{ proposal: AgentOpsProposal }> {
  const response = await fetch(`${API_BASE_URL}/api/agent-ops/proposals/${id}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      status: payload.status,
      reviewer_note: payload.reviewer_note,
    }),
  });
  if (!response.ok) throw await parseAgentOpsError(response, 'Failed to update Agent Ops proposal');
  return response.json();
}
