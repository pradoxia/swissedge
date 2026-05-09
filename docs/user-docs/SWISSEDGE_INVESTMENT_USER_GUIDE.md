# SwissEdge Investment Research Platform
## User Guide

*Private use only. For internal research purposes.*

---

## Table of Contents

1. [Introduction](#1-introduction)
2. [What SwissEdge Investment Research Platform Does](#2-what-swissedge-investment-research-platform-does)
3. [Important Safety Rules](#3-important-safety-rules)
4. [Quick Start](#4-quick-start)
5. [Navigation Overview](#5-navigation-overview)
6. [Evaluations and Research Cases](#6-evaluations-and-research-cases)
7. [Research Workspace](#7-research-workspace)
8. [Research Brief](#8-research-brief)
9. [Tasks and Missing Information](#9-tasks-and-missing-information)
10. [Documents](#10-documents)
11. [Sources](#11-sources)
12. [AI Brief Preview](#12-ai-brief-preview)
13. [Quality Assist](#13-quality-assist)
14. [Document Analysis Preview](#14-document-analysis-preview)
15. [Source Intelligence Preview](#15-source-intelligence-preview)
16. [Source Intelligence Queue](#16-source-intelligence-queue)
17. [Historical Cases](#17-historical-cases)
18. [What SwissEdge Does Not Do Automatically](#18-what-swissedge-does-not-do-automatically)
19. [Glossary](#19-glossary)
20. [FAQ](#20-faq)
21. [Screenshot Checklist](#21-screenshot-checklist)

---

## 1. Introduction

SwissEdge is a private research workspace for investigating corporate special situations — events such as spinoffs, mergers, tender offers, and similar transactions that appear in public regulatory filings.

This guide covers the Investment Research Platform. It is written for a single analyst who uses SwissEdge day-to-day to detect, investigate, and document research cases.

**Who this guide is for:** You, the private user of this platform.

**What this guide covers:** Every page and action available in the Investment Research section of SwissEdge.

**What this guide does not cover:** The Marketplace Assistant (a separate domain, currently paused) and any internal technical or deployment details.

---

## 2. What SwissEdge Investment Research Platform Does

SwissEdge monitors SEC EDGAR for regulatory filings related to special situations. When a filing matches the detection criteria, the platform creates an **Evaluation** — a structured snapshot of the event for your review.

From an Evaluation, you can open a **Research Case** — a full investigation workspace where you build a structured research brief, track tasks, attach documents, and register sources.

The platform also lets you create **Historical Cases** — manually reconstructed past situations you want to study for patterns and reference.

**AI assistance is available throughout, but always under your explicit control.** No AI result is applied without you choosing to apply it. Nothing is published automatically. All research output is educational — it is never financial advice.

---

## 3. Important Safety Rules

Read these before using the platform. They are not warnings to ignore — they describe how the system is designed to work.

**AI previews are never saved automatically.**
Every AI result (brief suggestions, quality checks, document analysis, source intelligence) is returned as a preview only. Nothing persists until you click the explicit save or apply button.

**URLs are stored as labels, not as live links.**
When you add a document or source URL, SwissEdge stores it as a reference label. The platform does not fetch, load, or read the content at that URL. You are responsible for reading documents yourself and pasting relevant text into the snippet field if you want AI analysis on them.

**No financial advice is generated.**
All AI output includes a fixed disclaimer: this analysis is educational and is not financial advice. This cannot be removed or overridden.

**Buy and sell language is blocked.**
The platform filters all AI output for buy/sell recommendation language. If such language appears in a response, it is automatically removed before the result reaches you.

**Publishing is not active.**
There is no publish button. Research Cases can be marked as *Documented* or *Archived* but there is no external publication feature in the current version.

**Status changes are always manual.**
The AI Quality Assist tool may suggest a status or readiness level. These are suggestions only — you apply them with an explicit button click, or ignore them.

---

## 4. Quick Start

If you are opening SwissEdge for the first time and want to reach the core workflow in five steps:

1. Open the platform and go to **Evaluations** in the left navigation.
2. Find an evaluation that looks interesting. Click it to open the Evaluation Detail.
3. At the bottom of the Evaluation Detail, click **Create Research Case** to open a live investigation workspace.
4. In the Research Workspace, read the pre-filled information and click **Edit Brief** to start building your research brief.
5. Add tasks, documents, and sources as you gather more information.

That is the core loop. Everything else in this guide describes how to go deeper from there.

---

## 5. Navigation Overview

The left sidebar contains all main sections. The Investment Research section has the following pages:

| Page | What it shows |
|---|---|
| **Evaluations** | The full list of detected special situations, newest first |
| **Research Cases** | All research cases you have created |
| **Watchlist** | Research cases filtered by watchlist status |
| **Radar Status** | The scanner's last-run status and detection log (read-only) |
| **Sources** | The registry of known information sources and their active/inactive toggle |
| **Historical Cases** | Manually created past case studies |
| **Source Intelligence Queue** | All source intelligence proposals waiting for your review |
| **Agents** | The agent registry showing active AI agents and their last activity |

---

## 6. Evaluations and Research Cases

### What is an Evaluation?

An Evaluation is a structured snapshot of a special situation detected from a regulatory filing. The scanner creates it automatically. You cannot create evaluations manually — they come from the detection process.

Each evaluation shows:
- The company name and ticker
- The type of event (spinoff, merger, tender offer, etc.)
- The filing date
- An AI-generated assessment of the situation's interest level
- Any prior evaluations of the same company

### Opening an Evaluation

Click any evaluation in the list to open its detail page. The detail page shows the full structured assessment, including confidence scores and flagged risk factors.

### Creating a Research Case from an Evaluation

If an evaluation looks worth investigating, scroll to the bottom of the Evaluation Detail page and click **Create Research Case**.

This opens a new Research Case pre-filled with:
- The company name and situation type from the evaluation
- The evaluation ID as a reference link
- An initial status of *Under Investigation*

You are taken directly to the Research Workspace.

### Research Case Statuses

A Research Case moves through four statuses over its life:

| Status | Meaning |
|---|---|
| **Under Investigation** | Active open investigation |
| **Documented** | Investigation complete; brief is written |
| **Watching** | Monitoring for developments; not actively investigating |
| **Archived** | Closed; no longer being tracked |

You change the status manually using the status selector in the Research Workspace header.

### Research Case Readiness Labels

Separately from status, each case carries a readiness label:

| Label | Meaning |
|---|---|
| **Monitor** | Worth keeping an eye on |
| **Not Actionable** | Reviewed; no action warranted |
| **Needs More Work** | Investigation incomplete |
| **Candidate** | Strong enough to prioritize |

These labels are editorial — you set them based on your judgment. The AI Quality Assist tool can suggest a readiness label, but applying it is always your choice.

---

## 7. Research Workspace

The Research Workspace is the main working environment for a Research Case. It is divided into several panels:

- **Header strip** — case name, status, readiness label, quick-edit controls
- **Workflow strip** — shows which phases of investigation are complete
- **Research Brief** — the 14-section structured document you build over time
- **Tasks** — a checklist of open research tasks and missing information
- **Documents** — attached documents with metadata and optional AI analysis
- **Sources** — registered information sources for this case
- **Source Intelligence Panel** — AI-generated source proposals and the approval queue for this case

You can work in any panel in any order. There is no required sequence.

### Opening a Research Case

Go to **Research Cases** in the navigation. Click any case to open its workspace.

---

## 8. Research Brief

The Research Brief is a 14-section structured document. Each section is a free-text field you fill in as you learn more about the situation.

### The 14 Sections

| # | Section | What to write |
|---|---|---|
| 1 | **Situation Summary** | What happened; the core event in plain terms |
| 2 | **Key Actors** | Companies, executives, and other parties involved |
| 3 | **Timeline** | Key dates and milestones |
| 4 | **Financial Overview** | Deal structure, valuations, financial terms |
| 5 | **Legal and Regulatory** | Filings, approvals, regulatory considerations |
| 6 | **Risks** | What could go wrong or complicate the situation |
| 7 | **Catalysts** | Events or conditions that could move the situation forward |
| 8 | **Comparable Situations** | Similar past cases for context |
| 9 | **Source Analysis** | Quality and coverage of your information sources |
| 10 | **Information Gaps** | What you still need to find out |
| 11 | **Preliminary Thesis** | Your working interpretation of the situation |
| 12 | **Monitoring Plan** | What to watch and how often |
| 13 | **Open Questions** | Unresolved questions you want to revisit |
| 14 | **Research Status Note** | Internal note on the current state of the investigation |

The header shows a counter — for example, **7/14 SECTIONS FILLED** — so you can track completeness at a glance.

### Editing the Brief

Click the **Edit Brief** button to open any section for editing. Type your text and click **Save** to persist the change. The save is immediate and explicit — there is no auto-save.

You can also use the AI Brief Preview (Chapter 12) to generate draft text for any section and then apply selected sections to the brief.

---

## 9. Tasks and Missing Information

The Tasks panel is a simple checklist for tracking open research tasks — things you need to do, find, or verify before the case is complete.

### Adding a Task

Click **Add Task** in the Tasks panel. Fill in:
- **Title** — a short description of what needs doing
- **Notes** — optional detail
- **Status** — Open, In Progress, or Done

Click **Save** to add it to the list.

### Editing a Task

Click any task to expand it. Edit the title, notes, or status inline. Click **Save** to update.

### Closing a Task

Change the task status to **Done**. It moves to the completed section of the list.

**Tip:** Use tasks to track information gaps identified in the brief. The AI Quality Assist tool and Document Analysis Preview may suggest new tasks — you add them manually if you decide they are worth tracking.

---

## 10. Documents

The Documents panel holds documents you have attached to this case. Each document is a metadata record — a reference to a filing, article, or other source material that you have reviewed.

### What a Document Record Contains

| Field | Description |
|---|---|
| **Title** | The document's name or headline |
| **URL** | The document's web address (stored as a label — not fetched) |
| **Document Type** | The type of document (e.g., 8-K, 10-K, proxy filing, press release) |
| **Signal Quality** | Your assessment of how reliable and useful this document is |
| **Metadata-only flag** | Indicates the URL has not been read by the platform |
| **Snippet** | A passage of text from the document, pasted manually by you |
| **Notes** | Your own annotations or tags |

### Adding a Document

Click **Add Document**. Fill in the title and URL at minimum. Set the document type and signal quality if known. Click **Save**.

### Adding a Snippet

A snippet is a passage of text you paste from a document you have read. Snippets enable AI document analysis.

To add a snippet:
1. Read the document yourself (SwissEdge does not fetch it for you).
2. Copy a relevant passage.
3. Open the document record in the workspace.
4. Paste the text into the **Snippet** field.
5. Click **Save Snippet**.

**Copyright notice:** Only paste short, clearly relevant excerpts. Do not paste entire documents.

A snippet must be at least 50 characters long to be eligible for AI Document Analysis Preview.

### Editing a Document

Click any document record to expand it. All fields are editable. Click **Save** to update.

---

## 11. Sources

The Sources panel holds the information sources you are using for this case — the feeds, databases, publications, or contact points that are providing information.

### What a Source Record Contains

| Field | Description |
|---|---|
| **Name** | The source's name |
| **URL** | The source's address (stored as a label — not fetched) |
| **Source Type** | Category of source (e.g., regulatory filing feed, news outlet) |
| **Signal Quality** | Your assessment of this source's reliability for this case |
| **Notes** | Your annotations |

### Adding a Source

Click **Add Source**. Fill in the name and any relevant fields. Click **Save**.

### Editing a Source

Click any source record to expand it. All fields are editable. Click **Save**.

**Note:** The Source Intelligence Preview (Chapter 15) can suggest new sources based on your existing source list. Those suggestions go to the approval queue and never appear in this panel automatically.

---

## 12. AI Brief Preview

The AI Brief Preview generates draft content for any of the 14 brief sections based on the information you have already added to the case. It is the primary AI writing assistant in the Research Workspace.

### What It Does

When you run the AI Brief Preview, it reads the case's existing brief content, tasks, documents, and sources, and returns suggested text for each brief section. The results appear in a preview panel.

The panel header shows: **PREVIEW ONLY — NOT SAVED**

Nothing is applied to your brief until you explicitly choose to apply it.

### Running the Preview

1. Open the Research Workspace for a case.
2. Click **Generate AI Brief Preview**.
3. Wait for the result to appear in the preview panel.
4. Read each suggested section.

### Selecting Sections to Apply

Each suggested section has a checkbox. Check the sections you want to apply.

Then click **Apply Selected Sections**.

The checked sections are merged into your existing brief. Sections you did not check are ignored.

### Saving After Apply

Applying sections updates the brief in memory. You must then click **Save Brief** to persist the changes to the database.

The preview panel closes after you apply. You can run the preview again at any time.

**Important:** Every time you run the preview, it generates fresh suggestions. It does not remember previous runs.

---

## 13. Quality Assist

Quality Assist is an AI tool that reviews your research case and returns a structured checklist of quality dimensions, along with suggested values for the case's status and readiness label.

### What It Checks

The checklist covers 9 quality dimensions, including:
- Whether the situation summary is complete
- Whether key actors are identified
- Whether risks and catalysts are documented
- Whether information sources are registered
- Whether the preliminary thesis is written
- Whether the monitoring plan exists
- Whether information gaps are acknowledged

Each item returns a pass/fail indicator and a brief note.

### Suggested Status and Readiness

Below the checklist, Quality Assist shows:
- A **suggested status** (Under Investigation / Documented / Watching / Archived)
- A **suggested readiness label** (Monitor / Not Actionable / Needs More Work / Candidate)

These are suggestions. Two buttons appear: **Apply Suggested Status** and **Apply Suggested Readiness**. Click either to apply that value, or ignore both.

**Hard rule on Published status:** Quality Assist cannot suggest *Published* as a status. The platform blocks that value entirely and will never generate it as a suggestion. Moving a case to a published state (if it ever becomes available) requires manual editorial action only.

### Running Quality Assist

1. Open the Research Workspace.
2. Click **Run Quality Check**.
3. Read the checklist and suggested values in the preview panel.
4. Apply suggestions individually, or close the panel and ignore them.

The panel header shows: **ASSISTIVE PREVIEW — NOT SAVED**

---

## 14. Document Analysis Preview

Document Analysis Preview runs AI analysis on a single document snippet you have pasted into a document record. It returns a structured breakdown of that excerpt.

### Requirements

- The document record must have a snippet (pasted text).
- The snippet must be at least 50 characters long.

If the snippet is too short, the button will not activate.

### What It Returns

The analysis includes:
- **Summary** — a plain-language summary of the excerpt
- **Key Points** — the main findings or claims in the text
- **Risks** — risk factors mentioned or implied
- **Timeline Items** — any dates, deadlines, or sequenced events mentioned
- **Suggested Research Tasks** — tasks the AI suggests you might want to add
- **Source Usefulness** — an assessment of how useful this document appears to be for the case

All of this is preview-only. Nothing is saved automatically.

### Running the Analysis

1. Open a document record that has a snippet.
2. Click **Analyze Snippet**.
3. Read the results in the preview panel.
4. If the suggested tasks look useful, add them manually to the Tasks panel.

---

## 15. Source Intelligence Preview

Source Intelligence Preview is an AI tool that reviews your current sources for a case and proposes changes — adding new sources, changing the priority of existing ones, or deactivating ones that appear redundant.

### What It Produces

The preview returns a list of **proposals**. Each proposal includes:
- **Action** — Add, Update Priority, or Deactivate
- **Proposed source name**
- **Rationale** — why the AI is suggesting this change
- **Confidence score** — how confident the AI is in this suggestion

The panel header shows: **PROPOSALS ONLY — NOT APPLIED**

Nothing is written to your source list automatically.

### Running the Preview

1. Open the Research Workspace.
2. Click **Generate Source Intelligence Preview**.
3. Read the proposals.
4. If you want to keep the proposals for review, click **Save Proposals to Queue**.

### Saving Proposals

Clicking **Save Proposals to Queue** sends the proposals to the **Source Intelligence Queue** (Chapter 16), where you can review them in detail and decide to approve or reject each one.

If you close the panel without saving, the proposals are discarded.

### After Saving

Once saved, the Source Intelligence panel in the Research Workspace also shows the saved proposals with inline approve and reject buttons. You can act on them from either location.

---

## 16. Source Intelligence Queue

The Source Intelligence Queue is a shared inbox for all source intelligence proposals across all cases — both Research Cases and Historical Cases.

### Opening the Queue

Click **Source Intelligence Queue** in the left navigation.

### What You See

The queue is divided into two sections:

- **Pending Review** — proposals not yet acted upon
- **Reviewed** — proposals you have approved or rejected

You can filter by:
- **Status** — Pending, Approved, Rejected
- **Action type** — Add, Update Priority, Deactivate

Each proposal card shows:
- The proposed source name
- The action type
- The rationale
- The originating case (with a link)
- Approve and Reject buttons (for pending proposals)

### Approving a Proposal

Click **Approve** on a pending proposal. Its status changes to *Approved* and it moves to the Reviewed section.

**Important:** Approving a proposal is a decision record. It does not automatically create a source in any case. The approved proposal is a signal of your intent. Applying it to create an actual source entry will be a separate action in a future platform update.

### Rejecting a Proposal

Click **Reject** on a pending proposal. Its status changes to *Rejected*.

### No Undo

Approve and reject actions cannot currently be undone from the interface. Act deliberately.

---

## 17. Historical Cases

Historical Cases are past special situations that you reconstruct manually for study and reference. They are not linked to any scanner detection. You create them entirely from your own knowledge and notes.

**Why use Historical Cases?** They let you build a library of comparable situations, train your pattern recognition, and accumulate source intelligence from cases the scanner did not detect.

### Creating a Historical Case

1. Go to **Historical Cases** in the navigation.
2. Click **Create Historical Case**.
3. Fill in:
   - **Company Name** (required)
   - **Situation Type** (required) — e.g., spinoff, merger, tender offer
   - **Approximate Event Date** (optional)
   - **Seed Notes** (optional) — initial context you want to capture
4. Click **Save**.

### Historical Case Statuses

A Historical Case moves through four lifecycle stages:

| Status | Meaning |
|---|---|
| **Seed** | Created; basic information only |
| **Reconstructed** | Sufficient detail added to represent the case |
| **Lessons Extracted** | Key learnings documented |
| **Source Intel Applied** | Source intelligence from this case has been processed |

You advance the status manually using the status selector in the case detail page.

### Editing a Historical Case

Open a case from the Historical Cases list. You can edit:
- The status
- The seed notes field (free-text notes about the case)

Click **Save** after any change.

### Source Intelligence for Historical Cases

The Historical Case detail page includes a Source Intelligence Preview panel identical in function to the one in the Research Workspace. You can generate source proposals and save them to the Source Intelligence Queue using the same workflow described in Chapter 15 and Chapter 16.

---

## 18. What SwissEdge Does Not Do Automatically

This chapter is a direct list of things the platform never does without your explicit action.

**SwissEdge does not:**

- **Apply AI results without your approval.** Every AI output (brief preview, quality check, document analysis, source intelligence) is returned as a preview. Nothing is applied or saved until you click an explicit button.

- **Fetch or read URLs.** Document and source URLs are stored as reference labels. The platform does not download, load, or parse any web page or document. You must read documents yourself.

- **Trigger the scanner on your behalf.** The detection scanner runs on its own schedule. You cannot start or stop it from the interface.

- **Create sources automatically from approved proposals.** Approving a source intelligence proposal marks your decision. It does not create a source record. That apply step is not yet available.

- **Publish research.** There is no publish action. No research leaves the platform automatically.

- **Suggest buy or sell actions.** All investment output is educational research. The platform filters any buy/sell language from AI responses before they reach you.

- **Create tasks automatically.** The AI can suggest tasks in a Document Analysis Preview, but you add them to the task list yourself.

- **Change case status without your input.** Status and readiness changes always require an explicit action from you.

---

## 19. Glossary

**Research Case**
A live investigation workspace for a single corporate special situation. Contains a research brief, tasks, documents, sources, and source intelligence proposals. Created from an evaluation or manually.

**Evaluation**
A structured snapshot of a special situation detected from a regulatory filing by the scanner. The starting point for opening a Research Case.

**Special Situation**
A corporate event — such as a spinoff, merger, tender offer, or recapitalization — that creates a potentially significant change in the value or structure of a company.

**Research Brief**
A 14-section structured document that captures everything known about a Research Case, from situation summary through monitoring plan. Built manually, with optional AI drafting assistance.

**Historical Case**
A manually created record of a past special situation, used for pattern study and source intelligence training. Not linked to any scanner detection.

**Source Intelligence**
An AI-powered analysis of the sources registered on a case. Returns proposals for adding, prioritizing, or deactivating sources. Proposals go to the approval queue and require your explicit decision before any action is taken.

**Source Intelligence Queue**
A shared inbox showing all source intelligence proposals across all cases, pending your review. Approve or reject each proposal individually.

**Quality Assist**
An AI tool that reviews your Research Case against a 9-item quality checklist and suggests a status and readiness label. All suggestions are assistive — nothing is applied automatically.

**Document Analysis Preview**
An AI tool that analyzes a text snippet you have pasted into a document record. Returns a structured breakdown including summary, key points, risks, timeline items, and suggested tasks.

**Signal Quality**
Your editorial assessment of how reliable and useful a specific document or source is for a given case. You set this manually.

**Readiness Label**
An editorial tag on a Research Case indicating how actionable the case is from a research perspective: Monitor, Not Actionable, Needs More Work, or Candidate.

**Snippet**
A short excerpt of text from a document, pasted manually into the document record. Required for Document Analysis Preview.

**Seed Notes**
Initial free-text notes entered when creating a Historical Case. Used as the starting point for reconstruction.

---

## 20. FAQ

**Q: I ran the AI Brief Preview but nothing changed in my brief. Why?**
You need to select sections using the checkboxes in the preview panel and then click **Apply Selected Sections**. After that, click **Save Brief** to persist the changes. Simply generating the preview does not modify anything.

**Q: The "Analyze Snippet" button is grayed out. Why?**
The document record either has no snippet, or the snippet is less than 50 characters long. Open the document record, paste a longer excerpt into the snippet field, and save it. The button will become active.

**Q: I approved a source intelligence proposal. Where is the new source?**
Approving a proposal is a decision record. It does not yet create a source entry in your case. That action will be available in a future platform update. For now, if you want to add the proposed source, add it manually using the **Add Source** button in the Sources panel.

**Q: Can I create a Research Case without an evaluation?**
Currently, Research Cases are created from evaluations. If you want to study a situation the scanner has not detected, use a **Historical Case** instead.

**Q: I see the URL I entered for a document but the platform says "metadata only." What does that mean?**
Your URL is stored as a reference label. The platform does not visit that URL or read its content. To analyze the document, visit the URL yourself, copy a relevant excerpt, and paste it into the document's snippet field.

**Q: Can I delete a Research Case?**
Case deletion is not available through the interface. Set the case status to **Archived** to remove it from active views.

**Q: The Quality Assist suggested a status I disagree with. Do I have to use it?**
No. The suggestion is assistive only. Click the status selector and choose the value you want, or simply ignore the suggestion.

**Q: How do I know the scanner found something new?**
Go to **Evaluations** and sort by date, or check **Radar Status** for the scanner's last-run log. You will not receive a push notification.

**Q: Can I edit a brief section after applying AI suggestions to it?**
Yes. Brief sections are always editable. Click **Edit Brief**, change any section, and save.

**Q: Source Intelligence proposals say "Add" — what exactly would be added?**
The proposal describes a source the AI thinks would be useful for the case. If applied (currently a future feature), it would create a new entry in the Sources panel for that case only. It would not add anything to the global sources registry.

---

## 21. Screenshot Checklist

The following screenshots are needed to complete the illustrated version of this guide. Each entry describes what must be visible in the screenshot.

### Navigation and Home

| # | Page | What must be visible |
|---|---|---|
| S-01 | Home / Mission Control | Full left navigation sidebar; all section labels |
| S-02 | Evaluations list | At least one evaluation row; company name, event type, date columns |

### Evaluations and Research Cases

| # | Page | What must be visible |
|---|---|---|
| S-03 | Evaluation Detail | Full assessment card; Create Research Case button at the bottom |
| S-04 | Research Cases list | At least one case; status badge; readiness label |
| S-05 | Research Case Workspace — overview | Header strip with case name, status selector, readiness selector; workflow strip; all four panels visible |

### Research Brief

| # | Page | What must be visible |
|---|---|---|
| S-06 | Research Brief — empty state | Section counter showing 0/14; empty section placeholders |
| S-07 | Research Brief — partially filled | Section counter showing at least 4/14; two or more filled sections |
| S-08 | Brief section editor | One section open for editing; Save button visible |

### Tasks, Documents, Sources

| # | Page | What must be visible |
|---|---|---|
| S-09 | Tasks panel | At least one task; status indicator; Add Task button |
| S-10 | Documents panel | At least one document record; metadata-only label; snippet field |
| S-11 | Sources panel | At least one source record; signal quality indicator |

### AI Features

| # | Page | What must be visible |
|---|---|---|
| S-12 | AI Brief Preview panel | "PREVIEW ONLY — NOT SAVED" header; at least two section suggestions with checkboxes; Apply Selected Sections button |
| S-13 | Quality Assist panel | "ASSISTIVE PREVIEW — NOT SAVED" header; checklist with pass/fail indicators; suggested status and readiness; Apply buttons |
| S-14 | Document Analysis Preview panel | Source document with snippet visible; analysis output with summary, key points, risks |
| S-15 | Source Intelligence Preview panel | "PROPOSALS ONLY — NOT APPLIED" header; at least one proposal with action type and rationale; Save Proposals to Queue button |

### Source Intelligence Queue and Historical Cases

| # | Page | What must be visible |
|---|---|---|
| S-16 | Source Intelligence Queue | Pending Review section; at least one proposal card; Approve and Reject buttons; originating case link |
| S-17 | Source Intelligence Queue — Reviewed section | At least one approved proposal; at least one rejected proposal |
| S-18 | Historical Cases list | At least one historical case; status label; Create Historical Case button |
| S-19 | Historical Case Detail | Status lifecycle selector; seed notes field; Source Intelligence Preview panel |

---

*End of User Guide*

---

**Document information**

- Version: 1.0
- Platform phase: 4C (last deployed feature: Historical Case Source Intelligence Preview)
- Audience: Private platform user
- Status: Draft — pending screenshot integration and Dani review

*All analysis generated by this platform is educational research. It is not financial advice.*
