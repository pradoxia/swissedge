'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import {
  fetchSourceIntelligenceSuggestions,
  reviewSourceIntelligenceSuggestion,
  type SourceIntelligenceSuggestionRecord,
} from '@/lib/api';

const STATUS_STYLE: Record<string, string> = {
  proposed: 'text-amber-500',
  approved: 'text-green-500',
  rejected: 'text-gray-600',
};

const ACTION_LABELS: Record<string, string> = {
  add: 'ADD SOURCE',
  update_priority: 'UPDATE PRIORITY',
  deactivate: 'DEACTIVATE',
};

export default function SourceIntelligenceQueuePage() {
  const [suggestions, setSuggestions] = useState<SourceIntelligenceSuggestionRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filterStatus, setFilterStatus] = useState('');
  const [filterAction, setFilterAction] = useState('');
  const [reviewMsg, setReviewMsg] = useState<string | null>(null);

  async function load() {
    try {
      setLoading(true);
      setError(null);
      const data = await fetchSourceIntelligenceSuggestions({
        status: filterStatus || undefined,
        action: filterAction || undefined,
      });
      setSuggestions(data.suggestions);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load suggestions');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { load(); }, [filterStatus, filterAction]);

  async function handleReview(suggestionId: string, status: 'approved' | 'rejected') {
    setReviewMsg(null);
    try {
      await reviewSourceIntelligenceSuggestion(suggestionId, status);
      setReviewMsg(`Proposal ${status}.`);
      await load();
    } catch (err) {
      setReviewMsg(err instanceof Error ? err.message : 'Review failed');
    }
  }

  const proposed = suggestions.filter(s => s.status === 'proposed');
  const reviewed = suggestions.filter(s => s.status !== 'proposed');

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100 p-6">
      <div className="max-w-4xl mx-auto">
        <div className="flex items-start justify-between mb-6">
          <div>
            <h1 className="text-xl font-mono font-bold text-white">Source Intelligence Queue</h1>
            <p className="text-xs font-mono text-gray-600 mt-0.5">
              Manual approval queue. No action applies proposals to investment_sources.
            </p>
          </div>
          <div className="flex gap-3">
            <Link href="/investment/historical-cases" className="px-3 py-1.5 rounded border border-gray-700 hover:border-gray-500 text-xs font-mono text-gray-400 transition-colors">
              HISTORICAL CASES
            </Link>
            <Link href="/investment/research" className="px-3 py-1.5 rounded border border-gray-700 hover:border-gray-500 text-xs font-mono text-gray-400 transition-colors">
              RESEARCH CASES
            </Link>
          </div>
        </div>

        <div className="mb-4 flex items-center gap-4 flex-wrap">
          <div className="flex items-center gap-2">
            <label className="text-xs font-mono text-gray-500">Status:</label>
            <select
              value={filterStatus}
              onChange={e => setFilterStatus(e.target.value)}
              className="bg-gray-900 border border-gray-700 rounded px-2 py-1 text-xs font-mono text-gray-300 focus:outline-none"
            >
              <option value="">All</option>
              <option value="proposed">proposed</option>
              <option value="approved">approved</option>
              <option value="rejected">rejected</option>
            </select>
          </div>
          <div className="flex items-center gap-2">
            <label className="text-xs font-mono text-gray-500">Action:</label>
            <select
              value={filterAction}
              onChange={e => setFilterAction(e.target.value)}
              className="bg-gray-900 border border-gray-700 rounded px-2 py-1 text-xs font-mono text-gray-300 focus:outline-none"
            >
              <option value="">All</option>
              <option value="add">add</option>
              <option value="update_priority">update_priority</option>
              <option value="deactivate">deactivate</option>
            </select>
          </div>
          {reviewMsg && <p className="text-xs font-mono text-emerald-500">{reviewMsg}</p>}
        </div>

        {loading && <p className="text-xs font-mono text-gray-600">Loading…</p>}
        {error && <p className="text-xs font-mono text-red-400">{error}</p>}

        {!loading && !error && suggestions.length === 0 && (
          <p className="text-xs font-mono text-gray-700">No proposals in queue.</p>
        )}

        {proposed.length > 0 && (
          <div className="mb-6">
            <p className="text-xs font-mono text-amber-500 uppercase tracking-widest mb-2">Pending Review ({proposed.length})</p>
            <div className="space-y-2">
              {proposed.map((p) => (
                <div key={p.id} className="rounded border border-amber-900/30 bg-gray-900/40 px-4 py-3">
                  <div className="flex items-center gap-2 flex-wrap mb-1">
                    <span className="text-xs font-mono text-gray-600 border border-gray-700 rounded px-1">
                      {ACTION_LABELS[p.action] ?? p.action.toUpperCase()}
                    </span>
                    <span className="text-sm font-mono text-gray-200">{p.proposed_name || '—'}</span>
                    {p.proposed_source_type && (
                      <span className="text-xs font-mono text-gray-600">{p.proposed_source_type}</span>
                    )}
                    <span className="text-xs font-mono ml-auto text-amber-500">PROPOSED</span>
                  </div>
                  {p.rationale && <p className="text-xs text-gray-500">{p.rationale}</p>}
                  <div className="flex items-center gap-3 mt-2 flex-wrap">
                    {p.research_case_id && (
                      <Link href={`/investment/research/${p.research_case_id}`} className="text-xs font-mono text-indigo-500 hover:text-indigo-400">
                        → Research Case
                      </Link>
                    )}
                    {p.historical_case_id && (
                      <Link href={`/investment/historical-cases/${p.historical_case_id}`} className="text-xs font-mono text-blue-500 hover:text-blue-400">
                        → Historical Case
                      </Link>
                    )}
                    <div className="flex gap-2 ml-auto">
                      <button
                        onClick={() => handleReview(p.id, 'approved')}
                        className="px-2 py-1 rounded bg-green-900 hover:bg-green-800 text-xs font-mono text-green-100 border border-green-700 transition-colors"
                      >
                        APPROVE
                      </button>
                      <button
                        onClick={() => handleReview(p.id, 'rejected')}
                        className="px-2 py-1 rounded border border-gray-700 hover:border-red-800 text-xs font-mono text-gray-500 hover:text-red-400 transition-colors"
                      >
                        REJECT
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {reviewed.length > 0 && (
          <div>
            <p className="text-xs font-mono text-gray-600 uppercase tracking-widest mb-2">Reviewed ({reviewed.length})</p>
            <div className="space-y-1">
              {reviewed.map((p) => (
                <div key={p.id} className="rounded border border-gray-800 bg-gray-900/20 px-4 py-2">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="text-xs font-mono text-gray-700 border border-gray-800 rounded px-1">
                      {ACTION_LABELS[p.action] ?? p.action.toUpperCase()}
                    </span>
                    <span className={`text-sm font-mono ${p.status === 'rejected' ? 'line-through text-gray-700' : 'text-gray-400'}`}>
                      {p.proposed_name || '—'}
                    </span>
                    <span className={`text-xs font-mono ml-auto ${STATUS_STYLE[p.status] ?? 'text-gray-500'}`}>
                      {p.status.toUpperCase()}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        <div className="mt-6 rounded border border-gray-800 bg-gray-900/20 px-4 py-3">
          <p className="text-xs font-mono text-gray-700">
            GUARDRAIL: Approved proposals are not applied to investment_sources. No apply action exists.
            Application to the global source registry requires a separate manual sprint (Phase 4D+).
          </p>
        </div>

        <p className="text-xs font-mono text-gray-800 mt-4 text-center">
          Este análisis es educativo. No es asesoramiento financiero.
        </p>
      </div>
    </div>
  );
}
