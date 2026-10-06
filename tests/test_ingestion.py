import pytest
import pandas as pd
from unittest.mock import MagicMock, patch
from src.ingestion.provider import YFinanceProvider

def test_yfinance_provider_historical_prices_mock():
    provider = YFinanceProvider(max_retries=1, retry_backoff=0.1)

    mock_df = pd.DataFrame({
        'Date': [pd.Timestamp('2025-01-01'), pd.Timestamp('2025-01-02')],
        'Open': [100.0, 102.0],
        'High': [105.0, 106.0],
        'Low': [99.0, 101.0],
        'Close': [103.0, 105.0],
        'Adj Close': [103.0, 105.0],
        'Volume': [10000, 12000]
    }).set_index('Date')

    with patch('yfinance.Ticker') as mock_ticker:
        mock_instance = MagicMock()
        mock_instance.history.return_value = mock_df
        mock_ticker.return_value = mock_instance

        result = provider.get_historical_prices('RELIANCE.NS', '2025-01-01', '2025-01-03')

        assert not result.empty
        assert 'close' in result.columns
        assert len(result) == 2
        assert result['close'].iloc[0] == 103.0

def test_yfinance_provider_empty():
    provider = YFinanceProvider(max_retries=1, retry_backoff=0.1)
    with patch('yfinance.Ticker') as mock_ticker:
        mock_instance = MagicMock()
        mock_instance.history.return_value = pd.DataFrame()
        mock_ticker.return_value = mock_instance

        result = provider.get_historical_prices('INVALID', '2025-01-01', '2025-01-03')
        assert result.empty
