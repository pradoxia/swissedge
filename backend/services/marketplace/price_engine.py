import statistics
from backend.services.marketplace.adapters.base import Listing, PriceComparison


def calculate_price_comparison(listings: list[Listing], currency: str = "CHF") -> PriceComparison:
    """Aggregate listings into a price comparison summary."""
    prices = [l.price for l in listings if l.price > 0]

    if not prices:
        return PriceComparison(
            average=0, median=0, min_price=0, max_price=0,
            count=0, currency=currency, listings=listings,
        )

    return PriceComparison(
        average=round(statistics.mean(prices), 2),
        median=round(statistics.median(prices), 2),
        min_price=round(min(prices), 2),
        max_price=round(max(prices), 2),
        count=len(prices),
        currency=currency,
        listings=listings,
    )


def price_vs_market(price: float, comparison: PriceComparison) -> dict:
    """Return how a given price compares to the market."""
    if comparison.average == 0:
        return {"pct_vs_avg": None, "label": "no data"}

    pct = round((price - comparison.average) / comparison.average * 100, 1)
    if pct <= -15:
        label = "great deal"
    elif pct <= -5:
        label = "below average"
    elif pct <= 5:
        label = "fair price"
    elif pct <= 15:
        label = "above average"
    else:
        label = "expensive"

    return {"pct_vs_avg": pct, "label": label}
