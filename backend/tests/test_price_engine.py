import pytest
from backend.services.marketplace.adapters.base import Listing
from backend.services.marketplace.price_engine import calculate_price_comparison, price_vs_market


def _make_listing(price: float) -> Listing:
    return Listing(title="Test", price=price, currency="CHF", url="https://tutti.ch", marketplace="tutti.ch")


def test_calculate_price_comparison_basic():
    listings = [_make_listing(p) for p in [100, 200, 300, 400, 500]]
    result = calculate_price_comparison(listings)
    assert result.average == 300.0
    assert result.median == 300.0
    assert result.min_price == 100.0
    assert result.max_price == 500.0
    assert result.count == 5


def test_calculate_price_comparison_empty():
    result = calculate_price_comparison([])
    assert result.count == 0
    assert result.average == 0


def test_price_vs_market_great_deal():
    listings = [_make_listing(400) for _ in range(5)]
    comparison = calculate_price_comparison(listings)
    result = price_vs_market(200, comparison)
    assert result["pct_vs_avg"] == -50.0
    assert result["label"] == "great deal"


def test_price_vs_market_fair():
    listings = [_make_listing(400) for _ in range(5)]
    comparison = calculate_price_comparison(listings)
    result = price_vs_market(400, comparison)
    assert result["pct_vs_avg"] == 0.0
    assert result["label"] == "fair price"


def test_price_vs_market_expensive():
    listings = [_make_listing(200) for _ in range(5)]
    comparison = calculate_price_comparison(listings)
    result = price_vs_market(350, comparison)
    assert result["label"] == "expensive"
