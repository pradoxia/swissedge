import pytest
from pathlib import Path
from backend.services.investment.playbook_loader import (
    load_evaluation_schema,
    get_situation_rules,
    get_allowed_checks,
    get_prohibited_checks,
    get_default_playbook_status,
    get_default_recommendation_if_detection_only,
    load_artifact_text,
)


def test_load_evaluation_schema():
    schema = load_evaluation_schema()
    assert "schema_version" in schema
    assert "enumerations" in schema
    assert "situation_rules" in schema
    assert schema["schema_version"] == "1.0"


def test_get_situation_rules_merger_arbitrage():
    rules = get_situation_rules("merger_arbitrage")
    assert "allowed_checks" in rules
    assert "prohibited_checks" in rules
    assert "default_playbook_status" in rules
    assert rules["default_playbook_status"] == "evaluator_ready"


def test_get_allowed_checks_merger_arbitrage():
    checks = get_allowed_checks("merger_arbitrage")
    assert isinstance(checks, list)
    assert len(checks) > 0
    assert "calculate_gross_spread" in checks


def test_get_prohibited_checks_merger_arbitrage():
    checks = get_prohibited_checks("merger_arbitrage")
    assert isinstance(checks, list)
    assert len(checks) > 0
    assert "stock_for_stock_exchange_ratio_analysis" in checks


def test_get_default_playbook_status():
    status = get_default_playbook_status("merger_arbitrage")
    assert status == "evaluator_ready"

    status = get_default_playbook_status("spin_off")
    assert status == "partial"

    status = get_default_playbook_status("proxy_fight")
    assert status == "detection_only"


def test_get_default_recommendation_if_detection_only():
    rec = get_default_recommendation_if_detection_only("proxy_fight")
    assert rec == "DETECTION_ONLY"

    rec = get_default_recommendation_if_detection_only("merger_arbitrage")
    assert rec is None


def test_load_artifact_text_taxonomy():
    text = load_artifact_text("taxonomy")
    assert len(text) > 0
    assert "Investment Situation Taxonomy" in text
    assert "Version:" in text


def test_load_artifact_text_source_map():
    text = load_artifact_text("source_map")
    assert len(text) > 0
    assert "Investment Data Source Map" in text


def test_load_artifact_text_risk_patterns():
    text = load_artifact_text("risk_patterns")
    assert len(text) > 0
    assert "Investment Risk Pattern Library" in text


def test_load_artifact_text_global_checklist():
    text = load_artifact_text("global_checklist")
    assert len(text) > 0
    assert "Global Investment Evaluation Checklist" in text


def test_load_artifact_text_invalid_name():
    with pytest.raises(ValueError):
        load_artifact_text("invalid_artifact_name")
