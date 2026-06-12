'use client';

import { useEffect, useState } from 'react';
import { fetchStudyGuideMap, type DocumentationAgentReport, type Situation } from '@/lib/api';
import {
  normalizeStudyGuideSituationType,
  studyGuideMapping,
  type StudyGuideSituationMapping,
  type StudyGuideChapterReference,
  type StudyGuideGap,
} from '@/app/components/studyGuideMapping';

function typeCandidates(situation: Situation, report: DocumentationAgentReport | null): unknown[] {
  return [
    situation.situation_type,
    situation.evaluation?.sec_detection?.situation_type,
    report?.case_type,
    situation.filing_type,
    situation.evaluation?.sec_detection?.detected_form_type,
  ];
}

function mappingFor(
  situation: Situation,
  report: DocumentationAgentReport | null,
  liveMap: Record<string, StudyGuideSituationMapping> | null,
) {
  const source = liveMap ?? studyGuideMapping;
  for (const candidate of typeCandidates(situation, report)) {
    const normalized = normalizeStudyGuideSituationType(candidate);
    if (normalized && source[normalized]) {
      return {
        normalizedType: normalized,
        mapping: source[normalized],
      };
    }
  }
  return {
    normalizedType: null,
    mapping: null,
  };
}

function chapterLabel(chapter: StudyGuideChapterReference): string {
  return `Ch ${chapter.chapter_number} — ${chapter.chapter_title}`;
}

function hasMappedContent(mapping: NonNullable<ReturnType<typeof mappingFor>['mapping']>): boolean {
  return mapping.core.length > 0 || mapping.supporting.length > 0 || mapping.gaps.length > 0;
}

function ChapterReferenceCard({
  chapter,
  priority,
}: {
  chapter: StudyGuideChapterReference;
  priority: 'Core' | 'Supporting';
}) {
  return (
    <details style={{ border: '1px solid var(--border-default)', borderRadius: 8, padding: 12 }}>
      <summary
        style={{
          cursor: 'pointer',
          display: 'flex',
          justifyContent: 'space-between',
          gap: 10,
          alignItems: 'center',
          listStyle: 'none',
        }}
      >
        <span>
          <span style={{ display: 'block', fontSize: 13, fontWeight: 700, color: 'var(--text-primary)' }}>
            {chapterLabel(chapter)}
          </span>
          <span style={{ display: 'block', marginTop: 3, fontSize: 12, color: 'var(--text-muted)' }}>
            {chapter.concept_label}
          </span>
        </span>
        <span className="status-badge status-badge--readonly">{priority}</span>
      </summary>

      <div style={{ display: 'grid', gap: 10, marginTop: 12 }}>
        <div>
          <div style={{ fontFamily: 'var(--font-mono)', fontSize: 10, textTransform: 'uppercase', color: 'var(--text-faint)', marginBottom: 4 }}>
            Why it matters
          </div>
          <div style={{ fontSize: 12, color: 'var(--text-muted)', lineHeight: 1.5 }}>
            {chapter.description}
          </div>
        </div>

        <div>
          <div style={{ fontFamily: 'var(--font-mono)', fontSize: 10, textTransform: 'uppercase', color: 'var(--text-faint)', marginBottom: 4 }}>
            Exact course reference
          </div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
            <span className="status-badge status-badge--readonly">{chapterLabel(chapter)}</span>
            {chapter.file_path ? (
              <span className="status-badge status-badge--readonly">Source: {chapter.file_path}</span>
            ) : (
              <span className="status-badge status-badge--readonly">Source file not mapped yet</span>
            )}
          </div>
        </div>
      </div>
    </details>
  );
}

function GapCard({ gap }: { gap: StudyGuideGap }) {
  return (
    <div style={{ border: '1px solid var(--border-default)', borderRadius: 8, padding: 12, display: 'grid', gap: 8 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', gap: 10, alignItems: 'flex-start' }}>
        <div>
          <div style={{ fontSize: 13, fontWeight: 700, color: 'var(--text-primary)' }}>{gap.concept_label}</div>
          <div style={{ marginTop: 4, fontSize: 12, color: 'var(--text-muted)', lineHeight: 1.5 }}>{gap.description}</div>
        </div>
        <span className="status-badge status-badge--readonly">Flag: Not covered in course</span>
      </div>

      {gap.closest_chapters.length > 0 && (
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
          {gap.closest_chapters.map(chapter => (
            <span key={`${gap.concept_label}-${chapter}`} className="status-badge status-badge--readonly">
              Closest Ch {chapter}
            </span>
          ))}
        </div>
      )}

      <div style={{ fontSize: 12, color: 'var(--text-muted)', lineHeight: 1.5 }}>
        <strong style={{ color: 'var(--text-primary)' }}>Annotation note: </strong>
        {gap.annotation_note}
      </div>
    </div>
  );
}

function ChapterSection({
  title,
  priority,
  chapters,
}: {
  title: string;
  priority: 'Core' | 'Supporting';
  chapters: StudyGuideChapterReference[];
}) {
  if (chapters.length === 0) return null;
  return (
    <div>
      <div className="section-title" style={{ marginBottom: 8 }}>{title}</div>
      <div style={{ display: 'grid', gap: 10 }}>
        {chapters.map(chapter => (
          <ChapterReferenceCard
            key={`${priority}-${chapter.chapter_number}-${chapter.concept_label}`}
            chapter={chapter}
            priority={priority}
          />
        ))}
      </div>
    </div>
  );
}

export function EducationStudyGuidePanel({
  situation,
  report,
}: {
  situation: Situation;
  report: DocumentationAgentReport | null;
}) {
  const [liveMap, setLiveMap] = useState<Record<string, StudyGuideSituationMapping> | null>(null);
  const [mapError, setMapError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    fetchStudyGuideMap()
      .then(payload => {
        if (!cancelled) setLiveMap(payload.situation_types ?? null);
      })
      .catch(() => {
        // Safe fallback: keep the empty local placeholder -> pending state.
        if (!cancelled) setMapError('Course mapping unavailable; showing pending state.');
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const { normalizedType, mapping } = mappingFor(situation, report, liveMap);
  const showPending = !mapping || !hasMappedContent(mapping);
  const studyFirst = mapping ? [...mapping.core, ...mapping.supporting].slice(0, 3) : [];

  return (
    <section className="card" style={{ padding: 16, display: 'grid', gap: 12 }}>
      <div className="card-header" style={{ alignItems: 'flex-start', gap: 12 }}>
        <div>
          <div className="card-title">Study Guide</div>
          <div className="card-desc">Situation-type-driven course references for manual case review.</div>
        </div>
        <span className="status-badge status-badge--readonly">educational</span>
      </div>

      {showPending ? (
        <div style={{ border: '1px solid var(--border-default)', borderRadius: 8, padding: 12, background: 'var(--bg-subtle)' }}>
          <div style={{ fontSize: 13, fontWeight: 700, color: 'var(--text-primary)' }}>
            Study Guide mapping pending for this situation type.
          </div>
          <div style={{ marginTop: 4, fontSize: 12, color: 'var(--text-muted)', lineHeight: 1.5 }}>
            {normalizedType
              ? `No course chapters are mapped for ${normalizedType} in the processed course index.`
              : 'No supported situation-type mapping was found for this record.'}
            {mapError ? ` ${mapError}` : ''}
          </div>
        </div>
      ) : (
        <>
          <div>
            <div className="section-title" style={{ marginBottom: 6 }}>What to study first</div>
            <ol style={{ margin: 0, paddingLeft: 18, display: 'grid', gap: 4 }}>
              {studyFirst.map(chapter => (
                <li key={`first-${chapter.chapter_number}-${chapter.concept_label}`} style={{ fontSize: 12, color: 'var(--text-muted)' }}>
                  {chapterLabel(chapter)}
                </li>
              ))}
            </ol>
          </div>

          <ChapterSection title="Core chapters" priority="Core" chapters={mapping.core} />
          <ChapterSection title="Supporting chapters" priority="Supporting" chapters={mapping.supporting} />

          {mapping.gaps.length > 0 && (
            <div>
              <div className="section-title" style={{ marginBottom: 8 }}>Gaps</div>
              <div style={{ display: 'grid', gap: 10 }}>
                {mapping.gaps.map(gap => (
                  <GapCard key={gap.concept_label} gap={gap} />
                ))}
              </div>
            </div>
          )}
        </>
      )}

      <div style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-faint)', lineHeight: 1.5 }}>
        Chapter labels are not links yet. Gaps are not course coverage. This study guide is educational and not evidence, verification, or investment advice.
      </div>
    </section>
  );
}
