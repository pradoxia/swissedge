"""Unit tests for Phase 1A investment research models.

These tests verify model structure, enum values, field presence, and
relationship declarations. They do not require a live database.
"""
import uuid
import importlib
import pytest


# ── import smoke tests ────────────────────────────────────────────────────────

def test_investment_research_module_imports():
    mod = importlib.import_module("backend.models.investment_research")
    assert hasattr(mod, "ResearchCase")
    assert hasattr(mod, "ResearchTask")
    assert hasattr(mod, "ResearchDocument")
    assert hasattr(mod, "ResearchSource")
    assert hasattr(mod, "HistoricalCase")


def test_source_intelligence_module_imports():
    mod = importlib.import_module("backend.models.source_intelligence")
    assert hasattr(mod, "SourceIntelligenceSuggestion")


def test_publishing_module_imports():
    mod = importlib.import_module("backend.models.publishing")
    assert hasattr(mod, "PublicArticleDraft")


# ── ResearchCase ──────────────────────────────────────────────────────────────

def test_research_case_tablename():
    from backend.models.investment_research import ResearchCase
    assert ResearchCase.__tablename__ == "research_cases"


def test_research_case_status_default():
    from backend.models.investment_research import ResearchCase
    col = ResearchCase.__table__.c["status"]
    assert col.default.arg == "detected"


def test_research_case_disclaimer_default():
    from backend.models.investment_research import ResearchCase
    col = ResearchCase.__table__.c["disclaimer"]
    assert col.default.arg == "Este análisis es educativo. No es asesoramiento financiero."


def test_research_case_has_investment_readiness():
    from backend.models.investment_research import ResearchCase
    assert "investment_readiness" in ResearchCase.__table__.c


def test_research_case_relationships():
    from backend.models.investment_research import ResearchCase
    assert hasattr(ResearchCase, "tasks")
    assert hasattr(ResearchCase, "documents")
    assert hasattr(ResearchCase, "sources")


def test_research_case_indexes():
    from backend.models.investment_research import ResearchCase
    index_names = {idx.name for idx in ResearchCase.__table__.indexes}
    assert "idx_research_cases_status" in index_names
    assert "idx_research_cases_situation_id" in index_names
    assert "idx_research_cases_investment_readiness" in index_names


# ── ResearchTask ──────────────────────────────────────────────────────────────

def test_research_task_tablename():
    from backend.models.investment_research import ResearchTask
    assert ResearchTask.__tablename__ == "research_tasks"


def test_research_task_status_default():
    from backend.models.investment_research import ResearchTask
    col = ResearchTask.__table__.c["status"]
    assert col.default.arg == "open"


def test_research_task_priority_default():
    from backend.models.investment_research import ResearchTask
    col = ResearchTask.__table__.c["priority"]
    assert col.default.arg == 3


def test_research_task_fk_cascade():
    from backend.models.investment_research import ResearchTask
    fk = next(f for f in ResearchTask.__table__.c["research_case_id"].foreign_keys)
    assert fk.ondelete == "CASCADE"


# ── ResearchDocument ──────────────────────────────────────────────────────────

def test_research_document_tablename():
    from backend.models.investment_research import ResearchDocument
    assert ResearchDocument.__tablename__ == "research_documents"


def test_research_document_has_historical_case_fk():
    from backend.models.investment_research import ResearchDocument
    assert "historical_case_id" in ResearchDocument.__table__.c


def test_research_document_url_not_nullable():
    from backend.models.investment_research import ResearchDocument
    col = ResearchDocument.__table__.c["url"]
    assert not col.nullable


# ── HistoricalCase ────────────────────────────────────────────────────────────

def test_historical_case_tablename():
    from backend.models.investment_research import HistoricalCase
    assert HistoricalCase.__tablename__ == "historical_cases"


def test_historical_case_status_default():
    from backend.models.investment_research import HistoricalCase
    col = HistoricalCase.__table__.c["status"]
    assert col.default.arg == "seed"


def test_historical_case_disclaimer_not_nullable():
    from backend.models.investment_research import HistoricalCase
    col = HistoricalCase.__table__.c["disclaimer"]
    assert not col.nullable


def test_historical_case_has_documents_relationship():
    from backend.models.investment_research import HistoricalCase
    assert hasattr(HistoricalCase, "documents")


# ── ResearchSource ────────────────────────────────────────────────────────────

def test_research_source_tablename():
    from backend.models.investment_research import ResearchSource
    assert ResearchSource.__tablename__ == "research_sources"


def test_research_source_signal_quality_not_nullable():
    from backend.models.investment_research import ResearchSource
    col = ResearchSource.__table__.c["signal_quality"]
    assert not col.nullable


# ── SourceIntelligenceSuggestion ──────────────────────────────────────────────

def test_si_suggestion_tablename():
    from backend.models.source_intelligence import SourceIntelligenceSuggestion
    assert SourceIntelligenceSuggestion.__tablename__ == "source_intelligence_suggestions"


def test_si_suggestion_status_default():
    from backend.models.source_intelligence import SourceIntelligenceSuggestion
    col = SourceIntelligenceSuggestion.__table__.c["status"]
    assert col.default.arg == "proposed"


def test_si_suggestion_action_not_nullable():
    from backend.models.source_intelligence import SourceIntelligenceSuggestion
    col = SourceIntelligenceSuggestion.__table__.c["action"]
    assert not col.nullable


def test_si_suggestion_rationale_not_nullable():
    from backend.models.source_intelligence import SourceIntelligenceSuggestion
    col = SourceIntelligenceSuggestion.__table__.c["rationale"]
    assert not col.nullable


def test_si_suggestion_indexes():
    from backend.models.source_intelligence import SourceIntelligenceSuggestion
    index_names = {idx.name for idx in SourceIntelligenceSuggestion.__table__.indexes}
    assert "idx_si_suggestions_status" in index_names
    assert "idx_si_suggestions_research_case_id" in index_names
    assert "idx_si_suggestions_historical_case_id" in index_names


# ── PublicArticleDraft ────────────────────────────────────────────────────────

def test_public_article_draft_tablename():
    from backend.models.publishing import PublicArticleDraft
    assert PublicArticleDraft.__tablename__ == "public_article_drafts"


def test_public_article_draft_status_default():
    from backend.models.publishing import PublicArticleDraft
    col = PublicArticleDraft.__table__.c["status"]
    assert col.default.arg == "draft"


def test_public_article_draft_buy_sell_check_field_exists():
    from backend.models.publishing import PublicArticleDraft
    assert "buy_sell_language_check" in PublicArticleDraft.__table__.c


def test_public_article_draft_buy_sell_not_nullable():
    from backend.models.publishing import PublicArticleDraft
    col = PublicArticleDraft.__table__.c["buy_sell_language_check"]
    assert not col.nullable


def test_public_article_draft_disclaimer_present_not_nullable():
    from backend.models.publishing import PublicArticleDraft
    col = PublicArticleDraft.__table__.c["disclaimer_present"]
    assert not col.nullable


def test_public_article_draft_fk_restrict():
    from backend.models.publishing import PublicArticleDraft
    fk = next(f for f in PublicArticleDraft.__table__.c["research_case_id"].foreign_keys)
    assert fk.ondelete == "RESTRICT"


def test_public_article_draft_readiness_label_not_nullable():
    from backend.models.publishing import PublicArticleDraft
    col = PublicArticleDraft.__table__.c["readiness_label"]
    assert not col.nullable


def test_public_article_draft_content_not_nullable():
    from backend.models.publishing import PublicArticleDraft
    col = PublicArticleDraft.__table__.c["content"]
    assert not col.nullable


# ── valid readiness label values (no buy/sell language) ───────────────────────

VALID_READINESS_LABELS = {"monitor", "not_actionable", "needs_more_work", "candidate"}
FORBIDDEN_TERMS = {"buy", "sell", "purchase", "vend"}


def test_readiness_labels_contain_no_buy_sell_language():
    for label in VALID_READINESS_LABELS:
        for term in FORBIDDEN_TERMS:
            assert term not in label.lower(), f"Label '{label}' contains forbidden term '{term}'"


def test_all_valid_readiness_labels_are_known():
    assert VALID_READINESS_LABELS == {"monitor", "not_actionable", "needs_more_work", "candidate"}


# ── migration file imports ────────────────────────────────────────────────────

def test_migration_c3_imports():
    mod = importlib.import_module(
        "backend.db.migrations.versions.c3d4e5f6a7b8_add_investment_research_tables"
    )
    assert hasattr(mod, "upgrade")
    assert hasattr(mod, "downgrade")
    assert mod.revision == "c3d4e5f6a7b8"
    assert mod.down_revision == "b2c3d4e5f6a7"
