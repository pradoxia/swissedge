'use client';

import { Suspense, useEffect, useState } from 'react';
import { useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { fetchPublicDrafts, type PublicArticleDraft } from '@/lib/api';
import { PageHeader, StatusBadge, EmptyState, LoadingState, ErrorBanner, InfoBanner } from '@/app/components/ui';

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
    <div className="page-container">

      <PageHeader
        title="Public Drafts"
        subtitle="Private drafts for review — not published."
        backHref="/investment/research"
        backLabel="Research Cases"
      />

      <InfoBanner variant="guardrail">
        Private drafts only. No Substack API, no public posting, no auto-publish. Manual approval required.
      </InfoBanner>

      {loading && <LoadingState label="Loading drafts…" />}
      {error && <ErrorBanner message={error} />}

      {!loading && !error && drafts.length === 0 && (
        <EmptyState icon="📝" title="No public drafts yet" />
      )}

      {!loading && !error && drafts.length > 0 && (
        <div style={{ display: 'grid', gap: '8px' }}>
          {drafts.map(draft => (
            <Link
              key={draft.id}
              href={`/investment/public-drafts/${draft.id}`}
              style={{ textDecoration: 'none' }}
            >
              <div className="card" style={{ cursor: 'pointer' }}>
                <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: '16px', flexWrap: 'wrap' }}>
                  <div style={{ minWidth: 0 }}>
                    <div style={{ fontWeight: 500, color: 'var(--text-primary)', marginBottom: '4px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {draft.title || 'Untitled public draft'}
                    </div>
                    <div style={{ fontFamily: 'var(--font-mono)', fontSize: '11px', color: 'var(--text-faint)' }}>
                      Created {new Date(draft.created_at).toLocaleString('en-CH')}
                      {draft.approved_at ? ` · Approved ${new Date(draft.approved_at).toLocaleString('en-CH')}` : ''}
                      {draft.published_at ? ` · Published ${new Date(draft.published_at).toLocaleString('en-CH')}` : ''}
                    </div>
                  </div>
                  <StatusBadge value={draft.status} />
                </div>
              </div>
            </Link>
          ))}
        </div>
      )}

    </div>
  );
}

export default function PublicDraftsPage() {
  return (
    <Suspense fallback={<div className="page-container"><LoadingState label="Loading drafts…" /></div>}>
      <PublicDraftsContent />
    </Suspense>
  );
}
