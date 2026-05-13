import inspect
import json

from backend.services.investment.evidence_links import (
    build_research_case_evidence_links,
    build_situation_evidence_links,
)
from backend.services.investment.official_source_finder import (
    build_research_case_official_source_finder,
    build_situation_official_source_finder,
)
from backend.tests.test_case_documentation import SEC_URL, _research_case, _situation


def test_sec_metadata_produces_source_context():
    situation = _situation()
    package = build_situation_official_source_finder(
        situation,
        build_situation_evidence_links(situation),
    )

    assert package.case_type == "special_situation"
    assert package.source_context.company_name == "Forian Inc."
    assert package.source_context.cik == "0001829280"
    assert package.source_context.accession_number == "0001140361-26-019536"
    assert package.source_context.filing_type == "SC TO-T"


def test_stored_filing_url_is_metadata_only_official_link():
    situation = _situation()
    package = build_situation_official_source_finder(
        situation,
        build_situation_evidence_links(situation),
    )

    stored = [link for link in package.official_links if link.link_type == "stored_sec_filing"]
    assert stored
    assert stored[0].url == SEC_URL
    assert stored[0].metadata_only is True
    assert stored[0].verified is False


def test_missing_resources_produce_document_targets_and_queries():
    situation = _situation()
    package = build_situation_official_source_finder(
        situation,
        build_situation_evidence_links(situation),
    )

    assert any(target.required_resource_id == "offer_document" for target in package.missing_document_targets)
    assert any("Offer document" in query.query for query in package.copyable_queries)
    assert all(query.not_executed_by_swissedge is True for query in package.copyable_queries)


def test_search_suggestions_become_copyable_manual_queries():
    situation = _situation()
    package = build_situation_official_source_finder(
        situation,
        build_situation_evidence_links(situation),
    )

    assert any(query.query == "\"Forian Inc.\" offer document" for query in package.copyable_queries)
    assert any("Google" in query.where_to_use for query in package.copyable_queries)


def test_no_url_invented_from_cik_or_accession_without_stored_filing_url():
    situation = _situation(filing_url=None)
    package = build_situation_official_source_finder(
        situation,
        build_situation_evidence_links(situation),
    )

    assert package.source_context.cik == "0001829280"
    assert package.source_context.accession_number == "0001140361-26-019536"
    assert package.source_context.stored_filing_url is None
    assert all(link.link_type != "stored_sec_filing" for link in package.official_links)
    assert any("CIK metadata search" in query.purpose for query in package.copyable_queries)


def test_candidate_and_evidence_found_are_not_treated_as_verified():
    situation = _situation()
    package = build_situation_official_source_finder(
        situation,
        build_situation_evidence_links(situation),
    )

    assert package.coverage.candidate_sources_count == 1
    assert package.coverage.evidence_found_count >= 1
    assert all(link.verified is False for link in package.official_links)
    text = json.dumps(package.model_dump()).lower()
    assert "not verified" in text or "requires human verification" in text


def test_research_case_package_connects_original_context():
    situation = _situation()
    rc = _research_case(situation)
    package = build_research_case_official_source_finder(
        rc,
        evidence_links=build_research_case_evidence_links(rc),
        source_situation=situation,
    )

    assert package.case_type == "research_case"
    assert package.source_context.company_name == "Forian Inc."
    assert package.source_context.stored_filing_url == SEC_URL
    assert any(link.url == SEC_URL for link in package.official_links)


def test_official_source_finder_has_no_buy_sell_hold_or_recommendation_language():
    situation = _situation()
    package = build_situation_official_source_finder(
        situation,
        build_situation_evidence_links(situation),
    )
    text = json.dumps(package.model_dump()).lower()

    assert "buy" not in text
    assert "sell" not in text
    assert "hold" not in text
    assert "recommendation" not in text


def test_official_source_finder_service_does_not_import_network_clients():
    import backend.services.investment.official_source_finder as official_source_finder

    source = inspect.getsource(official_source_finder)

    assert "httpx" not in source
    assert "requests" not in source
    assert "urllib.request" not in source
