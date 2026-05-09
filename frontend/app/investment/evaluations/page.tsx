'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { fetchSituations, archiveSituation, updateSituationStatus, type Situation } from '@/lib/api';

function inferSource(s: Situation): string {
  if (s.filing_url?.includes('sec.gov')) return 'SEC EDGAR';
  if (s.filing_type) return 'SEC Filing';
  return 'Unknown';
}

export default function EvaluationsPage() {
  const [situations, setSituations] = useState<Situation[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [quickStatusFilter, setQuickStatusFilter] = useState<string>('');
  const [filters, setFilters] = useState({
    evaluator_version: '',
    playbook_status: '',
    recommendation: '',
  });

  const handleStatusChange = async (id: string, status: string, companyName: string) => {
    try {
      await updateSituationStatus(id, status);
      loadSituations();
    } catch (err) {
      alert(`Failed to update status: ${err instanceof Error ? err.message : 'Unknown error'}`);
    }
  };

  const handleArchive = async (id: string, companyName: string) => {
    if (!confirm(`Archive "${companyName}"? This will hide it from the main list.`)) {
      return;
    }

    try {
      await archiveSituation(id);
      loadSituations();
    } catch (err) {
      alert(`Failed to archive: ${err instanceof Error ? err.message : 'Unknown error'}`);
    }
  };

  async function loadSituations() {
    try {
      setLoading(true);
      setError(null);
      const params = {
        evaluator_version: filters.evaluator_version || undefined,
        playbook_status: filters.playbook_status || undefined,
        recommendation: filters.recommendation || undefined,
        include_archived: true,
      };
      const data = await fetchSituations(params);
      setSituations(data.situations);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load evaluations');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadSituations();
  }, [filters]);

  const visibleSituations = quickStatusFilter
    ? situations.filter(s => s.status === quickStatusFilter)
    : situations;

  const statusCounts = {
    all: situations.length,
    detected: situations.filter(s => s.status === 'detected').length,
    reviewing: situations.filter(s => s.status === 'reviewing').length,
    watchlist: situations.filter(s => s.status === 'watchlist').length,
    ignored: situations.filter(s => s.status === 'ignored').length,
    archived: situations.filter(s => s.status === 'archived').length,
  };

  const formatValue = (value: any) => {
    if (value === null || value === undefined) return '-';
    if (typeof value === 'number') return value.toString();
    return value;
  };

  const getVersionBadge = (version: string | undefined) => {
    if (version === 'v2') return 'bg-cyan-500/20 text-cyan-400 border-cyan-400 glow-cyan';
    return 'bg-gray-700/50 text-gray-400 border-gray-600';
  };

  const getStatusBadge = (status: string | null | undefined) => {
    switch (status) {
      case 'evaluator_ready':
        return 'bg-green-500/20 text-green-400 border-green-400 glow-green';
      case 'partial':
        return 'bg-amber-500/20 text-amber-400 border-amber-400 glow-amber';
      case 'detection_only':
        return 'bg-violet-500/20 text-violet-400 border-violet-600';
      default:
        return 'bg-gray-700/50 text-gray-400 border-gray-600';
    }
  };

  const getRecommendationBadge = (rec: string | null | undefined) => {
    switch (rec) {
      case 'DEEP_RESEARCH':
        return 'bg-cyan-500/20 text-cyan-400 border-cyan-400';
      case 'HUMAN_REVIEW_REQUIRED':
        return 'bg-amber-500/20 text-amber-400 border-amber-400 glow-amber';
      case 'WATCHLIST':
        return 'bg-blue-500/20 text-blue-400 border-blue-400';
      case 'PASS':
        return 'bg-gray-700/50 text-gray-400 border-gray-600';
      default:
        return 'bg-gray-700/50 text-gray-400 border-gray-600';
    }
  };

  const getWorkflowStatusBadge = (status: string | null | undefined) => {
    switch (status) {
      case 'detected':
        return 'bg-gray-700/50 text-gray-400 border-gray-600';
      case 'reviewing':
        return 'bg-blue-500/20 text-blue-400 border-blue-400';
      case 'watchlist':
        return 'bg-green-500/20 text-green-400 border-green-400 glow-green';
      case 'ignored':
        return 'bg-gray-800/50 text-gray-600 border-gray-700';
      case 'archived':
        return 'bg-violet-500/20 text-violet-400 border-violet-600';
      default:
        return 'bg-gray-700/50 text-gray-400 border-gray-600';
    }
  };

  return (
    <>
      <div className="scan-line"></div>
      <div className="min-h-screen p-8">
        <div className="max-w-7xl mx-auto">
          <div className="mb-8">
            <div className="flex items-center justify-between">
              <Link href="/" className="text-cyan-400 hover:text-cyan-300 text-sm font-mono">
                ← MISSION CONTROL
              </Link>
              <div className="flex items-center gap-6">
                <Link href="/investment/sources" className="text-violet-400 hover:text-violet-300 text-sm font-mono">
                  SOURCES
                </Link>
                <Link href="/investment/research-inbox" className="text-violet-400 hover:text-violet-300 text-sm font-mono">
                  RESEARCH INBOX
                </Link>
                <Link href="/investment/research" className="text-cyan-400 hover:text-cyan-300 text-sm font-mono">
                  RESEARCH
                </Link>
                <Link href="/investment/radar-status" className="text-cyan-400 hover:text-cyan-300 text-sm font-mono">
                  RADAR STATUS
                </Link>
                <Link href="/investment/watchlist" className="text-green-400 hover:text-green-300 text-sm font-mono">
                  WATCHLIST →
                </Link>
              </div>
            </div>
          </div>

          <h1 className="text-4xl font-bold mb-2 text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-green-400">
            INVESTMENT EVALUATIONS QUEUE
          </h1>
          <p className="text-gray-500 text-xs font-mono mb-8">SPECIAL SITUATIONS RADAR // REAL-TIME MONITORING</p>

          {/* Summary Counters */}
          {!loading && !error && visibleSituations.length > 0 && (
            <div className="grid grid-cols-2 md:grid-cols-6 gap-4 mb-6">
              <div className="glass-panel rounded-lg p-4 border-cyan-500/30">
                <div className="text-2xl font-bold text-cyan-400 font-mono">{visibleSituations.length}</div>
                <div className="text-xs text-gray-500 font-mono uppercase mt-1">Total</div>
              </div>
              <div className="glass-panel rounded-lg p-4 border-green-500/30">
                <div className="text-2xl font-bold text-green-400 font-mono">
                  {visibleSituations.filter(s => s.playbook_status === 'evaluator_ready').length}
                </div>
                <div className="text-xs text-gray-500 font-mono uppercase mt-1">Ready</div>
              </div>
              <div className="glass-panel rounded-lg p-4 border-amber-500/30">
                <div className="text-2xl font-bold text-amber-400 font-mono">
                  {visibleSituations.filter(s => s.playbook_status === 'partial').length}
                </div>
                <div className="text-xs text-gray-500 font-mono uppercase mt-1">Partial</div>
              </div>
              <div className="glass-panel rounded-lg p-4 border-amber-500/30">
                <div className="text-2xl font-bold text-amber-400 font-mono">
                  {visibleSituations.filter(s => (s.human_review_required_count || 0) > 0).length}
                </div>
                <div className="text-xs text-gray-500 font-mono uppercase mt-1">HR Req</div>
              </div>
              <div className="glass-panel rounded-lg p-4 border-red-500/30">
                <div className="text-2xl font-bold text-red-400 font-mono">
                  {visibleSituations.reduce((sum, s) => sum + (s.prohibited_inferences_count || 0), 0)}
                </div>
                <div className="text-xs text-gray-500 font-mono uppercase mt-1">Proh</div>
              </div>
              <div className="glass-panel rounded-lg p-4 border-violet-500/30">
                <div className="text-2xl font-bold text-violet-400 font-mono">
                  {visibleSituations.reduce((sum, s) => sum + (s.missing_documents_count || 0), 0)}
                </div>
                <div className="text-xs text-gray-500 font-mono uppercase mt-1">Missing</div>
              </div>
            </div>
          )}

          {/* Alert Strip */}
          {!loading && !error && visibleSituations.length > 0 && (
            <>
              {visibleSituations.some(s => (s.prohibited_inferences_count || 0) > 0) ? (
                <div className="glass-panel rounded-lg p-4 mb-6 border-red-500/50 glow-red">
                  <p className="text-red-400 font-mono text-sm">
                    ⚠ PROHIBITED INFERENCES DETECTED: {visibleSituations.filter(s => (s.prohibited_inferences_count || 0) > 0).length} evaluation(s) flagged
                  </p>
                </div>
              ) : visibleSituations.some(s => (s.human_review_required_count || 0) > 0) ? (
                <div className="glass-panel rounded-lg p-4 mb-6 border-amber-500/30 glow-amber">
                  <p className="text-amber-400 font-mono text-sm">
                    ⚡ HUMAN REVIEW QUEUE: {visibleSituations.filter(s => (s.human_review_required_count || 0) > 0).length} evaluation(s) require review
                  </p>
                </div>
              ) : (
                <div className="glass-panel rounded-lg p-4 mb-6 border-cyan-500/30">
                  <p className="text-cyan-400 font-mono text-sm">
                    ✓ NO PROHIBITED INFERENCES DETECTED
                  </p>
                </div>
              )}
            </>
          )}

          {/* Quick Status Filters */}
          {!loading && !error && situations.length > 0 && (
            <div className="flex flex-wrap gap-2 mb-6">
              {([
                { key: '', label: 'All', count: statusCounts.all },
                { key: 'detected', label: 'Detected', count: statusCounts.detected },
                { key: 'reviewing', label: 'Reviewing', count: statusCounts.reviewing },
                { key: 'watchlist', label: 'Watchlist', count: statusCounts.watchlist },
                { key: 'ignored', label: 'Ignored', count: statusCounts.ignored },
                { key: 'archived', label: 'Archived', count: statusCounts.archived },
              ] as { key: string; label: string; count: number }[]).map(({ key, label, count }) => {
                const isActive = quickStatusFilter === key;
                return (
                  <button
                    key={key}
                    onClick={() => setQuickStatusFilter(key)}
                    className={`px-3 py-1.5 rounded text-xs font-mono font-bold border transition-colors ${
                      isActive
                        ? 'bg-cyan-500/30 text-cyan-300 border-cyan-400 glow-cyan'
                        : 'bg-gray-900/50 text-gray-400 border-gray-700 hover:border-cyan-500/50 hover:text-gray-300'
                    }`}
                  >
                    {label}
                    <span className={`ml-2 px-1.5 py-0.5 rounded text-xs ${isActive ? 'bg-cyan-500/30 text-cyan-300' : 'bg-gray-800 text-gray-500'}`}>
                      {count}
                    </span>
                  </button>
                );
              })}
            </div>
          )}

          {/* Filters */}
          <div className="glass-panel rounded-lg p-6 mb-6 border-cyan-500/30">
            <h2 className="text-sm font-mono text-cyan-400 mb-4 uppercase tracking-wider">Filter Parameters</h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-xs font-mono text-gray-400 mb-2 uppercase">
                  Evaluator Version
                </label>
                <select
                  value={filters.evaluator_version}
                  onChange={(e) => setFilters({ ...filters, evaluator_version: e.target.value })}
                  className="w-full bg-gray-900/50 border border-cyan-500/30 rounded px-3 py-2 text-gray-300 text-sm font-mono focus:border-cyan-400 focus:outline-none"
                >
                  <option value="">All</option>
                  <option value="v1">v1</option>
                  <option value="v2">v2</option>
                </select>
              </div>
              <div>
                <label className="block text-xs font-mono text-gray-400 mb-2 uppercase">
                  Playbook Status
                </label>
                <select
                  value={filters.playbook_status}
                  onChange={(e) => setFilters({ ...filters, playbook_status: e.target.value })}
                  className="w-full bg-gray-900/50 border border-cyan-500/30 rounded px-3 py-2 text-gray-300 text-sm font-mono focus:border-cyan-400 focus:outline-none"
                >
                  <option value="">All</option>
                  <option value="evaluator_ready">Evaluator Ready</option>
                  <option value="partial">Partial</option>
                  <option value="detection_only">Detection Only</option>
                </select>
              </div>
              <div>
                <label className="block text-xs font-mono text-gray-400 mb-2 uppercase">
                  Recommendation
                </label>
                <select
                  value={filters.recommendation}
                  onChange={(e) => setFilters({ ...filters, recommendation: e.target.value })}
                  className="w-full bg-gray-900/50 border border-cyan-500/30 rounded px-3 py-2 text-gray-300 text-sm font-mono focus:border-cyan-400 focus:outline-none"
                >
                  <option value="">All</option>
                  <option value="DEEP_RESEARCH">Deep Research</option>
                  <option value="HUMAN_REVIEW_REQUIRED">Human Review Required</option>
                  <option value="WATCHLIST">Watchlist</option>
                  <option value="PASS">Pass</option>
                </select>
              </div>
            </div>
          </div>

          {/* Loading State */}
          {loading && (
            <div className="glass-panel rounded-lg p-8 text-center border-cyan-500/30">
              <div className="inline-block w-8 h-8 border-2 border-cyan-400 border-t-transparent rounded-full animate-spin mb-4"></div>
              <p className="text-gray-400 font-mono text-sm">LOADING EVALUATION QUEUE...</p>
            </div>
          )}

          {/* Error State */}
          {error && (
            <div className="glass-panel rounded-lg p-4 mb-6 border-red-500/50 glow-red">
              <p className="text-red-400 font-mono text-sm">⚠ ERROR: {error}</p>
            </div>
          )}

          {/* Empty State */}
          {!loading && !error && visibleSituations.length === 0 && (
            <div className="glass-panel rounded-lg p-8 text-center border-gray-700">
              <p className="text-gray-500 font-mono text-sm">NO EVALUATIONS IN QUEUE</p>
            </div>
          )}

          {/* Table */}
          {!loading && !error && visibleSituations.length > 0 && (
            <div className="glass-panel rounded-lg overflow-hidden border-cyan-500/30">
              <div className="overflow-x-auto">
                <table className="min-w-full">
                  <thead className="bg-gray-900/50 border-b border-cyan-500/30">
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-mono text-cyan-400 uppercase tracking-wider">Company</th>
                      <th className="px-4 py-3 text-left text-xs font-mono text-cyan-400 uppercase tracking-wider">Ticker</th>
                      <th className="px-4 py-3 text-left text-xs font-mono text-cyan-400 uppercase tracking-wider">Filing</th>
                      <th className="px-4 py-3 text-left text-xs font-mono text-cyan-400 uppercase tracking-wider">Src</th>
                      <th className="px-4 py-3 text-left text-xs font-mono text-cyan-400 uppercase tracking-wider">Ver</th>
                      <th className="px-4 py-3 text-left text-xs font-mono text-cyan-400 uppercase tracking-wider">Playbook</th>
                      <th className="px-4 py-3 text-left text-xs font-mono text-cyan-400 uppercase tracking-wider">Playbook Status</th>
                      <th className="px-4 py-3 text-left text-xs font-mono text-cyan-400 uppercase tracking-wider">Workflow Status</th>
                      <th className="px-4 py-3 text-left text-xs font-mono text-cyan-400 uppercase tracking-wider">Rec</th>
                      <th className="px-4 py-3 text-left text-xs font-mono text-cyan-400 uppercase tracking-wider">Conf</th>
                      <th className="px-4 py-3 text-center text-xs font-mono text-cyan-400 uppercase tracking-wider">HR</th>
                      <th className="px-4 py-3 text-center text-xs font-mono text-cyan-400 uppercase tracking-wider">Risk</th>
                      <th className="px-4 py-3 text-center text-xs font-mono text-cyan-400 uppercase tracking-wider">Proh</th>
                      <th className="px-4 py-3 text-center text-xs font-mono text-cyan-400 uppercase tracking-wider">Miss</th>
                      <th className="px-4 py-3 text-center text-xs font-mono text-cyan-400 uppercase tracking-wider">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-800/50">
                    {visibleSituations.map((situation) => (
                      <tr key={situation.id} className="hover:bg-cyan-500/5 transition-colors">
                        <td className="px-4 py-3 text-sm font-mono">
                          <Link
                            href={`/investment/evaluations/${situation.id}`}
                            className="text-cyan-400 hover:text-cyan-300 hover:underline block max-w-[200px] truncate"
                            title={situation.company_name}
                          >
                            {situation.company_name}
                          </Link>
                        </td>
                        <td className="px-4 py-3 text-sm font-mono text-gray-400">
                          {formatValue(situation.ticker)}
                        </td>
                        <td className="px-4 py-3 text-sm font-mono text-gray-400">
                          {formatValue(situation.filing_type)}
                        </td>
                        <td className="px-4 py-3 text-xs font-mono text-gray-500">
                          {inferSource(situation)}
                        </td>
                        <td className="px-4 py-3 text-sm">
                          <span className={`px-2 py-1 rounded text-xs font-mono font-bold border ${getVersionBadge(situation.evaluator_version)}`}>
                            {formatValue(situation.evaluator_version)}
                          </span>
                        </td>
                        <td className="px-4 py-3 text-sm font-mono text-gray-400 truncate max-w-[150px]">
                          {formatValue(situation.selected_playbook)}
                        </td>
                        <td className="px-4 py-3 text-sm">
                          <span className={`px-2 py-1 rounded text-xs font-mono font-bold border ${getStatusBadge(situation.playbook_status)}`}>
                            {formatValue(situation.playbook_status)}
                          </span>
                        </td>
                        <td className="px-4 py-3 text-sm">
                          <span className={`px-2 py-1 rounded text-xs font-mono font-bold border ${getWorkflowStatusBadge(situation.status)}`}>
                            {formatValue(situation.status)}
                          </span>
                        </td>
                        <td className="px-4 py-3 text-sm">
                          <span className={`px-2 py-1 rounded text-xs font-mono border ${getRecommendationBadge(situation.recommendation)}`}>
                            {formatValue(situation.recommendation)}
                          </span>
                        </td>
                        <td className="px-4 py-3 text-sm font-mono text-gray-400">
                          {formatValue(situation.evaluator_confidence)}
                        </td>
                        <td className="px-4 py-3 text-sm text-center font-mono text-gray-400">
                          {formatValue(situation.human_review_required_count)}
                        </td>
                        <td className="px-4 py-3 text-sm text-center font-mono text-gray-400">
                          {formatValue(situation.risk_flags_count)}
                        </td>
                        <td className="px-4 py-3 text-sm text-center font-mono">
                          {situation.prohibited_inferences_count && situation.prohibited_inferences_count > 0 ? (
                            <span className="text-red-400 font-bold glow-red">
                              {situation.prohibited_inferences_count}
                            </span>
                          ) : (
                            <span className="text-gray-600">0</span>
                          )}
                        </td>
                        <td className="px-4 py-3 text-sm text-center font-mono text-gray-400">
                          {formatValue(situation.missing_documents_count)}
                        </td>
                        <td className="px-4 py-3 text-sm text-center">
                          <div className="flex gap-1 justify-center">
                            {situation.status !== 'reviewing' && situation.status !== 'archived' && (
                              <button
                                onClick={() => handleStatusChange(situation.id, 'reviewing', situation.company_name)}
                                className="px-2 py-1 rounded text-xs font-mono bg-blue-500/20 text-blue-400 border border-blue-400 hover:bg-blue-500/30 transition-colors"
                                title="Mark as reviewing"
                              >
                                Review
                              </button>
                            )}
                            {situation.status !== 'watchlist' && situation.status !== 'archived' && (
                              <button
                                onClick={() => handleStatusChange(situation.id, 'watchlist', situation.company_name)}
                                className="px-2 py-1 rounded text-xs font-mono bg-green-500/20 text-green-400 border border-green-400 hover:bg-green-500/30 transition-colors"
                                title="Add to watchlist"
                              >
                                Watch
                              </button>
                            )}
                            {situation.status !== 'ignored' && situation.status !== 'archived' && (
                              <button
                                onClick={() => handleStatusChange(situation.id, 'ignored', situation.company_name)}
                                className="px-2 py-1 rounded text-xs font-mono bg-gray-700/50 text-gray-500 border border-gray-600 hover:bg-gray-600/50 transition-colors"
                                title="Ignore this evaluation"
                              >
                                Ignore
                              </button>
                            )}
                            {situation.status !== 'archived' && (
                              <button
                                onClick={() => handleArchive(situation.id, situation.company_name)}
                                className="px-2 py-1 rounded text-xs font-mono bg-violet-500/20 text-violet-400 border border-violet-600 hover:bg-violet-500/30 transition-colors"
                                title="Archive this evaluation"
                              >
                                Archive
                              </button>
                            )}
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <div className="bg-gray-900/50 px-4 py-3 border-t border-cyan-500/30">
                <p className="text-xs font-mono text-gray-500">
                  QUEUE SIZE: {visibleSituations.length} EVALUATION{visibleSituations.length !== 1 ? 'S' : ''}
                </p>
              </div>
            </div>
          )}
        </div>
      </div>
    </>
  );
}
