'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { fetchAgents, type Agent } from '@/lib/api';

export default function AgentsPage() {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadAgents() {
      try {
        setLoading(true);
        setError(null);
        const data = await fetchAgents();
        setAgents(data.agents);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load agents');
      } finally {
        setLoading(false);
      }
    }

    loadAgents();
  }, []);

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

  const formatLastRun = (lastRun: string | null) => {
    if (!lastRun) return 'NEVER';
    const date = new Date(lastRun);
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

  return (
    <div className="page-container">

      <div className="mb-8 animate-fade-in">
        <Link href="/" className="nav-back">← Mission Control</Link>
      </div>

      <div className="page-header animate-fade-in">
        <h1 className="page-title">Agent Roster</h1>
        <p className="page-subtitle">Operational agents — status, runs, costs</p>
      </div>

      {/* Loading State */}
      {loading && (
        <div className="loading-state">
          <div className="loading-spinner"></div>
          <span>Loading agent roster…</span>
        </div>
      )}

      {/* Error State */}
      {error && (
        <div className="card card-accent mb-6">
          <p style={{ fontFamily: 'var(--font-mono)', fontSize: '13px', color: 'var(--text-secondary)' }}>
            ⚠ {error}
          </p>
        </div>
      )}

      {/* Agent Grid */}
      {!loading && !error && (
        <>
          <div className="top-bar mb-6 animate-fade-in-1">
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span className="status-dot status-dot--active"></span>
              <span className="top-bar-value">Roster operational</span>
            </div>
            <div style={{ marginLeft: 'auto' }}>
              <span className="top-bar-label">Total agents</span>{' '}
              <span className="top-bar-value">{agents.length}</span>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 animate-fade-in-2">
            {agents.map((agent) => (
              <Link
                key={agent.agent_name}
                href={`/agents/${agent.agent_name}`}
                className="card block no-underline"
                style={{ textDecoration: 'none' }}
              >
                <div className="card-header">
                  <div>
                    <div className="card-title">{agent.agent_name}</div>
                    <div className="card-desc">{agent.purpose || 'System agent'}</div>
                  </div>
                  <span className={getStatusBadge(agent.current_status)}>
                    {agent.current_status.toUpperCase()}
                  </span>
                </div>

                <div className="mb-3">
                  <span className={getRuntimeBadge(agent.runtime)}>
                    {agent.runtime.toUpperCase()}
                  </span>
                </div>

                <div className="card-metrics">
                  <div className="metric-pill">
                    <span className="metric-value">{agent.total_runs || 0}</span>
                    <span className="metric-label">Total Runs</span>
                  </div>
                  <div className="metric-pill">
                    <span className="metric-value" style={{ color: agent.failed_runs > 0 ? '#c62828' : 'var(--text-muted)' }}>
                      {agent.failed_runs || 0}
                    </span>
                    <span className="metric-label">Failed</span>
                  </div>
                  <div className="metric-pill" style={{ marginLeft: 'auto', textAlign: 'right' }}>
                    <span className="metric-value" style={{ fontSize: '13px' }}>{formatLastRun(agent.last_run)}</span>
                    <span className="metric-label">Last Run</span>
                  </div>
                </div>

                {agent.total_runs > 0 && (
                  <div className="mt-3" style={{ height: '3px', background: 'var(--bg-muted)', borderRadius: '2px', overflow: 'hidden' }}>
                    <div
                      style={{
                        height: '100%',
                        background: 'var(--status-active-text)',
                        borderRadius: '2px',
                        width: `${((agent.total_runs - agent.failed_runs) / agent.total_runs) * 100}%`,
                        transition: 'width 0.5s ease',
                      }}
                    />
                  </div>
                )}
              </Link>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
