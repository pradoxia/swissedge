'use client';

import { useEffect, useMemo, useState } from 'react';
import type { ReactNode } from 'react';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import {
  fetchAgentOpsActivity,
  fetchAgentOpsAgents,
  fetchAgentOpsDiagnostics,
  fetchAgentOpsProposals,
  fetchAgentOpsRooms,
  type AgentOpsActivity,
  type AgentOpsAgent,
  type AgentOpsDiagnostic,
  type AgentOpsProposal,
  type AgentOpsRoom,
} from '@/lib/api';

type AgentMetrics = {
  coverageXp: number;
  signalXp: number;
  learningXp: number;
  reliability: number;
  evidenceQuality: number;
  noisePenalty: number;
  reviewDiscipline: number;
};

const ROOM_CHAINS: Record<string, string[]> = {
  radar_room: ['Edgar Scout', 'Router Analyst', 'Signal Filter', 'Quality Sentinel', 'Fontana'],
  evidence_lab: ['Resource Scout', 'Official Source Finder', 'Pattern Analyst', 'Evidence Mapper', 'Missing Evidence Hunter', 'Quality Sentinel', 'Playbook Scribe'],
  research_desk: ['Case Builder', 'Case Completion Coach', 'Missing Evidence Hunter', 'Intelligence Scorer', 'Fontana'],
  quality_court: ['Quality Sentinel', 'Risk Discipline Checker', 'Human Review Gate', 'Fontana'],
  playbook_workshop: ['Playbook Scribe', 'Coverage Analyst', 'Drift Watcher', 'Fontana'],
  agent_ops: ['Agent Ops Registry', 'Activity Logger', 'Diagnostics Reader', 'Fontana'],
};

const AVATAR_COLORS = [
  'border-cyan-200 bg-cyan-50 text-cyan-800',
  'border-blue-200 bg-blue-50 text-blue-800',
  'border-indigo-200 bg-indigo-50 text-indigo-800',
  'border-teal-200 bg-teal-50 text-teal-800',
  'border-slate-200 bg-slate-100 text-slate-700',
];

type AgentIdentity = {
  name: string;
  keyHint: string;
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
    title: 'CTO / Project Governor',
    mission: 'Summarizes project diagnostics, operational status, and future sprint options without runtime authority.',
    watches: ['Agent Ops diagnostics', 'project state docs', 'review posture'],
    outputs: ['project diagnostics', 'next sprint options', 'operational status'],
    currentMode: 'documented observer',
    futureMode: 'reporting only after approval',
    scheduler: 'disabled in this sprint',
  },
];

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

function formatLabel(value: string | null | undefined): string {
  if (!value) return '-';
  return value.replace(/_/g, ' ').replace(/\s+/g, ' ').trim().replace(/^./, first => first.toUpperCase());
}

function badgeClass(value: string): string {
  const normalized = value.toLowerCase();
  if (['active', 'success', 'completed', 'implemented', 'accepted'].includes(normalized)) {
    return 'border-emerald-200 bg-emerald-50 text-emerald-700';
  }
  if (['warning', 'deferred', 'manual', 'assistive'].includes(normalized)) {
    return 'border-amber-200 bg-amber-50 text-amber-800';
  }
  if (['error', 'failed', 'rejected', 'critical'].includes(normalized)) {
    return 'border-red-200 bg-red-50 text-red-700';
  }
  if (['observer', 'documented', 'planned', 'proposed'].includes(normalized)) {
    return 'border-blue-200 bg-blue-50 text-blue-700';
  }
  return 'border-slate-200 bg-slate-50 text-slate-600';
}

function Badge({ value }: { value: string }) {
  return (
    <span className={`inline-flex max-w-full items-center rounded-full border px-2 py-0.5 text-left text-[11px] font-medium leading-4 ${badgeClass(value)}`} style={{ overflowWrap: 'anywhere' }}>
      {formatLabel(value)}
    </span>
  );
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

function guardrailText(value: AgentOpsAgent['guardrails']): string {
  if (Array.isArray(value)) return value.join(', ');
  if (typeof value === 'string') return value;
  if (value && typeof value === 'object') return Object.values(value).map(String).join(', ');
  return 'No autonomous production powers';
}

function identityForAgent(agent: AgentOpsAgent): AgentIdentity {
  const haystack = `${agent.key} ${agent.name} ${agent.role ?? ''}`.toLowerCase();
  return AGENT_IDENTITIES.find(identity => haystack.includes(identity.keyHint)) ?? {
    name: agent.name,
    keyHint: agent.key,
    title: 'Manual observer',
    mission: agent.role ?? 'Observer/manual role documented in Agent Ops.',
    watches: ['loaded Agent Ops rows', 'manual review state'],
    outputs: ['activity rows', 'diagnostics when present'],
    currentMode: agent.autonomy_level || 'observer-only',
    futureMode: 'manual-approved sprint required',
    scheduler: 'disabled in this sprint',
  };
}

function relatedLink(type?: string | null, id?: string | null) {
  if (!type || !id) return <span>-</span>;
  const normalized = type.toLowerCase();
  if (normalized.includes('research')) {
    return <Link href={`/investment/research/${id}`} className="text-cyan-700 hover:text-cyan-900">ResearchCase {id.slice(0, 8)}</Link>;
  }
  if (normalized.includes('situation')) {
    return <Link href={`/investment/situations/${id}`} className="text-cyan-700 hover:text-cyan-900">SpecialSituation {id.slice(0, 8)}</Link>;
  }
  return <span>{type}:{id.slice(0, 8)}</span>;
}

function isCaseRelated(type?: string | null): boolean {
  const normalized = (type ?? '').toLowerCase();
  return normalized.includes('researchcase') || normalized.includes('research_case') || normalized.includes('specialsituation') || normalized.includes('special_situation') || normalized.includes('research') || normalized.includes('situation');
}

function caseRelatedCount(activity: AgentOpsActivity[], diagnostics: AgentOpsDiagnostic[]): number {
  return activity.filter(item => isCaseRelated(item.related_entity_type)).length + diagnostics.filter(item => isCaseRelated(item.related_entity_type)).length;
}

function computeMetrics(
  agent: AgentOpsAgent,
  activity: AgentOpsActivity[],
  diagnostics: AgentOpsDiagnostic[],
  proposals: AgentOpsProposal[],
): AgentMetrics {
  const agentActivity = activity.filter(item => item.agent_key === agent.key);
  const agentDiagnostics = diagnostics.filter(item => item.agent_key === agent.key);
  const agentProposals = proposals.filter(item => item.agent_key === agent.key);
  const successCount = agentActivity.filter(item => ['success', 'completed'].includes(item.status) || item.severity === 'success').length;
  const evidenceRows = agentActivity.filter(item => `${item.activity_type} ${item.title} ${item.summary ?? ''}`.toLowerCase().includes('evidence')).length;
  const severeDiagnostics = agentDiagnostics.filter(item => ['warning', 'error', 'critical'].includes(item.severity)).length;
  const reviewedProposals = agentProposals.filter(item => item.reviewed_at || ['accepted', 'rejected', 'deferred', 'implemented', 'archived'].includes(item.status)).length;
  const safeActivity = agentActivity.filter(item => `${item.title} ${item.summary ?? ''}`.toLowerCase().includes('manual') || `${item.title} ${item.summary ?? ''}`.toLowerCase().includes('guardrail')).length;
  const reliability = Math.max(0, Math.min(100, 100 - severeDiagnostics * 15 + successCount * 3));

  return {
    coverageXp: agentActivity.length * 10,
    signalXp: successCount * 10,
    learningXp: (reviewedProposals + agentDiagnostics.length) * 10,
    reliability,
    evidenceQuality: Math.min(100, evidenceRows * 15 + successCount * 5),
    noisePenalty: severeDiagnostics * 10,
    reviewDiscipline: Math.min(100, safeActivity * 20 + reviewedProposals * 10),
  };
}

function lastActivityFor(agent: AgentOpsAgent, activity: AgentOpsActivity[]): string | null {
  return activity.find(item => item.agent_key === agent.key)?.created_at ?? null;
}

export default function AgentOpsRoomDetailPage() {
  const params = useParams();
  const roomId = String(params.id ?? '');

  const [rooms, setRooms] = useState<AgentOpsRoom[]>([]);
  const [agents, setAgents] = useState<AgentOpsAgent[]>([]);
  const [activity, setActivity] = useState<AgentOpsActivity[]>([]);
  const [diagnostics, setDiagnostics] = useState<AgentOpsDiagnostic[]>([]);
  const [proposals, setProposals] = useState<AgentOpsProposal[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [loadErrors, setLoadErrors] = useState<Record<string, string | null>>({});
  const [selectedAgentKey, setSelectedAgentKey] = useState<string | null>(null);

  const room = useMemo(
    () => rooms.find(item => item.key === roomId || item.id === roomId) ?? null,
    [roomId, rooms],
  );

  async function load() {
    setLoading(true);
    setError(null);
    setLoadErrors({});
    try {
      const roomsData = await fetchAgentOpsRooms();
      const foundRoom = roomsData.rooms.find(item => item.key === roomId || item.id === roomId);
      setRooms(roomsData.rooms);
      if (!foundRoom) {
        setAgents([]);
        setActivity([]);
        setDiagnostics([]);
        setProposals([]);
        setLoadErrors({});
        setError('Agent Ops room not found');
        return;
      }
      const [agentsResult, activityResult, diagnosticsResult, proposalsResult] = await Promise.allSettled([
        fetchAgentOpsAgents({ room_key: foundRoom.key }),
        fetchAgentOpsActivity({ room_key: foundRoom.key, limit: 100 }),
        fetchAgentOpsDiagnostics({ room_key: foundRoom.key, limit: 100 }),
        fetchAgentOpsProposals({ room_key: foundRoom.key, limit: 100 }),
      ]);
      const nextErrors: Record<string, string | null> = {};
      const nextAgents = agentsResult.status === 'fulfilled' ? agentsResult.value.agents : [];
      const nextActivity = activityResult.status === 'fulfilled' ? activityResult.value.items : [];
      const nextDiagnostics = diagnosticsResult.status === 'fulfilled' ? diagnosticsResult.value.items : [];
      const nextProposals = proposalsResult.status === 'fulfilled' ? proposalsResult.value.items : [];

      if (agentsResult.status === 'rejected') nextErrors.agents = agentsResult.reason instanceof Error ? agentsResult.reason.message : 'Failed to load room agents';
      if (activityResult.status === 'rejected') nextErrors.activity = activityResult.reason instanceof Error ? activityResult.reason.message : 'Failed to load room activity';
      if (diagnosticsResult.status === 'rejected') nextErrors.diagnostics = diagnosticsResult.reason instanceof Error ? diagnosticsResult.reason.message : 'Failed to load room diagnostics';
      if (proposalsResult.status === 'rejected') nextErrors.proposals = proposalsResult.reason instanceof Error ? proposalsResult.reason.message : 'Failed to load room proposals';

      setAgents(nextAgents);
      setActivity(nextActivity);
      setDiagnostics(nextDiagnostics);
      setProposals(nextProposals);
      setLoadErrors(nextErrors);
      setSelectedAgentKey(prev => (prev && nextAgents.some(agent => agent.key === prev)) ? prev : nextAgents[0]?.key ?? null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load Agent Ops room');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, [roomId]);

  const selectedAgent = agents.find(agent => agent.key === selectedAgentKey) ?? agents[0] ?? null;
  const selectedActivity = selectedAgent ? activity.filter(item => item.agent_key === selectedAgent.key) : [];
  const selectedDiagnostics = selectedAgent ? diagnostics.filter(item => item.agent_key === selectedAgent.key) : [];
  const roomChain = room ? ROOM_CHAINS[room.key] ?? agents.map(agent => agent.name) : [];
  const totalSevereDiagnostics = diagnostics.filter(item => ['warning', 'error', 'critical'].includes(item.severity)).length;
  const roomReliability = Math.max(0, Math.min(100, 100 - totalSevereDiagnostics * 12 + activity.filter(item => item.severity === 'success').length * 3));
  const secondaryLoadErrors = Object.entries(loadErrors).filter(([, message]) => Boolean(message));

  return (
    <div className="min-h-screen bg-slate-50 p-6 text-slate-900 md:p-8">
      <div className="mx-auto max-w-7xl">
        <nav className="mb-8 flex flex-wrap items-center gap-x-4 gap-y-2 text-sm">
          <Link href="/" className="font-medium text-slate-500 hover:text-slate-900">Mission Control</Link>
          <span className="text-slate-300">/</span>
          <Link href="/agent-ops" className="font-medium text-slate-500 hover:text-slate-900">Agent Ops</Link>
          <span className="text-slate-300">/</span>
          <span className="font-medium text-slate-900">{room?.name ?? roomId}</span>
        </nav>

        {loading ? (
          <div className="rounded-lg border border-slate-200 bg-white p-8 text-center shadow-sm">
            <div className="mb-4 inline-block h-8 w-8 animate-spin rounded-full border-2 border-slate-300 border-t-slate-700" />
            <p className="text-sm text-slate-500">Loading Agent Ops room...</p>
          </div>
        ) : error || !room ? (
          <div className="rounded-lg border border-red-200 bg-red-50 p-5 text-sm text-red-800">{error ?? 'Agent Ops room not found'}</div>
        ) : (
          <div className="space-y-6">
            {secondaryLoadErrors.length > 0 && (
              <section className="rounded-lg border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">
                <p className="font-semibold">Some Agent Ops room panels did not load.</p>
                <ul className="mt-2 list-disc space-y-1 pl-5">
                  {secondaryLoadErrors.map(([key, message]) => (
                    <li key={key}>{formatLabel(key)}: {message}</li>
                  ))}
                </ul>
              </section>
            )}

            <section className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
              <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
                <div>
                  <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-500">Agent Room</p>
                  <h1 className="text-3xl font-semibold tracking-tight text-slate-950">{room.name}</h1>
                  <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-600">{room.description ?? 'No room description.'}</p>
                  <div className="mt-4 flex flex-wrap gap-2">
                    <Badge value={room.status} />
                    <Badge value="read-only" />
                    <Badge value="manual review required" />
                    <Badge value="scheduler disabled" />
                  </div>
                </div>
                <button
                  type="button"
                  onClick={load}
                  className="rounded-md border border-slate-300 bg-white px-3 py-2 text-xs font-medium text-slate-700 shadow-sm hover:bg-slate-50"
                >
                  Refresh room
                </button>
              </div>

              <div className="mt-6 grid grid-cols-2 gap-3 md:grid-cols-6">
                <MetricBox label="Agents" value={agents.length} />
                <MetricBox label="Activity" value={activity.length} />
                <MetricBox label="Diagnostics" value={diagnostics.length} />
                <MetricBox label="Proposals" value={proposals.length} />
                <MetricBox label="Reliability" value={`${roomReliability}%`} />
                <MetricBox label="Mode" value="Observer" />
              </div>
              <div className="mt-4 grid gap-3 text-sm md:grid-cols-3">
                <div className="rounded-md border border-slate-200 bg-slate-50 p-3">
                  <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Current mode</p>
                  <p className="mt-1 text-slate-700">observer-only / manual-review</p>
                </div>
                <div className="rounded-md border border-slate-200 bg-slate-50 p-3">
                  <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Scheduler posture</p>
                  <p className="mt-1 text-slate-700">disabled in this sprint; future approved sprint required</p>
                </div>
                <div className="rounded-md border border-slate-200 bg-slate-50 p-3">
                  <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Guardrail status</p>
                  <p className="mt-1 text-slate-700">no autonomous execution, no scanner/evaluator runtime connection</p>
                </div>
              </div>
            </section>

            <section className="rounded-lg border border-blue-200 bg-blue-50 p-4 shadow-sm">
              <p className="text-sm font-semibold text-blue-950">Operational indicators only</p>
              <p className="mt-1 text-sm leading-6 text-blue-900">
                XP and reliability numbers are deterministic read-only indicators derived from Agent Ops rows loaded on this page.
                They are not persisted, not performance guarantees, and do not imply autonomous execution.
              </p>
            </section>

            <section className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
              <SectionTitle title="Agent Interaction Map" subtitle="Conceptual workflow only. Logs are required before treating an interaction as executed." />
              <div className="mt-4 flex flex-wrap items-center gap-2">
                {roomChain.map((name, index) => (
                  <div key={`${name}-${index}`} className="flex items-center gap-2">
                    <div className="max-w-full rounded-md border border-slate-200 bg-slate-50 px-3 py-2 text-sm font-medium text-slate-700" style={{ overflowWrap: 'anywhere' }}>{name}</div>
                    {index < roomChain.length - 1 && <span className="text-slate-300">-&gt;</span>}
                  </div>
                ))}
              </div>
            </section>

            <section className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
              <SectionTitle title="Agents In This Room" subtitle="Visual identities are deterministic CSS placeholders. No external images are fetched." />
              {agents.length === 0 ? (
                <EmptyPanel title="No agents in this room yet." description="Seed data may not include agents for this room." />
              ) : (
                <div className="mt-4 grid grid-cols-1 gap-4 lg:grid-cols-2">
                  {agents.map(agent => {
                    const metrics = computeMetrics(agent, activity, diagnostics, proposals);
                    const agentActivity = activity.filter(item => item.agent_key === agent.key);
                    const agentDiagnostics = diagnostics.filter(item => item.agent_key === agent.key);
                    const identity = identityForAgent(agent);
                    return (
                      <button
                        type="button"
                        key={agent.id}
                        onClick={() => setSelectedAgentKey(agent.key)}
                        className={`rounded-lg border bg-white p-4 text-left shadow-sm transition-colors hover:border-cyan-300 ${selectedAgent?.key === agent.key ? 'border-cyan-400 ring-1 ring-cyan-200' : 'border-slate-200'}`}
                      >
                        <div className="flex items-start gap-4">
                          <div className={`flex h-12 w-12 shrink-0 items-center justify-center rounded-lg border font-semibold ${avatarClass(agent.key)}`}>
                            {initials(agent.name)}
                          </div>
                          <div className="min-w-0 flex-1">
                            <div className="flex flex-wrap items-center gap-2">
                              <p className="font-semibold text-slate-950" style={{ overflowWrap: 'anywhere' }}>{identity.name}</p>
                              <Badge value={agent.status} />
                            </div>
                            <p className="mt-1 font-mono text-xs text-slate-400" style={{ overflowWrap: 'anywhere' }}>{agent.key}</p>
                            <p className="mt-1 text-xs font-medium uppercase tracking-wide text-slate-500" style={{ overflowWrap: 'anywhere' }}>{identity.title}</p>
                            <p className="mt-2 text-sm leading-6 text-slate-600" style={{ overflowWrap: 'anywhere' }}>{identity.mission}</p>
                          </div>
                        </div>
                        <div className="mt-3 grid gap-2 text-xs text-slate-600 md:grid-cols-2">
                          <p><span className="font-semibold">Watches:</span> {identity.watches.slice(0, 3).join(', ')}</p>
                          <p><span className="font-semibold">Outputs:</span> {identity.outputs.slice(0, 3).join(', ')}</p>
                          <p><span className="font-semibold">Mode:</span> {identity.currentMode}</p>
                          <p><span className="font-semibold">Scheduler:</span> {identity.scheduler}</p>
                        </div>
                        <div className="mt-4 grid grid-cols-2 gap-2 text-xs md:grid-cols-4">
                          <SmallMetric label="Activity" value={agentActivity.length} />
                          <SmallMetric label="Last" value={formatDate(lastActivityFor(agent, activity))} />
                          <SmallMetric label="Diagnostics" value={agentDiagnostics.length} />
                          <SmallMetric label="Case rows" value={caseRelatedCount(agentActivity, agentDiagnostics)} />
                        </div>
                        <div className="mt-3 grid grid-cols-2 gap-2 text-xs md:grid-cols-4">
                          <SmallMetric label="Coverage XP" value={metrics.coverageXp} />
                          <SmallMetric label="Signal XP" value={metrics.signalXp} />
                          <SmallMetric label="Learning XP" value={metrics.learningXp} />
                          <SmallMetric label="Noise Penalty" value={metrics.noisePenalty} />
                          <SmallMetric label="Evidence Quality" value={metrics.evidenceQuality} />
                          <SmallMetric label="Review Discipline" value={metrics.reviewDiscipline} />
                        </div>
                      </button>
                    );
                  })}
                </div>
              )}
            </section>

            {selectedAgent && (
              <section className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
                <SectionTitle title="Selected Agent Detail" subtitle="Expandable detail is read-only. Display-name and avatar editing are deferred until a safe profile customization endpoint exists." />
                <div className="mt-4 grid grid-cols-1 gap-5 lg:grid-cols-[320px_1fr]">
                  <div className="rounded-lg border border-slate-200 bg-slate-50 p-4">
                    {(() => {
                      const identity = identityForAgent(selectedAgent);
                      return (
                        <>
                    <div className="flex items-center gap-4">
                      <div className={`flex h-16 w-16 items-center justify-center rounded-lg border text-lg font-semibold ${avatarClass(selectedAgent.key)}`}>
                        {initials(identity.name)}
                      </div>
                      <div>
                        <p className="font-semibold text-slate-950" style={{ overflowWrap: 'anywhere' }}>{identity.name}</p>
                        <p className="mt-1 text-xs font-medium uppercase tracking-wide text-slate-500" style={{ overflowWrap: 'anywhere' }}>{identity.title}</p>
                        <p className="font-mono text-xs text-slate-400" style={{ overflowWrap: 'anywhere' }}>{selectedAgent.key}</p>
                      </div>
                    </div>
                    <div className="mt-4 space-y-3 text-sm text-slate-600">
                      <InfoRow label="Mission" value={identity.mission} />
                      <InfoRow label="Room" value={selectedAgent.room_key ?? room.key} />
                      <InfoRow label="Current mode" value={identity.currentMode} />
                      <InfoRow label="Future mode" value={identity.futureMode} />
                      <InfoRow label="Scheduler" value={identity.scheduler} />
                      <InfoRow label="Implementation" value={selectedAgent.implementation_status} />
                      <InfoRow label="Guardrails" value={guardrailText(selectedAgent.guardrails)} />
                    </div>
                    <div className="mt-4 grid gap-3 text-sm">
                      <InfoList label="Input signals" values={identity.watches} />
                      <InfoList label="Output artifacts" values={identity.outputs} />
                    </div>
                    {identity.name === 'Missing Evidence Hunter' && (
                      <div className="mt-4 rounded-md border border-emerald-200 bg-emerald-50 p-3 text-xs leading-5 text-emerald-900">
                        Next manual research actions: review missing required resources, check candidate-only resources, inspect rejected/noisy sources, and copy stored search suggestions from case pages.
                      </div>
                    )}
                    <div className="mt-4 rounded-md border border-slate-200 bg-white p-3 text-xs leading-5 text-slate-500">
                      Editable names and avatars planned for a future safe profile customization sprint.
                    </div>
                        </>
                      );
                    })()}
                  </div>

                  <div className="space-y-5">
                    <AgentActivityPanel activity={selectedActivity} />
                    <AgentDiagnosticsPanel diagnostics={selectedDiagnostics} />
                    <RelatedObjectsPanel activity={selectedActivity} diagnostics={selectedDiagnostics} />
                    <AgentTimelineRelevancePanel activity={selectedActivity} diagnostics={selectedDiagnostics} />
                  </div>
                </div>
              </section>
            )}

            <section className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
              <SectionTitle title="Problems Found" subtitle="Diagnostics are grouped at room level and stay read-only." />
              {diagnostics.length === 0 ? (
                <EmptyPanel title="No diagnostics in this room." description="Problems and warnings will appear here when Agent Ops rows exist." />
              ) : (
                <div className="mt-4 overflow-x-auto rounded-lg border border-slate-200">
                  <table className="min-w-full border-separate border-spacing-0">
                    <thead className="bg-slate-100">
                      <tr>{['Time', 'Agent', 'Severity', 'Type', 'Message', 'Related object'].map(header => <TableHeader key={header}>{header}</TableHeader>)}</tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100 bg-white">
                      {diagnostics.map(item => (
                        <tr key={item.id} className="align-top hover:bg-slate-50">
                          <td className="px-4 py-4 text-sm text-slate-500">{formatDate(item.created_at)}</td>
                          <td className="px-4 py-4 text-sm text-slate-600">{safeText(item.agent_key)}</td>
                          <td className="px-4 py-4"><Badge value={item.severity} /></td>
                          <td className="px-4 py-4 text-sm text-slate-600">{formatLabel(item.diagnostic_type)}</td>
                          <td className="max-w-md px-4 py-4 text-sm leading-6 text-slate-700">{item.title}{item.description ? ` - ${item.description}` : ''}</td>
                          <td className="px-4 py-4 text-sm text-slate-500">{relatedLink(item.related_entity_type, item.related_entity_id)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </section>
          </div>
        )}
      </div>
    </div>
  );
}

function SectionTitle({ title, subtitle }: { title: string; subtitle: string }) {
  return (
    <div>
      <h2 className="text-sm font-semibold text-slate-950">{title}</h2>
      <p className="mt-1 text-sm leading-6 text-slate-500">{subtitle}</p>
    </div>
  );
}

function MetricBox({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="rounded-lg border border-slate-200 bg-slate-50 p-3">
      <p className="text-lg font-semibold text-slate-950">{value}</p>
      <p className="mt-1 text-xs font-medium uppercase tracking-wide text-slate-500">{label}</p>
    </div>
  );
}

function SmallMetric({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="rounded-md border border-slate-200 bg-slate-50 px-2 py-1.5">
      <p className="font-semibold text-slate-800">{value}</p>
      <p className="mt-0.5 uppercase tracking-wide text-slate-400">{label}</p>
    </div>
  );
}

function InfoRow({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">{label}</p>
      <p className="mt-1 leading-6 text-slate-700">{value}</p>
    </div>
  );
}

function InfoList({ label, values }: { label: string; values: string[] }) {
  return (
    <div>
      <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">{label}</p>
      <div className="mt-2 flex flex-wrap gap-2">
        {values.map(value => (
          <span key={value} className="rounded-md border border-slate-200 bg-white px-2 py-1 text-xs text-slate-600">{value}</span>
        ))}
      </div>
    </div>
  );
}

function EmptyPanel({ title, description }: { title: string; description: string }) {
  return (
    <div className="mt-4 rounded-lg border border-slate-200 bg-slate-50 p-6 text-center">
      <p className="text-sm font-semibold text-slate-700">{title}</p>
      <p className="mt-2 text-sm text-slate-500">{description}</p>
    </div>
  );
}

function TableHeader({ children }: { children: ReactNode }) {
  return <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">{children}</th>;
}

function AgentActivityPanel({ activity }: { activity: AgentOpsActivity[] }) {
  return (
    <div>
      <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Recent logs by agent</p>
      {activity.length === 0 ? (
        <p className="mt-2 text-sm text-slate-500">No activity rows for this agent yet.</p>
      ) : (
        <div className="mt-3 space-y-2">
          {activity.slice(0, 8).map(item => (
            <div key={item.id} className="rounded-md border border-slate-200 bg-white p-3">
              <div className="flex flex-wrap items-start justify-between gap-2">
                <div>
                  <p className="text-sm font-medium text-slate-900">{item.title}</p>
                  <p className="mt-1 text-xs text-slate-400">{formatDate(item.created_at)} / {formatLabel(item.activity_type)}</p>
                </div>
                <Badge value={item.severity} />
              </div>
              {item.summary && <p className="mt-2 text-sm leading-6 text-slate-600">{item.summary}</p>}
              <p className="mt-2 text-xs text-slate-500">Related: {relatedLink(item.related_entity_type, item.related_entity_id)}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function AgentDiagnosticsPanel({ diagnostics }: { diagnostics: AgentOpsDiagnostic[] }) {
  return (
    <div>
      <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Diagnostics / warnings</p>
      {diagnostics.length === 0 ? (
        <p className="mt-2 text-sm text-slate-500">No diagnostics for this agent.</p>
      ) : (
        <div className="mt-3 space-y-2">
          {diagnostics.slice(0, 6).map(item => (
            <div key={item.id} className="rounded-md border border-slate-200 bg-white p-3">
              <div className="flex flex-wrap items-start justify-between gap-2">
                <p className="text-sm font-medium text-slate-900">{item.title}</p>
                <Badge value={item.severity} />
              </div>
              {item.description && <p className="mt-2 text-sm leading-6 text-slate-600">{item.description}</p>}
              <p className="mt-2 text-xs text-slate-500">{formatDate(item.created_at)} / {relatedLink(item.related_entity_type, item.related_entity_id)}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function RelatedObjectsPanel({
  activity,
  diagnostics,
}: {
  activity: AgentOpsActivity[];
  diagnostics: AgentOpsDiagnostic[];
}) {
  const rows = [...activity, ...diagnostics]
    .filter(item => item.related_entity_type && item.related_entity_id)
    .map(item => ({
      type: item.related_entity_type,
      id: item.related_entity_id,
    }));
  const uniqueRows = Array.from(new Map(rows.map(row => [`${row.type}:${row.id}`, row])).values());

  return (
    <div>
      <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Related cases / situations</p>
      {uniqueRows.length === 0 ? (
        <p className="mt-2 text-sm text-slate-500">No related ResearchCases or SpecialSituations recorded for this agent yet.</p>
      ) : (
        <div className="mt-3 flex flex-wrap gap-2">
          {uniqueRows.map(row => (
            <span key={`${row.type}:${row.id}`} className="rounded-md border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-600">
              {relatedLink(row.type, row.id)}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}

function AgentTimelineRelevancePanel({
  activity,
  diagnostics,
}: {
  activity: AgentOpsActivity[];
  diagnostics: AgentOpsDiagnostic[];
}) {
  const rows = [...activity, ...diagnostics]
    .filter(item => isCaseRelated(item.related_entity_type) && item.related_entity_id)
    .slice(0, 6);

  return (
    <div>
      <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Case timeline relevance</p>
      <p className="mt-2 text-sm leading-6 text-slate-500">
        These rows can help explain why a case timeline shows agent/process context. They are derived from existing Agent Ops rows only.
      </p>
      {rows.length === 0 ? (
        <p className="mt-2 text-sm text-slate-500">No case-related timeline rows loaded for this agent.</p>
      ) : (
        <div className="mt-3 space-y-2">
          {rows.map(item => (
            <div key={item.id} className="rounded-md border border-slate-200 bg-white p-3">
              <div className="flex flex-wrap items-start justify-between gap-2">
                <p className="text-sm font-medium text-slate-900">{item.title}</p>
                <Badge value={item.severity} />
              </div>
              <p className="mt-1 text-xs text-slate-500">{formatDate(item.created_at)} / {relatedLink(item.related_entity_type, item.related_entity_id)}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
