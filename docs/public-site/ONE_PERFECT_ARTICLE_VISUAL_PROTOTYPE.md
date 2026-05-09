# One Perfect Article — Visual Prototype

> Design documentation only. No code. No implementation. No deployment.
> No financial advice. No buy/sell language. No private or internal information.
> Reference: SWISSEDGE_PUBLIC_SITE_CONCEPT.md · ONE_PERFECT_ARTICLE_SPEC.md
> Last updated: 2026-05-04

---

## 1. Purpose

This document is a visual prototype specification for the SwissEdge public research article page. It describes — at implementation-ready fidelity — how the page looks, how it is laid out, how its components behave, and what it communicates to a first-time reader.

Its purpose is to give a designer or developer a complete picture of the page before any code is written. It is a design brief, not a wireframe legend. Every decision here is intentional and derived from the two source documents above.

The article page is the site. Everything else supports it. One article done correctly establishes the brand, the trust model, and the editorial register in a single read.

---

## 2. Prototype Scope

This prototype covers:

- Desktop article page at 1440px reference width
- Mobile article page at 375px reference width
- All named sections from breadcrumb to footer
- All component states (status badges, confidence levels, timeline nodes, signal quality)
- Sidebar behavior (sticky on desktop, inline on mobile)
- Disclaimer treatment (dual placement)
- Interaction and hover behaviors
- Accessibility posture
- What the page must not contain

This prototype does not cover:

- Homepage
- Research list page
- Case study page
- Source intelligence page
- Navigation mega-menus or dropdowns
- Any backend, database, scanner, cron, or deployment logic
- React/Next.js implementation
- Figma component assembly instructions (see ONE_PERFECT_ARTICLE_SPEC.md §13)

---

## 3. Design Mood

### Three Words

**Serious. Restrained. Research-first.**

### Extended Description

The page should feel like entering a quiet, well-lit reading room at a private research library — late evening, desk lamp on, no distractions. Everything is in its place. The structure is legible before a single word is read.

The tone is institutional without being cold. It is precise without being technical for its own sake. It is authoritative because the sources are present and named, not because a voice tells you to trust it.

The reader should feel oriented within the first three seconds — they should know: this is research documentation, not a recommendation, not a pitch.

### Mood Reference Points

| Reference | What this page borrows |
|-----------|------------------------|
| Financial Times long-form article | Typography authority, editorial spacing, serif confidence |
| Bloomberg Terminal data layer | Monospace metadata, hairline rules, information density without clutter |
| Linear / Stripe product pages | Restraint, whitespace discipline, purposeful motion |
| Are.na | Calm curatorial quality, research-board feel |
| McKinsey microsite | Professional seriousness, no decorative noise |

### What This Page Deliberately Avoids

- Crypto dark aesthetic: neon accent colors, glowing gradient fills, aggressive contrast
- Trading terminal urgency: tick-by-tick data, live price feeds, blinking indicators
- Guru landing page: big claims, testimonials, countdown timers, bold CTAs
- SaaS startup minimalism: too airy, too casual, not enough document weight
- AI branding: the research process uses tools; the tools are not the product

---

## 4. Desktop Prototype — 1440px

### 4.1 Page Frame

```
Viewport width:         1440px
Background:             #0A0B0D  (near-black, slightly warm charcoal)
Container max-width:    1200px, horizontally centered
Container padding:      0 60px
Grid:                   12 columns
Article column:         720px  (cols 1–7)
Column gap:              48px
Sidebar column:         300px  (cols 9–12)
Remaining:              132px  (absorbed into outer centering)
```

The background grid texture — very faint 1px lines at 32px intervals, `rgba(255,255,255,0.03)` — spans the full viewport. It is purely decorative structure. It is never visible at normal reading distance; it registers only as a feeling of organized space when the page is empty.

No full-bleed images. No background photographs. No gradients across the page background.

### 4.2 Reading Progress Bar

A single 2px horizontal emerald line (`#10B981`) fixed at the very top of the viewport, z-index above the navbar. It grows from 0% to 100% as the reader scrolls through the article. It has no rounded ends, no label, no percentage counter, no shadow. It disappears at 0% scroll and at 100% scroll. It is scroll-driven by JS, not time-driven — there is no CSS transition on it. It should feel like a shadow of your place in the document.

### 4.3 Sticky Navbar

```
Height:                 56px
Position:               sticky, top 0, z-index 100
Background:             rgba(10,11,13,0.88) with backdrop-filter blur(8px)
Border-bottom:          1px solid #1E2229
```

Left side: `SwissEdge` wordmark — serif, small caps, 16px, `#E8EAF0`. No icon. No tagline. The name alone.

Right side: `Research  ·  Case Studies  ·  Source Intelligence  ·  About  ·  Notes` — monospace, 11px, uppercase, letter-spacing 0.12em, `#6B7280`. Hover: color transitions to `#E8EAF0` in 150ms. No underline on nav links.

The navbar carries no article metadata. It does not show the article title on scroll. It does not change appearance based on scroll depth. It is the same at the top of the page and the bottom.

### 4.4 Breadcrumb

Positioned 24px below the navbar, flush left within the article column.

```
Content:    ← Research
Font:       monospace, 12px, #6B7280, letter-spacing 0.04em
Hover:      color → #9CA3AF, 150ms
Arrow:      literal ← character, not SVG
```

One level only. No slash separator. No path hierarchy beyond the immediate parent.

### 4.5 Article Hero — Header Block

The header block occupies the full article column width (720px) and contains, in strict vertical order:

---

**Row 1 — Badge line**

Two inline badges, 8px horizontal gap, wrapping if necessary:

Badge A — Situation Type:
```
Content:       e.g. "CORPORATE SEPARATION"
Font:          monospace, 11px, uppercase, letter-spacing 0.12em
Color:         #6B7280
Background:    none
Border:        1px solid #1E2229
Border-radius: 2px
Padding:       2px 8px
```

Badge B — Research Status (four possible states):
```
── monitor ──────────────────────────────────────────
  Text: "● MONITOR"      Color: #6B7280    Border: 1px solid #374151
  No glow. No animation.

── not actionable ───────────────────────────────────
  Text: "○ NOT ACTIONABLE"   Color: #4B5563   Border: 1px solid #1E2229
  No glow. No animation.

── needs more work ──────────────────────────────────
  Text: "◐ NEEDS MORE WORK"   Color: #F59E0B   Border: 1px solid rgba(245,158,11,0.40)
  No glow. No animation. (Uncertainty does not pulse.)

── candidate for further research ───────────────────
  Text: "● CANDIDATE FOR FURTHER RESEARCH"
  Color: #10B981    Border: 1px solid rgba(16,185,129,0.40)
  Animation: box-shadow pulse
    0%:   box-shadow 0 0 6px rgba(16,185,129,0.30)
    50%:  box-shadow 0 0 10px rgba(16,185,129,0.60)
    100%: box-shadow 0 0 6px rgba(16,185,129,0.30)
    Duration: 4s infinite ease-in-out
  This is the only badge that glows. It signals: reviewed and live.
```

The status badge is the first content a reader encounters after the breadcrumb. Before the title. Before the thesis. This is intentional — epistemic framing before subject matter.

---

**Row 2 — Article Title**

```
Font:         Serif (GT Alpina / Canela / Tiempos Headline / Georgia fallback)
Desktop:      48px, line-height 1.15, weight 400
Color:        #E8EAF0
Max-width:    620px
Margin-top:   20px from badge row
```

Format: `Company Name — The Structural Event`
Em dash separator. Not a colon. Not a hyphen. Not a slash.

Example: `Meridian Group — Planned Separation of Industrial and Consumer Divisions`

Title rules (enforced editorially, not typographically):
- Never begins with "Why" (clickbait register)
- Never contains an exclamation mark
- Never implies price movement or investor action
- Maximum 14 words strongly preferred
- Names the structural event, not its interpretation

---

**Row 3 — Thesis Line**

```
Prefix "Thesis —":   monospace, 12px, #6B7280
Thesis text:         sans, 18px, italic, #9CA3AF, line-height 1.55
Max-width:           640px
Margin-top:          16px
```

The prefix `Thesis —` sits on the same line as the first words of the thesis. It is not on its own line. It is a label, not a heading.

The thesis is one sentence, 20–40 words. It states the research question, not an investment view.

Example:
> Thesis — A conglomerate has publicly announced an intention to separate two structurally distinct businesses; this note documents the available public evidence, the open questions, and the conditions that would alter the research status.

---

**Row 4 — Metadata Strip**

```
Font:          monospace, 12px, #6B7280, letter-spacing 0.04em
Separator:     · (centered dot, space each side)
Margin-top:    20px
Padding-top:   20px
Border-top:    1px solid #1E2229
```

Content: `PUBLISHED 03 May 2026  ·  REVIEWED 03 May 2026`

If not yet reviewed: omit the REVIEWED field entirely. Do not show a blank or placeholder.

---

**Row 5 — Confidence / Uncertainty Indicator**

This component is the most philosophically important on the page. It measures coverage of available public information — not probability of an outcome.

```
Container:
  Margin-top:    24px
  Padding:       12px 16px
  Background:    #14171C
  Border:        1px solid #1E2229
  Border-left:   2px solid [level color]
  Border-radius: 2px

Layout: flex row
  Left:   4 × 8px circles, 4px gap
  Right:  12px gap → label (sans 13px #9CA3AF) + sub-text (mono 11px #6B7280, 4px below)
```

Four levels:
```
●○○○  "Information incomplete"       Left border: #374151
      "Primary sources not yet located"

●●○○  "Early signals"                Left border: #6B7280
      "Initial filings reviewed — open questions are numerous"

●●●○  "Evidence accumulating"        Left border: #F59E0B
      "Key documents reviewed — important questions remain open"

●●●●  "Well-documented"              Left border: #10B981
      "Primary sources reviewed — open questions are minor"
```

The level is set by the human reviewer at approval time. It is never auto-generated. Even at level 4, the "What Is Unknown" section must contain open questions — "well-documented" means comprehensive coverage of available information, not certainty of outcome.

### 4.6 Article Column — Section Structure

The article body flows top-to-bottom in the 720px left column. Each major section follows the same structural pattern:

```
[Section divider — 1px #141820, full column width]
[Section eyebrow — mono, 10px, uppercase, letter-spacing 0.12em, #6B7280]
  Example: "01 / KNOWN"
[Section H2 — serif, 28px, #E8EAF0, margin-top 48px]
[Body text — sans, 16px, #E8EAF0, line-height 1.75, max-width 68ch]
```

Section dividers appear between major blocks, not between every section. The divider sits 8px above the eyebrow; the H2 margin handles spacing below it.

#### Body text rules

- Max-width 68ch — never wider. Long line lengths cause fatigue on research-length reads.
- Emphasis: italic only. Bold is reserved for structural hierarchy, never inline emphasis.
- Links: `#E8EAF0` color, underline `#1E2229` (faint). Hover: underline brightens to `#10B981`, 150ms. Color does not change.
- Unordered lists: em dash prefix `—`, `#6B7280`, 24px left indent, 8px item spacing. No bullet discs. No numbers (use timeline for ordered events).
- Paragraph gap: 16px.

### 4.7 Section Order — Article Body

Sections appear in this exact order. This order is non-negotiable — it follows the epistemology of the research process, not the conventions of investment writing.

```
01 / KNOWN      What Is Known
02 / UNKNOWN    What Is Unknown
03 / VIEW       What Would Change This Research View
04 / DOCUMENTS  Key Documents
05 / TIMELINE   Timeline
06 / RISKS      Risks
07 / SOURCES    Source Notes
               [Disclaimer block]
               [Newsletter CTA]
```

### 4.8 What Is Known

Factual claims from public documents. Each claim is attributable to a named public source. Format within body text:

> "[Fact]. (Source: [Document name], [date].)"

No interpretation beyond what the document states. 3–8 claims, in short paragraphs or em-dash list format.

The visual treatment is identical to standard body text. No special container, no colored background. The source attributions appear inline, typeset in the same font, no superscript footnotes.

### 4.9 What Is Unknown

Open questions in em-dash list format. Each item is a specific, observable question.

Format: `— Whether [specific thing] has been [confirmed/filed/disclosed].`

This section cannot be empty. A note without open questions implies false certainty and must not be published.

The list items are body-text weight (`#E8EAF0`). The em-dash prefix is `#6B7280`. The visual restraint is intentional — the unknown is as important as the known, and it deserves the same calm treatment.

### 4.10 What Would Change This Research View

Two sub-groups, both required. A view that only goes one direction is not research — it is advocacy.

Sub-group headers: sans, 14px, italic, `#9CA3AF`, 4px left indent. Not a separate H3.

```
What would increase research interest:
  — [Specific observable event that would confirm or advance the situation.]

What would decrease research interest:
  — [Specific observable event that would indicate the situation has changed negatively.]
```

### 4.11 Key Documents Component

A bordered list container. Each document is one row.

```
Container:
  Border:        1px solid #1E2229
  Border-radius: 2px
  Background:    #0F1114
  Overflow:      hidden

Each row — flex, 3 columns:
  Padding:       12px 16px
  Border-bottom: 1px solid #1E2229  (last row: none)
  Hover:         background → #1A1E25, border-left 2px solid #10B981, 150ms

Column 1 — Type badge (fixed 120px):
  Monospace, 10px, uppercase, letter-spacing 0.10em
  Background: #14171C, border 1px solid #1E2229, border-radius 2px, padding 2px 6px
  Examples: SEC FILING · PROXY STMT · COURT ORDER · PRESS RELEASE · ANNUAL REPORT

Column 2 — Title and date (flex-grow):
  Title:  sans, 14px, #E8EAF0
  Date:   mono, 11px, #6B7280, 2px below title
  All URLs publicly accessible only. No private links.

Column 3 — Signal quality (fixed 80px, right-aligned):
  8px dot + mono 10px label
  ● HIGH      #10B981
  ◐ MEDIUM    #F59E0B
  ○ LOW       #6B7280
  · NO SIGNAL #374151
  Tooltip on hover explaining the rating.
```

### 4.12 Timeline Component — Desktop

The timeline is horizontal on desktop, scrollable if nodes exceed visible width. It is the most visually distinctive element on the page.

```
Container:
  Width:        100% of article column (720px)
  Height:       140px
  Overflow-x:   scroll
  Custom scrollbar: 2px track #1E2229, thumb #10B981 (opacity 0.35)
  Padding:      24px 0

Track:
  1px horizontal line, #1E2229
  Spans full scrollable width, vertically centered in container

Node spacing:   130px minimum
```

Node types:
```
Confirmed event:      10px circle, fill #34D399 (accent-bright)
Unconfirmed/anticipated: 10px circle, no fill, border 1px dashed #F59E0B
Historical/completed: 10px circle, fill #6B7280
Current/active edge:  10px circle, fill #10B981 + ring pulse animation
  Keyframes: 0% box-shadow 0 0 0 0px rgba(16,185,129,0.50)
             100% box-shadow 0 0 0 6px rgba(16,185,129,0.00)
  Duration: 2s infinite ease-out
Future/speculative:   10px circle, no fill, border 1px dashed #1E2229
```

Node labels (below track, centered on node):
```
Date:   mono, 10px, #6B7280
Title:  sans, 12px, #9CA3AF, max 2 lines centered, ellipsis at 3rd line
```

Hover tooltip (appears above node on mouseenter / focus):
```
Background:    #14171C
Border:        1px solid #10B981 (accent)
Border-radius: 2px
Padding:       12px 14px
Shadow:        0 8px 32px rgba(0,0,0,0.65)
Content:
  [Date]              mono, 11px, #6B7280
  [Event title]       sans, 14px, #E8EAF0
  [2–3 sentence desc] sans, 13px, #9CA3AF
  [Source link]       mono, 11px, #10B981, opens new tab
Animation: opacity 0→1, translateY(-4px)→0, 150ms ease-out
Dismiss: mouseleave or Escape key
```

Source rule: every confirmed node must cite a public source. Nodes without sources use the dashed "unconfirmed" style and are labeled "pending confirmation."

### 4.13 Risks Section

Standard body text treatment. No colored container. No warning border. Risks are written as short factual paragraphs, one risk per paragraph, each with a bolded one- or two-word label as the opening:

```
Announcement risk. [Body text...]

Disclosure incompleteness. [Body text...]
```

The bolded label serves as structural navigation. The risk description is analytical prose, not a list of emoji or colored callouts. The tone is the same as the rest of the article — calm, factual, specific.

### 4.14 Source Notes Table

```
Container:
  Border:        1px solid #1E2229
  Border-radius: 2px
  Overflow:      hidden

Header row:
  Background:    #14171C
  Padding:       10px 16px
  Font:          mono, 10px, uppercase, letter-spacing 0.12em, #6B7280
  Columns:       SOURCE NAME (40%) · CATEGORY (20%) · SIGNAL QUALITY (15%) · WHAT IT SHOWS (25%)

Data rows:
  Padding:       12px 16px
  Border-top:    1px solid #141820
  Hover:         background → #1A1E25, 150ms

  Source name:   sans, 13px, #E8EAF0  (linked if URL present, opens new tab)
  Category:      mono, 11px, #6B7280  (Primary Regulatory / Company-Issued / Independent / Commentary)
  Signal quality: dot + mono 10px label  (● HIGH / ◐ MEDIUM / ○ LOW / · NO SIGNAL)
  What it shows: sans, 12px, #9CA3AF  (short phrase, not a sentence)
```

Source safety rule: public source name only. No internal source IDs, scanner registry entries, private notes, API routes, or operational metadata. If a source cannot be named publicly, it must not appear in this table.

### 4.15 Sidebar — Desktop

The sidebar is 300px wide, positioned to the right of the article column with a 48px gap. It is sticky from the first scroll.

```
position: sticky
top: 72px   (clears navbar 56px + 16px breathing room)
```

On very long articles, the sidebar top pins at 72px and the bottom edge scrolls away naturally. On short articles, the sidebar is simply in-flow.

The sidebar contains four stacked elements, in order:

**1. Research Status Panel**

```
Container:
  Background:    #14171C
  Border:        1px solid #1E2229
  Border-radius: 2px
  Padding:       16px

Fields (each):
  Label:   mono, 10px, uppercase, letter-spacing 0.12em, #6B7280
  Value:   sans, 13px, #E8EAF0
  Spacing: 12px between field pairs

Fields shown:
  RESEARCH STATUS     [full status label text]
  SITUATION TYPE      [e.g. Spin-off]
  PUBLISHED           [DD Mon YYYY]
  LAST REVIEWED       [DD Mon YYYY]
```

**2. Coverage Checklist Panel**

```
Container:
  Same styling as Research Status Panel (attached or separated by 12px gap)

Header:
  "COVERAGE CHECKLIST" — mono, 10px, uppercase, letter-spacing 0.12em, #6B7280

Items (flex row: icon + label, 8px gap, 8px between items):
  Checked ✓:   mono 12px #10B981 + sans 12px #9CA3AF
  Unchecked ✗: mono 12px #374151 + sans 12px #374151

Items:
  ✓/✗ Primary sources cited
  ✓/✗ Key risks documented
  ✓/✗ Open questions listed
  ✓/✗ View-change conditions included
  ✓/✗ Sources evaluated for signal quality
  ✓/✗ Manually reviewed before publication
  ✓   Educational disclaimer present  (always checked if published)
```

This checklist is read-only. It is not an interactive form. It exists to communicate editorial discipline to the reader, not to collect input.

**3. Condensed Disclaimer Panel**

```
Container:
  Background:    #14171C
  Border:        1px solid rgba(245,158,11,0.30)
  Border-left:   2px solid #F59E0B
  Border-radius: 2px
  Padding:       12px 12px 12px 16px

Header:
  "EDUCATIONAL NOTE" — mono, 10px, uppercase, letter-spacing 0.12em, #F59E0B

English text (condensed):
  sans, 12px, #9CA3AF, line-height 1.65
  "This analysis is educational.
   Not financial advice.
   Nothing here constitutes a recommendation
   to buy, sell, or hold any security."

Spanish canonical (below, 8px gap):
  sans, 12px, italic, #6B7280
  "Este análisis es educativo.
   No es asesoramiento financiero."
```

This disclaimer is never in a collapsed state, behind a toggle, or hidden. It is always visible while the sidebar is in view.

**4. Sticky End Behavior**

When the reader reaches the footer zone, the sidebar unpins and scrolls with the page naturally. There is no animation on this behavior.

### 4.16 Disclaimer Block — Article Body (Full)

Appears at the bottom of the article column, after the Source Notes table, before the Newsletter CTA.

```
Container:
  Background:    #14171C
  Border:        1px solid rgba(245,158,11,0.30)
  Border-left:   2px solid #F59E0B
  Border-radius: 2px
  Padding:       16px 16px 16px 20px
  Margin-top:    48px

Header:
  "EDUCATIONAL DISCLAIMER" — mono, 10px, uppercase, letter-spacing 0.12em, #F59E0B
  Margin-bottom: 10px

English text:
  sans, 13px, #9CA3AF, line-height 1.65

Spanish canonical (below English, 8px gap):
  sans, 13px, italic, #6B7280
  "Este análisis es educativo. No es asesoramiento financiero."
```

The full English text reads:
> This analysis is published for educational and informational purposes only. Nothing in this note constitutes financial advice, a recommendation to buy, sell, or hold any security, or an offer of any kind. Research notes document a process of analysis and reflect information available at the time of writing. This view may change as new information becomes available.

Neither version of the disclaimer can be collapsed, hidden in an accordion, or shown only on hover. This rule is absolute.

### 4.17 Newsletter CTA

Appears at the very bottom of the article column, after the full disclaimer.

```
Container:
  Background:    #0F1114
  Border:        1px solid #1E2229
  Border-radius: 2px
  Padding:       32px
  Margin-top:    48px

Eyebrow:    "RESEARCH NOTES" — mono, 10px, uppercase, #6B7280
Headline:   serif, 22px, #E8EAF0, margin-top 8px
Body:       sans, 14px, #9CA3AF, line-height 1.65, margin-top 8px
Button:     "Subscribe to Notes →" — mono, 12px, #E8EAF0
            border 1px solid #1E2229, padding 8px 18px, border-radius 2px, bg none
            Hover: border-color → rgba(16,185,129,0.35), 150ms
Trust line: "Free. No spam. Unsubscribe anytime." — mono, 10px, #374151, margin-top 10px
```

The CTA is an invitation, not a conversion goal. It should be the quietest element on the page. The button does not use a filled background. It does not say "Join," "Get Access," or "Sign Up."

### 4.18 Footer

Full-width dark panel. 1px top border `#1E2229`. Constrained to 1200px container.

```
Height:        ~80px
Background:    #0A0B0D
Padding:       24px 60px

Left column:   "SwissEdge" wordmark — serif, small caps, 14px, #6B7280
               "2026" — mono, 11px, #374151, 4px below

Center column: nav links — Research · Case Studies · About · Disclaimer
               mono, 11px, #374151, letter-spacing 0.10em
               Hover: #6B7280, 150ms

Right column:  nothing. Empty. Breathing room.
```

The footer does not contain social media icons, affiliate links, or advertising. It does not contain a second newsletter signup form. It does not repeat the disclaimer in full — the full disclaimer is in the article body.

---

## 5. Mobile Prototype — 375px

### 5.1 Grid

```
Viewport:             375px
Horizontal padding:   20px each side
Content width:        335px
All content:          single column, top-to-bottom
No sidebar column.
```

### 5.2 Navbar — Mobile

```
Height:       52px
Background:   rgba(10,11,13,0.88), backdrop-filter blur(8px)
Border-bottom: 1px solid #1E2229

Left:  "SwissEdge" wordmark — same serif, small caps, 14px
Right: ☰ hamburger — 3 lines, 20×14px, #6B7280, tap target 44×44px
```

Mobile menu (open state):
```
Full viewport overlay — background #14171C
Nav items stacked, 24px apart, mono, 14px, uppercase, letter-spacing 0.10em, #9CA3AF
Close button: ✕ top-right, 44×44px tap target
Transition: opacity + translateY(-8px)→0, 200ms ease-out
```

### 5.3 Hero — Mobile

The header block compresses but preserves all structural elements. Nothing is omitted on mobile.

```
Breadcrumb:           ← Research, mono 12px #6B7280, 16px below navbar

Badge row:            Situation type + status badge
                      Both badges on one line if they fit (320px combined max)
                      Wraps to two lines if status label is long ("CANDIDATE FOR FURTHER RESEARCH" wraps)

Title:                serif, 30px, line-height 1.20, #E8EAF0
                      Runs to multiple lines naturally — no truncation

Thesis:               sans, 16px, italic, #9CA3AF, line-height 1.55

Metadata strip:       mono, 11px, #6B7280, stacked vertically
                      PUBLISHED [date] on one line
                      REVIEWED [date] on next line
                      1px divider #1E2229 above the block

Confidence indicator: same component, full width (335px)
                      flex row maintained — dots left, text right
```

### 5.4 Section Headers — Mobile

```
Eyebrow:   mono, 10px, uppercase, #6B7280
H2:        serif, 22px, #E8EAF0, margin-top 36px, margin-bottom 12px
Body:      sans, 15px, line-height 1.80, max-width 335px
```

### 5.5 What Is Known / Unknown / View — Mobile

Identical structure to desktop. All three sections present, in the same order. No sections hidden or collapsed on mobile. The content may be slightly shorter in practice due to natural mobile reading constraints, but the page design does not enforce any truncation.

### 5.6 Key Documents — Mobile

Desktop's 3-column flex row cannot fit on 335px. Each row becomes a stacked card.

```
Each document card:
  Padding:     12px
  Border:      1px solid #1E2229
  Border-radius: 2px
  Background:  #0F1114
  Margin-bottom: 8px

  Top row:     Type badge (left) — mono, 10px, uppercase
  Middle row:  Document title — sans, 14px, #E8EAF0
  Bottom row:  Date (mono 11px #6B7280) on left  ·  Signal quality dot + label on right
```

### 5.7 Timeline — Mobile (Vertical)

The horizontal timeline cannot render legibly at 335px. On mobile, the timeline becomes vertical.

```
Track:      2px vertical line, #1E2229, 16px from left edge of content area
Nodes:      8px circles, centered on track (same type styling as desktop)
Spacing:    52px minimum between nodes

Label layout (right of track, 28px left offset):
  Date:     mono, 10px, #6B7280
  Title:    sans, 13px, #9CA3AF, below date, 4px gap
```

Tap interaction: tapping a node expands an inline block below the label.
```
Content:    date · title · 2–3 sentence description · source link (same as desktop tooltip)
Transition: max-height 0→auto, 200ms ease-out
Dismiss:    second tap on same node, or tap another node
```

The "current" node pulse animation is preserved on mobile. The ring expands at 2s interval.

### 5.8 Risks — Mobile

Same as desktop: short paragraphs, bolded risk name as opening phrase. No special container. Full width (335px).

### 5.9 Source Notes Table — Mobile

The 4-column table collapses to stacked cards, same approach as Key Documents.

```
Each source card:
  Padding:     12px
  Border:      1px solid #1E2229, border-radius 2px, background #0F1114
  Margin-bottom: 8px

  Top:   Source name (sans 13px #E8EAF0) + category badge (mono 10px)
  Mid:   "What it shows" — sans 12px #9CA3AF
  Bot:   Signal quality dot + label — left aligned
```

### 5.10 Coverage Checklist — Mobile

On mobile, the sidebar does not exist. The coverage checklist moves inline in the article column, positioned between the Source Notes section and the Disclaimer block.

```
Same container styling as desktop sidebar version
Full width (335px)
All 7 items visible, no truncation
```

### 5.11 Disclaimer — Mobile

Full disclaimer block, full width (335px), same visual treatment as desktop. The condensed sidebar version does not appear on mobile — the full version replaces it.

```
Amber left border, amber header, full English text, Spanish canonical line.
Not collapsible. Not hidden behind a tap.
```

### 5.12 Newsletter CTA — Mobile

```
Same structural elements, 24px padding (vs 32px desktop)
Button full width on mobile (335px, text centered)
Trust line centered
```

### 5.13 Footer — Mobile

```
Single column, stacked:
  "SwissEdge 2026" — serif small caps + mono year
  Nav links: Research · Disclaimer · About (most critical three only)
  All mono, 11px, #374151

No horizontal layout. No multi-column grid.
```

---

## 6. Visual System

### 6.1 Colors

```
── Backgrounds ────────────────────────────────────────────────────
--bg-base:           #0A0B0D    page background
--bg-surface:        #0F1114    article body, document cards
--bg-elevated:       #14171C    sidebar panels, tooltip, navbar overlay
--bg-overlay:        #1A1E25    hover state

── Borders ────────────────────────────────────────────────────────
--border-default:    #1E2229    standard 1px rule
--border-subtle:     #141820    faint section dividers
--border-active:     #10B981    hover / focus / active

── Typography ─────────────────────────────────────────────────────
--text-primary:      #E8EAF0    headlines, body
--text-secondary:    #9CA3AF    thesis, sub-headings, summaries
--text-tertiary:     #6B7280    metadata, timestamps, labels
--text-ghost:        #374151    decorative only (never sole info carrier)

── Accent (emerald — one color only) ──────────────────────────────
--accent:            #10B981    active status, confirmed events
--accent-bright:     #34D399    confirmed timeline nodes
--accent-dim:        rgba(16,185,129,0.12)    tinted surface
--accent-border:     rgba(16,185,129,0.35)    glowing border, hover

── Status ─────────────────────────────────────────────────────────
monitor:             #6B7280
not-actionable:      #4B5563
needs-more-work:     #F59E0B
candidate:           #10B981

── Disclaimer / Warning ───────────────────────────────────────────
--warning:           #F59E0B    amber
--warning-dim:       rgba(245,158,11,0.15)
--warning-border:    rgba(245,158,11,0.30)

── Signal Quality ─────────────────────────────────────────────────
--signal-high:       #10B981
--signal-medium:     #F59E0B
--signal-low:        #6B7280
--signal-none:       #374151
```

**Color rules — no exceptions:**
- Emerald (`#10B981` / `#34D399`) appears only on: active status badge, confirmed timeline nodes, focus rings, reading progress bar, hover borders.
- Amber (`#F59E0B`) appears only on: "needs more work" badge, disclaimer labels and borders.
- No blue, purple, red, gradient fills, or gold anywhere on the page.
- No decorative use of any accent color.

### 6.2 Typography

Three typefaces. Strict role separation. Mixing roles dissolves the system.

```
SERIF
  font-family: 'GT Alpina', 'Canela', 'Tiempos Headline', Georgia, serif
  Roles: article title (H1), section H2, pull quotes
  Never: metadata, labels, body text, buttons

SANS
  font-family: 'Söhne', 'Inter', 'IBM Plex Sans', system-ui, sans-serif
  Roles: thesis, body text, document descriptions, source names
  Never: article title, status badges, timestamps

MONO
  font-family: 'JetBrains Mono', 'IBM Plex Mono', monospace
  Roles: status badges, eyebrow labels, timestamps, signal quality labels,
         breadcrumb, section numbers, metadata fields, checklist states,
         reading progress (conceptually)
  Never: body text, article title, thesis
```

Desktop type scale:
```
Article title:    Serif   48px   lh 1.15   wt 400
Section H2:       Serif   28px   lh 1.25   wt 400
Section H3:       Serif   20px   lh 1.30   wt 400
Thesis:           Sans    18px   lh 1.55   wt 400 italic
Body:             Sans    16px   lh 1.75   wt 400
Body small:       Sans    14px   lh 1.65   wt 400
Eyebrow:          Mono    11px   lh 1.40   wt 400   0.10em uppercase
Metadata:         Mono    12px   lh 1.40   wt 400   0.04em
Micro label:      Mono    10px   lh 1.40   wt 400   0.10em uppercase
```

Mobile type scale:
```
Article title:    Serif   30px   lh 1.20   wt 400
Section H2:       Serif   22px   lh 1.30   wt 400
Section H3:       Serif   18px   lh 1.35   wt 400
Thesis:           Sans    16px   lh 1.55   wt 400 italic
Body:             Sans    15px   lh 1.80   wt 400
Body small:       Sans    13px   lh 1.65   wt 400
Eyebrow:          Mono    10px   lh 1.40   wt 400
Metadata:         Mono    11px   lh 1.40   wt 400
```

### 6.3 Spacing System

Base unit: 4px. All spacing is a multiple of 4.

```
4px    micro gap (dot to label, badge internal)
8px    tight gap (list item spacing, field-to-field within panel)
12px   component internal padding (small)
16px   standard paragraph gap, section label margin-below
20px   standard internal padding, metadata strip margin-top
24px   section gap (mobile), breadcrumb below navbar
32px   CTA padding (desktop)
36px   H2 margin-top (mobile)
48px   H2 margin-top (desktop), large section gap
60px   container horizontal padding
72px   sidebar sticky offset
```

### 6.4 Borders

Every border is 1px. No 2px borders except: left accent on disclaimer (2px), left hover accent on document rows (2px), confidence indicator left accent (2px).

```
Standard rule:      1px solid #1E2229
Subtle divider:     1px solid #141820
Active / hover:     1px solid rgba(16,185,129,0.35)
Disclaimer accent:  2px solid #F59E0B  (left side only)
```

No box shadows as primary structure. No drop shadows on cards. The document-stack shadow from the concept document is reserved for the research list page, not the article page.

### 6.5 Cards

All card-like containers share a base pattern:
```
Background:    --bg-surface (#0F1114)
Border:        1px solid --border-default (#1E2229)
Border-radius: 2px
```

Two pixels of border radius only. Not 8px, not fully rounded. The geometry should read as structured and precise, not friendly or app-like.

### 6.6 Labels and Badges

All labels and badges use monospace. All-caps. Tight letter-spacing. Never sans, never serif.

Badge containers: 2px border-radius, 2–4px vertical padding, 6–10px horizontal padding. Never pill-shaped (never border-radius: 9999px).

### 6.7 Icons

The article page uses no icon library and no SVG icon set. The only symbols are:

- `●` `○` `◐` — Unicode circles for status badges and confidence dots
- `✓` `✗` — Unicode check marks for coverage checklist
- `←` — Unicode arrow for breadcrumb
- `☰` `✕` — Unicode for mobile nav toggle and close
- `·` — Centered dot for metadata separator
- `—` — Em dash for body list prefix

All other iconography is deferred to the homepage and list pages.

### 6.8 Motion Principles

Total animation budget: four interactions. Nothing else moves.

```
1. Page entry stagger (header block only):
   opacity 0→1, translateY(6px)→0, 300ms, cubic-bezier(0.0,0.0,0.2,1)
   Stagger: badges 0ms · title 50ms · thesis+meta 100ms · confidence 150ms
   Fires once per page load. Body sections render without animation.

2. Candidate status badge glow:
   box-shadow pulse, 4s infinite ease-in-out
   0%: 0 0 6px rgba(16,185,129,0.30)
   50%: 0 0 10px rgba(16,185,129,0.60)
   Candidate badge only. No other badge animates.

3. Timeline active node pulse (rightmost confirmed):
   ring expansion, 2s infinite ease-out
   0%: box-shadow 0 0 0 0px rgba(16,185,129,0.50)
   100%: box-shadow 0 0 0 6px rgba(16,185,129,0.00)

4. Reading progress bar:
   JS scroll-driven, no CSS transition, no lag.
```

Everything else is static. No parallax. No scroll-reveal. No hover scale. No background motion on the article page (the research radar animation is homepage-only).

`prefers-reduced-motion` support: animations 1, 2, and 3 are disabled; the candidate badge holds a static glow at 30% opacity; reading progress bar continues (it is scroll-driven, not time-driven); hover border transitions continue (they are interactive feedback, not decoration).

---

## 7. Article Anatomy

In reading order, from top to bottom.

### 7.1 Reading Progress Bar
2px emerald line, fixed at viewport top. First thing visible, last thing noticed.

### 7.2 Sticky Navbar
56px. `SwissEdge` wordmark left. Nav links right. Semi-transparent with backdrop blur. Present for the entire scroll. Never changes.

### 7.3 Breadcrumb
`← Research`. One step back. Monospace. Quiet.

### 7.4 Situation Type Badge
Small. Borderless except for a faint hairline. `CORPORATE SEPARATION` or similar. Sets subject category before the title.

### 7.5 Research Status Badge
The most important element on the page. Read before the title. Communicates the editorial stance of the research note immediately. The only element with an optional glow (candidate state only).

### 7.6 Article Title
Serif. 48px. Named entity — em dash — structural event. Authoritative and specific. Not clickbait. Not advice.

### 7.7 Thesis Line
One sentence. Italic. States the research question. Does not state a conclusion. The `Thesis —` prefix is a structural signal that this is research, not opinion.

### 7.8 Metadata Strip
`PUBLISHED [date]  ·  REVIEWED [date]`. Monospace. Hairline border above. Communicates recency and human review.

### 7.9 Confidence / Uncertainty Indicator
Four dots. A level label. A sub-text. Set by a human reviewer. Communicates epistemic state, not probability. Reads immediately after the metadata.

### 7.10 What Is Known
Factual claims with inline source attribution. Short paragraphs or em-dash list. No interpretation beyond what the documents say.

### 7.11 What Is Unknown
Open questions in em-dash list format. Always present. Never empty. Given equal visual weight to "What Is Known" — this is the brand.

### 7.12 What Would Change This Research View
Both directions: what would increase research interest and what would decrease it. Structured as two em-dash lists under italic sub-headers. Mandatory and bidirectional.

### 7.13 Key Documents
A bordered list. Each document: type badge, title, date, signal quality. Every document publicly accessible. Every row hover-active. Source discipline made visible.

### 7.14 Timeline
Horizontal on desktop, vertical on mobile. Nodes for confirmed and anticipated events. Current node pulses. Hover/tap for detail and source link. The visual anchor for the article — a reader who scans the timeline before reading the body gets the structural sequence of the situation immediately.

### 7.15 Risks
Short analytical paragraphs. Bolded risk name as opener. No special styling. Calm and matter-of-fact. Not catastrophizing, not minimizing.

### 7.16 Source Notes Table
Four columns: name, category, signal quality, what it shows. The evidence chain made explicit and evaluable. A reader can assess the quality of the research by reading this table alone.

### 7.17 Educational Disclaimer (Full)
Amber left border. Amber header label. Full English text. Spanish canonical line. Not a footnote. Placed above the CTA, not buried at the very bottom.

### 7.18 Newsletter CTA
Quiet invitation. Research notes, not tips. Serif headline, sans body, mono button. Not a conversion funnel element.

### 7.19 Footer
Dark. Minimal. Logo, year, three nav links. Nothing else.

---

## 8. Editorial Trust Signals

The page communicates trustworthiness through structure and restraint, not through explicit claims of authority. Here is how each trust signal is expressed visually.

### Manual Review

The `REVIEWED [date]` field in the metadata strip makes the review date explicit and specific. The Coverage Checklist item `✓ Manually reviewed before publication` makes the human review step visible. The checklist is read-only — it cannot be checked programmatically, only by a human at approval time.

### Educational Purpose

The disclaimer appears twice: in the sticky sidebar (always in view while the sidebar is visible) and in the article body above the CTA. The amber color — used nowhere else on the page — creates visual association between that color and "this is not advice." The header `EDUCATIONAL DISCLAIMER` uses the word directly, before the reader reaches the text.

### Uncertainty

Uncertainty is elevated to structural status, not relegated to a footnote. The confidence indicator is in the header block — immediately before the article body. "What Is Unknown" is a first-class section with a numbered eyebrow, a serif H2, and the same typographic weight as "What Is Known." The open questions in "What Is Unknown" are stated precisely as observable things, not vague hedges.

### Source Discipline

The Key Documents component makes the primary source chain tangible: readers can see exactly which filings were reviewed and click through to public URLs. The Source Notes table assigns a signal quality to each source — the research does not treat all sources as equal, and it says so publicly. The inline source attributions in "What Is Known" (`Source: [Document name], [date]`) tie every factual claim to a specific document.

### No Financial Advice

The page has no price data, no tickers, no return estimates, no buy/sell/hold language. The four status labels are the complete vocabulary for describing a research note's state. The disclaimer is typeset, not hidden, and appears in two locations. The thesis explicitly states what it is (a research question) and what it is not (an investment view). These are structural choices, not just editorial guidelines.

---

## 9. Anti-Patterns

What this page must never contain, and why.

### Stock Trading UI Elements
Price charts, candlestick charts, live tickers, ask/bid spreads, volume bars. These associate the page with trading orientation. SwissEdge researches structural events, not price movements.

### Buy / Sell / Hold Language
In the title, thesis, section headings, body text, checklist labels, button labels, metadata, meta tags, alt text, or any other text on the page. The four approved status labels are the complete vocabulary. No custom labels are permitted.

### Target Prices or Return Estimates
"Fair value," "upside," "downside," "gain," "return," "yield" in an investment context. These constitute financial advice language and are prohibited.

### Performance Claims
"Our track record," "our returns," "this approach generated X%," "our model predicted." SwissEdge does not claim performance. The credibility is in the documented process.

### Guru Landing Page Elements
Testimonials, member counts, urgency timers, "join N investors," "limited spots," "before it's too late." These patterns are incompatible with the trust model and the brand register.

### Overconfident Status Labels
"Strong candidate," "high conviction," "clear setup," "obvious trade." The four approved labels are final. Adding variants implies a gradient of confidence the research cannot support.

### Social Proof Numbers
View counts, read counts, engagement metrics, "X subscribers." Popularity is not quality.

### Social Sharing Button Bar
Share to Twitter/X, LinkedIn, email. Readers who want to share copy the URL. A sharing bar optimizes for virality, not depth.

### Comment Section
Investment comment sections attract noise, unsolicited advice, and signal pollution. There is no comment section.

### Email Popup or Subscription Modal
No popup appears on the article page. No modal interrupts reading. The newsletter CTA is at the bottom of the article, after the disclaimer — an invitation to readers who reach it.

### AI / Automation Branding
"AI-powered research," "AI-generated," "powered by Claude," "our model detected." AI is a tool in the research process. It is not the product. It is never mentioned on the public page.

### Animated Background on Article Page
The research radar animation is homepage-only. The article page has no background animation, no particles, no floating elements. The background grid texture is purely structural — invisible at normal reading distance.

### Internal Operational Metadata
Research case IDs, situation IDs, run IDs, draft IDs, evaluator results, scanner tags, Tailscale addresses, VPS details, API routes, file paths, `.env` content, database IDs. None of these appear on the public page. They must be stripped at the content approval layer before any content reaches a public-facing surface.

### Author Photo or Biography Panel
SwissEdge is a research practice, not a personality platform. There is no author byline photo, social link, or bio section on the article page.

### "Unpublished" or "Draft" Content
Only content in `approved` status reaches the public page. Draft, pending, or internally-tagged content must not be accessible from any public URL.

---

## 10. Implementation Notes for Later

This section is addressed to a future implementation sprint, not the current design documentation phase.

### Public Site Must Be Separate From Private Mission Control

The public website must live in a completely separate application from the private Mission Control platform. Different repository. Different deployment. Different domain. No shared authentication. No shared API keys. No shared infrastructure visible to the public.

The public site should not know that the private platform exists. The private platform should not care that the public website exists. They share content, not infrastructure.

### Recommended Technology Stack

```
Framework:      Next.js (App Router) with static generation (generateStaticParams)
Styling:        Tailwind CSS — the color tokens and spacing system above map to Tailwind config
Animation:      Framer Motion (minimal import: page entry, status badge glow, timeline pulse)
Timeline:       Custom component or D3.js lightweight import
Hosting:        Vercel or Cloudflare Pages
Content:        Markdown files exported from the private approval pipeline,
                or a headless CMS (Sanity, Contentlayer)
```

### Static Prototype First

Before building the Next.js app, build a static HTML/CSS prototype using the exact specifications in this document. Validate the layout, typography, color system, and component hierarchy in a browser before adding React/Next.js complexity.

The Figma frames specified in `ONE_PERFECT_ARTICLE_SPEC.md §13` are the prerequisite for the static prototype.

### No Auto-Publishing

No content ever appears on the public site without passing through the manual approval workflow. The static generation build must only consume content records with `approved` status. The build pipeline must not expose draft, pending, or `needs_review` records.

### Content Safety at the API / Export Layer

If content is served via a read-only public API, that API must expose only these fields per article:

```
title
situation_type
status_label
confidence_level
thesis
published_at
reviewed_at
body_sections  (known / unknown / view / documents / timeline / risks / sources)
disclaimer_text
```

The following fields must never appear in any public-facing payload:

```
research_case_id
situation_id
run_id
draft_id
internal_tags
evaluator_output
scanner_results
source_registry_ids
private_notes
VPS_metadata
API_routes
```

### No Substack API Integration in the First Sprint

The first public presence should be a static site or Substack publication with manually imported content. Substack API integration, if ever needed, is a later sprint and must be separately scoped.

### No Backend Changes in This Sprint

This prototype document does not require any changes to the backend, database, scanner, cron system, evaluator, investment sources, or private APIs. The implementation sprint that builds this page will consume already-approved content as static data.

### Typeface Licensing

For the initial prototype, use Inter (free, Google Fonts) for the sans role and JetBrains Mono (free, Google Fonts) for the mono role. Acquire a trial of GT Alpina, Canela, or Tiempos Headline for headline evaluation only before committing to a paid license.

### JSON-LD Structured Data

When the public site goes live, add JSON-LD `Article` schema to each article page:

```json
{
  "@context": "https://schema.org",
  "@type": "Article",
  "datePublished": "YYYY-MM-DD",
  "dateModified": "YYYY-MM-DD",
  "keywords": ["special situations", "corporate separation", "research note"]
}
```

Do not include `author`, `publisher`, or any field that implies advisory authority. Do not enable search indexing until the content pipeline is stable.

### Figma Frames Required Before Implementation

Before writing a single line of implementation code, the following Figma frames must exist and be approved:

```
Frame 1 — Desktop: Full page (1440px, auto height, all sections)
Frame 2 — Desktop: First viewport (1440px × 900px)
Frame 3 — Mobile: Full page (375px, auto height)
Frame 4 — Mobile: First viewport (375px × 812px)
Frame 5 — Component: Timeline desktop with tooltip state
Frame 6 — Component: All four status badge states
Frame 7 — Component: Source notes table with four signal quality rows
Frame 8 — Component: Confidence indicator all four levels
Frame 9 — Component: Disclaimer full + condensed side by side
```

The example copy from `ONE_PERFECT_ARTICLE_SPEC.md §12` (the Meridian Group fictional case) is the correct content for all Figma frames.

---

## Completion Summary

### File Created

```
docs/public-site/ONE_PERFECT_ARTICLE_VISUAL_PROTOTYPE.md
```

No backend files modified. No frontend files modified. No deployment performed.

### Main Design Decisions

**1. Status badge is the first element.**
Before the reader sees the title, they see the research status. This enforces epistemic framing. A reader cannot mistake a research note for a recommendation if the first thing they encounter is `● CANDIDATE FOR FURTHER RESEARCH` or `◐ NEEDS MORE WORK`.

**2. Uncertainty is elevated to first-class structural status.**
"What Is Unknown" appears immediately after "What Is Known" with equal typographic weight. The confidence indicator sits in the header block, not at the bottom of the page. Intellectual honesty is the visual brand, not a disclaimer buried in a footnote.

**3. The disclaimer appears twice, in persistent positions.**
On desktop: in the sticky sidebar (always visible while scrolling) and at the bottom of the article body. On mobile: inline before the CTA. The reader cannot reach the end of the article without having seen the disclaimer in full. Neither instance can be collapsed.

**4. One accent color, four precise use cases.**
Emerald (`#10B981`) appears on: active status badge, confirmed timeline nodes, focus rings, reading progress bar. Amber (`#F59E0B`) appears on: "needs more work" badge, disclaimer borders and labels. Every other color on the page is a shade of near-black, gray, or off-white. This constraint is the visual system.

**5. Animation budget is exactly four interactions.**
Page entry stagger, candidate badge glow, timeline current-node pulse, reading progress bar. Everything else is static. Motion is earned by meaning.

**6. Three typefaces, no mixing of roles.**
Serif carries authority (headlines). Sans carries substance (body). Mono carries data (metadata, labels, badges). Mixing these roles is the fastest path to destroying the visual register.

**7. Source discipline is made visible.**
Every factual claim in "What Is Known" has an inline source attribution. The Key Documents component shows type and signal quality per document. The Source Notes table assigns signal quality to each source with an explanatory framework. The reader can audit the research.

### Open Questions

| # | Question | Status |
|---|----------|--------|
| Q1 | Which serif typeface will be used in production? GT Alpina and Canela require paid licenses. Tiempos Headline requires a license. Georgia is free but significantly weaker aesthetically. | Needs decision before Figma high-fidelity frames. |
| Q2 | Who is responsible for setting the confidence indicator level at publication time? Is there a named step in the approval workflow? | Must be defined before the content pipeline is built. Currently implicit. |
| Q3 | Is the published/reviewed date populated from `published_at`, `approved_at`, or both in the content model? | Needs clarification before the API export layer is specified. |
| Q4 | Maximum expected number of timeline nodes per article? If consistently over 10, a desktop "expand mode" or vertical fallback is needed. | Defer until first real article content is available. |
| Q5 | Print / PDF export requirement? If yes, the disclaimer must persist in the print stylesheet and the layout changes significantly. | Defer until after the visual prototype is validated. |
| Q6 | Is JSON-LD structured data wanted from day one, or only once search indexing is enabled? | Recommendation: include from day one. No risk and reduces future work. |

### Recommended Next Sprint

**Sprint: "Validate the Frame"**

Goal: produce the nine Figma frames listed in Section 10 at high fidelity using the Meridian Group example copy from `ONE_PERFECT_ARTICLE_SPEC.md §12`. Resolve Q1 (typeface) before beginning. Use Inter and JetBrains Mono as temporary substitutes.

Deliverables:
- 9 Figma frames at exact pixel dimensions specified above
- 1 exported PDF for printed review at A4
- 1 annotation layer on Frame 1 keyed to component names in this spec

Not in scope: homepage, navigation animations, case study page, any backend changes.

Estimated time: 3–4 focused design sessions.

---

> *Este análisis es educativo. No es asesoramiento financiero.*
> *This document is a design specification only. It contains no financial advice,
> no investment recommendations, and no private or internal operational information.*
