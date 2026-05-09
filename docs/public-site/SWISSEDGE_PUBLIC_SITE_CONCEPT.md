# SwissEdge — Public Website Concept
## Brand, Experience & Information Architecture

> Design specification only. No code. No implementation. No deployment.
> Last updated: 2026-05-03

---

## 1. Brand Positioning

### What SwissEdge Is

SwissEdge is an independent investment research practice focused on special situations: corporate events, restructurings, spin-offs, mergers, and other structural catalysts that create temporary pricing dislocations.

The work is methodical. It follows primary sources — regulatory filings, board announcements, court documents, proxy statements — and builds research cases through structured analysis, not news reaction.

The public face of SwissEdge is educational. It shares how situations are identified, how they are evaluated, what sources matter, and what questions remain open. It does not advise. It does not predict. It documents the process of serious research and invites others who work the same way to engage.

### What It Is Not

- Not a newsletter promising alpha or edge.
- Not a stock-picking service or subscription signal.
- Not financial advice, ever, in any form.
- Not crypto, not day-trading, not momentum speculation.
- Not a community of influencers or "investors on Twitter."
- Not a platform claiming to know outcomes before they happen.

### Why It Exists

Most public investment writing optimizes for confidence and entertainment. SwissEdge is built around the opposite: structured uncertainty, source discipline, and the humility to say "we don't know yet."

Special situations research is methodical by nature. Regulatory filings exist. Timelines can be reconstructed. Sources can be evaluated for reliability. That process can be shared transparently — and sharing it is itself educational.

The public site exists to demonstrate that serious research has a process, and to connect with others who share that instinct.

### Who It Is For

- Independent investors who read regulatory filings as primary research.
- Analysts and researchers interested in special situations methodology.
- Students of value investing and event-driven strategies.
- Anyone frustrated with confident-sounding investment content and looking for honest process documentation.

Not for: people seeking trade signals, performance records, or specific investment recommendations.

---

## 2. Trust Principles

### Research-First

Every public piece begins with a question, not a conclusion. The visible structure of inquiry — what we looked at, what we found, what remains open — is itself the product. Conclusions are provisional.

### Source-Driven

Public research cites its origins. Primary documents, regulatory filings, company announcements, and named public sources are referenced explicitly. "We believe" is always followed by "because we found." Source quality is noted, not hidden.

### Transparent Uncertainty

The status of every research note is labeled honestly:

| Status | Meaning |
|--------|---------|
| `monitor` | Worth watching; no structural catalyst confirmed |
| `not actionable` | Interesting situation, but insufficient information to evaluate |
| `needs more work` | Research in progress; open questions remain |
| `candidate for further research` | Situation merits deeper investigation; not a recommendation |

These labels are final. The site does not use "buy," "sell," "strong conviction," "target price," or equivalent language.

### No Hype

No performance claims. No implied returns. No "our approach generates X%." The credibility is in the process, not the outcome.

### Manual Review

No content is published automatically. Every public research note is reviewed by a human before it appears. The pipeline includes explicit disclaimer and safety checks. Errors are corrected publicly.

### Educational Only

All content is framed as educational documentation of a research process. The site carries a permanent, canonical disclaimer:

> *Este análisis es educativo. No es asesoramiento financiero.*
> *This analysis is educational. It is not financial advice.*

---

## 3. Visual Direction

### Philosophy: Institutional Research Meets Modern AI Lab

The visual language should feel like an analyst's research desk at a serious private research firm — digital, quiet, focused. Not a trading terminal. Not a hedge fund marketing site. Not crypto.

The closest analogy: if you could walk into the room where careful research happens at midnight, this is what the walls look like.

### Color System

**Background:** Near-black. `#0A0B0D` base — not pure black, which reads as software/gaming. A very slightly warm charcoal that suggests paper under dim desk light.

**Surface layers:**
- Primary surface: `#0F1114` — document card background
- Secondary surface: `#14171C` — panel, sidebar
- Border: `#1E2229` — 1px rule, grid lines, separator

**Accent — one color only:**
- Emerald-teal: `#34D399` to `#10B981` range — the single color of active, live, or reviewed content
- Used sparingly: status indicators, active labels, confirmed research notes
- Not used for decoration, buttons, or backgrounds

**Typography color:**
- Primary: `#E8EAF0` — off-white, slightly blue-tinted. More readable than pure white on dark.
- Secondary: `#6B7280` — section labels, metadata, timestamps
- Tertiary: `#374151` — ghost text, placeholders

**Warning/caution:**
- `#F59E0B` amber — used only for "needs more work" status and disclaimers. Never for marketing.

### Typography

- **Headline:** A modern geometric serif — something with the weight of a financial editorial. Think: GT Alpina, Canela, or Tiempos Headline. Not Times New Roman, not a slab serif. A literary serif with structural intelligence.
- **Body:** A clean humanist sans — Söhne, Inter, or IBM Plex Sans. Dense and legible at small sizes. Feels like a research document, not a marketing page.
- **Monospace accents:** JetBrains Mono or IBM Plex Mono — used for status labels, source codes, timestamps, data fields, and metadata. This is the "research terminal" layer of the type system.

### Layout

- Maximum content width: 1200px. Never full bleed text.
- Generous vertical rhythm. Sections breathe. Nothing feels crammed.
- Editorial grid: 12-column at desktop, article column 7/12 max, sidebar 3/12.
- Research cards: equal-height, monochromatic, hover border-glow only.
- Data tables: flush left, no zebra striping — hairline row borders only.

### Motifs

**Data-grid subtext:** Very faint background grid — 1px lines at 32px intervals, 3–5% opacity. Suggests structured intelligence without being a "matrix effect."

**Radar / Intelligence ring:** On the homepage hero, a very slow-rotating concentric ring pattern — like a research radar or satellite signal map. 8% opacity, 6 rpm, blurred. Positioned behind hero text. No flashing. No bright colors.

**Document-stack shadows:** Research cards can have a subtle stacked-paper shadow — 3 layers at 45° offset, getting lighter and smaller. Implies depth of research, not UI decoration.

**Source graph:** On the Source Intelligence page, a slow node graph showing source categories and their relationships. Nodes are labeled. No live data, no specific source names from internal systems. Static or gently animated.

### Animation Budget

- Entrance animations: fade-in + 4px upward slide, 300ms ease-out. Once per page load. Never on scroll-repeat.
- Hover states: border glow (emerald, 40% opacity), 150ms. That is all.
- The research radar: continuous rotation, imperceptibly slow.
- Everything else: static.

No parallax. No scroll-jacking. No particle systems. No cursor effects. No loading spinners beyond a single opacity pulse.

---

## 4. Design References by Mood

These are mood references only — not visual copies.

| Reference | What to borrow |
|-----------|---------------|
| **Bloomberg Terminal** | Information density, monospace data layers, seriousness |
| **Stripe / Linear** | Modern product clarity, typographic confidence, whitespace discipline |
| **Substack** | Editorial readability, article template simplicity, author credibility framing |
| **Are.na** | Calm curatorial aesthetic, research-board feel |
| **McKinsey / BCG microsite** | Professional restraint, no flashy elements, document-like layouts |
| **Palantir's public site** | Intelligence-desk aesthetic — without the defense-contractor messaging |
| **FT / The Economist** | Editorial trustworthiness, dense information, serif headline authority |

**Hard avoids:**

| What to avoid | Why |
|---------------|-----|
| Crypto/DeFi aesthetic | Dark + neon + hype = association with speculation |
| Day-trading platforms | Tick-by-tick urgency reads as gambling |
| "Guru" newsletter landing pages | Big claims, bold testimonials, urgency CTAs |
| SaaS startup minimalism | Too casual, too "product" — not research |
| Wall Street marketing sites | Gold and marble motifs, aggressive authority posture |

---

## 5. Site Information Architecture

### Primary Navigation

```
SwissEdge
├── Research          → Published research notes (approved, educational)
├── Case Studies      → Historical situation reconstructions
├── Source Intelligence → How sources are evaluated and used
├── Methodology       → How SwissEdge approaches special situations
├── About             → Who we are and why we do this
├── Notes             → Newsletter / Substack community
└── Disclaimer        → Legal, educational-only language
```

### URL Pattern

```
swissedge.com/
swissedge.com/research/
swissedge.com/research/[slug]/
swissedge.com/case-studies/
swissedge.com/case-studies/[slug]/
swissedge.com/source-intelligence/
swissedge.com/methodology/
swissedge.com/about/
swissedge.com/notes/
swissedge.com/disclaimer/
```

### Navigation Behavior

- Sticky top navbar, dark background, no shadow — just a 1px bottom border.
- Logo left: `SwissEdge` wordmark, serif, small caps. No icon needed yet.
- Nav links right: regular weight, tracking-wide, small caps monospace.
- "Notes" link has a subtle indicator dot when new content is available.
- No mega-menus. No dropdowns. Flat and fast.
- Mobile: hamburger that slides in a full-screen panel. Same hierarchy.

---

## 6. Homepage Structure

### Section 1 — Hero

**Purpose:** Establish tone, seriousness, and what SwissEdge actually is in 4 seconds.

**Layout:** Full-viewport height. Left-aligned text. Right side: the slow research radar animation. Very dark.

**Content:**
- Eyebrow label (monospace, amber): `SPECIAL SITUATIONS RESEARCH`
- Headline (serif, large): The actual work, not the pitch.
- Subheadline (sans, secondary color): 2 sentences maximum.
- Single CTA: `Read the Research →` — no urgency, no offer.
- Bottom strip: 3 live stats (monospace): `N research notes published · N case studies · Last updated: [date]`

**No:** countdown timers, sign-up popups, "join X members" social proof.

---

### Section 2 — Trust Statement

**Purpose:** Immediate anchoring of what this is not and what it is.

**Layout:** Full-width, centered, constrained to 700px. Large editorial text. Generous padding.

**Content:** A single paragraph. Calm, declarative. No bullet points. Written like a journal preface, not a landing page.

---

### Section 3 — What SwissEdge Researches

**Purpose:** Orient unfamiliar visitors to "special situations" without being condescending.

**Layout:** 3-column grid of category cards.

**Cards:**
1. Spin-offs & Separations
2. Mergers & Reorganizations
3. Distress & Restructuring

Each card: icon (line-drawn, minimal), category name (serif), 2-sentence description, monospace "status frequency" stat.

---

### Section 4 — Latest Research Notes

**Purpose:** Show the actual work. Recent approved research cards.

**Layout:** 2-column card grid. Cards are editorial, dense, no images.

**Card anatomy:**
- Status badge (monospace, colored by status)
- Situation type (small caps)
- Title (serif, 1–2 lines)
- One-line thesis
- Publication date
- "Read note →" link

**Max:** 4 cards on homepage. "View all research →" link below.

---

### Section 5 — Special Situations Explained

**Purpose:** Educational credibility. Show structural knowledge.

**Layout:** Alternating text/data panel rows. 2 rows maximum on homepage.

**Content:**
- What makes a situation "special"
- Why structural events can create temporary information imbalances
- A simplified timeline diagram of how a spin-off unfolds

**No investment advice framing.** Written as process explanation.

---

### Section 6 — Source Intelligence Angle

**Purpose:** Differentiate. Source discipline is SwissEdge's distinctive quality.

**Layout:** Dark card, full-width. Left: text. Right: the slow static source-graph visualization.

**Content:**
- How sources are categorized (primary documents, regulatory filings, company announcements, secondary commentary)
- Signal quality framework (high / medium / low / no signal)
- The principle: primary sources first, secondary commentary last

---

### Section 7 — Historical Case Learning

**Purpose:** Demonstrate that SwissEdge learns from past situations.

**Layout:** Horizontal scroll of 3 historical case preview cards. Simple. No images.

**Card anatomy:**
- Company name
- Situation type
- Approximate date
- One-line lesson
- "Read case study →"

---

### Section 8 — Newsletter / Community CTA

**Purpose:** Invite thoughtful subscribers. No urgency. No promises.

**Layout:** Centered, generous padding, dark panel.

**Content:**
- Headline: calm invitation
- 2-sentence description of what notes contain
- Email input + "Subscribe" button — or redirect to Substack
- Trust line: "No tips. No signals. Research process only."

---

### Section 9 — Disclaimer / Footer

**Purpose:** Legal clarity. Permanent, visible, not buried.

**Layout:** Dark footer. 3-column: nav links / legal text / source note.

**Disclaimer text (always visible):**
> All content on SwissEdge is educational and for informational purposes only. Nothing on this site constitutes financial advice, investment recommendations, or an offer to buy or sell any security. Research notes document a process of analysis and should not be relied upon for any investment decision. SwissEdge does not manage money, does not accept client funds, and does not provide regulated financial services.

---

## 7. Research Article Template

### Page Structure

```
[Back to Research] ← breadcrumb

[SITUATION TYPE] · [STATUS BADGE]

# Title: Company Name — The Structural Event

**One-line thesis:** What the situation is and why it may warrant research attention.

---
Published: [date]   Last reviewed: [date]   Readiness: [status label]
---

## Overview
[3–5 sentence summary of the situation]

## Why This Situation May Be Interesting
[Structural reasons — not price predictions]

## Key Documents
[List of public filings, regulatory documents — all publicly accessible URLs]

## Timeline
[Chronological events — structured table or timeline component]

## Key Risks
[What could make this situation less interesting than it appears]

## Open Research Questions
[What we still don't know / what would need to be verified]

## Sources We Followed
[Named public sources and their signal quality]

## What Would Change This View
[Specific observable events that would raise or lower research interest]

---
**Educational Disclaimer**
Este análisis es educativo. No es asesoramiento financiero.
This analysis is educational. It is not financial advice. Nothing in this note constitutes a recommendation to buy, sell, or hold any security.
```

### Template Rules

- No first-person plural ("we think you should").
- No performance claims in any context.
- Status badge is the first visual element after the title.
- Timeline is always sourced — each event linked to a public document.
- "Open research questions" must be present in every note. A note without open questions is overconfident.
- Disclaimer is typeset, not hidden in a footer.

---

## 8. Case Study Template

### Page Structure

```
[Back to Case Studies] ← breadcrumb

[HISTORICAL]  [SITUATION TYPE]

# Case Study: Company — Situation Type (Approximate Year)

**What happened:** [One paragraph, factual, past tense]

---

## When the Situation Became Visible
[At what point a research-oriented investor might have begun tracking this]
[What the first observable signal was]

## Which Sources Mattered
[A structured list of source types and what they revealed]

| Source | What It Showed | Signal Quality |
|--------|---------------|----------------|
| Regulatory filing | Separation timeline | High |
| Proxy statement | Management incentive structure | High |
| Trade publication | Market positioning context | Medium |

## What Signals Were Useful
[Structured analysis of information quality at the time]

## What Was Missed or Unknown
[Honest accounting of gaps in analysis — this is required]

## Lessons for Future Research
[3–5 specific, generalizable lessons as bullet points]

## How This Informs SwissEdge Methodology
[How this case shaped our framework — not investment advice]

---
**Educational Disclaimer**
Este análisis es educativo. No es asesoramiento financiero.
This case study is a reconstruction for educational purposes. It does not constitute investment advice and does not represent investment performance.
```

### Template Rules

- Always past tense. Always "happened," never "will happen."
- Outcome is not described in terms of price movement — only in structural terms (separation completed, merger failed, plan abandoned).
- "What was missed" is mandatory. Perfect hindsight is intellectually dishonest.
- No percentage returns, no NAV references, no personal performance claims.

---

## 9. Source Intelligence Page

### Purpose

Explain the SwissEdge approach to source evaluation without exposing any internal source lists, signal databases, or operational metadata.

### Page Structure

```
# Source Intelligence

Methodology for how we identify, evaluate, and track information sources
relevant to special situations research.

---

## Source Categories

[Explained through four panels:]

1. PRIMARY REGULATORY SOURCES
   What: SEC filings, court documents, regulatory approvals, exchange notices
   Why: Legally mandated, timestamped, difficult to manipulate
   Signal quality: Consistently high for factual claims

2. COMPANY-ISSUED DOCUMENTS
   What: Press releases, investor presentations, proxy statements, annual reports
   Why: Authoritative for company intent; requires reading for management framing
   Signal quality: High for facts; requires judgment on spin

3. INDEPENDENT ANALYSIS
   What: Academic papers, independent research publications, think-tank reports
   Why: Provides framework and precedent; slower to update
   Signal quality: Variable; methodology must be assessed

4. SECONDARY COMMENTARY
   What: Financial press, analyst notes, community discussion
   Why: Useful for identifying what others are watching; unreliable for primary facts
   Signal quality: Low for facts; medium for market awareness

---

## Signal Quality Framework

| Rating | Meaning |
|--------|---------|
| High | Primary document; legally sourced; timestamped |
| Medium | Derived analysis; requires primary source verification |
| Low | Opinion or commentary; indicative only |
| No signal | Present in research but not yet evaluated |

---

## What Source Intelligence Is Not

- Not a list of "edge" data providers
- Not insider information
- Not a proprietary feed or live signal
- Not advice on which sources to subscribe to

All sources referenced in SwissEdge research are publicly accessible.

---

## Why Source Discipline Matters

[2–3 paragraphs on the epistemic value of source tracking in special situations:
why primary sources are more reliable, how secondary commentary introduces noise,
why source confidence decays over time]
```

---

## 10. Community / Newsletter Angle

### Philosophy

SwissEdge does not have a "community" in the social-media sense. It has readers — people who take the same methodical approach and want to see how the research develops.

The public presence invites:
- **Thoughtful investors** who read filings and want structured analysis companions
- **Special situations readers** interested in the methodology, not the tips
- **Source contributors** who know a specific domain well and want to share context
- **Process learners** who want to understand how this kind of research actually works

### Substack as First Distribution Layer

Before a standalone CMS exists, Substack is the appropriate first channel:
- Editorial by default
- Subscriber trust model, not follower model
- Clean reading experience
- No algorithmic amplification
- The email list is owned

**What goes in Substack notes:**
- New research notes (already reviewed, fully disclaimed)
- Process posts: "how we approached this situation type"
- Source deep-dives: "why proxy statements matter for this category"
- Historical case studies
- Methodology updates

**What never goes in Substack notes:**
- Trade signals or timing suggestions
- Performance updates
- "You should look at X before it moves"

### Community CTA Design

The newsletter invite on the public site should feel like an invitation to a reading group, not a funnel.

**Framing options:**

> "Research notes, not tips. We publish when something is worth documenting — not on a schedule."

> "If you read the filings, you'll understand the notes. If you're learning to, they'll help."

> "No predictions. No signals. Process and sources, plainly written."

The subscribe button should say: `Subscribe to Notes →`
Not: "Get Free Alpha," "Join the Community," "Don't Miss Out."

---

## 11. Tone of Voice

### Writing Principles

**Concise.** Every sentence does one thing. No padding. No hedging with extra words when simple is available.

**Analytical.** Structured, not stream-of-consciousness. Headers, lists, and tables serve the reader. Analysis is built up piece by piece.

**Transparent.** Say what you don't know. Say what the source is. Say what would change the view. Transparency is the trust signal — not confidence.

**Humble.** We don't know how situations resolve. We document what we found and what remains open. "We believe" is always provisional.

**No hype.** Avoid: "exciting," "incredible," "can't miss," "unique opportunity," "massive," "game-changing." These words exist in financial marketing. They don't exist here.

**No certainty theater.** Saying "clearly" or "obviously" when something is genuinely contested is intellectually dishonest. Label uncertainty as uncertainty.

**No aggressive finance language.** Not: "this one's a strong buy." Not: "the market is wrong about this." Not: "smart money knows." Not: "here's your edge."

### Voice Examples

| Instead of this | Write this |
|----------------|------------|
| "This is a must-watch situation" | "This situation warrants continued monitoring" |
| "Strong buy signal from the proxy" | "The proxy statement contains language consistent with an asset sale; further verification required" |
| "Everyone's missing this" | "This has received limited coverage in financial press to date" |
| "Our proprietary model says..." | "Our analysis of the filing timeline suggests..." |
| "Trust the process" | "The methodology is documented below" |

### Sentence Structure

- Prefer active voice. "The board announced" not "an announcement was made."
- Short sentences for key claims. Long sentences for qualified analysis.
- When a claim is uncertain: say so inline. "As of the most recent filing — subject to revision upon the anticipated proxy release — the timeline appears to be Q3."

---

## 12. Example Homepage Copy

### Hero Headline

> **Special situations research, plainly documented.**

### Subheadline

> We track structural corporate events — spin-offs, reorganizations, distressed situations — and document the research process: what sources matter, what questions remain open, and what we still don't know.

### Feature Card 1 — Research Notes

**Label (monospace):** `PUBLISHED RESEARCH`

**Headline:** Process over prediction.

**Body:** Each note documents a situation in progress: the source evidence, the open questions, and the research status. Educational only. No recommendations.

---

### Feature Card 2 — Case Studies

**Label (monospace):** `HISTORICAL CASES`

**Headline:** What we learned after the fact.

**Body:** Reconstructed case studies of completed situations. What became visible early, which sources mattered, and what was missed. Honest retrospectives.

---

### Feature Card 3 — Source Intelligence

**Label (monospace):** `SOURCE METHODOLOGY`

**Headline:** Primary sources first.

**Body:** Special situations research requires source discipline. We document the evidence chain — regulatory filings, proxy statements, court documents — and note the quality of each source.

---

### Newsletter CTA

**Headline:** Research notes when something is worth documenting.

**Body:** No tips. No signals. When a situation merits a structured note, we publish one. Subscribers get the full document.

**Button:** `Subscribe to Notes →`

**Trust line (small, monospace):** Free. No spam. Unsubscribe anytime.

---

### Disclaimer Footer

> All content on SwissEdge is published for educational and informational purposes only. Nothing here constitutes financial advice, a recommendation to buy or sell any security, or an offer of any kind. Research notes document a process of analysis and reflect the information available at the time of writing. SwissEdge does not manage external capital, does not provide regulated financial services, and does not accept investment mandates.
>
> *Este análisis es educativo. No es asesoramiento financiero.*

---

## 13. UX "Wow" Ideas

These are tasteful, restrained, and purposeful. None are decorative noise.

### The Research Radar (Hero Background)
A very slow-rotating concentric ring — like a signal radar or satellite dish sweep. 3 rings, 1px stroke, `#34D399` at 6% opacity. Rotation: 1 full turn per 60 seconds. Blur: 4px. Positioned centered-right behind hero text. Communicates: "something is being tracked."

### Source Graph Visualization (Source Intelligence Page)
A static or gently animated force-directed graph showing source categories (not specific sources) as labeled nodes connected by weighted edges. Nodes: regulatory, company-issued, independent, commentary. Edge weight = typical signal quality relationship. Slow breathing animation: nodes pulse at 0.3 opacity amplitude, 3s interval. Built with D3 or a lightweight canvas renderer. No live data. Purely illustrative.

### Research Timeline Component (Article Pages)
On each research note, a horizontal scrollable timeline component. Events are plotted as nodes on a horizontal axis. Hovering a node expands a small card with event date, description, and source link. The rightmost node is always labeled "Current" and pulses very slowly with a green ring. Conveys: the situation is ongoing and being tracked.

### Document Stack Hover Cards (Research List Page)
Research cards on the list page have a hover state that reveals a document-stack effect: 2 ghost cards emerge behind the hovered card at slight offsets, suggesting "depth of research" behind the visible summary. The effect is CSS-only, 200ms transition. No animation libraries needed.

### Case Study Intelligence Map (Case Study Pages)
On historical case pages, a small network diagram showing the source types used in the case and how they connected. Not interactive — just illustrative. Rendered as SVG inline. Source nodes are connected to "claim nodes" (key findings). Makes the evidence chain visual without exposing any private infrastructure.

### Subtle AI-Lab Glow (Status Indicators)
Approved research notes carry a very subtle emerald glow on their status badge: a 0px 0px 8px `#10B981` box-shadow at 40% opacity, pulsing at 4s interval, 0.6→1.0 opacity. This communicates "this has been reviewed and is live" without being garish. Only `approved` status gets the glow. `monitor` and `needs more work` badges are static.

### Dark Editorial Cards with Hairline Borders
Research cards use a 1px border at `#1E2229` at rest. On hover: border transitions to `#10B981` at 30% opacity over 150ms. No color fill change. No scale transform. Just the border brightens. The effect is subtle enough that you feel it before you see it.

### Reading Progress (Article Pages)
A 1px emerald line at the very top of the browser window grows from left to right as the reader scrolls through a research note. Width = scroll percentage. No text label. No percentage counter. Just the line. It resets when navigating away.

**What we explicitly do not build:**
- Cursor trails or custom cursors
- Particle systems or starfield backgrounds
- Scroll-jacked sections or horizontal scroll carousels (except the historical cases carousel, which is native overflow-x)
- Loading screens or splash pages
- Sound effects or haptic feedback triggers
- Auto-playing video or ambient audio

---

## 14. Implementation Recommendation

### Phase 1 — Substack First (Now)

Before any public website code exists, use Substack as the distribution layer.

- Set up a SwissEdge Substack publication with dark mode styling.
- Migrate the approved PublicArticleDraft markdown content to Substack manually.
- Use Substack for email list building, community discussion, and reader credibility.
- This costs zero engineering time and builds an audience before the website exists.

### Phase 2 — Separate Public Next.js App (Later)

The public website should be a **completely separate application** from the private Mission Control platform.

- Different repository, different deployment, different domain.
- No shared authentication, no shared API keys, no shared infrastructure visible to the public.
- Content is sourced from manually approved PublicArticleDraft records, exported as static markdown files or fetched through a minimal read-only public API.
- No write endpoints are exposed publicly.

**Recommended stack for public site:**
- Next.js (App Router) with static generation (`generateStaticParams`)
- Content from markdown files (exported from the private approval pipeline) or a headless CMS (Sanity, Contentlayer)
- Tailwind CSS — the visual system described above is implementable in Tailwind
- Framer Motion for the entrance animations and glow effects (minimal)
- D3.js (lightweight import) for the source graph and timeline
- Vercel or Cloudflare Pages for deployment

### Phase 3 — Content API Bridge (Optional)

If the private approval pipeline matures, a minimal read-only API endpoint can serve approved, sanitized PublicArticleDraft content to the public site. This allows the site to update when new content is approved without manual file exports.

**This bridge must:**
- Expose only `approved` status drafts
- Expose only public-safe fields (title, content, readiness_label, disclaimer, created_at, approved_at)
- Never expose: research_case_id, situation_id, run_id, internal tags, or any operational metadata

### Deployment Separation Principle

> The public website should not know that the private platform exists.
> The private platform should not care that the public website exists.
> They share content, not infrastructure.

---

## 15. Risks and What to Avoid

| Risk | Description | Mitigation |
|------|-------------|------------|
| **Sounding like financial advice** | Any language that implies a recommended action | Permanent disclaimer; status-only labels; editorial review before publish |
| **Exposing private/internal data** | Research case IDs, scanner results, internal source names, API paths | Sanitization pipeline; strict field whitelist on public API |
| **Overpromising returns** | Any mention of past performance, strategy returns, or "edge" | Hard editorial rule: performance language is never permitted |
| **Looking like crypto / trading hype** | Dark aesthetic + bold claims = wrong association | Visual direction explicitly avoids neon, urgency, and speculation framing |
| **Publishing too early** | Releasing notes before the editorial pipeline is solid | Manual approval gate; minimum viability is one good case study, not many weak ones |
| **SEO spam** | Publishing keyword-stuffed research notes for traffic | Quality-first publishing; fewer, better notes; no programmatic content generation |
| **Too much AI branding** | "AI-powered research" in the hero | AI is a tool in the process, not the product. Never lead with "AI." |
| **Subscriber confusion** | People subscribing expecting stock tips | Very clear positioning in every onboarding email and about page |
| **Speed over quality** | Rushing to publish because the pipeline is built | The bottleneck should always be editorial quality, not the technology |
| **Scope creep into financial services** | Adding features that imply portfolio management | Stay in lane: research documentation, methodology, education. Nothing else. |

---

## 16. Next Steps

### Step 1 — Phase 5 Public Draft Workflow (Now)
The internal approval pipeline (Phase 5A–5D) is the prerequisite. The public website cannot exist without approved content. Finish smoke-testing Phase 5 before any public web work begins.

### Step 2 — Visual Moodboard (Week 1)
Collect 10–15 reference screenshots (Bloomberg, Linear, Stripe, FT, Are.na) into a Figma board. Test the color system described above as a Figma page. Validate that the serif + mono + sans combination works at multiple sizes.

### Step 3 — Homepage Wireframe (Week 1–2)
Low-fidelity wireframe of the 9 homepage sections in Figma. No color. No type. Just layout, proportions, and content hierarchy. Get the structure right before adding visual detail.

### Step 4 — Research Article Template (Week 2)
Design one complete research article at high fidelity. This is the most important page on the site — it demonstrates the seriousness of the work. Include the timeline component, source list, status badge, and disclaimer.

### Step 5 — Substack Strategy (Week 2)
Configure the SwissEdge Substack. Write the first "about" post explaining the methodology. Manually import the first approved research note. Test the reading experience. This is the fastest path to a public presence.

### Step 6 — Public Site MVP (Month 2–3)
Build the public Next.js app. Pages in order of priority:
1. Homepage
2. Research list + article detail
3. About + Methodology
4. Disclaimer
5. Newsletter redirect to Substack

Case Studies and Source Intelligence pages can follow in Month 4.

---

## Final Report

### Changed Files

```
docs/public-site/SWISSEDGE_PUBLIC_SITE_CONCEPT.md    ← created (this document)
```

No backend files modified. No frontend files modified. No deployment performed.

---

### Key Design Direction

**Three words:** Serious. Restrained. Research-first.

The SwissEdge public site is not a marketing site. It is a published research practice with a digital home. The visual language borrows from editorial design, financial journalism, and modern product interfaces — not from fintech startups or investment influencers.

The differentiator is intellectual honesty: every article says what is known, what is unknown, and what would change the view. No other "investment" site leads with uncertainty. That is the brand.

---

### Proposed Pages (Priority Order)

| Priority | Page | Reason |
|----------|------|--------|
| 1 | Homepage | First impression and framing |
| 2 | Research article detail | The core product |
| 3 | Research list | Discovery and browsability |
| 4 | About + Methodology | Credibility anchor |
| 5 | Disclaimer | Legal and trust hygiene |
| 6 | Newsletter redirect | Community building |
| 7 | Case Studies | Educational depth |
| 8 | Source Intelligence | Methodology differentiation |

---

### Recommended Next Design Sprint

**Sprint: "One Perfect Article"**

The goal is not to launch a full website. The goal is to design one perfect research article page — with the correct structure, typography, status labels, timeline, source list, and disclaimer — and validate that it communicates what SwissEdge is in a single read.

If one article page is right, everything else follows from it.

- Deliverable: 1 Figma file, 1 complete article page at 1440px and 375px
- Time estimate: 3–4 focused design sessions
- Input required: 1 approved research note from the Phase 5 pipeline

---

> *Este análisis es educativo. No es asesoramiento financiero.*
> *This document is a design specification only. It contains no financial advice, no investment recommendations, and no operational or technical infrastructure details.*
