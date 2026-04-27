from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class Listing:
    title: str
    price: float
    currency: str
    url: str
    marketplace: str
    condition: str | None = None
    image_urls: list[str] = field(default_factory=list)


@dataclass
class PriceComparison:
    average: float
    median: float
    min_price: float
    max_price: float
    count: int
    currency: str
    listings: list[Listing] = field(default_factory=list)


class MarketplaceAdapter(ABC):
    @abstractmethod
    async def search(self, query: str, **filters) -> list[Listing]:
        """Search for listings matching query."""

    @abstractmethod
    async def get_price(self, query: str) -> PriceComparison:
        """Get price comparison for an item."""

    @abstractmethod
    async def create_listing(self, item: dict) -> dict:
        """Create a listing draft or publish."""

    @abstractmethod
    async def get_listing_status(self, listing_id: str) -> str:
        """Check listing status."""

    async def health_check(self) -> dict:
        """Return health status of this adapter."""
        try:
            results = await self.search("test", limit=1)
            return {"status": "ok", "message": f"Search returned {len(results)} results"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
