'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { CaseActivityTimeline } from '@/app/components/CaseActivityTimeline';
import { EvidenceLinksPanel } from '@/app/components/EvidenceLinksPanel';
import { IntelligenceScoreCard } from '@/app/components/IntelligenceScoreCard';
import { OfficialSourceFinderPanel } from '@/app/components/OfficialSourceFinderPanel';
import { HistoricalAnaloguesPanel } from '@/app/components/HistoricalAnaloguesPanel';
import { CaseCompletionWorkbench } from '@/app/components/CaseCompletionWorkbench';
import { SecDocumentAcquisitionPanel } from '@/app/components/SecDocumentAcquisitionPanel';
import { DocumentPackagePanel } from '@/app/components/DocumentPackagePanel';
import {
  acquireResearchCaseSecDocuments,
  fetchResearchCase,
  fetchResearchCaseActivityTimeline,
  fetchResearchCaseCompletionWorkbench,
  fetchResearchCaseEvidenceLinks,
  fetchResearchCaseDocumentationGuide,
  fetchResearchCaseDocumentPackage,
  fetchResearchCaseEvaluationPrep,
  fetchResearchCaseHistoricalAnalogues,
  fetchResearchCaseIntelligenceScore,
  fetchResearchCaseOfficialSourceFinder,
  fetchResearchCaseOperationalView,
  fetchResearchCaseSecDocumentAcquisitionPreview,
  updateResearchCase,
  addResearchTask,
  updateResearchTask,
  addResearchDocument,
  addResearchSource,
  updateResearchDocument,
  updateResearchSource,
  generateBriefPreview,
  generateQualityPreview,
  generateDocumentAnalysisPreview,
  generateSourceIntelligencePreview,
  saveSourceIntelligenceSuggestions,
  fetchSourceIntelligenceSuggestions,
  reviewSourceIntelligenceSuggestion,
  createPublicDraftFromResearchCase,
  fetchPublicDrafts,
  type ResearchCase,
  type CaseActivityTimelinePackage,
  type CaseCompletionPackage,
  type ResearchCaseEvidenceLinksPackage,
  type CaseDocumentationGuidePackage,
  type DocumentPackage,
  type EvaluationPrepPackage,
  type HistoricalAnaloguesPackage,
  type IntelligenceScorePackage,
  type OfficialSourceFinderPackage,
  type OperationalViewPackage,
  type SecDocumentAcquisitionPackage,
  type ResearchTask,
  type ResearchDocument,
  type ResearchSource,
  type BriefPreviewResult,
  type BriefPreviewSections,
  type QualityPreviewResult,
  type QualityChecklist,
  type DocumentAnalysisPreviewResult,
  type SourceIntelligencePreviewResult,
  type SourceScoreItem,
  type SourceIntelligenceSuggestion,
  type SourceIntelligenceSuggestionRecord,
  type PublicArticleDraft,
} from '@/lib/api';

const BRIEF_SECTIONS: { key: string; label: string }[] = [
  { key: 'executive_summary',         label: '1. Executive Summary' },
  { key: 'situation_type',            label: '2. Situation Type' },
  { key: 'why_interesting',           label: '3. Why It May Be Interesting' },
  { key: 'methodology_reference',     label: '4. Course Methodology Reference' },
  { key: 'company_context',           label: '5. Company Context' },
  { key: 'board_management',          label: '6. Board / Management' },
  { key: 'key_documents',             label: '7. Key Documents' },
  { key: 'timeline',                  label: '8. Timeline' },
  { key: 'risk_analysis',             label: '9. Risk Analysis' },
  { key: 'verify_before_investing',   label: '10. What To Verify Before Investing' },
  { key: 'missing_information',       label: '11. Missing Information / Manual Tasks for Dani' },
  { key: 'source_intelligence',       label: '12. Source Intelligence' },
  { key: 'investment_readiness_note', label: '13. Investment Readiness' },
  { key: 'public_summary_draft',      label: '14. Public Summary Draft' },
];

const STATUSES = ['detected', 'brief_generated', 'under_investigation', 'documented', 'archived', 'published'];
const READINESS = ['monitor', 'not_actionable', 'needs_more_work', 'candidate'];
const TASK_STATUSES = ['open', 'done', 'deferred', 'cancelled'];
const SIGNAL_QUALITY_VALUES = ['high', 'medium', 'low', 'no_signal'];

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

const SIGNAL_COLORS: Record<string, string> = {
  high:      'text-green-400',
  medium:    'text-amber-400',
  low:       'text-gray-400',
  no_signal: 'text-gray-600',
};

const TASK_STATUS_COLORS: Record<string, string> = {
  open:      'text-cyan-400',
  done:      'text-green-400',
  deferred:  'text-amber-400',
  cancelled: 'text-gray-600',
};

const WORKFLOW_STEPS: { key: string; label: string }[] = [
  { key: 'detected',            label: 'Detected' },
  { key: 'brief_generated',     label: 'Brief' },
  { key: 'under_investigation', label: 'Investigation' },
  { key: 'documented',          label: 'Documented' },
  { key: 'archived',            label: 'Archived' },
  { key: 'published',           label: 'Published' },
];

function Section({ title, hint, children, id }: { title: string; hint?: string; children: React.ReactNode; id?: string }) {
  return (
    <div id={id} className="glass-panel rounded-lg p-5 mb-4 scroll-mt-20">
      <div className="mb-4">
        <h2 className="text-xs font-mono font-bold text-gray-500 tracking-widest uppercase">{title}</h2>
        {hint && <p className="text-xs font-mono text-gray-700 mt-0.5">{hint}</p>}
      </div>
      {children}
    </div>
  );
}

function BriefEditor({
  brief,
  onSave,
}: {
  brief: Record<string, unknown> | null;
  onSave: (draft: Record<string, string>) => Promise<void>;
}) {
  const [expanded, setExpanded] = useState(false);
  const [draft, setDraft] = useState<Record<string, string>>(() => {
    const init: Record<string, string> = {};
    for (const s of BRIEF_SECTIONS) {
      const v = brief?.[s.key];
      init[s.key] = typeof v === 'string' ? v : '';
    }
    return init;
  });
  const [saving, setSaving] = useState(false);
  const [briefMsg, setBriefMsg] = useState<{ text: string; ok: boolean } | null>(null);

  async function handleSave() {
    setSaving(true);
    setBriefMsg(null);
    try {
      await onSave(draft);
      setBriefMsg({ text: 'Brief saved.', ok: true });
    } catch (err) {
      setBriefMsg({ text: err instanceof Error ? err.message : 'Failed to save brief', ok: false });
    } finally {
      setSaving(false);
      setTimeout(() => setBriefMsg(null), 3000);
    }
  }

  const filledCount = BRIEF_SECTIONS.filter(s => draft[s.key]?.trim()).length;

  return (
    <div>
      <div className="flex items-center justify-between mb-3">
        <span className="text-xs font-mono text-gray-600">
          {filledCount}/{BRIEF_SECTIONS.length} SECTIONS FILLED
        </span>
        <button
          onClick={() => setExpanded(e => !e)}
          className="text-xs font-mono text-cyan-700 hover:text-cyan-400 transition-colors"
        >
          {expanded ? '▲ COLLAPSE BRIEF' : '▼ EDIT BRIEF'}
        </button>
      </div>

      {expanded && (
        <div className="space-y-4">
          {BRIEF_SECTIONS.map(s => (
            <div key={s.key}>
              <label className="block text-xs font-mono text-gray-500 uppercase tracking-wide mb-1">
                {s.label}
              </label>
              <textarea
                value={draft[s.key]}
                onChange={e => setDraft(d => ({ ...d, [s.key]: e.target.value }))}
                rows={3}
                className="w-full bg-gray-900 border border-gray-700 rounded px-3 py-2 text-sm text-gray-200 font-mono resize-y"
                placeholder={`Enter ${s.label.replace(/^\d+\.\s*/, '')}…`}
              />
            </div>
          ))}

          <div className="flex items-center gap-3 pt-1">
            <button
              onClick={handleSave}
              disabled={saving}
              className="px-4 py-1.5 rounded bg-cyan-800 hover:bg-cyan-700 disabled:opacity-40 text-xs font-mono text-cyan-100 transition-colors"
            >
              {saving ? 'SAVING…' : 'SAVE BRIEF'}
            </button>
            {briefMsg && (
              <span className={`text-xs font-mono ${briefMsg.ok ? 'text-green-400' : 'text-red-400'}`}>
                {briefMsg.text}
              </span>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

function AiPreviewPanel({
  caseId,
  currentBrief,
  onApply,
}: {
  caseId: string;
  currentBrief: Record<string, unknown> | null;
  onApply: (sections: Partial<Record<string, string>>) => Promise<void>;
}) {
  const [generating, setGenerating] = useState(false);
  const [preview, setPreview] = useState<BriefPreviewResult | null>(null);
  const [genError, setGenError] = useState<string | null>(null);
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [applying, setApplying] = useState(false);
  const [applyMsg, setApplyMsg] = useState<{ text: string; ok: boolean } | null>(null);

  async function handleGenerate() {
    setGenerating(true);
    setGenError(null);
    setPreview(null);
    setSelected(new Set());
    try {
      const result = await generateBriefPreview(caseId);
      setPreview(result);
      const allKeys = BRIEF_SECTIONS.map(s => s.key).filter(k => result.preview[k as keyof BriefPreviewSections]?.trim());
      setSelected(new Set(allKeys));
    } catch (err) {
      setGenError(err instanceof Error ? err.message : 'Generation failed');
    } finally {
      setGenerating(false);
    }
  }

  function toggleSection(key: string) {
    setSelected(prev => {
      const next = new Set(prev);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      return next;
    });
  }

  function selectAll() {
    if (!preview) return;
    setSelected(new Set(BRIEF_SECTIONS.map(s => s.key).filter(k => preview.preview[k as keyof BriefPreviewSections]?.trim())));
  }

  function deselectAll() { setSelected(new Set()); }

  async function handleApply() {
    if (!preview || selected.size === 0) return;
    setApplying(true);
    setApplyMsg(null);
    try {
      const patch: Partial<Record<string, string>> = {};
      for (const key of selected) {
        const val = preview.preview[key as keyof BriefPreviewSections];
        if (val) patch[key] = val;
      }
      await onApply(patch);
      setApplyMsg({ text: `${selected.size} section(s) applied to brief.`, ok: true });
      setPreview(null);
      setSelected(new Set());
    } catch (err) {
      setApplyMsg({ text: err instanceof Error ? err.message : 'Apply failed', ok: false });
    } finally {
      setApplying(false);
      setTimeout(() => setApplyMsg(null), 4000);
    }
  }

  function handleDiscard() {
    setPreview(null);
    setSelected(new Set());
    setGenError(null);
  }

  return (
    <div className="mt-4 border-t border-gray-800 pt-4">
      <div className="flex items-center justify-between mb-3">
        <span className="text-xs font-mono text-gray-500 tracking-widest">AI BRIEF PREVIEW</span>
        {!preview && (
          <button
            onClick={handleGenerate}
            disabled={generating}
            className="px-3 py-1.5 rounded bg-violet-900 hover:bg-violet-800 disabled:opacity-40 text-xs font-mono text-violet-100 transition-colors border border-violet-700"
          >
            {generating ? 'GENERATING…' : '⚡ GENERATE AI BRIEF'}
          </button>
        )}
      </div>

      {genError && (
        <p className="text-xs font-mono text-red-400 mb-3">{genError}</p>
      )}

      {generating && (
        <p className="text-xs font-mono text-gray-600 italic">Assembling context and calling AI… this may take 15–30 seconds.</p>
      )}

      {preview && (
        <div className="space-y-3">
          {/* Status banner */}
          <div className="bg-amber-950/40 border border-amber-700/40 rounded px-3 py-2">
            <p className="text-xs font-mono text-amber-400 font-bold">PREVIEW ONLY — NOT SAVED</p>
            <p className="text-xs font-mono text-amber-700 mt-0.5">
              Context used: {preview.source_context_used.join(', ') || 'none'} ·
              Model: {preview.usage.model ?? '—'} ·
              Tokens: {(preview.usage.input_tokens ?? 0) + (preview.usage.output_tokens ?? 0)}
            </p>
            <p className="text-xs font-mono text-gray-700 mt-1">
              Attached document/source URLs are used as metadata only. SwissEdge does not fetch or read linked URLs in this preview.
            </p>
          </div>

          {/* Warnings */}
          {preview.warnings.length > 0 && (
            <div className="bg-orange-950/30 border border-orange-700/30 rounded px-3 py-2">
              <p className="text-xs font-mono text-orange-400 font-bold mb-1">WARNINGS</p>
              {preview.warnings.map((w, i) => (
                <p key={i} className="text-xs font-mono text-orange-600">• {w}</p>
              ))}
            </div>
          )}

          {/* Disclaimer */}
          <p className="text-xs font-mono text-amber-400/60 text-center">{preview.disclaimer}</p>

          {/* Section-by-section comparison */}
          <div className="flex items-center justify-between mb-1">
            <span className="text-xs font-mono text-gray-600">{selected.size} of {BRIEF_SECTIONS.length} sections selected</span>
            <div className="flex gap-2">
              <button onClick={selectAll} className="text-xs font-mono text-cyan-700 hover:text-cyan-400">SELECT ALL</button>
              <span className="text-xs font-mono text-gray-700">·</span>
              <button onClick={deselectAll} className="text-xs font-mono text-gray-600 hover:text-gray-400">NONE</button>
            </div>
          </div>

          <div className="space-y-3 max-h-[60vh] overflow-y-auto pr-1">
            {BRIEF_SECTIONS.map(s => {
              const aiVal = preview.preview[s.key as keyof BriefPreviewSections] ?? '';
              const currentVal = typeof currentBrief?.[s.key] === 'string' ? (currentBrief[s.key] as string) : '';
              const hasAi = aiVal.trim().length > 0;
              const isSelected = selected.has(s.key);
              return (
                <div
                  key={s.key}
                  className={`rounded border p-3 transition-colors ${isSelected && hasAi ? 'border-violet-700/60 bg-violet-950/20' : 'border-gray-800'}`}
                >
                  <div className="flex items-start gap-2 mb-2">
                    <input
                      type="checkbox"
                      checked={isSelected && hasAi}
                      disabled={!hasAi}
                      onChange={() => hasAi && toggleSection(s.key)}
                      className="mt-0.5 accent-violet-500 cursor-pointer disabled:cursor-not-allowed"
                    />
                    <label className="text-xs font-mono text-gray-400 uppercase tracking-wide cursor-pointer select-none flex-1"
                      onClick={() => hasAi && toggleSection(s.key)}>
                      {s.label}
                    </label>
                    {!hasAi && <span className="text-xs font-mono text-gray-700">EMPTY</span>}
                  </div>
                  {hasAi && (
                    <div className="ml-5 space-y-2">
                      <div className="rounded bg-violet-950/30 px-2 py-1.5">
                        <p className="text-xs font-mono text-violet-500 mb-0.5">AI PREVIEW</p>
                        <p className="text-xs text-gray-300 whitespace-pre-wrap">{aiVal}</p>
                      </div>
                      {currentVal && (
                        <div className="rounded bg-gray-900/60 px-2 py-1.5">
                          <p className="text-xs font-mono text-gray-600 mb-0.5">CURRENT</p>
                          <p className="text-xs text-gray-500 whitespace-pre-wrap">{currentVal}</p>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>

          {/* Apply / Discard controls */}
          <div className="flex items-center gap-3 pt-2 border-t border-gray-800">
            <button
              onClick={handleApply}
              disabled={applying || selected.size === 0}
              className="px-4 py-1.5 rounded bg-violet-800 hover:bg-violet-700 disabled:opacity-40 text-xs font-mono text-violet-100 transition-colors"
            >
              {applying ? 'APPLYING…' : `APPLY ${selected.size} SECTION(S)`}
            </button>
            <button
              onClick={handleDiscard}
              disabled={applying}
              className="px-3 py-1.5 rounded border border-gray-700 hover:border-gray-500 text-xs font-mono text-gray-500 transition-colors"
            >
              DISCARD
            </button>
            {applyMsg && (
              <span className={`text-xs font-mono ${applyMsg.ok ? 'text-green-400' : 'text-red-400'}`}>
                {applyMsg.text}
              </span>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

function QualityAssistPanel({
  caseId,
  onApplyStatus,
  onApplyReadiness,
}: {
  caseId: string;
  onApplyStatus: (status: string) => Promise<void>;
  onApplyReadiness: (readiness: string) => Promise<void>;
}) {
  const [running, setRunning] = useState(false);
  const [result, setResult] = useState<QualityPreviewResult | null>(null);
  const [runError, setRunError] = useState<string | null>(null);
  const [applying, setApplying] = useState(false);
  const [applyMsg, setApplyMsg] = useState<{ text: string; ok: boolean } | null>(null);

  async function handleRun() {
    setRunning(true);
    setRunError(null);
    setResult(null);
    try {
      const data = await generateQualityPreview(caseId);
      setResult(data);
    } catch (err) {
      setRunError(err instanceof Error ? err.message : 'Quality check failed');
    } finally {
      setRunning(false);
    }
  }

  function handleDiscard() {
    setResult(null);
    setRunError(null);
  }

  async function apply(fn: () => Promise<void>, label: string) {
    setApplying(true);
    setApplyMsg(null);
    try {
      await fn();
      setApplyMsg({ text: label, ok: true });
    } catch (err) {
      setApplyMsg({ text: err instanceof Error ? err.message : 'Apply failed', ok: false });
    } finally {
      setApplying(false);
      setTimeout(() => setApplyMsg(null), 4000);
    }
  }

  const CHECKLIST_LABELS: Record<keyof QualityChecklist, string> = {
    brief_completeness:       'Brief completeness',
    missing_information_noted:'Missing information noted',
    key_risks_identified:     'Key risks identified',
    documents_attached:       'Documents attached',
    tasks_open:               'Open tasks exist',
    sources_recorded:         'Sources recorded',
    disclaimer_present:       'Disclaimer present',
    no_buy_sell_language:     'No buy/sell language',
    readiness_label_valid:    'Readiness label valid',
  };

  return (
    <div className="mt-4 border-t border-gray-800 pt-4">
      <div className="flex items-center justify-between mb-3">
        <span className="text-xs font-mono text-gray-500 tracking-widest">RESEARCH QUALITY ASSIST</span>
        {!result && (
          <button
            onClick={handleRun}
            disabled={running}
            className="px-3 py-1.5 rounded bg-teal-900 hover:bg-teal-800 disabled:opacity-40 text-xs font-mono text-teal-100 transition-colors border border-teal-700"
          >
            {running ? 'CHECKING…' : '✓ RUN QUALITY CHECK'}
          </button>
        )}
      </div>

      {runError && <p className="text-xs font-mono text-red-400 mb-3">{runError}</p>}
      {running && (
        <p className="text-xs font-mono text-gray-600 italic">Reviewing case data… this may take 10–20 seconds.</p>
      )}

      {result && (
        <div className="space-y-3">
          <div className="bg-teal-950/40 border border-teal-700/40 rounded px-3 py-2">
            <p className="text-xs font-mono text-teal-400 font-bold">ASSISTIVE PREVIEW — NOT SAVED</p>
            <p className="text-xs font-mono text-gray-700 mt-1">
              Attached document/source URLs are used as metadata only. SwissEdge does not fetch or read linked URLs in this preview.
            </p>
          </div>

          {result.warnings.length > 0 && (
            <div className="bg-orange-950/30 border border-orange-700/30 rounded px-3 py-2">
              <p className="text-xs font-mono text-orange-400 font-bold mb-1">WARNINGS</p>
              {result.warnings.map((w, i) => (
                <p key={i} className="text-xs font-mono text-orange-600">• {w}</p>
              ))}
            </div>
          )}

          {/* Quality checklist */}
          <div className="rounded border border-gray-800 p-3">
            <p className="text-xs font-mono text-gray-500 uppercase tracking-widest mb-2">Quality Checklist</p>
            <div className="grid grid-cols-1 gap-1">
              {(Object.keys(CHECKLIST_LABELS) as (keyof QualityChecklist)[]).map(key => {
                const val = result.quality_checklist[key];
                return (
                  <div key={key} className="flex items-center gap-2">
                    <span className={`text-xs font-mono w-3 ${val ? 'text-green-400' : 'text-gray-700'}`}>
                      {val ? '✓' : '✗'}
                    </span>
                    <span className={`text-xs font-mono ${val ? 'text-gray-300' : 'text-gray-600'}`}>
                      {CHECKLIST_LABELS[key]}
                    </span>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Suggestions */}
          <div className="rounded border border-gray-800 p-3 space-y-2">
            <p className="text-xs font-mono text-gray-500 uppercase tracking-widest mb-1">Suggestions</p>
            <div className="flex flex-wrap gap-x-6 gap-y-1">
              <span className="text-xs font-mono text-gray-500">
                STATUS: <span className="text-teal-400">{result.suggested_status}</span>
              </span>
              <span className="text-xs font-mono text-gray-500">
                READINESS: <span className="text-teal-400">{result.suggested_readiness}</span>
              </span>
            </div>
            {result.rationale && (
              <p className="text-xs text-gray-400 whitespace-pre-wrap mt-1">{result.rationale}</p>
            )}
          </div>

          <p className="text-xs font-mono text-amber-400/60 text-center">{result.disclaimer}</p>

          {/* Apply / Discard controls */}
          <div className="flex flex-wrap items-center gap-2 pt-2 border-t border-gray-800">
            <button
              onClick={() => apply(() => onApplyStatus(result.suggested_status), `Status set to "${result.suggested_status}"`)}
              disabled={applying}
              className="px-3 py-1.5 rounded bg-teal-900 hover:bg-teal-800 disabled:opacity-40 text-xs font-mono text-teal-100 transition-colors"
            >
              APPLY SUGGESTED STATUS
            </button>
            <button
              onClick={() => apply(() => onApplyReadiness(result.suggested_readiness), `Readiness set to "${result.suggested_readiness}"`)}
              disabled={applying}
              className="px-3 py-1.5 rounded bg-teal-900 hover:bg-teal-800 disabled:opacity-40 text-xs font-mono text-teal-100 transition-colors"
            >
              APPLY SUGGESTED READINESS
            </button>
            <button
              onClick={() => apply(async () => {
                await onApplyStatus(result.suggested_status);
                await onApplyReadiness(result.suggested_readiness);
              }, `Status + readiness applied`)}
              disabled={applying}
              className="px-3 py-1.5 rounded bg-teal-800 hover:bg-teal-700 disabled:opacity-40 text-xs font-mono text-teal-100 transition-colors border border-teal-700"
            >
              APPLY BOTH
            </button>
            <button
              onClick={handleDiscard}
              disabled={applying}
              className="px-3 py-1.5 rounded border border-gray-700 hover:border-gray-500 text-xs font-mono text-gray-500 transition-colors"
            >
              DISCARD
            </button>
            {applyMsg && (
              <span className={`text-xs font-mono ${applyMsg.ok ? 'text-green-400' : 'text-red-400'}`}>
                {applyMsg.text}
              </span>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

const DOC_TYPES = ['sec_filing', 'press_release', 'ir_page', 'presentation', 'news', 'other'];

function DocumentCard({
  doc,
  caseId,
  onUpdated,
  onActionMsg,
}: {
  doc: ResearchDocument;
  caseId: string;
  onUpdated: () => void;
  onActionMsg: (text: string, ok: boolean) => void;
}) {
  const [editingMeta, setEditingMeta] = useState(false);
  const [docType, setDocType] = useState(doc.doc_type ?? '');
  const [title, setTitle] = useState(doc.title ?? '');
  const [savingMeta, setSavingMeta] = useState(false);

  const [snippetOpen, setSnippetOpen] = useState(false);
  const [snippetText, setSnippetText] = useState(doc.summary ?? '');
  const [savingSnippet, setSavingSnippet] = useState(false);

  const [analysis, setAnalysis] = useState<DocumentAnalysisPreviewResult | null>(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [analysisError, setAnalysisError] = useState<string | null>(null);
  const [analysisOpen, setAnalysisOpen] = useState(false);

  async function saveMeta() {
    setSavingMeta(true);
    try {
      await updateResearchDocument(caseId, doc.id, { doc_type: docType || undefined, title: title || undefined });
      setEditingMeta(false);
      onUpdated();
      onActionMsg('Document updated.', true);
    } catch (err) {
      onActionMsg(err instanceof Error ? err.message : 'Failed to update document', false);
    } finally {
      setSavingMeta(false);
    }
  }

  async function saveSnippet() {
    setSavingSnippet(true);
    try {
      await updateResearchDocument(caseId, doc.id, { summary: snippetText });
      setSnippetOpen(false);
      onUpdated();
      onActionMsg('Snippet saved.', true);
    } catch (err) {
      onActionMsg(err instanceof Error ? err.message : 'Failed to save snippet', false);
    } finally {
      setSavingSnippet(false);
    }
  }

  async function runAnalysis() {
    setAnalyzing(true);
    setAnalysisError(null);
    setAnalysis(null);
    try {
      const result = await generateDocumentAnalysisPreview(doc.id);
      setAnalysis(result);
      setAnalysisOpen(true);
    } catch (err) {
      setAnalysisError(err instanceof Error ? err.message : 'Analysis failed');
    } finally {
      setAnalyzing(false);
    }
  }

  return (
    <div className="border border-gray-800 rounded-lg p-3 space-y-2">
      <div className="flex items-start gap-3">
        {editingMeta ? (
          <div className="flex-1 space-y-2">
            <input
              value={title}
              onChange={e => setTitle(e.target.value)}
              placeholder="Title…"
              className="w-full bg-gray-900 border border-gray-700 rounded px-2 py-1 text-sm text-gray-200 font-mono"
            />
            <div className="flex items-center gap-2">
              <select
                value={docType}
                onChange={e => setDocType(e.target.value)}
                className="bg-gray-900 border border-gray-700 rounded px-2 py-1 text-xs font-mono text-gray-300"
              >
                <option value="">— type —</option>
                {DOC_TYPES.map(t => <option key={t} value={t}>{t}</option>)}
              </select>
              <button
                onClick={saveMeta}
                disabled={savingMeta}
                className="px-2 py-1 rounded bg-cyan-800 text-xs font-mono text-cyan-100 disabled:opacity-40"
              >
                {savingMeta ? '…' : 'SAVE'}
              </button>
              <button
                onClick={() => { setEditingMeta(false); setDocType(doc.doc_type ?? ''); setTitle(doc.title ?? ''); }}
                className="px-2 py-1 rounded border border-gray-700 text-xs font-mono text-gray-500"
              >
                CANCEL
              </button>
            </div>
          </div>
        ) : (
          <>
            <span className="text-xs font-mono text-gray-600 flex-shrink-0 mt-0.5 w-20">
              {(doc.doc_type ?? 'other').toUpperCase()}
            </span>
            <div className="flex-1 min-w-0">
              <a
                href={doc.url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-sm text-cyan-700 hover:text-cyan-400 transition-colors truncate block"
              >
                {doc.title ?? doc.url}
              </a>
              <p className="text-xs font-mono text-gray-700 mt-0.5">
                METADATA ONLY — URL not fetched
                {doc.created_at && ` · ${new Date(doc.created_at).toLocaleDateString('en-CH')}`}
              </p>
            </div>
            <button
              onClick={() => setEditingMeta(true)}
              className="text-xs font-mono text-gray-700 hover:text-cyan-400 flex-shrink-0"
            >
              ✎
            </button>
          </>
        )}
      </div>

      {/* 3B Snippet */}
      <div className="border-t border-gray-800 pt-2">
        <button
          onClick={() => setSnippetOpen(o => !o)}
          className="text-xs font-mono text-gray-600 hover:text-cyan-400 transition-colors"
        >
          {snippetOpen ? '▲ HIDE SNIPPET' : `▼ ${doc.summary ? 'EDIT SNIPPET' : 'ADD SNIPPET'}`}
        </button>
        {snippetOpen && (
          <div className="mt-2 space-y-2">
            <p className="text-xs font-mono text-amber-700">
              IMPORTANT: paste only text you are authorised to reproduce. Respect copyright.
              This snippet is stored in your private research workspace only.
            </p>
            <textarea
              value={snippetText}
              onChange={e => setSnippetText(e.target.value)}
              rows={5}
              className="w-full bg-gray-900 border border-gray-700 rounded px-3 py-2 text-sm text-gray-200 font-mono resize-y"
              placeholder="Paste a relevant text excerpt from this document…"
            />
            <div className="flex gap-2">
              <button
                onClick={saveSnippet}
                disabled={savingSnippet}
                className="px-3 py-1 rounded bg-cyan-800 hover:bg-cyan-700 disabled:opacity-40 text-xs font-mono text-cyan-100 transition-colors"
              >
                {savingSnippet ? 'SAVING…' : 'SAVE SNIPPET'}
              </button>
              <button
                onClick={() => { setSnippetOpen(false); setSnippetText(doc.summary ?? ''); }}
                className="px-3 py-1 rounded border border-gray-700 text-xs font-mono text-gray-500"
              >
                CANCEL
              </button>
            </div>
          </div>
        )}
        {!snippetOpen && doc.summary && (
          <p className="text-xs text-gray-600 mt-1 line-clamp-2 italic">{doc.summary}</p>
        )}
      </div>

      {/* 3C Analysis */}
      <div className="border-t border-gray-800 pt-2">
        <div className="flex items-center gap-3">
          <button
            onClick={runAnalysis}
            disabled={analyzing}
            className="px-3 py-1 rounded bg-violet-900/60 hover:bg-violet-800/60 disabled:opacity-40 text-xs font-mono text-violet-300 border border-violet-800/50 transition-colors"
          >
            {analyzing ? 'ANALYSING…' : 'ANALYSE SNIPPET'}
          </button>
          {analysis && (
            <button
              onClick={() => setAnalysisOpen(o => !o)}
              className="text-xs font-mono text-violet-600 hover:text-violet-400 transition-colors"
            >
              {analysisOpen ? '▲ HIDE ANALYSIS' : '▼ SHOW ANALYSIS'}
            </button>
          )}
          {analysisError && <span className="text-xs font-mono text-red-400">{analysisError}</span>}
        </div>

        {analysis && analysisOpen && (
          <div className="mt-3 space-y-3 border border-violet-900/40 rounded p-3 bg-violet-950/10">
            {analysis.warnings.length > 0 && (
              <div className="space-y-1">
                {analysis.warnings.map((w, i) => (
                  <p key={i} className="text-xs font-mono text-amber-500">⚠ {w}</p>
                ))}
              </div>
            )}
            {analysis.analysis.summary && (
              <div>
                <p className="text-xs font-mono text-gray-500 uppercase tracking-wide mb-1">Summary</p>
                <p className="text-sm text-gray-300">{analysis.analysis.summary}</p>
              </div>
            )}
            {analysis.analysis.key_points.length > 0 && (
              <div>
                <p className="text-xs font-mono text-gray-500 uppercase tracking-wide mb-1">Key Points</p>
                <ul className="space-y-0.5">
                  {analysis.analysis.key_points.map((p, i) => (
                    <li key={i} className="text-sm text-gray-300 flex gap-2"><span className="text-gray-700">·</span>{p}</li>
                  ))}
                </ul>
              </div>
            )}
            {analysis.analysis.risks.length > 0 && (
              <div>
                <p className="text-xs font-mono text-gray-500 uppercase tracking-wide mb-1">Risks</p>
                <ul className="space-y-0.5">
                  {analysis.analysis.risks.map((r, i) => (
                    <li key={i} className="text-sm text-amber-400/80 flex gap-2"><span className="text-gray-700">·</span>{r}</li>
                  ))}
                </ul>
              </div>
            )}
            {analysis.analysis.timeline_items.length > 0 && (
              <div>
                <p className="text-xs font-mono text-gray-500 uppercase tracking-wide mb-1">Timeline</p>
                <ul className="space-y-0.5">
                  {analysis.analysis.timeline_items.map((t, i) => (
                    <li key={i} className="text-sm text-gray-400 flex gap-2"><span className="text-gray-700">·</span>{t}</li>
                  ))}
                </ul>
              </div>
            )}
            {analysis.analysis.suggested_research_tasks.length > 0 && (
              <div>
                <p className="text-xs font-mono text-gray-500 uppercase tracking-wide mb-1">Suggested Tasks</p>
                <ul className="space-y-0.5">
                  {analysis.analysis.suggested_research_tasks.map((t, i) => (
                    <li key={i} className="text-sm text-cyan-400/70 flex gap-2"><span className="text-gray-700">·</span>{t}</li>
                  ))}
                </ul>
              </div>
            )}
            {analysis.analysis.source_usefulness && (
              <div>
                <p className="text-xs font-mono text-gray-500 uppercase tracking-wide mb-1">Source Usefulness</p>
                <p className="text-sm text-gray-400">{analysis.analysis.source_usefulness}</p>
              </div>
            )}
            <p className="text-xs font-mono text-amber-600/60 border-t border-gray-800 pt-2">{analysis.disclaimer}</p>
            <p className="text-xs font-mono text-gray-700">NOT SAVED — apply changes manually via task/notes/brief editors above.</p>
          </div>
        )}
      </div>
    </div>
  );
}

function SourceCard({
  source,
  caseId,
  onUpdated,
  onActionMsg,
}: {
  source: ResearchSource;
  caseId: string;
  onUpdated: () => void;
  onActionMsg: (text: string, ok: boolean) => void;
}) {
  const [editing, setEditing] = useState(false);
  const [quality, setQuality] = useState(source.signal_quality);
  const [notes, setNotes] = useState(source.notes ?? '');
  const [saving, setSaving] = useState(false);

  async function save() {
    setSaving(true);
    try {
      await updateResearchSource(caseId, source.id, { signal_quality: quality, notes: notes || undefined });
      setEditing(false);
      onUpdated();
      onActionMsg('Source updated.', true);
    } catch (err) {
      onActionMsg(err instanceof Error ? err.message : 'Failed to update source', false);
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="border border-gray-800 rounded p-3">
      <div className="flex items-start gap-3">
        <span className={`text-xs font-mono flex-shrink-0 mt-0.5 w-20 ${SIGNAL_COLORS[source.signal_quality] ?? 'text-gray-400'}`}>
          {source.signal_quality.toUpperCase()}
        </span>
        <div className="flex-1 min-w-0">
          <p className="text-sm text-gray-300">{source.source_name}</p>
          {source.source_url && (
            <p className="text-xs font-mono text-gray-700 mt-0.5 truncate">
              {source.source_url} <span className="text-gray-800">(metadata only)</span>
            </p>
          )}
          {!editing && source.notes && (
            <p className="text-xs text-gray-500 mt-0.5">{source.notes}</p>
          )}
          {!editing && (
            <p className="text-xs font-mono text-gray-700 mt-0.5">
              {source.created_at ? new Date(source.created_at).toLocaleDateString('en-CH') : ''}
            </p>
          )}
        </div>
        {!editing && (
          <button
            onClick={() => setEditing(true)}
            className="text-xs font-mono text-gray-700 hover:text-cyan-400 flex-shrink-0"
          >
            ✎
          </button>
        )}
      </div>
      {editing && (
        <div className="mt-2 space-y-2 border-t border-gray-800 pt-2">
          <div className="flex items-center gap-2">
            <label className="text-xs font-mono text-gray-500">SIGNAL QUALITY:</label>
            <select
              value={quality}
              onChange={e => setQuality(e.target.value)}
              className="bg-gray-900 border border-gray-700 rounded px-2 py-1 text-xs font-mono text-gray-300"
            >
              {SIGNAL_QUALITY_VALUES.map(q => <option key={q} value={q}>{q}</option>)}
            </select>
          </div>
          <label className="block text-xs font-mono text-gray-500 mt-1">WHY THIS SOURCE WAS USEFUL</label>
          <textarea
            value={notes}
            onChange={e => setNotes(e.target.value)}
            rows={2}
            className="w-full bg-gray-900 border border-gray-700 rounded px-2 py-1 text-sm text-gray-200 font-mono resize-y"
            placeholder="Sector, jurisdiction, source type, how it surfaced this case…"
          />
          <div className="flex gap-2">
            <button
              onClick={save}
              disabled={saving}
              className="px-2 py-1 rounded bg-cyan-800 text-xs font-mono text-cyan-100 disabled:opacity-40"
            >
              {saving ? '…' : 'SAVE'}
            </button>
            <button
              onClick={() => { setEditing(false); setQuality(source.signal_quality); setNotes(source.notes ?? ''); }}
              className="px-2 py-1 rounded border border-gray-700 text-xs font-mono text-gray-500"
            >
              CANCEL
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

const CONFIDENCE_COLORS: Record<string, string> = {
  high:   'text-green-400',
  medium: 'text-amber-400',
  low:    'text-gray-500',
};

const ACTION_LABELS: Record<string, string> = {
  add:             'ADD SOURCE',
  update_priority: 'UPDATE PRIORITY',
  deactivate:      'DEACTIVATE',
};

function SourceIntelligencePanel({ caseId }: { caseId: string }) {
  const [running, setRunning] = useState(false);
  const [result, setResult] = useState<SourceIntelligencePreviewResult | null>(null);
  const [runError, setRunError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [saveMsg, setSaveMsg] = useState<string | null>(null);
  const [savedProposals, setSavedProposals] = useState<SourceIntelligenceSuggestionRecord[]>([]);
  const [loadingProposals, setLoadingProposals] = useState(false);
  const [reviewMsg, setReviewMsg] = useState<string | null>(null);

  async function loadProposals() {
    setLoadingProposals(true);
    try {
      const data = await fetchSourceIntelligenceSuggestions({ research_case_id: caseId });
      setSavedProposals(data.suggestions);
    } catch {
      // non-fatal
    } finally {
      setLoadingProposals(false);
    }
  }

  async function handleRun() {
    setRunning(true);
    setRunError(null);
    setResult(null);
    try {
      const data = await generateSourceIntelligencePreview(caseId);
      setResult(data);
    } catch (err) {
      setRunError(err instanceof Error ? err.message : 'Source intelligence preview failed');
    } finally {
      setRunning(false);
    }
  }

  function handleDiscard() {
    setResult(null);
    setRunError(null);
    setSaveMsg(null);
  }

  async function handleSaveProposals() {
    if (!result || result.suggestions.length === 0) return;
    setSaving(true);
    setSaveMsg(null);
    try {
      const rows = await saveSourceIntelligenceSuggestions(caseId, result.suggestions);
      setSaveMsg(`${rows.length} proposal(s) saved to queue.`);
      await loadProposals();
    } catch (err) {
      setSaveMsg(err instanceof Error ? err.message : 'Failed to save proposals');
    } finally {
      setSaving(false);
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

  useEffect(() => { loadProposals(); }, [caseId]);

  const STATUS_STYLE: Record<string, string> = {
    proposed: 'text-amber-500',
    approved: 'text-green-500',
    rejected: 'text-gray-600 line-through',
  };

  return (
    <div className="mt-4 border-t border-gray-800 pt-4">
      <div className="flex items-center justify-between mb-3">
        <span className="text-xs font-mono text-gray-500 tracking-widest">SOURCE INTELLIGENCE PREVIEW</span>
        {!result && (
          <button
            onClick={handleRun}
            disabled={running}
            className="px-3 py-1.5 rounded bg-indigo-900 hover:bg-indigo-800 disabled:opacity-40 text-xs font-mono text-indigo-100 transition-colors border border-indigo-700"
          >
            {running ? 'ANALYSING…' : '⬡ GENERATE SOURCE INTELLIGENCE PREVIEW'}
          </button>
        )}
      </div>

      {runError && <p className="text-xs font-mono text-red-400 mb-3">{runError}</p>}
      {running && (
        <p className="text-xs font-mono text-gray-600 italic">Reviewing sources and case context… this may take 15–30 seconds.</p>
      )}

      {result && (
        <div className="space-y-3">
          <div className="bg-indigo-950/40 border border-indigo-700/40 rounded px-3 py-2">
            <p className="text-xs font-mono text-indigo-400 font-bold">PROPOSALS ONLY — NOT APPLIED</p>
            <p className="text-xs font-mono text-gray-700 mt-0.5">
              Source URLs are metadata only. SwissEdge does not crawl or read linked URLs.
            </p>
            <p className="text-xs font-mono text-gray-700 mt-0.5">
              Saved proposals are not applied to investment_sources. Manual approval required for any action.
            </p>
          </div>

          {result.warnings.length > 0 && (
            <div className="bg-orange-950/30 border border-orange-700/30 rounded px-3 py-2">
              <p className="text-xs font-mono text-orange-400 font-bold mb-1">WARNINGS</p>
              {result.warnings.map((w, i) => (
                <p key={i} className="text-xs font-mono text-orange-600">• {w}</p>
              ))}
            </div>
          )}

          {result.source_scores.length > 0 && (
            <div className="rounded border border-gray-800 p-3">
              <p className="text-xs font-mono text-gray-500 uppercase tracking-widest mb-2">Source Scores</p>
              <div className="space-y-3">
                {result.source_scores.map((score: SourceScoreItem, i: number) => (
                  <div key={score.source_id || i} className="border-b border-gray-800 last:border-0 pb-2 last:pb-0">
                    <div className="flex items-center gap-2 mb-1">
                      <span className={`text-xs font-mono ${SIGNAL_COLORS[score.signal_quality] ?? 'text-gray-400'}`}>
                        {score.signal_quality.toUpperCase()}
                      </span>
                      <span className="text-sm text-gray-300">{score.source_name}</span>
                    </div>
                    {score.usefulness_reason && (
                      <p className="text-xs text-gray-400 ml-0 mt-0.5">{score.usefulness_reason}</p>
                    )}
                    {score.suggested_follow_up && (
                      <p className="text-xs font-mono text-cyan-700 mt-0.5">→ {score.suggested_follow_up}</p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {result.suggestions.length > 0 && (
            <div className="rounded border border-gray-800 p-3">
              <p className="text-xs font-mono text-gray-500 uppercase tracking-widest mb-2">Suggested Source Actions</p>
              <div className="space-y-3">
                {result.suggestions.map((sug: SourceIntelligenceSuggestion, i: number) => (
                  <div key={i} className="border-b border-gray-800 last:border-0 pb-2 last:pb-0">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-xs font-mono text-gray-600 border border-gray-700 rounded px-1 py-0.5">
                        {ACTION_LABELS[sug.action] ?? sug.action.toUpperCase()}
                      </span>
                      <span className="text-sm text-gray-300">{sug.source_name}</span>
                      <span className="text-xs font-mono text-gray-600">{sug.source_type}</span>
                      <span className={`text-xs font-mono ml-auto ${CONFIDENCE_COLORS[sug.confidence] ?? 'text-gray-500'}`}>
                        {sug.confidence.toUpperCase()} CONFIDENCE
                      </span>
                    </div>
                    {sug.reason && <p className="text-xs text-gray-400 mt-0.5">{sug.reason}</p>}
                    {sug.evidence_from_case && (
                      <p className="text-xs font-mono text-gray-600 mt-0.5">Evidence: {sug.evidence_from_case}</p>
                    )}
                    <p className="text-xs font-mono text-amber-700 mt-0.5">⚠ Manual review required before any action</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          <p className="text-xs font-mono text-amber-400/60 text-center">{result.disclaimer}</p>

          <div className="pt-2 border-t border-gray-800 flex items-center gap-3 flex-wrap">
            {result.suggestions.length > 0 && (
              <button
                onClick={handleSaveProposals}
                disabled={saving}
                className="px-3 py-1.5 rounded bg-emerald-900 hover:bg-emerald-800 disabled:opacity-40 text-xs font-mono text-emerald-100 transition-colors border border-emerald-700"
              >
                {saving ? 'SAVING…' : `SAVE ${result.suggestions.length} PROPOSAL(S) TO QUEUE`}
              </button>
            )}
            <button
              onClick={handleDiscard}
              className="px-3 py-1.5 rounded border border-gray-700 hover:border-gray-500 text-xs font-mono text-gray-500 transition-colors"
            >
              DISCARD
            </button>
            {saveMsg && <p className="text-xs font-mono text-emerald-500">{saveMsg}</p>}
          </div>
        </div>
      )}

      {savedProposals.length > 0 && (
        <div className="mt-4 border-t border-gray-800 pt-4">
          <p className="text-xs font-mono text-gray-500 uppercase tracking-widest mb-2">
            Saved Proposals ({savedProposals.length})
          </p>
          {reviewMsg && <p className="text-xs font-mono text-emerald-500 mb-2">{reviewMsg}</p>}
          <div className="space-y-2">
            {savedProposals.map((p) => (
              <div key={p.id} className="rounded border border-gray-800 px-3 py-2">
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="text-xs font-mono text-gray-600 border border-gray-700 rounded px-1">
                    {ACTION_LABELS[p.action] ?? p.action.toUpperCase()}
                  </span>
                  <span className="text-sm text-gray-300">{p.proposed_name || '—'}</span>
                  {p.proposed_source_type && (
                    <span className="text-xs font-mono text-gray-600">{p.proposed_source_type}</span>
                  )}
                  <span className={`text-xs font-mono ml-auto ${STATUS_STYLE[p.status] ?? 'text-gray-500'}`}>
                    {p.status.toUpperCase()}
                  </span>
                </div>
                {p.rationale && <p className="text-xs text-gray-500 mt-1">{p.rationale}</p>}
                {p.status === 'proposed' && (
                  <div className="flex gap-2 mt-2">
                    <button
                      onClick={() => handleReview(p.id, 'approved')}
                      className="px-2 py-1 rounded bg-green-900 hover:bg-green-800 text-xs font-mono text-green-100 border border-green-700 transition-colors"
                    >
                      APPROVE
                    </button>
                    <button
                      onClick={() => handleReview(p.id, 'rejected')}
                      className="px-2 py-1 rounded border border-gray-700 hover:border-red-800 text-xs font-mono text-gray-500 hover:text-red-400 transition-colors"
                    >
                      REJECT
                    </button>
                  </div>
                )}
              </div>
            ))}
          </div>
          {loadingProposals && <p className="text-xs font-mono text-gray-700 mt-1">Loading…</p>}
          <p className="text-xs font-mono text-gray-700 mt-2">
            Approved proposals are not applied to investment_sources. No apply action is available.
          </p>
        </div>
      )}
    </div>
  );
}

function PublicDraftPanel({ caseId }: { caseId: string }) {
  const [drafts, setDrafts] = useState<PublicArticleDraft[]>([]);
  const [loading, setLoading] = useState(false);
  const [creating, setCreating] = useState(false);
  const [msg, setMsg] = useState<{ text: string; ok: boolean } | null>(null);

  async function loadDrafts() {
    setLoading(true);
    try {
      const data = await fetchPublicDrafts({ research_case_id: caseId });
      setDrafts(data.public_drafts);
    } catch (err) {
      setMsg({ text: err instanceof Error ? err.message : 'Failed to load public drafts', ok: false });
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadDrafts();
  }, [caseId]);

  async function handleCreate() {
    setCreating(true);
    setMsg(null);
    try {
      const draft = await createPublicDraftFromResearchCase(caseId);
      setDrafts(prev => [draft, ...prev]);
      setMsg({ text: 'Private public draft created.', ok: true });
    } catch (err) {
      setMsg({ text: err instanceof Error ? err.message : 'Failed to create public draft', ok: false });
    } finally {
      setCreating(false);
      setTimeout(() => setMsg(null), 4000);
    }
  }

  const latest = drafts[0];

  return (
    <div className="mt-4 border-t border-gray-800 pt-4">
      <div className="flex items-center justify-between gap-3 mb-3 flex-wrap">
        <span className="text-xs font-mono text-gray-500 tracking-widest">PUBLIC DRAFT</span>
        <button
          onClick={handleCreate}
          disabled={creating}
          className="px-3 py-1.5 rounded bg-emerald-900 hover:bg-emerald-800 disabled:opacity-40 text-xs font-mono text-emerald-100 transition-colors border border-emerald-700"
        >
          {creating ? 'CREATING...' : 'CREATE PUBLIC DRAFT'}
        </button>
      </div>

      <div className="bg-amber-950/40 border border-amber-700/40 rounded px-3 py-2 mb-3">
        <p className="text-xs font-mono text-amber-400 font-bold">PRIVATE DRAFT - NOT PUBLISHED</p>
        <p className="text-xs font-mono text-gray-700 mt-1">
          Manual workflow only. No Substack API, no public posting, no auto-publish.
        </p>
      </div>

      {loading && <p className="text-xs font-mono text-gray-600 italic">Loading drafts...</p>}
      {msg && <p className={`text-xs font-mono mb-3 ${msg.ok ? 'text-green-400' : 'text-red-400'}`}>{msg.text}</p>}

      {latest ? (
        <div className="rounded border border-gray-800 bg-gray-950/40 px-3 py-2">
          <div className="flex items-start justify-between gap-3 flex-wrap">
            <div>
              <p className="text-sm text-gray-200">{latest.title || 'Untitled public draft'}</p>
              <p className="text-xs font-mono text-gray-600 mt-0.5">
                {latest.status.toUpperCase()} · CREATED {new Date(latest.created_at).toLocaleString('en-CH')}
                {latest.approved_at ? ` · APPROVED ${new Date(latest.approved_at).toLocaleString('en-CH')}` : ''}
                {latest.published_at ? ` · PUBLISHED ${new Date(latest.published_at).toLocaleString('en-CH')}` : ''}
              </p>
            </div>
            <Link
              href={`/investment/public-drafts/${latest.id}`}
              className="text-xs font-mono text-emerald-600 hover:text-emerald-300 transition-colors"
            >
              OPEN DRAFT →
            </Link>
          </div>
          {drafts.length > 1 && (
            <Link
              href={`/investment/public-drafts?research_case_id=${caseId}`}
              className="inline-block mt-2 text-xs font-mono text-gray-600 hover:text-gray-400"
            >
              VIEW ALL {drafts.length} DRAFTS
            </Link>
          )}
        </div>
      ) : (
        <p className="text-xs font-mono text-gray-600 italic">
          No public draft exists for this case yet.
        </p>
      )}
    </div>
  );
}

function V2MetadataPanel({ rc }: { rc: ResearchCase }) {
  const hasAny = Boolean(
    rc.source_origin_name || rc.investment_source_id || rc.intake_method ||
    rc.connector_key || rc.intake_event_id || rc.evidence_level ||
    rc.official_source_status || rc.methodology_status ||
    rc.playbook_used || rc.checklist_used || rc.course_reference ||
    rc.duplicate_status || rc.next_follow_up_at || rc.discarded_reason,
  );

  function row(label: string, value: string | null | undefined, fallback = 'not set') {
    return (
      <div key={label}>
        <p className="text-xs font-mono text-gray-600 uppercase tracking-wide mb-0.5">{label}</p>
        <p className="text-xs text-gray-400">{value ?? fallback}</p>
      </div>
    );
  }

  if (!hasAny) {
    return (
      <p className="text-xs font-mono text-gray-600 italic">
        This case was created before V2 intake metadata. It is treated as legacy/manual until source-driven intake updates are implemented.
      </p>
    );
  }

  return (
    <div className="grid grid-cols-2 gap-x-6 gap-y-3 md:grid-cols-3">
      {row('Source origin', rc.source_origin_name, 'legacy/manual')}
      {row('Investment source ID', rc.investment_source_id, 'not linked')}
      {row('Intake method', rc.intake_method, 'legacy/manual')}
      {row('Connector key', rc.connector_key)}
      {row('Intake event ID', rc.intake_event_id)}
      {row('Evidence level', rc.evidence_level, 'unknown')}
      {row('Official source status', rc.official_source_status, 'unknown')}
      {row('Methodology status', rc.methodology_status, 'unknown')}
      {row('Playbook used', rc.playbook_used)}
      {row('Checklist used', rc.checklist_used)}
      {row('Course reference', rc.course_reference)}
      {row('Duplicate status', rc.duplicate_status)}
      {row(
        'Next follow-up',
        rc.next_follow_up_at ? new Date(rc.next_follow_up_at).toLocaleString('en-CH') : null,
      )}
      {row('Discarded reason', rc.discarded_reason)}
    </div>
  );
}

function prepItemTitle(item: unknown): string {
  if (!item || typeof item !== 'object') return 'Untitled item';
  const record = item as Record<string, unknown>;
  const value = record.title ?? record.description ?? record.resource_id ?? record.check_id;
  return typeof value === 'string' && value.trim() ? value.trim() : 'Untitled item';
}

function ReadinessBadge({ level }: { level: EvaluationPrepPackage['readiness']['level'] }) {
  const styles: Record<EvaluationPrepPackage['readiness']['level'], string> = {
    not_ready: 'text-red-300 border-red-900 bg-red-950/20',
    needs_more_evidence: 'text-amber-300 border-amber-900 bg-amber-950/20',
    ready_for_manual_evaluation: 'text-green-300 border-green-900 bg-green-950/20',
  };
  return (
    <span className={`rounded border px-2 py-0.5 text-xs font-mono ${styles[level]}`}>
      {level.replace(/_/g, ' ').toUpperCase()}
    </span>
  );
}

function OperationalViewCard({
  operationalView,
  loading,
  error,
  onRefresh,
}: {
  operationalView: OperationalViewPackage | null;
  loading: boolean;
  error: string | null;
  onRefresh: () => Promise<void>;
}) {
  const [refreshing, setRefreshing] = useState(false);

  async function refresh() {
    setRefreshing(true);
    try {
      await onRefresh();
    } finally {
      setRefreshing(false);
    }
  }

  const viewLabel = operationalView?.operational_view.replaceAll('_', ' ') ?? 'loading';
  const badgeClass =
    operationalView?.operational_view === 'candidate'
      ? 'border-emerald-800 bg-emerald-950/40 text-emerald-300'
      : operationalView?.operational_view === 'watchlist'
      ? 'border-amber-800 bg-amber-950/40 text-amber-300'
      : operationalView?.operational_view === 'reject'
      ? 'border-red-900 bg-red-950/40 text-red-300'
      : 'border-gray-800 bg-gray-950 text-gray-300';

  return (
    <section className="rounded-lg border border-gray-800 bg-gray-950/60 p-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-[11px] uppercase tracking-[0.16em] text-cyan-400">Operational View</p>
          <h2 className="mt-1 text-lg font-semibold text-white">Workflow label preparation</h2>
          <p className="mt-1 max-w-3xl text-sm text-gray-400">
            Deterministic read-only view for manual ResearchCase review. No status is applied automatically.
          </p>
        </div>
        <button
          onClick={refresh}
          disabled={refreshing}
          className="rounded-md border border-gray-700 px-3 py-1.5 text-xs text-gray-200 hover:border-cyan-700 disabled:opacity-50"
        >
          {refreshing ? 'Refreshing...' : 'Refresh'}
        </button>
      </div>

      {error && <p className="mt-4 rounded border border-red-900 bg-red-950/40 p-3 text-sm text-red-300">{error}</p>}
      {loading && <p className="mt-4 text-sm text-gray-500">Loading operational view...</p>}

      {operationalView && !loading && (
        <div className="mt-4 space-y-4">
          <div className="flex flex-wrap gap-2">
            <span className={`rounded-full border px-3 py-1 text-xs font-semibold uppercase ${badgeClass}`}>
              {viewLabel}
            </span>
            <span className="rounded-full border border-gray-800 bg-black/30 px-3 py-1 text-xs uppercase text-gray-300">
              Confidence: {operationalView.confidence}
            </span>
            <span className="rounded-full border border-cyan-900 bg-cyan-950/30 px-3 py-1 text-xs text-cyan-200">
              Final decision by Dani
            </span>
          </div>

          <div className="grid gap-3 md:grid-cols-2">
            <div>
              <h3 className="text-xs font-semibold uppercase text-gray-500">Rationale</h3>
              <ul className="mt-2 space-y-1 text-sm text-gray-300">
                {operationalView.rationale.map((item) => (
                  <li key={item}>- {item}</li>
                ))}
              </ul>
            </div>
            <div>
              <h3 className="text-xs font-semibold uppercase text-gray-500">Blockers</h3>
              {operationalView.blockers.length ? (
                <ul className="mt-2 space-y-1 text-sm text-gray-300">
                  {operationalView.blockers.map((item) => (
                    <li key={item}>- {item}</li>
                  ))}
                </ul>
              ) : (
                <p className="mt-2 text-sm text-gray-500">No blocking metadata detected.</p>
              )}
            </div>
            <div>
              <h3 className="text-xs font-semibold uppercase text-gray-500">What would change view</h3>
              <ul className="mt-2 space-y-1 text-sm text-gray-300">
                {operationalView.what_would_change_view.map((item) => (
                  <li key={item}>- {item}</li>
                ))}
              </ul>
            </div>
            <div>
              <h3 className="text-xs font-semibold uppercase text-gray-500">Next manual actions</h3>
              <ul className="mt-2 space-y-1 text-sm text-gray-300">
                {operationalView.next_manual_actions.map((item) => (
                  <li key={item}>- {item}</li>
                ))}
              </ul>
            </div>
          </div>

          <p className="rounded border border-cyan-900 bg-cyan-950/30 p-3 text-xs text-cyan-100">
            Operational View is a workflow label for manual review. It is not investment advice and does not imply a private action.
          </p>
        </div>
      )}
    </section>
  );
}

function EvaluationPrepPanel({
  prep,
  loading,
  error,
  onRefresh,
}: {
  prep: EvaluationPrepPackage | null;
  loading: boolean;
  error: string | null;
  onRefresh: () => Promise<void>;
}) {
  const [refreshing, setRefreshing] = useState(false);

  async function refresh() {
    setRefreshing(true);
    try {
      await onRefresh();
    } finally {
      setRefreshing(false);
    }
  }

  if (loading) {
    return <p className="text-xs font-mono text-gray-600">Loading preparation package…</p>;
  }
  if (error) {
    return (
      <div className="space-y-2">
        <p className="text-xs font-mono text-red-400">Preparation unavailable: {error}</p>
        <button onClick={refresh} className="text-xs font-mono text-cyan-700 hover:text-cyan-400">REFRESH PREPARATION</button>
      </div>
    );
  }
  if (!prep) {
    return <p className="text-xs font-mono text-gray-600 italic">No preparation package loaded.</p>;
  }

  const missingResources = prep.required_resources.missing.slice(0, 6);
  const checklistGaps = prep.checklist.missing.slice(0, 6);

  return (
    <div className="space-y-4">
      <div className="rounded border border-amber-900/60 bg-amber-950/10 p-3">
        <p className="text-xs font-mono text-amber-300">
          Preparation only — no AI evaluation, no recommendation, no publishing.
        </p>
      </div>

      <div className="flex flex-wrap items-center gap-3">
        <ReadinessBadge level={prep.readiness.level} />
        <span className="text-xs font-mono text-gray-500">SCORE {prep.readiness.score}/100</span>
        <button
          onClick={refresh}
          disabled={refreshing}
          className="ml-auto text-xs font-mono text-cyan-700 hover:text-cyan-400 disabled:opacity-40"
        >
          {refreshing ? 'REFRESHING…' : 'REFRESH PREPARATION'}
        </button>
      </div>

      {(prep.readiness.blocking_reasons.length > 0 || prep.readiness.warnings.length > 0) && (
        <div className="grid gap-3 md:grid-cols-2">
          <div>
            <p className="mb-1 text-xs font-mono uppercase tracking-wide text-gray-600">Blocking Reasons</p>
            {prep.readiness.blocking_reasons.length > 0 ? (
              <ul className="space-y-1">
                {prep.readiness.blocking_reasons.map(reason => (
                  <li key={reason} className="text-xs text-red-300">• {reason}</li>
                ))}
              </ul>
            ) : (
              <p className="text-xs text-gray-600">None.</p>
            )}
          </div>
          <div>
            <p className="mb-1 text-xs font-mono uppercase tracking-wide text-gray-600">Warnings</p>
            {prep.readiness.warnings.length > 0 ? (
              <ul className="space-y-1">
                {prep.readiness.warnings.map(warning => (
                  <li key={warning} className="text-xs text-amber-300">• {warning}</li>
                ))}
              </ul>
            ) : (
              <p className="text-xs text-gray-600">None.</p>
            )}
          </div>
        </div>
      )}

      <div className="grid gap-3 md:grid-cols-4">
        <div className="rounded border border-gray-800 p-3">
          <p className="text-xs font-mono text-gray-600">REQUIRED</p>
          <p className="text-lg font-mono text-gray-200">{prep.required_resources.total}</p>
        </div>
        <div className="rounded border border-gray-800 p-3">
          <p className="text-xs font-mono text-gray-600">MISSING</p>
          <p className="text-lg font-mono text-red-300">{prep.required_resources.missing.length}</p>
        </div>
        <div className="rounded border border-gray-800 p-3">
          <p className="text-xs font-mono text-gray-600">CANDIDATES</p>
          <p className="text-lg font-mono text-amber-300">{prep.required_resources.candidate_found.length}</p>
        </div>
        <div className="rounded border border-gray-800 p-3">
          <p className="text-xs font-mono text-gray-600">EVIDENCE</p>
          <p className="text-lg font-mono text-green-300">{prep.required_resources.evidence_found.length + prep.required_resources.verified.length}</p>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <div>
          <p className="mb-2 text-xs font-mono uppercase tracking-wide text-gray-600">Missing Required Resources</p>
          {missingResources.length > 0 ? (
            <ul className="space-y-1">
              {missingResources.map((item, index) => (
                <li key={`${prepItemTitle(item)}-${index}`} className="text-xs text-gray-300">• {prepItemTitle(item)}</li>
              ))}
            </ul>
          ) : (
            <p className="text-xs text-gray-600">No missing required resources in the snapshot.</p>
          )}
        </div>
        <div>
          <p className="mb-2 text-xs font-mono uppercase tracking-wide text-gray-600">Checklist Gaps</p>
          {checklistGaps.length > 0 ? (
            <ul className="space-y-1">
              {checklistGaps.map((item, index) => (
                <li key={`${prepItemTitle(item)}-${index}`} className="text-xs text-gray-300">• {prepItemTitle(item)}</li>
              ))}
            </ul>
          ) : (
            <p className="text-xs text-gray-600">No unsupported checklist gaps in the snapshot.</p>
          )}
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <div>
          <p className="mb-2 text-xs font-mono uppercase tracking-wide text-gray-600">Source Quality</p>
          <div className="space-y-1 text-xs text-gray-400">
            <p>Official sources: {prep.source_quality.official_sources_count}</p>
            <p>Attached sources/documents: {prep.source_quality.metadata_only_sources_count}</p>
            <p>Manual sources: {prep.source_quality.manual_sources_count}</p>
            <p className="text-gray-600">Sources are metadata-only; no document bodies are fetched.</p>
          </div>
          {prep.source_quality.issues.length > 0 && (
            <ul className="mt-2 space-y-1">
              {prep.source_quality.issues.map(issue => (
                <li key={issue} className="text-xs text-amber-300">• {issue}</li>
              ))}
            </ul>
          )}
          {prep.evidence_links_summary && (
            <div className="mt-3 rounded border border-gray-800 p-2">
              <p className="text-xs font-mono uppercase tracking-wide text-gray-600">Evidence Links</p>
              <div className="mt-1 space-y-1 text-xs text-gray-400">
                <p>Total links: {prep.evidence_links_summary.total_links}</p>
                <p>SEC links: {prep.evidence_links_summary.sec_links}</p>
                <p>Research records: {prep.evidence_links_summary.research_source_links + prep.evidence_links_summary.research_document_links}</p>
                <p>Missing linked items: {prep.evidence_links_summary.missing_link_items.length}</p>
              </div>
            </div>
          )}
        </div>
        <div>
          <p className="mb-2 text-xs font-mono uppercase tracking-wide text-gray-600">Next Manual Actions</p>
          <div className="space-y-2">
            {prep.suggested_next_actions.map(action => (
              <div key={`${action.label}-${action.reason}`} className="rounded border border-gray-800 p-2">
                <div className="flex items-center justify-between gap-2">
                  <p className="text-xs font-mono text-cyan-300">{action.label}</p>
                  <span className="text-[10px] font-mono text-gray-600">{action.priority.toUpperCase()}</span>
                </div>
                <p className="mt-1 text-xs text-gray-500">{action.reason}</p>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="border-t border-gray-800 pt-3">
        <p className="mb-1 text-xs font-mono uppercase tracking-wide text-gray-600">Guardrails</p>
        <div className="flex flex-wrap gap-2">
          {prep.guardrails.map(guardrail => (
            <span key={guardrail} className="rounded border border-gray-800 px-2 py-0.5 text-[10px] font-mono text-gray-500">
              {guardrail}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
}

function QuickSourceLinks({
  rc,
  evidenceLinks,
}: {
  rc: ResearchCase;
  evidenceLinks: ResearchCaseEvidenceLinksPackage | null;
}) {
  const links = [
    ...(rc.situation_id ? [{ label: 'Origin situation', href: `/investment/situations/${rc.situation_id}`, external: false }] : []),
    ...rc.documents.slice(0, 4).map(doc => ({
      label: doc.title || doc.doc_type || 'Research document',
      href: doc.url,
      external: true,
    })),
    ...rc.sources.filter(source => source.source_url).slice(0, 4).map(source => ({
      label: source.source_name,
      href: source.source_url!,
      external: true,
    })),
    ...(evidenceLinks?.links ?? []).filter(link => link.url).slice(0, 4).map(link => ({
      label: link.label || link.source_type,
      href: link.url!,
      external: true,
    })),
  ].slice(0, 8);

  return (
    <Section title="Quick Source Links" hint="Metadata links only. Opening a link is a manual browser action.">
      {links.length === 0 ? (
        <p className="text-xs font-mono text-gray-600 italic">No source, document, or evidence links recorded yet.</p>
      ) : (
        <div className="grid gap-2 md:grid-cols-2">
          {links.map((link, index) => (
            link.external ? (
              <a
                key={`${link.href}-${index}`}
                href={link.href}
                target="_blank"
                rel="noreferrer"
                className="rounded border border-gray-800 px-3 py-2 text-xs font-mono text-cyan-700 hover:text-cyan-400"
              >
                {link.label}
              </a>
            ) : (
              <Link
                key={`${link.href}-${index}`}
                href={link.href}
                className="rounded border border-gray-800 px-3 py-2 text-xs font-mono text-cyan-700 hover:text-cyan-400"
              >
                {link.label}
              </Link>
            )
          ))}
        </div>
      )}
    </Section>
  );
}

function CaseActivityLog({ rc }: { rc: ResearchCase }) {
  const rows = [
    { label: 'Case created', at: rc.created_at, detail: rc.intake_method ?? 'manual/private desk' },
    { label: 'Last updated', at: rc.updated_at, detail: rc.status },
    ...rc.tasks.slice(0, 3).map(task => ({ label: `Task ${task.status}`, at: task.created_at, detail: task.description })),
    ...rc.documents.slice(0, 3).map(doc => ({ label: 'Document added', at: doc.created_at, detail: doc.title || doc.doc_type || doc.url })),
    ...rc.sources.slice(0, 3).map(source => ({ label: 'Source added', at: source.created_at, detail: source.source_name })),
  ]
    .filter(row => row.at)
    .sort((a, b) => String(b.at).localeCompare(String(a.at)))
    .slice(0, 8);

  return (
    <Section title="Case Activity Log" hint="Read-only event summary from stored case records.">
      {rows.length === 0 ? (
        <p className="text-xs font-mono text-gray-600 italic">No case activity rows available yet.</p>
      ) : (
        <div className="space-y-2">
          {rows.map((row, index) => (
            <div key={`${row.label}-${row.at}-${index}`} className="flex items-start gap-3 rounded border border-gray-800 p-2">
              <span className="mt-1 h-2 w-2 rounded-full bg-cyan-700" />
              <div className="min-w-0">
                <p className="text-xs font-mono text-gray-300">{row.label}</p>
                <p className="text-xs text-gray-500">{new Date(row.at).toLocaleString('en-CH')} / {row.detail}</p>
              </div>
            </div>
          ))}
        </div>
      )}
    </Section>
  );
}

function guideItemTitle(item: Record<string, unknown>): string {
  const value = item.title ?? item.label ?? item.resource_id ?? item.check_id ?? item.query;
  return typeof value === 'string' && value.trim() ? value : 'Untitled item';
}

function guideTargetFor(label: string): string {
  const normalized = label.toLowerCase();
  if (normalized.includes('sec') || normalized.includes('filing') || normalized.includes('origin')) return 'guide-find-case';
  if (normalized.includes('required resource')) return 'guide-required-resources';
  if (normalized.includes('candidate') || normalized.includes('evidence link') || normalized.includes('evidence present')) return 'guide-evidence-links';
  if (normalized.includes('checklist') || normalized.includes('human review')) return 'guide-checklist';
  if (normalized.includes('search')) return 'guide-search-suggestions';
  if (normalized.includes('researchcase')) return 'guide-researchcase';
  return '';
}

function GuideStatusChip({ label, status }: { label: string; status: string }) {
  const target = guideTargetFor(label);
  if (!target) {
    return <p className={`text-xs font-mono ${status === 'ok' ? 'text-green-400' : 'text-amber-300'}`}>{status}</p>;
  }
  return (
    <a
      href={`#${target}`}
      className={`text-xs font-mono ${status === 'ok' ? 'text-green-400' : 'text-amber-300'} hover:text-cyan-300`}
      aria-label={`Jump to ${label} section`}
    >
      {status}
    </a>
  );
}

function DocumentationGuidePanel({
  guide,
  error,
}: {
  guide: CaseDocumentationGuidePackage | null;
  error: string | null;
}) {
  const [copiedKey, setCopiedKey] = useState<string | null>(null);

  async function copyQuery(query: string, key: string) {
    try {
      if (!navigator.clipboard?.writeText) throw new Error('Clipboard API unavailable');
      await navigator.clipboard.writeText(query);
      setCopiedKey(key);
    } catch {
      setCopiedKey('copy-failed');
    }
    setTimeout(() => setCopiedKey(null), 1500);
  }

  if (error) {
    return (
      <Section title="Case Documentation Guide">
        <p className="text-xs font-mono text-amber-300">{error}</p>
      </Section>
    );
  }
  if (!guide) return null;

  const missingTotal =
    guide.missing_evidence.missing_required_resources.length +
    guide.missing_evidence.missing_checklist_items.length;

  return (
    <Section title="Case Documentation Guide" hint="Derived from current case state. No autonomous agent run yet. No document body has been fetched.">
      <div className="space-y-5">
        <div className="grid gap-3 md:grid-cols-[180px_1fr]">
          <div className="rounded border border-gray-800 bg-gray-900/40 p-3">
            <p className="text-xs font-mono uppercase tracking-wide text-gray-600">Documentation quality</p>
            <p className="mt-1 text-2xl font-mono text-cyan-300">{guide.documentation_quality.score}/100</p>
            <p className="mt-1 text-xs font-mono text-gray-500">{guide.documentation_quality.level.replace(/_/g, ' ')}</p>
          </div>
          <div className="rounded border border-gray-800 p-3">
            <p className="text-sm text-gray-300">{guide.documentation_quality.summary}</p>
            <div className="mt-3 grid gap-2 md:grid-cols-3">
              {guide.documentation_quality.checks.map(check => (
                <div key={check.label} className="rounded border border-gray-800 px-2 py-1.5">
                  <p className="text-xs text-gray-400">{check.label}</p>
                  <GuideStatusChip label={check.label} status={check.status} />
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="grid gap-4 lg:grid-cols-3">
          <div id="guide-find-case" className="scroll-mt-20">
            <p className="mb-2 text-xs font-mono uppercase tracking-wide text-gray-600">How to find this case</p>
            <div className="space-y-1 text-xs text-gray-400">
              <p>Source: {guide.detection_guide.source}</p>
              <p>Origin SpecialSituation: {guide.detection_guide.company_name ?? '-'}</p>
              <p>CIK: {guide.detection_guide.cik ?? '-'}</p>
              <p>Accession: {guide.detection_guide.accession_number ?? '-'}</p>
              <p>Filing: {guide.detection_guide.filing_type ?? '-'} / {guide.detection_guide.filing_date ?? '-'}</p>
              {guide.detection_guide.filing_url && (
                <a href={guide.detection_guide.filing_url} target="_blank" rel="noreferrer" className="mt-2 inline-flex rounded border border-gray-700 px-3 py-1 text-xs font-mono text-cyan-700 hover:text-cyan-400">
                  Open SEC filing
                </a>
              )}
            </div>
          </div>
          <div id="guide-checklist" className="scroll-mt-20">
            <p className="mb-2 text-xs font-mono uppercase tracking-wide text-gray-600">Manual verification steps</p>
            <ol className="list-decimal space-y-1 pl-4">
              {guide.detection_guide.manual_verification_steps.map(step => (
                <li key={step} className="text-xs text-gray-400">{step}</li>
              ))}
            </ol>
          </div>
          <div id="guide-researchcase" className="scroll-mt-20">
            <p className="mb-2 text-xs font-mono uppercase tracking-wide text-gray-600">Missing Evidence Hunter</p>
            <p className="text-xs leading-5 text-gray-400">{guide.research_agent.current_mission}</p>
            <p className="mt-2 text-xs font-mono text-gray-500">Current mode: manual / observer-only</p>
            <p className="mt-1 text-xs text-gray-500">{guide.research_agent.future_scheduler_note}</p>
          </div>
        </div>

        <div className="grid gap-4 lg:grid-cols-3">
          <div id="guide-required-resources" className="scroll-mt-20">
            <p className="mb-2 text-xs font-mono uppercase tracking-wide text-gray-600">Missing required resources ({guide.missing_evidence.missing_required_resources.length})</p>
            {guide.missing_evidence.missing_required_resources.length === 0 ? (
              <p className="text-xs text-gray-600">No missing required resources in the guide.</p>
            ) : (
              <ul className="list-disc space-y-1 pl-4">
                {guide.missing_evidence.missing_required_resources.slice(0, 6).map((item, index) => (
                  <li key={`${guideItemTitle(item)}-${index}`} className="text-xs text-gray-400">{guideItemTitle(item)}</li>
                ))}
              </ul>
            )}
          </div>
          <div>
            <p className="mb-2 text-xs font-mono uppercase tracking-wide text-gray-600">Missing checklist evidence ({guide.missing_evidence.missing_checklist_items.length})</p>
            {guide.missing_evidence.missing_checklist_items.length === 0 ? (
              <p className="text-xs text-gray-600">No checklist gaps in the guide.</p>
            ) : (
              <ul className="list-disc space-y-1 pl-4">
                {guide.missing_evidence.missing_checklist_items.slice(0, 6).map((item, index) => (
                  <li key={`${guideItemTitle(item)}-${index}`} className="text-xs text-gray-400">{guideItemTitle(item)}</li>
                ))}
              </ul>
            )}
          </div>
          <div>
            <p className="mb-2 text-xs font-mono uppercase tracking-wide text-gray-600">Current manual research plan</p>
            <ul className="list-disc space-y-1 pl-4">
              {guide.research_agent.next_manual_actions.slice(0, 5).map(action => (
                <li key={action} className="text-xs text-gray-400">{action}</li>
              ))}
            </ul>
          </div>
        </div>

        <div id="guide-evidence-links" className="scroll-mt-20">
          <p className="mb-2 text-xs font-mono uppercase tracking-wide text-gray-600">Evidence links / resource candidates</p>
          <div className="flex flex-wrap gap-2">
            <span className="rounded border border-gray-800 px-2 py-0.5 text-[10px] font-mono text-gray-500">Candidate-only: {guide.missing_evidence.candidate_only_resources.length}</span>
            <span className="rounded border border-amber-900 px-2 py-0.5 text-[10px] font-mono text-amber-300">Evidence not verified: {guide.missing_evidence.evidence_found_not_verified.length}</span>
            <span className="rounded border border-gray-800 px-2 py-0.5 text-[10px] font-mono text-gray-500">Rejected: {guide.missing_evidence.rejected_resources.length}</span>
          </div>
        </div>

        <div id="guide-search-suggestions" className="scroll-mt-20">
          <p className="mb-2 text-xs font-mono uppercase tracking-wide text-gray-600">Manual search suggestions</p>
          <p className="mb-2 text-xs text-gray-500">
            Stored prompts for a human researcher. They are not fetched automatically, not evidence, and not verified.
            Paste this into Google, SEC search, or company IR. SwissEdge has not run this search automatically.
            {copiedKey === 'copy-failed' && (
              <span className="mt-1 block text-amber-400">Copy failed - select the query text manually.</span>
            )}
          </p>
          {guide.search_plan.copyable_queries.length === 0 ? (
            <p className="text-xs text-gray-600">No stored search suggestions yet.</p>
          ) : (
            <div className="grid gap-2">
              {guide.search_plan.copyable_queries.map((query, index) => (
                <div key={`${query}-${index}`} className="rounded border border-gray-800 px-3 py-2">
                  <p className="text-xs text-gray-300 break-words">{query}</p>
                  <button
                    onClick={() => copyQuery(query, `query-${index}`)}
                    className="mt-2 rounded border border-gray-700 px-3 py-1 text-xs font-mono text-gray-400 hover:text-cyan-400"
                  >
                    {copiedKey === `query-${index}` ? 'Copied' : 'Copy query'}
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>

        <div>
          <p className="mb-2 text-xs font-mono uppercase tracking-wide text-gray-600">Derived activity timeline</p>
          <div className="space-y-2">
            {guide.activity_timeline.slice(0, 8).map((event, index) => (
              <div key={`${event.label}-${index}`} className="rounded border border-gray-800 px-3 py-2">
                <p className="text-xs font-mono text-gray-300">{event.label}</p>
                <p className="text-xs text-gray-500">
                  {event.timestamp ? new Date(event.timestamp).toLocaleString('en-CH') : 'Current state — timestamp unavailable'}
                  {event.detail ? ` / ${event.detail}` : ''}
                </p>
              </div>
            ))}
          </div>
        </div>

        <p className="text-xs font-mono text-gray-700">
          Missing items: {missingTotal} · Frequent checks planned for future approved sprint · Scheduler disabled in this sprint
        </p>
      </div>
    </Section>
  );
}

export default function ResearchDetailPage() {
  const params = useParams();
  const id = params.id as string;

  const [rc, setRc] = useState<ResearchCase | null>(null);
  const [evaluationPrep, setEvaluationPrep] = useState<EvaluationPrepPackage | null>(null);
  const [evidenceLinks, setEvidenceLinks] = useState<ResearchCaseEvidenceLinksPackage | null>(null);
  const [intelligenceScore, setIntelligenceScore] = useState<IntelligenceScorePackage | null>(null);
  const [documentationGuide, setDocumentationGuide] = useState<CaseDocumentationGuidePackage | null>(null);
  const [completionWorkbench, setCompletionWorkbench] = useState<CaseCompletionPackage | null>(null);
  const [officialSourceFinder, setOfficialSourceFinder] = useState<OfficialSourceFinderPackage | null>(null);
  const [operationalView, setOperationalView] = useState<OperationalViewPackage | null>(null);
  const [secDocumentAcquisition, setSecDocumentAcquisition] = useState<SecDocumentAcquisitionPackage | null>(null);
  const [documentPackage, setDocumentPackage] = useState<DocumentPackage | null>(null);
  const [historicalAnalogues, setHistoricalAnalogues] = useState<HistoricalAnaloguesPackage | null>(null);
  const [activityTimeline, setActivityTimeline] = useState<CaseActivityTimelinePackage | null>(null);
  const [prepLoading, setPrepLoading] = useState(true);
  const [scoreLoading, setScoreLoading] = useState(true);
  const [officialSourceFinderLoading, setOfficialSourceFinderLoading] = useState(false);
  const [prepError, setPrepError] = useState<string | null>(null);
  const [evidenceLinksError, setEvidenceLinksError] = useState<string | null>(null);
  const [scoreError, setScoreError] = useState<string | null>(null);
  const [documentationGuideError, setDocumentationGuideError] = useState<string | null>(null);
  const [completionWorkbenchError, setCompletionWorkbenchError] = useState<string | null>(null);
  const [completionWorkbenchLoading, setCompletionWorkbenchLoading] = useState(false);
  const [officialSourceFinderError, setOfficialSourceFinderError] = useState<string | null>(null);
  const [operationalViewError, setOperationalViewError] = useState<string | null>(null);
  const [operationalViewLoading, setOperationalViewLoading] = useState(false);
  const [secDocumentAcquisitionError, setSecDocumentAcquisitionError] = useState<string | null>(null);
  const [secDocumentAcquisitionLoading, setSecDocumentAcquisitionLoading] = useState(false);
  const [secDocumentAcquiring, setSecDocumentAcquiring] = useState(false);
  const [documentPackageError, setDocumentPackageError] = useState<string | null>(null);
  const [documentPackageLoading, setDocumentPackageLoading] = useState(false);
  const [historicalAnaloguesError, setHistoricalAnaloguesError] = useState<string | null>(null);
  const [historicalAnaloguesLoading, setHistoricalAnaloguesLoading] = useState(false);
  const [activityTimelineError, setActivityTimelineError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [officialSourceCopiedKey, setOfficialSourceCopiedKey] = useState<string | null>(null);

  // Edit state
  const [editingStatus, setEditingStatus] = useState(false);
  const [newStatus, setNewStatus] = useState('');
  const [editingReadiness, setEditingReadiness] = useState(false);
  const [newReadiness, setNewReadiness] = useState('');
  const [editingNotes, setEditingNotes] = useState(false);
  const [notesText, setNotesText] = useState('');
  const [saving, setSaving] = useState(false);
  const [actionMsg, setActionMsg] = useState<{ text: string; ok: boolean } | null>(null);

  // Add task form
  const [showAddTask, setShowAddTask] = useState(false);
  const [newTaskDesc, setNewTaskDesc] = useState('');
  const [newTaskPriority, setNewTaskPriority] = useState('3');
  const [addingTask, setAddingTask] = useState(false);
  const [taskError, setTaskError] = useState<string | null>(null);

  // Add document form
  const [showAddDoc, setShowAddDoc] = useState(false);
  const [newDocUrl, setNewDocUrl] = useState('');
  const [newDocTitle, setNewDocTitle] = useState('');
  const [newDocType, setNewDocType] = useState('');
  const [addingDoc, setAddingDoc] = useState(false);
  const [docError, setDocError] = useState<string | null>(null);

  // Add source form
  const [showAddSource, setShowAddSource] = useState(false);
  const [newSrcName, setNewSrcName] = useState('');
  const [newSrcUrl, setNewSrcUrl] = useState('');
  const [newSrcQuality, setNewSrcQuality] = useState('medium');
  const [addingSource, setAddingSource] = useState(false);
  const [sourceError, setSourceError] = useState<string | null>(null);

  function showAction(text: string, ok: boolean) {
    setActionMsg({ text, ok });
    setTimeout(() => setActionMsg(null), 3000);
  }

  async function load() {
    try {
      setLoading(true);
      setError(null);
      const data = await fetchResearchCase(id);
      setRc(data);
      setNotesText(data.notes ?? '');
      setNewStatus(data.status);
      setNewReadiness(data.investment_readiness ?? '');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load research case');
    } finally {
      setLoading(false);
    }
  }

  async function loadEvaluationPrep() {
    try {
      setPrepLoading(true);
      setPrepError(null);
      const prepData = await fetchResearchCaseEvaluationPrep(id);
      setEvaluationPrep(prepData);
    } catch (err) {
      setPrepError(err instanceof Error ? err.message : 'Failed to load evaluation preparation');
    } finally {
      setPrepLoading(false);
    }
  }

  async function loadEvidenceLinks() {
    try {
      setEvidenceLinksError(null);
      const linksData = await fetchResearchCaseEvidenceLinks(id);
      setEvidenceLinks(linksData);
    } catch (err) {
      setEvidenceLinksError(err instanceof Error ? err.message : 'Failed to load research traceability');
    }
  }

  async function loadIntelligenceScore() {
    try {
      setScoreLoading(true);
      setScoreError(null);
      const scoreData = await fetchResearchCaseIntelligenceScore(id);
      setIntelligenceScore(scoreData);
    } catch (err) {
      setScoreError(err instanceof Error ? err.message : 'Failed to load intelligence score');
    } finally {
      setScoreLoading(false);
    }
  }

  async function loadDocumentationGuide() {
    try {
      setDocumentationGuideError(null);
      const guideData = await fetchResearchCaseDocumentationGuide(id);
      setDocumentationGuide(guideData);
    } catch (err) {
      setDocumentationGuideError(err instanceof Error ? err.message : 'Failed to load documentation guide');
    }
  }

  async function loadCompletionWorkbench() {
    try {
      setCompletionWorkbenchLoading(true);
      setCompletionWorkbenchError(null);
      const completionData = await fetchResearchCaseCompletionWorkbench(id);
      setCompletionWorkbench(completionData);
    } catch (err) {
      setCompletionWorkbenchError(err instanceof Error ? err.message : 'Failed to load completion workbench');
    } finally {
      setCompletionWorkbenchLoading(false);
    }
  }

  async function loadOfficialSourceFinder() {
    try {
      setOfficialSourceFinderLoading(true);
      setOfficialSourceFinderError(null);
      const finderData = await fetchResearchCaseOfficialSourceFinder(id);
      setOfficialSourceFinder(finderData);
    } catch (err) {
      setOfficialSourceFinderError(err instanceof Error ? err.message : 'Failed to load official source finder');
    } finally {
      setOfficialSourceFinderLoading(false);
    }
  }

  async function loadOperationalView() {
    try {
      setOperationalViewLoading(true);
      setOperationalViewError(null);
      const viewData = await fetchResearchCaseOperationalView(id);
      setOperationalView(viewData);
    } catch (err) {
      setOperationalViewError(err instanceof Error ? err.message : 'Failed to load operational view');
    } finally {
      setOperationalViewLoading(false);
    }
  }

  async function loadSecDocumentAcquisition() {
    try {
      setSecDocumentAcquisitionLoading(true);
      setSecDocumentAcquisitionError(null);
      const preview = await fetchResearchCaseSecDocumentAcquisitionPreview(id);
      setSecDocumentAcquisition(preview);
    } catch (err) {
      setSecDocumentAcquisitionError(err instanceof Error ? err.message : 'Failed to load SEC document acquisition preview');
    } finally {
      setSecDocumentAcquisitionLoading(false);
    }
  }

  async function loadDocumentPackage() {
    try {
      setDocumentPackageLoading(true);
      setDocumentPackageError(null);
      const data = await fetchResearchCaseDocumentPackage(id);
      setDocumentPackage(data);
    } catch (err) {
      setDocumentPackageError(err instanceof Error ? err.message : 'Failed to load document package');
    } finally {
      setDocumentPackageLoading(false);
    }
  }

  async function loadHistoricalAnalogues() {
    try {
      setHistoricalAnaloguesLoading(true);
      setHistoricalAnaloguesError(null);
      const analogueData = await fetchResearchCaseHistoricalAnalogues(id);
      setHistoricalAnalogues(analogueData);
    } catch (err) {
      setHistoricalAnaloguesError(err instanceof Error ? err.message : 'Failed to load historical analogues');
    } finally {
      setHistoricalAnaloguesLoading(false);
    }
  }

  async function loadActivityTimeline() {
    try {
      setActivityTimelineError(null);
      const timelineData = await fetchResearchCaseActivityTimeline(id);
      setActivityTimeline(timelineData);
    } catch (err) {
      setActivityTimelineError(err instanceof Error ? err.message : 'Failed to load case activity timeline');
    }
  }

  async function copyOfficialSourceQuery(text: string, key: string) {
    try {
      if (!navigator.clipboard?.writeText) throw new Error('Clipboard API unavailable');
      await navigator.clipboard.writeText(text);
      setOfficialSourceCopiedKey(key);
    } catch {
      setOfficialSourceCopiedKey('copy-failed');
    }
    setTimeout(() => setOfficialSourceCopiedKey(null), 1500);
  }

  async function handleSecDocumentAcquisition() {
    try {
      setSecDocumentAcquiring(true);
      setSecDocumentAcquisitionError(null);
      const result = await acquireResearchCaseSecDocuments(id);
      setSecDocumentAcquisition(result);
      await load();
      await loadEvidenceLinks();
      await loadOperationalView();
      await loadDocumentPackage();
    } catch (err) {
      setSecDocumentAcquisitionError(err instanceof Error ? err.message : 'Failed to acquire SEC document metadata');
    } finally {
      setSecDocumentAcquiring(false);
    }
  }

  useEffect(() => {
    load();
    loadEvaluationPrep();
    loadEvidenceLinks();
    loadIntelligenceScore();
    loadDocumentationGuide();
    loadCompletionWorkbench();
    loadOfficialSourceFinder();
    loadOperationalView();
    loadSecDocumentAcquisition();
    loadDocumentPackage();
    loadHistoricalAnalogues();
    loadActivityTimeline();
  }, [id]);

  async function saveField(payload: Parameters<typeof updateResearchCase>[1], successMsg: string) {
    if (!rc) return;
    setSaving(true);
    try {
      const updated = await updateResearchCase(rc.id, payload);
      setRc(updated);
      setNotesText(updated.notes ?? '');
      setNewStatus(updated.status);
      setNewReadiness(updated.investment_readiness ?? '');
      setEditingStatus(false);
      setEditingReadiness(false);
      setEditingNotes(false);
      showAction(successMsg, true);
    } catch (err) {
      showAction(err instanceof Error ? err.message : 'Failed to save', false);
    } finally {
      setSaving(false);
    }
  }

  async function handleAddTask() {
    if (!rc || !newTaskDesc.trim()) return;
    setAddingTask(true);
    setTaskError(null);
    try {
      await addResearchTask(rc.id, { description: newTaskDesc.trim(), priority: parseInt(newTaskPriority, 10) });
      setNewTaskDesc('');
      setNewTaskPriority('3');
      setShowAddTask(false);
      await load();
    } catch (err) {
      setTaskError(err instanceof Error ? err.message : 'Failed to add task');
    } finally {
      setAddingTask(false);
    }
  }

  async function handleUpdateTaskStatus(taskId: string, status: string) {
    try {
      await updateResearchTask(taskId, { status });
      await load();
    } catch (err) {
      showAction(err instanceof Error ? err.message : 'Failed to update task', false);
    }
  }

  async function handleAddDoc() {
    if (!rc || !newDocUrl.trim()) return;
    setAddingDoc(true);
    setDocError(null);
    try {
      await addResearchDocument(rc.id, {
        url: newDocUrl.trim(),
        title: newDocTitle.trim() || undefined,
        doc_type: newDocType || undefined,
      });
      setNewDocUrl('');
      setNewDocTitle('');
      setNewDocType('');
      setShowAddDoc(false);
      await load();
    } catch (err) {
      setDocError(err instanceof Error ? err.message : 'Failed to add document');
    } finally {
      setAddingDoc(false);
    }
  }

  async function handleAddSource() {
    if (!rc || !newSrcName.trim()) return;
    setAddingSource(true);
    setSourceError(null);
    try {
      await addResearchSource(rc.id, {
        source_name: newSrcName.trim(),
        source_url: newSrcUrl.trim() || undefined,
        signal_quality: newSrcQuality,
      });
      setNewSrcName('');
      setNewSrcUrl('');
      setNewSrcQuality('medium');
      setShowAddSource(false);
      await load();
    } catch (err) {
      setSourceError(err instanceof Error ? err.message : 'Failed to add source');
    } finally {
      setAddingSource(false);
    }
  }

  if (loading) return (
    <div className="min-h-screen p-8 flex items-center justify-center">
      <p className="text-gray-500 font-mono text-sm">Loading research case…</p>
    </div>
  );

  if (error || !rc) return (
    <div className="min-h-screen p-8">
      <div className="max-w-4xl mx-auto">
        <Link href="/investment/research" className="text-xs font-mono text-gray-600 hover:text-cyan-400">← RESEARCH CASES</Link>
        <p className="text-red-400 font-mono text-sm mt-4">Error: {error ?? 'Research case not found'}</p>
      </div>
    </div>
  );

  return (
    <div className="min-h-screen p-8">
      <div className="max-w-4xl mx-auto">

        {/* Breadcrumb nav */}
        <div className="flex items-center gap-3 mb-6 text-xs font-mono text-gray-600">
          <Link href="/" className="hover:text-cyan-400">MISSION CONTROL</Link>
          <span>/</span>
          <Link href="/investment/evaluations" className="hover:text-cyan-400">EVALUATIONS</Link>
          <span>/</span>
          <Link href="/investment/situations" className="hover:text-cyan-400">KANBAN</Link>
          <span>/</span>
          <Link href="/investment/research" className="hover:text-cyan-400">RESEARCH CASES</Link>
          <span>/</span>
          <span className="text-cyan-400">{rc.id.slice(0, 8).toUpperCase()}</span>
        </div>

        {/* Global action message */}
        {actionMsg && (
          <div className={`glass-panel rounded p-2 mb-4 text-xs font-mono text-center ${actionMsg.ok ? 'text-green-400 border-green-800' : 'text-red-400 border-red-800'}`}>
            {actionMsg.text}
          </div>
        )}

        {/* ── Workspace Header ── */}
        <div className="glass-panel rounded-lg p-5 mb-4">
          <div className="flex items-start justify-between gap-4 flex-wrap">
            <div>
              <p className="text-xs font-mono text-gray-600 tracking-widest uppercase mb-1">Research Workspace</p>
              <h1 className="text-xl font-bold font-mono text-cyan-400">
                CASE {rc.id.slice(0, 8).toUpperCase()}
              </h1>
              <div className="flex flex-wrap gap-x-4 gap-y-0.5 mt-1 text-xs font-mono text-gray-500">
                {rc.situation_id && (
                  <span>
                    SITUATION:{' '}
                    <Link href={`/investment/evaluations/${rc.situation_id}`} className="text-cyan-700 hover:text-cyan-400">
                      {rc.situation_id.slice(0, 8).toUpperCase()} →
                    </Link>
                  </span>
                )}
                <span>UPDATED: {new Date(rc.updated_at).toLocaleString('en-CH')}</span>
                {rc.model_used && <span>MODEL: {rc.model_used}</span>}
                {rc.playbook_version && <span>PLAYBOOK: {rc.playbook_version}</span>}
              </div>
            </div>

            {/* Status + Readiness editors */}
            <div className="flex gap-2 flex-wrap">
              <Link href="/investment/situations" className="px-2 py-0.5 rounded border border-gray-700 text-xs font-mono text-gray-400 hover:text-cyan-300">
                KANBAN
              </Link>
              <Link href="/investment/intelligence" className="px-2 py-0.5 rounded border border-gray-700 text-xs font-mono text-gray-400 hover:text-cyan-300">
                KPIS
              </Link>
              {editingStatus ? (
                <div className="flex items-center gap-2">
                  <select
                    value={newStatus}
                    onChange={e => setNewStatus(e.target.value)}
                    className="bg-gray-900 border border-cyan-700 rounded px-2 py-1 text-xs font-mono text-gray-200"
                  >
                    {STATUSES.map(s => <option key={s} value={s}>{s}</option>)}
                  </select>
                  <button
                    onClick={() => saveField({ status: newStatus }, 'Status updated')}
                    disabled={saving}
                    className="px-2 py-1 rounded bg-cyan-800 text-xs font-mono text-cyan-100 disabled:opacity-40"
                  >
                    {saving ? '…' : 'SAVE'}
                  </button>
                  <button onClick={() => setEditingStatus(false)} className="px-2 py-1 rounded border border-gray-700 text-xs font-mono text-gray-500">✕</button>
                </div>
              ) : (
                <button
                  onClick={() => setEditingStatus(true)}
                  className={`px-2 py-0.5 rounded border text-xs font-mono hover:opacity-80 transition-opacity ${STATUS_COLORS[rc.status] ?? 'text-gray-400 border-gray-700'}`}
                >
                  {rc.status.replace(/_/g, ' ').toUpperCase()} ✎
                </button>
              )}

              {editingReadiness ? (
                <div className="flex items-center gap-2">
                  <select
                    value={newReadiness}
                    onChange={e => setNewReadiness(e.target.value)}
                    className="bg-gray-900 border border-cyan-700 rounded px-2 py-1 text-xs font-mono text-gray-200"
                  >
                    <option value="">— none —</option>
                    {READINESS.map(r => <option key={r} value={r}>{r}</option>)}
                  </select>
                  <button
                    onClick={() => saveField({ investment_readiness: newReadiness || undefined }, 'Readiness updated')}
                    disabled={saving}
                    className="px-2 py-1 rounded bg-cyan-800 text-xs font-mono text-cyan-100 disabled:opacity-40"
                  >
                    {saving ? '…' : 'SAVE'}
                  </button>
                  <button onClick={() => setEditingReadiness(false)} className="px-2 py-1 rounded border border-gray-700 text-xs font-mono text-gray-500">✕</button>
                </div>
              ) : (
                <button
                  onClick={() => setEditingReadiness(true)}
                  className={`px-2 py-0.5 rounded border text-xs font-mono hover:opacity-80 transition-opacity ${rc.investment_readiness ? (READINESS_COLORS[rc.investment_readiness] ?? 'text-gray-400 border-gray-700') : 'text-gray-600 border-gray-800'}`}
                >
                  {rc.investment_readiness ? rc.investment_readiness.replace(/_/g, ' ') : 'no readiness'} ✎
                </button>
              )}
            </div>
          </div>

          {/* Workflow strip */}
          <div className="mt-4 flex items-center gap-0 flex-wrap">
            {WORKFLOW_STEPS.map((step, i) => {
              const isCurrent = rc.status === step.key;
              const statusIndex = WORKFLOW_STEPS.findIndex(s => s.key === rc.status);
              const isPast = i < statusIndex;
              return (
                <div key={step.key} className="flex items-center">
                  <span className={`text-xs font-mono px-2 py-0.5 rounded ${
                    isCurrent
                      ? 'bg-cyan-900/60 text-cyan-300 border border-cyan-700'
                      : isPast
                      ? 'text-gray-600'
                      : 'text-gray-800'
                  }`}>
                    {step.label}
                  </span>
                  {i < WORKFLOW_STEPS.length - 1 && (
                    <span className={`text-xs mx-1 ${isPast || isCurrent ? 'text-gray-600' : 'text-gray-800'}`}>›</span>
                  )}
                </div>
              );
            })}
          </div>
        </div>

        <DocumentationGuidePanel guide={documentationGuide} error={documentationGuideError} />

        <CaseCompletionWorkbench
          workbench={completionWorkbench}
          loading={completionWorkbenchLoading}
          error={completionWorkbenchError}
        />

        <OperationalViewCard
          operationalView={operationalView}
          loading={operationalViewLoading}
          error={operationalViewError}
          onRefresh={loadOperationalView}
        />

        <OfficialSourceFinderPanel
          finder={officialSourceFinder}
          loading={officialSourceFinderLoading}
          error={officialSourceFinderError}
          copiedKey={officialSourceCopiedKey}
          onCopy={copyOfficialSourceQuery}
        />

        <SecDocumentAcquisitionPanel
          packageData={secDocumentAcquisition}
          loading={secDocumentAcquisitionLoading}
          acquiring={secDocumentAcquiring}
          error={secDocumentAcquisitionError}
          copiedKey={officialSourceCopiedKey}
          onCopy={copyOfficialSourceQuery}
          onAcquire={handleSecDocumentAcquisition}
        />

        <DocumentPackagePanel
          packageData={documentPackage}
          loading={documentPackageLoading}
          error={documentPackageError}
        />

        <HistoricalAnaloguesPanel
          analogues={historicalAnalogues}
          loading={historicalAnaloguesLoading}
          error={historicalAnaloguesError}
        />

        <div className="grid gap-4 lg:grid-cols-2">
          {/* ── Intelligence Score ── */}
          <Section id="research-intelligence-score" title="Intelligence Score" hint="Read-only IA Score for preparation quality, safety, and usefulness. Manual review remains mandatory.">
            <IntelligenceScoreCard
              score={intelligenceScore}
              loading={scoreLoading}
              error={scoreError}
              onRefresh={loadIntelligenceScore}
            />
          </Section>

          {/* ── Evaluation Preparation ── */}
          <Section id="research-evaluation-preparation" title="Evaluation Preparation" hint="Read-only readiness package for manual evaluation planning. No AI, no recommendation, no publishing.">
            <EvaluationPrepPanel
              prep={evaluationPrep}
              loading={prepLoading}
              error={prepError}
              onRefresh={loadEvaluationPrep}
            />
          </Section>
        </div>

        {/* ── Evidence Links / Traceability ── */}
        <Section id="research-evidence-links" title="Evidence Links / Research Traceability" hint="Metadata-only source links used to trace where case information came from.">
          {evidenceLinksError && (
            <p className="mb-3 text-xs font-mono text-amber-300">{evidenceLinksError}</p>
          )}
          <EvidenceLinksPanel
            title="ResearchCase evidence links"
            links={evidenceLinks?.links ?? []}
            guardrails={evidenceLinks?.guardrails ?? []}
            emptyText="No stored traceability links are available for this ResearchCase yet."
          />
        </Section>

        <div className="grid gap-4 lg:grid-cols-2">
          <QuickSourceLinks rc={rc} evidenceLinks={evidenceLinks} />
          <CaseActivityTimeline
            title="Research Timeline / Case Activity Log"
            events={activityTimeline?.events ?? []}
            error={activityTimelineError}
          />
        </div>

        {/* ── Research Brief ── */}
        <Section title="Research Brief" hint="Structured 14-section research note. Manual editor below; AI preview via button.">
          <BriefEditor
            brief={rc.brief}
            onSave={draft => saveField({ brief: draft }, 'Brief saved')}
          />
          <AiPreviewPanel
            caseId={rc.id}
            currentBrief={rc.brief}
            onApply={async (sections) => {
              const merged = { ...(rc.brief ?? {}), ...sections };
              await saveField({ brief: merged }, 'AI sections applied');
            }}
          />
          <QualityAssistPanel
            caseId={rc.id}
            onApplyStatus={async (status) => {
              await saveField({ status }, `Status updated to "${status}"`);
            }}
            onApplyReadiness={async (readiness) => {
              await saveField({ investment_readiness: readiness }, `Readiness updated to "${readiness}"`);
            }}
          />
          <PublicDraftPanel caseId={rc.id} />
        </Section>

        {/* ── Notes ── */}
        <Section title="Notes">
          {editingNotes ? (
            <div className="space-y-2">
              <textarea
                value={notesText}
                onChange={e => setNotesText(e.target.value)}
                rows={4}
                className="w-full bg-gray-900 border border-gray-700 rounded px-3 py-2 text-sm text-gray-200 font-mono"
                placeholder="Add research notes…"
              />
              <div className="flex gap-2">
                <button
                  onClick={() => saveField({ notes: notesText }, 'Notes saved')}
                  disabled={saving}
                  className="px-3 py-1 rounded bg-cyan-800 text-xs font-mono text-cyan-100 disabled:opacity-40"
                >
                  {saving ? 'SAVING…' : 'SAVE NOTES'}
                </button>
                <button onClick={() => { setEditingNotes(false); setNotesText(rc.notes ?? ''); }} className="px-3 py-1 rounded border border-gray-700 text-xs font-mono text-gray-500">CANCEL</button>
              </div>
            </div>
          ) : (
            <div>
              {rc.notes
                ? <p className="text-sm text-gray-300 whitespace-pre-wrap">{rc.notes}</p>
                : <p className="text-xs font-mono text-gray-600 italic">No notes yet.</p>
              }
              <button onClick={() => setEditingNotes(true)} className="mt-2 text-xs font-mono text-cyan-700 hover:text-cyan-400 transition-colors">✎ EDIT NOTES</button>
            </div>
          )}
        </Section>

        {/* ── Tasks / Missing Info ── */}
        <Section id="research-tasks" title={`Tasks / Missing Info (${rc.tasks.length})`} hint="Track what still needs to be verified.">
          {rc.tasks.length === 0 && !showAddTask && (
            <p className="text-xs font-mono text-gray-600 italic mb-3">No tasks yet. Add items you still need to verify.</p>
          )}
          {rc.tasks.length > 0 && (
            <div className="space-y-2 mb-3">
              {rc.tasks
                .slice()
                .sort((a, b) => a.priority - b.priority)
                .map((t: ResearchTask) => (
                  <div key={t.id} className="flex items-start gap-3 py-2 border-b border-gray-800 last:border-0">
                    <select
                      value={t.status}
                      onChange={e => handleUpdateTaskStatus(t.id, e.target.value)}
                      className={`bg-transparent border-0 text-xs font-mono flex-shrink-0 mt-0.5 cursor-pointer ${TASK_STATUS_COLORS[t.status] ?? 'text-gray-400'}`}
                    >
                      {TASK_STATUSES.map(s => <option key={s} value={s}>{s.toUpperCase()}</option>)}
                    </select>
                    <div className="flex-1 min-w-0">
                      <p className={`text-sm ${t.status === 'done' || t.status === 'cancelled' ? 'text-gray-600 line-through' : 'text-gray-300'}`}>{t.description}</p>
                      {t.notes && <p className="text-xs text-gray-500 mt-0.5">{t.notes}</p>}
                    </div>
                    <span className="text-xs font-mono text-gray-700 flex-shrink-0">P{t.priority}</span>
                  </div>
                ))}
            </div>
          )}
          {showAddTask ? (
            <div className="space-y-2 pt-2 border-t border-gray-800">
              <input
                value={newTaskDesc}
                onChange={e => setNewTaskDesc(e.target.value)}
                placeholder="What needs to be verified…"
                className="w-full bg-gray-900 border border-gray-700 rounded px-3 py-2 text-sm text-gray-200 font-mono"
              />
              <div className="flex items-center gap-2">
                <label className="text-xs font-mono text-gray-500">PRIORITY:</label>
                <select
                  value={newTaskPriority}
                  onChange={e => setNewTaskPriority(e.target.value)}
                  className="bg-gray-900 border border-gray-700 rounded px-2 py-1 text-xs font-mono text-gray-300"
                >
                  {[1, 2, 3, 4, 5].map(n => <option key={n} value={n}>{n} — {n === 1 ? 'urgent' : n === 5 ? 'low' : ''}</option>)}
                </select>
              </div>
              {taskError && <p className="text-xs text-red-400 font-mono">{taskError}</p>}
              <div className="flex gap-2">
                <button
                  onClick={handleAddTask}
                  disabled={addingTask || !newTaskDesc.trim()}
                  className="px-3 py-1 rounded bg-cyan-800 hover:bg-cyan-700 disabled:opacity-40 text-xs font-mono text-cyan-100 transition-colors"
                >
                  {addingTask ? 'ADDING…' : 'ADD TASK'}
                </button>
                <button
                  onClick={() => { setShowAddTask(false); setTaskError(null); setNewTaskDesc(''); }}
                  className="px-3 py-1 rounded border border-gray-700 text-xs font-mono text-gray-500"
                >
                  CANCEL
                </button>
              </div>
            </div>
          ) : (
            <button
              onClick={() => setShowAddTask(true)}
              className="text-xs font-mono text-cyan-700 hover:text-cyan-400 transition-colors"
            >
              + ADD TASK
            </button>
          )}
        </Section>

        {/* ── Key Documents ── */}
        <Section id="research-documents" title={`Key Documents (${rc.documents.length})`} hint="Paste document URLs as metadata references. No content is fetched. Use the snippet field to paste relevant excerpts for AI analysis.">
          {rc.documents.length === 0 && !showAddDoc && (
            <p className="text-xs font-mono text-gray-600 italic mb-3">No documents added. Record URLs to SEC filings, press releases, or news articles. URLs are metadata only — no content is fetched.</p>
          )}
          {rc.documents.length > 0 && (
            <div className="space-y-4 mb-3">
              {rc.documents.map((d: ResearchDocument) => (
                <DocumentCard
                  key={d.id}
                  doc={d}
                  caseId={rc.id}
                  onUpdated={load}
                  onActionMsg={showAction}
                />
              ))}
            </div>
          )}
          {showAddDoc ? (
            <div className="space-y-2 pt-2 border-t border-gray-800">
              <input
                value={newDocUrl}
                onChange={e => setNewDocUrl(e.target.value)}
                placeholder="URL (required) — metadata only, not fetched…"
                className="w-full bg-gray-900 border border-gray-700 rounded px-3 py-2 text-sm text-gray-200 font-mono"
              />
              <input
                value={newDocTitle}
                onChange={e => setNewDocTitle(e.target.value)}
                placeholder="Title (optional)…"
                className="w-full bg-gray-900 border border-gray-700 rounded px-3 py-2 text-sm text-gray-200 font-mono"
              />
              <select
                value={newDocType}
                onChange={e => setNewDocType(e.target.value)}
                className="bg-gray-900 border border-gray-700 rounded px-2 py-1 text-xs font-mono text-gray-300"
              >
                <option value="">— type —</option>
                {['sec_filing', 'press_release', 'ir_page', 'presentation', 'news', 'other'].map(t => (
                  <option key={t} value={t}>{t}</option>
                ))}
              </select>
              {docError && <p className="text-xs text-red-400 font-mono">{docError}</p>}
              <div className="flex gap-2">
                <button
                  onClick={handleAddDoc}
                  disabled={addingDoc || !newDocUrl.trim()}
                  className="px-3 py-1 rounded bg-cyan-800 hover:bg-cyan-700 disabled:opacity-40 text-xs font-mono text-cyan-100 transition-colors"
                >
                  {addingDoc ? 'ADDING…' : 'ADD DOCUMENT'}
                </button>
                <button
                  onClick={() => { setShowAddDoc(false); setDocError(null); setNewDocUrl(''); setNewDocTitle(''); setNewDocType(''); }}
                  className="px-3 py-1 rounded border border-gray-700 text-xs font-mono text-gray-500"
                >
                  CANCEL
                </button>
              </div>
            </div>
          ) : (
            <button
              onClick={() => setShowAddDoc(true)}
              className="text-xs font-mono text-cyan-700 hover:text-cyan-400 transition-colors"
            >
              + ADD DOCUMENT
            </button>
          )}
        </Section>

        {/* ── Useful Sources ── */}
        <Section id="research-sources" title={`Useful Sources (${rc.sources.length})`} hint="Record sources that produced useful signal. Signal quality and usefulness notes are editable per source. Source URLs are metadata only — SwissEdge does not crawl or read linked URLs.">
          <p className="text-xs font-mono text-gray-700 mb-3">
            Source URLs are metadata only. SwissEdge does not crawl or read linked URLs.
          </p>
          {rc.sources.length === 0 && !showAddSource && (
            <p className="text-xs font-mono text-gray-600 italic mb-3">No sources recorded. Add sources that surfaced signal for this case. No URLs are fetched.</p>
          )}
          {rc.sources.length > 0 && (
            <div className="space-y-3 mb-3">
              {rc.sources.map((s: ResearchSource) => (
                <SourceCard
                  key={s.id}
                  source={s}
                  caseId={rc.id}
                  onUpdated={load}
                  onActionMsg={showAction}
                />
              ))}
            </div>
          )}
          {showAddSource ? (
            <div className="space-y-2 pt-2 border-t border-gray-800">
              <input
                value={newSrcName}
                onChange={e => setNewSrcName(e.target.value)}
                placeholder="Source name (required)…"
                className="w-full bg-gray-900 border border-gray-700 rounded px-3 py-2 text-sm text-gray-200 font-mono"
              />
              <input
                value={newSrcUrl}
                onChange={e => setNewSrcUrl(e.target.value)}
                placeholder="URL (optional, metadata only)…"
                className="w-full bg-gray-900 border border-gray-700 rounded px-3 py-2 text-sm text-gray-200 font-mono"
              />
              <div className="flex items-center gap-2">
                <label className="text-xs font-mono text-gray-500">SIGNAL QUALITY:</label>
                <select
                  value={newSrcQuality}
                  onChange={e => setNewSrcQuality(e.target.value)}
                  className="bg-gray-900 border border-gray-700 rounded px-2 py-1 text-xs font-mono text-gray-300"
                >
                  {SIGNAL_QUALITY_VALUES.map(q => <option key={q} value={q}>{q}</option>)}
                </select>
              </div>
              {sourceError && <p className="text-xs text-red-400 font-mono">{sourceError}</p>}
              <div className="flex gap-2">
                <button
                  onClick={handleAddSource}
                  disabled={addingSource || !newSrcName.trim()}
                  className="px-3 py-1 rounded bg-cyan-800 hover:bg-cyan-700 disabled:opacity-40 text-xs font-mono text-cyan-100 transition-colors"
                >
                  {addingSource ? 'ADDING…' : 'ADD SOURCE'}
                </button>
                <button
                  onClick={() => { setShowAddSource(false); setSourceError(null); setNewSrcName(''); setNewSrcUrl(''); setNewSrcQuality('medium'); }}
                  className="px-3 py-1 rounded border border-gray-700 text-xs font-mono text-gray-500"
                >
                  CANCEL
                </button>
              </div>
            </div>
          ) : (
            <button
              onClick={() => setShowAddSource(true)}
              className="text-xs font-mono text-cyan-700 hover:text-cyan-400 transition-colors"
            >
              + ADD SOURCE
            </button>
          )}
          <SourceIntelligencePanel caseId={rc.id} />
        </Section>

        {/* ── V2 Research Metadata ── */}
        <Section id="research-metadata" title="V2 Research Metadata" hint="Source-driven intake metadata. Read-only — populated by V2 intake agents when available.">
          <V2MetadataPanel rc={rc} />
          <p className="text-xs font-mono text-gray-700 mt-3">
            Read-only · no edits · no AI · no URL fetching · populated by future V2 intake path
          </p>
        </Section>

        {/* ── Disclaimer / Guardrails ── */}
        <div className="glass-panel rounded p-3 mb-4 border-amber-500/20">
          <p className="text-xs font-mono text-amber-400/70 text-center">{rc.disclaimer}</p>
          <p className="text-xs font-mono text-gray-700 text-center mt-1">PRIVATE RESEARCH DESK — NO PUBLISHING WITHOUT MANUAL APPROVAL</p>
        </div>

      </div>
    </div>
  );
}
