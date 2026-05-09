import { SiteFooter, SiteNav } from "@/components/SiteChrome";

const principles = [
  {
    title: "Educational research, not financial advice",
    body: "Public SwissEdge articles explain a research process. They are written to help readers understand source evidence, uncertainty, and risk, not to direct transactions.",
  },
  {
    title: "Manual review before public use",
    body: "A public article should appear only after a human editor checks the title, body, sources, risk language, checklist, and disclaimer.",
  },
  {
    title: "Source discipline",
    body: "Primary regulatory documents and company-issued materials carry the most weight for factual claims. Commentary can add context, but it does not replace primary evidence.",
  },
  {
    title: "Known and unknown are both visible",
    body: "Each article separates confirmed public facts from open research questions. A note without unknowns is too confident for this format.",
  },
  {
    title: "Uncertainty is explicit",
    body: "Status labels and confidence indicators describe the state of public evidence. They do not predict outcomes.",
  },
  {
    title: "No transaction-direction language",
    body: "SwissEdge public pages avoid language that tells a reader what to do with any security. The complete vocabulary is research status, source quality, risk, and open questions.",
  },
  {
    title: "Risks and checklist are part of the article",
    body: "Risks are presented in the same calm voice as the rest of the note. The checklist makes review coverage visible without turning the page into a private dashboard.",
  },
  {
    title: "Public articles are separate from internal research",
    body: "The public site receives only sanitized, educational copy. Internal notes, private identifiers, operational metadata, and unpublished material do not belong on public pages.",
  },
];

export default function MethodologyPage() {
  return (
    <main>
      <SiteNav />
      <section className="page-hero methodology-hero">
        <p className="eyebrow">METHODOLOGY</p>
        <h1>How to read SwissEdge public research.</h1>
        <p>
          SwissEdge public articles are structured research documents. The page
          design is intentionally quiet: status first, evidence next, unknowns
          made visible, and the educational disclaimer always close at hand.
        </p>
      </section>
      <section className="methodology-grid" aria-label="Research principles">
        {principles.map((principle, index) => (
          <article className="method-card" key={principle.title}>
            <p className="section-eyebrow">
              {String(index + 1).padStart(2, "0")} / PRINCIPLE
            </p>
            <h2>{principle.title}</h2>
            <p>{principle.body}</p>
          </article>
        ))}
      </section>
      <section className="trust-band methodology-note">
        <p>
          Canonical disclaimer: Este análisis es educativo. No es asesoramiento
          financiero. This public prototype is static and uses fictional sample
          content only.
        </p>
      </section>
      <SiteFooter />
    </main>
  );
}
