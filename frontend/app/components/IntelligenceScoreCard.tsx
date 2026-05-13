'use client';

import type { IntelligenceScorePackage } from '@/lib/api';

function gradeClass(grade: IntelligenceScorePackage['grade']): string {
  if (grade === 'APPROVABLE') return 'text-cyan-300 border-cyan-900 bg-cyan-950/20';
  if (grade === 'USEFUL_INCOMPLETE') return 'text-amber-300 border-amber-900 bg-amber-950/20';
  return 'text-red-300 border-red-900 bg-red-950/20';
}

function label(value: string): string {
  return value.replace(/_/g, ' ').toUpperCase();
}

function componentByKey(score: IntelligenceScorePackage, key: IntelligenceScorePackage['components'][number]['key']) {
  return score.components.find(component => component.key === key);
}

export function IntelligenceScoreCard({
  score,
  loading,
  error,
  onRefresh,
}: {
  score: IntelligenceScorePackage | null;
  loading: boolean;
  error: string | null;
  onRefresh: () => Promise<void>;
}) {
  if (loading) {
    return <p className="text-xs font-mono text-gray-600">Loading intelligence score...</p>;
  }

  if (error) {
    return (
      <div className="space-y-2">
        <p className="text-xs font-mono text-red-400">Intelligence score unavailable: {error}</p>
        <button onClick={onRefresh} className="text-xs font-mono text-cyan-700 hover:text-cyan-400">
          REFRESH SCORE
        </button>
      </div>
    );
  }

  if (!score) {
    return <p className="text-xs font-mono text-gray-600 italic">No intelligence score loaded.</p>;
  }

  const detection = componentByKey(score, 'detection');
  const structuring = componentByKey(score, 'structuring');
  const riskDiscipline = componentByKey(score, 'risk_discipline');

  return (
    <div className="space-y-4">
      <div className="rounded border border-amber-900/60 bg-amber-950/10 p-3">
        <p className="text-xs font-mono text-amber-300">
          IA Score is preparation quality only. APPROVABLE means structurally approvable for manual review, not investment approval.
        </p>
      </div>

      <div className="flex flex-wrap items-center gap-3">
        <div>
          <p className="text-xs font-mono text-gray-600">IA SCORE</p>
          <p className="text-3xl font-mono text-cyan-300">{score.total_score}<span className="text-base text-gray-600">/100</span></p>
        </div>
        <span className={`rounded border px-2 py-0.5 text-xs font-mono ${gradeClass(score.grade)}`}>
          {label(score.grade)}
        </span>
        <button onClick={onRefresh} className="ml-auto text-xs font-mono text-cyan-700 hover:text-cyan-400">
          REFRESH SCORE
        </button>
        <button
          type="button"
          onClick={() => document.querySelector('#case-completion-workbench')?.scrollIntoView({ behavior: 'smooth', block: 'start' })}
          className="text-xs font-mono text-cyan-700 hover:text-cyan-400"
        >
          OPEN COMPLETION PLAN
        </button>
      </div>

      <p className="text-xs text-gray-500">{score.grade_explanation}</p>

      <div className="grid gap-3 md:grid-cols-3">
        {score.components.map(component => (
          <div key={component.key} className="rounded border border-gray-800 p-3">
            <div className="mb-2 flex items-center justify-between gap-2">
              <p className="text-xs font-mono text-gray-500">{component.label.toUpperCase()}</p>
              <p className="text-xs font-mono text-gray-300">{component.score}/{component.max_score}</p>
            </div>
            <div className="h-1.5 overflow-hidden rounded bg-gray-900">
              <div
                className="h-full bg-cyan-700"
                style={{ width: `${Math.round((component.score / component.max_score) * 100)}%` }}
              />
            </div>
            {component.gaps.length > 0 && (
              <ul className="mt-2 space-y-1">
                {component.gaps.slice(0, 2).map(gap => (
                  <li key={gap} className="text-[11px] text-amber-300">- {gap}</li>
                ))}
              </ul>
            )}
          </div>
        ))}
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <div>
          <p className="mb-2 text-xs font-mono uppercase tracking-wide text-gray-600">Preparation Snapshot</p>
          <div className="space-y-1 text-xs text-gray-400">
            <p>Evaluation prep: {score.evaluation_prep_summary.level} ({score.evaluation_prep_summary.score}/100)</p>
            <p>Missing resources: {score.evaluation_prep_summary.required_resources_missing}/{score.evaluation_prep_summary.required_resources_total}</p>
            <p>Checklist gaps: {score.evaluation_prep_summary.checklist_missing}/{score.evaluation_prep_summary.checklist_total}</p>
            <p>Evidence links: {score.evidence_links_summary.total_links}</p>
          </div>
        </div>
        <div>
          <p className="mb-2 text-xs font-mono uppercase tracking-wide text-gray-600">Next Manual Actions</p>
          {score.suggested_next_actions.length > 0 ? (
            <ul className="space-y-1">
              {score.suggested_next_actions.slice(0, 4).map(action => (
                <li key={action} className="text-xs text-gray-300">- {action}</li>
              ))}
            </ul>
          ) : (
            <p className="text-xs text-gray-600">No score-specific actions.</p>
          )}
        </div>
      </div>

      <div className="rounded border border-gray-800 bg-gray-950/40 p-3">
        <p className="mb-2 text-xs font-mono uppercase tracking-wide text-gray-600">How to improve this score</p>
        <p className="text-xs leading-5 text-gray-500">
          The score measures preparation quality, documentation quality, and manual review readiness. It does not measure investment attractiveness.
        </p>
        <div className="mt-3 grid gap-3 md:grid-cols-3">
          <div>
            <p className="text-xs font-mono text-cyan-300">Detection ({detection?.score ?? 0}/{detection?.max_score ?? 40})</p>
            <ul className="mt-2 space-y-1 text-xs text-gray-400">
              <li>- Add or confirm the SEC source link.</li>
              <li>- Make filing type, company, date, CIK, and accession clear.</li>
              <li>- Link the case back to its SpecialSituation when available.</li>
              <li>- Keep source traceability visible.</li>
            </ul>
          </div>
          <div>
            <p className="text-xs font-mono text-cyan-300">Structuring ({structuring?.score ?? 0}/{structuring?.max_score ?? 40})</p>
            <ul className="mt-2 space-y-1 text-xs text-gray-400">
              <li>- Map required resources and reduce missing resources.</li>
              <li>- After manual review, mark useful candidates as evidence_found.</li>
              <li>- Link each source to a required resource or checklist item.</li>
              <li>- Add missing offer documents, press releases, or letters of transmittal.</li>
              <li>- Reject noisy source candidates.</li>
            </ul>
          </div>
          <div>
            <p className="text-xs font-mono text-cyan-300">Risk discipline ({riskDiscipline?.score ?? 0}/{riskDiscipline?.max_score ?? 20})</p>
            <ul className="mt-2 space-y-1 text-xs text-gray-400">
              <li>- Keep human review flags visible where needed.</li>
              <li>- Avoid unsafe assumptions.</li>
              <li>- Do not treat evidence_found as verified evidence.</li>
              <li>- Keep manual review mandatory before promotion or publishing.</li>
            </ul>
          </div>
        </div>
      </div>

      {score.warnings.length > 0 && (
        <div>
          <p className="mb-2 text-xs font-mono uppercase tracking-wide text-gray-600">Score Gaps</p>
          <div className="flex flex-wrap gap-2">
            {score.warnings.slice(0, 8).map(warning => (
              <span key={warning} className="rounded border border-gray-800 px-2 py-0.5 text-[10px] font-mono text-amber-300">
                {warning}
              </span>
            ))}
          </div>
        </div>
      )}

      <div className="border-t border-gray-800 pt-3">
        <div className="flex flex-wrap gap-2">
          {score.guardrails.map(guardrail => (
            <span key={guardrail} className="rounded border border-gray-800 px-2 py-0.5 text-[10px] font-mono text-gray-500">
              {guardrail}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
}
