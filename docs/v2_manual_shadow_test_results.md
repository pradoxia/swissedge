# Evaluator v2 Manual Shadow Test Results
**Date:** 2026-04-29
**Test Filings:** SC TO-I (Dillard's), SC TO-T (Chevron/Hess)

## SC TO-I Test (Dillard's Self-Tender)

**Routing:**
- Situation type: `tender_offer`
- Selected playbook: `tender_offer.md`
- Playbook status: `partial`

[OK] **Routing correct:** tender_offer.md, partial status

**Human review items:** 1
- Valuation of shares in relation to offer price

[OK] **No prohibited inferences**

[OK] **Disclaimer correct**

## SC TO-T Test (Chevron/Hess Acquisition Tender)

**Routing:**
- Situation type: `merger_arbitrage`
- Selected playbook: `merger_arbitrage.md`
- Playbook status: `evaluator_ready`

[OK] **Routing correct:** merger_arbitrage.md, evaluator_ready status

[OK] **No prohibited inferences**

[OK] **Disclaimer correct**

## API Usage Summary

- Total input tokens: 5378
- Total output tokens: 2437
- Evaluator calls: 4 (2 filings × 2 versions)

## Go/No-Go Decision

[OK] **GO** — All criteria met. V2 is ready for limited production testing.

**Next steps:**
1. Review full outputs manually
2. Test on 3-5 more filings
3. Consider enabling v2 for non-critical evaluations
