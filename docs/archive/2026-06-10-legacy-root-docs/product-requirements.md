# Product Requirements — SwissEdge Platform

## Domain 1: Marketplace Assistant

### User Story
As a user in Switzerland, I want to sell my personal items on second-hand marketplaces by sending a photo and brief description to a Telegram bot. The bot should generate a professional listing in German, suggest a fair price, and help me publish it.

### Functional Requirements

**FR-M1: Sell via Telegram**
- User sends photo + text (any language) to Telegram bot
- System identifies item type, brand, model, condition from photo and text
- System asks clarifying questions if needed (via Telegram)
- System generates Hochdeutsch title and description
- System suggests price based on market comparison

**FR-M2: Price Comparison**
- System searches configured marketplaces for similar items
- Returns: average price, median, min, max, number of comparables
- Shows user's price as percentage of market average
- Phase 1 sources: Tutti.ch
- Phase 2+ sources: Ricardo.ch, Amazon DE/ES/FR, Digitec.ch

**FR-M3: Listing Publication**
- Phase 1: System generates formatted text for copy-paste to Tutti.ch
- Phase 2+: Automated publication with user approval
- Progressive trust: after N approvals without edits, suggest auto-publish

**FR-M4: Deal Finding**
- User describes item they want to buy
- System searches marketplaces and returns best deals
- Shows % below market average for each result
- Optional: watch an item and alert when price drops

**FR-M5: Safety Rules (non-negotiable)**
- Never share phone, address, email, bank details
- Never accept offers without approval
- Never arrange meetings without approval
- Never publish without approval (phase 1)
- All outgoing text in Hochdeutsch, simple and clear

### Non-Functional Requirements
- Response time: <30 seconds for listing draft
- Price comparison: cached for 1 hour
- Language: all marketplace text in Hochdeutsch
- Rate limiting: respect marketplace TOS

---

## Domain 2: Special Situations Investment Radar

### User Story
As an investor learning about special situations, I want a system that automatically scans SEC filings and news sources for spin-offs, mergers, tender offers and other corporate events, evaluates them using the methodology from my investment course, and presents me with a prioritized list of opportunities with risk analysis.

### Functional Requirements

**FR-I1: Course Knowledge Base**
- Process 20 chapters of investment course transcripts
- Generate per-chapter: summary, playbook, checklist, timestamps
- Create master index mapping situation types to chapters
- Reference system: any situation → relevant chapter + timestamp

**FR-I2: Source Scanning**
- Scan SEC EDGAR for new filings: 8-K, S-1, F-1, SC TO, Form 10, DEF 14A
- Scan configurable list of sources (YAML config, editable)
- Run 4x daily on schedule
- Filter and classify by situation type

**FR-I3: Situation Evaluation**
- For each detected situation, run evaluation checklist from course
- Score strengths and weaknesses
- Identify key risks
- Attach source URLs and course chapter references
- Assign confidence level

**FR-I4: Situation Lifecycle**
- Status tracking: DETECTED → ANALYZING → WATCHLIST → ACTIVE → CLOSED_PROFIT → CLOSED_LOSS → PASSED → EXPIRED
- Each transition logged with date and reason
- Follow-up agenda: schedule when to re-check a situation
- Telegram alerts for new detections and status changes

**FR-I5: Public Research Journal**
- Web page listing published situations
- Each entry: type, date, company, thesis, checklist, risks, sources, status
- Filter by type, status, date
- Mandatory disclaimer on every page
- SEO optimized

**FR-I6: Historical Analysis (Phase 3)**
- Search for past special situations (2-3 years back)
- Calculate hypothetical returns
- Find who wrote about them (blogs, newsletters)
- Build contact database

**FR-I7: Investment Disclaimers (non-negotiable)**
- Every output includes uncertainty level
- Every output includes identified risks
- Every output includes source citations
- Every output includes course methodology reference
- Every output includes legal disclaimer
- System never provides personalized financial advice

### Non-Functional Requirements
- Scanning frequency: 4x daily minimum
- SEC EDGAR compliance: proper User-Agent, rate limiting
- Data retention: all situations kept indefinitely for track record
- Web performance: <2s page load on research journal
