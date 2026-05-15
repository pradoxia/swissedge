'use client';

import { useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import {
  fetchAgentOpsActivity,
  fetchAgentOpsAgents,
  fetchAgentOpsDiagnostics,
  fetchAgentOpsProposals,
  fetchAgentOpsRooms,
  fetchDaniWeberMetrics,
  fetchExecutiveReview,
  fetchFontanaReport,
  updateAgentOpsProposal,
  type AgentOpsActivity,
  type AgentOpsAgent,
  type AgentOpsDiagnostic,
  type AgentOpsProposal,
  type AgentOpsProposalStatus,
  type AgentOpsRoom,
  type DaniWeberMetrics,
  type ExecutiveReviewPackage,
  type FontanaDiagnosticReport,
} from '@/lib/api';

const SECTIONS = [
  ['executive-office', 'Executive Office'],
  ['executive-review', 'Executive Review'],
  ['executive-proposals', 'Improvement Proposals'],
  ['rooms', 'Rooms'],
  ['agents', 'Agents'],
  ['activity', 'Activity Feed'],
  ['diagnostics', 'Diagnostics'],
  ['proposals', 'Learning Proposals'],
  ['scoreboard', 'Scoreboard'],
  ['fontana', 'Fontana Reports'],
] as const;

const FONTANA_SECTIONS = [
  'Current State',
  'Recently Completed',
  'Active Risks',
  'Architectural Concerns',
  'Agent Diagnostics',
  'Proposed Improvements',
  'Manual Next Steps',
  'Deferred Decisions',
  'Things We Should NOT Touch Yet',
];

const TOP_NAV_LINKS = [
  ['/', 'Mission Control'],
  ['/investment/research', 'Research Cases'],
  ['/investment/research-inbox', 'Research Inbox'],
  ['/investment/intelligence', 'Intelligence KPIs'],
  ['/investment/evaluations', 'Evaluations'],
  ['/investment/internal-audit', 'Internal Audit'],
  ['/investment/radar-status', 'Radar Status'],
  ['/investment/sources', 'Sources'],
] as const;

const ROOM_CHAINS: Record<string, string[]> = {
  radar_room: ['EDGAR Scout', 'Router Analyst', 'Signal Filter', 'Quality Sentinel', 'Fontana'],
  evidence_lab: ['Resource Scout', 'Official Source Finder', 'Pattern Analyst', 'Evidence Mapper', 'Missing Evidence Hunter', 'Quality Sentinel', 'Playbook Scribe'],
  research_desk: ['Case Builder', 'Case Completion Coach', 'Missing Evidence Hunter', 'Intelligence Scorer', 'Fontana'],
  quality_court: ['Quality Sentinel', 'Risk Discipline Checker', 'Human Review Gate', 'Fontana'],
  playbook_workshop: ['Playbook Scribe', 'Coverage Analyst', 'Drift Watcher', 'Fontana'],
  agent_ops: ['Registry', 'Activity Logger', 'Diagnostics Reader', 'Fontana'],
};

const AGENT_CALLSIGNS: Record<string, string> = {
  edgar: 'Signal scout',
  router: 'Playbook router',
  quality: 'Guardrail judge',
  resource: 'Evidence finder',
  official: 'SEC locator',
  pattern: 'Analogue mapper',
  evidence: 'Traceability mapper',
  case: 'Case assembler',
  completion: 'Completion coach',
  evaluation: 'Manual prep officer',
  intelligence: 'Scorekeeper',
  fontana: 'CTO observer',
};

type AgentIdentity = {
  name: string;
  keyHint: string;
  room: string;
  title: string;
  mission: string;
  watches: string[];
  outputs: string[];
  currentMode: string;
  futureMode: string;
  scheduler: string;
};

const AGENT_IDENTITIES: AgentIdentity[] = [
  {
    name: 'Edgar Scout',
    keyHint: 'edgar',
    room: 'radar_room',
    title: 'Official signal scout',
    mission: 'Watches stored SEC EDGAR detection metadata and keeps the official-source trail visible.',
    watches: ['SEC EDGAR detection metadata', 'filing type', 'detected company context'],
    outputs: ['candidate SpecialSituations', 'detection context', 'stored SEC metadata'],
    currentMode: 'observer-only',
    futureMode: 'approved official-source checks only',
    scheduler: 'existing SEC intake separate; no Agent Ops scheduler',
  },
  {
    name: 'Router Analyst',
    keyHint: 'router',
    room: 'radar_room',
    title: 'Playbook routing analyst',
    mission: 'Checks situation type, SEC form, and playbook routing so cases land in the right manual workflow.',
    watches: ['situation type', 'SEC form', 'selected playbook'],
    outputs: ['routing confidence', 'required review flags', 'playbook fit notes'],
    currentMode: 'observer-only',
    futureMode: 'manual-approved routing review',
    scheduler: 'disabled in this sprint',
  },
  {
    name: 'Resource Scout',
    keyHint: 'resource',
    room: 'evidence_lab',
    title: 'Known-resource finder',
    mission: 'Creates known resource candidates and manual search suggestions from stored metadata.',
    watches: ['SEC filing links', 'resource candidates', 'stored search suggestions'],
    outputs: ['candidate links', 'manual search ideas', 'resource status hints'],
    currentMode: 'manual-trigger',
    futureMode: 'frequent checks only after approval',
    scheduler: 'disabled in this sprint',
  },
  {
    name: 'Official Source Finder',
    keyHint: 'official',
    room: 'evidence_lab',
    title: 'SEC filing locator',
    mission: 'Builds manual official-source search plans from stored SEC metadata, workspace gaps, and resource candidates.',
    watches: ['stored SEC filing URL', 'CIK', 'accession number', 'required resources', 'checklist gaps', 'search suggestions'],
    outputs: ['manual locator steps', 'copyable official-source queries', 'missing document targets'],
    currentMode: 'manual / observer-only',
    futureMode: 'approved official-source checks may run in a future sprint',
    scheduler: 'disabled in this sprint',
  },
  {
    name: 'Pattern Analyst',
    keyHint: 'pattern',
    room: 'evidence_lab',
    title: 'Historical analogue mapper',
    mission: 'Maps live cases to historical examples and sanitized course/playbook patterns for manual comparison.',
    watches: ['situation type', 'filing type', 'selected playbook', 'historical cases', 'checklist gaps'],
    outputs: ['matched patterns', 'historical analogues', 'manual comparison checklist'],
    currentMode: 'manual / observer-only',
    futureMode: 'expanded historical comparison after approval',
    scheduler: 'disabled in this sprint',
  },
  {
    name: 'Evidence Mapper',
    keyHint: 'evidence',
    room: 'evidence_lab',
    title: 'Traceability mapper',
    mission: 'Connects resource candidates to required resources and checklist items.',
    watches: ['candidate links', 'required resources', 'checklist evidence refs'],
    outputs: ['evidence mapping status', 'traceability links', 'metadata-only source map'],
    currentMode: 'manual-review',
    futureMode: 'assistive mapping after review',
    scheduler: 'disabled in this sprint',
  },
  {
    name: 'Missing Evidence Hunter',
    keyHint: 'missing',
    room: 'evidence_lab',
    title: 'Case research agent',
    mission: 'Tracks missing required resources and checklist gaps, then suggests the next manual research steps.',
    watches: ['missing required resources', 'missing checklist evidence', 'candidate_found resources', 'rejected/noisy sources', 'missing SEC filing URL', 'low documentation quality', 'low Intelligence Score'],
    outputs: ['missing evidence list', 'manual search plan', 'documentation gaps', 'suggested next actions'],
    currentMode: 'manual / observer-only',
    futureMode: 'frequent missing-evidence checks after explicit approval',
    scheduler: 'disabled in this sprint',
  },
  {
    name: 'Case Completion Coach',
    keyHint: 'completion',
    room: 'research_desk',
    title: 'Manual completion guide',
    mission: 'Turns documentation, evidence, and score gaps into manual next steps for case completion.',
    watches: ['missing required resources', 'candidate sources', 'checklist gaps', 'Intelligence Score gaps', 'review readiness'],
    outputs: ['completion level', 'blocking items', 'manual next actions', 'score improvement plan'],
    currentMode: 'manual / observer-only',
    futureMode: 'guided workflow agent after approval',
    scheduler: 'disabled in this sprint',
  },
  {
    name: 'Quality Sentinel',
    keyHint: 'quality',
    room: 'quality_court',
    title: 'Guardrail judge',
    mission: 'Finds weak traceability, missing evidence, unsafe assumptions, and manual-review needs.',
    watches: ['documentation gaps', 'diagnostics', 'manual review flags'],
    outputs: ['quality warnings', 'risk discipline flags', 'manual review requirements'],
    currentMode: 'observer-only',
    futureMode: 'approved diagnostics only',
    scheduler: 'disabled in this sprint',
  },
  {
    name: 'Intelligence Scorer',
    keyHint: 'intelligence',
    room: 'research_desk',
    title: 'Preparation scorekeeper',
    mission: 'Measures preparation quality, structuring, and risk discipline from stored case metadata.',
    watches: ['Evaluation Preparation', 'Evidence Links', 'documentation quality'],
    outputs: ['Intelligence Score', 'risk flags', 'preparation components'],
    currentMode: 'read-only derived',
    futureMode: 'manual-approved score refresh',
    scheduler: 'disabled in this sprint',
  },
  {
    name: 'Playbook Scribe',
    keyHint: 'playbook',
    room: 'playbook_workshop',
    title: 'Methodology coverage keeper',
    mission: 'Tracks playbook coverage, checklist completeness, and methodology gaps.',
    watches: ['playbook template', 'checklist completion', 'coverage drift'],
    outputs: ['playbook coverage notes', 'methodology gap list', 'template hygiene signals'],
    currentMode: 'observer-only',
    futureMode: 'manual-approved playbook hygiene',
    scheduler: 'disabled in this sprint',
  },
  {
    name: 'Fontana',
    keyHint: 'fontana',
    room: 'agent_ops',
    title: 'CTO / Project Governor',
    mission: 'Summarizes project diagnostics, operational status, and future sprint options without runtime authority.',
    watches: ['Agent Ops diagnostics', 'project state docs', 'review posture'],
    outputs: ['project diagnostics', 'next sprint options', 'operational status'],
    currentMode: 'documented observer',
    futureMode: 'reporting only after approval',
    scheduler: 'disabled in this sprint',
  },
];

const AVATAR_COLORS = [
  'border-emerald-200 bg-emerald-50 text-emerald-800',
  'border-blue-200 bg-blue-50 text-blue-800',
  'border-cyan-200 bg-cyan-50 text-cyan-800',
  'border-amber-200 bg-amber-50 text-amber-800',
  'border-slate-200 bg-slate-100 text-slate-700',
];

const PROPOSAL_TYPES = [
  'ADD_SOURCE',
  'IMPROVE_AGENT_SKILL',
  'IMPROVE_DETECTION_RULE',
  'IMPROVE_DOCUMENTATION_WORKFLOW',
  'SIMPLIFY_UI_SURFACE',
  'ADD_KPI',
  'FIX_BOTTLENECK',
  'DEFER_FEATURE',
  'HIDE_LEGACY_SURFACE',
  'CREATE_SPRINT',
] as const;

type ProposalType = (typeof PROPOSAL_TYPES)[number];

type ExecutiveCard = {
  title: string;
  role: string;
  focus: string;
  signal: string;
  next: string;
};

type ExecutiveReviewItem = {
  cooFindingCategory: string;
  ctoInterpretation: string;
  jointRecommendation: string;
  approvalRequired: string;
  relatedProductArea: string;
  guardrailNote: string;
};

type ImprovementProposalV1 = {
  id: string;
  title: string;
  proposal_type: ProposalType;
  owner: 'Dani Weber' | 'Fontana' | 'Executive Review';
  problem: string;
  evidence: string;
  recommendation: string;
  expected_impact: string;
  risk: string;
  complexity: string;
  approval_status: 'proposed' | 'approved' | 'rejected' | 'deferred';
  requires_dani_approval: true;
};

function isProposalType(value: unknown): value is ProposalType {
  return typeof value === 'string' && PROPOSAL_TYPES.includes(value as ProposalType);
}

function containsAny(value: string, keywords: string[]): boolean {
  return keywords.some(keyword => value.includes(keyword));
}

function inferProposalType(proposal: AgentOpsProposal): ProposalType {
  const explicit = (proposal as AgentOpsProposal & { proposal_type?: unknown }).proposal_type;
  if (isProposalType(explicit)) return explicit;

  const text = [
    proposal.title,
    proposal.problem_statement,
    proposal.proposed_change,
    proposal.expected_benefit,
    proposal.status,
    proposal.risk_level,
    proposal.agent_key,
    proposal.room_key,
  ].map(value => safeText(value, '')).join(' ').toLowerCase();

  if (containsAny(text, ['defer', 'deferred', 'pause', 'paused', 'later'])) return 'DEFER_FEATURE';
  if (containsAny(text, ['sprint', 'implementation', 'next sprint'])) return 'CREATE_SPRINT';
  if (containsAny(text, ['kpi', 'metric', 'score', 'dashboard'])) return 'ADD_KPI';
  if (containsAny(text, ['legacy'])) return 'HIDE_LEGACY_SURFACE';
  if (containsAny(text, ['ui', 'navigation', 'surface', 'screen', 'clutter'])) return 'SIMPLIFY_UI_SURFACE';
  if (containsAny(text, ['document', 'evidence', 'resource', 'checklist', 'completion'])) return 'IMPROVE_DOCUMENTATION_WORKFLOW';
  if (containsAny(text, ['detection', 'detector', 'routing', 'classify', 'scanner'])) return 'IMPROVE_DETECTION_RULE';
  if (containsAny(text, ['skill', 'agent capability', 'hunter', 'parser'])) return 'IMPROVE_AGENT_SKILL';
  if (containsAny(text, ['source', 'feed', 'rss', 'edgar', 'twitter', 'x/twitter'])) return 'ADD_SOURCE';
  if (containsAny(text, ['bottleneck', 'blocked', 'stuck', 'flow'])) return 'FIX_BOTTLENECK';

  return 'FIX_BOTTLENECK';
}

function safeText(value: unknown, fallback = '-'): string {
  if (value === null || value === undefined || value === '') return fallback;
  if (typeof value === 'string' || typeof value === 'number' || typeof value === 'boolean') return String(value);
  return fallback;
}

function formatDate(value: string | null | undefined): string {
  if (!value) return '-';
  try {
    return new Date(value).toLocaleString('en-CH', {
      year: '2-digit',
      month: 'short',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    });
  } catch {
    return value;
  }
}

function formatLabel(value: string): string {
  if (!value) return '-';
  return value
    .replace(/_/g, ' ')
    .replace(/\s+/g, ' ')
    .trim()
    .replace(/^./, first => first.toUpperCase());
}

function formatActivityType(value: string): string {
  const labels: Record<string, string> = {
    scan_run: 'Scan run',
    reliability_warning: 'Reliability warning',
    routing_audit: 'Routing audit',
    source_gap: 'Source gap',
  };
  return labels[value] ?? formatLabel(value);
}

function formatDiagnosticType(value: string): string {
  const labels: Record<string, string> = {
    scan_run: 'Scan run',
    reliability_warning: 'Reliability warning',
    routing_audit: 'Routing audit',
    source_gap: 'Source gap',
  };
  return labels[value] ?? formatLabel(value);
}

function badgeClass(value: string): string {
  const normalized = value.toLowerCase();
  if (['active', 'success', 'completed', 'implemented', 'accepted'].includes(normalized)) {
    return 'border-emerald-200 bg-emerald-50 text-emerald-700';
  }
  if (['warning', 'deferred', 'manual', 'assistive'].includes(normalized)) {
    return 'border-amber-200 bg-amber-50 text-amber-800';
  }
  if (['error', 'failed', 'rejected'].includes(normalized)) {
    return 'border-red-200 bg-red-50 text-red-700';
  }
  if (['observer', 'documented', 'planned', 'proposed'].includes(normalized)) {
    return 'border-blue-200 bg-blue-50 text-blue-700';
  }
  if (['archived', 'skipped'].includes(normalized)) {
    return 'border-slate-200 bg-slate-100 text-slate-500';
  }
  return 'border-slate-200 bg-slate-50 text-slate-600';
}

function Badge({ value }: { value: string }) {
  return (
    <span className={`inline-flex max-w-full items-center rounded-full border px-2 py-0.5 text-left text-[11px] font-medium leading-4 ${badgeClass(value)}`} style={{ overflowWrap: 'anywhere' }}>
      {value}
    </span>
  );
}

function EmptyState({ title, description }: { title: string; description: string }) {
  return (
    <div className="rounded-lg border border-slate-200 bg-slate-50 p-8 text-center">
      <p className="text-sm font-semibold text-slate-700">{title}</p>
      <p className="mt-2 text-sm text-slate-500">{description}</p>
    </div>
  );
}

function ExecutiveOfficeSection({
  cards,
  daniMetrics,
  executiveReview,
  reviewItems,
  proposals,
}: {
  cards: ExecutiveCard[];
  daniMetrics: DaniWeberMetrics | null;
  executiveReview: ExecutiveReviewPackage | null;
  reviewItems: ExecutiveReviewItem[];
  proposals: ImprovementProposalV1[];
}) {
  const topBottleneck = daniMetrics?.top_bottlenecks[0];
  const topFinding = executiveReview?.joint_findings[0];

  return (
    <section id="executive-office" className="mb-6 rounded-lg border border-slate-200 bg-white p-5 shadow-sm scroll-mt-6">
      <div className="mb-4 flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Executive Office</p>
          <h2 className="mt-1 text-lg font-semibold text-slate-950">COO / CTO Governance Layer</h2>
          <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-600">
            Deterministic office view for human approval and audit. No chat, live AI, autonomous execution, scanner run, evaluator change, cron change, or deploy is triggered here.
          </p>
        </div>
        <Badge value="proposal-only" />
      </div>

      <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
        {cards.map(card => (
          <div key={card.title} className="rounded-lg border border-slate-200 bg-slate-50 p-4">
            <div className="flex items-start justify-between gap-3">
              <div>
                <p className="text-sm font-semibold text-slate-950">{card.title}</p>
                <p className="mt-1 text-xs font-semibold uppercase tracking-wide text-slate-400">{card.role}</p>
              </div>
              <Badge value="manual" />
            </div>
            <ProposalText label="Focus" value={card.focus} />
            <ProposalText label="Last deterministic signal" value={card.signal} />
            <ProposalText label="Next user action" value={card.next} />
            <p className="mt-3 text-xs text-slate-500">No autonomous execution.</p>
          </div>
        ))}
      </div>

      <div className="mt-4 rounded-lg border border-emerald-200 bg-emerald-50 p-4">
        <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
          <div>
            <p className="text-sm font-semibold text-emerald-950">Dani Weber COO Metrics</p>
            <p className="mt-1 text-sm text-emerald-900">Process/funnel snapshot only. Findings become proposals; they do not execute changes.</p>
          </div>
          <Badge value="read-only" />
        </div>
        <div className="grid grid-cols-2 gap-2 md:grid-cols-4">
          <SmallStat label="Signals" value={daniMetrics?.total_special_situations ?? 0} />
          <SmallStat label="Promoted" value={`${daniMetrics?.promotion_rate_to_research_case.rate_percent ?? 0}%`} />
          <SmallStat label="Missing resources" value={daniMetrics?.documentation_blockers.missing_required_resources ?? 0} />
          <SmallStat label="Noise rows" value={daniMetrics?.low_priority_or_noise_count ?? 0} />
        </div>
        <p className="mt-3 text-xs leading-5 text-emerald-900">
          Top bottleneck: {topBottleneck ? `${topBottleneck.title} (${topBottleneck.count})` : 'No dominant bottleneck loaded.'}
        </p>
      </div>

      <div id="executive-review" className="mt-5 scroll-mt-6 rounded-lg border border-blue-200 bg-blue-50 p-4">
        <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
          <div>
            <p className="text-sm font-semibold text-blue-950">Executive Review</p>
            <p className="mt-1 text-sm text-blue-900">COO and CTO findings combined into approval-based next steps.</p>
          </div>
          <Badge value="read-only" />
        </div>
        <div className="mb-3 rounded-md border border-blue-200 bg-white p-3">
          <div className="grid gap-3 lg:grid-cols-2">
            <ProposalText label="COO summary" value={executiveReview?.coo_summary ?? 'Dani Weber metrics not loaded.'} />
            <ProposalText label="CTO summary" value={executiveReview?.cto_summary ?? 'Fontana interpretation not loaded.'} />
          </div>
          <div className="mt-3 grid gap-3 lg:grid-cols-2">
            <ProposalText
              label="Top joint finding"
              value={topFinding ? `${topFinding.coo_observation} Fontana: ${topFinding.cto_interpretation}` : 'No dominant COO / CTO joint finding loaded.'}
            />
            <ProposalText
              label="Joint recommendation"
              value={executiveReview?.joint_recommendations[0]?.recommended_action ?? 'Continue deterministic monitoring until Dani approves a process-improvement sprint.'}
            />
          </div>
          <div className="mt-3 flex flex-wrap gap-2">
            <Badge value={`${executiveReview?.joint_findings.length ?? 0} finding(s)`} />
            <Badge value={`${executiveReview?.pending_approval_items.length ?? 0} approval item(s)`} />
            <Badge value="no auto-apply" />
          </div>
        </div>
        <div className="grid gap-3 lg:grid-cols-3">
          {reviewItems.map(item => (
            <div key={`${item.cooFindingCategory}-${item.relatedProductArea}`} className="rounded-md border border-blue-200 bg-white p-3">
              <ProposalText label="COO finding category" value={item.cooFindingCategory} />
              <ProposalText label="CTO interpretation" value={item.ctoInterpretation} />
              <ProposalText label="Joint recommendation" value={item.jointRecommendation} />
              <div className="mt-3 flex flex-wrap gap-2">
                <Badge value={item.approvalRequired} />
                <Badge value={item.relatedProductArea} />
              </div>
              <p className="mt-3 text-xs leading-5 text-blue-900">{item.guardrailNote}</p>
            </div>
          ))}
        </div>
      </div>

      <div id="executive-proposals" className="mt-5 scroll-mt-6 rounded-lg border border-amber-200 bg-amber-50 p-4">
        <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
          <div>
            <p className="text-sm font-semibold text-amber-950">Improvement Proposals v1</p>
            <p className="mt-1 text-sm text-amber-900">Read-only proposal model. Persisted Agent Ops proposals can still be reviewed in the Learning Proposals section below.</p>
          </div>
          <Badge value={`${proposals.length} proposed`} />
        </div>
        <div className="grid gap-3 lg:grid-cols-3">
          {proposals.map(proposal => (
            <div key={proposal.id} className="rounded-md border border-amber-200 bg-white p-3">
              <div className="mb-3 flex flex-wrap items-start justify-between gap-2">
                <div>
                  <p className="text-sm font-semibold text-slate-950">{proposal.title}</p>
                  <p className="mt-1 font-mono text-xs text-slate-400">{proposal.id}</p>
                </div>
                <Badge value={proposal.approval_status} />
              </div>
              <div className="mb-3 flex flex-wrap gap-2">
                <Badge value={proposal.proposal_type} />
                <Badge value={proposal.owner} />
              </div>
              <ProposalText label="Problem" value={proposal.problem} />
              <ProposalText label="Evidence" value={proposal.evidence} />
              <ProposalText label="Recommendation" value={proposal.recommendation} />
              <ProposalText label="Expected impact" value={proposal.expected_impact} />
              <div className="mt-3 grid grid-cols-2 gap-2 text-xs">
                <SmallStat label="Risk" value={proposal.risk} />
                <SmallStat label="Complexity" value={proposal.complexity} />
              </div>
              <p className="mt-3 text-xs font-medium text-amber-900">Requires Dani approval before implementation.</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function SectionShell({
  id,
  title,
  subtitle,
  error,
  children,
}: {
  id: string;
  title: string;
  subtitle: string;
  error?: string | null;
  children: React.ReactNode;
}) {
  return (
    <section id={id} className="scroll-mt-6 rounded-lg border border-slate-200 bg-white shadow-sm">
      <div className="border-b border-slate-200 bg-slate-50 px-5 py-4">
        <h2 className="text-sm font-semibold text-slate-900">{title}</h2>
        <p className="mt-1 text-sm text-slate-500">{subtitle}</p>
      </div>
      {error && (
        <div className="border-b border-amber-200 bg-amber-50 px-5 py-3">
          <p className="text-sm text-amber-900">{error}. Backend may not yet be deployed or migrated.</p>
        </div>
      )}
      <div className="p-5">{children}</div>
    </section>
  );
}

function PlaceholderPanel({ title, description, items }: { title: string; description: string; items: string[] }) {
  return (
    <div className="rounded-lg border border-slate-200 bg-slate-50 p-5">
      <p className="text-sm font-semibold text-slate-800">{title}</p>
      <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-600">{description}</p>
      <div className="mt-4 grid grid-cols-1 gap-2 md:grid-cols-3">
        {items.map(item => (
          <div key={item} className="rounded-md border border-slate-200 bg-white px-3 py-2 text-sm text-slate-600">
            {item}
          </div>
        ))}
      </div>
    </div>
  );
}

function guardrailText(value: AgentOpsAgent['guardrails']): string {
  if (Array.isArray(value)) return value.join(', ');
  if (typeof value === 'string') return value;
  if (value && typeof value === 'object') return Object.values(value).map(String).join(', ');
  return 'No autonomous production powers';
}

function initials(name: string): string {
  return name
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map(part => part[0]?.toUpperCase())
    .join('') || 'AO';
}

function avatarClass(key: string): string {
  const total = key.split('').reduce((sum, char) => sum + char.charCodeAt(0), 0);
  return AVATAR_COLORS[total % AVATAR_COLORS.length];
}

function identityForAgent(agent: AgentOpsAgent): AgentIdentity {
  const haystack = `${agent.key} ${agent.name} ${agent.role ?? ''}`.toLowerCase();
  return AGENT_IDENTITIES.find(identity => haystack.includes(identity.keyHint)) ?? {
    name: agent.name,
    keyHint: agent.key,
    room: agent.room_key ?? 'agent_ops',
    title: agentCallsign(agent),
    mission: agent.role ?? 'Observer/manual role documented in Agent Ops.',
    watches: ['loaded Agent Ops rows', 'manual review state'],
    outputs: ['activity rows', 'diagnostics when present'],
    currentMode: agent.autonomy_level || 'observer-only',
    futureMode: 'manual-approved sprint required',
    scheduler: 'disabled in this sprint',
  };
}

function agentCallsign(agent: AgentOpsAgent): string {
  const key = `${agent.key} ${agent.name}`.toLowerCase();
  const match = Object.entries(AGENT_CALLSIGNS).find(([needle]) => key.includes(needle));
  return match?.[1] ?? 'Manual operator';
}

function activityCountForAgent(agent: AgentOpsAgent, activity: AgentOpsActivity[]): number {
  return activity.filter(item => item.agent_key === agent.key).length;
}

function problemCountForAgent(agent: AgentOpsAgent, diagnostics: AgentOpsDiagnostic[]): number {
  return diagnostics.filter(item => item.agent_key === agent.key).length;
}

function isCaseRelated(type?: string | null): boolean {
  const normalized = (type ?? '').toLowerCase();
  return normalized.includes('researchcase') || normalized.includes('research_case') || normalized.includes('specialsituation') || normalized.includes('special_situation');
}

function caseActivityCountForAgent(agent: AgentOpsAgent, activity: AgentOpsActivity[], diagnostics: AgentOpsDiagnostic[]): number {
  return [
    ...activity.filter(item => item.agent_key === agent.key && isCaseRelated(item.related_entity_type)),
    ...diagnostics.filter(item => item.agent_key === agent.key && isCaseRelated(item.related_entity_type)),
  ].length;
}

function agentMetrics(agent: AgentOpsAgent, activity: AgentOpsActivity[], diagnostics: AgentOpsDiagnostic[], proposals: AgentOpsProposal[]) {
  const agentActivity = activity.filter(item => item.agent_key === agent.key);
  const agentDiagnostics = diagnostics.filter(item => item.agent_key === agent.key);
  const agentProposals = proposals.filter(item => item.agent_key === agent.key);
  const successCount = agentActivity.filter(item => ['success', 'completed'].includes(item.status) || item.severity === 'success').length;
  const evidenceRows = agentActivity.filter(item => `${item.activity_type} ${item.title} ${item.summary ?? ''}`.toLowerCase().includes('evidence')).length;
  const severeDiagnostics = agentDiagnostics.filter(item => ['warning', 'error', 'critical'].includes(item.severity)).length;
  const reviewedProposals = agentProposals.filter(item => item.reviewed_at || ['accepted', 'rejected', 'deferred', 'implemented', 'archived'].includes(item.status)).length;
  const reviewRows = agentActivity.filter(item => `${item.title} ${item.summary ?? ''}`.toLowerCase().includes('manual') || `${item.title} ${item.summary ?? ''}`.toLowerCase().includes('guardrail')).length;
  return {
    coverageXp: agentActivity.length * 10,
    signalXp: successCount * 10,
    learningXp: (agentDiagnostics.length + reviewedProposals) * 10,
    reliability: Math.max(0, Math.min(100, 100 - severeDiagnostics * 15 + successCount * 3)),
    evidenceQuality: Math.min(100, evidenceRows * 15 + successCount * 5),
    noisePenalty: severeDiagnostics * 10,
    reviewDiscipline: Math.min(100, reviewRows * 20 + reviewedProposals * 10),
  };
}

function roomScore(counts?: { activity: number; diagnostics: number; proposals: number }): number {
  if (!counts) return 0;
  return Math.max(0, Math.min(100, 50 + counts.activity * 4 + counts.proposals * 3 - counts.diagnostics * 10));
}

function relatedCaseHref(type?: string | null, id?: string | null): string | null {
  if (!type || !id) return null;
  const normalized = type.toLowerCase();
  if (normalized.includes('researchcase') || normalized.includes('research_case')) return `/investment/research/${id}`;
  if (normalized.includes('specialsituation') || normalized.includes('special_situation')) return `/investment/situations/${id}`;
  return null;
}

function relatedEntity(type?: string | null, id?: string | null): string {
  return type ? `${type}:${id ?? '-'}` : '-';
}

function allowedActions(status: AgentOpsProposalStatus): { status: AgentOpsProposalStatus; label: string }[] {
  if (status === 'proposed') {
    return [
      { status: 'accepted', label: 'Accept' },
      { status: 'rejected', label: 'Reject' },
      { status: 'deferred', label: 'Defer' },
      { status: 'archived', label: 'Archive' },
    ];
  }
  if (status === 'accepted') {
    return [
      { status: 'implemented', label: 'Mark implemented' },
      { status: 'archived', label: 'Archive' },
    ];
  }
  if (status === 'deferred') {
    return [
      { status: 'proposed', label: 'Reopen' },
      { status: 'rejected', label: 'Reject' },
      { status: 'archived', label: 'Archive' },
    ];
  }
  return status === 'archived' ? [] : [{ status: 'archived', label: 'Archive' }];
}

export default function AgentOpsPage() {
  const [rooms, setRooms] = useState<AgentOpsRoom[]>([]);
  const [agents, setAgents] = useState<AgentOpsAgent[]>([]);
  const [activity, setActivity] = useState<AgentOpsActivity[]>([]);
  const [diagnostics, setDiagnostics] = useState<AgentOpsDiagnostic[]>([]);
  const [proposals, setProposals] = useState<AgentOpsProposal[]>([]);
  const [fontanaReport, setFontanaReport] = useState<FontanaDiagnosticReport | null>(null);
  const [daniWeberMetrics, setDaniWeberMetrics] = useState<DaniWeberMetrics | null>(null);
  const [executiveReview, setExecutiveReview] = useState<ExecutiveReviewPackage | null>(null);
  const [loading, setLoading] = useState(true);
  const [errors, setErrors] = useState<Record<string, string | null>>({});
  const [proposalErrors, setProposalErrors] = useState<Record<string, string>>({});
  const [proposalNotes, setProposalNotes] = useState<Record<string, string>>({});
  const [updatingProposal, setUpdatingProposal] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);
  const [lastRefreshedAt, setLastRefreshedAt] = useState<Date | null>(null);

  async function loadAgentOps({ initial = false }: { initial?: boolean } = {}) {
    if (initial) setLoading(true);
    else setRefreshing(true);
    const nextErrors: Record<string, string | null> = {};
    const [
      roomsResult,
      agentsResult,
      activityResult,
      diagnosticsResult,
      proposalsResult,
      fontanaResult,
      daniMetricsResult,
      executiveReviewResult,
    ] = await Promise.allSettled([
      fetchAgentOpsRooms(),
      fetchAgentOpsAgents(),
      fetchAgentOpsActivity({ limit: 25 }),
      fetchAgentOpsDiagnostics({ limit: 25 }),
      fetchAgentOpsProposals({ limit: 25 }),
      fetchFontanaReport(),
      fetchDaniWeberMetrics(),
      fetchExecutiveReview(),
    ]);

    if (roomsResult.status === 'fulfilled') setRooms(roomsResult.value.rooms);
    else nextErrors.rooms = roomsResult.reason instanceof Error ? roomsResult.reason.message : 'Failed to load rooms';

    if (agentsResult.status === 'fulfilled') setAgents(agentsResult.value.agents);
    else nextErrors.agents = agentsResult.reason instanceof Error ? agentsResult.reason.message : 'Failed to load agents';

    if (activityResult.status === 'fulfilled') setActivity(activityResult.value.items);
    else nextErrors.activity = activityResult.reason instanceof Error ? activityResult.reason.message : 'Failed to load activity';

    if (diagnosticsResult.status === 'fulfilled') setDiagnostics(diagnosticsResult.value.items);
    else nextErrors.diagnostics = diagnosticsResult.reason instanceof Error ? diagnosticsResult.reason.message : 'Failed to load diagnostics';

    if (proposalsResult.status === 'fulfilled') setProposals(proposalsResult.value.items);
    else nextErrors.proposals = proposalsResult.reason instanceof Error ? proposalsResult.reason.message : 'Failed to load proposals';

    if (fontanaResult.status === 'fulfilled') setFontanaReport(fontanaResult.value);
    else nextErrors.fontana = fontanaResult.reason instanceof Error ? fontanaResult.reason.message : 'Failed to load Fontana report';

    if (daniMetricsResult.status === 'fulfilled') setDaniWeberMetrics(daniMetricsResult.value);
    else nextErrors.daniWeberMetrics = daniMetricsResult.reason instanceof Error ? daniMetricsResult.reason.message : 'Failed to load Dani Weber metrics';

    if (executiveReviewResult.status === 'fulfilled') setExecutiveReview(executiveReviewResult.value);
    else nextErrors.executiveReview = executiveReviewResult.reason instanceof Error ? executiveReviewResult.reason.message : 'Failed to load Executive Review';

    setErrors(nextErrors);
    setLastRefreshedAt(new Date());
    if (initial) setLoading(false);
    else setRefreshing(false);
  }

  useEffect(() => {
    loadAgentOps({ initial: true });
  }, []);

  const agentCountByRoom = useMemo(() => {
    const counts = new Map<string, number>();
    for (const agent of agents) {
      if (agent.room_key) counts.set(agent.room_key, (counts.get(agent.room_key) ?? 0) + 1);
    }
    return counts;
  }, [agents]);

  const roomCounts = useMemo(() => {
    const counts = new Map<string, { activity: number; diagnostics: number; proposals: number }>();
    for (const room of rooms) counts.set(room.key, { activity: 0, diagnostics: 0, proposals: 0 });
    for (const item of activity) {
      if (!item.room_key) continue;
      const row = counts.get(item.room_key) ?? { activity: 0, diagnostics: 0, proposals: 0 };
      row.activity += 1;
      counts.set(item.room_key, row);
    }
    for (const item of diagnostics) {
      if (!item.room_key) continue;
      const row = counts.get(item.room_key) ?? { activity: 0, diagnostics: 0, proposals: 0 };
      row.diagnostics += 1;
      counts.set(item.room_key, row);
    }
    for (const item of proposals) {
      if (!item.room_key) continue;
      const row = counts.get(item.room_key) ?? { activity: 0, diagnostics: 0, proposals: 0 };
      row.proposals += 1;
      counts.set(item.room_key, row);
    }
    return counts;
  }, [activity, diagnostics, proposals, rooms]);

  const caseRelevanceRows = useMemo(() => {
    return [...activity, ...diagnostics]
      .filter(item => isCaseRelated(item.related_entity_type) && item.related_entity_id)
      .slice(0, 6);
  }, [activity, diagnostics]);

  const qualityGapRows = useMemo(() => {
    return diagnostics
      .filter(item => isCaseRelated(item.related_entity_type) && ['warning', 'error', 'critical'].includes(item.severity))
      .slice(0, 4);
  }, [diagnostics]);

  const fontanaRows = useMemo(() => {
    return [...activity, ...diagnostics]
      .filter(item => `${item.agent_key ?? ''} ${item.title}`.toLowerCase().includes('fontana'))
      .slice(0, 3);
  }, [activity, diagnostics]);

  const agentWorkload = useMemo(() => {
    return agents
      .map(agent => {
        const logs = activityCountForAgent(agent, activity);
        const problems = problemCountForAgent(agent, diagnostics);
        const caseRows = caseActivityCountForAgent(agent, activity, diagnostics);
        return { agent, identity: identityForAgent(agent), logs, problems, caseRows, load: logs + problems * 2 + caseRows };
      })
      .sort((a, b) => b.load - a.load)
      .slice(0, 5);
  }, [activity, agents, diagnostics]);

  const nextManualActions = [
    'Open case-related diagnostic rows and resolve missing evidence gaps manually.',
    'Use Official Source Finder queries from case pages; SwissEdge does not run them.',
    'Reject noisy candidates and map manually reviewed sources to resources/checklist items.',
    'Review Fontana bottlenecks before planning the next sprint.',
  ];

  const executiveCards = useMemo<ExecutiveCard[]>(() => {
    const pendingProposalCount = proposals.filter(proposal => proposal.status === 'proposed').length;
    const warningCount = diagnostics.filter(item => ['warning', 'error', 'critical'].includes(item.severity)).length;
    const fontanaSignal = fontanaReport?.summary ?? 'Fontana report not loaded; deterministic placeholder only.';
    const promotionRate = daniWeberMetrics?.promotion_rate_to_research_case.rate_percent ?? 0;
    const missingResources = daniWeberMetrics?.documentation_blockers.missing_required_resources ?? 0;
    const topCooBottleneck = daniWeberMetrics?.top_bottlenecks[0]?.title ?? 'No dominant COO bottleneck loaded.';
    return [
      {
        title: 'Dani Weber Office — COO',
        role: 'Process governor / approval authority',
        focus: 'Process flow, bottlenecks, promotion rate, documentation quality, noise reduction, and source/skill/process improvements.',
        signal: `${daniWeberMetrics?.total_special_situations ?? 0} signal(s), ${promotionRate}% promoted, ${missingResources} missing required resource(s). Top bottleneck: ${topCooBottleneck}`,
        next: 'Review proposed changes, accept/defer/reject status only, and approve implementation in a future sprint.',
      },
      {
        title: 'Fontana Office — CTO',
        role: 'Deterministic technology audit',
        focus: 'Technology, architecture, product coherence, technical debt, guardrails, and sprint recommendations.',
        signal: fontanaSignal,
        next: 'Inspect bottlenecks and technical findings before selecting the next implementation batch.',
      },
      {
        title: 'Executive Review',
        role: 'COO / CTO feedback loop',
        focus: 'Combines COO process findings with CTO interpretation for approval-based next steps.',
        signal: `${activity.length} activity row(s), ${diagnostics.length} diagnostic row(s), ${proposals.length} persisted proposal row(s), ${pendingProposalCount} pending proposal(s).`,
        next: 'Compare process and technical findings, then choose which proposal stays in the manual queue.',
      },
      {
        title: 'Pending Improvement Proposals',
        role: 'Manual proposal queue',
        focus: 'Proposal status review only. Proposals require Dani approval before implementation.',
        signal: `${pendingProposalCount} persisted proposal(s) still proposed.`,
        next: 'Use Learning Proposals below for status review; implementation remains a separate Dani-approved sprint.',
      },
    ];
  }, [activity.length, daniWeberMetrics, diagnostics, fontanaReport, proposals]);

  const executiveReviewItems = useMemo<ExecutiveReviewItem[]>(() => {
    const caseWarnings = diagnostics.filter(item => isCaseRelated(item.related_entity_type) && ['warning', 'error', 'critical'].includes(item.severity)).length;
    const proposedCount = proposals.filter(proposal => proposal.status === 'proposed').length;
    const cooBottleneck = daniWeberMetrics?.top_bottlenecks[0];
    return [
      {
        cooFindingCategory: 'COO funnel bottleneck',
        ctoInterpretation: cooBottleneck ? `${cooBottleneck.title}: ${cooBottleneck.count} item(s) in deterministic metrics.` : 'No dominant Dani Weber COO bottleneck loaded.',
        jointRecommendation: 'Use COO metrics to choose a future process-improvement sprint; do not auto-apply proposals.',
        approvalRequired: 'Dani approval required',
        relatedProductArea: 'Executive Office',
        guardrailNote: 'Dani Weber metrics are read-only and do not create cases, verify evidence, run evaluator, or trigger scans.',
      },
      {
        cooFindingCategory: 'Documentation throughput',
        ctoInterpretation: caseWarnings > 0 ? `${caseWarnings} case-related warning row(s) need traceability review.` : 'No case-related warning rows loaded in Agent Ops.',
        jointRecommendation: 'Keep evidence review manual and resolve missing documentation before promotion or editorial work.',
        approvalRequired: 'Dani approval required',
        relatedProductArea: 'Evidence Room',
        guardrailNote: 'evidence_found does not mean verified; no checklist or source auto-completion.',
      },
      {
        cooFindingCategory: 'Product surface simplicity',
        ctoInterpretation: 'Mission Control now separates core, supporting, advanced/legacy, and paused surfaces.',
        jointRecommendation: 'Continue hiding/de-emphasizing legacy surfaces through labels and hierarchy instead of deleting routes.',
        approvalRequired: 'Dani approval required',
        relatedProductArea: 'Mission Control',
        guardrailNote: 'No Marketplace/Sales functional change and no public-site implementation.',
      },
      {
        cooFindingCategory: 'Improvement proposal flow',
        ctoInterpretation: `${proposedCount} persisted Agent Ops proposal(s) are awaiting manual review.`,
        jointRecommendation: 'Review proposal status only; implementation belongs in a future explicit sprint.',
        approvalRequired: 'Dani approval required',
        relatedProductArea: 'Agent Ops',
        guardrailNote: 'Proposal review does not deploy, run agents, change cron, run scanner, or enable evaluator v2.',
      },
    ];
  }, [daniWeberMetrics, diagnostics, proposals]);

  const improvementProposalsV1 = useMemo<ImprovementProposalV1[]>(() => {
    const mapped = proposals.slice(0, 4).map((proposal): ImprovementProposalV1 => ({
      id: `agent-ops-${proposal.id.slice(0, 8)}`,
      title: proposal.title,
      proposal_type: inferProposalType(proposal),
      owner: proposal.agent_key?.toLowerCase().includes('fontana') ? 'Fontana' : 'Executive Review',
      problem: proposal.problem_statement,
      evidence: proposal.source_diagnostic_id ? `Linked diagnostic ${proposal.source_diagnostic_id.slice(0, 8)}.` : 'Loaded from existing Agent Ops proposal row.',
      recommendation: proposal.proposed_change,
      expected_impact: proposal.expected_benefit ?? 'Expected impact requires manual review before implementation.',
      risk: proposal.risk_level,
      complexity: proposal.risk_level === 'high' ? 'high' : 'low',
      approval_status: proposal.status === 'accepted' ? 'approved' : proposal.status === 'archived' || proposal.status === 'implemented' ? 'deferred' : proposal.status,
      requires_dani_approval: true,
    }));
    const deterministicFallbacks: ImprovementProposalV1[] = [
      {
        id: 'ap-simplify-legacy-surfaces',
        title: 'Keep legacy investment surfaces de-emphasized',
        proposal_type: 'HIDE_LEGACY_SURFACE',
        owner: 'Executive Review',
        problem: 'Legacy evaluation and watchlist surfaces can compete with the SEC-driven workflow.',
        evidence: 'Mission Control classifies Evaluations Queue and Watchlist as Advanced / Legacy.',
        recommendation: 'Maintain labels and grouping; do not delete routes without a future explicit cleanup sprint.',
        expected_impact: 'Reduces workflow noise while preserving historical access.',
        risk: 'low',
        complexity: 'low',
        approval_status: 'proposed',
        requires_dani_approval: true,
      },
      {
        id: 'ap-source-workflow-gap',
        title: 'Create a focused source workflow improvement sprint',
        proposal_type: 'CREATE_SPRINT',
        owner: 'Dani Weber',
        problem: 'SEC document acquisition now creates metadata candidates that still require manual review and mapping.',
        evidence: 'Sprint AO stores official SEC candidates without verification or checklist completion.',
        recommendation: 'Plan a future sprint for manual source review ergonomics, not automated verification.',
        expected_impact: 'Improves documentation quality without weakening guardrails.',
        risk: 'medium',
        complexity: 'medium',
        approval_status: 'proposed',
        requires_dani_approval: true,
      },
      {
        id: 'ap-fontana-kpi-followup',
        title: 'Add Executive Office KPI snapshot later',
        proposal_type: 'ADD_KPI',
        owner: 'Fontana',
        problem: 'Executive Office currently summarizes loaded operational rows but does not persist a KPI snapshot.',
        evidence: 'Agent Ops already has rooms, diagnostics, proposals, and Fontana report data available.',
        recommendation: 'Defer persisted KPI snapshots until Dani approves the exact metrics.',
        expected_impact: 'Keeps AP small while identifying a clean future measurement surface.',
        risk: 'low',
        complexity: 'medium',
        approval_status: 'deferred',
        requires_dani_approval: true,
      },
    ];
    return [...mapped, ...deterministicFallbacks].slice(0, 6);
  }, [proposals]);

  async function reviewProposal(proposal: AgentOpsProposal, status: AgentOpsProposalStatus) {
    setUpdatingProposal(proposal.id);
    setProposalErrors(prev => ({ ...prev, [proposal.id]: '' }));
    try {
      const result = await updateAgentOpsProposal(proposal.id, {
        status,
        reviewer_note: proposalNotes[proposal.id] || proposal.reviewer_note || `Reviewed from Agent Ops UI: ${status}`,
      });
      setProposals(prev => prev.map(item => item.id === proposal.id ? result.proposal : item));
    } catch (err) {
      setProposalErrors(prev => ({
        ...prev,
        [proposal.id]: err instanceof Error ? err.message : 'Proposal update failed',
      }));
    } finally {
      setUpdatingProposal(null);
    }
  }

  return (
    <div className="min-h-screen bg-slate-50 p-6 text-slate-900 md:p-8">
      <div className="mx-auto max-w-7xl">
        <nav className="mb-8 flex flex-wrap items-center gap-x-5 gap-y-2 text-sm">
          {TOP_NAV_LINKS.map(([href, label]) => (
            <Link key={href} href={href} className="font-medium text-slate-500 hover:text-slate-900">
              {label}
            </Link>
          ))}
        </nav>

        <div className="mb-6 flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
          <div>
            <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-500">Platform Observability</p>
            <h1 className="mb-2 text-3xl font-semibold tracking-tight text-slate-950">Agent Ops</h1>
            <p className="max-w-3xl text-sm leading-6 text-slate-600">
              Read-only operating rooms for SwissEdge agents: who they are, what they watch, where they log, and which cases/problems they touch.
            </p>
          </div>
          <div className="flex flex-col items-start gap-2 md:items-end">
            <button
              type="button"
              onClick={() => loadAgentOps()}
              disabled={loading || refreshing}
              className="rounded-md border border-slate-300 bg-white px-3 py-2 text-xs font-medium text-slate-700 shadow-sm hover:bg-slate-50 disabled:opacity-60"
            >
              {refreshing ? 'Refreshing...' : 'Refresh'}
            </button>
            <p className="text-xs text-slate-400">
              Last refreshed: {lastRefreshedAt ? formatDate(lastRefreshedAt.toISOString()) : '-'}
            </p>
          </div>
        </div>

        <div className="mb-6 rounded-lg border border-blue-200 bg-blue-50 p-4 shadow-sm">
          <p className="text-sm font-semibold text-blue-950">Observability-first guardrail</p>
          <p className="mt-1 text-sm leading-6 text-blue-900">
            Agent Ops is observability-first. This page does not trigger scans, change cron, enable evaluator v2, call live AI,
            deploy, or apply learning proposals automatically.
          </p>
        </div>

        <ExecutiveOfficeSection
          cards={executiveCards}
          daniMetrics={daniWeberMetrics}
          executiveReview={executiveReview}
          reviewItems={executiveReviewItems}
          proposals={improvementProposalsV1}
        />

        <div className="mb-6 grid grid-cols-2 gap-3 md:grid-cols-5">
          {[
            ['Rooms', rooms.length],
            ['Agents', agents.length],
            ['Activity rows', activity.length],
            ['Diagnostics', diagnostics.length],
            ['Proposals', proposals.length],
          ].map(([label, value]) => (
            <div key={label} className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
              <div className="text-xl font-semibold text-slate-950">{value}</div>
              <div className="mt-1 text-xs font-medium uppercase tracking-wide text-slate-500">{label}</div>
            </div>
          ))}
        </div>

        <div className="mb-6 grid grid-cols-1 gap-4 lg:grid-cols-[1.4fr_0.9fr]">
          <section className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
            <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
              <div>
                <h2 className="text-sm font-semibold text-slate-950">Agent Roster</h2>
                <p className="mt-1 text-sm text-slate-500">Visual identities are deterministic placeholders; no external images are fetched.</p>
              </div>
              <Badge value="manual-only" />
            </div>
            {agents.length === 0 ? (
              <EmptyState title="No agents found." description="Seed data may not be present yet." />
            ) : (
              <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
                {agents.slice(0, 6).map(agent => {
                  const identity = identityForAgent(agent);
                  return (
                  <Link
                    key={agent.id}
                    href={agent.room_key ? `/agent-ops/rooms/${agent.room_key}` : '/agent-ops'}
                    className={`rounded-lg border p-4 text-left no-underline transition-colors hover:border-blue-300 hover:bg-white ${identity.name === 'Missing Evidence Hunter' ? 'border-emerald-200 bg-emerald-50' : 'border-slate-200 bg-slate-50'}`}
                  >
                    <div className="flex items-start gap-3">
                      <div className={`flex h-11 w-11 shrink-0 items-center justify-center rounded-md border font-semibold ${avatarClass(agent.key)}`}>
                        {initials(agent.name)}
                      </div>
                      <div className="min-w-0">
                        <div className="flex flex-wrap items-center gap-2">
                          <p className="min-w-0 font-semibold text-slate-950" style={{ overflowWrap: 'anywhere' }}>{identity.name}</p>
                          <Badge value={agent.autonomy_level} />
                        </div>
                        <p className="mt-1 text-xs font-medium uppercase tracking-wide text-slate-400" style={{ overflowWrap: 'anywhere' }}>{identity.title}</p>
                        <p className="mt-2 text-sm leading-6 text-slate-600" style={{ overflowWrap: 'anywhere' }}>{identity.mission}</p>
                      </div>
                    </div>
                    <div className="mt-3 grid grid-cols-2 gap-2 text-xs md:grid-cols-4">
                      <SmallStat label="Logs" value={activityCountForAgent(agent, activity)} />
                      <SmallStat label="Problems" value={problemCountForAgent(agent, diagnostics)} />
                      <SmallStat label="Case rows" value={caseActivityCountForAgent(agent, activity, diagnostics)} />
                      <SmallStat label="Room" value={agent.room_key ?? '-'} />
                    </div>
                  </Link>
                  );
                })}
              </div>
            )}
          </section>

          <section className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
            <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
              <div>
                <h2 className="text-sm font-semibold text-slate-950">Agent Workload & Next Manual Actions</h2>
                <p className="mt-1 text-sm leading-6 text-slate-500">
                  Derived from loaded Agent Ops rows only. Scheduler remains disabled; future frequency changes require an approved sprint.
                </p>
              </div>
              <Badge value="observer/manual-only" />
            </div>
            {agentWorkload.length === 0 ? (
              <EmptyState title="No workload rows yet." description="Agent activity and diagnostics will appear after safe logging is present." />
            ) : (
              <div className="grid gap-2">
                {agentWorkload.map(({ agent, identity, logs, problems, caseRows }) => (
                  <div key={agent.id} className="rounded-md border border-slate-200 bg-slate-50 px-3 py-2">
                    <div className="flex flex-wrap items-start justify-between gap-2">
                      <div className="min-w-0">
                        <p className="text-sm font-semibold text-slate-900" style={{ overflowWrap: 'anywhere' }}>{identity.name}</p>
                        <p className="mt-0.5 text-xs text-slate-500" style={{ overflowWrap: 'anywhere' }}>{identity.title}</p>
                      </div>
                      <Badge value={identity.currentMode} />
                    </div>
                    <div className="mt-2 grid grid-cols-3 gap-2 text-xs">
                      <SmallStat label="Logs" value={logs} />
                      <SmallStat label="Problems" value={problems} />
                      <SmallStat label="Case rows" value={caseRows} />
                    </div>
                  </div>
                ))}
              </div>
            )}
            <div className="mt-4 rounded-md border border-slate-200 bg-white p-3">
              <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Next manual actions</p>
              <ul className="mt-2 space-y-1">
                {nextManualActions.map(action => (
                  <li key={action} className="text-sm leading-6 text-slate-600">{action}</li>
                ))}
              </ul>
            </div>
          </section>
        </div>

        <div className="mb-6 rounded-lg border border-emerald-200 bg-emerald-50 p-5 shadow-sm">
          <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
            <div>
              <p className="text-xs font-semibold uppercase tracking-wide text-emerald-700">Observer Agent Identity</p>
              <h2 className="mt-1 text-lg font-semibold text-emerald-950">Missing Evidence Hunter</h2>
              <p className="mt-2 max-w-3xl text-sm leading-6 text-emerald-900">
                Tracks missing required resources and checklist gaps. Suggests manual search steps. Observer-only.
              </p>
              <div className="mt-4 grid gap-3 text-sm md:grid-cols-2">
                <div className="rounded-md border border-emerald-200 bg-white p-3">
                  <p className="text-xs font-semibold uppercase tracking-wide text-emerald-700">Watches</p>
                  <p className="mt-2 leading-6 text-emerald-900">
                    Missing required resources, checklist gaps, candidate-only resources, rejected/noisy sources, missing SEC filing URLs, low documentation quality, and low Intelligence Score.
                  </p>
                </div>
                <div className="rounded-md border border-emerald-200 bg-white p-3">
                  <p className="text-xs font-semibold uppercase tracking-wide text-emerald-700">Outputs</p>
                  <p className="mt-2 leading-6 text-emerald-900">
                    Missing evidence list, manual search plan, documentation gaps, and suggested next manual actions.
                  </p>
                </div>
              </div>
            </div>
            <div className="grid min-w-64 gap-2 text-xs">
              <div className="flex justify-between rounded-md border border-emerald-200 bg-white px-3 py-2">
                <span className="text-emerald-700">Current mode</span>
                <span className="font-semibold text-emerald-950">manual / observer-only</span>
              </div>
              <div className="flex justify-between rounded-md border border-emerald-200 bg-white px-3 py-2">
                <span className="text-emerald-700">Future mode</span>
                <span className="font-semibold text-emerald-950">frequent missing-evidence checks planned</span>
              </div>
              <div className="flex justify-between rounded-md border border-emerald-200 bg-white px-3 py-2">
                <span className="text-emerald-700">Scheduler</span>
                <span className="font-semibold text-emerald-950">disabled in this sprint</span>
              </div>
            </div>
          </div>
        </div>

        <div className="mb-6 grid gap-4 lg:grid-cols-3">
          <AgentTimelineCard
            title="Missing Evidence Hunter"
            subtitle="Case activity relevance"
            rows={caseRelevanceRows}
            empty="No related case activity loaded yet."
          />
          <AgentTimelineCard
            title="Quality Sentinel"
            subtitle="Documentation gaps and risks"
            rows={qualityGapRows}
            empty="No related warning rows loaded yet."
          />
          <AgentTimelineCard
            title="Fontana"
            subtitle="Diagnostics pending / no autonomous report yet"
            rows={fontanaRows}
            empty="No Fontana activity rows. Runtime remains unimplemented."
          />
        </div>

        <section className="mb-6 rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
          <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
            <div>
              <h2 className="text-sm font-semibold text-slate-950">Research Agent Network</h2>
              <p className="mt-1 text-sm text-slate-500">Derived operational indicators only. Metrics are not persisted and do not imply execution.</p>
            </div>
            <Badge value="observer-only" />
          </div>
          <div className="grid gap-4 lg:grid-cols-3">
            {AGENT_IDENTITIES.map(identity => {
              const matchingAgent = agents.find(agent => {
                const haystack = `${agent.key} ${agent.name} ${agent.role ?? ''}`.toLowerCase();
                return haystack.includes(identity.keyHint);
              });
              const metrics = matchingAgent ? agentMetrics(matchingAgent, activity, diagnostics, proposals) : null;
              const relatedCases = matchingAgent ? caseActivityCountForAgent(matchingAgent, activity, diagnostics) : 0;
              const problems = matchingAgent ? problemCountForAgent(matchingAgent, diagnostics) : 0;
              const logs = matchingAgent ? activityCountForAgent(matchingAgent, activity) : 0;
              return (
                <div key={identity.name} className={`rounded-lg border p-4 ${identity.name === 'Missing Evidence Hunter' ? 'border-emerald-200 bg-emerald-50' : 'border-slate-200 bg-slate-50'}`}>
                  <div className="flex items-start gap-3">
                    <div className={`flex h-12 w-12 shrink-0 items-center justify-center rounded-lg border font-semibold ${avatarClass(identity.keyHint)}`}>
                      {initials(identity.name)}
                    </div>
                    <div className="min-w-0">
                      <p className="font-semibold text-slate-950">{identity.name}</p>
                      <p className="mt-1 text-xs font-medium uppercase tracking-wide text-slate-500">{identity.title}</p>
                      <p className="mt-2 text-sm leading-6 text-slate-600">{identity.mission}</p>
                    </div>
                  </div>
                  <div className="mt-3 flex flex-wrap gap-2">
                    <Badge value={identity.currentMode} />
                    <Badge value={identity.scheduler} />
                  </div>
                  <div className="mt-4 grid grid-cols-3 gap-2 text-xs">
                    <SmallStat label="Logs" value={logs} />
                    <SmallStat label="Cases" value={relatedCases} />
                    <SmallStat label="Problems" value={problems} />
                  </div>
                  <div className="mt-3 grid grid-cols-2 gap-2 text-xs">
                    <SmallStat label="Coverage XP" value={metrics?.coverageXp ?? 0} />
                    <SmallStat label="Signal XP" value={metrics?.signalXp ?? 0} />
                    <SmallStat label="Learning XP" value={metrics?.learningXp ?? 0} />
                    <SmallStat label="Reliability" value={metrics ? `${metrics.reliability}%` : '0%'} />
                    <SmallStat label="Evidence Quality" value={metrics?.evidenceQuality ?? 0} />
                    <SmallStat label="Noise Penalty" value={metrics?.noisePenalty ?? 0} />
                    <SmallStat label="Review Discipline" value={metrics?.reviewDiscipline ?? 0} />
                  </div>
                  <div className="mt-4 grid gap-2 text-xs text-slate-600">
                    <p><span className="font-semibold">Watches:</span> {identity.watches.slice(0, 3).join(', ')}</p>
                    <p><span className="font-semibold">Outputs:</span> {identity.outputs.slice(0, 3).join(', ')}</p>
                    <p><span className="font-semibold">Future mode:</span> {identity.futureMode}</p>
                  </div>
                </div>
              );
            })}
          </div>
        </section>

        <div className="mb-6 flex flex-wrap gap-2">
          {SECTIONS.map(([key, label]) => (
            <a
              key={key}
              href={`#${key}`}
              className="rounded-full bg-white px-3 py-1.5 text-xs font-medium text-slate-600 ring-1 ring-slate-200 transition-colors hover:bg-slate-100 hover:text-slate-900"
            >
              {label}
            </a>
          ))}
        </div>

        {loading ? (
          <div className="rounded-lg border border-slate-200 bg-white p-8 text-center shadow-sm">
            <div className="mb-4 inline-block h-8 w-8 animate-spin rounded-full border-2 border-slate-300 border-t-slate-700" />
            <p className="text-sm text-slate-500">Loading Agent Ops...</p>
          </div>
        ) : (
          <div className="space-y-6">
            <SectionShell id="rooms" title="Rooms" subtitle="Conceptual operating areas for diagnostics and future Mission Control views." error={errors.rooms}>
              {rooms.length === 0 ? (
                <EmptyState title="No Agent Ops rooms found." description="Backend may not be deployed or seed data may be missing." />
              ) : (
                <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                  {rooms.map(room => (
                    <div key={room.id} className="rounded-lg border border-slate-200 bg-white p-4">
                      <div className="mb-3 flex items-start justify-between gap-3">
                        <div>
                          <p className="text-sm font-semibold text-slate-900">{room.name}</p>
                          <p className="mt-1 font-mono text-xs text-slate-400">{room.key}</p>
                        </div>
                        <Badge value={room.status} />
                      </div>
                      <p className="min-h-12 text-sm leading-6 text-slate-600" style={{ overflowWrap: 'anywhere' }}>{room.description ?? 'No description.'}</p>
                      <div className="mt-3 grid grid-cols-2 gap-2 text-xs md:grid-cols-4">
                        <SmallStat label="Ops Score" value={`${roomScore(roomCounts.get(room.key))}%`} />
                        <SmallStat label="Mode" value="observer" />
                        <SmallStat label="Scheduler" value="disabled" />
                        <SmallStat label="Future" value="approval required" />
                      </div>
                      <div className="mt-4 grid grid-cols-2 gap-2 border-t border-slate-100 pt-3 text-xs text-slate-500 md:grid-cols-4">
                        <span>{agentCountByRoom.get(room.key) ?? 0} agent(s)</span>
                        <span>{roomCounts.get(room.key)?.activity ?? 0} activity</span>
                        <span>{roomCounts.get(room.key)?.diagnostics ?? 0} diagnostics</span>
                        <span>{roomCounts.get(room.key)?.proposals ?? 0} proposals</span>
                      </div>
                      <div className="mt-4 flex flex-wrap items-center gap-2 rounded-md border border-slate-100 bg-slate-50 p-2">
                        {(ROOM_CHAINS[room.key] ?? [room.name]).map((name, index, chain) => (
                          <span key={`${room.key}-${name}-${index}`} className="inline-flex items-center gap-2">
                            <span className="max-w-full rounded border border-slate-200 bg-white px-2 py-1 text-xs font-medium text-slate-600" style={{ overflowWrap: 'anywhere' }}>{name}</span>
                            {index < chain.length - 1 && <span className="text-slate-300">-&gt;</span>}
                          </span>
                        ))}
                      </div>
                      <div className="mt-4 flex justify-end">
                        <Link
                          href={`/agent-ops/rooms/${room.key}`}
                          className="rounded-md border border-slate-300 bg-white px-3 py-2 text-xs font-medium text-slate-700 shadow-sm hover:bg-slate-50"
                        >
                          Open room
                        </Link>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </SectionShell>

            <SectionShell id="agents" title="Agents" subtitle="Documented operational agents. All current agents are observer/manual/assistive only." error={errors.agents}>
              {agents.length === 0 ? (
                <EmptyState title="No Agent Ops agents found." description="Seed data may not be present yet." />
              ) : (
                <div className="overflow-x-auto rounded-lg border border-slate-200">
                  <table className="min-w-full border-separate border-spacing-0">
                    <thead className="bg-slate-100">
                      <tr>{['Agent', 'Room', 'Role', 'Status', 'Implementation', 'Autonomy', 'Guardrails'].map(header => <TableHeader key={header}>{header}</TableHeader>)}</tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100 bg-white">
                      {agents.map(agent => (
                        <tr key={agent.id} className="align-top hover:bg-slate-50">
                          <td className="px-4 py-4">
                            <div className="text-sm font-semibold text-slate-900" style={{ overflowWrap: 'anywhere' }}>{agent.name}</div>
                            <div className="font-mono text-xs text-slate-400" style={{ overflowWrap: 'anywhere' }}>{agent.key}</div>
                          </td>
                          <td className="px-4 py-4 text-sm text-slate-600">{safeText(agent.room_key)}</td>
                          <td className="max-w-xs px-4 py-4 text-sm leading-6 text-slate-600">{agent.role ?? '-'}</td>
                          <td className="px-4 py-4"><Badge value={agent.status} /></td>
                          <td className="px-4 py-4"><Badge value={agent.implementation_status} /></td>
                          <td className="px-4 py-4"><Badge value={agent.autonomy_level} /></td>
                          <td className="max-w-sm px-4 py-4 text-sm leading-6 text-slate-500">{guardrailText(agent.guardrails)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
              <p className="mt-4 text-xs text-slate-500">No agent shown here has autonomous production powers. Fontana runtime is not implemented in this sprint.</p>
            </SectionShell>

            <ActivitySection items={activity} error={errors.activity} />
            <DiagnosticsSection items={diagnostics} error={errors.diagnostics} />

            <SectionShell id="proposals" title="Learning Proposals" subtitle="Human-supervised improvement proposals. Changing proposal status does not change production behavior." error={errors.proposals}>
              <div className="mb-4 rounded-lg border border-amber-200 bg-amber-50 px-4 py-3">
                <p className="text-sm text-amber-900">
                  Review actions only update proposal status and notes. They do not run code, deploy, change scanner/evaluator behavior, or apply proposals.
                </p>
              </div>
              {proposals.length === 0 ? (
                <EmptyState title="No learning proposals yet." description="Proposals will appear after diagnostics generate human-reviewed improvement ideas." />
              ) : (
                <div className="space-y-4">
                  {proposals.map(proposal => (
                    <div key={proposal.id} className="rounded-lg border border-slate-200 bg-white p-4">
                      <div className="mb-3 flex flex-wrap items-start justify-between gap-3">
                        <div>
                          <p className="text-sm font-semibold text-slate-900">{proposal.title}</p>
                          <p className="mt-1 text-xs text-slate-400">Created {formatDate(proposal.created_at)} / Updated {formatDate(proposal.updated_at)}</p>
                        </div>
                        <div className="flex gap-2">
                          <Badge value={proposal.risk_level} />
                          <Badge value={proposal.status} />
                        </div>
                      </div>
                      <div className="grid grid-cols-1 gap-3 md:grid-cols-3">
                        <ProposalText label="Problem statement" value={proposal.problem_statement} />
                        <ProposalText label="Proposed change" value={proposal.proposed_change} />
                        <ProposalText label="Expected benefit" value={proposal.expected_benefit ?? '-'} />
                      </div>
                      <div className="mt-4 grid grid-cols-1 gap-3 md:grid-cols-[1fr_auto]">
                        <input
                          value={proposalNotes[proposal.id] ?? proposal.reviewer_note ?? ''}
                          onChange={event => setProposalNotes(prev => ({ ...prev, [proposal.id]: event.target.value }))}
                          placeholder="Reviewer note"
                          className="rounded-md border border-slate-300 bg-white px-3 py-2 text-sm text-slate-700 shadow-sm focus:border-slate-500 focus:outline-none"
                        />
                        <div className="flex flex-wrap gap-2">
                          {allowedActions(proposal.status).map(action => (
                            <button
                              key={action.status}
                              onClick={() => reviewProposal(proposal, action.status)}
                              disabled={updatingProposal === proposal.id}
                              className="rounded-md border border-slate-300 bg-white px-3 py-2 text-xs font-medium text-slate-700 shadow-sm hover:bg-slate-50 disabled:opacity-60"
                            >
                              {updatingProposal === proposal.id ? 'Updating...' : action.label}
                            </button>
                          ))}
                        </div>
                      </div>
                      {proposalErrors[proposal.id] && <p className="mt-3 text-sm text-red-600">{proposalErrors[proposal.id]}</p>}
                    </div>
                  ))}
                </div>
              )}
            </SectionShell>

            <SectionShell id="scoreboard" title="Scoreboard" subtitle="Operational metrics are documented but score snapshots are deferred.">
              <PlaceholderPanel
                title="Scoreboard is not active yet."
                description="Agent score snapshots are deferred. Future metrics may include Coverage XP, Signal XP, Learning XP, Reliability Score, Evidence Quality, and Noise Penalty."
                items={['Coverage XP', 'Signal XP', 'Learning XP', 'Reliability Score', 'Evidence Quality', 'Noise Penalty']}
              />
            </SectionShell>

            <SectionShell
              id="fontana"
              title="Fontana Diagnostic Report"
              subtitle="Deterministic observer report. No autonomous changes, live AI, evaluator, scanner, or external fetch is called."
              error={errors.fontana}
            >
              {!fontanaReport ? (
                <PlaceholderPanel
                  title="Fontana report endpoint is not available yet."
                  description="Fontana remains an advisor/documenter concept only and cannot deploy, modify production, trigger scans, change cron, or enable evaluator v2."
                  items={FONTANA_SECTIONS}
                />
              ) : (
                <div className="grid gap-4 lg:grid-cols-2">
                  <div className="rounded-md border border-slate-200 bg-slate-50 p-4">
                    <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Summary</p>
                    <p className="mt-2 text-sm leading-6 text-slate-700">{fontanaReport.summary}</p>
                    <div className="mt-3 flex flex-wrap gap-2">
                      <Badge value={fontanaReport.mode} />
                      <Badge value="read-only" />
                    </div>
                  </div>
                  <div className="rounded-md border border-slate-200 bg-slate-50 p-4">
                    <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">System Health</p>
                    <ul className="mt-2 space-y-1">
                      {fontanaReport.system_health.map(item => (
                        <li key={item} className="text-sm leading-6 text-slate-700">{item}</li>
                      ))}
                    </ul>
                  </div>
                  <div className="rounded-md border border-slate-200 bg-slate-50 p-4">
                    <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Bottlenecks / Evidence Gaps</p>
                    <ul className="mt-2 space-y-1">
                      {[...fontanaReport.case_bottlenecks, ...fontanaReport.evidence_gaps].map(item => (
                        <li key={item} className="text-sm leading-6 text-slate-700">{item}</li>
                      ))}
                    </ul>
                  </div>
                  <div className="rounded-md border border-slate-200 bg-slate-50 p-4">
                    <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Next Manual Steps</p>
                    <ul className="mt-2 space-y-1">
                      {fontanaReport.recommended_manual_next_steps.map(item => (
                        <li key={item} className="text-sm leading-6 text-slate-700">{item}</li>
                      ))}
                    </ul>
                  </div>
                  <div className="rounded-md border border-slate-200 bg-slate-50 p-4 lg:col-span-2">
                    <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Guardrails</p>
                    <div className="mt-2 flex flex-wrap gap-2">
                      {fontanaReport.guardrails.map(guardrail => (
                        <Badge key={guardrail} value={guardrail} />
                      ))}
                    </div>
                  </div>
                </div>
              )}
            </SectionShell>
          </div>
        )}
      </div>
    </div>
  );
}

function AgentTimelineCard({
  title,
  subtitle,
  rows,
  empty,
}: {
  title: string;
  subtitle: string;
  rows: Array<AgentOpsActivity | AgentOpsDiagnostic>;
  empty: string;
}) {
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-sm font-semibold text-slate-950">{title}</p>
          <p className="mt-1 text-xs font-medium uppercase tracking-wide text-slate-400">{subtitle}</p>
        </div>
        <Badge value="manual" />
      </div>
      <p className="mt-3 text-sm leading-6 text-slate-600">
        Derived from loaded Agent Ops rows only. No scheduler, runtime, or autonomous case scan is active.
      </p>
      {rows.length === 0 ? (
        <p className="mt-4 rounded-md border border-slate-200 bg-slate-50 p-3 text-sm text-slate-500">{empty}</p>
      ) : (
        <div className="mt-4 space-y-2">
          {rows.map(row => {
            const href = relatedCaseHref(row.related_entity_type, row.related_entity_id);
            return (
              <div key={row.id} className="rounded-md border border-slate-200 bg-slate-50 p-3">
                <div className="flex flex-wrap items-start justify-between gap-2">
                  <p className="text-sm font-medium text-slate-900">{row.title}</p>
                  <Badge value={row.severity} />
                </div>
                <p className="mt-1 text-xs text-slate-500">{formatDate(row.created_at)}</p>
                {href ? (
                  <Link href={href} className="mt-2 inline-block text-xs font-medium text-emerald-700 hover:text-emerald-900">
                    Open related case
                  </Link>
                ) : (
                  <p className="mt-2 text-xs text-slate-500">{relatedEntity(row.related_entity_type, row.related_entity_id)}</p>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

function SmallStat({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="rounded-md border border-slate-200 bg-white px-2 py-1.5">
      <p className="font-semibold text-slate-800">{value}</p>
      <p className="mt-0.5 uppercase tracking-wide text-slate-400">{label}</p>
    </div>
  );
}

function TableHeader({ children }: { children: React.ReactNode }) {
  return <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">{children}</th>;
}

function ProposalText({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">{label}</p>
      <p className="mt-1 text-sm leading-6 text-slate-600">{value}</p>
    </div>
  );
}

function ActivitySection({ items, error }: { items: AgentOpsActivity[]; error?: string | null }) {
  return (
    <SectionShell id="activity" title="Activity Feed" subtitle="Latest Agent Ops activity rows. Logger integration is not wired into scanner/evaluator yet." error={error}>
      {items.length === 0 ? (
        <EmptyState title="No Agent Ops activity has been logged yet." description="Logger integration is not wired into scanner/evaluator yet." />
      ) : (
        <div className="overflow-x-auto rounded-lg border border-slate-200">
          <table className="min-w-full border-separate border-spacing-0">
            <thead className="bg-slate-100">
              <tr>{['Time', 'Agent', 'Room', 'Activity type', 'Title', 'Severity', 'Status', 'Related entity'].map(header => <TableHeader key={header}>{header}</TableHeader>)}</tr>
            </thead>
            <tbody className="divide-y divide-slate-100 bg-white">
              {items.map(item => (
                <tr key={item.id} className="align-top hover:bg-slate-50">
                  <td className="px-4 py-4 text-sm text-slate-500">{formatDate(item.created_at)}</td>
                  <td className="px-4 py-4 text-sm text-slate-600">{safeText(item.agent_key)}</td>
                  <td className="px-4 py-4 text-sm text-slate-600">{safeText(item.room_key)}</td>
                  <td className="px-4 py-4 text-sm text-slate-600">{formatActivityType(item.activity_type)}</td>
                  <td className="max-w-sm px-4 py-4 text-sm text-slate-800">{item.title}</td>
                  <td className="px-4 py-4"><Badge value={item.severity} /></td>
                  <td className="px-4 py-4"><Badge value={item.status} /></td>
                  <td className="px-4 py-4 text-sm text-slate-500">{relatedEntity(item.related_entity_type, item.related_entity_id)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </SectionShell>
  );
}

function DiagnosticsSection({ items, error }: { items: AgentOpsDiagnostic[]; error?: string | null }) {
  return (
    <SectionShell id="diagnostics" title="Diagnostics" subtitle="Reliability, evidence, source, routing, methodology, and workflow diagnostics." error={error}>
      {items.length === 0 ? (
        <EmptyState title="No diagnostic events yet." description="Diagnostics will appear here after Agent Ops logging is integrated." />
      ) : (
        <div className="overflow-x-auto rounded-lg border border-slate-200">
          <table className="min-w-full border-separate border-spacing-0">
            <thead className="bg-slate-100">
              <tr>{['Time', 'Severity', 'Type', 'Title', 'Description', 'Room / Agent', 'Related entity'].map(header => <TableHeader key={header}>{header}</TableHeader>)}</tr>
            </thead>
            <tbody className="divide-y divide-slate-100 bg-white">
              {items.map(item => (
                <tr key={item.id} className="align-top hover:bg-slate-50">
                  <td className="px-4 py-4 text-sm text-slate-500">{formatDate(item.created_at)}</td>
                  <td className="px-4 py-4"><Badge value={item.severity} /></td>
                  <td className="px-4 py-4 text-sm text-slate-600">{formatDiagnosticType(item.diagnostic_type)}</td>
                  <td className="max-w-xs px-4 py-4 text-sm font-medium text-slate-800">{item.title}</td>
                  <td className="max-w-md px-4 py-4 text-sm leading-6 text-slate-600">{item.description ?? '-'}</td>
                  <td className="px-4 py-4 text-sm text-slate-500">{safeText(item.room_key)} / {safeText(item.agent_key)}</td>
                  <td className="px-4 py-4 text-sm text-slate-500">{relatedEntity(item.related_entity_type, item.related_entity_id)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </SectionShell>
  );
}
