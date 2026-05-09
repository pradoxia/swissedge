export type Status =
  | "monitor"
  | "not actionable"
  | "needs more work"
  | "candidate for further research";

export type SignalQuality = "high" | "medium" | "low" | "none";

export type StatusSlug =
  | "monitor"
  | "not-actionable"
  | "needs-work"
  | "candidate";

export const statusSlugByStatus: Record<Status, StatusSlug> = {
  monitor: "monitor",
  "not actionable": "not-actionable",
  "needs more work": "needs-work",
  "candidate for further research": "candidate",
};

export function getStatusSlug(status: Status): StatusSlug {
  return statusSlugByStatus[status];
}

export type ChecklistItem = {
  label: string;
  complete: boolean;
};

export type Article = typeof article;

export const article = {
  slug: "meridian-group-separation",
  title:
    "Meridian Group - Planned Separation of Industrial and Consumer Divisions",
  situationType: "CORPORATE SEPARATION",
  situationTypeLabel: "Corporate separation",
  status: "candidate for further research" as Status,
  statusSlug: getStatusSlug("candidate for further research"),
  publishedAt: "03 May 2026",
  reviewedAt: "03 May 2026",
  abstract:
    "A fictional public-company separation note showing how SwissEdge presents known facts, open questions, source quality, and risk factors without giving transaction instructions.",
  disciplineLabel: "Educational research - manually reviewed",
  thesis:
    "A fictional conglomerate has publicly announced an intention to separate two structurally distinct businesses; this note documents the available public evidence, the open questions, and the conditions that would alter the research status.",
  confidence: {
    level: 3,
    label: "Evidence accumulating",
    description: "Key documents reviewed - important questions remain open",
  },
  known: [
    "The board of Meridian Group announced on 14 February 2026 the intention to separate its Industrial Solutions division from its Consumer Products division into two independent public entities. The announcement was made through a public exchange notice on the same date. (Source: Exchange Notice, 14 February 2026.)",
    "A current report, filed concurrently, confirmed the formation of a three-member independent board committee to oversee the separation process. The report referenced completion in the second half of 2026, subject to regulatory and shareholder approvals, but did not specify individual milestone dates. (Source: Current Report, 14 February 2026, Section 2.1.)",
    "The annual proxy statement filed on 01 March 2026 contains amendments to executive compensation arrangements, including separation-contingent equity vesting provisions for three named officers. This is consistent with an ongoing formal separation process, while still requiring independent verification. (Source: Proxy Statement, 01 March 2026, Exhibit A.)",
  ],
  unknown: [
    "Whether a registration statement has been filed or is currently in preparation for the entity expected to become independent.",
    "Whether regulatory approval has been sought or is anticipated from any jurisdiction.",
    "How debt obligations and existing collective bargaining arrangements will be allocated between the two entities.",
    "Whether shareholder approval will be sought through a separate vote or whether the board has authority under its current charter to proceed without one.",
    "Whether the referenced second-half 2026 window remains operative given no specific milestone dates have been disclosed since February.",
  ],
  viewChange: {
    increase: [
      "Filing of a registration statement that begins a formal review period and provides detailed financial disclosure for the new entity.",
      "Announcement of specific separation milestone dates in a subsequent regulatory filing.",
      "Publication of a separation agreement document disclosing asset and liability allocation terms.",
    ],
    decrease: [
      "Regulatory filing disclosing suspension or cancellation of the announced separation plans.",
      "Filing indicating a material adverse change in business conditions that may prevent or indefinitely delay completion.",
      "Proxy update or board statement indicating that separation-contingent compensation provisions have been removed or restructured.",
    ],
  },
  documents: [
    {
      type: "EXCHANGE NOTICE",
      title: "Separation Announcement",
      date: "14 February 2026",
      signal: "high" as SignalQuality,
      href: "#documents",
    },
    {
      type: "CURRENT REPORT",
      title: "Board Committee Disclosure",
      date: "14 February 2026",
      signal: "high" as SignalQuality,
      href: "#documents",
    },
    {
      type: "PROXY STMT",
      title: "Executive Compensation Amendment",
      date: "01 March 2026",
      signal: "high" as SignalQuality,
      href: "#documents",
    },
    {
      type: "PRESS RELEASE",
      title: "Initial Announcement Coverage",
      date: "14 February 2026",
      signal: "medium" as SignalQuality,
      href: "#documents",
    },
  ],
  timeline: [
    {
      date: "14 Feb 2026",
      title: "Exchange notice",
      description: "Separation plan announced through a public notice.",
      state: "confirmed",
    },
    {
      date: "14 Feb 2026",
      title: "Committee formed",
      description: "Independent board committee disclosed in a public report.",
      state: "confirmed",
    },
    {
      date: "01 Mar 2026",
      title: "Proxy filed",
      description: "Compensation amendments described in the annual proxy.",
      state: "confirmed",
    },
    {
      date: "May 2026",
      title: "Monitoring",
      description: "Registration statement and milestone dates remain pending.",
      state: "current",
    },
  ],
  risks: [
    {
      label: "Announcement risk",
      text: "Separation announcements can be withdrawn or delayed. The public filing language indicates conditional dependencies that could prevent completion.",
    },
    {
      label: "Disclosure incompleteness",
      text: "The capital structure of each separated entity has not been disclosed. Assessment of the independent financial profile of each business from public information alone is not currently possible.",
    },
    {
      label: "Regulatory dependency",
      text: "No specific jurisdictions requiring approval have been named. If approvals are needed from multiple regulatory bodies, timeline extension risk increases without additional public disclosure.",
    },
    {
      label: "Timeline uncertainty",
      text: "Second half of 2026 is a wide window. No specific milestone dates have been publicly committed as of the most recent filing.",
    },
  ],
  sources: [
    {
      name: "Exchange Notice (Feb 2026)",
      category: "Primary regulatory",
      signal: "high" as SignalQuality,
      shows: "Announcement date",
    },
    {
      name: "Current Report (Feb 2026)",
      category: "Primary regulatory",
      signal: "high" as SignalQuality,
      shows: "Board structure",
    },
    {
      name: "Proxy Statement (Mar 2026)",
      category: "Company-issued",
      signal: "high" as SignalQuality,
      shows: "Compensation amendments",
    },
    {
      name: "Financial press (Feb 2026)",
      category: "Commentary",
      signal: "low" as SignalQuality,
      shows: "Market awareness",
    },
  ],
  checklist: [
    { label: "Primary sources cited", complete: true },
    { label: "Key risks documented", complete: true },
    { label: "Open questions listed", complete: true },
    { label: "View-change conditions included", complete: true },
    { label: "Sources evaluated for signal quality", complete: true },
    { label: "Manually reviewed before publication", complete: true },
    { label: "Educational disclaimer present", complete: true },
  ],
};

export const researchArchive = [
  {
    slug: article.slug,
    title: article.title,
    situationType: article.situationTypeLabel,
    status: article.status,
    statusSlug: article.statusSlug,
    abstract: article.abstract,
    publishedAt: article.publishedAt,
    reviewedAt: article.reviewedAt,
    disciplineLabel: article.disciplineLabel,
    href: `/research/${article.slug}`,
    available: true,
  },
  {
    slug: "sample-reorganization-note",
    title: "Sample Reorganization Note - Placeholder",
    situationType: "Reorganization",
    status: "needs more work" as Status,
    statusSlug: getStatusSlug("needs more work"),
    abstract:
      "Placeholder card for a future manually reviewed educational note. No real company, source, or private material is represented.",
    publishedAt: "Sample",
    reviewedAt: "Pending human review",
    disciplineLabel: "Sample placeholder - not a public article",
    href: "/research",
    available: false,
  },
  {
    slug: "sample-historical-case",
    title: "Sample Historical Case - Placeholder",
    situationType: "Historical reconstruction",
    status: "monitor" as Status,
    statusSlug: getStatusSlug("monitor"),
    abstract:
      "Placeholder card for a future educational case reconstruction focused on source discipline and uncertainty.",
    publishedAt: "Sample",
    reviewedAt: "Pending human review",
    disciplineLabel: "Sample placeholder - not a public article",
    href: "/research",
    available: false,
  },
];
