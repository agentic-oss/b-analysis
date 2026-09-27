"""
Data ingestion module for market data providers.
"""
from src.ingestion.provider import MarketDataProvider, YFinanceProvider

__all__ = ["MarketDataProvider", "YFinanceProvider"]
