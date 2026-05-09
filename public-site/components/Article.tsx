import type { Article, ChecklistItem, SignalQuality, Status } from "@/data/article";

const statusText: Record<Status, string> = {
  monitor: "● MONITOR",
  "not actionable": "○ NOT ACTIONABLE",
  "needs more work": "◐ NEEDS MORE WORK",
  "candidate for further research": "● CANDIDATE FOR FURTHER RESEARCH",
};

const signalText: Record<SignalQuality, string> = {
  high: "● HIGH",
  medium: "◐ MEDIUM",
  low: "○ LOW",
  none: "· NO SIGNAL",
};

export function ArticleHeader({ article }: { article: Article }) {
  return (
    <header className="article-header">
      <div className="badge-row">
        <span className="badge badge-muted">{article.situationType}</span>
        <span className={`badge status status-${article.statusSlug}`}>
          {statusText[article.status]}
        </span>
      </div>
      <h1>{article.title}</h1>
      <p className="thesis">
        <span>Thesis - </span>
        {article.thesis}
      </p>
      <p className="metadata">
        PUBLISHED {article.publishedAt} <span>·</span> REVIEWED{" "}
        {article.reviewedAt}
      </p>
      <ConfidenceIndicator article={article} />
    </header>
  );
}

export function ConfidenceIndicator({ article }: { article: Article }) {
  return (
    <div className={`confidence confidence-${article.confidence.level}`}>
      <div className="confidence-dots" aria-hidden="true">
        {[1, 2, 3, 4].map((dot) => (
          <span key={dot}>{dot <= article.confidence.level ? "●" : "○"}</span>
        ))}
      </div>
      <div>
        <strong>{article.confidence.label}</strong>
        <p>{article.confidence.description}</p>
      </div>
    </div>
  );
}

export function Section({
  eyebrow,
  title,
  children,
}: {
  eyebrow: string;
  title: string;
  children: React.ReactNode;
}) {
  return (
    <section className="article-section">
      <p className="section-eyebrow">{eyebrow}</p>
      <h2>{title}</h2>
      {children}
    </section>
  );
}

export function KeyDocuments({ documents }: { documents: Article["documents"] }) {
  return (
    <div className="document-list" id="documents">
      {documents.map((document) => (
        <a className="document-row" href={document.href} key={document.title}>
          <span className="doc-type">{document.type}</span>
          <span>
            <strong>{document.title}</strong>
            <small>{document.date}</small>
          </span>
          <span className={`signal signal-${document.signal}`}>
            {signalText[document.signal]}
          </span>
        </a>
      ))}
    </div>
  );
}

export function Timeline({ events }: { events: Article["timeline"] }) {
  return (
    <ol className="timeline" aria-label="Research timeline">
      {events.map((event) => (
        <li className={`timeline-item timeline-${event.state}`} key={event.date}>
          <span className="timeline-node" aria-hidden="true" />
          <time>{event.date}</time>
          <strong>{event.title}</strong>
          <p>{event.description}</p>
        </li>
      ))}
    </ol>
  );
}

export function RisksSection({ risks }: { risks: Article["risks"] }) {
  return (
    <>
      {risks.map((risk) => (
        <p key={risk.label}>
          <strong>{risk.label}.</strong> {risk.text}
        </p>
      ))}
    </>
  );
}

export function SourceNotes({ sources }: { sources: Article["sources"] }) {
  return (
    <div className="source-table" role="table" aria-label="Source notes">
      <div className="source-row source-head" role="row">
        <span role="columnheader">Source</span>
        <span role="columnheader">Category</span>
        <span role="columnheader">Signal</span>
        <span role="columnheader">What It Shows</span>
      </div>
      {sources.map((source) => (
        <div className="source-row" role="row" key={source.name}>
          <span role="cell">{source.name}</span>
          <span role="cell">{source.category}</span>
          <span className={`signal signal-${source.signal}`} role="cell">
            {signalText[source.signal]}
          </span>
          <span role="cell">{source.shows}</span>
        </div>
      ))}
    </div>
  );
}

export function CoverageChecklist({
  checklist,
}: {
  checklist: ChecklistItem[];
}) {
  return (
    <section className="checklist-panel" aria-labelledby="coverage-title">
      <p className="eyebrow" id="coverage-title">
        COVERAGE
      </p>
      <ul>
        {checklist.map((item) => (
          <li key={item.label}>
            <span aria-hidden="true">{item.complete ? "✓" : "○"}</span>
            {item.label}
          </li>
        ))}
      </ul>
    </section>
  );
}

export function DisclaimerBlock({ full = false }: { full?: boolean }) {
  return (
    <section className={full ? "disclaimer disclaimer-full" : "disclaimer"}>
      <p className="eyebrow">EDUCATIONAL DISCLAIMER</p>
      <p>
        This analysis is published for educational and informational purposes
        only. Nothing in this note is financial advice, transaction
        instruction, or an offer of any kind. Research notes document a process
        of analysis and reflect information available at the time of writing.
      </p>
      <p>
        <em>Este análisis es educativo. No es asesoramiento financiero.</em>
      </p>
    </section>
  );
}

export function ResearchSidebar({ article }: { article: Article }) {
  return (
    <aside className="article-sidebar" aria-label="Article summary">
      <section className="sidebar-panel">
        <p className="eyebrow">RESEARCH STATUS</p>
        <dl>
          <dt>Status</dt>
          <dd>{article.status}</dd>
          <dt>Situation Type</dt>
          <dd>{article.situationTypeLabel}</dd>
          <dt>Published</dt>
          <dd>{article.publishedAt}</dd>
          <dt>Last Reviewed</dt>
          <dd>{article.reviewedAt}</dd>
        </dl>
      </section>
      <CoverageChecklist checklist={article.checklist} />
      <DisclaimerBlock />
    </aside>
  );
}
