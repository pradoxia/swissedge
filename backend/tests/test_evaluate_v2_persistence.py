import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from backend.api.investment.router import FilingInput


@pytest.fixture
def sample_filing():
    """Sample filing input for testing."""
    return {
        "company": "Test Corp",
        "ticker": "TEST",
        "filing_type": "SC TO-T",
        "date": "2026-04-29",
        "url": "https://sec.gov/test",
        "summary": "Test acquisition tender offer",
        "situation_type": "merger_arbitrage",
        "cik": "0001234567",
        "accession_number": "0001234567-26-000001"
    }


def test_filing_input_schema_has_save_to_db_field():
    """Test that FilingInput schema includes save_to_db field with correct default."""
    filing = FilingInput(
        company="Test",
        filing_type="8-K",
        date="2026-04-29",
        url="https://test.com",
        summary="Test"
    )
    assert hasattr(filing, 'save_to_db')
    assert filing.save_to_db is False


def test_filing_input_schema_accepts_save_to_db_true():
    """Test that FilingInput schema accepts save_to_db=true."""
    filing = FilingInput(
        company="Test",
        filing_type="8-K",
        date="2026-04-29",
        url="https://test.com",
        summary="Test",
        save_to_db=True
    )
    assert filing.save_to_db is True


def test_filing_input_schema_accepts_save_to_db_false():
    """Test that FilingInput schema accepts save_to_db=false."""
    filing = FilingInput(
        company="Test",
        filing_type="8-K",
        date="2026-04-29",
        url="https://test.com",
        summary="Test",
        save_to_db=False
    )
    assert filing.save_to_db is False
