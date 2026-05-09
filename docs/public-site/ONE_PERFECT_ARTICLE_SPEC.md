# SwissEdge — One Perfect Article
## Public Research Note Page: Complete Design Specification

> Design specification only. No code. No implementation. No deployment.
> No financial advice. No buy/sell language. No private or internal information.
> Supersedes earlier draft. Last updated: 2026-05-03

---

## Premise

One article page is the site. Every other page is derived from it.

If the article communicates — in a single read — that SwissEdge publishes serious, methodical, honest research about structural corporate events, the brand is established. If it fails, no homepage design rescues it.

This document specifies the article page at production fidelity: exact layout coordinates, component anatomy, type scale, color tokens, motion behaviour, ARIA spec, example copy, and safety rules. A designer should be able to open this document alongside the moodboard and produce Figma frames without further design decisions.

---

## 1. Color Token System

```
── Backgrounds ────────────────────────────────────────────────────────────────
--bg-base:         #0A0B0D    page background (slightly warm charcoal, not pure black)
--bg-surface:      #0F1114    article body, card, panel
--bg-elevated:     #14171C    sidebar, tooltip, dropdown
--bg-overlay:      #1A1E25    hover state, active card

── Borders ────────────────────────────────────────────────────────────────────
--border-default:  #1E2229    standard 1px rule, grid lines, card edges
--border-subtle:   #141820    very faint section dividers
--border-active:   #10B981    emerald hover / focus / active border

── Typography ─────────────────────────────────────────────────────────────────
--text-primary:    #E8EAF0    headlines, body (slightly blue-tinted off-white)
--text-secondary:  #9CA3AF    thesis, sub-headings, card summaries
--text-tertiary:   #6B7280    metadata, timestamps, labels, eyebrows
--text-ghost:      #374151    placeholders, decorative only (WCAG: use sparingly)

── Accent (emerald — single accent only) ──────────────────────────────────────
--accent:          #10B981    active status, confirmed events, glow core
--accent-bright:   #34D399    timeline confirmed node, badge text
--accent-dim:      rgba(16,185,129,0.12)    tinted surface (use sparingly)
--accent-border:   rgba(16,185,129,0.35)    glowing border / hover

── Status ─────────────────────────────────────────────────────────────────────
--status-monitor:          #6B7280    gray text/border
--status-not-actionable:   #4B5563    dark gray text/border
--status-needs-work:       #F59E0B    amber text/border
--status-candidate:        #10B981    emerald text/border + glow

── Caution / Disclaimer ───────────────────────────────────────────────────────
--warning:         #F59E0B    amber — disclaimer borders and labels only
--warning-dim:     rgba(245,158,11,0.15)    amber surface tint
--warning-border:  rgba(245,158,11,0.30)    amber border

── Signal Quality (source notes) ──────────────────────────────────────────────
--signal-high:     #10B981    primary legally sourced document
--signal-medium:   #F59E0B    derived analysis, needs verification
--signal-low:      #6B7280    opinion, commentary
--signal-none:     #374151    present but not yet evaluated
```

**Color rules:**
- Emerald is the only accent color. It appears on: active status badge, confirmed timeline nodes, focus rings, reading progress bar, "candidate" glow. Nowhere else.
- Amber appears on: "needs more work" badge, disclaimer labels and borders. Nowhere else.
- No blue, purple, or gradient fills. No gold. No marble.
- Fills change only in: surface vs. elevated vs. overlay. Never as decoration.

---

## 2. Typography System

Three typefaces. Strict role separation. Mixing roles destroys the system.

### Typeface Assignments

```
SERIF — intellectual authority, headlines
  font-family: 'GT Alpina', 'Canela', 'Tiempos Headline', Georgia, serif
  Roles: article title, section H2, pull quotes
  Never used for: metadata, labels, body text, buttons

SANS — readability, substance
  font-family: 'Söhne', 'Inter', 'IBM Plex Sans', system-ui, sans-serif
  Roles: thesis line, body text, document descriptions, source names
  Never used for: article title, status badges, timestamps

MONO — data layer, research terminal
  font-family: 'JetBrains Mono', 'IBM Plex Mono', monospace
  Roles: status badges, eyebrow labels, timestamps, signal quality, breadcrumb,
         section numbering, metadata fields, checklist states, reading progress
  Never used for: body text, article title, thesis
```

### Type Scale — Desktop (1440px)

```
Role                  Typeface  Size    Line-height  Weight  Letter-spacing
──────────────────    ────────  ──────  ───────────  ──────  ──────────────
Article title         Serif     48px    1.15         400     0
Section H2            Serif     28px    1.25         400     0
Section H3            Serif     20px    1.30         400     0
Thesis (italic)       Sans      18px    1.55         400     0
Body                  Sans      16px    1.75         400     0
Body small            Sans      14px    1.65         400     0
Source link           Sans      14px    1.40         400     0
Eyebrow / label       Mono      11px    1.40         400     0.10em  uppercase
Metadata              Mono      12px    1.40         400     0.04em
Micro label           Mono      10px    1.40         400     0.10em  uppercase
```

### Type Scale — Mobile (375px)

```
Role                  Typeface  Size    Line-height  Weight
──────────────────    ────────  ──────  ───────────  ──────
Article title         Serif     30px    1.20         400
Section H2            Serif     22px    1.30         400
Section H3            Serif     18px    1.35         400
Thesis (italic)       Sans      16px    1.55         400
Body                  Sans      15px    1.80         400
Body small            Sans      13px    1.65         400
Eyebrow / label       Mono      10px    1.40         400
Metadata              Mono      11px    1.40         400
```

### Typography Rules

- Body text max-width: 68ch. Never wider. Prevents fatigue on long reads.
- Emphasis within body: italic only. Never bold inline. Bold = visual hierarchy element, not emphasis.
- All-caps: mono labels only. Never body, never headings.
- H2 has 48px space-above, 16px space-below (desktop); 36px/12px (mobile).
- First paragraph after H2: no top margin.
- Links: `--text-primary` color, very faint underline (`--border-default`). Hover: underline brightens to `--accent`. Color does not change.
- Section numbers (01, 02…) in mono eyebrow above H2. Small. Tertiary color. Optional but recommended for navigation comprehension.

---

## 3. Desktop Layout — 1440px

### Grid

```
Viewport:           1440px
Container max-width: 1200px, horizontally centered
Container padding:  0 60px (applied once at container)

Column distribution (within 1200px):
  Article column:    720px
  Column gap:         48px
  Sidebar:           300px
  Remaining:         132px (absorbed into centering)

Article internal:
  Text max-width:    68ch ≈ 680px at 16px
  The column is 720px; text breathes within it.
```

### Full Page Map — Desktop

```
┌──────────────────────────────────── 1440px ────────────────────────────────────┐
│▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓ READING PROGRESS (2px) ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓│
│                                                                                 │
│╔═══════════════════════════════ NAVBAR 56px (sticky) ═══════════════════════╗  │
│║ SwissEdge                          Research · Case Studies · About · Notes ║  │
│╚════════════════════════════════════════════════════════════════════════════╝  │
│                                                                                 │
│    ←──────────────────── 1200px container ────────────────────→               │
│    ┌───────────────── 720px ARTICLE ─────────────────┐ ┌── 300px SIDEBAR ──┐  │
│    │                                                  │ │                    │  │
│    │ ← Research                        breadcrumb    │ │  [sticky start]    │  │
│    │                                                  │ │                    │  │
│    │ [SPIN-OFF]  [● CANDIDATE FOR FURTHER RESEARCH]  │ │  RESEARCH STATUS   │  │
│    │                                                  │ │  ──────────────    │  │
│    │ ████████████████████████                         │ │  ● Candidate for   │  │
│    │ Article Title Spanning                           │ │    further research│  │
│    │ Two Lines in Serif                               │ │                    │  │
│    │                                                  │ │  SITUATION TYPE    │  │
│    │ Thesis — One sentence describing the structural  │ │  Spin-off          │  │
│    │ situation and why it is being researched now.    │ │                    │  │
│    │                                                  │ │  PUBLISHED         │  │
│    │ PUBLISHED 03 May 2026 · REVIEWED 03 May 2026    │ │  03 May 2026       │  │
│    │ ──────────────────────────────────────────────  │ │                    │  │
│    │                                                  │ │  LAST REVIEWED     │  │
│    │ ┌──────────────────────────────────────────────┐│ │  03 May 2026       │  │
│    │ │ ●●●○  Evidence accumulating                  ││ │                    │  │
│    │ │       Important questions remain open         ││ │  ──────────────    │  │
│    │ └──────────────────────────────────────────────┘│ │                    │  │
│    │                                                  │ │  COVERAGE          │  │
│    │ 01 / KNOWN                                       │ │  ✓ Sources cited   │  │
│    │ What Is Known                                    │ │  ✓ Risks noted     │  │
│    │                                                  │ │  ✓ Open questions  │  │
│    │ Body text body text body text body text body     │ │  ✓ View-change     │  │
│    │ text body text body text body text body text     │ │  ✓ Manually rev'd  │  │
│    │ body text body text.                             │ │  ✓ Disclaimer      │  │
│    │                                                  │ │                    │  │
│    │ 02 / UNKNOWN                                     │ │  ──────────────    │  │
│    │ What Is Unknown                                  │ │                    │  │
│    │                                                  │ │  EDUCATIONAL NOTE  │  │
│    │ — Open question one stated precisely.            │ │  This analysis is  │  │
│    │ — Open question two stated precisely.            │ │  educational.      │  │
│    │ — Open question three stated precisely.          │ │  Not financial     │  │
│    │                                                  │ │  advice.           │  │
│    │ 03 / VIEW                                        │ │                    │  │
│    │ What Would Change This View                      │ │  Este análisis es  │  │
│    │                                                  │ │  educativo. No es  │  │
│    │ Body text body text body text.                   │ │  asesoramiento     │  │
│    │                                                  │ │  financiero.       │  │
│    │ 04 / DOCUMENTS                                   │ │  [sticky end]      │  │
│    │ Key Documents                                    │ │                    │  │
│    │ [document list component]                        │ └────────────────────┘  │
│    │                                                  │                         │
│    │ 05 / TIMELINE                                    │                         │
│    │ [horizontal timeline component]                  │                         │
│    │                                                  │                         │
│    │ 06 / RISKS                                       │                         │
│    │ Risks                                            │                         │
│    │                                                  │                         │
│    │ 07 / SOURCES                                     │                         │
│    │ Source Notes                                     │                         │
│    │ [source table component]                         │                         │
│    │                                                  │                         │
│    │ ┌─────────── DISCLAIMER ─────────────────────┐  │                         │
│    │ │ EDUCATIONAL DISCLAIMER                      │  │                         │
│    │ │ Educational text in English, full.          │  │                         │
│    │ │ Este análisis es educativo.                 │  │                         │
│    │ │ No es asesoramiento financiero.             │  │                         │
│    │ └─────────────────────────────────────────────┘  │                         │
│    │                                                  │                         │
│    │ ┌─────────── NEWSLETTER CTA ─────────────────┐  │                         │
│    │ │ RESEARCH NOTES                              │  │                         │
│    │ │ Research notes when something is worth      │  │                         │
│    │ │ documenting.                                │  │                         │
│    │ │ [Subscribe to Notes →]                      │  │                         │
│    │ └─────────────────────────────────────────────┘  │                         │
│    └──────────────────────────────────────────────────┘                         │
│                                                                                 │
│╔══════════════════════════════════ FOOTER ═══════════════════════════════════╗  │
│║ Research · Case Studies · About · Disclaimer   SwissEdge 2026              ║  │
│╚════════════════════════════════════════════════════════════════════════════╝  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Sidebar Stickiness Behaviour

```
position: sticky
top: 72px    (clears navbar height + 16px)

The sidebar begins sticky from the first scroll.
It scrolls with the page until its own height is exhausted,
then the bottom edge pins and the top scrolls away.

On articles shorter than the sidebar: sidebar is simply in-flow.
On articles much longer than the sidebar: sidebar top pins at 72px for the
full article scroll, then releases and scrolls with the footer.
```

---

## 4. Mobile Layout — 375px

### Grid

```
Viewport:             375px
Horizontal padding:   20px each side
Content width:        335px
All content:          single column, top-to-bottom
```

### Full Page Map — Mobile

```
┌──────────── 375px ─────────────┐
│▓ READING PROGRESS BAR (2px) ▓ │
│                                │
│╔═══ NAVBAR 52px (sticky) ════╗ │
│║ SwissEdge              ☰   ║ │
│╚════════════════════════════╝ │
│                                │
│ ← Research          16px top  │
│                                │
│ [SPIN-OFF]                     │  situation type badge
│ [● CANDIDATE FOR FURTHER...]  │  status badge (wraps if needed)
│                                │
│ Article Title in               │  30px serif
│ Serif Running                  │
│ to Multiple Lines              │
│                                │
│ Thesis — One sentence that     │  16px italic sans
│ describes the structural       │
│ situation and the open         │
│ research questions.            │
│                                │
│ PUBLISHED 03 May 2026          │  mono meta
│ REVIEWED  03 May 2026          │
│ ─────────────────────────────  │  1px divider
│                                │
│ ┌────────────────────────────┐ │
│ │ ●●●○  Evidence accumulating│ │  confidence indicator
│ │       Open questions remain│ │
│ └────────────────────────────┘ │
│                                │
│ 01 / KNOWN                     │  eyebrow
│ What Is Known                  │  22px serif H2
│                                │
│ Body text body text body text  │
│ body text body text.           │
│                                │
│ 02 / UNKNOWN                   │
│ What Is Unknown                │
│                                │
│ — Open question one.           │
│ — Open question two.           │
│ — Open question three.         │
│                                │
│ 03 / VIEW                      │
│ What Would Change This View    │
│                                │
│ Body text body text.           │
│                                │
│ 04 / DOCUMENTS                 │
│ Key Documents                  │
│ [stacked document cards]       │
│                                │
│ 05 / TIMELINE                  │
│ [vertical timeline]            │
│                                │
│ 06 / RISKS                     │
│ Risks                          │
│ Body text.                     │
│                                │
│ 07 / SOURCES                   │
│ Source Notes                   │
│ [stacked source cards]         │
│                                │
│ COVERAGE CHECKLIST             │
│ ✓ Primary sources cited        │
│ ✓ Key risks documented         │
│ ✓ Open questions listed        │
│ ✓ View-change conditions       │
│ ✓ Manually reviewed            │
│ ✓ Disclaimer present           │
│                                │
│ ┌── EDUCATIONAL DISCLAIMER ──┐ │
│ │ EDUCATIONAL DISCLAIMER     │ │
│ │ This analysis is education-│ │
│ │ al. Not financial advice.  │ │
│ │ Nothing here constitutes   │ │
│ │ a recommendation to buy,   │ │
│ │ sell, or hold any security.│ │
│ │                            │ │
│ │ Este análisis es educativo.│ │
│ │ No es asesoramiento        │ │
│ │ financiero.                │ │
│ └────────────────────────────┘ │
│                                │
│ ┌── NEWSLETTER CTA ──────────┐ │
│ │ RESEARCH NOTES             │ │
│ │ Research notes when        │ │
│ │ something is worth         │ │
│ │ documenting.               │ │
│ │ [Subscribe to Notes →]     │ │
│ │ Free. No spam.             │ │
│ └────────────────────────────┘ │
│                                │
│╔═══ FOOTER ══════════════════╗ │
│║ SwissEdge 2026              ║ │
│║ Disclaimer · About          ║ │
│╚════════════════════════════╝ │
└────────────────────────────────┘
```

---

## 5. Component Specifications

### 5.1 — Reading Progress Bar

```
Position:     fixed, top: 0, left: 0, z-index: 9999, width: 0→100% (JS driven)
Height:       2px
Color:        --accent (#10B981)
Transition:   none (follows scroll with zero lag)
Visibility:   hidden at scroll=0 and scroll=max
Border-radius: 0 (pure line, not rounded)
Label:        none
```

The bar communicates: "this is a long form document being read." It does not
show percentage text. It does not have an end cap or shadow.

---

### 5.2 — Sticky Navbar

```
Desktop:
  height:           56px
  position:         sticky, top: 0, z-index: 100
  background:       rgba(10,11,13,0.88) + backdrop-filter: blur(8px)
  border-bottom:    1px solid --border-default

  Left:  "SwissEdge" — serif, small-caps, 16px, --text-primary
  Right: "Research  Case Studies  Source Intelligence  About  Notes"
         Mono, 11px, uppercase, letter-spacing 0.12em, --text-tertiary
         Hover: color → --text-primary, 150ms

Mobile:
  height:           52px
  Left:  "SwissEdge" wordmark (same styling)
  Right: ☰ — 3 lines, 20px wide × 14px height, --text-tertiary, tap target 44px

Mobile menu (open state):
  Full viewport overlay, background --bg-elevated
  Nav items stacked, 24px apart, same mono styling as desktop
  Close: ✕ button top-right, same tap target
  Transition: opacity + translateY(-8px) → none, 200ms ease-out
```

---

### 5.3 — Breadcrumb

```
Content:    ← Research
Font:       mono, 12px, --text-tertiary, letter-spacing 0.04em
Hover:      color → --text-secondary, 150ms
Margin:     24px below navbar (desktop), 16px (mobile)
Arrow:      literal ← character, not an SVG

Desktop:    inline, single line
Mobile:     same

No slash separator. No full path hierarchy. One level back is sufficient.
```

---

### 5.4 — Article Header Block

Padding: 40px top (desktop), 24px top (mobile), 48px bottom.

#### 5.4a Situation Type Badge

```
Content:    e.g. "SPIN-OFF" / "CORPORATE REORGANIZATION" / "MERGER"
Font:       mono, 11px, uppercase, letter-spacing 0.12em
Color:      --text-tertiary
Background: none
Border:     1px solid --border-default
Border-radius: 2px
Padding:    2px 8px
Display:    inline-block
```

#### 5.4b Status Badge

The status badge is the primary research signal. First visual element after the breadcrumb.

```
Position:   inline-block, 8px left margin from situation type badge
            (wraps to next line on mobile if combined width exceeds column)
Border-radius: 2px
Padding:    2px 10px
Font:       mono, 11px, uppercase, letter-spacing 0.12em

── monitor ────────────────────────────────────────────────────────────────
  Label:       "● MONITOR"
  Text:        --status-monitor (#6B7280)
  Border:      1px solid #374151
  Background:  transparent
  Animation:   none

── not actionable ─────────────────────────────────────────────────────────
  Label:       "○ NOT ACTIONABLE"
  Text:        --status-not-actionable (#4B5563)
  Border:      1px solid #1E2229
  Background:  transparent
  Animation:   none

── needs more work ────────────────────────────────────────────────────────
  Label:       "◐ NEEDS MORE WORK"
  Text:        --status-needs-work (#F59E0B)
  Border:      1px solid rgba(245,158,11,0.40)
  Background:  transparent
  Animation:   none (uncertainty must not pulse — it would imply dynamism)

── candidate for further research ─────────────────────────────────────────
  Label:       "● CANDIDATE FOR FURTHER RESEARCH"
  Text:        --status-candidate (#10B981)
  Border:      1px solid rgba(16,185,129,0.40)
  Background:  transparent
  Animation:   box-shadow pulse (see Motion §8.2)
               This is the only badge that glows.
               Glow = "reviewed, research is live and active."
               Not "invest now."
```

**Absolute rule:** No other label variants. No "strong candidate." No "high conviction." No "clear setup." These four labels are complete.

#### 5.4c Article Title

```
Font:         serif
Desktop:      48px, line-height 1.15, weight 400
Mobile:       30px, line-height 1.20, weight 400
Color:        --text-primary (#E8EAF0)
Max-width:    620px (desktop), 335px (mobile)
Margin-top:   20px from badges
Margin-bottom: 16px

Title format: "Company Name — The Structural Event"
              em-dash separator, not colon, not hyphen
```

**Title rules:**
- Never starts with "Why" (clickbait register)
- Never contains exclamation mark
- Never implies price movement or investor action
- Maximum 14 words strongly preferred
- Describes the structural event, not its interpretation

#### 5.4d Thesis Line

```
Prefix:       "Thesis —" in mono, 12px, --text-tertiary
Font:         sans, 18px desktop / 16px mobile, italic
Color:        --text-secondary (#9CA3AF)
Line-height:  1.55
Max-width:    640px (desktop)
Margin-top:   16px

The prefix "Thesis —" sits on the same line as the first words.
It does not have its own line.
```

**Thesis rules:**
- One sentence maximum, 20–40 words
- Ends with a period
- Describes the research question, not an investment view
- No buy/sell language
- States what the situation is and why research attention is warranted, not why someone should act

**Example:**
> Thesis — A planned separation of two structurally distinct business units has been announced; this note documents the available public evidence, the open questions, and the conditions that would alter the research status.

#### 5.4e Metadata Strip

```
Font:         mono, 12px, --text-tertiary, letter-spacing 0.04em
Separator:    · (centred dot, space each side)
Margin-top:   20px
Padding-top:  20px
Border-top:   1px solid --border-default

Content:      PUBLISHED [DD Mon YYYY] · REVIEWED [DD Mon YYYY]

If not yet reviewed: omit the REVIEWED field entirely.
Do not show "REVIEWED —" with a blank or "never."
```

---

### 5.5 — Confidence / Uncertainty Indicator

**Critical design note:** This component measures coverage of available public information — not probability of any outcome. The wording must make this explicit.

```
Container:
  Margin-top:    24px
  Padding:       12px 16px
  Background:    --bg-elevated (#14171C)
  Border:        1px solid --border-default
  Border-left:   2px solid [level-specific color — see below]
  Border-radius: 2px

Dot row (left):
  Four 8px circles, 4px gap between them
  Filled circle: border-radius 50%, background = level color
  Hollow circle: border-radius 50%, border 1px solid --border-default, background transparent

Text row (right of dots, 12px gap):
  Label:    sans, 13px, --text-secondary
  Sub-text: mono, 11px, --text-tertiary, 4px below label

── Level 1 — Information Incomplete ──────────────────────────────────────
  Dots:       ●○○○
  Color:      --signal-none (#374151)
  Label:      "Information incomplete"
  Sub:        "Primary sources not yet located"

── Level 2 — Early Signals ───────────────────────────────────────────────
  Dots:       ●●○○
  Color:      --signal-low (#6B7280)
  Label:      "Early signals"
  Sub:        "Initial filings reviewed — open questions are numerous"

── Level 3 — Evidence Accumulating ───────────────────────────────────────
  Dots:       ●●●○
  Color:      --signal-medium (#F59E0B)
  Label:      "Evidence accumulating"
  Sub:        "Key documents reviewed — important questions remain open"

── Level 4 — Well-Documented ─────────────────────────────────────────────
  Dots:       ●●●●
  Color:      --signal-high (#10B981)
  Label:      "Well-documented"
  Sub:        "Primary sources reviewed — open questions are minor"
```

**Editorial rule:** The level is set manually by the human reviewer during approval. It is never auto-generated. A note at level 4 still requires open questions in the "What Is Unknown" section — "well-documented" means comprehensive coverage of available public information, not certainty of outcome.

---

### 5.6 — Section Structure

```
Section eyebrow (optional, precedes H2):
  Font:         mono, 10px, uppercase, letter-spacing 0.12em
  Color:        --text-tertiary
  Content:      "01 / KNOWN" format
  Margin-bottom: 6px

Section H2:
  Font:         serif, 28px (desktop) / 22px (mobile)
  Color:        --text-primary
  Margin-top:   48px desktop / 36px mobile (from previous section bottom)
  Margin-bottom: 16px

Section divider (between sections):
  1px horizontal, --border-subtle, full article column width
  8px above divider, 0px below (H2 margin handles spacing)
  Not between every section — only between major blocks
```

---

### 5.7 — Body Text

```
Font:         sans, 16px / 15px mobile
Color:        --text-primary
Line-height:  1.75 desktop / 1.80 mobile
Max-width:    68ch
Paragraph gap: 16px between consecutive paragraphs
First paragraph after H2: no top margin

Inline elements:
  Italic:       for qualifications, uncertainty phrases, named source references
  Bold:         never in body text (bold implies hierarchy, not emphasis)
  Links:        --text-primary, underline --border-default; hover: underline → --accent
                All external links: target="_blank" rel="noopener noreferrer"

Lists (body):
  Prefix:       — (em dash), --text-tertiary, 24px left indent
  No bullets, no discs, no numbers (use timeline component for ordered events)
  Item spacing: 8px
```

---

### 5.8 — What Is Known / Unknown / What Would Change the View

These three sections form the intellectual core. They must appear in this order.

```
── What Is Known ─────────────────────────────────────────────────────────
  H2:      "What Is Known"
  Content: Factual claims from public documents.
           Each claim attributable to a named public source.
           Format: "[Fact]. (Source: [Document name], [date])"
           No interpretation beyond what the document states.
           3–8 claims, presented as short paragraphs or em-dash list.

── What Is Unknown ───────────────────────────────────────────────────────
  H2:      "What Is Unknown"
  Content: Open questions in em-dash list format.
           Each item is a specific observable question.
           Format: "— Whether [specific thing] has been [confirmed/filed/disclosed]."
           This section cannot be empty under any circumstances.
           A note without open questions implies false certainty.

── What Would Change This View ───────────────────────────────────────────
  H2:      "What Would Change This Research View"
  Content: Two sub-groups, each as an em-dash list.
           Both groups must appear. A view that only goes one direction is not falsifiable.

  Sub-group A — "What would increase research interest:"
    Format: "— [Specific observable event] that would confirm or advance the situation."

  Sub-group B — "What would decrease research interest:"
    Format: "— [Specific observable event] that would indicate the situation has changed negatively."
```

Sub-group headers: sans, 14px, italic, --text-secondary. Indented 4px. No separate H3.

---

### 5.9 — Key Documents Component

```
Container:
  Border:        1px solid --border-default
  Border-radius: 2px
  Background:    --bg-surface
  Overflow:      hidden

Each document row:
  Padding:       12px 16px
  Border-bottom: 1px solid --border-default (last row: none)
  Layout:        3-column flex row
  Hover:         background → --bg-overlay, border-left 2px solid --border-active, 150ms

Column 1 — Type badge (fixed 120px):
  Font:          mono, 10px, uppercase, letter-spacing 0.10em
  Background:    --bg-elevated
  Border:        1px solid --border-default
  Border-radius: 2px
  Padding:       2px 6px
  Truncate:      ellipsis if label exceeds width
  Examples:      SEC FILING, PROXY STMT, COURT ORDER, PRESS RELEASE, ANNUAL REPORT

Column 2 — Title and date (flex grow):
  Title:         sans, 14px, --text-primary, link on hover (underline --accent)
  Date:          mono, 11px, --text-tertiary, 2px below title
  All URLs:      publicly accessible only

Column 3 — Signal quality (fixed 80px, right-aligned):
  Dot:           8px circle, colored by signal quality
  Label:         mono, 10px, next to dot (HIGH / MEDIUM / LOW / NO SIGNAL)
  Tooltip:       appears on hover, explains the rating

Mobile:
  All 3 columns stack to a single card layout
  Type badge: top-left, small
  Title: below, full width
  Date + signal quality: bottom row, flex space-between
```

---

### 5.10 — Timeline Component

The timeline is the most visually distinctive component. Approach: horizontal on desktop (scrollable), vertical on mobile.

#### Desktop Timeline

```
Container:
  Width:         100% of article column
  Height:        140px
  Overflow-x:    scroll (custom scrollbar: 2px track --border-default, thumb --border-active)
  Padding:       24px 0
  User-select:   none

Track:
  1px horizontal line, --border-default
  Spans full scrollable width
  Vertically centered in container

Minimum node spacing:   130px
Maximum nodes shown:    8 before scroll is implied

── Node types ─────────────────────────────────────────────────────────────
  Confirmed event:
    Circle:    10px, fill --accent-bright (#34D399), no border
  Unconfirmed / anticipated:
    Circle:    10px, no fill, border 1px dashed --signal-medium (#F59E0B)
  Historical / completed:
    Circle:    10px, fill --text-tertiary (#6B7280), no border
  Current / active edge (rightmost confirmed):
    Circle:    10px, fill --accent (#10B981), no border
    Animation: ring pulse (see §8.3)
  Future / speculative:
    Circle:    10px, no fill, border 1px dashed --border-default

Node labels (below track, centered on node):
  Date:          mono, 10px, --text-tertiary
  Title:         sans, 12px, --text-secondary, max 2 lines, centered, ellipsis at 3rd line

Hover tooltip (above node):
  Trigger:       mouseenter / focus
  Background:    --bg-elevated
  Border:        1px solid --border-active
  Border-radius: 2px
  Padding:       12px 14px
  Shadow:        0 8px 32px rgba(0,0,0,0.65)
  Content:
    [Date — mono, 11px, --text-tertiary]
    [Event title — sans, 14px, --text-primary]
    [2–3 sentence description — sans, 13px, --text-secondary]
    [Source — mono, 11px, --accent, link to public document]
  Animation:     fade-in + translateY(-4px) → 0, 150ms ease-out
  Dismiss:       mouseleave or Escape key
```

#### Mobile Timeline (Vertical)

```
Track:           2px vertical line, --border-default, 16px from left edge
Nodes:           8px circles, centered on track (same type styling as desktop)
Spacing:         52px minimum between nodes
Label layout:    right of track, 28px left offset
  Date:          mono, 10px, --text-tertiary
  Title:         sans, 13px, --text-secondary, below date

Tap interaction: expands inline block below the label
  Content:       same as tooltip content
  Transition:    height 0 → auto, 200ms ease-out (use max-height for CSS animation)
  Dismiss:       second tap on same node, or tap another node
```

**Source rule:** Every confirmed timeline event must cite a public source. Events without sources are labeled "pending confirmation" with a dashed node style.

---

### 5.11 — Source Notes Table

```
Container:
  Border:        1px solid --border-default
  Border-radius: 2px
  Overflow:      hidden

Header row:
  Background:    --bg-elevated
  Padding:       10px 16px
  Font:          mono, 10px, uppercase, letter-spacing 0.12em, --text-tertiary
  Columns:
    SOURCE NAME       40%
    CATEGORY          20%
    SIGNAL QUALITY    15%
    WHAT IT SHOWS     25%

Data rows:
  Padding:       12px 16px
  Border-top:    1px solid --border-subtle
  Background:    --bg-surface (default), --bg-overlay (hover, 150ms)

  Source name cell:
    Font:        sans, 13px, --text-primary
    If URL:      link styling, opens new tab
    No bold

  Category cell:
    Font:        mono, 11px, --text-tertiary
    Values:      "Primary Regulatory" / "Company-Issued" / "Independent" / "Commentary"

  Signal quality cell:
    Dot + label:
      ● HIGH       --signal-high (#10B981)
      ◐ MEDIUM     --signal-medium (#F59E0B)
      ○ LOW        --signal-low (#6B7280)
      · NO SIGNAL  --signal-none (#374151)
    Font:        mono, 10px (the label is self-describing)

  What it shows cell:
    Font:        sans, 12px, --text-secondary
    Short phrase, not a sentence
    Examples:    "Separation timeline" / "Board incentive structure"

Mobile:
  Columns collapse to stacked source cards
  Each card:     source name (primary) + category badge + signal quality dot + what it shows (below)
```

**Source safety rule:** Public source name only. No internal source IDs, scanner registry entries, private notes, API routes, or operational metadata. If a source cannot be named publicly, it must not appear in the source notes table.

---

### 5.12 — Coverage Checklist (Sidebar — Desktop / Inline — Mobile)

```
Container:
  Background:    --bg-elevated
  Border:        1px solid --border-default
  Border-radius: 2px
  Padding:       16px

Header:
  Font:          mono, 10px, uppercase, letter-spacing 0.12em, --text-tertiary
  Content:       "COVERAGE CHECKLIST"
  Margin-bottom: 12px

Checklist items:
  Layout:        [icon] [label] — flex row, 8px gap
  Spacing:       8px between items

  Checked (✓):
    Icon:        "✓" mono, 12px, --accent (#10B981)
    Label:       sans, 12px, --text-secondary

  Unchecked (✗):
    Icon:        "✗" mono, 12px, --text-ghost (#374151)
    Label:       sans, 12px, --text-ghost

Items:
  ✓/✗ Primary sources cited
  ✓/✗ Key risks documented
  ✓/✗ Open questions listed
  ✓/✗ "What would change view" included
  ✓/✗ Sources evaluated for signal quality
  ✓/✗ Manually reviewed before publication
  ✓   Educational disclaimer present (always checked if published)
```

The disclaimer item is always checked. If the disclaimer is absent, the note must not be published. This checklist is read-only — it is not an interactive form.

---

### 5.13 — Educational Disclaimer Block

This is not a footnote. It appears twice: in the sticky sidebar (condensed) and at the bottom of the article body (full).

```
Container (full — article body):
  Background:    --bg-elevated
  Border:        1px solid --warning-border (rgba(245,158,11,0.30))
  Border-left:   2px solid --warning (#F59E0B)
  Border-radius: 2px
  Padding:       16px 16px 16px 20px
  Margin-top:    48px

Header label:
  Font:          mono, 10px, uppercase, letter-spacing 0.12em
  Color:         --warning (#F59E0B)
  Content:       "EDUCATIONAL DISCLAIMER"
  Margin-bottom: 10px

English text:
  Font:          sans, 13px, --text-secondary, line-height 1.65

Spanish text (canonical line, below English, 8px gap):
  Font:          sans, 13px, italic, --text-tertiary
  Content:       "Este análisis es educativo. No es asesoramiento financiero."

Container (condensed — sidebar):
  Same border styling, smaller padding: 12px 12px 12px 16px

Condensed content (English only, shortened):
  "This analysis is educational.
   Not financial advice.
   Nothing here constitutes a recommendation
   to buy, sell, or hold any security."

Condensed content (Spanish canonical, below):
  "Este análisis es educativo.
   No es asesoramiento financiero."
```

**Rule:** Neither version of the disclaimer can be hidden in an accordion, tooltip, or collapsed section.

---

### 5.14 — Newsletter / Substack CTA

```
Container:
  Background:    --bg-surface
  Border:        1px solid --border-default
  Border-radius: 2px
  Padding:       32px (desktop) / 24px (mobile)
  Margin-top:    48px

Eyebrow:
  Font:          mono, 10px, uppercase, letter-spacing 0.12em, --text-tertiary
  Content:       "RESEARCH NOTES"

Headline:
  Font:          serif, 22px / 20px mobile
  Color:         --text-primary
  Margin-top:    8px
  Content:       "Research notes when something is worth documenting."

Body:
  Font:          sans, 14px, --text-secondary, line-height 1.65
  Margin-top:    8px
  Content:       "No tips. No signals. When a situation warrants a structured
                  note, we publish one. Process and sources, plainly written."

CTA button:
  Label:         "Subscribe to Notes →"
  Font:          mono, 12px, --text-primary
  Border:        1px solid --border-default
  Padding:       8px 18px
  Border-radius: 2px
  Background:    none
  Hover:         border-color → --border-active (150ms)
  Margin-top:    20px

Trust line:
  Font:          mono, 10px, --text-ghost
  Content:       "Free. No spam. Unsubscribe anytime."
  Margin-top:    10px
```

---

## 6. Visual Hierarchy Ladder

Reading order and visual weight, from first glance to deep read.

```
Rank  Element                           Weight   Why
────  ──────────────────────────────    ──────   ────────────────────────────────────────
 1    Status badge                      High     Immediate research state signal before reading
 2    Article title (serif 48px)        High     Establishes subject
 3    Confidence indicator              Medium   Epistemic framing before body
 4    Thesis line (italic 18px)         Medium   Research question, not conclusion
 5    "What Is Known" section           Medium   Primary substance
 6    Timeline component                Medium   Visual scan anchor, structural overview
 7    "What Is Unknown"                 Medium   Equal weight to Known — intellectually honest
 8    "What Would Change This View"     Medium   Falsifiability — separates research from opinion
 9    Source Notes table                Low-Med  Evidence chain
10    Key Documents list                Low-Med  Primary sources
11    Risks section                     Low-Med  Structural caution
12    Coverage Checklist (sidebar)      Low      At-a-glance verification
13    Disclaimer block                  Low      Permanent, unignorable
14    Newsletter CTA                    Lowest   Invitation, not a conversion goal
```

The hierarchy is unconventional: uncertainty content (confidence indicator, "What Is Unknown") carries nearly the same weight as the affirmative content. This is the brand signal.

---

## 7. Hover States — Complete Reference

All transitions: 150ms ease-out unless noted.

```
Element                    Rest state              Hover state
──────────────────────     ──────────────────────  ──────────────────────────
Navbar link                --text-tertiary          --text-primary
Breadcrumb link            --text-tertiary          --text-secondary
Body link                  faint underline          underline → --accent
Document row               --bg-surface             --bg-overlay + 2px left border --border-active
Source table row           --bg-surface             --bg-overlay
Timeline node              default                  tooltip appears above node
Timeline node focus        same as hover            same as hover (keyboard accessible)
Newsletter CTA button      border --border-default  border --border-active
Footer links               --text-ghost             --text-tertiary
Coverage checklist         static (non-interactive) —
```

**Forbidden hover patterns:**
- Scaling card (no transform: scale)
- Background color fill change (only border and text change)
- Color fill on status badges (border glow only)

---

## 8. Motion and Animation Specification

Total animation budget for this page: **4 defined interactions**.

### 8.1 — Page Entry (Header Block Only)

```
Trigger:     once, on page load
Elements:    badges, title, thesis, metadata strip, confidence indicator
             (body sections and sidebar: render without animation)

Animation:   opacity: 0→1, transform: translateY(6px)→translateY(0)
Duration:    300ms
Easing:      cubic-bezier(0.0, 0.0, 0.2, 1)

Stagger:
  Badges (situation + status):    delay 0ms
  Title:                          delay 50ms
  Thesis + metadata:              delay 100ms
  Confidence indicator:           delay 150ms
```

### 8.2 — Status Badge Glow (Candidate Only)

```
Property:    box-shadow on badge
Keyframes:   0%   { box-shadow: 0 0 6px rgba(16,185,129,0.30); }
             50%  { box-shadow: 0 0 10px rgba(16,185,129,0.60); }
             100% { box-shadow: 0 0 6px rgba(16,185,129,0.30); }
Duration:    4s
Iteration:   infinite
Easing:      ease-in-out
Applies to:  candidate status badge ONLY
```

### 8.3 — Timeline Active Node Pulse

```
Property:    box-shadow ring expansion
Keyframes:   0%   { box-shadow: 0 0 0 0px rgba(16,185,129,0.50); }
             100% { box-shadow: 0 0 0 6px rgba(16,185,129,0.00); }
Duration:    2s
Iteration:   infinite
Easing:      ease-out
Applies to:  the rightmost confirmed event node (labeled "Current")
```

### 8.4 — Reading Progress Bar

```
Not an animation — CSS width property driven by JS scrollY / document.body.scrollHeight.
No CSS transition applied (must be instantaneous to feel natural).
```

### Explicitly Excluded Animations

```
✗ Section reveal on scroll
✗ Parallax on any element
✗ Hover scale / transform
✗ Background motion
✗ Loading skeleton shimmer
✗ Font size transitions
✗ Gradient animation
✗ Sidebar entrance
✗ Footer entrance
✗ Any animation on body content sections
```

---

## 9. Accessibility Specification

### Semantic HTML Structure

```html
<div role="progressbar" aria-valuenow="{n}" aria-valuemin="0"
     aria-valuemax="100" aria-label="Reading progress">
  <!-- progress bar -->
</div>

<header>
  <nav aria-label="Main navigation">
    <!-- navbar -->
  </nav>
</header>

<main>
  <nav aria-label="Breadcrumb">
    <a href="/research">Research</a>
  </nav>

  <article>
    <header>
      <!-- badges, title, thesis, metadata, confidence indicator -->
    </header>

    <section aria-labelledby="known-heading">
      <h2 id="known-heading">What Is Known</h2>
      <!-- content -->
    </section>

    <section aria-labelledby="unknown-heading">
      <h2 id="unknown-heading">What Is Unknown</h2>
    </section>

    <section aria-labelledby="view-heading">
      <h2 id="view-heading">What Would Change This View</h2>
    </section>

    <section aria-labelledby="docs-heading">
      <h2 id="docs-heading">Key Documents</h2>
    </section>

    <section aria-labelledby="timeline-heading">
      <h2 id="timeline-heading">Timeline</h2>
      <ol role="list"> <!-- timeline events as ordered list -->
      </ol>
    </section>

    <section aria-labelledby="risks-heading">
      <h2 id="risks-heading">Risks</h2>
    </section>

    <section aria-labelledby="sources-heading">
      <h2 id="sources-heading">Source Notes</h2>
    </section>

    <aside aria-label="Educational disclaimer">
      <!-- disclaimer block -->
    </aside>

    <section aria-label="Newsletter">
      <!-- newsletter CTA -->
    </section>
  </article>

  <aside aria-label="Research summary" aria-sticky="true">
    <!-- sticky sidebar -->
  </aside>
</main>

<footer>
  <!-- footer -->
</footer>
```

### ARIA — Component Level

```
Status badge:
  aria-label="Research status: [full label text]"
  (abbreviated badge text may not be screen-reader sufficient)

Confidence indicator:
  aria-label="Research coverage level: [level name]. [sub-text]."
  role="img" (the dot pattern is decorative; text carries meaning)

Timeline container:
  role="list"
  aria-label="Research timeline"

Timeline node:
  role="listitem"
  aria-label="[Event title], [date]. [source if present]."
  tabindex="0"
  When Enter/Space: opens tooltip inline (aria-expanded="true/false")

Tooltip (timeline):
  role="tooltip"
  id="tooltip-[node-id]"
  aria-labelledby points from node to tooltip

External links:
  aria-label="[text] (opens in new tab)"
  rel="noopener noreferrer"

Mobile hamburger:
  aria-label="Open navigation menu"
  aria-expanded="false/true"
  aria-controls="mobile-menu"

Disclaimer block:
  role="note"
  aria-label="Educational disclaimer"

Coverage checklist:
  role="list"
  Each item: role="listitem", read as "[status] [label]"
```

### Colour Contrast Audit

```
Pair                                          Ratio    WCAG AA
--text-primary on --bg-base                   ~18:1    ✓ PASS
--text-secondary on --bg-base                 ~7.1:1   ✓ PASS
--text-tertiary on --bg-base                  ~4.6:1   ✓ PASS (borderline — use 12px+ always)
--text-tertiary on --bg-surface               ~4.5:1   ✓ PASS (verify in implementation)
--accent on --bg-base                         ~6.8:1   ✓ PASS
--warning on --bg-base                        ~8.2:1   ✓ PASS
--status-not-actionable on --bg-base          ~2.8:1   ✗ FAIL (use --text-tertiary as text, badge border only)
--text-ghost on --bg-base                     ~2.2:1   ✗ FAIL (decorative only — never sole information carrier)
```

### Focus Rings

```css
:focus-visible {
  outline: 2px solid var(--accent);    /* #10B981 */
  outline-offset: 3px;
  border-radius: inherit;              /* matches element's own radius */
}
```

No `outline: none` without a replacement. No `outline: 0`.

### Keyboard Navigation

```
Global tab order:
  1.  Skip-to-content link (visually hidden, revealed on first Tab press)
      Content: "Skip to main content"
      Target: main element
  2.  Navbar logo
  3.  All nav links (left to right)
  4.  Breadcrumb link
  5.  Article body links in document order
  6.  Timeline (enter timeline with Tab, navigate nodes with ← → arrows)
  7.  Document links in key documents section
  8.  Source links in source notes
  9.  Newsletter CTA button
  10. Footer links

Timeline keyboard:
  Tab:        focus the timeline container
  ← →:       navigate between nodes
  Enter/Space: open tooltip for focused node
  Escape:     close tooltip, return focus to node
```

### Reduced Motion

```css
@media (prefers-reduced-motion: reduce) {

  /* Disable status badge glow animation */
  [data-status="candidate"] {
    animation: none;
    box-shadow: 0 0 6px rgba(16,185,129,0.30);  /* static glow, no pulse */
  }

  /* Disable timeline active node pulse */
  .timeline-node--current {
    animation: none;
  }

  /* Disable page entry stagger */
  .article-header > * {
    opacity: 1;
    transform: none;
    transition: none;
  }

  /* Keep reading progress bar — it is scroll-driven, not time-driven */
  /* Keep hover border transitions — they are interactive feedback, not decoration */
}
```

---

## 10. Public Safety Language Rules

### Mandatory Presence (pre-publication checklist)

```
✓ Status badge — one of four approved labels only
✓ Confidence indicator — set manually by reviewer
✓ "What Is Known" — sourced factual claims only
✓ "What Is Unknown" — cannot be empty
✓ "What Would Change This View" — both increase and decrease directions
✓ Educational disclaimer — full English + Spanish canonical line
✓ Coverage checklist — manually reviewed item checked
✓ No buy/sell language anywhere on the page (title, thesis, body, sources)
```

### Forbidden Terms and Phrases

The following are banned anywhere on the public article page: headings, body text, thesis, source descriptions, checklist labels, CTA copy, meta tags.

```
BUY-SIDE:      buy, purchase shares, go long, long position, recommend buying,
               strong buy, add to portfolio, accumulate

SELL-SIDE:     sell, go short, short position, recommend selling, strong sell,
               exit position, reduce exposure

PRICE-BASED:   target price, price target, fair value, intrinsic value, upside,
               downside, return, gain, yield (in investment context)

HYPE:          must-watch, can't miss, everyone's missing this, hidden gem,
               unique opportunity, massive upside, game-changer, market-moving

AUTHORITY:     proprietary, exclusive intelligence, insider, proven approach,
               track record, our model, trust us, alpha, edge

CERTAINTY:     clearly, obviously, without doubt, it is certain, will happen
```

### Approved Status Labels (complete set)

```
monitor
not actionable
needs more work
candidate for further research
```

No variants. No additions. "Strong candidate" is not allowed.

### Source Language Rules

```
✓ "Primary regulatory source — [filing name], [date]"
✓ "Company-issued document — [document name], [date]"
✓ "Independent analysis — [publication name]"
✓ "Secondary commentary — [outlet name]"

✗ "Proprietary source"
✗ "Private intelligence"
✗ "Exclusive data feed"
✗ "Our model" or "our AI"
✗ Any source not publicly accessible by any reader
```

### Uncertainty Framing Rules

```
✓ "As of [date], [fact] has not been confirmed in public filings."
✓ "The proxy statement, anticipated in [quarter], has not yet been filed."
✓ "This view may change if [specific observable event] occurs."
✓ "The filing language is consistent with [interpretation]; independent verification required."

✗ "Clearly, the company intends to..."
✗ "Obviously, this situation is..."
✗ "Without doubt, the separation will..."
✗ "The market is missing this."
✗ "Investors should consider..."
```

---

## 11. What Not to Include

Explicit exclusions for the article page.

```
Price charts or tickers
  Why: implies trading orientation

Target prices or return estimates
  Why: financial advice, prohibited

Buy / sell / hold labels
  Why: investment recommendation language

Performance claims or past-return references
  Why: implies advisory capability, prohibited

"Opportunity" framing
  Why: implies investment action is warranted

Social sharing button bar
  Why: optimises for virality, not depth. Readers who want to share will copy the URL.

Comment section
  Why: investment comment sections attract noise and unsolicited advice

View / read / engagement count
  Why: social proof anchors readers to popularity over quality

Advertisements or sponsored content labels
  Why: creates conflict of interest, incompatible with trust model

Email popup or subscription modal
  Why: interrupts reading, incompatible with the brand register

Countdown timer or urgency element
  Why: implies time-sensitive action is needed

Member count or social proof numbers
  Why: implies popularity = quality, misleads

Author photo or biography panel (article page)
  Why: SwissEdge is a research practice, not a personality platform

Internal IDs (research case ID, situation ID, run ID, draft ID)
  Why: private operational information, must never be public

VPS details, Tailscale configuration, API routes, file paths, system logs
  Why: operational metadata, never public-safe

Private research notes not manually approved for public use
  Why: not part of the public draft pipeline

"AI-powered" or "AI-generated" branding
  Why: AI is a tool in the process, not the product; never lead with it

Chatbot, AI assistant widget, "ask me anything"
  Why: implies advisory or interactive advice capability

Animated background (stars, particles, radar on article page)
  Why: the radar is homepage-only; article pages are static editorial

Any content in "unpublished" or "draft" status
  Why: must not be accessible; only approved drafts are served
```

---

## 12. Example Article Copy — Complete Page Draft

A full example of one published research note. Written in SwissEdge voice. No real company, ticker, or situation. Structural illustration only.

---

**Badges (header)**

```
[CORPORATE SEPARATION]   [● CANDIDATE FOR FURTHER RESEARCH]
```

---

**Title**

```
Meridian Group — Planned Separation of Industrial and Consumer Divisions
```

---

**Thesis**

```
Thesis — A conglomerate has publicly announced an intention to separate two
structurally distinct businesses; this note documents the available public
evidence, the open questions, and the conditions that would alter the
research status.
```

---

**Metadata strip**

```
PUBLISHED 03 May 2026  ·  REVIEWED 03 May 2026
```

---

**Confidence indicator**

```
●●●○  Evidence accumulating
      Key documents reviewed — important questions remain open
```

---

**01 / KNOWN — What Is Known**

The board of Meridian Group announced on 14 February 2026 the intention to separate its Industrial Solutions division from its Consumer Products division into two independent publicly-traded entities. The announcement was made via exchange notice filed on the same date. (Source: Exchange Notice, 14 February 2026.)

A Form 8-K, filed concurrently, confirmed the formation of a three-member independent board committee to oversee the separation process. The 8-K referenced "completion in the second half of 2026, subject to regulatory and shareholder approvals," but did not specify individual milestone dates. (Source: Form 8-K, 14 February 2026, Section 2.1.)

The annual proxy statement filed on 01 March 2026 contains amendments to executive compensation arrangements, including separation-contingent equity vesting provisions for three named officers. This is consistent with — but not exclusively indicative of — an ongoing formal separation process. (Source: DEF 14A Proxy Statement, 01 March 2026, Exhibit A.)

---

**02 / UNKNOWN — What Is Unknown**

— Whether a Form 10 or equivalent registration statement has been filed or is currently in preparation for the to-be-separated entity.

— Whether regulatory approval has been sought or is anticipated from any jurisdiction.

— How debt obligations and existing collective bargaining arrangements will be allocated between the two entities.

— Whether shareholder approval will be sought via a separate vote or whether the board has authority under its current charter to proceed without one.

— Whether the referenced "second half of 2026" window remains operative given no specific milestone dates have been disclosed since February.

---

**03 / VIEW — What Would Change This Research View**

*What would increase research interest:*

— Filing of a Form 10 registration statement, which would initiate a formal SEC review period and provide detailed financial disclosure for the new entity.

— Announcement of specific separation milestone dates in a subsequent regulatory filing.

— Publication of a separation agreement document disclosing asset and liability allocation terms.

*What would decrease research interest:*

— Regulatory filing disclosing suspension or cancellation of the announced separation plans.

— Filing indicating a material adverse change in business conditions that may prevent or indefinitely delay completion.

— Proxy update or board statement indicating that separation-contingent compensation provisions have been removed or restructured.

---

**04 / DOCUMENTS — Key Documents**

```
┌──────────────────┬──────────────────────────────────┬───────────┐
│ EXCHANGE NOTICE  │ Separation Announcement          │ ● HIGH    │
│ FORM 8-K         │ Board Committee Disclosure       │ ● HIGH    │
│ PROXY STMT       │ Executive Compensation Amendment │ ● HIGH    │
│ PRESS RELEASE    │ Initial Announcement Coverage    │ ◐ MEDIUM  │
└──────────────────┴──────────────────────────────────┴───────────┘
All documents publicly accessible.
```

---

**05 / TIMELINE**

```
○──────────────────●─────────────────●──────────────────◉
14 Feb 2026        14 Feb 2026       01 Mar 2026        May 2026
Exchange Notice    Form 8-K          DEF 14A Proxy       Monitoring
Announced          Board committee   Comp. amendment     (Form 10 pending)
separation         formed            filed
```

---

**06 / RISKS — Risks**

**Announcement risk.** Separation announcements are subject to withdrawal. The 8-K language ("subject to regulatory and shareholder approvals") indicates conditional dependencies that could delay or prevent completion. No binding commitment to a specific timeline has been disclosed.

**Disclosure incompleteness.** The capital structure of each separated entity has not been disclosed. Assessment of the independent financial profile of each business from public information alone is not currently possible.

**Regulatory dependency.** No specific jurisdictions requiring approval have been named. If approvals are needed from multiple regulatory bodies, timeline extension risk increases without additional public disclosure.

**Timeline uncertainty.** "Second half of 2026" is a wide window. No specific milestone dates have been publicly committed as of the most recent filing.

---

**07 / SOURCES — Source Notes**

```
┌────────────────────────────┬──────────────────────┬──────────┬─────────────────────┐
│ SOURCE                     │ CATEGORY             │ QUALITY  │ WHAT IT SHOWS       │
├────────────────────────────┼──────────────────────┼──────────┼─────────────────────┤
│ Exchange Notice (Feb 2026) │ Primary Regulatory   │ ● HIGH   │ Announcement date   │
│ Form 8-K (Feb 2026)        │ Primary Regulatory   │ ● HIGH   │ Board structure     │
│ DEF 14A Proxy (Mar 2026)   │ Company-Issued       │ ● HIGH   │ Comp. amendments    │
│ Financial press (Feb 2026) │ Commentary           │ ○ LOW    │ Market awareness    │
└────────────────────────────┴──────────────────────┴──────────┴─────────────────────┘
All sources referenced in this note are publicly accessible.
```

---

**Coverage Checklist (sidebar / inline on mobile)**

```
✓  Primary sources cited
✓  Key risks documented
✓  Open questions listed (5 items)
✓  View-change conditions — both directions
✓  Sources evaluated for signal quality
✓  Manually reviewed before publication
✓  Educational disclaimer present
```

---

**Educational Disclaimer**

> EDUCATIONAL DISCLAIMER
>
> This analysis is published for educational and informational purposes only. Nothing in this note constitutes financial advice, a recommendation to buy, sell, or hold any security, or an offer of any kind. Research notes document a process of analysis and reflect information available at the time of writing. This view may change as new information becomes available.
>
> *Este análisis es educativo. No es asesoramiento financiero.*

---

**Newsletter CTA**

> RESEARCH NOTES
>
> Research notes when something is worth documenting.
>
> No tips. No signals. When a situation warrants a structured note, we publish one. Process and sources, plainly written.
>
> [Subscribe to Notes →]
>
> Free. No spam. Unsubscribe anytime.

---

## 13. Figma Frame Specification

### Required Frames

```
Frame 1 — Desktop Article: Full Page
  Width:       1440px
  Height:      auto (extend to include all sections)
  Background:  #0A0B0D

Frame 2 — Desktop Article: First Viewport
  Width:       1440px
  Height:      900px
  Shows:       navbar + header block through confidence indicator + first section heading

Frame 3 — Mobile Article: Full Page
  Width:       375px
  Height:      auto

Frame 4 — Mobile Article: First Viewport
  Width:       375px
  Height:      812px
  Shows:       navbar + article header through confidence indicator

Frame 5 — Component: Timeline (Desktop)
  Width:       720px
  Height:      200px
  Shows:       5 nodes (confirmed/unconfirmed/current), hover tooltip on node 3

Frame 6 — Component: Status Badges (All States)
  Width:       500px
  Height:      200px
  Shows:       all 4 badge variants + candidate glow state

Frame 7 — Component: Source Notes Table
  Width:       720px
  Height:      auto
  Shows:       4 rows with varying signal quality

Frame 8 — Component: Confidence Indicator (All Levels)
  Width:       420px
  Height:      280px
  Shows:       all 4 levels stacked vertically

Frame 9 — Component: Disclaimer Block
  Width:       720px
  Height:      auto
  Shows:       full disclaimer + condensed sidebar version side by side
```

### Layer Naming Convention

```
[page] / [section] / [component] / [variant] / [element]

Examples:
  article / header / status-badge / candidate / container
  article / header / status-badge / candidate / dot
  article / header / status-badge / needs-more-work / label
  article / body / timeline / desktop / node--confirmed
  article / body / timeline / desktop / node--current
  article / body / timeline / desktop / tooltip--open
  article / body / source-table / row--high-signal
  article / sidebar / disclaimer / condensed
  article / sidebar / checklist / item--checked
  article / sidebar / checklist / item--unchecked
```

---

## 14. Final Report

### Changed Files

```
docs/public-site/ONE_PERFECT_ARTICLE_SPEC.md    ← replaced earlier draft (this document)
```

No backend files modified. No frontend files modified. No deployment performed.

---

### Key Design Decisions

**1. Uncertainty leads visually.**
The confidence indicator and the "What Is Unknown" section carry nearly equal visual weight to the affirmative content. This is unconventional in investment content and is the primary brand differentiator.

**2. Status badge is the first element.**
Before reading the title, a visitor sees the research status. This forces immediate epistemic framing — the reader knows this is not a recommendation before the subject is named.

**3. Three typefaces, strict role separation.**
Serif (authority), sans (readability), mono (data). Mixing these roles is the single fastest path to destroying the visual system.

**4. One accent color, four rules for its use.**
Emerald appears on: active status, confirmed timeline events, focus rings, reading progress bar. Nowhere else. Amber appears on: "needs more work" status, disclaimer. Nowhere else.

**5. "What Would Change the View" is mandatory and bidirectional.**
A view that only goes in one direction is not research — it is advocacy. Both increase and decrease conditions must be present, in every published note.

**6. Disclaimer appears twice: in sticky sidebar and at article bottom.**
On desktop, the disclaimer is always in view. A reader cannot scroll past a state where "this is not financial advice" is invisible.

**7. Animation budget is exactly four interactions.**
Entry stagger, candidate glow, current-node pulse, reading progress bar. Everything else is static. Motion is earned.

---

### Open Questions

| # | Question | Recommendation |
|---|----------|---------------|
| Q1 | Print / PDF export required? | If yes: disclaimer must persist in print stylesheet; layout changes significantly at print width. |
| Q2 | Timeline: external links or internal anchor links to Key Documents? | Internal anchors first — keeps reader on the page and links to the document card row. |
| Q3 | Expected maximum number of timeline nodes? | If consistently over 10: desktop horizontal needs a designated "expand" mode or vertical alternative. |
| Q4 | Who sets the confidence indicator level? | Must be the human reviewer at approval time. Needs an explicit step in the Phase 5 editorial workflow. Currently not defined in the approval pipeline. |
| Q5 | Typeface licensing: paid font or system fallback for prototype? | Use Inter (free) for body and JetBrains Mono (free) for mono in initial Figma frames. Acquire GT Alpina or Canela trial for headline evaluation only. |
| Q6 | Should the public article page include JSON-LD structured data? | Yes — `Article` schema with `datePublished`, `dateModified`, `keywords` (situation type, status). Required if search indexing is ever enabled. |
| Q7 | Is `published_at` distinct from `approved_at` in the content model? | Currently `published_at` is stored but never written. If the public site serves on approval, `approved_at` is the correct field. Clarify before building the content pipeline. |

---

### Recommended Next Design Sprint

**Sprint: "Validate the Frame"**

Produce Frames 1–4 from Section 13 in Figma at high fidelity, using the example copy from Section 12.

Deliverables:
- 4 Figma frames at exact pixel dimensions specified
- 1 exported PDF for printed review at A4
- 1 annotation layer on Frame 1 keyed to decision numbers in this spec

Scope:
- Article page only
- Use the Meridian Group example copy
- Use Inter and JetBrains Mono as temporary type substitutes
- Evaluate GT Alpina or Canela for headline in a separate type exploration frame

Not in scope:
- Homepage, navigation animations, case study page, source intelligence page

Estimated time: 3–4 design sessions.

---

> *Este análisis es educativo. No es asesoramiento financiero.*
> *This document is a design specification only. It contains no financial advice,
> no investment recommendations, and no private or internal operational information.*
