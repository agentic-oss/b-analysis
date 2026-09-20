"""Mock Market Data Provider for deterministic offline testing and pipeline verification."""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from src.ingestion.provider import MarketDataProvider

class MockMarketDataProvider(MarketDataProvider):
    """Generates synthetic stock market data for testing."""

    def __init__(self, seed: int = 42):
        self.seed = seed

    def _generate_synthetic_df(self, symbol: str, start_date: str, end_date: str, is_index: bool = False) -> pd.DataFrame:
        dates = pd.date_range(start=start_date, end=end_date, freq='B') # Business days
        if len(dates) == 0:
            return pd.DataFrame(columns=['date', 'open', 'high', 'low', 'close', 'adj_close', 'volume', 'ticker'])

        np.random.seed(abs(hash(symbol) + self.seed) % (2**32 - 1))

        base_price = 100.0 if not is_index else 22000.0
        n = len(dates)

        # Random walk
        returns = np.random.normal(0.0005, 0.015, size=n)
        price_series = base_price * np.exp(np.cumsum(returns))

        daily_volatility = np.random.uniform(0.01, 0.025, size=n)
        highs = price_series * (1 + daily_volatility)
        lows = price_series * (1 - daily_volatility)
        opens = price_series * (1 + np.random.uniform(-0.005, 0.005, size=n))
        closes = price_series

        # Fix high/low relative to open/close
        highs = np.maximum(highs, np.maximum(opens, closes))
        lows = np.minimum(lows, np.minimum(opens, closes))

        volumes = np.random.randint(100000, 5000000, size=n) if not is_index else np.random.randint(5000000, 50000000, size=n)

        df = pd.DataFrame({
            'date': dates.strftime('%Y-%m-%d'),
            'open': np.round(opens, 2),
            'high': np.round(highs, 2),
            'low': np.round(lows, 2),
            'close': np.round(closes, 2),
            'adj_close': np.round(closes, 2),
            'volume': volumes,
            'ticker': symbol,
            'provider': 'mock'
        })
        return df

    def get_historical_prices(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        return self._generate_synthetic_df(symbol, start_date, end_date, is_index=symbol.startswith('^'))

    def get_latest_prices(self, symbols: list) -> pd.DataFrame:
        today = datetime.now().strftime('%Y-%m-%d')
        dfs = [self._generate_synthetic_df(sym, today, today) for sym in symbols]
        return pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()

    def get_volume_data(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        df = self.get_historical_prices(symbol, start_date, end_date)
        if not df.empty:
            df['deliverable_volume'] = (df['volume'] * np.random.uniform(0.3, 0.7, size=len(df))).astype(int)
            df['delivery_percentage'] = np.round((df['deliverable_volume'] / df['volume']) * 100, 2)
        return df

    def get_corporate_actions(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        return pd.DataFrame(columns=['date', 'action_type', 'value', 'ticker'])

    def get_index_data(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        return self._generate_synthetic_df(symbol, start_date, end_date, is_index=True)
