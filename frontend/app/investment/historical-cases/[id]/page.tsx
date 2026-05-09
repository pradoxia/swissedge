'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import {
  fetchHistoricalCase,
  updateHistoricalCase,
  generateHistoricalCaseSourceIntelligencePreview,
  saveHistoricalCaseSourceIntelligenceSuggestions,
  fetchSourceIntelligenceSuggestions,
  reviewSourceIntelligenceSuggestion,
  type HistoricalCase,
  type HistoricalCaseSourceIntelligencePreviewResult,
  type SourceIntelligenceSuggestion,
  type SourceIntelligenceSuggestionRecord,
} from '@/lib/api';

const VALID_STATUSES = ['seed', 'reconstructed', 'lessons_extracted', 'source_intel_applied'];

const STATUS_COLORS: Record<string, string> = {
  seed: 'text-gray-500',
  reconstructed: 'text-blue-400',
  lessons_extracted: 'text-emerald-400',
  source_intel_applied: 'text-indigo-400',
};

const PROPOSAL_STATUS_STYLE: Record<string, string> = {
  proposed: 'text-amber-500',
  approved: 'text-green-500',
  rejected: 'text-gray-600 line-through',
};

const ACTION_LABELS: Record<string, string> = {
  add: 'ADD SOURCE',
  update_priority: 'UPDATE PRIORITY',
  deactivate: 'DEACTIVATE',
};

const CONFIDENCE_COLORS: Record<string, string> = {
  high: 'text-green-400',
  medium: 'text-yellow-400',
  low: 'text-gray-500',
};

export default function HistoricalCaseDetailPage() {
  const params = useParams();
  const id = params.id as string;

  const [hc, setHc] = useState<HistoricalCase | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [actionMsg, setActionMsg] = useState<{ text: string; ok: boolean } | null>(null);

  const [editingNotes, setEditingNotes] = useState(false);
  const [notesText, setNotesText] = useState('');
  const [editingStatus, setEditingStatus] = useState(false);
  const [newStatus, setNewStatus] = useState('');

  const [intelRunning, setIntelRunning] = useState(false);
  const [intelResult, setIntelResult] = useState<HistoricalCaseSourceIntelligencePreviewResult | null>(null);
  const [intelError, setIntelError] = useState<string | null>(null);
  const [savingProposals, setSavingProposals] = useState(false);
  const [saveProposalMsg, setSaveProposalMsg] = useState<string | null>(null);

  const [proposals, setProposals] = useState<SourceIntelligenceSuggestionRecord[]>([]);
  const [reviewMsg, setReviewMsg] = useState<string | null>(null);

  function showAction(text: string, ok: boolean) {
    setActionMsg({ text, ok });
    setTimeout(() => setActionMsg(null), 3000);
  }

  async function load() {
    try {
      setLoading(true);
      setError(null);
      const data = await fetchHistoricalCase(id);
      setHc(data);
      setNotesText(data.seed_notes ?? '');
      setNewStatus(data.status);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load historical case');
    } finally {
      setLoading(false);
    }
  }

  async function loadProposals() {
    try {
      const data = await fetchSourceIntelligenceSuggestions({ historical_case_id: id });
      setProposals(data.suggestions);
    } catch {
      // non-fatal
    }
  }

  useEffect(() => { load(); loadProposals(); }, [id]);

  async function saveNotes() {
    if (!hc) return;
    setSaving(true);
    try {
      const updated = await updateHistoricalCase(id, { seed_notes: notesText });
      setHc(updated);
      setEditingNotes(false);
      showAction('Notes saved', true);
    } catch (err) {
      showAction(err instanceof Error ? err.message : 'Failed to save', false);
    } finally {
      setSaving(false);
    }
  }

  async function saveStatus() {
    if (!hc) return;
    setSaving(true);
    try {
      const updated = await updateHistoricalCase(id, { status: newStatus });
      setHc(updated);
      setEditingStatus(false);
      showAction('Status updated', true);
    } catch (err) {
      showAction(err instanceof Error ? err.message : 'Failed to update status', false);
    } finally {
      setSaving(false);
    }
  }

  async function handleIntelPreview() {
    setIntelRunning(true);
    setIntelError(null);
    setIntelResult(null);
    setSaveProposalMsg(null);
    try {
      const data = await generateHistoricalCaseSourceIntelligencePreview(id);
      setIntelResult(data);
    } catch (err) {
      setIntelError(err instanceof Error ? err.message : 'Source intelligence preview failed');
    } finally {
      setIntelRunning(false);
    }
  }

  async function handleSaveProposals() {
    if (!intelResult || intelResult.suggestions.length === 0) return;
    setSavingProposals(true);
    setSaveProposalMsg(null);
    try {
      const rows = await saveHistoricalCaseSourceIntelligenceSuggestions(id, intelResult.suggestions);
      setSaveProposalMsg(`${rows.length} proposal(s) saved to queue.`);
      await loadProposals();
    } catch (err) {
      setSaveProposalMsg(err instanceof Error ? err.message : 'Failed to save proposals');
    } finally {
      setSavingProposals(false);
    }
  }

  async function handleReview(suggestionId: string, status: 'approved' | 'rejected') {
    setReviewMsg(null);
    try {
      await reviewSourceIntelligenceSuggestion(suggestionId, status);
      setReviewMsg(`Proposal ${status}.`);
      await loadProposals();
    } catch (err) {
      setReviewMsg(err instanceof Error ? err.message : 'Review failed');
    }
  }

  if (loading) return <div className="min-h-screen bg-gray-950 p-6 text-xs font-mono text-gray-600">Loading…</div>;
  if (error) return <div className="min-h-screen bg-gray-950 p-6 text-xs font-mono text-red-400">{error}</div>;
  if (!hc) return null;

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100 p-6">
      <div className="max-w-4xl mx-auto space-y-6">
        <div className="flex items-start justify-between">
          <div>
            <Link href="/investment/historical-cases" className="text-xs font-mono text-gray-600 hover:text-gray-400">
              ← Historical Cases
            </Link>
            <h1 className="text-xl font-mono font-bold text-white mt-1">{hc.company_name}</h1>
            <p className="text-xs font-mono text-gray-500 mt-0.5">{hc.situation_type}</p>
          </div>
          {actionMsg && (
            <p className={`text-xs font-mono ${actionMsg.ok ? 'text-emerald-400' : 'text-red-400'}`}>
              {actionMsg.text}
            </p>
          )}
        </div>

        <div className="rounded border border-gray-800 bg-gray-900/40 p-4 space-y-4">
          <div className="flex items-center gap-4">
            <div>
              <p className="text-xs font-mono text-gray-600">STATUS</p>
              {editingStatus ? (
                <div className="flex items-center gap-2 mt-1">
                  <select
                    value={newStatus}
                    onChange={e => setNewStatus(e.target.value)}
                    className="bg-gray-900 border border-gray-700 rounded px-2 py-1 text-xs font-mono text-gray-300 focus:outline-none"
                  >
                    {VALID_STATUSES.map(s => <option key={s} value={s}>{s}</option>)}
                  </select>
                  <button onClick={saveStatus} disabled={saving} className="text-xs font-mono text-emerald-400 hover:text-emerald-300">SAVE</button>
                  <button onClick={() => setEditingStatus(false)} className="text-xs font-mono text-gray-600">CANCEL</button>
                </div>
              ) : (
                <div className="flex items-center gap-2 mt-1">
                  <span className={`text-sm font-mono ${STATUS_COLORS[hc.status] ?? 'text-gray-400'}`}>{hc.status}</span>
                  <button onClick={() => setEditingStatus(true)} className="text-xs font-mono text-gray-700 hover:text-gray-400">EDIT</button>
                </div>
              )}
            </div>
            <div>
              <p className="text-xs font-mono text-gray-600">EVENT DATE</p>
              <p className="text-sm font-mono text-gray-400 mt-1">{hc.event_date_approx || '—'}</p>
            </div>
            {hc.course_chapter_ref && (
              <div>
                <p className="text-xs font-mono text-gray-600">CHAPTER REF</p>
                <p className="text-sm font-mono text-gray-400 mt-1">{hc.course_chapter_ref}</p>
              </div>
            )}
          </div>

          <div>
            <div className="flex items-center justify-between mb-1">
              <p className="text-xs font-mono text-gray-600">SEED NOTES</p>
              {!editingNotes && (
                <button onClick={() => setEditingNotes(true)} className="text-xs font-mono text-gray-700 hover:text-gray-400">EDIT</button>
              )}
            </div>
            {editingNotes ? (
              <div className="space-y-2">
                <textarea
                  value={notesText}
                  onChange={e => setNotesText(e.target.value)}
                  rows={5}
                  className="w-full bg-gray-900 border border-gray-700 rounded px-2 py-1.5 text-sm text-gray-200 font-mono focus:outline-none focus:border-gray-500 resize-none"
                />
                <div className="flex gap-2">
                  <button onClick={saveNotes} disabled={saving} className="text-xs font-mono text-emerald-400 hover:text-emerald-300 disabled:opacity-40">SAVE</button>
                  <button onClick={() => { setEditingNotes(false); setNotesText(hc.seed_notes ?? ''); }} className="text-xs font-mono text-gray-600">CANCEL</button>
                </div>
              </div>
            ) : (
              <p className="text-sm text-gray-400 whitespace-pre-wrap">{hc.seed_notes || '—'}</p>
            )}
          </div>
        </div>

        <div className="rounded border border-gray-800 bg-gray-900/40 p-4">
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-mono text-gray-500 tracking-widest">SOURCE INTELLIGENCE PREVIEW</span>
            {!intelResult && (
              <button
                onClick={handleIntelPreview}
                disabled={intelRunning}
                className="px-3 py-1.5 rounded bg-indigo-900 hover:bg-indigo-800 disabled:opacity-40 text-xs font-mono text-indigo-100 transition-colors border border-indigo-700"
              >
                {intelRunning ? 'ANALYSING…' : '⬡ GENERATE SOURCE INTELLIGENCE PREVIEW'}
              </button>
            )}
          </div>

          {intelError && <p className="text-xs font-mono text-red-400">{intelError}</p>}
          {intelRunning && <p className="text-xs font-mono text-gray-600 italic">Reviewing case notes… this may take 15–30 seconds.</p>}

          {intelResult && (
            <div className="space-y-3">
              <div className="bg-indigo-950/40 border border-indigo-700/40 rounded px-3 py-2">
                <p className="text-xs font-mono text-indigo-400 font-bold">PROPOSALS ONLY — NOT APPLIED</p>
                <p className="text-xs font-mono text-gray-700 mt-0.5">No crawling. No URL fetching. Saved proposals not applied to investment_sources.</p>
              </div>
              {intelResult.warnings.length > 0 && (
                <div className="bg-orange-950/30 border border-orange-700/30 rounded px-3 py-2">
                  {intelResult.warnings.map((w, i) => <p key={i} className="text-xs font-mono text-orange-600">• {w}</p>)}
                </div>
              )}
              {intelResult.suggestions.length > 0 && (
                <div className="rounded border border-gray-800 p-3 space-y-2">
                  <p className="text-xs font-mono text-gray-500 uppercase tracking-widest">Suggested Sources</p>
                  {intelResult.suggestions.map((sug: SourceIntelligenceSuggestion, i: number) => (
                    <div key={i} className="border-b border-gray-800 last:border-0 pb-2 last:pb-0">
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-mono text-gray-600 border border-gray-700 rounded px-1">{ACTION_LABELS[sug.action] ?? sug.action.toUpperCase()}</span>
                        <span className="text-sm text-gray-300">{sug.source_name}</span>
                        <span className={`text-xs font-mono ml-auto ${CONFIDENCE_COLORS[sug.confidence] ?? 'text-gray-500'}`}>{sug.confidence.toUpperCase()}</span>
                      </div>
                      {sug.reason && <p className="text-xs text-gray-400 mt-0.5">{sug.reason}</p>}
                    </div>
                  ))}
                </div>
              )}
              <p className="text-xs font-mono text-amber-400/60">{intelResult.disclaimer}</p>
              <div className="flex gap-3 items-center flex-wrap pt-2 border-t border-gray-800">
                {intelResult.suggestions.length > 0 && (
                  <button
                    onClick={handleSaveProposals}
                    disabled={savingProposals}
                    className="px-3 py-1.5 rounded bg-emerald-900 hover:bg-emerald-800 disabled:opacity-40 text-xs font-mono text-emerald-100 border border-emerald-700 transition-colors"
                  >
                    {savingProposals ? 'SAVING…' : `SAVE ${intelResult.suggestions.length} PROPOSAL(S)`}
                  </button>
                )}
                <button onClick={() => setIntelResult(null)} className="px-3 py-1.5 rounded border border-gray-700 text-xs font-mono text-gray-500 transition-colors">DISCARD</button>
                {saveProposalMsg && <p className="text-xs font-mono text-emerald-500">{saveProposalMsg}</p>}
              </div>
            </div>
          )}

          {proposals.length > 0 && (
            <div className="mt-4 border-t border-gray-800 pt-4">
              <p className="text-xs font-mono text-gray-500 uppercase tracking-widest mb-2">Saved Proposals ({proposals.length})</p>
              {reviewMsg && <p className="text-xs font-mono text-emerald-500 mb-2">{reviewMsg}</p>}
              <div className="space-y-2">
                {proposals.map((p) => (
                  <div key={p.id} className="rounded border border-gray-800 px-3 py-2">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="text-xs font-mono text-gray-600 border border-gray-700 rounded px-1">{ACTION_LABELS[p.action] ?? p.action.toUpperCase()}</span>
                      <span className="text-sm text-gray-300">{p.proposed_name || '—'}</span>
                      <span className={`text-xs font-mono ml-auto ${PROPOSAL_STATUS_STYLE[p.status] ?? 'text-gray-500'}`}>{p.status.toUpperCase()}</span>
                    </div>
                    {p.rationale && <p className="text-xs text-gray-500 mt-1">{p.rationale}</p>}
                    {p.status === 'proposed' && (
                      <div className="flex gap-2 mt-2">
                        <button onClick={() => handleReview(p.id, 'approved')} className="px-2 py-1 rounded bg-green-900 hover:bg-green-800 text-xs font-mono text-green-100 border border-green-700 transition-colors">APPROVE</button>
                        <button onClick={() => handleReview(p.id, 'rejected')} className="px-2 py-1 rounded border border-gray-700 hover:border-red-800 text-xs font-mono text-gray-500 hover:text-red-400 transition-colors">REJECT</button>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        <p className="text-xs font-mono text-gray-800 text-center">{hc.disclaimer}</p>
      </div>
    </div>
  );
}
