import uuid
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient

from backend.main import app
from backend.models.sales import SalesItem, SalesItemPhoto, SalesPlatformListing, SalesItemStatus, Platform

client = TestClient(app)

_FULL_PAYLOAD = {
    "title": "Bosch Staubsauger",
    "brand_model": "Bosch BSG6",
    "category": "Haushaltsgeräte",
    "condition": "very_good",
    "description": "Wenig benutzt, voll funktionsfähig.",
    "target_price_chf": "35.00",
    "pickup_location": "Zürich",
    "shipping_policy": "no_shipping",
    "created_from": "test",
}

_MINIMAL_PAYLOAD = {
    "brand_model": "Nike Shirt",
    "condition": "good",
}


def _make_item(overrides=None):
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)
    data = {
        "id": uuid.uuid4(),
        "title": "Test Item",
        "brand_model": "Test Brand",
        "category": "Test Cat",
        "condition": "good",
        "description": None,
        "internal_notes": None,
        "target_price_chf": None,
        "pickup_location": None,
        "shipping_policy": None,
        "status": SalesItemStatus.NEEDS_INFO,
        "needs_action_reason": None,
        "created_from": "test",
        "telegram_chat_id": None,
        "telegram_message_id": None,
        "created_at": now,
        "updated_at": now,
        "photos": [],
        "platform_listings": [],
    }
    if overrides:
        data.update(overrides)
    item = MagicMock(spec=SalesItem)
    for k, v in data.items():
        setattr(item, k, v)
    return item


def _make_db_mock(item):
    db = AsyncMock()
    scalar_result = MagicMock()
    scalar_result.scalar_one_or_none.return_value = item
    scalar_result.scalars.return_value.all.return_value = [item]
    db.execute = AsyncMock(return_value=scalar_result)
    db.flush = AsyncMock()
    db.commit = AsyncMock()
    db.add = MagicMock()
    return db


def test_create_sales_item_full_payload_status_draft_ready():
    from decimal import Decimal
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)
    item_id = uuid.uuid4()
    listings = [
        MagicMock(spec=SalesPlatformListing, **{
            "id": uuid.uuid4(), "item_id": item_id, "platform": p,
            "status": "not_listed", "title": None, "description": None,
            "category_suggestion": None, "price_chf": None, "publish_url": None,
            "published_at": None, "sold_at": None, "archived_at": None,
            "created_at": now, "updated_at": now,
        })
        for p in [Platform.RICARDO, Platform.TUTTI, Platform.ANIBIS, Platform.FACEBOOK_MARKETPLACE_CH]
    ]
    item = MagicMock(spec=SalesItem)
    item.id = item_id
    item.title = "Bosch Staubsauger"
    item.brand_model = "Bosch BSG6"
    item.category = "Haushaltsgeräte"
    item.condition = "very_good"
    item.description = "Wenig benutzt, voll funktionsfähig."
    item.internal_notes = None
    item.target_price_chf = Decimal("35.00")
    item.pickup_location = "Zürich"
    item.shipping_policy = "no_shipping"
    item.status = SalesItemStatus.DRAFT_READY
    item.needs_action_reason = None
    item.created_from = "test"
    item.telegram_chat_id = None
    item.telegram_message_id = None
    item.created_at = now
    item.updated_at = now
    item.photos = []
    item.platform_listings = listings

    db = _make_db_mock(item)

    with patch("backend.api.marketplace.sales_items.get_db", return_value=db):
        async def _override():
            return db
        app.dependency_overrides[__import__("backend.db.database", fromlist=["get_db"]).get_db] = _override
        try:
            response = client.post("/api/marketplace/sales/items", json=_FULL_PAYLOAD)
        finally:
            app.dependency_overrides.clear()

    assert response.status_code == 201
    data = response.json()
    assert data["status"] == SalesItemStatus.DRAFT_READY
    assert len(data["platform_listings"]) == 4
    platforms = {pl["platform"] for pl in data["platform_listings"]}
    assert platforms == {Platform.RICARDO, Platform.TUTTI, Platform.ANIBIS, Platform.FACEBOOK_MARKETPLACE_CH}


def test_create_sales_item_minimal_payload_status_needs_info():
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)
    item_id = uuid.uuid4()
    listings = [
        MagicMock(spec=SalesPlatformListing, **{
            "id": uuid.uuid4(), "item_id": item_id, "platform": p,
            "status": "not_listed", "title": None, "description": None,
            "category_suggestion": None, "price_chf": None, "publish_url": None,
            "published_at": None, "sold_at": None, "archived_at": None,
            "created_at": now, "updated_at": now,
        })
        for p in [Platform.RICARDO, Platform.TUTTI, Platform.ANIBIS, Platform.FACEBOOK_MARKETPLACE_CH]
    ]
    item = MagicMock(spec=SalesItem)
    item.id = item_id
    item.title = None
    item.brand_model = "Nike Shirt"
    item.category = None
    item.condition = "good"
    item.description = None
    item.internal_notes = None
    item.target_price_chf = None
    item.pickup_location = None
    item.shipping_policy = None
    item.status = SalesItemStatus.NEEDS_INFO
    item.needs_action_reason = None
    item.created_from = None
    item.telegram_chat_id = None
    item.telegram_message_id = None
    item.created_at = now
    item.updated_at = now
    item.photos = []
    item.platform_listings = listings

    db = _make_db_mock(item)

    with patch("backend.api.marketplace.sales_items.get_db", return_value=db):
        async def _override():
            return db
        app.dependency_overrides[__import__("backend.db.database", fromlist=["get_db"]).get_db] = _override
        try:
            response = client.post("/api/marketplace/sales/items", json=_MINIMAL_PAYLOAD)
        finally:
            app.dependency_overrides.clear()

    assert response.status_code == 201
    data = response.json()
    assert data["status"] == SalesItemStatus.NEEDS_INFO


def test_list_sales_items_returns_list():
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)
    item = _make_item()

    db = _make_db_mock(item)

    with patch("backend.api.marketplace.sales_items.get_db", return_value=db):
        async def _override():
            return db
        app.dependency_overrides[__import__("backend.db.database", fromlist=["get_db"]).get_db] = _override
        try:
            response = client.get("/api/marketplace/sales/items")
        finally:
            app.dependency_overrides.clear()

    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_sales_item_not_found():
    db = AsyncMock()
    scalar_result = MagicMock()
    scalar_result.scalar_one_or_none.return_value = None
    db.execute = AsyncMock(return_value=scalar_result)

    with patch("backend.api.marketplace.sales_items.get_db", return_value=db):
        async def _override():
            return db
        app.dependency_overrides[__import__("backend.db.database", fromlist=["get_db"]).get_db] = _override
        try:
            response = client.get(f"/api/marketplace/sales/items/{uuid.uuid4()}")
        finally:
            app.dependency_overrides.clear()

    assert response.status_code == 404


def test_patch_invalid_status_transition():
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)
    item_id = uuid.uuid4()
    item = MagicMock(spec=SalesItem)
    item.id = item_id
    item.title = "Test"
    item.brand_model = None
    item.category = None
    item.condition = "good"
    item.description = None
    item.internal_notes = None
    item.target_price_chf = None
    item.pickup_location = None
    item.shipping_policy = None
    item.status = SalesItemStatus.NEEDS_INFO
    item.needs_action_reason = None
    item.created_from = None
    item.telegram_chat_id = None
    item.telegram_message_id = None
    item.created_at = now
    item.updated_at = now
    item.photos = []
    item.platform_listings = []

    db = _make_db_mock(item)

    with patch("backend.api.marketplace.sales_items.get_db", return_value=db):
        async def _override():
            return db
        app.dependency_overrides[__import__("backend.db.database", fromlist=["get_db"]).get_db] = _override
        try:
            response = client.patch(
                f"/api/marketplace/sales/items/{item_id}",
                json={"status": SalesItemStatus.PUBLISHED},
            )
        finally:
            app.dependency_overrides.clear()

    assert response.status_code == 422


def test_derive_status_logic():
    from backend.api.marketplace.sales_items import _derive_status
    from decimal import Decimal

    assert _derive_status({"title": "X", "condition": "good", "target_price_chf": Decimal("10"), "pickup_location": "ZH"}) == SalesItemStatus.DRAFT_READY
    assert _derive_status({"title": None, "condition": "good", "target_price_chf": Decimal("10"), "pickup_location": "ZH"}) == SalesItemStatus.NEEDS_INFO
    assert _derive_status({}) == SalesItemStatus.NEEDS_INFO
