"""
Factory function to instantiate the configured market data provider.
"""

from typing import Any, Dict, Optional
from src.ingestion.provider import MarketDataProvider
from src.ingestion.yfinance_provider import YFinanceProvider


def get_market_data_provider(
    provider_name: str = "yfinance",
    config: Optional[Dict[str, Any]] = None,
) -> MarketDataProvider:
    """
    Returns an instance of MarketDataProvider based on provider_name.
    """
    provider_name = provider_name.lower()
    if provider_name == "yfinance":
        return YFinanceProvider()
    else:
        raise ValueError(f"Unsupported market data provider: {provider_name}")
