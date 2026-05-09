'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { fetchSituation, archiveSituation, updateSituationStatus, saveNotes, runV2Preview, fetchResearchCases, createResearchCaseFromSituation, type Situation, type V2PreviewResult, type ResearchCase } from '@/lib/api';

function inferSource(s: Situation): string {
  if (s.filing_url?.includes('sec.gov')) return 'SEC EDGAR';
  if (s.filing_type) return 'SEC Filing';
  return 'Unknown';
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

  const getStatusBadge = (status: string | null | undefined) => {
    switch (status) {
      case 'evaluator_ready':
        return 'bg-green-500/20 text-green-400 border-green-400 glow-green';
      case 'partial':
        return 'bg-amber-500/20 text-amber-400 border-amber-400 glow-amber';
      case 'detection_only':
        return 'bg-violet-500/20 text-violet-400 border-violet-600';
      default:
        return 'bg-gray-700/50 text-gray-400 border-gray-600';
    }
  };

  const getVersionBadge = (version: string | undefined) => {
    if (version === 'v2') return 'bg-cyan-500/20 text-cyan-400 border-cyan-400 glow-cyan';
    return 'bg-gray-700/50 text-gray-400 border-gray-600';
  };

  const getWorkflowStatusBadge = (status: string) => {
    switch (status) {
      case 'detected': return 'bg-cyan-500/20 text-cyan-400 border-cyan-400 glow-cyan';
      case 'reviewing': return 'bg-blue-500/20 text-blue-400 border-blue-400';
      case 'watchlist': return 'bg-green-500/20 text-green-400 border-green-400 glow-green';
      case 'ignored': return 'bg-gray-700/50 text-gray-500 border-gray-600';
      case 'archived': return 'bg-violet-500/20 text-violet-400 border-violet-600';
      default: return 'bg-gray-700/50 text-gray-400 border-gray-600';
    }
  };

  const getRecommendationBadge = (rec: string | null | undefined) => {
    switch (rec) {
      case 'INVESTIGATE': return 'bg-cyan-500/20 text-cyan-400 border-cyan-400 glow-cyan';
      case 'MONITOR': return 'bg-amber-500/20 text-amber-400 border-amber-400 glow-amber';
      case 'PASS': return 'bg-gray-700/50 text-gray-500 border-gray-600';
      case 'STRONG_BUY':
      case 'BUY': return 'bg-green-500/20 text-green-400 border-green-400 glow-green';
      case 'AVOID':
      case 'SELL': return 'bg-red-500/20 text-red-400 border-red-400 glow-red';
      default: return 'bg-gray-700/50 text-gray-400 border-gray-600';
    }
  };

  if (loading) {
    return (
      <>
        <div className="scan-line"></div>
        <div className="min-h-screen p-8">
          <div className="max-w-5xl mx-auto">
            <div className="glass-panel rounded-lg p-8 text-center border-cyan-500/30">
              <div className="inline-block w-8 h-8 border-2 border-cyan-400 border-t-transparent rounded-full animate-spin mb-4"></div>
              <p className="text-gray-400 font-mono text-sm">LOADING EVALUATION DATA...</p>
            </div>
          </div>
        </div>
      </>
    );
  }

  if (error || !situation) {
    return (
      <>
        <div className="scan-line"></div>
        <div className="min-h-screen p-8">
          <div className="max-w-5xl mx-auto">
            <div className="glass-panel rounded-lg p-4 mb-6 border-red-500/50 glow-red">
              <p className="text-red-400 font-mono text-sm">⚠ ERROR: {error || 'EVALUATION NOT FOUND'}</p>
            </div>
            <Link href="/investment/evaluations" className="text-cyan-400 hover:text-cyan-300 text-sm font-mono">
              ← RETURN TO QUEUE
            </Link>
          </div>
        </div>
      </>
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
    <>
      <div className="scan-line"></div>
      <div className="min-h-screen p-8">
        <div className="max-w-5xl mx-auto">
          <div className="mb-6">
            <div className="flex items-center justify-between">
              <Link href="/investment/evaluations" className="text-cyan-400 hover:text-cyan-300 text-sm font-mono">
                ← RETURN TO QUEUE
              </Link>
              <div className="flex items-center gap-3">
                {actionMessage && (
                  <span className={`text-xs font-mono ${actionMessage.type === 'success' ? 'text-green-400' : 'text-red-400'}`}>
                    {actionMessage.type === 'success' ? '✓' : '⚠'} {actionMessage.text}
                  </span>
                )}
                <div className="flex gap-2">
                  {situation.status !== 'reviewing' && situation.status !== 'archived' && (
                    <button
                      onClick={() => handleStatusChange('reviewing')}
                      className="px-3 py-1 rounded text-sm font-mono bg-blue-500/20 text-blue-400 border border-blue-400 hover:bg-blue-500/30 transition-colors"
                    >
                      Mark Reviewing
                    </button>
                  )}
                  {situation.status !== 'watchlist' && situation.status !== 'archived' && (
                    <button
                      onClick={() => handleStatusChange('watchlist')}
                      className="px-3 py-1 rounded text-sm font-mono bg-green-500/20 text-green-400 border border-green-400 hover:bg-green-500/30 transition-colors"
                    >
                      Add to Watchlist
                    </button>
                  )}
                  {situation.status !== 'ignored' && situation.status !== 'archived' && (
                    <button
                      onClick={() => handleStatusChange('ignored')}
                      className="px-3 py-1 rounded text-sm font-mono bg-gray-700/50 text-gray-500 border border-gray-600 hover:bg-gray-600/50 transition-colors"
                    >
                      Ignore
                    </button>
                  )}
                  {situation.status !== 'archived' && (
                    <button
                      onClick={handleArchive}
                      className="px-3 py-1 rounded text-sm font-mono bg-violet-500/20 text-violet-400 border border-violet-600 hover:bg-violet-500/30 transition-colors"
                    >
                      Archive
                    </button>
                  )}
                </div>
              </div>
            </div>
          </div>

          <h1 className="text-3xl font-bold mb-2 text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-green-400">
            {situation.company_name}
          </h1>
          <p className="text-gray-500 text-xs font-mono mb-8">EVALUATION DETAIL // ID: {situation.id.substring(0, 8)}</p>

          {/* Decision Card */}
          <div className="glass-panel rounded-lg p-6 mb-6 border-cyan-500/50 glow-cyan">
            <h2 className="text-xs font-mono text-cyan-400 uppercase tracking-widest mb-4">Decision Summary</h2>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-x-6 gap-y-4">
              <div>
                <div className="text-xs font-mono text-gray-500 uppercase mb-1">Company</div>
                <div className="text-sm font-mono text-gray-200 font-bold">{situation.company_name}</div>
              </div>
              {situation.ticker && (
                <div>
                  <div className="text-xs font-mono text-gray-500 uppercase mb-1">Ticker</div>
                  <div className="text-sm font-mono text-gray-200">{situation.ticker}</div>
                </div>
              )}
              {situation.filing_type && (
                <div>
                  <div className="text-xs font-mono text-gray-500 uppercase mb-1">Filing Type</div>
                  <div className="text-sm font-mono text-gray-200">{situation.filing_type}</div>
                </div>
              )}
              <div>
                <div className="text-xs font-mono text-gray-500 uppercase mb-1">Workflow Status</div>
                <span className={`px-2 py-1 rounded text-xs font-mono font-bold border ${getWorkflowStatusBadge(situation.status ?? '')}`}>
                  {(situation.status ?? 'unknown').toUpperCase()}
                </span>
              </div>
              <div>
                <div className="text-xs font-mono text-gray-500 uppercase mb-1">Evaluator Version</div>
                <span className={`px-2 py-1 rounded text-xs font-mono font-bold border ${getVersionBadge(situation.evaluator_version)}`}>
                  {situation.evaluator_version ?? '-'}
                </span>
              </div>
              <div>
                <div className="text-xs font-mono text-gray-500 uppercase mb-1">Discovery Source</div>
                <div className="text-sm font-mono text-gray-200">{discoverySource}</div>
              </div>
              {situation.filing_type && (
                <div>
                  <div className="text-xs font-mono text-gray-500 uppercase mb-1">Source Detail</div>
                  <div className="text-sm font-mono text-gray-300">{situation.filing_type}</div>
                </div>
              )}
              {situation.selected_playbook && (
                <div>
                  <div className="text-xs font-mono text-gray-500 uppercase mb-1">Playbook</div>
                  <div className="text-sm font-mono text-gray-200">{situation.selected_playbook}</div>
                </div>
              )}
              {situation.playbook_status && (
                <div>
                  <div className="text-xs font-mono text-gray-500 uppercase mb-1">Playbook Status</div>
                  <span className={`px-2 py-1 rounded text-xs font-mono font-bold border ${getStatusBadge(situation.playbook_status)}`}>
                    {situation.playbook_status.replace(/_/g, ' ').toUpperCase()}
                  </span>
                </div>
              )}
              {situation.recommendation && (
                <div>
                  <div className="text-xs font-mono text-gray-500 uppercase mb-1">Recommendation</div>
                  <span className={`px-2 py-1 rounded text-xs font-mono font-bold border ${getRecommendationBadge(situation.recommendation)}`}>
                    {situation.recommendation}
                  </span>
                </div>
              )}
              {situation.evaluator_confidence && (
                <div>
                  <div className="text-xs font-mono text-gray-500 uppercase mb-1">Confidence</div>
                  <div className="text-sm font-mono text-gray-200">{situation.evaluator_confidence}</div>
                </div>
              )}
              {(situation.human_review_required_count ?? 0) > 0 && (
                <div>
                  <div className="text-xs font-mono text-gray-500 uppercase mb-1">Human Review Items</div>
                  <span className="px-2 py-1 rounded text-xs font-mono font-bold border bg-amber-500/20 text-amber-400 border-amber-400 glow-amber">
                    {situation.human_review_required_count}
                  </span>
                </div>
              )}
              {(situation.risk_flags_count ?? 0) > 0 && (
                <div>
                  <div className="text-xs font-mono text-gray-500 uppercase mb-1">Risk Flags</div>
                  <span className="px-2 py-1 rounded text-xs font-mono font-bold border bg-red-500/20 text-red-400 border-red-400 glow-red">
                    {situation.risk_flags_count}
                  </span>
                </div>
              )}
              {situation.filing_url && (
                <div className="col-span-2 md:col-span-3">
                  <div className="text-xs font-mono text-gray-500 uppercase mb-1">Filing URL</div>
                  <a
                    href={situation.filing_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-xs font-mono text-cyan-400 hover:text-cyan-300 break-all"
                  >
                    {situation.filing_url}
                  </a>
                </div>
              )}
            </div>
          </div>

          {/* Research Case */}
          <div className="glass-panel rounded-lg p-6 mb-6 border-cyan-500/30">
            <h2 className="text-xs font-mono text-cyan-400 uppercase tracking-widest mb-1">Research Case</h2>
            <p className="text-xs font-mono text-amber-400/70 mb-4">
              Este análisis es educativo. No es asesoramiento financiero.
            </p>
            {rcLoading && (
              <p className="text-xs font-mono text-gray-500">Loading research case…</p>
            )}
            {!rcLoading && rcError && (
              <div>
                <p className="text-xs font-mono text-red-400">{rcError}</p>
                <button
                  onClick={() => {
                    setRcError(null);
                    setRcLoading(true);
                    fetchResearchCases({ situation_id: id })
                      .then(d => setResearchCase(d.research_cases.length > 0 ? d.research_cases[0] : null))
                      .catch(() => setRcError('Could not load research case. Try again.'))
                      .finally(() => setRcLoading(false));
                  }}
                  className="mt-2 text-xs font-mono text-cyan-700 hover:text-cyan-400 transition-colors"
                >
                  Retry
                </button>
              </div>
            )}
            {!rcLoading && !rcError && researchCase && (
              <div className="flex items-center gap-3 flex-wrap">
                <span className={`px-2 py-0.5 rounded border text-xs font-mono ${
                  researchCase.status === 'detected' ? 'text-gray-400 border-gray-700' :
                  researchCase.status === 'brief_generated' ? 'text-cyan-400 border-cyan-800' :
                  researchCase.status === 'under_investigation' ? 'text-violet-400 border-violet-800' :
                  researchCase.status === 'documented' ? 'text-green-400 border-green-800' :
                  researchCase.status === 'archived' ? 'text-gray-600 border-gray-800' :
                  researchCase.status === 'published' ? 'text-emerald-400 border-emerald-800' :
                  'text-gray-400 border-gray-700'
                }`}>
                  {researchCase.status.replace(/_/g, ' ').toUpperCase()}
                </span>
                {researchCase.investment_readiness && (
                  <span className={`px-2 py-0.5 rounded border text-xs font-mono ${
                    researchCase.investment_readiness === 'monitor' ? 'text-amber-400 border-amber-800' :
                    researchCase.investment_readiness === 'not_actionable' ? 'text-gray-500 border-gray-700' :
                    researchCase.investment_readiness === 'needs_more_work' ? 'text-violet-400 border-violet-800' :
                    researchCase.investment_readiness === 'candidate' ? 'text-cyan-400 border-cyan-800' :
                    'text-gray-400 border-gray-700'
                  }`}>
                    {researchCase.investment_readiness.replace(/_/g, ' ')}
                  </span>
                )}
                <span className="text-xs font-mono text-gray-600">
                  UPDATED: {new Date(researchCase.updated_at).toLocaleString('en-CH')}
                </span>
                <Link
                  href={`/investment/research/${researchCase.id}`}
                  className="px-3 py-1 rounded border border-cyan-700 text-cyan-400 text-xs font-mono hover:bg-cyan-900/30 transition-colors"
                >
                  Open Research Case →
                </Link>
              </div>
            )}
            {!rcLoading && !rcError && !researchCase && (
              <div className="flex items-center gap-4 flex-wrap">
                <p className="text-xs font-mono text-gray-500">No research case yet.</p>
                {rcMessage ? (
                  <p className="text-xs font-mono text-gray-400">
                    {rcMessage.text}
                    <Link href="/investment/research" className="text-cyan-700 hover:text-cyan-400 underline">view research cases</Link>
                  </p>
                ) : (
                  <button
                    onClick={handleCreateResearchCase}
                    disabled={rcCreating}
                    className="px-4 py-1.5 rounded text-xs font-mono bg-cyan-500/20 text-cyan-400 border border-cyan-500 hover:bg-cyan-500/30 transition-colors disabled:opacity-50"
                  >
                    {rcCreating ? 'Creating…' : 'Create Research Case'}
                  </button>
                )}
              </div>
            )}
          </div>

          {/* v2 Preview */}
          <div className="glass-panel rounded-lg p-6 mb-6 border-violet-500/30">
            <div className="flex items-center justify-between mb-3">
              <div>
                <h2 className="text-xs font-mono text-violet-400 uppercase tracking-widest">Evaluator v2 Preview</h2>
                <span className="text-xs font-mono text-amber-400/70">PREVIEW ONLY — NOT SAVED TO DB</span>
              </div>
              {v2Result && (
                <button
                  onClick={() => setShowV2Result(!showV2Result)}
                  className="text-xs font-mono text-gray-400 hover:text-violet-400 transition-colors"
                >
                  {showV2Result ? '▼ Hide result' : '▶ Show result'}
                </button>
              )}
            </div>
            <p className="text-xs font-mono text-gray-500 mb-4">
              Manual preview only. Does not save to DB. Does not change v1/default evaluator. Requires explicit confirmation.
            </p>
            <div className="flex items-center gap-3">
              {v2CanRun ? (
                <button
                  onClick={handleRunV2Preview}
                  disabled={v2Running}
                  className="px-4 py-1.5 rounded text-sm font-mono bg-violet-500/20 text-violet-400 border border-violet-500 hover:bg-violet-500/30 transition-colors disabled:opacity-50"
                >
                  {v2Running ? 'Running v2...' : 'Run v2 preview (preview only)'}
                </button>
              ) : (
                <>
                  <button
                    disabled
                    className="px-4 py-1.5 rounded text-sm font-mono bg-gray-700/30 text-gray-600 border border-gray-700 cursor-not-allowed"
                  >
                    Run v2 preview (preview only)
                  </button>
                  <span className="text-xs font-mono text-gray-600">Missing required fields (company, filing_type, date, or url)</span>
                </>
              )}
            </div>
            {v2Error && (
              <div className="mt-4 p-3 rounded border border-red-500/40 bg-red-500/10">
                <p className="text-xs font-mono text-red-400">⚠ {v2Error}</p>
              </div>
            )}
            {v2Result && showV2Result && (
              <div className="mt-4">
                <div className="flex flex-wrap gap-4 mb-3 text-xs font-mono text-gray-400">
                  <span>Version: <span className="text-violet-400">{v2Result.evaluator_version}</span></span>
                  {v2Result.fallback_occurred && <span className="text-amber-400">⚠ Fallback to v1</span>}
                  {v2Result.usage?.model && <span>Model: {v2Result.usage.model}</span>}
                  {v2Result.usage?.input_tokens != null && (
                    <span>Tokens: {v2Result.usage.input_tokens}in / {v2Result.usage.output_tokens}out</span>
                  )}
                  <span className={v2Result.daily_limit.remaining === 0 ? 'text-red-400' : 'text-gray-400'}>
                    Daily: {v2Result.daily_limit.used}/{v2Result.daily_limit.limit} used ({v2Result.daily_limit.remaining} remaining)
                  </span>
                </div>
                <pre className="p-4 bg-black/50 rounded overflow-x-auto text-xs font-mono text-violet-300 border border-violet-500/20">
                  {JSON.stringify(v2Result.result, null, 2)}
                </pre>
              </div>
            )}
          </div>

          {/* Test Data Banner */}
          {isTestData(situation) && (
            <div className="glass-panel rounded-lg p-4 mb-6 border-amber-500/30 glow-amber">
              <p className="text-amber-400 font-mono text-sm">
                ⚠ TEST/DEMO EVALUATION — Not a real investment candidate
              </p>
            </div>
          )}

          {/* Filing Metadata */}
          <div className="glass-panel rounded-lg p-6 mb-6 border-cyan-500/30">
            <h2 className="text-sm font-mono text-cyan-400 mb-4 uppercase tracking-wider">Filing Information</h2>
            <dl className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <dt className="text-xs font-mono text-gray-500 uppercase">Company</dt>
                <dd className="mt-1 text-sm font-mono text-gray-300">{situation.company_name}</dd>
              </div>
              <div>
                <dt className="text-xs font-mono text-gray-500 uppercase">Ticker</dt>
                <dd className="mt-1 text-sm font-mono text-gray-300">{formatValue(situation.ticker)}</dd>
              </div>
              <div>
                <dt className="text-xs font-mono text-gray-500 uppercase">Filing Type</dt>
                <dd className="mt-1 text-sm font-mono text-gray-300">{formatValue(situation.filing_type)}</dd>
              </div>
              <div>
                <dt className="text-xs font-mono text-gray-500 uppercase">Detected At</dt>
                <dd className="mt-1 text-sm font-mono text-gray-300">
                  {situation.detected_at ? new Date(situation.detected_at).toLocaleString() : '-'}
                </dd>
              </div>
              {situation.filing_url && (
                <div className="md:col-span-2">
                  <dt className="text-xs font-mono text-gray-500 uppercase">Source URL</dt>
                  <dd className="mt-1 text-sm">
                    <a
                      href={situation.filing_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-cyan-400 hover:text-cyan-300 font-mono break-all"
                    >
                      {situation.filing_url}
                    </a>
                  </dd>
                </div>
              )}
            </dl>
          </div>

          {/* Evaluation Summary */}
          <div className="glass-panel rounded-lg p-6 mb-6 border-cyan-500/30">
            <h2 className="text-sm font-mono text-cyan-400 mb-4 uppercase tracking-wider">Evaluation Summary</h2>
            <dl className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <dt className="text-xs font-mono text-gray-500 uppercase">Evaluator Version</dt>
                <dd className="mt-1">
                  <span className={`px-2 py-1 rounded text-xs font-mono font-bold border ${getVersionBadge(situation.evaluator_version)}`}>
                    {formatValue(situation.evaluator_version)}
                  </span>
                </dd>
              </div>
              <div>
                <dt className="text-xs font-mono text-gray-500 uppercase">Playbook Status</dt>
                <dd className="mt-1">
                  <span className={`px-2 py-1 rounded text-xs font-mono font-bold border ${getStatusBadge(situation.playbook_status)}`}>
                    {formatValue(situation.playbook_status)}
                  </span>
                </dd>
              </div>
              <div>
                <dt className="text-xs font-mono text-gray-500 uppercase">Selected Playbook</dt>
                <dd className="mt-1 text-sm font-mono text-gray-300">{formatValue(situation.selected_playbook)}</dd>
              </div>
              <div>
                <dt className="text-xs font-mono text-gray-500 uppercase">Situation Type</dt>
                <dd className="mt-1 text-sm font-mono text-gray-300">{formatValue(situation.v2_situation_type)}</dd>
              </div>
              <div>
                <dt className="text-xs font-mono text-gray-500 uppercase">Subtype</dt>
                <dd className="mt-1 text-sm font-mono text-gray-300">{formatValue(situation.v2_subtype)}</dd>
              </div>
              <div>
                <dt className="text-xs font-mono text-gray-500 uppercase">Recommendation</dt>
                <dd className="mt-1 text-sm font-mono text-gray-300">{formatValue(situation.recommendation)}</dd>
              </div>
              <div>
                <dt className="text-xs font-mono text-gray-500 uppercase">Evaluator Confidence</dt>
                <dd className="mt-1 text-sm font-mono text-gray-300">{formatValue(situation.evaluator_confidence)}</dd>
              </div>
              {situation.fallback_occurred && (
                <div className="md:col-span-2">
                  <dt className="text-xs font-mono text-gray-500 uppercase">Fallback Occurred</dt>
                  <dd className="mt-1">
                    <span className="px-2 py-1 rounded text-xs font-mono font-bold bg-amber-500/20 text-amber-400 border border-amber-400 glow-amber">
                      YES - FELL BACK TO V1
                    </span>
                  </dd>
                </div>
              )}
            </dl>
          </div>

          {/* Human Review Required */}
          {humanReviewItems.length > 0 && (
            <div className="glass-panel rounded-lg p-6 mb-6 border-amber-500/30 glow-amber">
              <h2 className="text-sm font-mono text-amber-400 mb-4 uppercase tracking-wider">
                Human Review Required ({humanReviewItems.length})
              </h2>
              <div className="grid grid-cols-1 gap-3">
                {humanReviewItems.map((item: any, index: number) => (
                  <div key={index} className="glass-panel rounded border-l-4 border-amber-400 p-4 bg-amber-500/5">
                    <div className="text-sm font-mono text-amber-300 font-bold mb-2">
                      {item.item || 'Review item'}
                    </div>
                    {item.reason && (
                      <div className="text-xs font-mono text-gray-400 mb-1">
                        <span className="text-gray-500">REASON:</span> {item.reason}
                      </div>
                    )}
                    {item.required_human_input && (
                      <div className="text-xs font-mono text-gray-400 mb-1">
                        <span className="text-gray-500">REQUIRED:</span> {item.required_human_input}
                      </div>
                    )}
                    {item.related_playbook && (
                      <div className="text-xs font-mono text-gray-500 mt-2">
                        📋 {item.related_playbook}
                      </div>
                    )}
                    {item.blocking_for_recommendation && (
                      <div className="text-xs font-mono text-amber-400 mt-2">
                        ⚠ BLOCKING
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Risk Flags */}
          {riskFlags.length > 0 && (
            <div className="glass-panel rounded-lg p-6 mb-6 border-red-500/30">
              <h2 className="text-sm font-mono text-red-400 mb-4 uppercase tracking-wider">
                Risk Flags ({riskFlags.length})
              </h2>
              <div className="grid grid-cols-1 gap-3">
                {riskFlags.map((flag: any, index: number) => (
                  <div key={index} className="glass-panel rounded border-l-4 border-red-400 p-4 bg-red-500/5">
                    <div className="flex items-start">
                      <span className="text-red-400 mr-3 text-lg">⚠</span>
                      <div className="flex-1">
                        <div className="text-sm font-mono text-gray-300">
                          {typeof flag === 'string' ? flag : flag.flag || flag.risk_type || 'Risk detected'}
                        </div>
                        {typeof flag === 'object' && flag.description && (
                          <div className="text-xs font-mono text-gray-500 mt-1">{flag.description}</div>
                        )}
                        {typeof flag === 'object' && flag.severity && (
                          <div className="text-xs font-mono text-red-400 mt-2">SEVERITY: {flag.severity}</div>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Prohibited Inferences */}
          {prohibitedInferences.length > 0 && (
            <div className="glass-panel rounded-lg p-6 mb-6 border-red-500/50 glow-red">
              <h2 className="text-sm font-mono text-red-400 mb-4 uppercase tracking-wider">
                ⚠ PROHIBITED INFERENCES DETECTED ({prohibitedInferences.length})
              </h2>
              <div className="grid grid-cols-1 gap-3">
                {prohibitedInferences.map((inference: any, index: number) => (
                  <div key={index} className="glass-panel rounded border-l-4 border-red-500 p-4 bg-red-500/10 glow-red">
                    <div className="flex items-start">
                      <span className="text-red-400 mr-3 text-lg font-bold">⛔</span>
                      <div className="text-sm font-mono text-red-300 font-bold">
                        {typeof inference === 'string' ? inference.replace(/_/g, ' ').toUpperCase() : JSON.stringify(inference)}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Missing Documents */}
          {missingDocuments.length > 0 && (
            <div className="glass-panel rounded-lg p-6 mb-6 border-violet-500/30">
              <h2 className="text-sm font-mono text-violet-400 mb-4 uppercase tracking-wider">
                Missing Documents ({missingDocuments.length})
              </h2>
              <div className="grid grid-cols-1 gap-3">
                {missingDocuments.map((doc: any, index: number) => (
                  <div key={index} className="glass-panel rounded border-l-4 border-violet-400 p-4 bg-violet-500/5">
                    <div className="flex items-start">
                      <span className="text-violet-400 mr-3 text-lg">📄</span>
                      <div className="flex-1">
                        <div className="text-sm font-mono text-gray-300">
                          {typeof doc === 'string' ? doc : doc.document || doc.document_type || 'Document missing'}
                        </div>
                        {typeof doc === 'object' && doc.reason && (
                          <div className="text-xs font-mono text-gray-500 mt-1">REASON: {doc.reason}</div>
                        )}
                        {typeof doc === 'object' && doc.impact && (
                          <div className="text-xs font-mono text-violet-400 mt-1">IMPACT: {doc.impact}</div>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Latest Amendment Check */}
          {latestAmendment.checked && (
            <div className="glass-panel rounded-lg p-6 mb-6 border-cyan-500/30">
              <h2 className="text-sm font-mono text-cyan-400 mb-4 uppercase tracking-wider">Latest Amendment Check</h2>
              <dl className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <dt className="text-xs font-mono text-gray-500 uppercase">Latest Document Date</dt>
                  <dd className="mt-1 text-sm font-mono text-gray-300">{formatValue(latestAmendment.latest_document_date)}</dd>
                </div>
                <div>
                  <dt className="text-xs font-mono text-gray-500 uppercase">Latest Document Type</dt>
                  <dd className="mt-1 text-sm font-mono text-gray-300">{formatValue(latestAmendment.latest_document_type)}</dd>
                </div>
                <div>
                  <dt className="text-xs font-mono text-gray-500 uppercase">Amendment Found</dt>
                  <dd className="mt-1 text-sm font-mono text-gray-300">{formatValue(latestAmendment.amendment_found)}</dd>
                </div>
                <div>
                  <dt className="text-xs font-mono text-gray-500 uppercase">Stale Data Risk</dt>
                  <dd className="mt-1 text-sm font-mono text-gray-300">{formatValue(latestAmendment.stale_data_risk)}</dd>
                </div>
              </dl>
            </div>
          )}

          {/* Human Notes */}
          <div className="glass-panel rounded-lg p-6 mb-6 border-cyan-500/30">
            <h2 className="text-sm font-mono text-cyan-400 mb-4 uppercase tracking-wider">Human Notes</h2>
            <textarea
              value={notesText}
              onChange={(e) => setNotesText(e.target.value)}
              rows={4}
              placeholder="Add your notes here..."
              className="w-full bg-black/40 border border-cyan-500/30 rounded px-3 py-2 text-gray-300 text-sm font-mono focus:border-cyan-400 focus:outline-none resize-y"
            />
            <div className="flex items-center gap-3 mt-3">
              <button
                onClick={handleSaveNotes}
                disabled={notesSaving}
                className="px-4 py-1.5 rounded text-sm font-mono bg-cyan-500/20 text-cyan-400 border border-cyan-400 hover:bg-cyan-500/30 transition-colors disabled:opacity-50"
              >
                {notesSaving ? 'Saving...' : 'Save Notes'}
              </button>
              {notesSaved && (
                <span className="text-xs font-mono text-green-400">✓ Notes saved</span>
              )}
              {notesError && (
                <span className="text-xs font-mono text-red-400">⚠ {notesError}</span>
              )}
            </div>
          </div>

          {/* Raw Evaluation JSON */}
          <div className="glass-panel rounded-lg p-6 border-gray-700">
            <button
              onClick={() => setShowRawJson(!showRawJson)}
              className="w-full flex items-center justify-between text-left hover:text-cyan-400 transition-colors"
            >
              <h2 className="text-sm font-mono text-gray-400 uppercase tracking-wider">Raw Evaluation JSON</h2>
              <span className="text-cyan-400 font-mono">{showRawJson ? '▼' : '▶'}</span>
            </button>
            {showRawJson && (
              <pre className="mt-4 p-4 bg-black/50 rounded overflow-x-auto text-xs font-mono text-green-400 border border-green-500/20">
                {JSON.stringify(situation.evaluation, null, 2)}
              </pre>
            )}
          </div>
        </div>
      </div>
    </>
  );
}
