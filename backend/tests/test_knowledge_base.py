import pytest
from fastapi import HTTPException

from backend.api.investment import router as situation_api
from backend.services.investment.knowledge_base import (
    get_knowledge_entry,
    list_knowledge_entries,
    resolve_knowledge_key_for_document,
    resolve_knowledge_key_for_field,
    resolve_knowledge_key_for_playbook,
)


def test_initial_tender_offer_entries_exist():
    assert get_knowledge_entry("offer_to_purchase") is not None
    assert get_knowledge_entry("letter_of_transmittal") is not None
    assert get_knowledge_entry("proration") is not None
    assert get_knowledge_entry("issuer_tender_offer") is not None


def test_knowledge_resolvers_map_document_field_and_playbook_keys():
    assert resolve_knowledge_key_for_document("offer_to_purchase") == "offer_to_purchase"
    assert resolve_knowledge_key_for_field("proration_terms") == "proration"
    assert resolve_knowledge_key_for_field("proration") == "proration"
    assert resolve_knowledge_key_for_playbook("tender_offer") == "issuer_tender_offer"


def test_list_knowledge_entries_filters_by_type_and_situation_type():
    docs = list_knowledge_entries(type="document", situation_type="tender_offer")
    keys = {entry.knowledge_key for entry in docs}
    assert "offer_to_purchase" in keys
    assert all(entry.type == "document" for entry in docs)


@pytest.mark.asyncio
async def test_knowledge_api_is_read_only_and_returns_entry():
    entry = await situation_api.get_investment_knowledge_entry("offer_to_purchase")
    rows = await situation_api.get_knowledge_entries(type="playbook", situation_type="tender_offer")

    assert entry.knowledge_key == "offer_to_purchase"
    assert entry.guardrail
    assert any(row.knowledge_key == "issuer_tender_offer" for row in rows)


@pytest.mark.asyncio
async def test_unknown_knowledge_key_raises_404():
    with pytest.raises(HTTPException) as exc:
        await situation_api.get_investment_knowledge_entry("not_a_key")
    assert exc.value.status_code == 404
