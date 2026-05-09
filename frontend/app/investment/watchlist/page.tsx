'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { fetchSituations, updateSituationStatus, type Situation } from '@/lib/api';

export default function WatchlistPage() {
  const [situations, setSituations] = useState<Situation[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function load() {
    try {
      setLoading(true);
      setError(null);
      const data = await fetchSituations({ include_archived: false });
      setSituations(data.situations.filter(s => s.status === 'watchlist'));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load watchlist');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { load(); }, []);

  const handleStatusChange = async (id: string, status: string, companyName: string) => {
    try {
      await updateSituationStatus(id, status);
      load();
    } catch (err) {
      alert(`Failed to update status: ${err instanceof Error ? err.message : 'Unknown error'}`);
    }
  };

  const formatValue = (value: any) => {
    if (value === null || value === undefined) return '-';
    if (typeof value === 'number') return value.toString();
    return value;
  };

  const getRecommendationBadge = (rec: string | null | undefined) => {
    switch (rec) {
      case 'INVESTIGATE': return 'bg-cyan-500/20 text-cyan-400 border-cyan-400 glow-cyan';
      case 'MONITOR': return 'bg-amber-500/20 text-amber-400 border-amber-400 glow-amber';
      case 'PASS': return 'bg-gray-700/50 text-gray-500 border-gray-600';
      case 'STRONG_BUY':
      case 'BUY': return 'bg-green-500/20 text-green-400 border-green-400 glow-green';
      case 'AVOID':
      case 'SELL': return 'bg-red-500/20 text-red-400 border-red-400 glow-red';
      default: return 'bg-gray-700/50 text-gray-400 border-gray-600';
    }
  };

  return (
    <>
      <div className="scan-line"></div>
      <div className="min-h-screen p-8">
        <div className="max-w-7xl mx-auto">
          <div className="flex items-center justify-between mb-6">
            <Link href="/investment/evaluations" className="text-cyan-400 hover:text-cyan-300 text-sm font-mono">
              ← EVALUATION QUEUE
            </Link>
          </div>

          <h1 className="text-3xl font-bold mb-2 text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-green-400">
            Watchlist
          </h1>
          <p className="text-gray-500 text-xs font-mono mb-8">SITUATIONS UNDER ACTIVE MONITORING</p>

          {loading && (
            <div className="glass-panel rounded-lg p-8 text-center border-cyan-500/30">
              <div className="inline-block w-8 h-8 border-2 border-cyan-400 border-t-transparent rounded-full animate-spin mb-4"></div>
              <p className="text-gray-400 font-mono text-sm">LOADING WATCHLIST...</p>
            </div>
          )}

          {error && (
            <div className="glass-panel rounded-lg p-4 mb-6 border-red-500/50 glow-red">
              <p className="text-red-400 font-mono text-sm">⚠ ERROR: {error}</p>
            </div>
          )}

          {!loading && !error && situations.length === 0 && (
            <div className="glass-panel rounded-lg p-8 text-center border-gray-700">
              <p className="text-gray-500 font-mono text-sm">NO SITUATIONS ON WATCHLIST</p>
            </div>
          )}

          {!loading && !error && situations.length > 0 && (
            <div className="glass-panel rounded-lg overflow-hidden border-green-500/30">
              <div className="overflow-x-auto">
                <table className="min-w-full">
                  <thead className="bg-gray-900/50 border-b border-green-500/30">
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-mono text-green-400 uppercase tracking-wider">Company</th>
                      <th className="px-4 py-3 text-left text-xs font-mono text-green-400 uppercase tracking-wider">Ticker</th>
                      <th className="px-4 py-3 text-left text-xs font-mono text-green-400 uppercase tracking-wider">Filing</th>
                      <th className="px-4 py-3 text-left text-xs font-mono text-green-400 uppercase tracking-wider">Playbook</th>
                      <th className="px-4 py-3 text-left text-xs font-mono text-green-400 uppercase tracking-wider">Rec</th>
                      <th className="px-4 py-3 text-left text-xs font-mono text-green-400 uppercase tracking-wider">Confidence</th>
                      <th className="px-4 py-3 text-left text-xs font-mono text-green-400 uppercase tracking-wider">Detected</th>
                      <th className="px-4 py-3 text-center text-xs font-mono text-green-400 uppercase tracking-wider">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-800/50">
                    {situations.map((s) => (
                      <tr key={s.id} className="hover:bg-green-500/5 transition-colors">
                        <td className="px-4 py-3 text-sm font-mono">
                          <Link
                            href={`/investment/evaluations/${s.id}`}
                            className="text-cyan-400 hover:text-cyan-300 hover:underline block max-w-[200px] truncate"
                            title={s.company_name}
                          >
                            {s.company_name}
                          </Link>
                        </td>
                        <td className="px-4 py-3 text-sm font-mono text-gray-400">{formatValue(s.ticker)}</td>
                        <td className="px-4 py-3 text-sm font-mono text-gray-400">{formatValue(s.filing_type)}</td>
                        <td className="px-4 py-3 text-sm font-mono text-gray-400 truncate max-w-[150px]">{formatValue(s.selected_playbook)}</td>
                        <td className="px-4 py-3 text-sm">
                          <span className={`px-2 py-1 rounded text-xs font-mono border ${getRecommendationBadge(s.recommendation)}`}>
                            {formatValue(s.recommendation)}
                          </span>
                        </td>
                        <td className="px-4 py-3 text-sm font-mono text-gray-400">{formatValue(s.evaluator_confidence)}</td>
                        <td className="px-4 py-3 text-sm font-mono text-gray-400">
                          {s.detected_at ? new Date(s.detected_at).toLocaleDateString() : '-'}
                        </td>
                        <td className="px-4 py-3 text-sm text-center">
                          <div className="flex gap-1 justify-center">
                            <button
                              onClick={() => handleStatusChange(s.id, 'reviewing', s.company_name)}
                              className="px-2 py-1 rounded text-xs font-mono bg-blue-500/20 text-blue-400 border border-blue-400 hover:bg-blue-500/30 transition-colors"
                            >
                              Review
                            </button>
                            <button
                              onClick={() => handleStatusChange(s.id, 'ignored', s.company_name)}
                              className="px-2 py-1 rounded text-xs font-mono bg-gray-700/50 text-gray-500 border border-gray-600 hover:bg-gray-600/50 transition-colors"
                            >
                              Ignore
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <div className="bg-gray-900/50 px-4 py-3 border-t border-green-500/30">
                <p className="text-xs font-mono text-gray-500">
                  WATCHLIST: {situations.length} SITUATION{situations.length !== 1 ? 'S' : ''}
                </p>
              </div>
            </div>
          )}
        </div>
      </div>
    </>
  );
}
