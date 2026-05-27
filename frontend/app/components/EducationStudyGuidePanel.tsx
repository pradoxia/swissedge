'use client';

import { KnowledgeInfoButton } from '@/app/components/KnowledgeInfoButton';
import type { DocumentationAgentReport, Situation } from '@/lib/api';

type Chapter = {
  title: string;
  why: string;
  priority: 'Core' | 'Supporting' | 'Review';
  relatedDocuments: string[];
  studyQuestions: string[];
  concepts: Concept[];
};

type Concept = {
  label: string;
  knowledgeKey: string | null;
};

const TENDER_CHAPTERS: Chapter[] = [
  {
    title: 'Issuer Tender Offers',
    priority: 'Core',
    why: 'This case is an issuer self-tender. This chapter explains offer mechanics, price/range, expiration, proration, withdrawal rights, participation mechanics, and required tender documents.',
    relatedDocuments: ['SC TO-I', 'Offer to Purchase', 'Letter of Transmittal', 'Amendments'],
    studyQuestions: [
      'What is the issuer offering to buy?',
      'Is the price fixed or a range?',
      'When does the offer expire?',
      'What happens if the offer is oversubscribed?',
      'Are withdrawal rights clear?',
      'What documents define participation?',
    ],
    concepts: [
      { label: 'Offer to Purchase', knowledgeKey: 'offer_to_purchase' },
      { label: 'Letter of Transmittal', knowledgeKey: 'letter_of_transmittal' },
      { label: 'Proration', knowledgeKey: 'proration' },
      { label: 'Withdrawal Rights', knowledgeKey: 'withdrawal_rights' },
    ],
  },
  {
    title: 'Capital Return Events',
    priority: 'Supporting',
    why: 'Issuer tender offers often function as buybacks, liquidity events, or capital allocation events.',
    relatedDocuments: ['Press release', 'SC TO-I', 'Source of funds section'],
    studyQuestions: [
      'Why is the issuer launching the tender?',
      'Is it providing liquidity?',
      'How is the offer funded?',
      'What does it imply for remaining holders?',
    ],
    concepts: [
      { label: 'Source of Funds', knowledgeKey: 'source_of_funds' },
      { label: 'Offer Price', knowledgeKey: 'offer_price' },
      { label: 'Offer to Purchase', knowledgeKey: 'offer_to_purchase' },
    ],
  },
  {
    title: 'Risk / Downside Controls',
    priority: 'Review',
    why: 'This helps identify conditions, amendments, timing issues, and risks before relying on the case.',
    relatedDocuments: ['Offer to Purchase', 'Amendments', 'Conditions section'],
    studyQuestions: [
      'Can the issuer amend or terminate the offer?',
      'Are there broad conditions?',
      'Are amendments missing?',
      'Is timing clear?',
    ],
    concepts: [
      { label: 'Conditions of the Offer', knowledgeKey: 'conditions_of_offer' },
      { label: 'Amendments', knowledgeKey: 'amendments' },
      { label: 'Expiration Date', knowledgeKey: 'expiration_date' },
    ],
  },
];

const MERGER_TENDER_CHAPTERS: Chapter[] = [
  {
    title: 'Merger Arbitrage / Acquisition Tender Offers',
    priority: 'Core',
    why: 'This chapter explains third-party tender offer mechanics, offer consideration, timing, and the path from launch to closing.',
    relatedDocuments: ['SC TO-T', 'Offer to Purchase', 'Schedule 14D-9'],
    studyQuestions: [
      'Who is making the offer?',
      'What consideration is offered?',
      'When does the offer expire?',
      'What conditions must be satisfied before closing?',
    ],
    concepts: [
      { label: 'SC TO-T', knowledgeKey: null },
      { label: 'Offer to Purchase', knowledgeKey: 'offer_to_purchase' },
      { label: 'Offer Price', knowledgeKey: 'offer_price' },
      { label: 'Expiration Date', knowledgeKey: 'expiration_date' },
    ],
  },
  {
    title: 'Deal Document Review',
    priority: 'Supporting',
    why: 'This chapter helps connect tender documents to the target response, merger agreement, conditions, and closing mechanics.',
    relatedDocuments: ['Schedule 14D-9', 'Merger Agreement', 'Offer to Purchase'],
    studyQuestions: [
      'What does the target board recommend?',
      'Which deal documents define closing conditions?',
      'Are financing, regulatory, or minimum tender conditions clear?',
      'Do amendments change timing or economics?',
    ],
    concepts: [
      { label: 'Schedule 14D-9', knowledgeKey: null },
      { label: 'Merger Agreement', knowledgeKey: null },
      { label: 'Conditions', knowledgeKey: 'conditions_of_offer' },
      { label: 'Amendments', knowledgeKey: 'amendments' },
    ],
  },
  {
    title: 'Risk / Downside Controls',
    priority: 'Review',
    why: 'This helps Dani check closing conditions, regulatory risk, financing, termination rights, and timing risk before treating the case as usable.',
    relatedDocuments: ['Offer to Purchase', 'Schedule 14D-9', 'Merger Agreement', 'Amendments'],
    studyQuestions: [
      'What could stop the tender from closing?',
      'Are regulatory or financing conditions present?',
      'Can either side terminate or amend the offer?',
      'Is the current filing package complete enough for manual review?',
    ],
    concepts: [
      { label: 'Conditions', knowledgeKey: 'conditions_of_offer' },
      { label: 'Withdrawal Rights', knowledgeKey: 'withdrawal_rights' },
      { label: 'Amendments', knowledgeKey: 'amendments' },
    ],
  },
];

const TENDER_CONCEPTS: Concept[] = [
  { label: 'Offer to Purchase', knowledgeKey: 'offer_to_purchase' },
  { label: 'Letter of Transmittal', knowledgeKey: 'letter_of_transmittal' },
  { label: 'Proration', knowledgeKey: 'proration' },
  { label: 'Odd-lot priority', knowledgeKey: 'odd_lot_priority' },
  { label: 'Expiration Date', knowledgeKey: 'expiration_date' },
  { label: 'Withdrawal Rights', knowledgeKey: 'withdrawal_rights' },
  { label: 'Source of Funds', knowledgeKey: 'source_of_funds' },
  { label: 'Conditions of the Offer', knowledgeKey: 'conditions_of_offer' },
  { label: 'Amendments', knowledgeKey: 'amendments' },
];

const MERGER_TENDER_CONCEPTS: Concept[] = [
  { label: 'SC TO-T', knowledgeKey: null },
  { label: 'Offer to Purchase', knowledgeKey: 'offer_to_purchase' },
  { label: 'Schedule 14D-9', knowledgeKey: null },
  { label: 'Merger Agreement', knowledgeKey: null },
  { label: 'Offer Price', knowledgeKey: 'offer_price' },
  { label: 'Expiration Date', knowledgeKey: 'expiration_date' },
  { label: 'Conditions', knowledgeKey: 'conditions_of_offer' },
  { label: 'Withdrawal Rights', knowledgeKey: 'withdrawal_rights' },
  { label: 'Amendments', knowledgeKey: 'amendments' },
];

function normalizedType(situation: Situation, report: DocumentationAgentReport | null): string {
  return String(report?.case_type ?? situation.situation_type ?? situation.evaluation?.sec_detection?.situation_type ?? '').toLowerCase();
}

function chaptersFor(situation: Situation, report: DocumentationAgentReport | null): Chapter[] {
  const type = normalizedType(situation, report);
  const filing = String(situation.filing_type ?? situation.evaluation?.sec_detection?.detected_form_type ?? '').toUpperCase();
  if (type === 'tender_offer' || filing.includes('SC TO-I')) return TENDER_CHAPTERS;
  if (type === 'merger_arbitrage' || filing.includes('SC TO-T')) return MERGER_TENDER_CHAPTERS;
  return (report?.course_chapters ?? []).slice(0, 3).map((chapter, index) => ({
    title: chapter.title || 'Course reference not mapped yet.',
    why: chapter.reason || 'Course reference not mapped yet.',
    priority: index === 0 ? 'Core' : index === 1 ? 'Supporting' : 'Review',
    relatedDocuments: report?.documents_missing.slice(0, 3).map(item => item.label) ?? [],
    studyQuestions: ['What document supports this case point?', 'What still requires Dani review?'],
    concepts: [],
  }));
}

function conceptsFor(situation: Situation, report: DocumentationAgentReport | null): Concept[] {
  const type = normalizedType(situation, report);
  const filing = String(situation.filing_type ?? situation.evaluation?.sec_detection?.detected_form_type ?? '').toUpperCase();
  if (type === 'tender_offer' || filing.includes('SC TO-I')) return TENDER_CONCEPTS;
  if (type === 'merger_arbitrage' || filing.includes('SC TO-T')) return MERGER_TENDER_CONCEPTS;
  return (report?.required_information ?? []).slice(0, 8).map(item => ({
    label: String(item.label ?? item.info_key ?? 'Course concept'),
    knowledgeKey: typeof item.info_key === 'string' ? item.info_key : null,
  }));
}

function studyFirstFor(situation: Situation, report: DocumentationAgentReport | null): string[] {
  const type = normalizedType(situation, report);
  const filing = String(situation.filing_type ?? situation.evaluation?.sec_detection?.detected_form_type ?? '').toUpperCase();
  if (type === 'merger_arbitrage' || filing.includes('SC TO-T')) {
    return [
      'Acquisition Tender Offers',
      'Offer to Purchase',
      'Schedule 14D-9 / Deal Documents',
      'Conditions and closing risk',
    ];
  }
  return [
    'Issuer Tender Offers',
    'Offer to Purchase',
    'Proration / withdrawal rights / source of funds',
    'Conditions and amendments',
  ];
}

function ConceptChip({ concept }: { concept: Concept }) {
  return (
    <span
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: 5,
        padding: '5px 8px',
        border: '1px solid var(--border-default)',
        borderRadius: 6,
        fontSize: 12,
        color: 'var(--text-muted)',
        background: 'var(--bg-subtle)',
      }}
    >
      {concept.label}
      <KnowledgeInfoButton knowledgeKey={concept.knowledgeKey} label={concept.label} />
    </span>
  );
}

function StudyPriorityCard({ chapter }: { chapter: Chapter }) {
  return (
    <div style={{ border: '1px solid var(--border-default)', borderRadius: 8, padding: 12, display: 'grid', gap: 10 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', gap: 10, alignItems: 'flex-start' }}>
        <div>
          <div style={{ fontSize: 13, fontWeight: 700, color: 'var(--text-primary)' }}>{chapter.title}</div>
          <div style={{ marginTop: 2 }}>
            <span className="status-badge status-badge--readonly">Priority: {chapter.priority}</span>
          </div>
        </div>
      </div>

      <div>
        <div style={{ fontFamily: 'var(--font-mono)', fontSize: 10, textTransform: 'uppercase', color: 'var(--text-faint)', marginBottom: 4 }}>
          Why it matters
        </div>
        <div style={{ fontSize: 12, color: 'var(--text-muted)', lineHeight: 1.5 }}>{chapter.why}</div>
      </div>

      <div>
        <div style={{ fontFamily: 'var(--font-mono)', fontSize: 10, textTransform: 'uppercase', color: 'var(--text-faint)', marginBottom: 5 }}>
          Related documents
        </div>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
          {chapter.relatedDocuments.map(document => (
            <span key={document} className="status-badge status-badge--readonly">{document}</span>
          ))}
        </div>
      </div>

      <div>
        <div style={{ fontFamily: 'var(--font-mono)', fontSize: 10, textTransform: 'uppercase', color: 'var(--text-faint)', marginBottom: 5 }}>
          Study questions
        </div>
        <ul style={{ margin: 0, paddingLeft: 18, display: 'grid', gap: 3 }}>
          {chapter.studyQuestions.map(question => (
            <li key={question} style={{ fontSize: 12, color: 'var(--text-muted)', lineHeight: 1.4 }}>{question}</li>
          ))}
        </ul>
      </div>

      {chapter.concepts.length > 0 && (
        <div>
          <div style={{ fontFamily: 'var(--font-mono)', fontSize: 10, textTransform: 'uppercase', color: 'var(--text-faint)', marginBottom: 5 }}>
            Related concepts
          </div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
            {chapter.concepts.map(concept => (
              <ConceptChip key={`${chapter.title}-${concept.label}-${concept.knowledgeKey ?? 'none'}`} concept={concept} />
            ))}
          </div>
        </div>
      )}
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
  const chapters = chaptersFor(situation, report);
  const concepts = conceptsFor(situation, report);
  const studyFirst = studyFirstFor(situation, report);

  return (
    <section className="card" style={{ padding: 16, display: 'grid', gap: 12 }}>
      <div className="card-header" style={{ alignItems: 'flex-start', gap: 12 }}>
        <div>
          <div className="card-title">Education / Study Guide</div>
          <div className="card-desc">Course topics to study before manual case review.</div>
        </div>
        <span className="status-badge status-badge--readonly">educational</span>
      </div>

      <div>
        <div className="section-title" style={{ marginBottom: 6 }}>What to study first</div>
        <ol style={{ margin: 0, paddingLeft: 18, display: 'grid', gap: 4 }}>
          {studyFirst.map(item => (
            <li key={item} style={{ fontSize: 12, color: 'var(--text-muted)' }}>{item}</li>
          ))}
        </ol>
      </div>

      <div>
        <div className="section-title" style={{ marginBottom: 8 }}>Study priority</div>
        <div style={{ display: 'grid', gap: 10 }}>
          {chapters.length > 0 ? chapters.map(chapter => (
            <StudyPriorityCard key={chapter.title} chapter={chapter} />
          )) : (
            <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>Course reference not mapped yet.</div>
          )}
        </div>
      </div>

      <div>
        <div className="section-title" style={{ marginBottom: 6 }}>Key concepts to understand</div>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
          {concepts.map(concept => (
            <ConceptChip key={`${concept.label}-${concept.knowledgeKey ?? 'none'}`} concept={concept} />
          ))}
        </div>
      </div>

      <details>
        <summary style={{ cursor: 'pointer', fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--text-muted)' }}>
          Show study details
        </summary>
        <div style={{ display: 'grid', gap: 12, marginTop: 10 }}>
          <div>
            <div className="section-title" style={{ marginBottom: 6 }}>Manual study checklist</div>
            <ul style={{ margin: 0, paddingLeft: 18, display: 'grid', gap: 4 }}>
              <li style={{ fontSize: 12, color: 'var(--text-muted)' }}>Understand the filing type before relying on extracted terms.</li>
              <li style={{ fontSize: 12, color: 'var(--text-muted)' }}>Identify the source document for each key field.</li>
              <li style={{ fontSize: 12, color: 'var(--text-muted)' }}>Check amendments and conditions separately.</li>
            </ul>
          </div>
        </div>
      </details>

      <div style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-faint)', lineHeight: 1.5 }}>
        This study guide is educational. It is not evidence, verification, or investment advice.
      </div>
    </section>
  );
}
