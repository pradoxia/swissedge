# Open Questions — SwissEdge Platform

## Must Answer Before Phase 1

### Q1: Telegram Bot — New or Reuse OpenClaw's?
**Status:** NEEDS DECISION
**Options:**
- A) Reuse existing OpenClaw Telegram bot → simpler, but OpenClaw controls the conversation
- B) Create a new bot → more control, but need to manage two bots

**Recommendation:** Reuse OpenClaw's bot. Configure OpenClaw to route marketplace/investment messages to FastAPI endpoints. Less setup, same result.

**Action:** Test if OpenClaw bot can call custom HTTP endpoints with photo attachments.

---

### Q2: AI Provider for Description Generation
**Status:** NEEDS DECISION
**Options:**
- A) ChatGPT via OpenClaw (already paid for)
- B) Claude API (separate cost)
- C) Local model (no cost, lower quality)

**Recommendation:** Start with ChatGPT via OpenClaw since you already pay for it. Design the AI client as a swappable interface so you can switch later.

---

### Q3: Course Language
**Status:** WAITING FOR USER INPUT
**Question:** Is the investment course in Spanish or English?
**Impact:** Affects transcript processing prompts and situation type taxonomy.

---

### Q4: Amazon Associates Account
**Status:** WAITING FOR USER INPUT
**Question:** Do you have an Amazon Associates (affiliate) account for DE/ES/FR?
**Impact:** Required for Product Advertising API. Without it, Amazon price comparison will need scraping instead.

---

### Q5: Seeking Alpha — Language Commitment
**Status:** WAITING FOR USER INPUT
**Question:** Are you willing to write/review analyses in English for Seeking Alpha?
**Impact:** Determines if we build English output in the publisher or skip Seeking Alpha.

---

## Must Answer Before Phase 2

### Q6: Ricardo.ch Partnership
**Status:** NOT STARTED
**Action:** Apply for Ricardo.ch partnership credentials.
**URL:** https://help.ricardo.ch (look for partner/developer section)

### Q7: OpenClaw Cron Configuration
**Status:** NOT STARTED
**Question:** How does OpenClaw configure scheduled tasks? Need to document the exact steps.

### Q8: VPS Resources
**Status:** NEEDS ASSESSMENT
**Question:** How much RAM/CPU/disk does the Contabo VPS have? Is there enough for PostgreSQL + Redis + FastAPI + OpenClaw simultaneously?

---

## Can Answer Later

### Q9: Substack Setup
When ready for Phase 3. Newsletter name, branding, initial content plan.

### Q10: Domain Name
For the research journal website. Suggestions: swissedge.ch, specialsits.ch, etc.

### Q11: Browser Automation Approach
For Phase 2+ auto-publishing on Tutti.ch. Options: Playwright, Puppeteer, or Selenium.
Recommendation: Playwright (best modern option, good Python support).

### Q12: Multi-Language Web
Should the research journal be in English only, or also German/French for Swiss audience?
Recommendation: English only at first (investment community is global).
