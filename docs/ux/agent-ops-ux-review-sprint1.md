# /agent-ops — UX Review Sprint 1
**Date:** 2026-06-08  
**Reviewer:** Cowork (Claude UX role)  
**Basis:** SwissEdge Cowork Onboarding doc §6–8 + GUARDRAILS.md  
**Scope:** UI / copy / layout only. No backend, DB, new routes, autonomous behavior, or investment-recommendation language.

---

## UX Review Summary

Sprint 1 moved `/agent-ops` from a confusing "concept only" skeleton with broken states into a functional governance surface with real data, honest empty states, and clear role separation. The most critical gaps from Batch 1 — no role identity for the agents, all-zero Dani Weber metrics, a hard error on Fontana, and no guardrail framing — are now resolved.

What remains are polish issues and two copy problems that could still confuse a first-time viewer: a technical jargon string that hasn't been cleared ("deterministic observer report" / "0 activity row(s)") and truncated endpoint labels that look like display bugs. The Campus ↔ Agent Ops ↔ Mission Control navigation story is still implicit. None of these block a demo, but the copy issues should be addressed before closing Sprint 1.

**Sprint 1 fixes: confirmed implemented (8/10 items)**  
**Still open: 2 copy issues + 1 layout issue**

---

## What Works Well

**Role identity is now clear.** Fontana (CTO · System Governor) and Dani Weber (COO · Operations Governor) are distinguished by role chips, making it obvious they serve different functions without needing to read a tooltip.

**Diagnostic-only framing is explicit.** MODE = `diagnostic_only`, the always-visible guardrail banner, and the "requires Dani approval" tag on every Governance Proposal work together to make autonomy impossible to misread.

**Honesty of runtime state.** "Intended cadence: every 4h · runtime not active yet" is exactly the right copy — it signals intent without overpromising. This is a meaningful upgrade from Batch 1's silent zeros.

**Real data on Dani Weber.** 39 signals / 8% promoted / 402 missing resources is actionable and credible. Batch 1 showed all zeros, which looked broken.

**Fontana's report structure is correct.** Summary → System Health → Bottlenecks/Evidence Gaps → Proposed Tasks → Guardrails is a logical, scannable hierarchy. The Guardrails row at the bottom anchors the report's authority boundary.

**Governance Proposals are safely framed.** RISK/COMPLEXITY chips + read-only status + per-proposal approval tag make the proposals feel like a review queue, not an action panel.

**Agent Roster empty states read as intentional.** "No runs yet" is honest and doesn't look like an error.

---

## Risks / Confusing Areas

**1. Truncated endpoint strings look like display bugs.**  
`GET /api/investment/e…weber-metrics` — a viewer who doesn't know the system will assume the text overflowed incorrectly. There's no tooltip or affordance indicating it's intentionally shortened.

**2. Jargon in Fontana's report.**  
"deterministic observer report" is internal architecture language, not operational copy. Same for "0 activity row(s)" — the parenthetical singular/plural construct reads like raw template output that wasn't cleaned up.

**3. Governance Proposals section title could imply action.**  
"Governance / Improvement Proposals" — "Proposals" suggests something is being submitted to Dani for approval right now, which is correct, but without subtext the section looks like a to-do list, not a read-only review queue. A first viewer might try to click "approve" and find nothing interactive.

**4. Campus ↔ Agent Ops ↔ Mission Control relationship is still implicit.**  
The document notes that Mission Control links to `/agent-ops` but doesn't duplicate full governance. From inside `/agent-ops`, there's no breadcrumb or contextual line that says what surface this is relative to Campus. If a user lands here from the wrong page they won't know where they are in the product.

**5. Agent room names are semantically mismatched (known, tracked).**  
`radar_room` is displayed where "Detection Room" would be more meaningful. `agent_ops` is a backend name exposed in the frontend. Noted here for completeness; backend alignment is tracked as a future sprint item.

---

## Must Fix Before Closing Sprint 1

1. **Clean up Fontana report copy.** Replace "deterministic observer report" with plain operational language. Replace "0 activity row(s)" with a proper empty state string.

2. **Fix truncated endpoint labels.** Either show full endpoint text (wrapping is fine in a metadata row), or add a `title` attribute tooltip so hover reveals the full path. The current truncation looks like a CSS overflow bug.

3. **Add a read-only indicator to the Governance Proposals section header.** A small "(read-only · pending approval)" line under the section title removes ambiguity about whether any action is available.

---

## Nice To Have

- Add a one-line contextual note at the top of `/agent-ops` linking back to Mission Control: "This is the governance surface for the SwissEdge operating system. → Return to Mission Control". Low effort, removes navigation confusion.
- "Proposed Engineering Tasks" in Fontana's report could drop "Engineering" — it's redundant given Fontana is the CTO agent. "Proposed Tasks" reads cleaner and is equally unambiguous.
- Dani Weber's top bottleneck label ("top bottleneck = missing required resources") could be a highlighted callout line rather than inline text, giving it more visual weight relative to the metric grid.

---

## Future Sprint Ideas

- **Dedicated navigation bar or breadcrumb** connecting Mission Control → Campus → Agent Ops → Case Surface. (New layout element, future sprint.)
- **Agent room semantic rename** — `radar_room` → Detection Room, `agent_ops` → Executive Office — once backend alignment is approved. (Requires backend label change; future sprint.)
- **Dedicated `/governance` route** — the document notes this doesn't exist yet; when it does, `/agent-ops` should redirect or clarify the relationship.
- **Execution calendar portal** — already scoped as next piece of work per §4.
- **Collapsible Fontana report** — if the report grows, a collapsed-by-default view with "Expand full report" would reduce page density.

---

## Suggested Copy Changes

| Location | Current | Suggested |
|---|---|---|
| Fontana report header | "deterministic observer report" | "System status report" |
| Fontana report empty activity | "0 activity row(s)" | "No activity recorded yet" |
| Fontana report task section | "Proposed Engineering Tasks — require Dani approval" | "Proposed Tasks · Pending Dani's approval" |
| Governance Proposals section header | "Governance / Improvement Proposals" | "Governance Proposals · Read-only · Pending Dani's approval" |
| Endpoint label (truncated) | `GET /api/investment/e…weber-metrics` | Full path shown (wrap) or tooltip on hover |
| Agent Roster section (if not present) | *(no context label)* | "Active agents and rooms — no runs recorded yet" |
| Page-level sub-navigation (if absent) | *(none)* | "← Mission Control · Agent Operations & Governance" |

---

## Suggested Layout Changes

1. **Endpoint strings:** Switch from `text-overflow: ellipsis` to `word-break: break-all` or `overflow-wrap: anywhere` in the endpoint metadata row. Endpoints are important enough to show in full; they're short enough to wrap without breaking the card layout.

2. **Governance Proposals section header:** Add a secondary line in muted text below the section title: "Read-only review queue · each item requires Dani's approval before any implementation." This can reuse existing muted-text styles from the guardrail banner.

3. **Fontana report Guardrails row:** Consider pinning the Guardrails row visually (thin top border or slightly different background) to distinguish it from the diagnostic content rows. It's governance metadata, not diagnostic output — it should feel anchored, not like a trailing footnote.

4. **Dani Weber top bottleneck callout:** Lift the bottleneck label out of the metric grid and show it as a highlighted line directly below the four metric chips. Use the same peach/gold palette chip used elsewhere in the design system. This makes the most actionable signal immediately visible.

---

## Codex Implementation Handoff

All items below are UI/copy/layout only. No backend changes, no new routes, no DB changes, no autonomous behavior.

**P1 — Must fix before Sprint 1 closes:**

- [ ] In Fontana's report component: replace the string `"deterministic observer report"` with `"System status report"`. Locate the string in the frontend template for the Fontana card/report section.
- [ ] In Fontana's report component: replace the empty-state string `"0 activity row(s)"` (or equivalent template) with `"No activity recorded yet"`.
- [ ] In the Fontana report, rename the proposed tasks section label from `"Proposed Engineering Tasks — require Dani approval"` to `"Proposed Tasks · Pending Dani's approval"`.
- [ ] In the Governance Proposals section header: add a secondary subtitle line `"Read-only review queue · each item requires Dani's approval before any implementation."` Style it in muted text below the section title (reuse existing muted/subtitle class).
- [ ] Fix truncated endpoint labels: change the CSS rule controlling endpoint string display from `overflow: hidden; text-overflow: ellipsis` to `overflow-wrap: anywhere; word-break: break-all`. No content change needed, only the style rule.

**P2 — Nice to have, same sprint if time allows:**

- [ ] Remove "Engineering" from "Proposed Engineering Tasks" → "Proposed Tasks".
- [ ] Add `title="[full endpoint URL]"` attribute to truncated endpoint elements as a fallback tooltip (even if the CSS fix above ships, the tooltip is a safe safety net).
- [ ] Add a muted breadcrumb/return link at the top of `/agent-ops`: `"← Mission Control"` linking to `/`.

---

## Claude Code Verification Checklist

When Codex delivers the fixes above, Claude Code should verify:

- [ ] `"deterministic observer report"` no longer appears in any rendered string in the Fontana card. Grep for the string in frontend files.
- [ ] `"0 activity row(s)"` (and variants like `"${n} activity row(s)"`) replaced with the new empty-state copy. Grep for the pattern.
- [ ] Fontana's proposed-tasks section label reads "Proposed Tasks · Pending Dani's approval" (or equivalent agreed copy). Not "Proposed Engineering Tasks".
- [ ] Governance Proposals section header has a visible subtitle / secondary line. Check rendered output — the line must appear on the actual page, not just in code.
- [ ] No endpoint label is truncated with ellipsis. Visually verify or check the CSS rule on the endpoint display element.
- [ ] No buy/sell language introduced. Grep for "buy", "sell", "recommend", "invest in" in the changed files.
- [ ] No new routes added. Confirm no new `/api/` or Next.js page routes were created as part of these UI changes.
- [ ] No cron or scanner behavior changed. Confirm no changes to APScheduler config or scanner-related files.
- [ ] Guardrail banner remains visible (not removed or conditionally hidden) after the layout changes.
- [ ] Agent Roster still shows "no runs yet" empty state (not replaced with fake data or removed).
- [ ] MODE = `diagnostic_only` label still present on both Fontana and Dani Weber cards.
- [ ] RISK/COMPLEXITY chips still present on each Governance Proposal item.
