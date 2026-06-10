'use client';

import { useState } from 'react';
import Link from 'next/link';
import styles from './home.module.css';

// ── Types ─────────────────────────────────────────────────────────────────

interface ModuleCard {
  name: string;
  status: string;
  description: string;
  href: string;
  icon: string;
}

type Tone =
  | 'active'
  | 'core'
  | 'manual'
  | 'readonly'
  | 'legacy'
  | 'paused'
  | 'advanced'
  | 'supporting'
  | 'preview';

function statusTone(status: string): Tone {
  switch (status) {
    case 'ACTIVE':     return 'active';
    case 'CORE':       return 'core';
    case 'MANUAL':     return 'manual';
    case 'READ-ONLY':  return 'readonly';
    case 'LEGACY':     return 'legacy';
    case 'PAUSED':     return 'paused';
    case 'ADVANCED':   return 'advanced';
    case 'SUPPORTING': return 'supporting';
    case 'PREVIEW':    return 'preview';
    case 'PARTIAL':    return 'advanced';
    default:           return 'supporting';
  }
}

// ── Collapsible section ───────────────────────────────────────────────────

function Collapsible({
  title,
  helper,
  count,
  defaultOpen = false,
  children,
}: {
  title: string;
  helper?: string;
  count?: number;
  defaultOpen?: boolean;
  children: React.ReactNode;
}) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <div className={styles.collapsible} data-open={open ? 'true' : 'false'}>
      <button
        type="button"
        className={styles.collapsibleHeader}
        onClick={() => setOpen((o) => !o)}
        aria-expanded={open}
      >
        <span className={styles.collapsibleTitle}>{title}</span>
        {helper && <span className={styles.collapsibleHelper}>{helper}</span>}
        {count !== undefined && <span className={styles.collapsibleCount}>{count}</span>}
        <svg
          className={styles.collapsibleChevron}
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2.5"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <polyline points="6 9 12 15 18 9" />
        </svg>
      </button>
      <div className={styles.collapsibleBody}>{children}</div>
    </div>
  );
}

// ── Section label (visible sections only) ────────────────────────────────

function SectionLabel({ label, count }: { label: string; count?: number }) {
  return (
    <div className={styles.sectionLabel}>
      <span className={styles.sectionLabelText}>{label}</span>
      <div className={styles.sectionLabelLine} />
      {count !== undefined && <span className={styles.sectionLabelCount}>{count}</span>}
    </div>
  );
}

// ── Module grid card ─────────────────────────────────────────────────────

function ModuleGrid({ modules }: { modules: ModuleCard[] }) {
  return (
    <div className={styles.moduleGrid}>
      {modules.map((module) => (
        <Link key={module.name} href={module.href} className={styles.moduleCard}>
          <div className={styles.moduleHeader}>
            <div style={{ display: 'flex', gap: 10, flex: 1, minWidth: 0 }}>
              <span className={styles.moduleIcon}>{module.icon}</span>
              <div className={styles.moduleTitleWrap}>
                <div className={styles.moduleTitle}>{module.name}</div>
                <div className={styles.moduleDesc}>{module.description}</div>
              </div>
            </div>
            <span className={styles.moduleBadge} data-tone={statusTone(module.status)}>
              {module.status}
            </span>
          </div>
        </Link>
      ))}
    </div>
  );
}

// ── Data ─────────────────────────────────────────────────────────────────

const workflowSteps = [
  { label: 'Detect',     href: '/investment/radar-status', helper: 'SEC EDGAR cron creates stored detection metadata' },
  { label: 'Triage',     href: '/investment/situations',   helper: 'SpecialSituation is a detected signal and triage object' },
  { label: 'Document',   href: '/investment/situations',   helper: 'Attach required resources, source candidates, notes' },
  { label: 'Evidence',   href: '/investment/situations',   helper: 'Evidence remains unverified until manual review' },
  { label: 'Promote',    href: '/investment/situations',   helper: 'Manual promotion creates a durable ResearchCase' },
  { label: 'Evaluate',   href: '/investment/research',     helper: 'Evaluation preparation and Intelligence Score' },
  { label: 'Decide',     href: '/investment/research-inbox', helper: 'Human decision with recorded reason; not investment advice' },
];

const workflowNotes = [
  'SpecialSituation = detected signal / triage object.',
  'ResearchCase = durable research object after manual promotion.',
  'Watchlist = ResearchCase state/view label, not a separate entity.',
  'Candidate / Watchlist / Reject = operational view, not investment advice.',
];

const quickLinks: Array<[string, string]> = [
  ['Research Inbox', '/investment/research-inbox'],
  ['Kanban — Special Situations', '/investment/situations'],
  ['Research Cases', '/investment/research'],
  ['Intelligence KPIs', '/investment/intelligence'],
  ['Governance / Agent Ops', '/agent-ops'],
  ['Sources', '/investment/sources'],
  ['Historical Cases / Analogues', '/investment/historical-cases'],
  ['Publishing Drafts (manual only)', '/investment/public-drafts'],
];

const offices: ModuleCard[] = [
  {
    name: 'Governance / Agent Ops',
    description: 'Review Fontana, Dani Weber, Executive Review, agent activity, diagnostics and proposals.',
    href: '/agent-ops',
    status: 'READ-ONLY',
    icon: 'GO',
  },
  {
    name: 'Dani Weber Office — COO',
    description: 'Manual approval authority for promotion, editorial gates, deploys, scanner changes, and publication.',
    href: '/agent-ops',
    status: 'MANUAL',
    icon: 'DW',
  },
  {
    name: 'Fontana Office — CTO',
    description: 'Deterministic audit surface for quality, bottlenecks, guardrails, and technical findings.',
    href: '/agent-ops',
    status: 'READ-ONLY',
    icon: 'RF',
  },
  {
    name: 'Executive Review',
    description: 'Review proposals and next actions without triggering agents, scans, evaluations, or publishing.',
    href: '/agent-ops',
    status: 'SUPPORTING',
    icon: 'ER',
  },
  {
    name: 'Pending Improvement Proposals',
    description: 'Human-reviewed process and product improvement proposals. Dani approval required before implementation.',
    href: '/agent-ops#executive-proposals',
    status: 'MANUAL',
    icon: 'PP',
  },
];

const backendChecklist = [
  'Health ping',
  'ResearchCases endpoint',
  'Situations endpoint',
  'Agent Ops rooms endpoint',
  'Documentation Guide endpoint',
  'Activity Timeline endpoint',
  'Intelligence Score endpoint',
  'Intelligence KPIs endpoint',
  'Fontana report endpoint',
  'GET /api/investment/executive/dani-weber-metrics',
  'GET /api/investment/executive/review',
  'GET /api/investment/research-cases/{id}/operational-view',
  'GET /api/investment/situations/{id}/sec-document-acquisition-preview',
  'POST /api/investment/situations/{id}/sec-document-acquisition',
  'GET /api/investment/research-cases/{id}/sec-document-acquisition-preview',
  'POST /api/investment/research-cases/{id}/sec-document-acquisition',
];

const frontendChecklist = [
  '/',
  '/campus',
  '/investment/situations',
  '/investment/situations/{id}',
  '/investment/research/{id}',
  '/investment/intelligence',
  '/agent-ops',
  '/agent-ops/rooms/{id}',
];

const secAcquisitionSmokeChecks = [
  'Situation preview loads',
  'Situation POST only runs manually',
  'ResearchCase preview loads',
  'ResearchCase POST only runs manually',
  'Evidence remains unverified',
  'Checklist/resource statuses are not auto-completed',
  'No ResearchCase auto-promotion',
  'No evaluator or AI',
];

// ── Page ──────────────────────────────────────────────────────────────────

export default function Home() {
  const investmentOps: ModuleCard[] = [
    {
      name: 'Kanban — Special Situations',
      status: 'CORE',
      description: 'Active SEC-detection workflow: triage, evidence mapping, and manual ResearchCase promotion',
      href: '/investment/situations',
      icon: 'KB',
    },
    {
      name: 'Research Cases',
      status: 'MANUAL',
      description: 'Durable research objects after manual promotion; briefs, tasks, documents, and sources',
      href: '/investment/research',
      icon: 'RC',
    },
    {
      name: 'Research Inbox',
      status: 'CORE',
      description: 'Single working queue: review new detections and open cases, decide next action',
      href: '/investment/research-inbox',
      icon: 'RI',
    },
    {
      name: 'Investment Sources',
      status: 'SUPPORTING',
      description: 'Source registry and SEC source posture; no scan trigger from Mission Control',
      href: '/investment/sources',
      icon: 'SR',
    },
  ];

  const observability: ModuleCard[] = [
    {
      name: 'Radar Status',
      status: 'READ-ONLY',
      description: 'Scanner runs, cron schedule, source health — no scan trigger',
      href: '/investment/radar-status',
      icon: 'RS',
    },
    {
      name: 'Agent Ops',
      status: 'READ-ONLY',
      description: 'Agent rooms, observer diagnostics, Fontana report, and manual next-action context',
      href: '/agent-ops',
      icon: 'AO',
    },
  ];

  const supporting: ModuleCard[] = [
    {
      name: 'Historical Cases',
      status: 'SUPPORTING',
      description: 'Historical analogues and safe methodology context for manual comparison',
      href: '/investment/historical-cases',
      icon: 'HC',
    },
    {
      name: 'Intelligence KPIs',
      status: 'READ-ONLY',
      description: 'Preparation quality, evidence coverage, documentation gaps, and manual review workload',
      href: '/investment/intelligence',
      icon: 'IK',
    },
    {
      name: 'Public Drafts',
      status: 'MANUAL',
      description: 'Manual draft review only; no external posting from Mission Control',
      href: '/investment/public-drafts',
      icon: 'PD',
    },
    {
      name: 'Internal Audit',
      status: 'READ-ONLY',
      description: 'Data-quality checks for missing metadata, methodology, and source alignment',
      href: '/investment/internal-audit',
      icon: 'IA',
    },
  ];

  const advancedPaused: ModuleCard[] = [
    {
      name: 'Evaluations Queue',
      status: 'LEGACY',
      description: 'Legacy/advanced evaluator queue. New SEC-driven cases should flow through Special Situations.',
      href: '/investment/evaluations',
      icon: 'EQ',
    },
    {
      name: 'Investment Watchlist',
      status: 'LEGACY',
      description: 'Older monitoring surface tied to the pre-Kanban evaluation flow',
      href: '/investment/watchlist',
      icon: 'WL',
    },
    {
      name: 'Source Intelligence',
      status: 'ADVANCED',
      description: 'Proposal approval queue for source quality; supporting workflow only',
      href: '/investment/source-intelligence',
      icon: 'SI',
    },
    {
      name: 'Marketplace Assistant',
      status: 'PAUSED',
      description: 'Paused surface. Not part of the current investment workflow.',
      href: '/marketplace',
      icon: 'MP',
    },
    {
      name: 'Operations Campus',
      status: 'PAUSED',
      description: 'Static visual layer. Not operational truth; agent state lives in Agent Ops.',
      href: '/campus',
      icon: 'OC',
    },
    {
      name: 'Agent Roster',
      status: 'ADVANCED',
      description: 'Operational roster for all agents; not needed for daily case completion',
      href: '/agents',
      icon: 'AR',
    },
    {
      name: 'Evaluator v2',
      status: 'ADVANCED',
      description: 'Manual preview only. Not globally enabled and not part of autonomous runtime.',
      href: '/investment/evaluations',
      icon: 'EV',
    },
  ];

  return (
    <div className={styles.page}>
      <div className={styles.canvas}>

        {/* ── Brand ── */}
        <div>
          <div className={styles.brand}>
            <span className={styles.brandName}>SwissEdge</span>
            <span className={styles.brandSuffix}>Mission Control</span>
          </div>
          <div className={styles.brandTagline}>
            Private investment research platform · authorized access only
          </div>
        </div>

        {/* ── System status note (no hardcoded operational claims) ── */}
        <div className={styles.statusStrip}>
          <div className={styles.statusItem}>
            <div className={styles.statusLabel}>System status</div>
            <div className={styles.statusValue}>
              See <Link href="/investment/radar-status" style={{ textDecoration: 'underline' }}>Radar Status</Link> for live scanner/cron state
            </div>
          </div>
          <div className={styles.statusSpacer} />
          <div className={styles.statusPill}>
            <span className={styles.statusPillDot} />
            Human-reviewed · No autonomous decisions
          </div>
        </div>

        {/* ── Investment Operations (visible, primary surface) ── */}
        <div>
          <SectionLabel label="Investment Operations" count={investmentOps.length} />
          <ModuleGrid modules={investmentOps} />
        </div>

        {/* ── Collapsed by default — Research Command Center ── */}
        <Collapsible title="Research Command Center" helper="Detect → Triage → Document → Promote → Evaluate">
          <div className={styles.workflowRow}>
            {workflowSteps.map((step, index) => (
              <span key={step.label} style={{ display: 'inline-flex', alignItems: 'center', gap: 8 }}>
                {index > 0 && <span className={styles.workflowArrow}>→</span>}
                <Link href={step.href} className={styles.workflowStep} title={step.helper}>
                  {step.label}
                </Link>
              </span>
            ))}
          </div>
          <div className={styles.notesGrid}>
            {workflowNotes.map((note) => (
              <div key={note} className={styles.noteCard}>{note}</div>
            ))}
          </div>
          <div className={styles.quickLinks}>
            {quickLinks.map(([label, href]) => (
              <Link key={href} href={href} className={styles.quickLink}>{label}</Link>
            ))}
          </div>
        </Collapsible>

        {/* ── Collapsed by default — Executive Office ── */}
        <Collapsible
          title="Executive Office"
          helper="Governance · human approval · deterministic audit"
          count={offices.length}
        >
          <div className={styles.officeGrid}>
            {offices.map((o) => (
              <Link key={o.name} href={o.href} className={styles.officeCard}>
                <div className={styles.officeHeader}>
                  <div style={{ display: 'flex', gap: 10 }}>
                    <span className={styles.moduleIcon}>{o.icon}</span>
                    <div>
                      <div className={styles.officeTitle}>{o.name}</div>
                    </div>
                  </div>
                  <span className={styles.moduleBadge} data-tone={statusTone(o.status)}>
                    {o.status}
                  </span>
                </div>
                <div className={styles.officeDesc}>{o.description}</div>
              </Link>
            ))}
          </div>
        </Collapsible>

        {/* ── Collapsed by default — Platform Observability ── */}
        <Collapsible
          title="Platform Observability"
          helper="Scanner runs, cron schedule, agent diagnostics"
          count={observability.length}
        >
          <ModuleGrid modules={observability} />
        </Collapsible>

        {/* ── Collapsed by default — Supporting Research Tools ── */}
        <Collapsible
          title="Supporting Research Tools"
          helper="Historical analogues, research inbox, drafts, audit"
          count={supporting.length}
        >
          <ModuleGrid modules={supporting} />
        </Collapsible>

        {/* ── Collapsed by default — Advanced / Legacy / Paused ── */}
        <Collapsible
          title="Advanced / Legacy / Paused"
          helper="Older surfaces and advanced operational tools"
          count={advancedPaused.length}
        >
          <ModuleGrid modules={advancedPaused} />
        </Collapsible>

        {/* ── Collapsed by default — Deployment Verification ── */}
        <Collapsible
          title="Deployment Verification Checklist"
          helper="Manual post-deployment checks · does not call any endpoint"
        >
          <div className={styles.checklistGrid}>
            <div className={styles.checklistColumn}>
              <div className={styles.checklistTitle}>Backend checks</div>
              {backendChecklist.map((item) => (
                <div key={item} className={styles.checklistItem}>
                  <span className={styles.checklistBox} />
                  <span>{item}</span>
                </div>
              ))}
            </div>
            <div className={styles.checklistColumn}>
              <div className={styles.checklistTitle}>Frontend routes</div>
              {frontendChecklist.map((item) => (
                <div key={item} className={styles.checklistItem}>
                  <span className={styles.checklistBox} />
                  <span className={styles.checklistItemMono}>{item}</span>
                </div>
              ))}
            </div>
            <div className={styles.checklistColumn}>
              <div className={styles.checklistTitle}>SEC Acquisition smoke checks</div>
              {secAcquisitionSmokeChecks.map((item) => (
                <div key={item} className={styles.checklistItem}>
                  <span className={styles.checklistBox} />
                  <span>{item}</span>
                </div>
              ))}
            </div>
          </div>
        </Collapsible>

      </div>
    </div>
  );
}
