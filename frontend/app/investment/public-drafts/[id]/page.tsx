'use client';

import { useEffect, useMemo, useState } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import {
  fetchPublicDraft,
  fetchPublicDraftMarkdown,
  updatePublicDraft,
  type PublicArticleDraft,
} from '@/lib/api';

const DISCLAIMER = 'Este análisis es educativo. No es asesoramiento financiero.';

function allowedStatuses(currentStatus: PublicArticleDraft['status']) {
  if (currentStatus === 'draft') return ['draft', 'in_review', 'archived'] as PublicArticleDraft['status'][];
  if (currentStatus === 'in_review') return ['in_review', 'approved', 'archived'] as PublicArticleDraft['status'][];
  if (currentStatus === 'approved') return ['approved', 'archived'] as PublicArticleDraft['status'][];
  return ['archived'] as PublicArticleDraft['status'][];
}

function checklist(draft: PublicArticleDraft | null) {
  const text = `${draft?.title ?? ''}\n${draft?.content ?? ''}`.toLowerCase();
  return [
    { label: 'Title reviewed', ok: Boolean(draft?.title?.trim()) },
    { label: 'Disclaimer present', ok: Boolean(draft?.content.includes(DISCLAIMER) && draft.disclaimer === DISCLAIMER) },
    { label: 'No buy/sell language', ok: Boolean(draft?.buy_sell_language_check) },
    { label: 'No private notes', ok: !text.includes('private notes') },
    { label: 'No internal IDs', ok: !text.includes('research_case_id') && !text.includes('situation_id') && !text.includes('run_id') },
    { label: 'Sources are public references only', ok: !text.includes('vps') && !text.includes('tailscale') && !text.includes('/api/') },
    { label: 'Not financial advice', ok: Boolean(draft?.content.includes(DISCLAIMER)) },
    { label: 'Manual approval required before external posting', ok: draft?.status === 'approved' },
  ];
}

export default function PublicDraftDetailPage() {
  const params = useParams<{ id: string }>();
  const draftId = params.id;
  const [draft, setDraft] = useState<PublicArticleDraft | null>(null);
  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');
  const [status, setStatus] = useState<PublicArticleDraft['status']>('draft');
  const [markdown, setMarkdown] = useState('');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [msg, setMsg] = useState<{ text: string; ok: boolean } | null>(null);

  async function load() {
    setLoading(true);
    setMsg(null);
    try {
      const data = await fetchPublicDraft(draftId);
      setDraft(data);
      setTitle(data.title ?? '');
      setContent(data.content);
      setStatus(data.status);
      const md = await fetchPublicDraftMarkdown(draftId);
      setMarkdown(md.markdown);
    } catch (err) {
      setMsg({ text: err instanceof Error ? err.message : 'Failed to load public draft', ok: false });
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, [draftId]);

  const checks = useMemo(() => checklist(draft), [draft]);
  const statusOptions = useMemo(() => allowedStatuses(draft?.status ?? 'draft'), [draft?.status]);

  async function saveDraft(nextStatus?: PublicArticleDraft['status']) {
    setSaving(true);
    setMsg(null);
    try {
      const updated = await updatePublicDraft(draftId, {
        title,
        content,
        status: nextStatus ?? status,
      });
      setDraft(updated);
      setStatus(updated.status);
      const md = await fetchPublicDraftMarkdown(draftId);
      setMarkdown(md.markdown);
      setMsg({ text: 'Draft saved.', ok: true });
    } catch (err) {
      setMsg({ text: err instanceof Error ? err.message : 'Failed to save draft', ok: false });
    } finally {
      setSaving(false);
      setTimeout(() => setMsg(null), 5000);
    }
  }

  async function copyMarkdown() {
    try {
      await navigator.clipboard.writeText(markdown);
      setMsg({ text: 'Markdown copied.', ok: true });
    } catch {
      setMsg({ text: 'Copy failed. Select the markdown and copy manually.', ok: false });
    } finally {
      setTimeout(() => setMsg(null), 4000);
    }
  }

  if (loading) {
    return <div className="min-h-screen bg-gray-950 text-gray-500 p-6 font-mono">Loading public draft...</div>;
  }

  if (!draft) {
    return <div className="min-h-screen bg-gray-950 text-red-400 p-6 font-mono">{msg?.text ?? 'Draft not found'}</div>;
  }

  return (
    <div className="min-h-screen bg-gray-950 text-gray-200 p-6">
      <div className="max-w-6xl mx-auto space-y-5">
        <div>
          <Link href="/investment/public-drafts" className="text-xs font-mono text-gray-600 hover:text-gray-400">
            ← PUBLIC DRAFTS
          </Link>
          <h1 className="text-2xl font-mono font-bold text-emerald-400 mt-2">Public Article Draft</h1>
          <p className="text-xs font-mono text-amber-500 mt-2">
            PRIVATE DRAFT - NOT PUBLISHED. Manual approval required before any external posting.
          </p>
          <p className="text-xs font-mono text-gray-600 mt-1">
            CREATED {new Date(draft.created_at).toLocaleString('en-CH')}
            {draft.approved_at ? ` · APPROVED ${new Date(draft.approved_at).toLocaleString('en-CH')}` : ''}
            {draft.published_at ? ` · PUBLISHED ${new Date(draft.published_at).toLocaleString('en-CH')}` : ''}
          </p>
        </div>

        {msg && <div className={`glass-panel rounded p-2 text-xs font-mono ${msg.ok ? 'text-green-400' : 'text-red-400'}`}>{msg.text}</div>}

        <div className="grid grid-cols-1 lg:grid-cols-[1fr_360px] gap-5">
          <div className="space-y-4">
            <div className="glass-panel rounded-lg p-5">
              <label className="block text-xs font-mono text-gray-500 uppercase tracking-wide mb-1">Title</label>
              <input
                value={title}
                onChange={e => setTitle(e.target.value)}
                className="w-full bg-gray-900 border border-gray-700 rounded px-3 py-2 text-sm text-gray-100"
              />
              <label className="block text-xs font-mono text-gray-500 uppercase tracking-wide mt-4 mb-1">Public body / markdown</label>
              <textarea
                value={content}
                onChange={e => setContent(e.target.value)}
                rows={22}
                className="w-full bg-gray-900 border border-gray-700 rounded px-3 py-2 text-sm text-gray-200 font-mono resize-y"
              />
              <div className="flex items-center gap-2 mt-3 flex-wrap">
                <select
                  value={status}
                  onChange={e => setStatus(e.target.value as PublicArticleDraft['status'])}
                  disabled={draft.status === 'archived'}
                  className="bg-gray-900 border border-gray-700 rounded px-2 py-1 text-xs font-mono text-gray-300"
                >
                  {statusOptions.map(s => <option key={s} value={s}>{s.replace(/_/g, ' ')}</option>)}
                </select>
                <button
                  onClick={() => saveDraft()}
                  disabled={saving}
                  className="px-3 py-1.5 rounded bg-emerald-900 hover:bg-emerald-800 disabled:opacity-40 text-xs font-mono text-emerald-100 border border-emerald-700"
                >
                  {saving ? 'SAVING...' : 'SAVE DRAFT'}
                </button>
                {draft.status === 'draft' && (
                  <button
                    onClick={() => saveDraft('in_review')}
                    disabled={saving}
                    className="px-3 py-1.5 rounded bg-blue-900 hover:bg-blue-800 disabled:opacity-40 text-xs font-mono text-blue-100 border border-blue-700"
                  >
                    MOVE TO REVIEW
                  </button>
                )}
                {draft.status === 'in_review' && (
                  <button
                    onClick={() => saveDraft('approved')}
                    disabled={saving}
                    className="px-3 py-1.5 rounded bg-green-900 hover:bg-green-800 disabled:opacity-40 text-xs font-mono text-green-100 border border-green-700"
                  >
                    APPROVE MANUALLY
                  </button>
                )}
                {draft.status !== 'archived' && (
                  <button
                    onClick={() => saveDraft('archived')}
                    disabled={saving}
                    className="px-3 py-1.5 rounded bg-gray-900 hover:bg-gray-800 disabled:opacity-40 text-xs font-mono text-gray-300 border border-gray-700"
                  >
                    ARCHIVE
                  </button>
                )}
              </div>
            </div>

            <div className="glass-panel rounded-lg p-5">
              <div className="flex items-center justify-between gap-3 mb-3">
                <div>
                  <p className="text-xs font-mono text-gray-500 tracking-widest">SUBSTACK-READY MARKDOWN</p>
                  <p className="text-xs font-mono text-gray-700">No API call. No posting. Copy only.</p>
                </div>
                <button
                  onClick={copyMarkdown}
                  className="px-3 py-1.5 rounded border border-gray-700 hover:border-gray-500 text-xs font-mono text-gray-300"
                >
                  COPY MARKDOWN
                </button>
              </div>
              <pre className="max-h-96 overflow-auto whitespace-pre-wrap bg-gray-900 border border-gray-800 rounded p-3 text-xs text-gray-400">
                {markdown}
              </pre>
            </div>
          </div>

          <div className="space-y-4">
            <div className="glass-panel rounded-lg p-5">
              <p className="text-xs font-mono text-gray-500 tracking-widest mb-3">PUBLISHING CHECKLIST</p>
              <div className="space-y-2">
                {checks.map(item => (
                  <div key={item.label} className="flex items-center gap-2">
                    <span className={`text-xs font-mono ${item.ok ? 'text-green-400' : 'text-red-400'}`}>{item.ok ? 'PASS' : 'CHECK'}</span>
                    <span className="text-xs text-gray-400">{item.label}</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="glass-panel rounded-lg p-5">
              <p className="text-xs font-mono text-gray-500 tracking-widest mb-2">BACKEND VALIDATION</p>
              {draft.validation_warnings.length === 0 ? (
                <p className="text-xs font-mono text-green-400">No validation warnings.</p>
              ) : (
                <div className="space-y-1">
                  {draft.validation_warnings.map((warning, i) => (
                    <p key={i} className="text-xs font-mono text-orange-400">- {warning}</p>
                  ))}
                </div>
              )}
              <p className="text-xs font-mono text-amber-500 mt-4">{draft.disclaimer}</p>
            </div>

            <div className="glass-panel rounded-lg p-5 border-amber-500/20">
              <p className="text-xs font-mono text-amber-400 font-bold">MANUAL-ONLY GUARDRAILS</p>
              <p className="text-xs font-mono text-gray-600 mt-2">
                No auto-publish. No Substack API integration. No public posting. Educational content only.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
