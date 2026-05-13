from __future__ import annotations

import inspect
import uuid

from backend.models.investment import SpecialSituation
from backend.models.investment_research import HistoricalCase, ResearchCase
from backend.services.investment import historical_analogues as module
from backend.services.investment.historical_analogues import (
    build_research_case_historical_analogues,
    build_situation_historical_analogues,
)


def _workspace(*, playbook: str = "tender_offer", missing: bool = True) -> dict:
    status = "missing" if missing else "evidence_found"
    return {
        "selected_playbook": playbook,
        "methodology_status": "partial",
        "required_resources": [
            {
                "resource_id": "offer_purchase",
                "title": "Offer to Purchase",
                "source_type": "offer_document",
                "status": status,
            }
        ],
        "checklist": [
            {
                "check_id": "offer_terms",
                "title": "Offer terms",
                "section": "terms",
                "status": status,
            }
        ],
    }


def _situation(*, filing_type: str, situation_type: str, playbook: str = "tender_offer") -> SpecialSituation:
    return SpecialSituation(
        id=uuid.uuid4(),
        situation_type=situation_type,
        company_name="Example Corp",
        ticker="EXM",
        filing_type=filing_type,
        filing_url="https://www.sec.gov/example",
        status="detected",
        evaluation={
            "sec_detection": {
                "detected_form_type": filing_type,
                "situation_type": situation_type,
                "selected_playbook": playbook,
            },
            "methodology_workspace": _workspace(playbook=playbook),
        },
    )


def _research_case_from_situation(situation: SpecialSituation) -> ResearchCase:
    return ResearchCase(
        id=uuid.uuid4(),
        situation_id=situation.id,
        status="under_investigation",
        brief={
            "detection_summary": {
                "company_name": situation.company_name,
                "ticker": situation.ticker,
                "filing_type": situation.filing_type,
                "situation_type": situation.situation_type,
                "selected_playbook": "tender_offer",
            },
            "methodology_workspace_snapshot": _workspace(playbook="tender_offer"),
        },
        disclaimer="Educational only.",
        methodology_status="partial",
        playbook_used="tender_offer",
    )


def _historical_case(*, situation_type: str, playbook: str = "tender_offer", filing_type: str = "SC TO-I") -> HistoricalCase:
    return HistoricalCase(
        id=uuid.uuid4(),
        company_name=f"Historical {situation_type}",
        situation_type=situation_type,
        status="reconstructed",
        disclaimer="Educational only.",
        reconstruction={
            "filing_type": filing_type,
            "playbook_used": playbook,
            "methodology_status": "partial",
            "methodology_workspace": _workspace(playbook=playbook, missing=False),
        },
    )


def _all_text(value) -> str:
    if isinstance(value, dict):
        return " ".join(_all_text(v) for v in value.values())
    if isinstance(value, list):
        return " ".join(_all_text(v) for v in value)
    return str(value)


def test_sc_to_i_maps_to_self_tender_pattern():
    package = build_situation_historical_analogues(_situation(filing_type="SC TO-I", situation_type="tender_offer"))
    assert package.matched_patterns[0].pattern_id == "self_tender_sc_to_i"
    assert "self-tender" in package.matched_patterns[0].title.lower()


def test_sc_to_t_maps_to_tender_merger_pattern():
    package = build_situation_historical_analogues(_situation(filing_type="SC TO-T", situation_type="merger_arbitrage"))
    assert package.matched_patterns[0].pattern_id == "acquisition_tender_sc_to_t"


def test_form_10_maps_to_spin_off_pattern():
    package = build_situation_historical_analogues(_situation(filing_type="Form 10", situation_type="spin_off", playbook="spin_off"))
    assert package.matched_patterns[0].pattern_id == "spin_off_form_10"


def test_8k_liquidation_maps_to_liquidation_pattern():
    package = build_situation_historical_analogues(_situation(filing_type="8-K", situation_type="liquidation", playbook="liquidation"))
    assert package.matched_patterns[0].pattern_id == "liquidation_dissolution_8k"


def test_research_case_promoted_snapshot_returns_relevant_pattern():
    situation = _situation(filing_type="SC TO-I", situation_type="tender_offer")
    package = build_research_case_historical_analogues(_research_case_from_situation(situation), source_situation=situation)
    assert package.case_type == "research_case"
    assert package.matched_patterns[0].pattern_id == "self_tender_sc_to_i"


def test_historical_case_same_situation_type_scores_higher_than_different_type():
    situation = _situation(filing_type="SC TO-I", situation_type="tender_offer")
    same = _historical_case(situation_type="tender_offer", filing_type="SC TO-I")
    different = _historical_case(situation_type="spin_off", playbook="spin_off", filing_type="Form 10")
    package = build_situation_historical_analogues(situation, [different, same])
    scores = {match.historical_case_id: match.similarity_score for match in package.historical_case_matches}
    assert scores[str(same.id)] > scores[str(different.id)]


def test_no_investment_action_language_or_raw_course_text():
    package = build_situation_historical_analogues(_situation(filing_type="SC TO-I", situation_type="tender_offer"))
    text = _all_text(package.model_dump()).lower()
    assert "buy" not in text
    assert "sell" not in text
    assert "hold" not in text
    assert "recommendation" not in text
    assert "transcript" not in text


def test_no_network_clients_imported():
    source = inspect.getsource(module)
    banned = ["requests", "httpx", "aiohttp", "urllib", "SECEdgarAdapter", "load_master_index"]
    assert not any(token in source for token in banned)
