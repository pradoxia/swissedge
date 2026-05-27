// SwissEdge Campus — Configuration
// Single source of truth for rooms, agents, hotspots, and positions.
// Data sources:
//   - Rooms: docs/AGENT_ROOMS_OPERATING_MODEL.md (purpose + main question)
//   - Agents: backend/services/observability/agent_registry.py (agent_name + role)
//             swissedge-ai-context/agent-ops/agents.md (roster + skills)

export type RoomId =
  | 'observatory'
  | 'evidence'
  | 'library'
  | 'research'
  | 'editorial'
  | 'executive'
  | 'historical'
  | 'operations';

export type AgentId =
  | 'edgar_scout'
  | 'form_parser'
  | 'playbook_scribe'
  | 'case_builder'
  | 'quality_sentinel'
  | 'fontana'
  | 'weber'
  | 'historian';

export interface RoomConfig {
  id: RoomId;
  displayName: string;
  backend: string;
  subtitle: string;
  description: string;
  mainQuestion: string;
  image: string | null;
  agentIds: AgentId[];
  isHub?: boolean;
  noLink?: boolean;
}

export interface AgentConfig {
  id: AgentId;
  defaultName: string;
  movieRef: string | null;
  role: string;
  purpose: string;
  pipeline: { position: number | null; room: string };
  skills: string[];
  roomId: RoomId;
  position: { x: number; y: number };
  initials: string;
  color: string;
  // Backend agent_name in the observability registry (if mapped).
  // Used to fetch real logs / runs via fetchAgent(backendAgentName).
  // If undefined, the agent is conceptual only (governance/exploration role)
  // and the panel will derive info from mission-control aggregates.
  backendAgentName?: string;
}

export interface HotspotConfig {
  roomId: RoomId;
  points: string;
  labelX: number;
  labelY: number;
  labelText: string;
}

// ── ROOMS ─────────────────────────────────────────────────────────────────────

export const ROOMS: Record<RoomId, RoomConfig> = {
  observatory: {
    id: 'observatory',
    displayName: 'Observatory',
    backend: 'Detection Room',
    subtitle: 'Detection · Radar Room',
    description:
      'Scans sources such as SEC EDGAR, identifies filings and signals, classifies form type and probable situation type.',
    mainQuestion: 'Has something new appeared that deserves review?',
    image: '/campus/rooms/observatory.png',
    agentIds: ['edgar_scout'],
  },
  evidence: {
    id: 'evidence',
    displayName: 'Evidence Vault',
    backend: 'Evidence Lab',
    subtitle: 'Evidence · Evidence Lab',
    description:
      'Turns a detected signal into an evidence packet: maps official source links, identifies the primary document and exhibits, preserves source provenance.',
    mainQuestion: 'What official evidence do we already have and where is it?',
    image: '/campus/rooms/evidence.png',
    agentIds: ['form_parser'],
  },
  library: {
    id: 'library',
    displayName: 'Library of Alexandria',
    backend: 'Playbook Workshop',
    subtitle: 'Methodology · Playbook Workshop',
    description:
      'Connects each case with the course methodology: maps situation types to chapters, selects playbooks, and builds case-specific checklists.',
    mainQuestion:
      'According to the course, what do we need to know and what documents are required?',
    image: '/campus/rooms/library.png',
    agentIds: ['playbook_scribe'],
  },
  research: {
    id: 'research',
    displayName: 'Research Studio',
    backend: 'Research Desk',
    subtitle: 'Documentation · Research Desk',
    description:
      'Turns evidence plus the course checklist into actionable documentation: detects missing critical documents, prepares promotion readiness, proposes next manual actions.',
    mainQuestion:
      'Is this case sufficiently documented for Dani to review or promote manually?',
    image: '/campus/rooms/research.png',
    agentIds: ['case_builder'],
  },
  editorial: {
    id: 'editorial',
    displayName: 'Editorial Room',
    backend: 'Quality Court',
    subtitle: 'Quality · Quality Court',
    description:
      'Reviews quality, consistency, and guardrails: checks inconsistencies, detects misclassification, flags trust risks, prevents investment-advice language.',
    mainQuestion:
      'Can we operationally trust this documentation, or must something be reviewed first?',
    image: '/campus/rooms/editorial.png',
    agentIds: ['quality_sentinel'],
  },
  executive: {
    id: 'executive',
    displayName: 'Executive Office',
    backend: 'Executive Office',
    subtitle: 'Leadership · Operating system supervision',
    description:
      'Supervises the full SwissEdge operating system: detects bottlenecks, reviews every room, proposes improvements, prioritizes sprints.',
    mainQuestion: 'Is SwissEdge working as a system and what should be improved next?',
    image: '/campus/rooms/executive.png',
    agentIds: ['fontana', 'weber'],
  },
  // Historical Archive: kept visually in the campus but not navigable.
  // It is NOT part of the canonical operating model. Future iteration:
  // either remove it from the campus or rework the layout to absorb its
  // function into another room.
  historical: {
    id: 'historical',
    displayName: 'Historical Archive',
    backend: '(exploration · not in operating model)',
    subtitle: 'Historical · Pattern Analogies',
    description:
      'Exploration room. Surfaces historical analogies of past special situations to enrich research. Not part of the canonical operating model.',
    mainQuestion: 'Has this kind of situation happened before?',
    image: '/campus/rooms/historical.png',
    agentIds: ['historian'],
    noLink: true,
  },
  operations: {
    id: 'operations',
    displayName: 'Operations Center',
    backend: 'Hub',
    subtitle: 'Central Hub · No interior',
    description:
      'Visual hub of the campus. Surfaces the live pulse of every room and the case pipeline.',
    mainQuestion: '',
    image: null,
    agentIds: [],
    isHub: true,
  },
};

// ── AGENTS ────────────────────────────────────────────────────────────────────

export const AGENTS: Record<AgentId, AgentConfig> = {
  edgar_scout: {
    id: 'edgar_scout',
    defaultName: 'John Anderton',
    movieRef: 'Minority Report (2002) — Tom Cruise',
    role: 'Edgar Scout',
    purpose:
      'Scans sources such as SEC EDGAR, identifies filings and signals, classifies form type and probable situation type.',
    pipeline: { position: 1, room: 'Detection Room' },
    skills: ['Edgar Scout', 'Router Analyst', 'Noise Filter', 'Duplicate Detector', 'Source Monitor'],
    roomId: 'observatory',
    position: { x: 35, y: 90 },
    initials: 'JA',
    color: '#7e6cb0',
    backendAgentName: 'investment_scanner',
  },
  form_parser: {
    id: 'form_parser',
    defaultName: 'Winston "The Wolf" Wolfe',
    movieRef: 'Pulp Fiction (1994) — Harvey Keitel',
    role: 'Evidence Mapper',
    purpose:
      'Turns detected signals into evidence packets. Identifies primary documents and exhibits, preserves source provenance.',
    pipeline: { position: 2, room: 'Evidence Lab' },
    skills: [
      'Evidence Mapper',
      'SEC Filing Locator',
      'SEC Exhibit Index Reader',
      'SEC Document Classifier',
      'Related Filing Finder',
      'Source Provenance Tracker',
    ],
    roomId: 'evidence',
    position: { x: 50, y: 92 },
    initials: 'WW',
    color: '#6b5b8c',
    backendAgentName: 'investment_classifier',
  },
  playbook_scribe: {
    id: 'playbook_scribe',
    defaultName: 'Gandalf el Gris',
    movieRef: 'El Señor de los Anillos (2001) — Ian McKellen',
    role: 'Playbook Scribe',
    purpose:
      'Maps situation types to course chapters, selects playbooks, builds case-specific checklists.',
    pipeline: { position: 3, room: 'Playbook Workshop' },
    skills: [
      'Playbook Scribe',
      'Course Chapter Mapper',
      'Checklist Builder',
      'Course Question Mapper',
      'Skill Requirement Mapper',
      'Document Importance Assigner',
    ],
    roomId: 'library',
    position: { x: 50, y: 92 },
    initials: 'GG',
    color: '#7e6cb0',
    backendAgentName: 'course_reference_agent',
  },
  case_builder: {
    id: 'case_builder',
    defaultName: 'Robert Langdon',
    movieRef: 'El código Da Vinci (2006) — Tom Hanks',
    role: 'Documentation Agent',
    purpose:
      'Turns evidence + course checklist into documentation. Detects missing critical documents, prepares promotion readiness.',
    pipeline: { position: 4, room: 'Research Desk' },
    skills: [
      'Documentation Agent',
      'Missing Document Detector',
      'Document Matcher',
      'Readiness Scorer',
      'Next Best Action Generator',
      'Consideration Extractor',
      'Timeline Extractor',
      'Condition Extractor',
      'Risk Factor Extractor',
    ],
    roomId: 'research',
    position: { x: 50, y: 92 },
    initials: 'RL',
    color: '#d4a155',
    backendAgentName: 'investment_evaluator',
  },
  quality_sentinel: {
    id: 'quality_sentinel',
    defaultName: 'Ron Burgundy',
    movieRef: 'Anchorman (2004) — Will Ferrell',
    role: 'Quality Sentinel',
    purpose:
      'Reviews quality, consistency, and guardrails. Detects misclassification, flags trust risks, prevents investment-advice language.',
    pipeline: { position: 5, room: 'Quality Court' },
    skills: [
      'Quality Sentinel',
      'Consistency Checker',
      'Guardrail Checker',
      'Evidence Completeness Reviewer',
      'Misclassification Detector',
      'Noise Reviewer',
    ],
    roomId: 'editorial',
    position: { x: 50, y: 92 },
    initials: 'RB',
    color: '#f4c89e',
  },
  fontana: {
    id: 'fontana',
    defaultName: 'Rafael Fontana',
    movieRef: null,
    role: 'CTO · Project Governor',
    purpose:
      'Maintains continuity, reports, roadmap, ADRs, risks, and architecture proposals. Observes all rooms conceptually.',
    pipeline: { position: 6, room: 'Executive Office' },
    skills: [
      'Technical Governance',
      'Strategic Reviewer',
      'Skill Gap Analyst',
      'Bottleneck Analyst',
      'ADR Maintainer',
    ],
    roomId: 'executive',
    position: { x: 38, y: 90 },
    initials: 'RF',
    color: '#d4a155',
  },
  weber: {
    id: 'weber',
    defaultName: 'Danny Weber',
    movieRef: null,
    role: 'COO · Operations Lead',
    purpose:
      'Oversees daily operations and execution across rooms. Translates recurring issues into sprint candidates.',
    pipeline: { position: 6, room: 'Executive Office' },
    skills: [
      'Process Governance',
      'Operations Lead',
      'Sprint Prioritizer',
      'Process Bottleneck Analyst',
    ],
    roomId: 'executive',
    position: { x: 62, y: 90 },
    initials: 'DW',
    color: '#6b5b8c',
  },
  historian: {
    id: 'historian',
    defaultName: 'Emmett "Doc" Brown',
    movieRef: 'Regreso al futuro (1985) — Christopher Lloyd',
    role: 'Pattern Analogist',
    purpose:
      'Surfaces historical analogies of past special situations. Exploration only — not part of the canonical pipeline.',
    pipeline: { position: null, room: 'Exploration · Historical Archive' },
    skills: ['Pattern Analogist', 'Case Historian', 'Timeline Builder'],
    roomId: 'historical',
    position: { x: 50, y: 92 },
    initials: 'DB',
    color: '#a8d5d3',
  },
};

// ── HOTSPOTS ──────────────────────────────────────────────────────────────────
// Coordinates are direct percentages of the stage (0-100 x, 0-100 y).
// viewBox="0 0 100 100" with preserveAspectRatio="none".

export const HOTSPOTS: HotspotConfig[] = [
  { roomId: 'executive',   points: '15,22 27,18 28,65 16,68', labelX: 21, labelY: 44, labelText: '1 · Executive' },
  { roomId: 'observatory', points: '24,12 46,10 46,52 25,55', labelX: 35, labelY: 33, labelText: '2 · Observatory' },
  { roomId: 'operations',  points: '46,10 60,10 62,66 45,68', labelX: 54, labelY: 40, labelText: '3 · Operations' },
  { roomId: 'research',    points: '58,22 74,22 74,52 58,52', labelX: 66, labelY: 38, labelText: '4 · Research' },
  { roomId: 'editorial',   points: '76,28 94,28 94,66 77,68', labelX: 85, labelY: 48, labelText: '5 · Editorial' },
  { roomId: 'historical',  points: '18,50 38,48 38,78 18,78', labelX: 28, labelY: 64, labelText: '6 · Historical' },
  { roomId: 'evidence',    points: '43,72 56,72 56,93 43,93', labelX: 49, labelY: 84, labelText: '7 · Evidence' },
  { roomId: 'library',     points: '52,58 80,56 80,88 52,90', labelX: 66, labelY: 73, labelText: '8 · Library' },
];

// ── AGENT NAME OVERRIDES (persists in localStorage) ───────────────────────────

const NAME_STORAGE_KEY = 'swissedge.campus.agentNameOverrides';

export function loadAgentNameOverrides(): Partial<Record<AgentId, string>> {
  if (typeof window === 'undefined') return {};
  try {
    const raw = localStorage.getItem(NAME_STORAGE_KEY);
    return raw ? JSON.parse(raw) : {};
  } catch {
    return {};
  }
}

export function saveAgentNameOverride(agentId: AgentId, name: string): void {
  if (typeof window === 'undefined') return;
  try {
    const current = loadAgentNameOverrides();
    current[agentId] = name;
    localStorage.setItem(NAME_STORAGE_KEY, JSON.stringify(current));
  } catch {
    // Silently ignore — localStorage might be disabled
  }
}

export function getAgentDisplayName(
  agentId: AgentId,
  overrides: Partial<Record<AgentId, string>>,
): string {
  return overrides[agentId] || AGENTS[agentId].defaultName;
}
