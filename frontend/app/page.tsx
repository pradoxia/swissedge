import Link from "next/link";

interface ModuleCard {
  name: string;
  status: string;
  description: string;
  href: string;
  icon: string;
}

function statusBadgeClass(status: string) {
  switch (status) {
    case 'ACTIVE':    return 'status-badge status-badge--active';
    case 'CORE':      return 'status-badge status-badge--active';
    case 'READ-ONLY': return 'status-badge status-badge--readonly';
    case 'MANUAL':    return 'status-badge status-badge--manual';
    case 'PREVIEW':   return 'status-badge status-badge--preview';
    case 'PARTIAL':   return 'status-badge status-badge--partial';
    case 'SUPPORTING': return 'status-badge status-badge--readonly';
    case 'ADVANCED':  return 'status-badge status-badge--partial';
    case 'LEGACY':    return 'status-badge status-badge--preview';
    case 'PAUSED':    return 'status-badge status-badge--readonly';
    default:          return 'status-badge status-badge--readonly';
  }
}

function SectionLabel({ label, count }: { label: string; count?: number }) {
  return (
    <div className="section-header">
      <span className="section-title">{label}</span>
      <div className="section-line"></div>
      {count !== undefined && <span className="section-count">{count}</span>}
    </div>
  );
}

function ModuleGrid({ modules }: { modules: ModuleCard[] }) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-10">
      {modules.map((module) => (
        <Link
          key={module.name}
          href={module.href}
          className="card block no-underline"
          style={{ textDecoration: 'none' }}
        >
          <div className="card-header">
            <div className="card-title-group">
              <span className="card-icon">{module.icon}</span>
              <div>
                <div className="card-title">{module.name}</div>
                <div className="card-desc">{module.description}</div>
              </div>
            </div>
            <span className={statusBadgeClass(module.status)}>{module.status}</span>
          </div>
        </Link>
      ))}
    </div>
  );
}

const workflowSteps = [
  { label: "Detect", href: "/investment/radar-status", helper: "SEC EDGAR cron creates stored detection metadata" },
  { label: "Triage", href: "/investment/situations", helper: "SpecialSituation is a detected signal and triage object" },
  { label: "Document", href: "/investment/situations", helper: "Attach required resources, source candidates, and notes" },
  { label: "Evidence Review", href: "/investment/situations", helper: "Evidence remains unverified until manual review" },
  { label: "Promote", href: "/investment/situations", helper: "Manual promotion creates a durable ResearchCase" },
  { label: "Evaluate", href: "/investment/research", helper: "Evaluation preparation and Intelligence Score are readiness tools" },
  { label: "Candidate / Watchlist / Reject", href: "/investment/intelligence", helper: "Operational view labels only; not investment advice" },
] as const;

const quickLinks = [
  ["Kanban — Special Situations", "/investment/situations"],
  ["Research Cases", "/investment/research"],
  ["Intelligence KPIs", "/investment/intelligence"],
  ["Agent Ops / Executive Office", "/agent-ops"],
  ["Sources", "/investment/sources"],
  ["Historical Cases / Analogues", "/investment/historical-cases"],
  ["Publishing Drafts, manual only", "/investment/public-drafts"],
] as const;

const backendChecklist = [
  "Health ping",
  "ResearchCases endpoint",
  "Situations endpoint",
  "Agent Ops rooms endpoint",
  "Documentation Guide endpoint",
  "Activity Timeline endpoint",
  "Intelligence Score endpoint",
  "Intelligence KPIs endpoint",
  "Fontana report endpoint",
  "GET /api/investment/executive/dani-weber-metrics",
  "GET /api/investment/executive/review",
  "GET /api/investment/research-cases/{id}/operational-view",
  "GET /api/investment/situations/{id}/sec-document-acquisition-preview",
  "POST /api/investment/situations/{id}/sec-document-acquisition",
  "GET /api/investment/research-cases/{id}/sec-document-acquisition-preview",
  "POST /api/investment/research-cases/{id}/sec-document-acquisition",
] as const;

const frontendChecklist = [
  "/",
  "/investment/situations",
  "/investment/situations/{id}",
  "/investment/research/{id}",
  "/investment/intelligence",
  "/agent-ops",
  "/agent-ops/rooms/{id}",
] as const;

const secAcquisitionSmokeChecks = [
  "Situation preview loads",
  "Situation POST only runs manually",
  "ResearchCase preview loads",
  "ResearchCase POST only runs manually",
  "Evidence remains unverified",
  "Checklist/resource statuses are not auto-completed",
  "No ResearchCase auto-promotion",
  "No evaluator or AI",
] as const;

function ResearchCommandCenter() {
  return (
    <div className="card mb-10 animate-fade-in-2">
      <div className="card-header" style={{ alignItems: 'flex-start', gap: 16 }}>
        <div>
          <div className="card-title">Research Command Center</div>
          <div className="card-desc" style={{ marginTop: 4 }}>
            Current operating flow: Detect &gt; Triage &gt; Document &gt; Evidence Review &gt; Promote &gt; Evaluate &gt; Candidate / Watchlist / Reject.
          </div>
        </div>
        <span className="status-badge status-badge--readonly">READ-ONLY</span>
      </div>

      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginTop: 18 }}>
        {workflowSteps.map((step, index) => (
          <div key={step.label} style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            {index > 0 && <span style={{ color: 'var(--text-faint)', fontSize: 12 }}>-&gt;</span>}
            <Link
              href={step.href}
              className="status-badge status-badge--manual"
              title={step.helper}
              style={{ textDecoration: 'none' }}
            >
              {step.label}
            </Link>
          </div>
        ))}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(210px, 1fr))', gap: 10, marginTop: 18 }}>
        {[
          "SpecialSituation = detected signal / triage object.",
          "ResearchCase = durable research object after manual promotion.",
          "Watchlist = ResearchCase state/view label, not a separate entity.",
          "Candidate / Watchlist / Reject = operational view, not investment advice.",
        ].map(note => (
          <div key={note} style={{ border: '1px solid var(--border-subtle)', borderRadius: 8, padding: 12, color: 'var(--text-muted)', fontSize: 12, lineHeight: 1.5 }}>
            {note}
          </div>
        ))}
      </div>

      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginTop: 18 }}>
        {quickLinks.map(([label, href]) => (
          <Link key={href} href={href} className="btn btn--secondary btn--sm">
            {label}
          </Link>
        ))}
      </div>
    </div>
  );
}

function ExecutiveOffice() {
  const offices = [
    {
      name: "Dani Weber Office — COO",
      description: "Manual approval authority for promotion, editorial gates, deploys, scanner changes, and publication.",
      href: "/agent-ops",
      status: "MANUAL",
    },
    {
      name: "Fontana Office — CTO",
      description: "Deterministic audit surface for quality, bottlenecks, guardrails, and technical findings.",
      href: "/agent-ops",
      status: "READ-ONLY",
    },
    {
      name: "Executive Review",
      description: "Review proposals and next actions without triggering agents, scans, evaluations, or publishing.",
      href: "/agent-ops",
      status: "SUPPORTING",
    },
    {
      name: "Pending Improvement Proposals",
      description: "Human-reviewed process and product improvement proposals. Dani approval is required before implementation.",
      href: "/agent-ops#executive-proposals",
      status: "MANUAL",
    },
  ];

  return (
    <div className="card mb-10 animate-fade-in-2">
      <div className="card-header" style={{ alignItems: 'flex-start', gap: 16 }}>
        <div>
          <div className="card-title">Executive Office</div>
          <div className="card-desc" style={{ marginTop: 4 }}>
            Governance surfaces for human approval and deterministic audit. No chat, live AI, autonomous agents, or scheduler actions.
          </div>
        </div>
        <span className="status-badge status-badge--manual">HUMAN GATED</span>
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: 10, marginTop: 16 }}>
        {offices.map(office => (
          <Link
            key={office.name}
            href={office.href}
            className="block no-underline"
            style={{
              textDecoration: 'none',
              border: '1px solid var(--border-subtle)',
              borderRadius: 8,
              padding: 14,
              background: 'var(--bg-subtle)',
            }}
          >
            <div className="card-header">
              <div>
                <div className="card-title">{office.name}</div>
                <div className="card-desc">{office.description}</div>
              </div>
              <span className={statusBadgeClass(office.status)}>{office.status}</span>
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
}

function DeploymentVerificationChecklist() {
  return (
    <div className="card mb-10 animate-fade-in-2">
      <div className="card-header" style={{ alignItems: 'flex-start', gap: 16 }}>
        <div>
          <div className="card-title">Deployment Verification Checklist</div>
          <div className="card-desc" style={{ marginTop: 4 }}>
            Manual post-deployment checks only. This panel does not call health endpoints, trigger scans, or deploy anything.
          </div>
        </div>
        <span className="status-badge status-badge--readonly">MANUAL QA</span>
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: 16, marginTop: 16 }}>
        <ChecklistColumn title="Backend checks" items={backendChecklist} />
        <ChecklistColumn title="Frontend routes" items={frontendChecklist} mono />
        <ChecklistColumn title="SEC Acquisition v1 smoke checks" items={secAcquisitionSmokeChecks} />
      </div>
    </div>
  );
}

function ChecklistColumn({ title, items, mono = false }: { title: string; items: readonly string[]; mono?: boolean }) {
  return (
    <div style={{ border: '1px solid var(--border-subtle)', borderRadius: 8, padding: 14 }}>
      <div className="section-title" style={{ marginBottom: 10 }}>{title}</div>
      <div style={{ display: 'grid', gap: 8 }}>
        {items.map(item => (
          <div key={item} style={{ display: 'flex', gap: 8, alignItems: 'flex-start', fontSize: 12, color: 'var(--text-muted)' }}>
            <span style={{ width: 10, height: 10, border: '1px solid var(--border-default)', borderRadius: 2, marginTop: 4, flexShrink: 0 }} />
            <span style={{ fontFamily: mono ? 'var(--font-mono)' : undefined }}>{item}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

export default function Home() {
  const investmentOps: ModuleCard[] = [
    {
      name: "Kanban — Special Situations",
      status: "CORE",
      description: "Active SEC-detection workflow: triage, evidence mapping, and manual ResearchCase promotion",
      href: "/investment/situations",
      icon: "KB",
    },
    {
      name: "Research Cases",
      status: "MANUAL",
      description: "Durable research objects after manual promotion; briefs, tasks, documents, and sources",
      href: "/investment/research",
      icon: "RC",
    },
    {
      name: "Intelligence KPIs",
      status: "READ-ONLY",
      description: "Preparation quality, evidence coverage, documentation gaps, and manual review workload",
      href: "/investment/intelligence",
      icon: "IK",
    },
    {
      name: "Investment Sources",
      status: "SUPPORTING",
      description: "Source registry and SEC source posture; no scan trigger from Mission Control",
      href: "/investment/sources",
      icon: "SR",
    },
  ];

  const observability: ModuleCard[] = [
    {
      name: "Radar Status",
      status: "READ-ONLY",
      description: "Scanner runs, cron schedule, source health — no scan trigger",
      href: "/investment/radar-status",
      icon: "📊",
    },
    {
      name: "Agent Ops",
      status: "READ-ONLY",
      description: "Agent rooms, observer diagnostics, Fontana report, and manual next-action context",
      href: "/agent-ops",
      icon: "AO",
    },
  ];

  const supporting: ModuleCard[] = [
    {
      name: "Historical Cases",
      status: "SUPPORTING",
      description: "Historical analogues and safe methodology context for manual comparison",
      href: "/investment/historical-cases",
      icon: "HC",
    },
    {
      name: "Research Inbox",
      status: "SUPPORTING",
      description: "ResearchCase intake overview and manual labels",
      href: "/investment/research-inbox",
      icon: "RI",
    },
    {
      name: "Public Drafts",
      status: "MANUAL",
      description: "Manual draft review only; no auto-publish or external posting",
      href: "/investment/public-drafts",
      icon: "PD",
    },
    {
      name: "Internal Audit",
      status: "READ-ONLY",
      description: "Data-quality checks for missing metadata, methodology, and source alignment",
      href: "/investment/internal-audit",
      icon: "IA",
    },
  ];

  const advancedPaused: ModuleCard[] = [
    {
      name: "Evaluations Queue",
      status: "LEGACY",
      description: "Legacy/advanced evaluator queue. New SEC-driven cases should flow through Special Situations.",
      href: "/investment/evaluations",
      icon: "EQ",
    },
    {
      name: "Investment Watchlist",
      status: "LEGACY",
      description: "Older monitoring surface tied to the pre-Kanban evaluation flow",
      href: "/investment/watchlist",
      icon: "WL",
    },
    {
      name: "Source Intelligence",
      status: "ADVANCED",
      description: "Proposal approval queue for source quality; supporting workflow only",
      href: "/investment/source-intelligence",
      icon: "SI",
    },
    {
      name: "Marketplace Assistant",
      status: "PAUSED",
      description: "Paused surface. Not part of the current investment workflow.",
      href: "/marketplace",
      icon: "MP",
    },
    {
      name: "Agent Roster",
      status: "ADVANCED",
      description: "Operational roster for all agents; not needed for daily case completion",
      href: "/agents",
      icon: "AR",
    },
    {
      name: "Evaluator v2",
      status: "ADVANCED",
      description: "Manual preview only. Not globally enabled and not part of autonomous runtime.",
      href: "/investment/evaluations",
      icon: "EV",
    },
  ];

  return (
    <>
      <div className="ambient-glow" />
      <div className="page-container" style={{ position: 'relative', zIndex: 1 }}>

        {/* Brand header */}
        <div className="mb-10 animate-fade-in">
          <div className="brand-row">
            <span className="brand-name">SwissEdge</span>
            <span className="brand-suffix">Mission Control</span>
          </div>
          <div className="brand-tagline">Private AI operations dashboard · authorized access only</div>
        </div>

        {/* System status strip */}
        <div className="top-bar animate-fade-in-1">
          <div className="top-bar-stat">
            <span className="top-bar-label">V2 Mode</span>
            <span className="top-bar-value">Manual-only</span>
          </div>
          <div className="top-bar-stat">
            <span className="top-bar-label">V2 Daily Cap</span>
            <span className="top-bar-value">10 / day</span>
          </div>
          <div className="top-bar-stat">
            <span className="top-bar-label">Production</span>
            <span className="top-bar-value">V1 Default</span>
          </div>
          <div className="top-bar-stat">
            <span className="top-bar-label">Cron V2</span>
            <span className="top-bar-value">Disabled</span>
          </div>
          <div className="top-bar-stat" style={{ marginLeft: 'auto', display: 'flex', flexDirection: 'row', alignItems: 'center', gap: '8px' }}>
            <span className="status-dot status-dot--active"></span>
            <span className="top-bar-value">Operational</span>
          </div>
        </div>

        <ResearchCommandCenter />
        <ExecutiveOffice />
        <DeploymentVerificationChecklist />

        {/* Investment Operations */}
        <div className="animate-fade-in-3">
          <SectionLabel label="Investment Operations" count={investmentOps.length} />
          <ModuleGrid modules={investmentOps} />
        </div>

        {/* Platform Observability */}
        <div className="animate-fade-in-4">
          <SectionLabel label="Platform Observability" count={observability.length} />
          <ModuleGrid modules={observability} />
        </div>

        {/* Supporting Research Tools */}
        <div className="animate-fade-in-4">
          <SectionLabel label="Supporting Research Tools" count={supporting.length} />
          <ModuleGrid modules={supporting} />
        </div>

        {/* Advanced / Legacy / Paused */}
        <div className="animate-fade-in-4">
          <SectionLabel label="Advanced / Legacy / Paused" count={advancedPaused.length} />
          <ModuleGrid modules={advancedPaused} />
        </div>

      </div>
    </>
  );
}
