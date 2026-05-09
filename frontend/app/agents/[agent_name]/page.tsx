'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { fetchAgent, type AgentDetail } from '@/lib/api';

export default function AgentDetailPage() {
  const params = useParams();
  const agent_name = params.agent_name as string;

  const [agent, setAgent] = useState<AgentDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showRawJson, setShowRawJson] = useState(false);

  useEffect(() => {
    async function loadAgent() {
      try {
        setLoading(true);
        setError(null);
        const data = await fetchAgent(agent_name);
        setAgent(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load agent');
      } finally {
        setLoading(false);
      }
    }

    if (agent_name) {
      loadAgent();
    }
  }, [agent_name]);

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'active':    return 'status-badge status-badge--active';
      case 'partial':   return 'status-badge status-badge--partial';
      case 'manual':    return 'status-badge status-badge--manual';
      case 'pending':
      case 'future':    return 'status-badge status-badge--preview';
      case 'attention': return 'status-badge status-badge--preview';
      default:          return 'status-badge status-badge--readonly';
    }
  };

  const getRuntimeBadge = (_runtime: string) => {
    return 'status-badge status-badge--readonly';
  };

  const formatTimestamp = (timestamp: string | null) => {
    if (!timestamp) return 'NEVER';
    const date = new Date(timestamp);
    return date.toLocaleString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    });
  };

  const formatRelativeTime = (timestamp: string | null) => {
    if (!timestamp) return 'NEVER';
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return 'JUST NOW';
    if (diffMins < 60) return `${diffMins}m AGO`;
    if (diffHours < 24) return `${diffHours}h AGO`;
    return `${diffDays}d AGO`;
  };

  const getRunStatusBadge = (status: string) => {
    switch (status) {
      case 'completed': return 'status-badge status-badge--active';
      case 'failed':    return 'status-badge status-badge--preview';
      case 'running':   return 'status-badge status-badge--partial';
      default:          return 'status-badge status-badge--readonly';
    }
  };

  if (loading) {
    return (
      <div className="page-container">
        <div className="loading-state">
          <div className="loading-spinner"></div>
          <span>Loading agent dossier…</span>
        </div>
      </div>
    );
  }

  if (error || !agent) {
    return (
      <div className="page-container">
        <div className="card card-accent mb-6">
          <p style={{ fontFamily: 'var(--font-mono)', fontSize: '13px', color: 'var(--text-secondary)' }}>
            ⚠ {error || 'Agent not found'}
          </p>
        </div>
        <Link href="/agents" className="nav-back">← Return to Roster</Link>
      </div>
    );
  }

  const successRate = agent.stats.total_runs > 0
    ? ((agent.stats.total_runs - agent.stats.failed_runs) / agent.stats.total_runs) * 100
    : 0;

  return (
    <div className="page-container">

      <div className="mb-8 animate-fade-in">
        <Link href="/agents" className="nav-back">← Agent Roster</Link>
      </div>

      {/* Header */}
      <div className="page-header animate-fade-in">
        <h1 className="page-title">{agent.display_name}</h1>
        <p className="page-subtitle">Agent dossier · {agent.agent_name}</p>
        <div className="flex items-center gap-3 mt-3">
          <span className={getStatusBadge(agent.current_status)}>{agent.current_status.toUpperCase()}</span>
          <span className={getRuntimeBadge(agent.runtime)}>{agent.runtime.toUpperCase()}</span>
        </div>
      </div>

      {/* Warnings */}
      {agent.warnings && agent.warnings.length > 0 && (
        <div className="card card-accent mb-6 animate-fade-in-1">
          <div className="card-title" style={{ marginBottom: '8px' }}>⚠ Warnings</div>
          <ul style={{ margin: 0, paddingLeft: '16px' }}>
            {agent.warnings.map((warning, index) => (
              <li key={index} style={{ fontFamily: 'var(--font-mono)', fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '4px' }}>
                {warning}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Metrics Strip */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4 mb-6 animate-fade-in-1">
        {[
          { label: 'Total Runs',     value: String(agent.stats.total_runs) },
          { label: 'Failed',         value: String(agent.stats.failed_runs),        accent: agent.stats.failed_runs > 0 },
          { label: 'Success Rate',   value: `${successRate.toFixed(1)}%` },
          { label: 'Total Cost',     value: `$${agent.stats.total_cost_usd.toFixed(4)}` },
          { label: 'Input Tokens',   value: agent.stats.total_input_tokens.toLocaleString() },
          { label: 'Output Tokens',  value: agent.stats.total_output_tokens.toLocaleString() },
        ].map(({ label, value, accent }) => (
          <div key={label} className="card" style={{ padding: '16px' }}>
            <div className="metric-pill">
              <span className="metric-value" style={accent ? { color: '#c62828' } : undefined}>{value}</span>
              <span className="metric-label">{label}</span>
            </div>
          </div>
        ))}
      </div>

      {/* Agent Configuration */}
      <div className="card mb-6 animate-fade-in-2">
        <div className="section-header" style={{ marginBottom: '16px' }}>
          <span className="section-title">Agent Configuration</span>
          <div className="section-line"></div>
        </div>
        <dl className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {[
            { label: 'Purpose',        value: agent.purpose,              span: false },
            { label: 'Module',         value: agent.module,               span: false },
            { label: 'Owner',          value: agent.owner,                span: false },
            { label: 'Model',          value: agent.model || 'None (no AI)', span: false },
            { label: 'Instructions',   value: agent.instructions,         span: true  },
            { label: 'Permissions',    value: agent.permissions,          span: false },
            { label: 'Human Approval', value: agent.human_approval_rules, span: false },
          ].map(({ label, value, span }) => (
            <div key={label} className={span ? 'md:col-span-2' : undefined}>
              <dt style={{ fontFamily: 'var(--font-mono)', fontSize: '10px', fontWeight: 500, letterSpacing: '0.12em', textTransform: 'uppercase', color: 'var(--text-muted)' }}>{label}</dt>
              <dd style={{ marginTop: '4px', fontFamily: 'var(--font-mono)', fontSize: '12px', color: 'var(--text-secondary)' }}>{value}</dd>
            </div>
          ))}
          {agent.tools && agent.tools.length > 0 && (
            <div className="md:col-span-2">
              <dt style={{ fontFamily: 'var(--font-mono)', fontSize: '10px', fontWeight: 500, letterSpacing: '0.12em', textTransform: 'uppercase', color: 'var(--text-muted)' }}>Tools</dt>
              <dd style={{ marginTop: '4px', fontFamily: 'var(--font-mono)', fontSize: '12px', color: 'var(--text-secondary)' }}>{agent.tools.join(', ')}</dd>
            </div>
          )}
        </dl>
      </div>

      {/* Last Execution */}
      {(agent.last_outcome || agent.last_error) && (
        <div className="card mb-6 animate-fade-in-2">
          <div className="section-header" style={{ marginBottom: '16px' }}>
            <span className="section-title">Last Execution</span>
            <div className="section-line"></div>
          </div>
          <dl style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {agent.last_outcome && (
              <div>
                <dt style={{ fontFamily: 'var(--font-mono)', fontSize: '10px', fontWeight: 500, letterSpacing: '0.12em', textTransform: 'uppercase', color: 'var(--text-muted)' }}>Outcome</dt>
                <dd style={{ marginTop: '4px', fontFamily: 'var(--font-mono)', fontSize: '12px', color: 'var(--text-secondary)' }}>{agent.last_outcome}</dd>
              </div>
            )}
            {agent.last_error && (
              <div>
                <dt style={{ fontFamily: 'var(--font-mono)', fontSize: '10px', fontWeight: 500, letterSpacing: '0.12em', textTransform: 'uppercase', color: 'var(--text-muted)' }}>Error</dt>
                <dd style={{ marginTop: '4px', fontFamily: 'var(--font-mono)', fontSize: '12px', color: '#c62828' }}>{agent.last_error}</dd>
              </div>
            )}
            <div>
              <dt style={{ fontFamily: 'var(--font-mono)', fontSize: '10px', fontWeight: 500, letterSpacing: '0.12em', textTransform: 'uppercase', color: 'var(--text-muted)' }}>Last Run</dt>
              <dd style={{ marginTop: '4px', fontFamily: 'var(--font-mono)', fontSize: '12px', color: 'var(--text-secondary)' }}>
                {formatTimestamp(agent.stats.last_run)} ({formatRelativeTime(agent.stats.last_run)})
              </dd>
            </div>
          </dl>
        </div>
      )}

      {/* Recent Runs */}
      {agent.recent_runs && agent.recent_runs.length > 0 && (
        <div className="card mb-6 animate-fade-in-3" style={{ padding: 0, overflow: 'hidden' }}>
          <div style={{ padding: '20px 24px 16px', borderBottom: '1px solid var(--border-subtle)' }}>
            <div className="section-header" style={{ marginBottom: 0 }}>
              <span className="section-title">Recent Runs</span>
              <div className="section-line"></div>
              <span className="section-count">{agent.recent_runs.length}</span>
            </div>
          </div>
          <div style={{ overflowX: 'auto' }}>
            <table className="data-table">
              <thead>
                <tr>
                  <th>Started</th>
                  <th>Status</th>
                  <th>Task</th>
                  <th>Duration</th>
                  <th>Cost</th>
                  <th>Outcome</th>
                </tr>
              </thead>
              <tbody>
                {agent.recent_runs.map((run) => (
                  <tr key={run.id}>
                    <td>{formatRelativeTime(run.started_at)}</td>
                    <td><span className={getRunStatusBadge(run.status)}>{run.status.toUpperCase()}</span></td>
                    <td style={{ maxWidth: '200px' }} className="truncate">{run.task_name || '—'}</td>
                    <td>{run.duration_ms ? `${run.duration_ms}ms` : '—'}</td>
                    <td>{run.estimated_cost_usd ? `$${run.estimated_cost_usd.toFixed(4)}` : '—'}</td>
                    <td style={{ maxWidth: '200px' }} className="truncate">{run.final_outcome || '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Failure Modes */}
      {agent.failure_modes && agent.failure_modes.length > 0 && (
        <div className="card card-accent mb-6 animate-fade-in-3">
          <div className="section-header" style={{ marginBottom: '12px' }}>
            <span className="section-title">Known Failure Modes</span>
            <div className="section-line"></div>
          </div>
          <ul style={{ margin: 0, paddingLeft: '16px' }}>
            {agent.failure_modes.map((mode, index) => (
              <li key={index} style={{ fontFamily: 'var(--font-mono)', fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '6px' }}>
                {mode}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Recommended Action */}
      {agent.recommended_next_action && (
        <div className="card mb-6 animate-fade-in-3">
          <div className="section-header" style={{ marginBottom: '12px' }}>
            <span className="section-title">Recommended Next Action</span>
            <div className="section-line"></div>
          </div>
          <p style={{ fontFamily: 'var(--font-mono)', fontSize: '12px', color: 'var(--text-secondary)', margin: 0 }}>
            {agent.recommended_next_action}
          </p>
        </div>
      )}

      {/* Raw JSON */}
      <div className="card animate-fade-in-4">
        <button
          onClick={() => setShowRawJson(!showRawJson)}
          className="btn btn--ghost btn--sm"
          style={{ width: '100%', justifyContent: 'space-between', fontFamily: 'var(--font-mono)' }}
        >
          <span>Raw Agent JSON</span>
          <span>{showRawJson ? '▼' : '▶'}</span>
        </button>
        {showRawJson && (
          <pre style={{ marginTop: '16px', padding: '16px', background: 'var(--bg-subtle)', borderRadius: '8px', overflowX: 'auto', fontSize: '11px', fontFamily: 'var(--font-mono)', color: 'var(--text-secondary)', border: '1px solid var(--border-default)' }}>
            {JSON.stringify(agent, null, 2)}
          </pre>
        )}
      </div>

    </div>
  );
}
