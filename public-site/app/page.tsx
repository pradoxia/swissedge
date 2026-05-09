import Link from "next/link";
import { SiteFooter, SiteNav } from "@/components/SiteChrome";
import { researchArchive } from "@/data/article";

export default function Home() {
  const featured = researchArchive[0];

  return (
    <main>
      <SiteNav />
      <section className="home-shell">
        <p className="eyebrow">SPECIAL SITUATIONS RESEARCH</p>
        <h1>SwissEdge research notes, plainly documented.</h1>
        <p className="home-copy">
          Public notes document structural corporate events through source
          evidence, open questions, review dates, and risk awareness. This
          static prototype uses fictional sample content only.
        </p>
        <div className="home-actions">
          <Link className="text-link" href="/research">
            View research archive {">"}
          </Link>
          <Link className="text-link muted-link" href="/methodology">
            Read methodology {">"}
          </Link>
        </div>
        <div className="home-feature" aria-label="Featured sample note">
          <p className="eyebrow">FEATURED SAMPLE NOTE</p>
          <h2>{featured.title}</h2>
          <p>{featured.abstract}</p>
          <Link href={featured.href}>Open note {">"}</Link>
        </div>
      </section>
      <section className="trust-band" id="source-discipline">
        <p>
          SwissEdge public articles are educational research documents. They
          show what is known, what remains unknown, what sources support the
          note, and what would change the research view after human review.
        </p>
      </section>
      <SiteFooter />
    </main>
  );
}
