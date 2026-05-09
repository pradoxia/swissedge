'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import {
  fetchHistoricalCases,
  createHistoricalCase,
  type HistoricalCase,
} from '@/lib/api';

const VALID_STATUSES = ['seed', 'reconstructed', 'lessons_extracted', 'source_intel_applied'];

const STATUS_COLORS: Record<string, string> = {
  seed: 'text-gray-500',
  reconstructed: 'text-blue-400',
  lessons_extracted: 'text-emerald-400',
  source_intel_applied: 'text-indigo-400',
};

export default function HistoricalCasesPage() {
  const [cases, setCases] = useState<HistoricalCase[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filterStatus, setFilterStatus] = useState('');

  const [showCreate, setShowCreate] = useState(false);
  const [newCompany, setNewCompany] = useState('');
  const [newSituationType, setNewSituationType] = useState('');
  const [newEventDate, setNewEventDate] = useState('');
  const [newNotes, setNewNotes] = useState('');
  const [creating, setCreating] = useState(false);
  const [createError, setCreateError] = useState<string | null>(null);

  async function load() {
    try {
      setLoading(true);
      setError(null);
      const data = await fetchHistoricalCases({ status: filterStatus || undefined });
      setCases(data.historical_cases);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load historical cases');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { load(); }, [filterStatus]);

  async function handleCreate() {
    if (!newCompany.trim() || !newSituationType.trim()) return;
    setCreating(true);
    setCreateError(null);
    try {
      await createHistoricalCase({
        company_name: newCompany.trim(),
        situation_type: newSituationType.trim(),
        event_date_approx: newEventDate.trim() || undefined,
        seed_notes: newNotes.trim() || undefined,
      });
      setNewCompany('');
      setNewSituationType('');
      setNewEventDate('');
      setNewNotes('');
      setShowCreate(false);
      await load();
    } catch (err) {
      setCreateError(err instanceof Error ? err.message : 'Failed to create historical case');
    } finally {
      setCreating(false);
    }
  }

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100 p-6">
      <div className="max-w-4xl mx-auto">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-xl font-mono font-bold text-white">Historical Cases</h1>
            <p className="text-xs font-mono text-gray-600 mt-0.5">
              Manual workspace for reconstructed special situations. Educational research only.
            </p>
          </div>
          <div className="flex items-center gap-3">
            <Link
              href="/investment/source-intelligence"
              className="px-3 py-1.5 rounded border border-gray-700 hover:border-gray-500 text-xs font-mono text-gray-400 transition-colors"
            >
              SOURCE QUEUE
            </Link>
            <button
              onClick={() => setShowCreate(!showCreate)}
              className="px-3 py-1.5 rounded bg-indigo-900 hover:bg-indigo-800 text-xs font-mono text-indigo-100 border border-indigo-700 transition-colors"
            >
              + NEW HISTORICAL CASE
            </button>
          </div>
        </div>

        {showCreate && (
          <div className="mb-6 rounded border border-indigo-700/50 bg-indigo-950/30 p-4 space-y-3">
            <p className="text-xs font-mono text-indigo-400 font-bold">CREATE HISTORICAL CASE</p>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-xs font-mono text-gray-500 block mb-1">Company Name *</label>
                <input
                  value={newCompany}
                  onChange={e => setNewCompany(e.target.value)}
                  className="w-full bg-gray-900 border border-gray-700 rounded px-2 py-1.5 text-sm text-gray-200 font-mono focus:outline-none focus:border-indigo-600"
                  placeholder="e.g. Dell Technologies"
                />
              </div>
              <div>
                <label className="text-xs font-mono text-gray-500 block mb-1">Situation Type *</label>
                <input
                  value={newSituationType}
                  onChange={e => setNewSituationType(e.target.value)}
                  className="w-full bg-gray-900 border border-gray-700 rounded px-2 py-1.5 text-sm text-gray-200 font-mono focus:outline-none focus:border-indigo-600"
                  placeholder="e.g. spinoff, merger, tender_offer"
                />
              </div>
              <div>
                <label className="text-xs font-mono text-gray-500 block mb-1">Event Date (approx)</label>
                <input
                  value={newEventDate}
                  onChange={e => setNewEventDate(e.target.value)}
                  className="w-full bg-gray-900 border border-gray-700 rounded px-2 py-1.5 text-sm text-gray-200 font-mono focus:outline-none focus:border-indigo-600"
                  placeholder="e.g. 2016-Q4"
                />
              </div>
            </div>
            <div>
              <label className="text-xs font-mono text-gray-500 block mb-1">Seed Notes</label>
              <textarea
                value={newNotes}
                onChange={e => setNewNotes(e.target.value)}
                rows={3}
                className="w-full bg-gray-900 border border-gray-700 rounded px-2 py-1.5 text-sm text-gray-200 font-mono focus:outline-none focus:border-indigo-600 resize-none"
                placeholder="Initial notes about the case…"
              />
            </div>
            {createError && <p className="text-xs font-mono text-red-400">{createError}</p>}
            <div className="flex gap-3">
              <button
                onClick={handleCreate}
                disabled={creating || !newCompany.trim() || !newSituationType.trim()}
                className="px-3 py-1.5 rounded bg-indigo-900 hover:bg-indigo-800 disabled:opacity-40 text-xs font-mono text-indigo-100 border border-indigo-700 transition-colors"
              >
                {creating ? 'CREATING…' : 'CREATE'}
              </button>
              <button
                onClick={() => setShowCreate(false)}
                className="px-3 py-1.5 rounded border border-gray-700 text-xs font-mono text-gray-500 transition-colors"
              >
                CANCEL
              </button>
            </div>
          </div>
        )}

        <div className="mb-4 flex items-center gap-3">
          <label className="text-xs font-mono text-gray-500">Filter by status:</label>
          <select
            value={filterStatus}
            onChange={e => setFilterStatus(e.target.value)}
            className="bg-gray-900 border border-gray-700 rounded px-2 py-1 text-xs font-mono text-gray-300 focus:outline-none focus:border-gray-500"
          >
            <option value="">All</option>
            {VALID_STATUSES.map(s => (
              <option key={s} value={s}>{s}</option>
            ))}
          </select>
        </div>

        {loading && <p className="text-xs font-mono text-gray-600">Loading…</p>}
        {error && <p className="text-xs font-mono text-red-400">{error}</p>}

        {!loading && !error && cases.length === 0 && (
          <p className="text-xs font-mono text-gray-700">No historical cases. Create one to begin.</p>
        )}

        <div className="space-y-2">
          {cases.map((hc) => (
            <Link
              key={hc.id}
              href={`/investment/historical-cases/${hc.id}`}
              className="block rounded border border-gray-800 hover:border-gray-600 bg-gray-900/40 px-4 py-3 transition-colors"
            >
              <div className="flex items-center justify-between">
                <div>
                  <span className="text-sm font-mono text-gray-200">{hc.company_name}</span>
                  <span className="text-xs font-mono text-gray-600 ml-3">{hc.situation_type}</span>
                  {hc.event_date_approx && (
                    <span className="text-xs font-mono text-gray-700 ml-2">{hc.event_date_approx}</span>
                  )}
                </div>
                <span className={`text-xs font-mono ${STATUS_COLORS[hc.status] ?? 'text-gray-500'}`}>
                  {hc.status.toUpperCase()}
                </span>
              </div>
              {hc.seed_notes && (
                <p className="text-xs text-gray-600 mt-1 truncate">{hc.seed_notes}</p>
              )}
            </Link>
          ))}
        </div>

        <p className="text-xs font-mono text-gray-800 mt-6 text-center">
          Este análisis es educativo. No es asesoramiento financiero.
        </p>
      </div>
    </div>
  );
}
