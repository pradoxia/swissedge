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
  radar_room: ['Edgar Scout', 'Router Analyst', 'Quality Sentinel', 'Fontana'],
  evidence_lab: ['Resource Scout', 'Evidence Mapper', 'Quality Sentinel', 'Playbook Scribe'],
  research_desk: ['Case Builder', 'Evaluation Prep Assistant', 'Intelligence Scorer', 'Fontana'],
  quality_court: ['Quality Sentinel', 'Router Analyst', 'Playbook Scribe', 'Fontana'],
  playbook_workshop: ['Playbook Scribe', 'Router Analyst', 'Quality Sentinel', 'Fontana'],
  agent_ops: ['Agent Ops Registry', 'Activity Logger', 'Diagnostics Reader', 'Fontana'],
};

const AVATAR_COLORS = [
  'border-cyan-200 bg-cyan-50 text-cyan-800',
  'border-blue-200 bg-blue-50 text-blue-800',
  'border-indigo-200 bg-indigo-50 text-indigo-800',
  'border-teal-200 bg-teal-50 text-teal-800',
  'border-slate-200 bg-slate-100 text-slate-700',
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
    <span className={`inline-flex items-center rounded-full border px-2 py-0.5 text-[11px] font-medium ${badgeClass(value)}`}>
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
  const [selectedAgentKey, setSelectedAgentKey] = useState<string | null>(null);

  const room = useMemo(
    () => rooms.find(item => item.key === roomId || item.id === roomId) ?? null,
    [roomId, rooms],
  );

  async function load() {
    setLoading(true);
    setError(null);
    try {
      const roomsData = await fetchAgentOpsRooms();
      const foundRoom = roomsData.rooms.find(item => item.key === roomId || item.id === roomId);
      setRooms(roomsData.rooms);
      if (!foundRoom) {
        setAgents([]);
        setActivity([]);
        setDiagnostics([]);
        setProposals([]);
        setError('Agent Ops room not found');
        return;
      }
      const [agentsData, activityData, diagnosticsData, proposalsData] = await Promise.all([
        fetchAgentOpsAgents({ room_key: foundRoom.key }),
        fetchAgentOpsActivity({ room_key: foundRoom.key, limit: 100 }),
        fetchAgentOpsDiagnostics({ room_key: foundRoom.key, limit: 100 }),
        fetchAgentOpsProposals({ room_key: foundRoom.key, limit: 100 }),
      ]);
      setAgents(agentsData.agents);
      setActivity(activityData.items);
      setDiagnostics(diagnosticsData.items);
      setProposals(proposalsData.items);
      setSelectedAgentKey(prev => prev ?? agentsData.agents[0]?.key ?? null);
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
            </section>

            <section className="rounded-lg border border-blue-200 bg-blue-50 p-4 shadow-sm">
              <p className="text-sm font-semibold text-blue-950">Operational indicators only</p>
              <p className="mt-1 text-sm leading-6 text-blue-900">
                XP and reliability numbers are deterministic read-only indicators derived from Agent Ops rows loaded on this page.
                They are not persisted, not performance guarantees, and do not imply autonomous execution.
              </p>
            </section>

            <section className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
              <SectionTitle title="Agent Interaction Map" subtitle="Conceptual chain only. Logs are required before treating any interaction as executed." />
              <div className="mt-4 flex flex-wrap items-center gap-2">
                {roomChain.map((name, index) => (
                  <div key={`${name}-${index}`} className="flex items-center gap-2">
                    <div className="rounded-md border border-slate-200 bg-slate-50 px-3 py-2 text-sm font-medium text-slate-700">{name}</div>
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
                              <p className="font-semibold text-slate-950">{agent.name}</p>
                              <Badge value={agent.status} />
                            </div>
                            <p className="mt-1 font-mono text-xs text-slate-400">{agent.key}</p>
                            <p className="mt-2 text-sm leading-6 text-slate-600">{agent.role ?? 'No role documented.'}</p>
                          </div>
                        </div>
                        <div className="mt-4 grid grid-cols-2 gap-2 text-xs md:grid-cols-4">
                          <SmallMetric label="Activity" value={agentActivity.length} />
                          <SmallMetric label="Last" value={formatDate(lastActivityFor(agent, activity))} />
                          <SmallMetric label="Diagnostics" value={agentDiagnostics.length} />
                          <SmallMetric label="Reliability" value={`${metrics.reliability}%`} />
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
                    <div className="flex items-center gap-4">
                      <div className={`flex h-16 w-16 items-center justify-center rounded-lg border text-lg font-semibold ${avatarClass(selectedAgent.key)}`}>
                        {initials(selectedAgent.name)}
                      </div>
                      <div>
                        <p className="font-semibold text-slate-950">{selectedAgent.name}</p>
                        <p className="font-mono text-xs text-slate-400">{selectedAgent.key}</p>
                      </div>
                    </div>
                    <div className="mt-4 space-y-3 text-sm text-slate-600">
                      <InfoRow label="Room" value={selectedAgent.room_key ?? room.key} />
                      <InfoRow label="Autonomy" value={selectedAgent.autonomy_level} />
                      <InfoRow label="Implementation" value={selectedAgent.implementation_status} />
                      <InfoRow label="Guardrails" value={guardrailText(selectedAgent.guardrails)} />
                    </div>
                    <div className="mt-4 rounded-md border border-slate-200 bg-white p-3 text-xs leading-5 text-slate-500">
                      Editable names and avatars planned for a future safe profile customization sprint.
                    </div>
                  </div>

                  <div className="space-y-5">
                    <AgentActivityPanel activity={selectedActivity} />
                    <AgentDiagnosticsPanel diagnostics={selectedDiagnostics} />
                    <RelatedObjectsPanel activity={selectedActivity} diagnostics={selectedDiagnostics} />
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
