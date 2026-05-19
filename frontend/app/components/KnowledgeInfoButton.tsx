'use client';

import { useState } from 'react';
import { KnowledgeDrawer } from '@/app/components/KnowledgeDrawer';

export function KnowledgeInfoButton({
  knowledgeKey,
  label,
}: {
  knowledgeKey: string | null | undefined;
  label?: string;
}) {
  const [openKey, setOpenKey] = useState<string | null>(null);
  if (!knowledgeKey) return null;

  return (
    <>
      <button
        type="button"
        aria-label={label ? `Open knowledge guidance for ${label}` : 'Open knowledge guidance'}
        title={label ? `Open knowledge guidance for ${label}` : 'Open knowledge guidance'}
        onClick={event => {
          event.stopPropagation();
          setOpenKey(knowledgeKey);
        }}
        style={{
          display: 'inline-flex',
          alignItems: 'center',
          justifyContent: 'center',
          width: 18,
          height: 18,
          borderRadius: 999,
          border: '1px solid var(--border-default)',
          background: 'var(--bg-subtle)',
          color: 'var(--text-muted)',
          fontFamily: 'var(--font-mono)',
          fontSize: 11,
          lineHeight: 1,
          cursor: 'pointer',
          flexShrink: 0,
        }}
      >
        i
      </button>
      <KnowledgeDrawer knowledgeKey={openKey} onClose={() => setOpenKey(null)} />
    </>
  );
}
