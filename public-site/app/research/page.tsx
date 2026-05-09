import Link from "next/link";
import { SiteFooter, SiteNav } from "@/components/SiteChrome";
import { researchArchive } from "@/data/article";

export default function ResearchIndexPage() {
  return (
    <main>
      <SiteNav />
      <section className="page-hero">
        <p className="eyebrow">PUBLIC RESEARCH ARCHIVE</p>
        <h1>Manually reviewed educational research notes.</h1>
        <p>
          A calm archive of SwissEdge public notes. Each published note is
          expected to show the research status, source discipline, open
          questions, risks, and a visible educational disclaimer.
        </p>
      </section>
      <section className="archive-shell" aria-label="Research notes">
        {researchArchive.map((item) => (
          <article
            className={`research-card ${item.available ? "" : "is-placeholder"}`}
            key={item.slug}
          >
            <div className="badge-row">
              <span className="badge badge-muted">{item.situationType}</span>
              <span className={`badge status status-${item.statusSlug}`}>
                {item.status}
              </span>
            </div>
            <h2>{item.title}</h2>
            <p>{item.abstract}</p>
            <dl className="card-meta">
              <div>
                <dt>Published</dt>
                <dd>{item.publishedAt}</dd>
              </div>
              <div>
                <dt>Reviewed</dt>
                <dd>{item.reviewedAt}</dd>
              </div>
            </dl>
            <p className="discipline-label">{item.disciplineLabel}</p>
            {item.available ? (
              <Link className="text-link" href={item.href}>
                Read note {">"}
              </Link>
            ) : (
              <span className="text-link muted-link">Static placeholder</span>
            )}
          </article>
        ))}
      </section>
      <SiteFooter />
    </main>
  );
}
