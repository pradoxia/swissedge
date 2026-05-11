'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import {
  fetchHistoricalCases,
  createHistoricalCase,
  type HistoricalCase,
} from '@/lib/api';
import { PageHeader, StatusBadge, EmptyState, LoadingState, ErrorBanner, InfoBanner } from '@/app/components/ui';

const VALID_STATUSES = ['seed', 'reconstructed', 'lessons_extracted', 'source_intel_applied'];

const inputStyle: React.CSSProperties = {
  width: '100%',
  padding: '7px 10px',
  background: 'var(--bg-subtle)',
  border: '1px solid var(--border-default)',
  borderRadius: '7px',
  fontFamily: 'var(--font-mono)',
  fontSize: '12px',
  color: 'var(--text-primary)',
  outline: 'none',
};

const labelStyle: React.CSSProperties = {
  display: 'block',
  fontFamily: 'var(--font-mono)',
  fontSize: '10px',
  fontWeight: 500,
  letterSpacing: '0.1em',
  textTransform: 'uppercase',
  color: 'var(--text-faint)',
  marginBottom: '6px',
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
    <div className="page-container">

      <PageHeader
        title="Historical Cases"
        subtitle="Manual workspace for reconstructed special situations. Educational research only."
        backHref="/investment/source-intelligence"
        backLabel="Source Intelligence"
        actions={
          <button onClick={() => setShowCreate(v => !v)} className="btn btn--primary btn--sm">
            + New Historical Case
          </button>
        }
      />

      {/* Create form */}
      {showCreate && (
        <div className="card" style={{ marginBottom: '24px' }}>
          <div className="section-header" style={{ marginBottom: '14px' }}>
            <span className="section-title">Create Historical Case</span>
            <div className="section-line" />
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginBottom: '12px' }}>
            <div>
              <label style={labelStyle}>Company Name *</label>
              <input
                value={newCompany}
                onChange={e => setNewCompany(e.target.value)}
                style={inputStyle}
                placeholder="e.g. Dell Technologies"
              />
            </div>
            <div>
              <label style={labelStyle}>Situation Type *</label>
              <input
                value={newSituationType}
                onChange={e => setNewSituationType(e.target.value)}
                style={inputStyle}
                placeholder="e.g. spinoff, merger, tender_offer"
              />
            </div>
            <div>
              <label style={labelStyle}>Event Date (approx)</label>
              <input
                value={newEventDate}
                onChange={e => setNewEventDate(e.target.value)}
                style={inputStyle}
                placeholder="e.g. 2016-Q4"
              />
            </div>
          </div>
          <div style={{ marginBottom: '12px' }}>
            <label style={labelStyle}>Seed Notes</label>
            <textarea
              value={newNotes}
              onChange={e => setNewNotes(e.target.value)}
              rows={3}
              style={{ ...inputStyle, resize: 'vertical' }}
              placeholder="Initial notes about the case…"
            />
          </div>
          {createError && <ErrorBanner message={createError} />}
          <div style={{ display: 'flex', gap: '8px' }}>
            <button
              onClick={handleCreate}
              disabled={creating || !newCompany.trim() || !newSituationType.trim()}
              className="btn btn--primary btn--sm"
            >
              {creating ? 'Creating…' : 'Create'}
            </button>
            <button onClick={() => setShowCreate(false)} className="btn btn--ghost btn--sm">Cancel</button>
          </div>
        </div>
      )}

      {/* Filter */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '20px' }}>
        <label style={{ ...labelStyle, marginBottom: 0 }}>Status</label>
        <select
          value={filterStatus}
          onChange={e => setFilterStatus(e.target.value)}
          style={{ padding: '6px 10px', background: 'var(--bg-subtle)', border: '1px solid var(--border-default)', borderRadius: '7px', fontFamily: 'var(--font-mono)', fontSize: '12px', color: 'var(--text-secondary)', outline: 'none' }}
        >
          <option value="">All</option>
          {VALID_STATUSES.map(s => <option key={s} value={s}>{s}</option>)}
        </select>
      </div>

      {loading && <LoadingState label="Loading historical cases…" />}
      {error && <ErrorBanner message={error} />}

      {!loading && !error && cases.length === 0 && (
        <EmptyState icon="📚" title="No historical cases" description="Create one to begin documenting reconstructed situations." />
      )}

      {!loading && !error && cases.length > 0 && (
        <div style={{ display: 'grid', gap: '8px' }}>
          {cases.map(hc => (
            <Link key={hc.id} href={`/investment/historical-cases/${hc.id}`} style={{ textDecoration: 'none' }}>
              <div className="card" style={{ cursor: 'pointer' }}>
                <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: '12px' }}>
                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '4px', flexWrap: 'wrap' }}>
                      <span style={{ fontFamily: 'var(--font-mono)', fontSize: '13px', color: 'var(--text-primary)', fontWeight: 500 }}>
                        {hc.company_name}
                      </span>
                      <span style={{ fontFamily: 'var(--font-mono)', fontSize: '11px', color: 'var(--text-faint)' }}>
                        {hc.situation_type}
                      </span>
                      {hc.event_date_approx && (
                        <span style={{ fontFamily: 'var(--font-mono)', fontSize: '11px', color: 'var(--text-faint)' }}>
                          {hc.event_date_approx}
                        </span>
                      )}
                    </div>
                    {hc.seed_notes && (
                      <p style={{ fontFamily: 'var(--font-sans)', fontSize: '12px', color: 'var(--text-secondary)', margin: 0, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                        {hc.seed_notes}
                      </p>
                    )}
                  </div>
                  <StatusBadge value={hc.status} />
                </div>
              </div>
            </Link>
          ))}
        </div>
      )}

      <InfoBanner variant="guardrail" >
        Este análisis es educativo. No es asesoramiento financiero.
      </InfoBanner>

    </div>
  );
}
