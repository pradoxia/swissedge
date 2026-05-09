'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import {
  fetchResearchCases,
  fetchSituations,
  createResearchCaseFromSituation,
  type ResearchCase,
  type Situation,
} from '@/lib/api';

const STATUSES = ['detected', 'brief_generated', 'under_investigation', 'documented', 'archived', 'published'];
const READINESS = ['monitor', 'not_actionable', 'needs_more_work', 'candidate'];

const STATUS_COLORS: Record<string, string> = {
  detected:             'text-gray-400 border-gray-700',
  brief_generated:      'text-cyan-400 border-cyan-800',
  under_investigation:  'text-violet-400 border-violet-800',
  documented:           'text-green-400 border-green-800',
  archived:             'text-gray-600 border-gray-800',
  published:            'text-emerald-400 border-emerald-800',
};

const READINESS_COLORS: Record<string, string> = {
  monitor:           'text-amber-400 border-amber-800',
  not_actionable:    'text-gray-500 border-gray-700',
  needs_more_work:   'text-violet-400 border-violet-800',
  candidate:         'text-cyan-400 border-cyan-800',
};

function safeStr(v: unknown): string {
  if (typeof v === 'string') return v;
  return '';
}

export default function ResearchListPage() {
  const [cases, setCases] = useState<ResearchCase[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState('');
  const [readinessFilter, setReadinessFilter] = useState('');

  // Create-from-situation panel state
  const [situations, setSituations] = useState<Situation[]>([]);
  const [showCreate, setShowCreate] = useState(false);
  const [selectedSituationId, setSelectedSituationId] = useState('');
  const [createNotes, setCreateNotes] = useState('');
  const [createReadiness, setCreateReadiness] = useState('');
  const [creating, setCreating] = useState(false);
  const [createError, setCreateError] = useState<string | null>(null);

  async function loadCases() {
    try {
      setLoading(true);
      setError(null);
      const data = await fetchResearchCases({
        status: statusFilter || undefined,
        investment_readiness: readinessFilter || undefined,
      });
      setCases(data.research_cases);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load research cases');
    } finally {
      setLoading(false);
    }
  }

  async function loadSituations() {
    try {
      const data = await fetchSituations({ include_archived: false });
      setSituations(data.situations);
    } catch {
      // non-fatal — create panel degrades gracefully
    }
  }

  useEffect(() => { loadCases(); }, [statusFilter, readinessFilter]);

  async function handleCreate() {
    if (!selectedSituationId) return;
    setCreating(true);
    setCreateError(null);
    try {
      await createResearchCaseFromSituation(selectedSituationId, {
        notes: createNotes || undefined,
        investment_readiness: createReadiness || undefined,
      });
      setShowCreate(false);
      setSelectedSituationId('');
      setCreateNotes('');
      setCreateReadiness('');
      loadCases();
    } catch (err) {
      setCreateError(err instanceof Error ? err.message : 'Failed to create research case');
    } finally {
      setCreating(false);
    }
  }

  const counts: Record<string, number> = { all: cases.length };
  for (const s of STATUSES) counts[s] = cases.filter(c => c.status === s).length;

  return (
    <div className="min-h-screen p-8">
      <div className="max-w-5xl mx-auto">

        {/* Nav */}
        <div className="flex items-center gap-3 mb-6 text-xs font-mono text-gray-600">
          <Link href="/" className="hover:text-cyan-400">MISSION CONTROL</Link>
          <span>/</span>
          <Link href="/investment/evaluations" className="hover:text-cyan-400">EVALUATIONS</Link>
          <span>/</span>
          <Link href="/investment/research-inbox" className="hover:text-cyan-400">RESEARCH INBOX</Link>
          <span>/</span>
          <span className="text-cyan-400">RESEARCH CASES</span>
        </div>

        {/* Header */}
        <div className="flex items-start justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold text-cyan-400 font-mono">RESEARCH CASES</h1>
            <p className="text-xs text-gray-500 font-mono mt-1">
              Private research workspace for detected special situations. Create a case from an evaluation, then document tasks, sources and key documents.
            </p>
          </div>
          <div className="flex items-center gap-3">
            <Link
              href="/investment/research-inbox"
              className="px-4 py-2 rounded border border-violet-700 text-violet-400 text-xs font-mono hover:bg-violet-900/30 transition-colors"
            >
              Research Inbox
            </Link>
            <button
              onClick={() => { setShowCreate(v => !v); if (!situations.length) loadSituations(); }}
              className="px-4 py-2 rounded border border-cyan-700 text-cyan-400 text-xs font-mono hover:bg-cyan-900/30 transition-colors"
            >
              + Create from existing evaluation
            </button>
          </div>
        </div>

        {/* Disclaimer strip */}
        <div className="glass-panel rounded p-2 mb-6 border-amber-500/20 text-center">
          <span className="text-xs font-mono text-amber-400/70">
            RESEARCH ONLY — ESTE ANÁLISIS ES EDUCATIVO. NO ES ASESORAMIENTO FINANCIERO.
          </span>
        </div>

        {/* Create panel */}
        {showCreate && (
          <div className="glass-panel rounded-lg p-5 mb-6 border-cyan-700/40">
            <h3 className="text-sm font-mono font-bold text-cyan-400 mb-4">CREATE RESEARCH CASE FROM SITUATION</h3>
            <div className="space-y-3">
              <div>
                <label className="block text-xs font-mono text-gray-400 mb-1">SITUATION</label>
                <select
                  value={selectedSituationId}
                  onChange={e => setSelectedSituationId(e.target.value)}
                  className="w-full bg-gray-900 border border-gray-700 rounded px-3 py-2 text-sm text-gray-200 font-mono"
                >
                  <option value="">— select a situation —</option>
                  {situations.map(s => (
                    <option key={s.id} value={s.id}>
                      {s.company_name} ({safeStr(s.filing_type) || safeStr(s.situation_type) || 'unknown'}) — {s.status}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-xs font-mono text-gray-400 mb-1">INITIAL READINESS (optional)</label>
                <select
                  value={createReadiness}
                  onChange={e => setCreateReadiness(e.target.value)}
                  className="w-full bg-gray-900 border border-gray-700 rounded px-3 py-2 text-sm text-gray-200 font-mono"
                >
                  <option value="">— leave blank —</option>
                  {READINESS.map(r => <option key={r} value={r}>{r}</option>)}
                </select>
              </div>
              <div>
                <label className="block text-xs font-mono text-gray-400 mb-1">NOTES (optional)</label>
                <textarea
                  value={createNotes}
                  onChange={e => setCreateNotes(e.target.value)}
                  rows={2}
                  className="w-full bg-gray-900 border border-gray-700 rounded px-3 py-2 text-sm text-gray-200 font-mono"
                  placeholder="Initial observation..."
                />
              </div>
              {createError && <p className="text-xs text-red-400 font-mono">{createError}</p>}
              <div className="flex gap-3">
                <button
                  onClick={handleCreate}
                  disabled={creating || !selectedSituationId}
                  className="px-4 py-2 rounded bg-cyan-800 hover:bg-cyan-700 disabled:opacity-40 text-xs font-mono text-cyan-100 transition-colors"
                >
                  {creating ? 'CREATING…' : 'CREATE CASE'}
                </button>
                <button
                  onClick={() => setShowCreate(false)}
                  className="px-4 py-2 rounded border border-gray-700 text-xs font-mono text-gray-400 hover:text-gray-200 transition-colors"
                >
                  CANCEL
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Helper text */}
        <p className="text-xs font-mono text-gray-500 mb-4">
          Each research case is a private workspace linked to one detected special situation. Open a case to add tasks, documents, sources and research notes.
        </p>

        {/* Filters */}
        <div className="flex flex-wrap gap-3 mb-6">
          <div className="flex gap-1">
            <button
              onClick={() => setStatusFilter('')}
              className={`px-3 py-1 rounded text-xs font-mono border transition-colors ${statusFilter === '' ? 'border-cyan-500 text-cyan-400 bg-cyan-900/20' : 'border-gray-700 text-gray-500 hover:text-gray-300'}`}
            >
              ALL ({counts.all})
            </button>
            {STATUSES.map(s => counts[s] ? (
              <button
                key={s}
                onClick={() => setStatusFilter(s === statusFilter ? '' : s)}
                className={`px-3 py-1 rounded text-xs font-mono border transition-colors ${statusFilter === s ? 'border-cyan-500 text-cyan-400 bg-cyan-900/20' : 'border-gray-700 text-gray-500 hover:text-gray-300'}`}
              >
                {s.replace('_', ' ')} ({counts[s]})
              </button>
            ) : null)}
          </div>
          <select
            value={readinessFilter}
            onChange={e => setReadinessFilter(e.target.value)}
            className="bg-gray-900 border border-gray-700 rounded px-2 py-1 text-xs font-mono text-gray-400"
          >
            <option value="">All readiness</option>
            {READINESS.map(r => <option key={r} value={r}>{r}</option>)}
          </select>
        </div>

        {/* Table */}
        {loading && <p className="text-gray-500 font-mono text-sm">Loading…</p>}
        {error && <p className="text-red-400 font-mono text-sm">Error: {error}</p>}

        {!loading && !error && cases.length === 0 && (
          <div className="glass-panel rounded-lg p-8 text-center">
            <p className="text-gray-500 font-mono text-sm">No research cases found.</p>
            <p className="text-gray-600 font-mono text-xs mt-2">
              Create one from an existing situation using the button above.
            </p>
          </div>
        )}

        {!loading && cases.length > 0 && (
          <div className="space-y-3">
            {cases.map(rc => (
              <Link
                key={rc.id}
                href={`/investment/research/${rc.id}`}
                className="block glass-panel rounded-lg p-4 hover:border-cyan-400/40 transition-all duration-200 group"
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1 flex-wrap">
                      <span className="px-2 py-0.5 rounded border border-gray-600 text-gray-400 text-xs font-mono">
                        RESEARCH CASE
                      </span>
                      <span className={`px-2 py-0.5 rounded border text-xs font-mono ${STATUS_COLORS[rc.status] ?? 'text-gray-400 border-gray-700'}`}>
                        {rc.status.replace('_', ' ').toUpperCase()}
                      </span>
                      {rc.investment_readiness && (
                        <span className={`px-2 py-0.5 rounded border text-xs font-mono ${READINESS_COLORS[rc.investment_readiness] ?? 'text-gray-400 border-gray-700'}`}>
                          {rc.investment_readiness.replace('_', ' ')}
                        </span>
                      )}
                      {rc.brief && (
                        <span className="px-2 py-0.5 rounded border border-violet-800 text-violet-400 text-xs font-mono">
                          HAS BRIEF
                        </span>
                      )}
                    </div>
                    <p className="text-xs font-mono text-gray-500 truncate">
                      CASE {rc.id.slice(0, 8).toUpperCase()}
                      {rc.situation_id && <span className="text-gray-500"> — Linked Situation: {rc.situation_id.slice(0, 8).toUpperCase()}</span>}
                    </p>
                    {rc.notes && (
                      <p className="text-xs text-gray-400 mt-1 truncate"><span className="text-gray-600 font-mono">Notes: </span>{rc.notes}</p>
                    )}
                  </div>
                  <div className="text-right flex-shrink-0">
                    <p className="text-xs font-mono text-gray-600">
                      {rc.tasks.length}T · {rc.documents.length}D · {rc.sources.length}S
                    </p>
                    <p className="text-xs font-mono text-gray-700 mt-0.5">
                      {new Date(rc.created_at).toLocaleDateString('en-CH', { day: '2-digit', month: 'short', year: '2-digit' })}
                    </p>
                    <span className="mt-2 inline-block px-3 py-1 rounded border border-cyan-700 text-cyan-400 text-xs font-mono group-hover:bg-cyan-900/30 transition-colors">
                      Open Research Case →
                    </span>
                  </div>
                </div>
              </Link>
            ))}
          </div>
        )}

        {/* Footer */}
        <div className="mt-8 text-xs font-mono text-gray-700 text-center">
          PRIVATE RESEARCH DESK — NO PUBLISHING WITHOUT MANUAL APPROVAL
        </div>

      </div>
    </div>
  );
}
