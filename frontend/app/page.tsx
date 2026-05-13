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
  { label: "SEC EDGAR", href: "/investment/radar-status", helper: "Stored official-source detection metadata" },
  { label: "SpecialSituation", href: "/investment/situations", helper: "Detected case candidate" },
  { label: "Kanban", href: "/investment/situations", helper: "Manual triage and evidence mapping" },
  { label: "Missing Evidence Hunter", href: "/agent-ops", helper: "Observer/manual documentation gaps" },
  { label: "ResearchCase", href: "/investment/research", helper: "Manual promotion target" },
  { label: "Evaluation Preparation", href: "/investment/research", helper: "Preparation readiness only" },
  { label: "Evidence Links", href: "/investment/research", helper: "Metadata-only traceability" },
  { label: "Intelligence Score", href: "/investment/research", helper: "Preparation quality score" },
  { label: "Intelligence KPIs", href: "/investment/intelligence", helper: "Platform quality metrics" },
  { label: "Fontana", href: "/agent-ops#fontana", helper: "Deterministic observer report" },
] as const;

const quickLinks = [
  ["Open Kanban", "/investment/situations"],
  ["Open Research Inbox", "/investment/research-inbox"],
  ["Open ResearchCases", "/investment/research"],
  ["Open Intelligence KPIs", "/investment/intelligence"],
  ["Open Agent Ops", "/agent-ops"],
  ["Open Radar Status", "/investment/radar-status"],
  ["Open Sources", "/investment/sources"],
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

function ResearchCommandCenter() {
  return (
    <div className="card mb-10 animate-fade-in-2">
      <div className="card-header" style={{ alignItems: 'flex-start', gap: 16 }}>
        <div>
          <div className="card-title">Research Command Center</div>
          <div className="card-desc" style={{ marginTop: 4 }}>
            Active SEC-driven workflow, QA posture, and next manual navigation in one place.
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
          "Detected does not mean evaluated.",
          "Evidence found does not mean verified.",
          "Scores measure preparation quality, not investment attractiveness.",
          "Fontana is deterministic observer only.",
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
      name: "Research Inbox",
      status: "READ-ONLY",
      description: "V2 operating queue — existing ResearchCases, legacy/manual labels",
      href: "/investment/research-inbox",
      icon: "RI",
    },
    {
      name: "Intelligence KPIs",
      status: "READ-ONLY",
      description: "Preparation quality, evidence coverage, documentation gaps, and manual review workload.",
      href: "/investment/intelligence",
      icon: "IK",
    },
    {
      name: "Evaluations Queue",
      status: "ACTIVE",
      description: "Legacy/evaluator review queue for evaluator outputs and manually reviewed situations",
      href: "/investment/evaluations",
      icon: "📋",
    },
    {
      name: "Investment Watchlist",
      status: "ACTIVE",
      description: "Situations under active monitoring",
      href: "/investment/watchlist",
      icon: "👁",
    },
    {
      name: "Investment Sources",
      status: "ACTIVE",
      description: "Source registry — enable/disable scanner sources",
      href: "/investment/sources",
      icon: "🗂",
    },
    {
      name: "Evaluator v2",
      status: "PREVIEW",
      description: "Playbook-routed evaluation — manual preview only, not saved",
      href: "/investment/evaluations",
      icon: "🤖",
    },
    {
      name: "Research Cases",
      status: "MANUAL",
      description: "Private research desk — cases, briefs, tasks, documents",
      href: "/investment/research",
      icon: "🔬",
    },
    {
      name: "Historical Cases",
      status: "MANUAL",
      description: "Past situations — reconstruction, lessons, source intelligence",
      href: "/investment/historical-cases",
      icon: "🏛",
    },
    {
      name: "Source Intelligence",
      status: "MANUAL",
      description: "Proposal approval queue — review, approve, reject",
      href: "/investment/source-intelligence",
      icon: "🧠",
    },
    {
      name: "Public Drafts",
      status: "MANUAL",
      description: "Editorial review — Markdown/Substack-ready export",
      href: "/investment/public-drafts",
      icon: "📄",
    },
    {
      name: "Internal Audit",
      status: "READ-ONLY",
      description: "V2 data-quality checks — missing metadata, methodology, source alignment",
      href: "/investment/internal-audit",
      icon: "IA",
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
      description: "Rooms, agents, diagnostics, proposals, and future Fontana reports",
      href: "/agent-ops",
      icon: "AO",
    },
    {
      name: "Agent Roster",
      status: "ACTIVE",
      description: "All operational agents — status, runs, costs",
      href: "/agents",
      icon: "👥",
    },
  ];

  const marketplace: ModuleCard[] = [
    {
      name: "Marketplace Assistant",
      status: "PARTIAL",
      description: "Hochdeutsch listing generation — Tutti.ch adapter // draft-only",
      href: "/marketplace",
      icon: "🏪",
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

        {/* Marketplace */}
        <div className="animate-fade-in-4">
          <SectionLabel label="Marketplace" count={marketplace.length} />
          <ModuleGrid modules={marketplace} />
        </div>

      </div>
    </>
  );
}
