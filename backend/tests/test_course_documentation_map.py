from backend.api.investment import router as investment_router
from backend.services.investment.course_documentation_map import (
    SUPPORTED_SITUATION_TYPES,
    get_course_checklist,
    get_course_documentation_map,
    get_required_documents,
    get_required_information,
    get_relevant_course_chapters,
)
from backend.services.investment.skill_registry import get_skill_registry


def test_all_supported_situation_types_return_course_documentation_map():
    for situation_type in SUPPORTED_SITUATION_TYPES:
        data = get_course_documentation_map(situation_type)

        assert data["situation_type"] == situation_type
        assert data["display_name"]
        assert data["relevant_course_chapters"]
        assert data["applicable_playbooks"]
        assert data["checklist_items"]
        assert data["required_documents"]
        assert data["required_information"]
        assert data["blocking_conditions"]


def test_unknown_falls_back_safely():
    data = get_course_documentation_map("not_a_real_type")

    assert data["situation_type"] == "unknown"
    assert data["applicable_playbooks"] == ["manual_triage"]


def test_accessor_functions_return_expected_sections():
    assert get_relevant_course_chapters("merger_arbitrage")
    assert get_required_documents("merger_arbitrage")
    assert get_required_information("merger_arbitrage")
    assert get_course_checklist("merger_arbitrage")


def test_critical_documents_exist_for_core_situation_types():
    expected = {
        "tender_offer": {"sc_to_i", "offer_to_purchase"},
        "merger_arbitrage": {"sc_to_t", "offer_to_purchase", "schedule_14d_9", "merger_agreement"},
        "spin_off": {"form_10", "information_statement", "pro_forma_financials"},
        "liquidation": {"8k_liquidation", "plan_of_liquidation", "estimated_distribution_documents"},
    }

    for situation_type, document_keys in expected.items():
        docs = get_required_documents(situation_type)
        critical = {item["document_key"] for item in docs if item["importance"] == "critical"}
        assert document_keys.issubset(critical)


def test_checklist_items_reference_valid_document_and_skill_keys():
    skill_keys = {skill["skill_key"] for skill in get_skill_registry()["skills"]}
    for situation_type in SUPPORTED_SITUATION_TYPES:
        data = get_course_documentation_map(situation_type)
        document_keys = {item["document_key"] for item in data["required_documents"]}

        for item in data["checklist_items"]:
            assert set(item["required_document_keys"]).issubset(document_keys)
            assert set(item["required_skill_keys"]).issubset(skill_keys)

        for item in data["required_information"]:
            assert set(item["source_document_keys"]).issubset(document_keys)
            assert set(item["required_skill_keys"]).issubset(skill_keys)


def test_course_documentation_map_api_is_read_only_shape():
    data = investment_router.get_course_documentation_map_endpoint("spin_off")

    assert data["situation_type"] == "spin_off"
    assert data["required_documents"]
    assert "post" not in investment_router.get_course_documentation_map_endpoint.__name__
