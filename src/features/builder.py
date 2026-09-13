import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional

class FeatureBuilder:
    """
    Builds ML-ready tabular feature matrix for stock dataset while preventing look-ahead bias (leakage).

    Leakage Prevention Guarantee:
    - Features for date T only use data available on or before date T.
    - Future target variables (e.g. future_return_1d, future_return_5d) are generated explicitly
      by shifting prices backwards (i.e., close[T + k] / close[T] - 1) and marked clearly as target labels.
    """

    @staticmethod
    def build_features(
        stock_df: pd.DataFrame,
        ticker: str,
        nifty_df: Optional[pd.DataFrame] = None,
        sector_df: Optional[pd.DataFrame] = None,
        include_targets: bool = True
    ) -> pd.DataFrame:
        if stock_df.empty:
            return pd.DataFrame()

        df = stock_df.sort_values('date').copy()
        df['ticker'] = ticker

        # Align NIFTY market returns
        if nifty_df is not None and not nifty_df.empty:
            nifty_sub = nifty_df[['date', 'return_1d', 'volatility_20d']].rename(
                columns={'return_1d': 'market_return_1d', 'volatility_20d': 'market_volatility'}
            )
            df = pd.merge(df, nifty_sub, on='date', how='left')
        else:
            df['market_return_1d'] = 0.0
            df['market_volatility'] = 0.0

        # Align Sector returns
        if sector_df is not None and not sector_df.empty:
            sec_sub = sector_df[['date', 'return_1d']].rename(columns={'return_1d': 'sector_return_1d'})
            df = pd.merge(df, sec_sub, on='date', how='left')
        else:
            df['sector_return_1d'] = 0.0

        # Features list definition
        feature_cols = [
            'date', 'ticker', 'open', 'high', 'low', 'close', 'volume',
            'return_1d', 'gap_pct', 'intraday_range_pct',
            'dist_52w_high', 'dist_52w_low',
            'sma_20', 'sma_50', 'sma_200', 'ema_20', 'ema_50',
            'dist_sma_20', 'dist_sma_50', 'dist_sma_200',
            'rsi_14', 'stoch_rsi', 'macd', 'macd_signal', 'macd_hist',
            'atr_14', 'volatility_20d', 'bollinger_width',
            'relative_volume', 'market_return_1d', 'market_volatility', 'sector_return_1d'
        ]

        existing_feature_cols = [c for c in feature_cols if c in df.columns]
        feature_matrix = df[existing_feature_cols].copy()

        # Multi-day historical return features (Point-in-time on date T)
        feature_matrix['return_5d'] = df['close'].pct_change(5)
        feature_matrix['return_20d'] = df['close'].pct_change(20)

        # Generate future targets (ONLY for training datasets, explicitly labeled as future)
        if include_targets:
            for k in [1, 3, 5, 10, 20]:
                # shift(-k) gets price at T + k without leaking into features of date T
                feature_matrix[f'target_future_return_{k}d'] = (df['close'].shift(-k) - df['close']) / df['close']
                feature_matrix[f'target_direction_{k}d'] = (feature_matrix[f'target_future_return_{k}d'] > 0).astype(int)

        return feature_matrix
