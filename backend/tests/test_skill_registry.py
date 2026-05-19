from backend.api.investment import router as investment_router
from backend.services.investment.course_documentation_map import SUPPORTED_SITUATION_TYPES
from backend.services.investment.skill_registry import (
    get_missing_skills_for_situation_type,
    get_skill_registry,
    get_skill_requirements_map,
    get_skills_for_situation_type,
)


def test_skill_registry_has_groups_and_required_shape():
    registry = get_skill_registry()

    assert "Course Intelligence" in registry["groups"]
    assert "SEC Evidence" in registry["groups"]
    assert registry["skills"]
    for skill in registry["skills"]:
        assert skill["skill_key"]
        assert skill["label"]
        assert skill["group"] in registry["groups"]
        assert isinstance(skill["implemented"], bool)
        assert isinstance(skill["required_for_situation_types"], list)
        assert isinstance(skill["outputs"], list)
        assert isinstance(skill["dependencies"], list)


def test_skills_for_each_supported_situation_type():
    for situation_type in SUPPORTED_SITUATION_TYPES:
        skills = get_skills_for_situation_type(situation_type)

        assert skills
        assert any(skill["skill_key"] == "course_chapter_mapper" for skill in skills)
        assert any(skill["skill_key"] == "guardrail_checker" for skill in skills)


def test_skill_requirements_map_returns_implemented_and_missing_skills():
    data = get_skill_requirements_map("merger_arbitrage")

    assert data["situation_type"] == "merger_arbitrage"
    assert data["required_skills"]
    assert data["implemented_skills"]
    assert data["missing_skills"]
    assert data["summary"]["required_count"] == len(data["required_skills"])
    assert data["summary"]["implemented_count"] == len(data["implemented_skills"])
    assert data["summary"]["missing_count"] == len(data["missing_skills"])
    assert any(skill["skill_key"] == "schedule_14d9_finder" for skill in data["missing_skills"])


def test_unknown_skill_requirements_fall_back_safely():
    data = get_skill_requirements_map("nope")

    assert data["situation_type"] == "unknown"
    assert data["required_skills"]


def test_missing_skills_helper_returns_only_unimplemented():
    missing = get_missing_skills_for_situation_type("spin_off")

    assert missing
    assert all(skill["implemented"] is False for skill in missing)
    assert any(skill["skill_key"] == "form_10_analyzer" for skill in missing)


def test_skill_requirements_api_is_read_only_shape():
    data = investment_router.get_skill_requirements_endpoint("tender_offer")

    assert data["situation_type"] == "tender_offer"
    assert data["required_skills"]
    assert "post" not in investment_router.get_skill_requirements_endpoint.__name__
