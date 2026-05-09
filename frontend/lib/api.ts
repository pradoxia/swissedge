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
  evaluation?: any;
  notes?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
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

export interface V2PreviewResult {
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
  guardrails: string[] | Record<string, unknown> | null;
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
