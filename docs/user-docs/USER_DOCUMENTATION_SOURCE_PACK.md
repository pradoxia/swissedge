# SwissEdge Investment Research Platform — User Documentation Source Pack

> **Purpose:** Source material for a future user manual. Not a finished user-facing document.
> Written for the documentation author, not for direct publication.
> Based on: `docs/technical/INVESTMENT_RESEARCH_TECHNICAL_OVERVIEW.md` and `docs/PROJECT_STATE_LIGHT.md`.
> Last updated: 2026-05-02. Covers platform state through Phase 4C (all deployed and validated).

---

## 1. What the Platform Is

SwissEdge Investment Research Platform is a **private analyst workspace** for researching special situation investments — corporate events like spinoffs, mergers, tender offers, and similar transactions.

The platform helps an analyst:
- Keep track of situations detected from public financial filings (SEC EDGAR).
- Build and maintain a structured research brief for each case.
- Organize supporting documents and information sources.
- Use AI assistance to draft, review, and improve that research — while keeping the analyst in control of every decision.
- Study past cases through a separate historical case workspace.
- Manage a queue of suggested new information sources that the AI proposes.

**What it is not:**
- It is not a trading platform.
- It is not a financial advice tool.
- It does not make buy or sell recommendations.
- It does not publish research automatically.

Every page in the platform carries this notice: *"Este análisis es educativo. No es asesoramiento financiero."* ("This analysis is educational. It is not financial advice.")

---

## 2. Who It Is For

The platform is designed for a single analyst (or a small analyst team) who:
- Reviews corporate event filings and wants a structured place to build investment research notes.
- Wants AI assistance to speed up drafting without delegating decisions to the AI.
- Manages a set of information sources and wants help evaluating and improving them over time.
- Studies past special situations as a learning and pattern-recognition exercise.

**No prior technical knowledge is required** to use the core features — adding documents, editing a brief, reviewing AI suggestions. The AI panels explain what they are doing and always require a manual confirm before anything is saved.

---

## 3. What the User Can Do

### Active today (Phases 1A–4C, all deployed)

- **Browse evaluations** — see automatically detected corporate events.
- **Create a research case** from a detected event, or from scratch.
- **Work in a research workspace** — write notes, fill a structured 14-section brief, add tasks, add documents, add sources.
- **Get AI suggestions for the brief** — review them section by section, choose which to accept.
- **Run a quality check** — get an AI assessment of how complete and consistent the research is; apply status suggestions manually.
- **Analyze a document snippet** — paste text from a filing or article; get an AI breakdown of key points, risks, and timeline items.
- **Generate source intelligence** — ask the AI to evaluate existing sources and suggest new ones; save proposals to a review queue.
- **Review the source intelligence queue** — approve or reject each AI-suggested source, individually, from a central queue.
- **Create and maintain historical cases** — manually reconstruct past special situations; run source intelligence on them too.
- **Browse the watchlist, radar status, and source registry** (read-oriented).

### Not yet available

- Applying an approved source proposal directly to the case sources list (coming in Phase 4D).
- Exporting or publishing a brief in any format.
- Bulk operations on the source intelligence queue.

---

## 4. Main Navigation Structure

The platform uses a left-side or top navigation. The investment research section contains these pages:

| Page | What it shows |
|---|---|
| **Evaluations** | Queue of automatically detected corporate events. Entry point to create a new research case. |
| **Research Cases** | List of all ongoing research cases. Filter by status or readiness. Create a case directly here too. |
| **Research Case (detail)** | The full research workspace for one case. Brief, tasks, documents, sources, all AI tools. |
| **Source Intelligence Queue** | Central approval queue for all AI-proposed sources, across all cases. |
| **Historical Cases** | List of manually created past case studies. Create new historical cases here. |
| **Historical Case (detail)** | Notes, status, and source intelligence tools for one historical case. |
| **Watchlist** | Cases filtered by status, for monitoring. |
| **Radar Status** | Scanner observability — read-only view of the detection system. |
| **Sources** | Global source registry with toggles. |

### Inside a Research Case (the workspace)

A research case detail page is organized into panels. The user scrolls through them in sequence:

1. **Header** — company name, situation type, status badge, readiness badge, edit controls.
2. **Workflow strip** — quick status and readiness indicators.
3. **Notes** — free-form analyst notes field.
4. **Brief** — 14-section structured brief editor (collapsible).
5. **AI Brief Preview** — trigger AI draft suggestions; compare and apply.
6. **Quality Assist** — trigger AI quality check; apply status/readiness suggestions.
7. **Tasks** — add and manage research tasks.
8. **Documents** — add documents, paste snippets, run AI document analysis.
9. **Sources** — add sources, set signal quality, add notes.
10. **Source Intelligence** — generate AI source proposals; save to queue; inline approve/reject.

---

## 5. Key Workflows in Plain Language

---

### 5.1 Find an Evaluation

An evaluation is a corporate event that the scanner has automatically detected from a public filing.

1. Go to **Evaluations** in the navigation.
2. Browse the list. Each evaluation shows the company name, event type, and a preliminary AI-generated assessment.
3. Click an evaluation to open the detail view.
4. Review the assessment. If the situation looks worth investigating, proceed to create a research case.

> **Note for documentation author:** The evaluations page and evaluator v2 preview are separate from the research platform. The research platform starts at the "Create Research Case" step below.

---

### 5.2 Create a Research Case

**From an evaluation:**
1. Open an evaluation detail page.
2. In the panel at the bottom of that page, click **"Create Research Case"**.
3. The platform creates a new case pre-filled with the company name and situation type from the evaluation.
4. You are taken directly to the research workspace for the new case.

**From scratch (no linked evaluation):**
1. Go to **Research Cases**.
2. Click **"+ NEW RESEARCH CASE"** or use the create panel.
3. Enter the company name and situation type.
4. Click **Create**.

In both cases, the new case starts with status **under_investigation**.

---

### 5.3 Open the Research Workspace

1. Go to **Research Cases**.
2. Click any case in the list.
3. The workspace opens, showing all panels: brief, tasks, documents, sources, and AI tools.

The workspace is a single scrollable page. All editing happens inline — there are no separate edit screens.

---

### 5.4 Edit the Research Brief

The research brief has **14 sections**. A counter at the top shows how many are filled (e.g. "3/14 SECTIONS FILLED").

The 14 sections are:
1. Situation Summary
2. Key Actors
3. Timeline
4. Financial Overview
5. Legal / Regulatory
6. Risks
7. Catalysts
8. Comparable Situations
9. Source Analysis
10. Information Gaps
11. Preliminary Thesis
12. Monitoring Plan
13. Open Questions
14. Research Status Note

**To edit a section:**
1. Scroll to the **Brief** panel and expand it.
2. Click into any section's text area.
3. Type or edit the content.
4. Click **Save Brief** (or the section-level save button) to persist the change.

Each section is independent. Editing one section does not affect others.

> **Screenshot needed:** Brief panel with several sections filled, showing the "3/14 SECTIONS FILLED" counter.

---

### 5.5 Add Tasks

Tasks are used to track research to-dos for a case (e.g. "Read the 10-K filing", "Verify the timeline with a second source").

1. Scroll to the **Tasks** panel in the research workspace.
2. Type a task title in the input field.
3. Click **Add** or press Enter.
4. The task appears in the list with status **pending**.

**To update a task's status:**
1. Click the status badge next to the task title.
2. Select a new status from the dropdown: `pending`, `in_progress`, `done`, `blocked`.
3. The change saves immediately.

You can also add notes to a task using the notes field that appears when you expand a task row.

---

### 5.6 Add Documents

Documents are references to filings, articles, reports, or other materials relevant to the case. The platform stores the title and optionally the URL — it does **not** fetch or read the URL content automatically.

1. Scroll to the **Documents** panel.
2. Enter the document title.
3. Optionally paste the URL (stored for reference only — not visited by the platform).
4. Click **Add Document**.

**To edit a document after adding it:**
- Select the **document type** from the dropdown (e.g. SEC filing, press release, news article, analyst report).
- Set the **signal quality** (high / medium / low / noise) to indicate how useful this document is.
- Add **analyst notes** in the notes field.
- To enable AI analysis, paste relevant text into the **snippet / summary** field (see §5.11 below).

All edits have an explicit **Save** button. Nothing saves on blur or automatically.

> **Screenshot needed:** A document card in editing state, showing the doc_type selector, signal quality dropdown, and snippet field.

---

### 5.7 Add Sources

Sources are information sources relevant to the case — e.g. a specific regulatory database, a news outlet, a government agency website. Like documents, the URL is stored as metadata only.

1. Scroll to the **Sources** panel.
2. Enter the source name.
3. Optionally enter the URL and source type.
4. Click **Add Source**.

**To edit a source after adding it:**
- Set the **signal quality** (high / medium / low / noise).
- Add **analyst notes**.
- Click **Save**.

---

### 5.8 Run the AI Brief Preview

The AI Brief Preview generates suggested text for each of the 14 brief sections, based on the case's notes, documents, sources, and tasks. The analyst selects which suggestions to accept — nothing is applied automatically.

**How to run it:**
1. Scroll to the **AI Brief Preview** panel in the workspace.
2. Click **"GENERATE AI BRIEF PREVIEW"**.
3. Wait 15–30 seconds. A side-by-side comparison appears: the current saved text on the left, the AI suggestion on the right.
4. For each section, review the suggestion.
5. Check the checkbox next to each section you want to accept.
6. Click **"APPLY SELECTED SECTIONS"** — those sections are merged into the brief.
7. Click **Save Brief** to persist.

**What the panel shows at the bottom:**
- Which sources and documents were used as context.
- The AI model name and token count used.
- A notice if any document URLs were present but not fetched: *"URL METADATA ONLY — document/source URLs were not fetched."*

> **Important:** The banner at the top of the panel reads **"PREVIEW ONLY — NOT SAVED"**. Nothing is written to the database until you click Apply and then Save.

> **Screenshot needed:** AI Brief Preview panel showing a side-by-side comparison with checkboxes, before clicking Apply.

---

### 5.9 Apply Selected Preview Sections

This is step 6 of the AI Brief Preview workflow (§5.8), described separately here because it is the key decision point.

1. After generating the preview, review each section side by side.
2. Tick the checkbox for each section whose AI suggestion you want to use.
3. Leave the checkbox empty for sections you want to keep as they are.
4. Click **"APPLY SELECTED SECTIONS"**.
5. The checked sections are merged into the brief. Unchecked sections are not changed.
6. The preview panel closes (or can be dismissed).
7. Click **Save Brief** to write the changes to the database.

If you want to discard the entire preview without applying anything, click **Discard** or close the panel.

---

### 5.10 Run the Quality Check

The Quality Assist panel runs an AI review of how complete and internally consistent the research case is. It returns a checklist of 9 quality criteria and suggests a status and readiness level. The analyst decides whether to apply those suggestions.

**The 9 checklist items assess:**
1. Whether a situation summary exists.
2. Whether key actors are identified.
3. Whether a timeline is present.
4. Whether financial data is documented.
5. Whether legal/regulatory context is noted.
6. Whether risks are identified.
7. Whether catalysts are identified.
8. Whether sources are added.
9. Whether an initial thesis exists.

**How to run it:**
1. Scroll to the **Quality Assist** panel.
2. Click **"RUN QUALITY ANALYSIS"**.
3. The panel displays the 9-item checklist (each marked true or false) and a suggested status + readiness.
4. Review the checklist. If you agree with the suggested status or readiness, click:
   - **"APPLY SUGGESTED STATUS"** — updates the case status field.
   - **"APPLY SUGGESTED READINESS"** — updates the investment readiness field.
   - **"APPLY BOTH"** — applies both at once.
5. Each apply action saves immediately.

> **Important:** The banner reads **"ASSISTIVE PREVIEW — NOT SAVED"**. The AI never changes the status or readiness automatically.
> **Hard rule:** The AI cannot suggest or set the status to **published**. That status requires manual editorial approval only.

> **Screenshot needed:** Quality Assist panel showing the 9-item checklist with suggested status/readiness and the three Apply buttons.

---

### 5.11 Analyze a Pasted Document Snippet

The Document Analysis tool reads a text snippet you paste into a document and returns a structured breakdown: summary, key points, risks, timeline items, and suggested follow-up tasks. It does not fetch the document URL.

**Requirements:**
- The document must already exist in the workspace (added via §5.6).
- The snippet must be at least **50 characters** long.

**How to use it:**
1. Open the document card.
2. Paste relevant text into the **Snippet / Summary** field. This might be a key paragraph from an SEC filing, a press release quote, or any relevant text you have copied manually.
3. Click **Save** on the document card to persist the snippet.
4. Click **"ANALYSE DOCUMENT"**.
5. Wait a few seconds. The analysis panel appears below the document card and shows:
   - **Summary** — one-paragraph overview of the snippet.
   - **Key Points** — bullet list of the most significant facts.
   - **Risks** — risks identified in the text.
   - **Timeline Items** — dates and events mentioned.
   - **Suggested Research Tasks** — follow-up actions the AI recommends based on the content.
   - **Source Usefulness** — assessment of how useful this document is to the case.
6. Use the output to manually update the brief, add tasks, or flag gaps.

> **Important:** The footer reads **"NOT SAVED — apply changes manually"**. Nothing in the analysis is auto-applied to the brief or task list.

> **Screenshot needed:** A document card with the analysis panel expanded, showing Key Points and Suggested Research Tasks.

---

### 5.12 Generate the Source Intelligence Preview

Source Intelligence reviews the sources already attached to a case, scores their usefulness, and suggests new sources the analyst might want to add, update, or deactivate. Suggestions are proposals only — they go into a review queue before any action is taken.

**How to run it:**
1. Scroll to the **Source Intelligence** panel in the research workspace.
2. Click **"GENERATE SOURCE INTELLIGENCE PREVIEW"**.
3. Wait 15–30 seconds. The panel shows two sections:
   - **Source Scores** — for each existing source: a usefulness assessment, signal quality note, and suggested follow-up action.
   - **Suggested Sources** — a list of proposed actions (Add a new source / Update priority / Deactivate) with confidence level (high / medium / low) and reasoning.
4. The banner reads **"PROPOSALS ONLY — NOT APPLIED"**.
5. To save the suggestions to the review queue, click **"SAVE X PROPOSAL(S)"**.
6. Saved proposals appear below in the **Saved Proposals** list with Approve and Reject buttons.

> **Important:** Saving proposals does not apply them to anything. Approving a proposal in the queue does not add a source automatically either. Application to the source list is a separate action coming in a future release (Phase 4D).

---

### 5.13 Review Source Intelligence Suggestions

Suggestions from both research cases and historical cases collect in a central queue at **Source Intelligence Queue** in the navigation.

**From the queue page:**
1. Go to **Source Intelligence Queue**.
2. Use the filters at the top to narrow by status (proposed / approved / rejected) or action type (add / update priority / deactivate).
3. The **Pending Review** section shows proposals awaiting a decision.
4. For each proposal, read the suggested source name, type, and reasoning.
5. Click **APPROVE** to mark it approved, or **REJECT** to dismiss it.
6. The **Reviewed** section below shows all decided proposals (read-only).
7. Each proposal links back to the case it came from.

**From within a research case or historical case:**
The Saved Proposals list at the bottom of the Source Intelligence panel also shows inline Approve/Reject buttons for proposals in `proposed` status.

> **Important:** Approving a proposal is a **decision record only**. It does not create a source in the case or in the global source registry. That apply step does not yet exist (Phase 4D).

> **Screenshot needed:** Source Intelligence Queue page showing the Pending Review section with Approve and Reject buttons visible.

---

### 5.14 Create a Historical Case

Historical cases are manually entered records of past special situations — used for learning, pattern recognition, and testing source intelligence against known events.

1. Go to **Historical Cases** in the navigation.
2. Click **"+ NEW HISTORICAL CASE"**.
3. Fill in:
   - **Company Name** (required) — e.g. "Dell Technologies"
   - **Situation Type** (required) — e.g. "spinoff", "merger", "tender_offer"
   - **Event Date (approx)** (optional) — free-form, e.g. "2016-Q4"
   - **Seed Notes** (optional) — initial notes about the case
4. Click **CREATE**.

The case is created with status **seed** and opens in the list.

**Inside a historical case:**
- Edit **Seed Notes** at any time using the inline editor and explicit Save button.
- Advance the **Status** through its lifecycle:
  - `seed` → `reconstructed` → `lessons_extracted` → `source_intel_applied`
  - Each step requires a manual save via the status dropdown and Save button.
- Run **Source Intelligence Preview** using the same flow as on a research case (§5.12).
- Review saved proposals inline (§5.13).

> **Note:** The historical case status lifecycle is intentionally manual. The analyst decides when reconstruction is complete, when lessons have been extracted, and when source intelligence has been applied.

---

## 6. Warnings and Safety

---

### 6.1 AI Previews Are Not Saved Automatically

Every AI feature in the platform — Brief Preview, Quality Assist, Document Analysis, Source Intelligence Preview — returns a result that is **not written to the database**. The result exists only in the browser until the analyst takes an explicit action.

Each AI panel clearly shows one of these banners:
- **"PREVIEW ONLY — NOT SAVED"** — for the Brief Preview.
- **"ASSISTIVE PREVIEW — NOT SAVED"** — for Quality Assist.
- **"NOT SAVED — apply changes manually"** — for Document Analysis.
- **"PROPOSALS ONLY — NOT APPLIED"** — for Source Intelligence.

If you close the panel, navigate away, or refresh the page before applying, the preview result is lost. This is intentional — the analyst is always in control.

---

### 6.2 URLs Are Metadata Only — Paste Text Manually

When you add a document or source with a URL, **the platform does not visit or read that URL**. The URL is stored as a reference label only.

If you want the AI to analyse the content of a document, you must:
1. Open the original document in your browser or another tool.
2. Select and copy the relevant text.
3. Paste it into the **Snippet / Summary** field of the document card.
4. Save the snippet.
5. Then click Analyse Document.

This is a deliberate design decision. The platform does not crawl, scrape, or fetch any URLs at any point.

When a case has documents or sources with URLs, the AI Brief Preview panel will display this notice: *"URL METADATA ONLY — document/source URLs were not fetched."*

---

### 6.3 No Financial Advice

All output from the platform — including AI-generated brief suggestions, quality assessments, document analysis, and source intelligence — is **educational research material only**.

The platform does not provide financial advice. It does not recommend buying or selling any security. This notice appears at the bottom of every page:

> *Este análisis es educativo. No es asesoramiento financiero.*
> *(This analysis is educational. It is not financial advice.)*

The AI output layer has a built-in filter that detects and removes buy/sell recommendation language before any result is returned to the user. If the AI generates such language internally, it is stripped from the output automatically.

---

### 6.4 No Buy/Sell Recommendations

Distinct from the financial advice notice above: the platform applies an automated filter to every AI-generated field. Any text matching buy/sell recommendation patterns is detected, and the affected output is sanitized or flagged with a warning before it reaches the analyst.

This filter applies to:
- Brief section suggestions
- Quality Assist output
- Document analysis output
- Source intelligence proposals (name and rationale)

The analyst cannot disable this filter.

---

### 6.5 Publishing Is Not Active

The research brief has a concept of a `published` status, but **the publishing pipeline does not exist yet**.

- The AI Quality Assist cannot suggest `published` status. If it ever generates this value internally, the system automatically downgrades it to `documented` (if the brief is substantially complete) or `under_investigation` (otherwise).
- The analyst can technically set a case to status `documented`, which is as far as the current workflow goes.
- There is no export (PDF, email, web page) and no publish button anywhere in the current platform.
- Publishing requires separate editorial approval and is planned as a future feature.

---

## 7. Glossary

---

### Research Case

A Research Case is the main object in the platform. It represents one active investigation into a special situation. It contains:
- A structured 14-section brief.
- A list of tasks (things to do or verify).
- A list of documents (filings, articles, reports referenced).
- A list of sources (information sources tracked for this case).
- Status and investment readiness labels.
- Notes.

A Research Case can be linked to an upstream detected situation (from the scanner), or created manually from scratch.

---

### Source

A Source is an information outlet tracked as part of a case — for example, a company's investor relations page, a regulatory database, a financial news outlet, or a court filing service.

Sources have:
- A name and optional URL (URL is metadata only — never fetched).
- A **signal quality** rating (high / medium / low / noise) — the analyst's assessment of how useful and reliable this source is.
- Analyst notes.

Sources are distinct from Documents. A source is an ongoing information channel; a document is a specific artifact from that channel.

---

### Document

A Document is a specific artifact added to a case — a 10-K filing, a press release, a news article, an analyst report. Documents have:
- A title and optional URL (metadata only).
- A **document type** (SEC filing, press release, news article, analyst report, court filing, regulatory filing, other).
- A **signal quality** rating.
- A **snippet / summary** field — this is where the analyst pastes text for AI analysis.
- Analyst notes.

The snippet field is the only way to feed document content to the AI. Minimum length: 50 characters.

---

### Brief

The Brief is a 14-section structured research document attached to a Research Case. It is the primary output of the research process. Each section is a free-text field, edited independently.

The 14 sections cover: situation summary, key actors, timeline, financial overview, legal/regulatory, risks, catalysts, comparable situations, source analysis, information gaps, preliminary thesis, monitoring plan, open questions, and research status note.

The Brief is written by the analyst. The AI Brief Preview tool can suggest text for each section, but the analyst decides what to accept.

---

### Quality Assist

Quality Assist is the AI tool that reviews a Research Case and returns a quality assessment. It checks 9 criteria (is there a summary? Are risks documented? Are sources added? etc.) and suggests a status and readiness level.

Quality Assist is **assistive only**. It never changes anything automatically. The analyst clicks explicit apply buttons to use any suggestion.

The AI cannot suggest the status `published`. That is hard-blocked at the system level.

---

### Source Intelligence

Source Intelligence is the AI tool that reviews the sources attached to a case (or historical case) and suggests improvements:
- Scoring each existing source for usefulness.
- Proposing new sources to add.
- Flagging sources to update or deactivate.

Source Intelligence generates **proposals only**. Proposals go into a review queue. The analyst approves or rejects each one individually. Approval is a decision record — it does not yet create or modify sources automatically (that is a planned future feature).

---

### Historical Case

A Historical Case is a manually entered record of a past special situation — used for learning and pattern recognition. Unlike a Research Case, it is not connected to the live scanner or current filings.

Historical Cases have:
- A company name, situation type, and approximate event date.
- Seed notes — free-form text about the case.
- A status that advances manually: `seed` → `reconstructed` → `lessons_extracted` → `source_intel_applied`.
- Access to the Source Intelligence tool (same as research cases).

Historical Cases are a research and training tool, not a live investigation workspace.

---

## 8. Suggested Screenshots Needed

The following screenshots should be captured from the live platform before writing the final user manual. Each entry includes what must be visible in the shot.

| # | Page / Panel | What Must Be Visible | Purpose |
|---|---|---|---|
| 1 | `/investment/evaluations` | List with at least one evaluation row; status badge visible | Illustrate the entry point for creating a research case |
| 2 | `/investment/evaluations/[id]` | Evaluation detail with "Create Research Case" button visible | Show the create-from-evaluation action |
| 3 | `/investment/research` | Research Cases list with status and readiness filters, at least two cases | Illustrate the main list page |
| 4 | `/investment/research/[id]` — top | Case header with company name, status badge, readiness badge, workflow strip | Show the workspace header |
| 5 | `/investment/research/[id]` — Brief panel | Brief expanded showing "X/14 SECTIONS FILLED" counter, at least 2 sections with text | Illustrate the brief editor |
| 6 | `/investment/research/[id]` — AI Brief Preview (pre-apply) | Side-by-side compare visible, at least one checkbox ticked, "APPLY SELECTED SECTIONS" button visible | The key decision moment for brief preview |
| 7 | `/investment/research/[id]` — AI Brief Preview (URL notice) | The "URL METADATA ONLY" notice visible in panel footer | Needed for the URL metadata warning section |
| 8 | `/investment/research/[id]` — Quality Assist | 9-item checklist shown, suggested status/readiness visible, three Apply buttons visible | Quality Assist workflow |
| 9 | `/investment/research/[id]` — Document card | Document card in edit state: doc_type selector, signal quality, snippet field, Analyse button | Document analysis prerequisite |
| 10 | `/investment/research/[id]` — Document analysis result | Analysis panel open showing Key Points, Risks, Suggested Research Tasks sections | Illustrate document analysis output |
| 11 | `/investment/research/[id]` — Source Intelligence panel (preview) | Suggestions list visible with confidence labels; "PROPOSALS ONLY — NOT APPLIED" banner; "SAVE X PROPOSAL(S)" button | Source intelligence preview workflow |
| 12 | `/investment/research/[id]` — Source Intelligence panel (saved proposals) | Saved proposals list with at least one APPROVE and one REJECT button | Inline approval flow |
| 13 | `/investment/source-intelligence` | Pending Review section with at least one proposal; Approve/Reject buttons visible; filter dropdowns | Global queue page |
| 14 | `/investment/historical-cases` | List with at least one case; status color coding visible; "+ NEW HISTORICAL CASE" button | Historical cases entry point |
| 15 | `/investment/historical-cases/[id]` | Case detail with notes editor open; status dropdown visible | Historical case workspace |
| 16 | Any page footer | Disclaimer text visible: "Este análisis es educativo. No es asesoramiento financiero." | To illustrate the disclaimer section in the manual |

---

## 9. Open Questions for Dani

The following questions arose during documentation and need Dani's input before the final user manual can be written.

1. **Audience language** — Should the final user manual be in English, Spanish, or both? The platform UI is in English but the disclaimer is in Spanish. What is the intended primary audience language?

2. **"Readiness" label wording** — The field is technically `investment_readiness` with values `monitor`, `not_actionable`, `needs_more_work`, `candidate`. How should these be described in plain language in the manual? Are there preferred synonyms or descriptions for each value?

3. **"Status" label wording for ResearchCase** — `under_investigation`, `documented`, `watching`, `archived`. Same question — are there plain-language descriptions or user-facing names for each?

4. **Phase 4D timing** — The Source Intelligence Approval Queue currently shows that approving a proposal does not apply it anywhere. When Phase 4D (apply-to-case-sources) ships, the manual will need an update. Should a placeholder section be written now, or should that section wait until 4D is live?

5. **Historical Cases vs. Research Cases in the manual** — Should they appear as two separate chapters, or as one chapter with a section distinguishing them? Historical cases share many concepts (source intelligence, proposals, approval) but are fundamentally different in origin and purpose.

6. **"Signal quality" — user-facing definition** — The four values are `high`, `medium`, `low`, `noise`. Is there a defined meaning for each that should be documented (e.g. "noise = source consistently provides irrelevant data")? Or is this left to analyst judgment?

7. **Course chapter reference on Historical Cases** — `course_chapter_ref` is stored but has no editor in the UI. Should it be mentioned in the manual at all, or omitted since it cannot be edited?

8. **Watchlist page** — Is the watchlist page in scope for the user manual? It exists and is deployed, but was not included in the files read for this pack. If it is in scope, a separate read will be needed.

9. **Radar Status page** — Same question. Read-only scanner observability. Should it be documented for the analyst, or is it an internal-only / admin view?

10. **"Source Intelligence" naming** — Is "Source Intelligence" the intended user-facing name for this feature (the AI tool that scores and suggests sources)? Or is there a preferred plain-language name for the manual (e.g. "Source Review", "Source Suggestions")?

---

## Final Report

### Changed Files

| Action | File |
|---|---|
| Created | `docs/user-docs/USER_DOCUMENTATION_SOURCE_PACK.md` (this file) |
| Read (source, unchanged) | `docs/technical/INVESTMENT_RESEARCH_TECHNICAL_OVERVIEW.md` |
| Read (source, unchanged) | `docs/PROJECT_STATE_LIGHT.md` |

No code was changed. No deployment. No tests run. No repo scan.

---

### Suggested User Manual Structure

Based on this source pack, the final user manual should be organized as follows:

**Chapter 1 — Introduction**
- What SwissEdge Investment Research Platform is
- Who it is for
- Important notices (educational purpose, no financial advice)

**Chapter 2 — Getting Started**
- Navigating the platform
- Understanding the main screens
- Your first research case (quick start)

**Chapter 3 — Research Cases**
- Creating a research case (from evaluation / from scratch)
- Understanding the workspace layout
- Editing case status and readiness

**Chapter 4 — The Research Brief**
- What the 14 sections are and what goes in each
- Editing sections manually
- Using the AI Brief Preview
- Applying and saving preview sections

**Chapter 5 — Tasks**
- Adding tasks
- Managing task status
- Using task notes

**Chapter 6 — Documents**
- Adding documents
- Setting document type and signal quality
- Pasting snippets for analysis
- Running the AI Document Analysis
- Reading the analysis output

**Chapter 7 — Sources**
- Adding sources
- Setting signal quality and notes
- Understanding the difference between sources and documents

**Chapter 8 — Quality Assist**
- What Quality Assist checks
- Running the quality check
- Applying suggested status and readiness
- Understanding the published status restriction

**Chapter 9 — Source Intelligence**
- What Source Intelligence does
- Running the preview (research case)
- Understanding source scores and suggestions
- Saving proposals to the queue
- Reviewing proposals inline

**Chapter 10 — Source Intelligence Queue**
- Navigating the approval queue
- Filtering by status and action type
- Approving and rejecting proposals
- Understanding what approval means (and does not mean)

**Chapter 11 — Historical Cases**
- What historical cases are and why they exist
- Creating a historical case
- Editing notes and advancing status
- Running source intelligence on a historical case

**Chapter 12 — Warnings and Limits**
- AI preview is not automatic saving
- URLs are metadata only
- No financial advice
- No buy/sell recommendations
- Publishing is not active
- What is not yet available (Phase 4D and later)

**Appendix A — Glossary**
**Appendix B — Status and Readiness Reference** (pending answer to open question #2 and #3)
**Appendix C — Brief Section Reference** (one paragraph per section describing what goes in it)

---

### Missing Screenshots

All 16 screenshots listed in Section 8 are required before the manual can be finalized. The highest priority ones for initial drafting are:

| Priority | Screenshot # | Reason |
|---|---|---|
| High | 6 | AI Brief Preview apply moment — most complex and important workflow step |
| High | 8 | Quality Assist checklist — needed for Chapter 8 |
| High | 11 | Source Intelligence preview — proposals banner critical for warnings section |
| High | 13 | Source Intelligence Queue page — needed for Chapter 10 |
| Medium | 1, 2 | Evaluations entry point — Chapter 2 quick start |
| Medium | 9, 10 | Document analysis — Chapter 6 |
| Medium | 14, 15 | Historical cases — Chapter 11 |
| Low | 3, 4, 5 | Research cases list and workspace header — useful but less complex to describe without |
| Low | 7 | URL metadata notice — needed but can be described textually |
| Low | 12 | Inline approval — duplicates concept from screenshot 13 |
| Low | 16 | Disclaimer footer — needed but easily captured at any time |
