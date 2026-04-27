from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class Filing:
    company: str
    ticker: str | None
    filing_type: str
    date: str
    url: str
    summary: str
    situation_type: str | None = None
    cik: str | None = None
    accession_number: str | None = None
    extra: dict = field(default_factory=dict)


class InvestmentSource(ABC):
    @abstractmethod
    async def search_recent(self, hours_back: int = 6) -> list[Filing]:
        """Search for recent filings/news."""

    @abstractmethod
    async def search_by_type(self, situation_type: str) -> list[Filing]:
        """Search for specific situation types."""

    async def health_check(self) -> dict:
        try:
            results = await self.search_recent(hours_back=24)
            return {"status": "ok", "message": f"Returned {len(results)} filings"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
