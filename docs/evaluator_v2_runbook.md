# Investment Evaluator v2 — Controlled Deployment Runbook

**Version:** 1.0  
**Date:** 2026-04-29  
**Status:** Pre-deployment validation phase

---

## 1. Purpose

Controlled validation of investment evaluator v2 before production activation. V2 introduces structured routing, evaluation_schema.json-compliant output, and prohibited inference guards. This runbook ensures v2 is validated on live SEC filings before enabling in production.

---

## 2. Current Safety State

### Production Status
- **V1 remains default** — `EVALUATOR_VERSION` unset or `v1`
- **V2 only activates with explicit flag** — `EVALUATOR_VERSION=v2`
- **42/42 tests passed** — all tests use mocks (no live AI/SEC calls)
- **V2 not yet validated on live SEC filings** — requires manual testing
- **V2 must not be enabled in cron/global production** — manual activation only

### Feature Flag Behavior
- Default: `EVALUATOR_VERSION=v1` (or unset)
- V2 activation: Set `EVALUATOR_VERSION=v2` in environment
- Safe fallback: V2 errors automatically fall back to v1 with warning log
- No DB schema changes required for v2 activation

### Code Locations
- Evaluator: `backend/services/investment/evaluator.py`
- Routing engine: `backend/services/investment/routing_engine.py`
- Playbook loader: `backend/services/investment/playbook_loader.py`
- V2 prompt: `backend/prompts/situation_evaluator_v2.txt`
- Tests: `backend/tests/test_evaluator.py`, `backend/tests/test_routing_engine.py`, `backend/tests/test_playbook_loader.py`

---

## 3. Pre-Flight Checklist

Before any v2 testing:

- [ ] Confirm latest tests pass: `python -m pytest backend/tests/test_evaluator.py backend/tests/test_playbook_loader.py backend/tests/test_routing_engine.py -v`
- [ ] Confirm `docs/PROJECT_STATE.md` is current
- [ ] Confirm `course_index/playbooks/` artifacts exist and are v1.0
- [ ] Confirm no deploy/environment change without explicit approval
- [ ] Confirm rollback path to v1 is clear (unset `EVALUATOR_VERSION` or set to `v1`)
- [ ] Confirm FastAPI backend is running and healthy
- [ ] Confirm observability endpoints are accessible (`/api/observability/summary`)

---

## 4. Shadow Testing Plan

### 4.1 Test Filing Selection

Select a small, representative set of known SEC filings:

1. **Cash merger / acquisition tender (SC TO-T)**
   - Example: Recent definitive merger agreement with SC TO-T filing
   - Expected routing: `merger_arbitrage.md`
   - Expected playbook_status: `evaluator_ready`

2. **Self-tender (SC TO-I)**
   - Example: Recent issuer self-tender offer
   - Expected routing: `tender_offer.md`
   - Expected playbook_status: `partial`
   - Expected human_review: hold-vs-tender decision flagged

3. **Spin-off (Form 10)**
   - Example: Recent spinco registration statement
   - Expected routing: `spin_off.md`
   - Expected playbook_status: `partial`
   - Expected human_review: sum-of-parts valuation, institutional mandate inference flagged

4. **Plan of dissolution / liquidation (8-K)**
   - Example: Recent voluntary liquidation announcement
   - Expected routing: `bankruptcy.md`
   - Expected playbook_status: `partial`
   - Expected human_review: NAV construction flagged

5. **Proxy fight or rights offering (SC 13D or S-3)**
   - Example: Recent activist campaign or rights offering
   - Expected routing: `proxy_fight.md` or `rights_offering.md`
   - Expected playbook_status: `detection_only`
   - Expected recommendation: `DETECTION_ONLY`

### 4.2 Testing Procedure

For each test filing:

1. **Run v1 evaluation:**
   ```bash
   # Ensure EVALUATOR_VERSION is unset or v1
   unset EVALUATOR_VERSION
   # Call POST /api/investment/scan or evaluate_situation() directly
   # Save v1 output to file: v1_output_<filing_type>.json
   ```

2. **Run v2 evaluation:**
   ```bash
   # Set v2 flag
   export EVALUATOR_VERSION=v2
   # Call same endpoint/function with same filing
   # Save v2 output to file: v2_output_<filing_type>.json
   ```

3. **Compare outputs:**
   - Routing decision: situation_type, subtype, selected_playbook, detection_confidence
   - Recommendation: PASS / WATCHLIST / DEEP_RESEARCH / HUMAN_REVIEW_REQUIRED / OUT_OF_SCOPE / DETECTION_ONLY
   - Human review items: list of items flagged for human review
   - Risk flags: list of risks detected
   - Prohibited inferences: list of fabrication attempts detected
   - Missing documents: list of documents required but not available
   - Disclaimer: exact string match

4. **Document differences:**
   - Create comparison table in `docs/v2_shadow_test_results.md`
   - Note any routing errors, missing fields, or unexpected behavior

### 4.3 Comparison Checklist

For each filing comparison:

- [ ] V2 routing matches expected playbook (SC TO-T → merger_arbitrage, SC TO-I → tender_offer, etc.)
- [ ] V2 playbook_status matches expected status (evaluator_ready, partial, detection_only)
- [ ] V2 recommendation is schema-compliant (one of 6 valid values)
- [ ] V2 human_review_required list is populated for partial playbooks
- [ ] V2 prohibited_inferences_detected is empty (no fabrication attempts)
- [ ] V2 disclaimer is exactly: "Este análisis es educativo. No es asesoramiento financiero."
- [ ] V2 output has all required schema fields (situation_type, subtype, playbook_status, evaluator_confidence, recommendation, routing_decision, evidence_sources, checklist_results, risk_flags, human_review_required, prohibited_inferences_detected, missing_documents, latest_amendment_check, scope_notes, disclaimer)
- [ ] V2 does not crash or fall back to v1 unexpectedly

---

## 5. Go / No-Go Criteria

### GO Criteria (proceed to limited production testing)

All of the following must be true:

- ✅ Routing is correct for all 5 test filings
- ✅ No fabricated valuation, NAV, recovery, tax, legal, broker outputs in any test
- ✅ Disclaimer present and exact in all outputs
- ✅ Schema fields stable and populated correctly
- ✅ Prohibited inference guard detects fabrication attempts (if any)
- ✅ V2 does not crash without fallback
- ✅ V2 does not misroute SC TO-I / SC TO-T
- ✅ Human review items are appropriately flagged for partial playbooks

### NO-GO Criteria (do not proceed)

Any of the following triggers a no-go:

- ❌ Any prohibited inference is accepted as fact (NAV construction, sum-of-parts, recovery estimate, institutional mandate, broker deadline, tax advice, legal outcome, CFIUS status)
- ❌ V2 crashes without falling back to v1
- ❌ V2 misroutes SC TO-I to merger_arbitrage or SC TO-T to tender_offer
- ❌ V2 output missing required schema fields
- ❌ V2 disclaimer missing or incorrect
- ❌ V2 recommendation outside valid enum values
- ❌ V2 playbook_status does not match taxonomy.md definitions

---

## 6. Rollback Plan

### Immediate Rollback

If v2 causes errors or produces invalid output:

1. **Unset or revert environment variable:**
   ```bash
   unset EVALUATOR_VERSION
   # OR
   export EVALUATOR_VERSION=v1
   ```

2. **Restart FastAPI backend (if needed):**
   ```bash
   # Only with explicit approval
   # systemctl restart swissedge-backend
   ```

3. **Verify v1 is active:**
   ```bash
   # Call /api/investment/scan
   # Verify output has v1 structure (checklist_results, strengths, weaknesses, risks, confidence, recommendation)
   ```

### No DB Schema Changes

V2 does not require DB schema changes. Rollback is environment-variable-only.

### Observability

Monitor `agent_runs` table for evaluation failures:
```sql
SELECT * FROM agent_runs 
WHERE agent_name = 'investment_evaluator' 
AND status = 'failed' 
ORDER BY started_at DESC 
LIMIT 10;
```

---

## 7. Manual Review Checklist for First 10 V2 Evaluations

For each of the first 10 v2 evaluations in production:

- [ ] **Route correctness:** situation_type and selected_playbook match filing type
- [ ] **Playbook status correctness:** evaluator_ready / partial / routing_detection_only / detection_only / out_of_scope matches taxonomy.md
- [ ] **Human review flags:** appropriate items flagged for partial playbooks (NAV, sum-of-parts, recovery, mandate, broker, tax, legal)
- [ ] **Prohibited inference guard:** no fabricated values in summary or scope_notes
- [ ] **Recommendation sanity:** recommendation matches evaluator_confidence and playbook_status
- [ ] **Disclaimer present:** exact string "Este análisis es educativo. No es asesoramiento financiero."
- [ ] **Schema completeness:** all required fields populated (no missing arrays/objects)
- [ ] **Evidence sources:** filing details recorded in evidence_sources array
- [ ] **Risk flags:** relevant risks from risk_patterns.md detected
- [ ] **Amendment check:** latest_amendment_check performed (if applicable)

### Review Frequency

- First 5 evaluations: review within 1 hour
- Next 5 evaluations: review within 24 hours
- After 10 successful reviews: reduce to spot-check (1 in 10)

---

## 8. Dashboard Implications

### Fields to Expose (when v2 output is stable)

The following v2 fields should be exposed in future dashboard/observability UI:

- `routing_decision` — show detected_form_type, selected_playbook, detection_confidence
- `evaluator_confidence` — FULL / PARTIAL / INSUFFICIENT
- `recommendation` — PASS / WATCHLIST / DEEP_RESEARCH / HUMAN_REVIEW_REQUIRED / OUT_OF_SCOPE / DETECTION_ONLY
- `risk_flags` — list of detected risks with severity
- `human_review_required` — list of items requiring human judgment
- `prohibited_inferences_detected` — list of fabrication attempts (should be empty)
- `missing_documents` — list of documents required but not available
- `latest_amendment_check` — amendment status and stale data risk

### Dashboard Timing

**Do not build dashboard integration until:**
- V2 has been validated on 50+ live filings
- V2 output schema is stable (no breaking changes for 2 weeks)
- V2 is enabled in production cron jobs

---

## 9. Production Activation Checklist

**Do not enable v2 in production until:**

- [ ] Shadow testing complete (5 test filings, all pass go/no-go criteria)
- [ ] First 10 manual reviews complete (all pass review checklist)
- [ ] No prohibited inferences detected in any evaluation
- [ ] No v2 crashes or unexpected fallbacks to v1
- [ ] Observability confirms v2 is logging correctly to agent_runs and ai_usage
- [ ] Explicit approval from Dani to enable v2 in production
- [ ] Rollback plan tested and confirmed working

### Production Activation Steps

1. **Set environment variable in production:**
   ```bash
   # In .env or systemd service file
   EVALUATOR_VERSION=v2
   ```

2. **Restart FastAPI backend:**
   ```bash
   # Only with explicit approval
   # systemctl restart swissedge-backend
   ```

3. **Monitor first 24 hours:**
   - Check `/api/observability/summary` for evaluation failures
   - Check `agent_runs` table for failed evaluations
   - Spot-check 5 evaluations manually

4. **If any issues:**
   - Immediately rollback to v1 (unset EVALUATOR_VERSION)
   - Document issue in `docs/v2_production_issues.md`
   - Fix issue before re-attempting activation

---

## 10. Known Limitations

### V2 Scope Limits

- **Merger arbitrage:** evaluator-ready for cash merger and acquisition tender paths only; stock-for-stock and CVR outside scope
- **Spin-off:** partial; sum-of-parts valuation and institutional mandate inference require human review
- **Tender offer:** partial; hold-vs-tender decision, Dutch auction clearing, broker confirmation, tax treatment require human review
- **Bankruptcy:** partial; NAV construction, margin-of-safety, recovery estimation require human review
- **Proxy fight:** detection-only; no evaluation methodology
- **Rights offering:** detection-only; no evaluation methodology

### V2 Does Not Support

- Non-US regulatory processes (CFIUS, non-US merger frameworks)
- Chapter 11 / Chapter 7 bankruptcy analysis
- Post-reorganization equity valuation
- Liquidation trust analysis
- Out-of-court restructuring
- Appraisal rights valuation
- CVR milestone probability estimation
- Dutch auction clearing price estimation
- Institutional mandate inference from 13F fund category
- Broker internal deadline identification
- Personal tax treatment determination

---

## 11. Contact and Escalation

### For Issues During Testing

- Document in `docs/v2_shadow_test_results.md`
- Do not proceed to production if go/no-go criteria not met
- Escalate to Dani for architecture decisions

### For Production Issues

- Immediate rollback to v1
- Document in `docs/v2_production_issues.md`
- Check observability endpoints for error details
- Review `agent_runs` table for failure patterns

---

## 12. Success Metrics

### Shadow Testing Success

- 5/5 test filings pass go/no-go criteria
- 0 prohibited inferences detected
- 0 routing errors
- 0 v2 crashes without fallback

### Production Success (after 30 days)

- >95% evaluation success rate (no crashes, no fallbacks)
- 0 prohibited inferences detected in production
- <5% human review escalation rate for evaluator-ready playbooks
- User feedback confirms v2 output is more useful than v1

---

**End of runbook v1.0**
