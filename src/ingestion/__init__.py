"""Market Data Ingestion Module."""
from .provider import MarketDataProvider, YFinanceProvider

__all__ = ["MarketDataProvider", "YFinanceProvider"]
