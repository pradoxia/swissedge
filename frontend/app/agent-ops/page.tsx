'use client';

import { useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import {
  fetchAgentOpsActivity,
  fetchAgentOpsAgents,
  fetchAgentOpsDiagnostics,
  fetchAgentOpsProposals,
  fetchAgentOpsRooms,
  updateAgentOpsProposal,
  type AgentOpsActivity,
  type AgentOpsAgent,
  type AgentOpsDiagnostic,
  type AgentOpsProposal,
  type AgentOpsProposalStatus,
  type AgentOpsRoom,
} from '@/lib/api';

const SECTIONS = [
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
  'Recommended Next Steps',
  'Deferred Decisions',
  'Things We Should NOT Touch Yet',
];

const TOP_NAV_LINKS = [
  ['/', 'Mission Control'],
  ['/investment/research', 'Research Cases'],
  ['/investment/research-inbox', 'Research Inbox'],
  ['/investment/evaluations', 'Evaluations'],
  ['/investment/internal-audit', 'Internal Audit'],
  ['/investment/radar-status', 'Radar Status'],
  ['/investment/sources', 'Sources'],
] as const;

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
    <span className={`inline-flex items-center rounded-full border px-2 py-0.5 text-[11px] font-medium ${badgeClass(value)}`}>
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
    const [roomsResult, agentsResult, activityResult, diagnosticsResult, proposalsResult] = await Promise.allSettled([
      fetchAgentOpsRooms(),
      fetchAgentOpsAgents(),
      fetchAgentOpsActivity({ limit: 25 }),
      fetchAgentOpsDiagnostics({ limit: 25 }),
      fetchAgentOpsProposals({ limit: 25 }),
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
              Observability, diagnostics, learning proposals, and agent operations for SwissEdge.
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
                      <p className="min-h-12 text-sm leading-6 text-slate-600">{room.description ?? 'No description.'}</p>
                      <div className="mt-4 flex items-center justify-between border-t border-slate-100 pt-3 text-xs text-slate-500">
                        <span>{agentCountByRoom.get(room.key) ?? 0} agent(s)</span>
                        <span>Display order {room.display_order}</span>
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
                            <div className="text-sm font-semibold text-slate-900">{agent.name}</div>
                            <div className="font-mono text-xs text-slate-400">{agent.key}</div>
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

            <SectionShell id="fontana" title="Fontana Reports" subtitle="Fontana is documented as CTO / Project Governor, but runtime is not implemented yet.">
              <PlaceholderPanel
                title="Fontana CTO reports are documented but not implemented yet."
                description="Fontana is an advisor/documenter concept only and cannot deploy, modify production, trigger scans, change cron, or enable evaluator v2."
                items={FONTANA_SECTIONS}
              />
            </SectionShell>
          </div>
        )}
      </div>
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
