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

        {/* Investment Operations */}
        <div className="animate-fade-in-2">
          <SectionLabel label="Investment Operations" count={investmentOps.length} />
          <ModuleGrid modules={investmentOps} />
        </div>

        {/* Platform Observability */}
        <div className="animate-fade-in-3">
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
