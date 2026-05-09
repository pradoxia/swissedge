'use client';

import { Suspense, useEffect, useState } from 'react';
import { useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { fetchPublicDrafts, type PublicArticleDraft } from '@/lib/api';

const STATUS_COLORS: Record<string, string> = {
  draft: 'text-gray-400 border-gray-700',
  in_review: 'text-amber-400 border-amber-800',
  approved: 'text-green-400 border-green-800',
  archived: 'text-gray-600 border-gray-800',
};

function PublicDraftsContent() {
  const searchParams = useSearchParams();
  const researchCaseId = searchParams.get('research_case_id') || undefined;
  const [drafts, setDrafts] = useState<PublicArticleDraft[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      setLoading(true);
      setError(null);
      try {
        const data = await fetchPublicDrafts({ research_case_id: researchCaseId });
        setDrafts(data.public_drafts);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load public drafts');
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [researchCaseId]);

  return (
    <div className="min-h-screen bg-gray-950 text-gray-200 p-6">
      <div className="max-w-5xl mx-auto">
        <div className="mb-6">
          <p className="text-xs font-mono text-gray-600 tracking-widest uppercase mb-1">Investment Publishing</p>
          <h1 className="text-2xl font-mono font-bold text-emerald-400">Public Drafts</h1>
          <p className="text-xs font-mono text-amber-500 mt-2">
            PRIVATE DRAFTS - NOT PUBLISHED. No Substack API, no public posting, no auto-publish.
          </p>
        </div>

        {loading && <p className="text-sm font-mono text-gray-500">Loading drafts...</p>}
        {error && <p className="text-sm font-mono text-red-400">{error}</p>}

        {!loading && !error && drafts.length === 0 && (
          <div className="glass-panel rounded-lg p-5">
            <p className="text-sm text-gray-500">No public drafts yet.</p>
          </div>
        )}

        <div className="space-y-3">
          {drafts.map(draft => (
            <Link
              key={draft.id}
              href={`/investment/public-drafts/${draft.id}`}
              className="block glass-panel rounded-lg p-4 hover:border-emerald-700/50 transition-colors"
            >
              <div className="flex items-start justify-between gap-4 flex-wrap">
                <div className="min-w-0">
                  <h2 className="text-sm font-semibold text-gray-100 truncate">
                    {draft.title || 'Untitled public draft'}
                  </h2>
                  <p className="text-xs font-mono text-gray-600 mt-1">
                    CREATED {new Date(draft.created_at).toLocaleString('en-CH')}
                    {draft.approved_at ? ` · APPROVED ${new Date(draft.approved_at).toLocaleString('en-CH')}` : ''}
                    {draft.published_at ? ` · PUBLISHED ${new Date(draft.published_at).toLocaleString('en-CH')}` : ''}
                  </p>
                </div>
                <span className={`px-2 py-0.5 rounded border text-xs font-mono ${STATUS_COLORS[draft.status] ?? STATUS_COLORS.draft}`}>
                  {draft.status.replace(/_/g, ' ').toUpperCase()}
                </span>
              </div>
            </Link>
          ))}
        </div>
      </div>
    </div>
  );
}

export default function PublicDraftsPage() {
  return (
    <Suspense fallback={<div className="min-h-screen bg-gray-950 text-gray-500 p-6 font-mono">Loading drafts...</div>}>
      <PublicDraftsContent />
    </Suspense>
  );
}
