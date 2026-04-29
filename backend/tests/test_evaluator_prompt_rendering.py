import pytest
from backend.services.investment.evaluator import _load_prompt_v2


def test_v2_prompt_contains_json_schema():
    """Verify that v2 prompt contains literal JSON braces in schema examples."""
    prompt = _load_prompt_v2()

    # The prompt should contain JSON schema examples with literal braces
    assert '"checklist_results":' in prompt
    assert '{{' in prompt  # Double braces for format escaping or literal JSON


def test_v2_prompt_rendering_preserves_json_braces():
    """Test that prompt rendering doesn't fail when template contains JSON schema."""
    from backend.services.investment.sources.base import Filing

    # Create a minimal filing
    filing = Filing(
        company="Test Corp",
        ticker="TEST",
        filing_type="SC TO-I",
        date="2024-07-03",
        url="https://test.com",
        summary="Test tender offer",
        situation_type="tender_offer",
    )

    # Load the v2 prompt template
    template = _load_prompt_v2()

    # Simulate the replacement logic from evaluator
    replacements = {
        "{company_name}": filing.company,
        "{ticker}": filing.ticker or "N/A",
        "{filing_type}": filing.filing_type,
        "{filing_date}": filing.date,
        "{filing_url}": filing.url or "N/A",
        "{filing_summary}": filing.summary,
        "{routing_decision}": "{}",
        "{situation_type}": "tender_offer",
        "{subtype}": "N/A",
        "{playbook_status}": "partial",
        "{selected_playbook}": "tender_offer.md",
        "{detection_confidence}": "HIGH",
        "{allowed_checks}": "None specified",
        "{prohibited_checks}": "None specified",
        "{human_review_triggers}": "None specified",
        "{relevant_risk_patterns}": "See risk_patterns.md",
        "{playbook_context}": "Test context",
        "{evidence_sources}": "Test filing",
    }

    # This should NOT raise KeyError
    prompt = template
    for placeholder, value in replacements.items():
        prompt = prompt.replace(placeholder, value)

    # Verify the prompt still contains JSON schema examples
    assert '"checklist_results":' in prompt
    assert filing.company in prompt
    assert filing.filing_type in prompt
