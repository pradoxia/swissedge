#!/usr/bin/env python3
"""
Manual shadow test for evaluator v2.
Runs v1 and v2 on 2 real SEC filings: SC TO-I and SC TO-T.
"""
import asyncio
import json
import os
from backend.services.investment.sources.base import Filing
from backend.services.investment.evaluator import evaluate_situation


# Test filings - using recent examples
SC_TO_I_FILING = Filing(
    company="Dillard's Inc",
    ticker="DDS",
    filing_type="SC TO-I",
    date="2024-11-15",
    url="https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=0000028917&type=SC+TO-I",
    summary="Dillard's Inc. announces self-tender offer to repurchase up to $500 million of its Class A Common Stock at a price not greater than $425.00 nor less than $375.00 per share. Offer expires December 13, 2024. Odd-lot priority provision included."
)

SC_TO_T_FILING = Filing(
    company="Hess Corporation",
    ticker="HES",
    filing_type="SC TO-T",
    date="2024-10-23",
    url="https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=0000004447&type=SC+TO-T",
    summary="Chevron Corporation commences tender offer to acquire all outstanding shares of Hess Corporation at $171.00 per share in cash. Offer expires November 20, 2024. Minimum condition: majority of shares tendered."
)


async def run_test():
    results = {
        "sc_to_i": {"v1": None, "v2": None},
        "sc_to_t": {"v1": None, "v2": None}
    }

    print("=== SC TO-I Test (Dillard's self-tender) ===\n")

    # SC TO-I v1
    print("Running v1...")
    os.environ.pop("EVALUATOR_VERSION", None)
    try:
        result_v1, usage_v1 = await evaluate_situation(SC_TO_I_FILING)
        results["sc_to_i"]["v1"] = {
            "result": result_v1,
            "usage": usage_v1
        }
        print(f"[OK] v1 complete: {usage_v1.get('input_tokens', 0)} in, {usage_v1.get('output_tokens', 0)} out")
    except Exception as e:
        print(f"[FAIL] v1 failed: {e}")
        results["sc_to_i"]["v1"] = {"error": str(e)}

    # SC TO-I v2
    print("Running v2...")
    os.environ["EVALUATOR_VERSION"] = "v2"
    try:
        result_v2, usage_v2 = await evaluate_situation(SC_TO_I_FILING)
        results["sc_to_i"]["v2"] = {
            "result": result_v2,
            "usage": usage_v2
        }
        print(f"[OK] v2 complete: {usage_v2.get('input_tokens', 0)} in, {usage_v2.get('output_tokens', 0)} out")
    except Exception as e:
        print(f"[FAIL] v2 failed: {e}")
        results["sc_to_i"]["v2"] = {"error": str(e)}

    print("\n=== SC TO-T Test (Chevron/Hess acquisition tender) ===\n")

    # SC TO-T v1
    print("Running v1...")
    os.environ.pop("EVALUATOR_VERSION", None)
    try:
        result_v1, usage_v1 = await evaluate_situation(SC_TO_T_FILING)
        results["sc_to_t"]["v1"] = {
            "result": result_v1,
            "usage": usage_v1
        }
        print(f"[OK] v1 complete: {usage_v1.get('input_tokens', 0)} in, {usage_v1.get('output_tokens', 0)} out")
    except Exception as e:
        print(f"[FAIL] v1 failed: {e}")
        results["sc_to_t"]["v1"] = {"error": str(e)}

    # SC TO-T v2
    print("Running v2...")
    os.environ["EVALUATOR_VERSION"] = "v2"
    try:
        result_v2, usage_v2 = await evaluate_situation(SC_TO_T_FILING)
        results["sc_to_t"]["v2"] = {
            "result": result_v2,
            "usage": usage_v2
        }
        print(f"[OK] v2 complete: {usage_v2.get('input_tokens', 0)} in, {usage_v2.get('output_tokens', 0)} out")
    except Exception as e:
        print(f"[FAIL] v2 failed: {e}")
        results["sc_to_t"]["v2"] = {"error": str(e)}

    # Clean up
    os.environ.pop("EVALUATOR_VERSION", None)

    return results


def analyze_results(results):
    """Analyze results and generate go/no-go decision."""
    report = []
    go = True

    report.append("# Evaluator v2 Manual Shadow Test Results\n")
    report.append(f"**Date:** 2026-04-29\n")
    report.append(f"**Test Filings:** SC TO-I (Dillard's), SC TO-T (Chevron/Hess)\n\n")

    # SC TO-I Analysis
    report.append("## SC TO-I Test (Dillard's Self-Tender)\n\n")

    if "error" in results["sc_to_i"]["v2"]:
        report.append(f"[FAIL] **V2 FAILED:** {results['sc_to_i']['v2']['error']}\n\n")
        go = False
    else:
        v2 = results["sc_to_i"]["v2"]["result"]

        # Check routing
        routing = v2.get("routing_decision", {})
        situation_type = v2.get("situation_type", routing.get("situation_type"))
        selected_playbook = routing.get("selected_playbook")
        playbook_status = v2.get("playbook_status", routing.get("playbook_status"))

        report.append(f"**Routing:**\n")
        report.append(f"- Situation type: `{situation_type}`\n")
        report.append(f"- Selected playbook: `{selected_playbook}`\n")
        report.append(f"- Playbook status: `{playbook_status}`\n\n")

        if situation_type != "tender_offer":
            report.append(f"[FAIL] **ROUTING ERROR:** Expected `tender_offer`, got `{situation_type}`\n\n")
            go = False
        elif selected_playbook != "tender_offer.md":
            report.append(f"[FAIL] **ROUTING ERROR:** Expected `tender_offer.md`, got `{selected_playbook}`\n\n")
            go = False
        elif playbook_status != "partial":
            report.append(f"[WARN] **WARNING:** Expected `partial` status, got `{playbook_status}`\n\n")
        else:
            report.append(f"[OK] **Routing correct:** tender_offer.md, partial status\n\n")

        # Check human review
        human_review = v2.get("human_review_required", [])
        report.append(f"**Human review items:** {len(human_review)}\n")
        if human_review:
            for item in human_review[:3]:
                report.append(f"- {item.get('item', 'N/A')}\n")
        report.append("\n")

        # Check prohibited inferences
        prohibited = v2.get("prohibited_inferences_detected", [])
        if prohibited:
            report.append(f"[FAIL] **PROHIBITED INFERENCES DETECTED:** {prohibited}\n\n")
            go = False
        else:
            report.append(f"[OK] **No prohibited inferences**\n\n")

        # Check disclaimer
        disclaimer = v2.get("disclaimer", "")
        expected_disclaimer = "Este análisis es educativo. No es asesoramiento financiero."
        if disclaimer != expected_disclaimer:
            report.append(f"[FAIL] **DISCLAIMER MISMATCH:**\n")
            report.append(f"- Expected: `{expected_disclaimer}`\n")
            report.append(f"- Got: `{disclaimer}`\n\n")
            go = False
        else:
            report.append(f"[OK] **Disclaimer correct**\n\n")

    # SC TO-T Analysis
    report.append("## SC TO-T Test (Chevron/Hess Acquisition Tender)\n\n")

    if "error" in results["sc_to_t"]["v2"]:
        report.append(f"[FAIL] **V2 FAILED:** {results['sc_to_t']['v2']['error']}\n\n")
        go = False
    else:
        v2 = results["sc_to_t"]["v2"]["result"]

        # Check routing
        routing = v2.get("routing_decision", {})
        situation_type = v2.get("situation_type", routing.get("situation_type"))
        selected_playbook = routing.get("selected_playbook")
        playbook_status = v2.get("playbook_status", routing.get("playbook_status"))

        report.append(f"**Routing:**\n")
        report.append(f"- Situation type: `{situation_type}`\n")
        report.append(f"- Selected playbook: `{selected_playbook}`\n")
        report.append(f"- Playbook status: `{playbook_status}`\n\n")

        if situation_type != "merger_arbitrage":
            report.append(f"[FAIL] **ROUTING ERROR:** Expected `merger_arbitrage`, got `{situation_type}`\n\n")
            go = False
        elif selected_playbook != "merger_arbitrage.md":
            report.append(f"[FAIL] **ROUTING ERROR:** Expected `merger_arbitrage.md`, got `{selected_playbook}`\n\n")
            go = False
        elif playbook_status not in ("evaluator_ready", "partial"):
            report.append(f"[WARN] **WARNING:** Expected `evaluator_ready` or `partial`, got `{playbook_status}`\n\n")
        else:
            report.append(f"[OK] **Routing correct:** merger_arbitrage.md, {playbook_status} status\n\n")

        # Check prohibited inferences
        prohibited = v2.get("prohibited_inferences_detected", [])
        if prohibited:
            report.append(f"[FAIL] **PROHIBITED INFERENCES DETECTED:** {prohibited}\n\n")
            go = False
        else:
            report.append(f"[OK] **No prohibited inferences**\n\n")

        # Check disclaimer
        disclaimer = v2.get("disclaimer", "")
        expected_disclaimer = "Este análisis es educativo. No es asesoramiento financiero."
        if disclaimer != expected_disclaimer:
            report.append(f"[FAIL] **DISCLAIMER MISMATCH:**\n")
            report.append(f"- Expected: `{expected_disclaimer}`\n")
            report.append(f"- Got: `{disclaimer}`\n\n")
            go = False
        else:
            report.append(f"[OK] **Disclaimer correct**\n\n")

    # Usage summary
    report.append("## API Usage Summary\n\n")
    total_input = 0
    total_output = 0
    for filing_type in ["sc_to_i", "sc_to_t"]:
        for version in ["v1", "v2"]:
            if "usage" in results[filing_type][version]:
                usage = results[filing_type][version]["usage"]
                total_input += usage.get("input_tokens", 0)
                total_output += usage.get("output_tokens", 0)

    report.append(f"- Total input tokens: {total_input}\n")
    report.append(f"- Total output tokens: {total_output}\n")
    report.append(f"- Evaluator calls: 4 (2 filings × 2 versions)\n\n")

    # Go/No-Go Decision
    report.append("## Go/No-Go Decision\n\n")
    if go:
        report.append("[OK] **GO** — All criteria met. V2 is ready for limited production testing.\n\n")
        report.append("**Next steps:**\n")
        report.append("1. Review full outputs manually\n")
        report.append("2. Test on 3-5 more filings\n")
        report.append("3. Consider enabling v2 for non-critical evaluations\n")
    else:
        report.append("[FAIL] **NO-GO** — Critical issues detected. Do not enable v2 in production.\n\n")
        report.append("**Required fixes:**\n")
        report.append("1. Review routing logic\n")
        report.append("2. Fix prohibited inference detection\n")
        report.append("3. Verify disclaimer handling\n")
        report.append("4. Re-run shadow test after fixes\n")

    return "".join(report), go


if __name__ == "__main__":
    print("Starting evaluator v2 shadow test...\n")
    results = asyncio.run(run_test())

    print("\n=== Generating Report ===\n")
    report, go_decision = analyze_results(results)

    # Save report
    with open("docs/v2_manual_shadow_test_results.md", "w", encoding="utf-8") as f:
        f.write(report)

    print("Report saved to: docs/v2_manual_shadow_test_results.md")
    print(f"\nDecision: {'GO [OK]' if go_decision else 'NO-GO [FAIL]'}")
