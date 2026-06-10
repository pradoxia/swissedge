'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { fetchSituation, archiveSituation, updateSituationStatus, saveNotes, runV2Preview, fetchResearchCases, createResearchCaseFromSituation, type Situation, type V2PreviewResult, type ResearchCase } from '@/lib/api';
import { PageHeader, SectionCard, StatusBadge, LoadingState, ErrorBanner, InfoBanner } from '@/app/components/ui';

function inferSource(s: Situation): string {
  if (s.filing_url?.includes('sec.gov')) return 'SEC EDGAR';
  if (s.filing_type) return 'SEC Filing';
  return 'Unknown';
}

const LABEL_STYLE: React.CSSProperties = {
  fontFamily: 'var(--font-mono)',
  fontSize: 11,
  color: 'var(--text-muted)',
  textTransform: 'uppercase',
  letterSpacing: '0.04em',
  marginBottom: 4,
};

const VALUE_STYLE: React.CSSProperties = {
  fontFamily: 'var(--font-mono)',
  fontSize: 13,
  color: 'var(--text-primary)',
};

function Field({ label, children, span2 }: { label: string; children: React.ReactNode; span2?: boolean }) {
  return (
    <div style={span2 ? { gridColumn: '1 / -1' } : undefined}>
      <div style={LABEL_STYLE}>{label}</div>
      <div style={VALUE_STYLE}>{children}</div>
    </div>
  );
}

function recommendationBadgeClass(rec: string | null | undefined): string {
  switch (rec) {
    case 'INVESTIGATE': return 'status-badge--manual';
    case 'MONITOR':     return 'status-badge--partial';
    case 'AVOID':
    case 'SELL':        return 'status-badge--danger';
    default:            return 'status-badge--readonly';
  }
}

export default function EvaluationDetailPage() {
  const params = useParams();
  const router = useRouter();
  const id = params.id as string;

  const [situation, setSituation] = useState<Situation | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showRawJson, setShowRawJson] = useState(false);
  const [notesText, setNotesText] = useState('');
  const [notesSaving, setNotesSaving] = useState(false);
  const [notesSaved, setNotesSaved] = useState(false);
  const [notesError, setNotesError] = useState<string | null>(null);
  const [v2Running, setV2Running] = useState(false);
  const [v2Result, setV2Result] = useState<V2PreviewResult | null>(null);
  const [v2Error, setV2Error] = useState<string | null>(null);
  const [showV2Result, setShowV2Result] = useState(false);
  const [actionMessage, setActionMessage] = useState<{ text: string; type: 'success' | 'error' } | null>(null);

  const [researchCase, setResearchCase] = useState<ResearchCase | null>(null);
  const [rcLoading, setRcLoading] = useState(true);
  const [rcError, setRcError] = useState<string | null>(null);
  const [rcCreating, setRcCreating] = useState(false);
  const [rcMessage, setRcMessage] = useState<{ text: string; isError: boolean } | null>(null);

  const isTestData = (situation: Situation): boolean => {
    const summary = situation.evaluation?.summary || '';
    const title = situation.evaluation?.title || '';
    return (
      situation.company_name.includes('Example') ||
      (situation.ticker?.startsWith('EX') ?? false) ||
      summary.includes('Manual v2 dashboard validation') ||
      title.includes('Manual v2 dashboard validation') ||
      situation.filing_url === 'https://www.sec.gov/'
    );
  };

  const showAction = (text: string, type: 'success' | 'error') => {
    setActionMessage({ text, type });
    setTimeout(() => setActionMessage(null), 3000);
  };

  const handleStatusChange = async (status: string) => {
    if (!situation) return;

    try {
      await updateSituationStatus(situation.id, status);
      const updated = await fetchSituation(situation.id);
      setSituation(updated);
      const labels: Record<string, string> = {
        reviewing: 'Marked as Reviewing',
        watchlist: 'Added to Watchlist',
        ignored: 'Marked as Ignored',
      };
      showAction(labels[status] ?? `Status updated to ${status}`, 'success');
    } catch (err) {
      showAction(`Failed to update status: ${err instanceof Error ? err.message : 'Unknown error'}`, 'error');
    }
  };

  const handleSaveNotes = async () => {
    if (!situation) return;
    setNotesSaving(true);
    setNotesSaved(false);
    setNotesError(null);
    try {
      await saveNotes(situation.id, notesText);
      setNotesSaved(true);
      setTimeout(() => setNotesSaved(false), 2000);
    } catch (err) {
      setNotesError(err instanceof Error ? err.message : 'Failed to save notes');
    } finally {
      setNotesSaving(false);
    }
  };

  const handleArchive = async () => {
    if (!situation) return;

    if (!confirm(`Archive "${situation.company_name}"? This will hide it from the main list.`)) {
      return;
    }

    try {
      await archiveSituation(situation.id);
      router.push('/investment/evaluations');
    } catch (err) {
      showAction(`Failed to archive: ${err instanceof Error ? err.message : 'Unknown error'}`, 'error');
    }
  };

  const handleRunV2Preview = async () => {
    if (!situation) return;

    const confirmed = confirm(
      'Run v2 evaluation preview?\n\nThis will make a live AI call.\nResult is PREVIEW ONLY — nothing will be saved to DB.\nThe v1/default evaluator is not affected.\n\nContinue?'
    );
    if (!confirmed) return;

    setV2Running(true);
    setV2Result(null);
    setV2Error(null);
    setShowV2Result(false);

    try {
      const result = await runV2Preview(situation);
      setV2Result(result);
      setShowV2Result(true);
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'v2 preview failed';
      if (msg.includes('429') || msg.toLowerCase().includes('limit')) {
        setV2Error(`DAILY LIMIT REACHED — ${msg}`);
      } else {
        setV2Error(msg);
      }
    } finally {
      setV2Running(false);
    }
  };

  useEffect(() => {
    async function loadSituation() {
      try {
        setLoading(true);
        setError(null);
        const data = await fetchSituation(id);
        setSituation(data);
        setNotesText(data.notes ?? '');
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load evaluation');
      } finally {
        setLoading(false);
      }
    }

    if (id) {
      loadSituation();
    }
  }, [id]);

  useEffect(() => {
    async function loadResearchCase() {
      try {
        setRcLoading(true);
        setRcError(null);
        const data = await fetchResearchCases({ situation_id: id });
        setResearchCase(data.research_cases.length > 0 ? data.research_cases[0] : null);
      } catch {
        setRcError('Could not load research case. Try again.');
      } finally {
        setRcLoading(false);
      }
    }
    if (id) loadResearchCase();
  }, [id]);

  async function handleCreateResearchCase() {
    setRcCreating(true);
    setRcMessage(null);
    try {
      const created = await createResearchCaseFromSituation(id);
      router.push(`/investment/research/${created.id}`);
    } catch (err) {
      const msg = err instanceof Error ? err.message : '';
      if (msg.includes('409')) {
        try {
          const recovery = await fetchResearchCases({ situation_id: id });
          if (recovery.research_cases.length > 0) {
            router.push(`/investment/research/${recovery.research_cases[0].id}`);
          } else {
            setRcMessage({ text: 'A research case already exists — ', isError: false });
          }
        } catch {
          setRcMessage({ text: 'A research case already exists — ', isError: false });
        }
      } else {
        setRcError('Could not create research case. Try again.');
      }
    } finally {
      setRcCreating(false);
    }
  }

  const formatValue = (value: any) => {
    if (value === null || value === undefined) return '-';
    if (typeof value === 'boolean') return value ? 'YES' : 'NO';
    if (typeof value === 'number') return value.toString();
    return value;
  };

  if (loading) {
    return (
      <div className="page-container--wide">
        <LoadingState label="Loading evaluation data…" />
      </div>
    );
  }

  if (error || !situation) {
    return (
      <div className="page-container--wide">
        <ErrorBanner message={error || 'Evaluation not found'} />
        <Link href="/investment/evaluations" className="nav-back">← Return to queue</Link>
      </div>
    );
  }

  const evaluation = situation.evaluation || {};
  const humanReviewItems = evaluation.human_review_required || [];
  const riskFlags = evaluation.risk_flags || [];
  const prohibitedInferences = evaluation.prohibited_inferences_detected || [];
  const missingDocuments = evaluation.missing_documents || [];
  const latestAmendment = evaluation.latest_amendment_check || {};

  const v2CanRun = !!(situation.company_name && situation.filing_type && situation.detected_at && situation.filing_url);
  const discoverySource = inferSource(situation);

  return (
    <div className="page-container--wide">

      <PageHeader
        title={situation.company_name}
        subtitle={`Evaluation detail (legacy surface) · ID ${situation.id.substring(0, 8)} · day-to-day triage lives in the Workbench`}
        backHref="/investment/evaluations"
        backLabel="Evaluations Queue"
        badge={<StatusBadge value={situation.status ?? 'unknown'} />}
        actions={
          <div style={{ display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap' }}>
            {actionMessage && (
              <span style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: actionMessage.type === 'success' ? '#2e7d32' : '#c62828' }}>
                {actionMessage.type === 'success' ? '✓' : '⚠'} {actionMessage.text}
              </span>
            )}
            <Link href={`/investment/situations/${situation.id}`} className="btn btn--primary btn--sm">
              Open in Workbench →
            </Link>
            {situation.status !== 'reviewing' && situation.status !== 'archived' && (
              <button onClick={() => handleStatusChange('reviewing')} className="btn btn--secondary btn--sm">Mark Reviewing</button>
            )}
            {situation.status !== 'watchlist' && situation.status !== 'archived' && (
              <button onClick={() => handleStatusChange('watchlist')} className="btn btn--secondary btn--sm">Add to Watchlist</button>
            )}
            {situation.status !== 'ignored' && situation.status !== 'archived' && (
              <button onClick={() => handleStatusChange('ignored')} className="btn btn--ghost btn--sm">Ignore</button>
            )}
            {situation.status !== 'archived' && (
              <button onClick={handleArchive} className="btn btn--ghost btn--sm">Archive</button>
            )}
          </div>
        }
      />

      {isTestData(situation) && (
        <InfoBanner variant="warning">
          ⚠ TEST/DEMO EVALUATION — Not a real investment candidate
        </InfoBanner>
      )}

      {/* Decision Summary */}
      <SectionCard title="Decision Summary" accent className="mb-6">
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: '16px 24px' }}>
          <Field label="Company"><strong>{situation.company_name}</strong></Field>
          {situation.ticker && <Field label="Ticker">{situation.ticker}</Field>}
          {situation.filing_type && <Field label="Filing Type">{situation.filing_type}</Field>}
          <Field label="Workflow Status"><StatusBadge value={situation.status ?? 'unknown'} /></Field>
          <Field label="Evaluator Version">
            <span className="status-badge status-badge--readonly">{situation.evaluator_version ?? 'v1 (default)'}</span>
          </Field>
          <Field label="Discovery Source">{discoverySource}</Field>
          {situation.selected_playbook && <Field label="Playbook">{situation.selected_playbook}</Field>}
          {situation.playbook_status && (
            <Field label="Playbook Status"><StatusBadge value={situation.playbook_status} /></Field>
          )}
          {situation.recommendation && (
            <Field label="Recommendation">
              <span className={`status-badge ${recommendationBadgeClass(situation.recommendation)}`}>{situation.recommendation}</span>
            </Field>
          )}
          {situation.evaluator_confidence && <Field label="Confidence">{situation.evaluator_confidence}</Field>}
          {(situation.human_review_required_count ?? 0) > 0 && (
            <Field label="Human Review Items">
              <span className="status-badge status-badge--partial">{situation.human_review_required_count}</span>
            </Field>
          )}
          {(situation.risk_flags_count ?? 0) > 0 && (
            <Field label="Risk Flags">
              <span className="status-badge status-badge--danger">{situation.risk_flags_count}</span>
            </Field>
          )}
          {situation.filing_url && (
            <Field label="Filing URL" span2>
              <a href={situation.filing_url} target="_blank" rel="noopener noreferrer" style={{ wordBreak: 'break-all' }}>
                {situation.filing_url}
              </a>
            </Field>
          )}
        </div>
      </SectionCard>

      {/* Research Case */}
      <SectionCard title="Research Case" className="mb-6">
        <InfoBanner variant="guardrail">Este análisis es educativo. No es asesoramiento financiero.</InfoBanner>
        {rcLoading && <div style={{ ...VALUE_STYLE, color: 'var(--text-muted)' }}>Loading research case…</div>}
        {!rcLoading && rcError && (
          <div>
            <div style={{ ...VALUE_STYLE, color: '#c62828' }}>{rcError}</div>
            <button
              onClick={() => {
                setRcError(null);
                setRcLoading(true);
                fetchResearchCases({ situation_id: id })
                  .then(d => setResearchCase(d.research_cases.length > 0 ? d.research_cases[0] : null))
                  .catch(() => setRcError('Could not load research case. Try again.'))
                  .finally(() => setRcLoading(false));
              }}
              className="btn btn--ghost btn--sm"
              style={{ marginTop: 8 }}
            >
              Retry
            </button>
          </div>
        )}
        {!rcLoading && !rcError && researchCase && (
          <div style={{ display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap' }}>
            <StatusBadge value={researchCase.status} />
            {researchCase.investment_readiness && <StatusBadge value={researchCase.investment_readiness} />}
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--text-faint)' }}>
              UPDATED: {new Date(researchCase.updated_at).toLocaleString('en-CH')}
            </span>
            <Link href={`/investment/research/${researchCase.id}`} className="btn btn--secondary btn--sm">
              Open Research Case →
            </Link>
          </div>
        )}
        {!rcLoading && !rcError && !researchCase && (
          <div style={{ display: 'flex', alignItems: 'center', gap: 16, flexWrap: 'wrap' }}>
            <span style={{ ...VALUE_STYLE, color: 'var(--text-muted)' }}>No research case yet.</span>
            {rcMessage ? (
              <span style={{ ...VALUE_STYLE, color: 'var(--text-muted)' }}>
                {rcMessage.text}
                <Link href="/investment/research" style={{ textDecoration: 'underline' }}>view research cases</Link>
              </span>
            ) : (
              <button onClick={handleCreateResearchCase} disabled={rcCreating} className="btn btn--primary btn--sm">
                {rcCreating ? 'Creating…' : 'Create Research Case'}
              </button>
            )}
          </div>
        )}
      </SectionCard>

      {/* Evaluator v2 Preview */}
      <SectionCard title="Evaluator v2 Preview" className="mb-6">
        <InfoBanner variant="warning">
          PREVIEW ONLY — NOT SAVED TO DB. Manual preview only. Does not change the v1/default evaluator. Requires explicit confirmation.
        </InfoBanner>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap' }}>
          {v2CanRun ? (
            <button onClick={handleRunV2Preview} disabled={v2Running} className="btn btn--secondary btn--sm">
              {v2Running ? 'Running v2…' : 'Run v2 preview (preview only)'}
            </button>
          ) : (
            <>
              <button disabled className="btn btn--ghost btn--sm" style={{ cursor: 'not-allowed', opacity: 0.6 }}>
                Run v2 preview (preview only)
              </button>
              <span style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--text-faint)' }}>
                Missing required fields (company, filing_type, date, or url)
              </span>
            </>
          )}
          {v2Result && (
            <button onClick={() => setShowV2Result(!showV2Result)} className="btn btn--ghost btn--sm">
              {showV2Result ? '▼ Hide result' : '▶ Show result'}
            </button>
          )}
        </div>
        {v2Error && (
          <div style={{ marginTop: 12 }}>
            <ErrorBanner message={v2Error} />
          </div>
        )}
        {v2Result && showV2Result && (
          <div style={{ marginTop: 16 }}>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 16, marginBottom: 12, fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--text-muted)' }}>
              <span>Version: <strong>{v2Result.evaluator_version}</strong></span>
              {v2Result.fallback_occurred && <span style={{ color: '#7a5a00' }}>⚠ Fallback to v1</span>}
              {v2Result.usage?.model && <span>Model: {v2Result.usage.model}</span>}
              {v2Result.usage?.input_tokens != null && (
                <span>Tokens: {v2Result.usage.input_tokens}in / {v2Result.usage.output_tokens}out</span>
              )}
              <span style={{ color: v2Result.daily_limit.remaining === 0 ? '#c62828' : 'var(--text-muted)' }}>
                Daily: {v2Result.daily_limit.used}/{v2Result.daily_limit.limit} used ({v2Result.daily_limit.remaining} remaining)
              </span>
            </div>
            <pre style={{ padding: 16, background: 'var(--bg-subtle, #f5f4f1)', borderRadius: 8, overflowX: 'auto', fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--text-secondary)', border: '1px solid var(--border-subtle)' }}>
              {JSON.stringify(v2Result.result, null, 2)}
            </pre>
          </div>
        )}
      </SectionCard>

      {/* Filing Information */}
      <SectionCard title="Filing Information" className="mb-6">
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(240px, 1fr))', gap: '16px 24px' }}>
          <Field label="Company">{situation.company_name}</Field>
          <Field label="Ticker">{formatValue(situation.ticker)}</Field>
          <Field label="Filing Type">{formatValue(situation.filing_type)}</Field>
          <Field label="Detected At">{situation.detected_at ? new Date(situation.detected_at).toLocaleString() : '-'}</Field>
          {situation.filing_url && (
            <Field label="Source URL" span2>
              <a href={situation.filing_url} target="_blank" rel="noopener noreferrer" style={{ wordBreak: 'break-all' }}>
                {situation.filing_url}
              </a>
            </Field>
          )}
        </div>
      </SectionCard>

      {/* Evaluation Summary */}
      <SectionCard title="Evaluation Summary" className="mb-6">
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(240px, 1fr))', gap: '16px 24px' }}>
          <Field label="Evaluator Version">
            <span className="status-badge status-badge--readonly">{formatValue(situation.evaluator_version)}</span>
          </Field>
          <Field label="Playbook Status">
            {situation.playbook_status ? <StatusBadge value={situation.playbook_status} /> : '-'}
          </Field>
          <Field label="Selected Playbook">{formatValue(situation.selected_playbook)}</Field>
          <Field label="Situation Type">{formatValue(situation.v2_situation_type)}</Field>
          <Field label="Subtype">{formatValue(situation.v2_subtype)}</Field>
          <Field label="Recommendation">{formatValue(situation.recommendation)}</Field>
          <Field label="Evaluator Confidence">{formatValue(situation.evaluator_confidence)}</Field>
          {situation.fallback_occurred && (
            <Field label="Fallback Occurred" span2>
              <span className="status-badge status-badge--partial">YES — FELL BACK TO V1</span>
            </Field>
          )}
        </div>
      </SectionCard>

      {/* Human Review Required */}
      {humanReviewItems.length > 0 && (
        <SectionCard title={`Human Review Required (${humanReviewItems.length})`} className="mb-6">
          <div style={{ display: 'grid', gap: 12 }}>
            {humanReviewItems.map((item: any, index: number) => (
              <div key={index} style={{ borderLeft: '3px solid #f0d080', background: '#fffbf0', padding: '12px 16px', borderRadius: 6 }}>
                <div style={{ ...VALUE_STYLE, fontWeight: 600, marginBottom: 6 }}>{item.item || 'Review item'}</div>
                {item.reason && (
                  <div style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--text-muted)', marginBottom: 2 }}>
                    REASON: {item.reason}
                  </div>
                )}
                {item.required_human_input && (
                  <div style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--text-muted)', marginBottom: 2 }}>
                    REQUIRED: {item.required_human_input}
                  </div>
                )}
                {item.related_playbook && (
                  <div style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--text-muted)', marginTop: 6 }}>
                    📋 {item.related_playbook}
                  </div>
                )}
                {item.blocking_for_recommendation && (
                  <div style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: '#7a5a00', marginTop: 6 }}>⚠ BLOCKING</div>
                )}
              </div>
            ))}
          </div>
        </SectionCard>
      )}

      {/* Risk Flags */}
      {riskFlags.length > 0 && (
        <SectionCard title={`Risk Flags (${riskFlags.length})`} className="mb-6">
          <div style={{ display: 'grid', gap: 12 }}>
            {riskFlags.map((flag: any, index: number) => (
              <div key={index} style={{ borderLeft: '3px solid #e57373', background: '#fdf3f3', padding: '12px 16px', borderRadius: 6 }}>
                <div style={VALUE_STYLE}>
                  ⚠ {typeof flag === 'string' ? flag : flag.flag || flag.risk_type || 'Risk detected'}
                </div>
                {typeof flag === 'object' && flag.description && (
                  <div style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--text-muted)', marginTop: 4 }}>{flag.description}</div>
                )}
                {typeof flag === 'object' && flag.severity && (
                  <div style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: '#c62828', marginTop: 6 }}>SEVERITY: {flag.severity}</div>
                )}
              </div>
            ))}
          </div>
        </SectionCard>
      )}

      {/* Prohibited Inferences */}
      {prohibitedInferences.length > 0 && (
        <SectionCard title={`⚠ Prohibited Inferences Detected (${prohibitedInferences.length})`} className="mb-6">
          <div style={{ display: 'grid', gap: 12 }}>
            {prohibitedInferences.map((inference: any, index: number) => (
              <div key={index} style={{ borderLeft: '3px solid #c62828', background: '#fdf3f3', padding: '12px 16px', borderRadius: 6 }}>
                <div style={{ ...VALUE_STYLE, color: '#c62828', fontWeight: 600 }}>
                  ⛔ {typeof inference === 'string' ? inference.replace(/_/g, ' ').toUpperCase() : JSON.stringify(inference)}
                </div>
              </div>
            ))}
          </div>
        </SectionCard>
      )}

      {/* Missing Documents */}
      {missingDocuments.length > 0 && (
        <SectionCard title={`Missing Documents (${missingDocuments.length})`} className="mb-6">
          <div style={{ display: 'grid', gap: 12 }}>
            {missingDocuments.map((doc: any, index: number) => (
              <div key={index} style={{ borderLeft: '3px solid var(--border-strong, #d4d0c8)', background: 'var(--bg-subtle, #f5f4f1)', padding: '12px 16px', borderRadius: 6 }}>
                <div style={VALUE_STYLE}>
                  📄 {typeof doc === 'string' ? doc : doc.document || doc.document_type || 'Document missing'}
                </div>
                {typeof doc === 'object' && doc.reason && (
                  <div style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--text-muted)', marginTop: 4 }}>REASON: {doc.reason}</div>
                )}
                {typeof doc === 'object' && doc.impact && (
                  <div style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--text-muted)', marginTop: 4 }}>IMPACT: {doc.impact}</div>
                )}
              </div>
            ))}
          </div>
        </SectionCard>
      )}

      {/* Latest Amendment Check */}
      {latestAmendment.checked && (
        <SectionCard title="Latest Amendment Check" className="mb-6">
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(240px, 1fr))', gap: '16px 24px' }}>
            <Field label="Latest Document Date">{formatValue(latestAmendment.latest_document_date)}</Field>
            <Field label="Latest Document Type">{formatValue(latestAmendment.latest_document_type)}</Field>
            <Field label="Amendment Found">{formatValue(latestAmendment.amendment_found)}</Field>
            <Field label="Stale Data Risk">{formatValue(latestAmendment.stale_data_risk)}</Field>
          </div>
        </SectionCard>
      )}

      {/* Human Notes */}
      <SectionCard title="Human Notes" className="mb-6">
        <textarea
          value={notesText}
          onChange={(e) => setNotesText(e.target.value)}
          rows={4}
          placeholder="Add your notes here..."
          style={{
            width: '100%',
            background: 'var(--bg-subtle, #f5f4f1)',
            border: '1px solid var(--border-subtle)',
            borderRadius: 8,
            padding: '10px 12px',
            fontFamily: 'var(--font-mono)',
            fontSize: 13,
            color: 'var(--text-primary)',
            resize: 'vertical',
          }}
        />
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginTop: 12 }}>
          <button onClick={handleSaveNotes} disabled={notesSaving} className="btn btn--primary btn--sm">
            {notesSaving ? 'Saving…' : 'Save Notes'}
          </button>
          {notesSaved && <span style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: '#2e7d32' }}>✓ Notes saved</span>}
          {notesError && <span style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: '#c62828' }}>⚠ {notesError}</span>}
        </div>
      </SectionCard>

      {/* Raw Evaluation JSON */}
      <SectionCard className="mb-6">
        <button
          onClick={() => setShowRawJson(!showRawJson)}
          style={{ width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'space-between', background: 'none', border: 'none', cursor: 'pointer', padding: 0 }}
        >
          <span style={{ ...LABEL_STYLE, marginBottom: 0, fontSize: 12 }}>Raw Evaluation JSON</span>
          <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>{showRawJson ? '▼' : '▶'}</span>
        </button>
        {showRawJson && (
          <pre style={{ marginTop: 16, padding: 16, background: 'var(--bg-subtle, #f5f4f1)', borderRadius: 8, overflowX: 'auto', fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--text-secondary)', border: '1px solid var(--border-subtle)' }}>
            {JSON.stringify(situation.evaluation, null, 2)}
          </pre>
        )}
      </SectionCard>

    </div>
  );
}
