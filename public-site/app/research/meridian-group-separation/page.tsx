import {
  ArticleHeader,
  CoverageChecklist,
  DisclaimerBlock,
  KeyDocuments,
  ResearchSidebar,
  RisksSection,
  Section,
  SourceNotes,
  Timeline,
} from "@/components/Article";
import { ReadingProgress, SiteFooter, SiteNav } from "@/components/SiteChrome";
import { article } from "@/data/article";

export default function ArticlePage() {
  return (
    <main>
      <ReadingProgress />
      <SiteNav />
      <div className="article-layout">
        <article className="article-column">
          <a className="breadcrumb" href="/research">
            {"<-"} Research
          </a>
          <ArticleHeader article={article} />
          <div className="mobile-only">
            <CoverageChecklist checklist={article.checklist} />
            <DisclaimerBlock />
          </div>
          <Section eyebrow="01 / KNOWN" title="What Is Known">
            {article.known.map((paragraph) => (
              <p key={paragraph}>{paragraph}</p>
            ))}
          </Section>
          <Section eyebrow="02 / UNKNOWN" title="What Is Unknown">
            <ul className="dash-list">
              {article.unknown.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </Section>
          <Section
            eyebrow="03 / VIEW"
            title="What Would Change This Research View"
          >
            <h3 className="subhead">What would increase research interest:</h3>
            <ul className="dash-list">
              {article.viewChange.increase.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
            <h3 className="subhead">What would decrease research interest:</h3>
            <ul className="dash-list">
              {article.viewChange.decrease.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </Section>
          <Section eyebrow="04 / DOCUMENTS" title="Key Documents">
            <KeyDocuments documents={article.documents} />
          </Section>
          <Section eyebrow="05 / TIMELINE" title="Timeline">
            <Timeline events={article.timeline} />
          </Section>
          <Section eyebrow="06 / RISKS" title="Risks">
            <RisksSection risks={article.risks} />
          </Section>
          <Section eyebrow="07 / SOURCES" title="Source Notes">
            <SourceNotes sources={article.sources} />
          </Section>
          <DisclaimerBlock full />
          <section className="newsletter-panel" aria-labelledby="newsletter-title">
            <p className="eyebrow">RESEARCH NOTES</p>
            <h2 id="newsletter-title">
              Research notes when something is worth documenting.
            </h2>
            <p>
              No tips. No signals. When a situation warrants a structured note,
              SwissEdge publishes the process and sources in plain language.
            </p>
            <a className="mono-button" href="/methodology">
              Read methodology {">"}
            </a>
          </section>
        </article>
        <ResearchSidebar article={article} />
      </div>
      <SiteFooter />
    </main>
  );
}
