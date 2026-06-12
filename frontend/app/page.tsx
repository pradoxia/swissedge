'use client';

import Link from 'next/link';
import { PageHeader, SectionCard, InfoBanner } from '@/app/components/ui';

// ── Types ─────────────────────────────────────────────────────────────────

interface ModuleCard {
  name: string;
  status: string;
  description: string;
  href: string;
  icon: string;
}

function badgeClass(status: string): string {
  switch (status) {
    case 'CORE':       return 'status-badge--active';
    case 'ACTIVE':     return 'status-badge--active';
    case 'MANUAL':     return 'status-badge--manual';
    case 'READ-ONLY':  return 'status-badge--readonly';
    case 'SUPPORTING': return 'status-badge--readonly';
    case 'PREVIEW':    return 'status-badge--preview';
    case 'ADVANCED':   return 'status-badge--partial';
    case 'LEGACY':     return 'status-badge--readonly';
    case 'PAUSED':     return 'status-badge--readonly';
    default:           return 'status-badge--readonly';
  }
}

// ── Data ─────────────────────────────────────────────────────────────────

const workflowSteps = [
  { label: 'Detect',   href: '/investment/radar-status',   helper: 'SEC EDGAR cron + automatic document acquisition' },
  { label: 'Triage',   href: '/investment/research-inbox', helper: 'Unified queue for detections and open cases' },
  { label: 'Document', href: '/investment/situations',     helper: 'Auto-acquired SEC documents, candidate evidence' },
  { label: 'Promote',  href: '/investment/situations',     helper: 'Manual promotion creates a durable ResearchCase' },
  { label: 'Analyze',  href: '/investment/research',       helper: 'Gated preview-only AI analysis (manual approval)' },
  { label: 'Decide',   href: '/investment/research-inbox', helper: 'Human decision with recorded reason; not investment advice' },
];

const quickLinks: Array<[string, string]> = [
  ['Research Inbox', '/investment/research-inbox'],
  ['Kanban — Special Situations', '/investment/situations'],
  ['Research Cases', '/investment/research'],
  ['Radar Status', '/investment/radar-status'],
  ['Governance / Agent Ops', '/agent-ops'],
  ['Sources', '/investment/sources'],
];

const investmentOps: ModuleCard[] = [
  {
    name: 'Research Inbox',
    status: 'CORE',
    description: 'Single working queue: review new detections and open cases, record decisions, update price context',
    href: '/investment/research-inbox',
    icon: 'RI',
  },
  {
    name: 'Kanban — Special Situations',
    status: 'CORE',
    description: 'Active SEC-detection workflow: triage, acquired documents, evidence mapping, manual promotion',
    href: '/investment/situations',
    icon: 'KB',
  },
  {
    name: 'Research Cases',
    status: 'MANUAL',
    description: 'Durable research objects after manual promotion; daily workbench with documents, brief, and decision',
    href: '/investment/research',
    icon: 'RC',
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
    description: 'Scanner runs, cron schedule, auto-acquisition counters, source health — no scan trigger',
    href: '/investment/radar-status',
    icon: 'RS',
  },
  {
    name: 'Agent Ops',
    status: 'READ-ONLY',
    description: 'Agent registry, run history, diagnostics, and governance proposals',
    href: '/agent-ops',
    icon: 'AO',
  },
];

const supporting: ModuleCard[] = [
  {
    name: 'Historical Cases',
    status: 'SUPPORTING',
    description: 'Historical analogues and methodology context for manual comparison',
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
    description: 'Legacy evaluator queue. New SEC-driven cases flow through Special Situations.',
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
];

// ── Components ───────────────────────────────────────────────────────────

function ModuleGrid({ modules }: { modules: ModuleCard[] }) {
  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: 14 }}>
      {modules.map(module => (
        <Link key={module.name} href={module.href} className="card" style={{ textDecoration: 'none' }}>
          <div className="card-header">
            <div className="card-title-group">
              <span className="card-icon">{module.icon}</span>
              <div>
                <div className="card-title">{module.name}</div>
              </div>
            </div>
            <span className={`status-badge ${badgeClass(module.status)}`}>{module.status}</span>
          </div>
          <div className="card-desc">{module.description}</div>
        </Link>
      ))}
    </div>
  );
}

function GroupHeader({ label, count }: { label: string; count?: number }) {
  return (
    <div className="section-header" style={{ margin: '26px 0 12px' }}>
      <span className="section-title">{label}</span>
      <div className="section-line" />
      {count !== undefined && (
        <span style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--text-faint)' }}>{count}</span>
      )}
    </div>
  );
}

// ── Page ──────────────────────────────────────────────────────────────────

export default function Home() {
  return (
    <div className="page-container--wide">

      <PageHeader
        title="SwissEdge"
        subtitle="Mission Control · private investment research platform · authorized access only"
        badge={<span className="status-badge status-badge--manual">Human-reviewed</span>}
        actions={
          <Link href="/investment/radar-status" className="btn btn--secondary btn--sm">
            Live system status →
          </Link>
        }
      />

      <InfoBanner variant="guardrail">
        Detected does not mean evaluated. Evidence found does not mean verified. No autonomous decisions,
        recommendations, or publishing happen from this platform.
      </InfoBanner>

      {/* Daily loop */}
      <SectionCard title="Daily research loop">
        <div style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', gap: 8 }}>
          {workflowSteps.map((step, index) => (
            <span key={step.label} style={{ display: 'inline-flex', alignItems: 'center', gap: 8 }}>
              {index > 0 && <span style={{ color: 'var(--text-faint)' }}>→</span>}
              <Link href={step.href} className="btn btn--ghost btn--sm" title={step.helper}>
                {step.label}
              </Link>
            </span>
          ))}
        </div>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginTop: 12 }}>
          {quickLinks.map(([label, href]) => (
            <Link key={href} href={href} className="status-badge status-badge--readonly" style={{ textDecoration: 'none' }}>
              {label}
            </Link>
          ))}
        </div>
      </SectionCard>

      <GroupHeader label="Investment Operations" count={investmentOps.length} />
      <ModuleGrid modules={investmentOps} />

      <GroupHeader label="Platform Observability" count={observability.length} />
      <ModuleGrid modules={observability} />

      <details style={{ marginTop: 26 }}>
        <summary className="section-header" style={{ cursor: 'pointer', marginBottom: 12 }}>
          <span className="section-title">Supporting Research Tools</span>
          <div className="section-line" />
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--text-faint)' }}>{supporting.length}</span>
        </summary>
        <ModuleGrid modules={supporting} />
      </details>

      <details style={{ marginTop: 18 }}>
        <summary className="section-header" style={{ cursor: 'pointer', marginBottom: 12 }}>
          <span className="section-title">Advanced · Legacy · Paused</span>
          <div className="section-line" />
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--text-faint)' }}>{advancedPaused.length}</span>
        </summary>
        <ModuleGrid modules={advancedPaused} />
      </details>

      <div style={{ marginTop: 30, fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-faint)', lineHeight: 1.6 }}>
        Private research desk — detected does not mean evaluated — no publishing without manual approval.
      </div>

    </div>
  );
}
