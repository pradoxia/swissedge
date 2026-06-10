export interface StudyGuideChapterReference {
  chapter_number: number;
  chapter_title: string;
  concept_label: string;
  description: string;
  file_path: string | null;
}

export interface StudyGuideGap {
  concept_label: string;
  description: string;
  closest_chapters: number[];
  annotation_note: string;
}

export interface StudyGuideSituationMapping {
  core: StudyGuideChapterReference[];
  supporting: StudyGuideChapterReference[];
  gaps: StudyGuideGap[];
}

const KNOWN_SITUATION_TYPES = new Set([
  'merger',
  'merger_arbitrage',
  'tender_offer',
  'self_tender',
  'proxy_fight',
  'activism',
  'spin_off',
  'rights_offering',
  'liquidation',
  'bankruptcy',
  'other',
]);

export const studyGuideMapping: Record<string, StudyGuideSituationMapping> = Object.fromEntries(
  [...KNOWN_SITUATION_TYPES].map(key => [key, { core: [], supporting: [], gaps: [] }]),
);

export function normalizeStudyGuideSituationType(value: unknown): string | null {
  if (typeof value !== 'string') return null;
  const normalized = value.trim().toLowerCase().replace(/[^a-z0-9]+/g, '_').replace(/^_+|_+$/g, '');
  if (!normalized) return null;
  return KNOWN_SITUATION_TYPES.has(normalized) ? normalized : null;
}
