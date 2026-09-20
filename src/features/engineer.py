"""Feature Engineering for ML models with strict leak prevention."""

import pandas as pd
import numpy as np
from typing import Dict, Any, List

class FeatureEngineer:
    """Generates tabular feature datasets for stock market prediction while strictly preventing look-ahead bias."""

    @staticmethod
    def build_features_and_targets(df: pd.DataFrame, horizons: List[int] = [1, 3, 5, 10, 20]) -> pd.DataFrame:
        """Computes point-in-time features on date T and forward return targets using data strictly AFTER date T.

        Features for row T use strictly historical observations up to row T.
        Target `future_return_Kd` for row T is `(close[T+K] - close[T]) / close[T]`.
        """
        if df.empty or len(df) < 20:
            return df

        res = df.copy()
        close = res['close']

        # Historical returns up to date T
        res['return_1d'] = close.pct_change(1)
        res['return_5d'] = close.pct_change(5)
        res['return_20d'] = close.pct_change(20)

        # Ensure indicator features exist or compute them
        if 'rsi_14' not in res.columns:
            delta = close.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14, min_periods=1).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14, min_periods=1).mean()
            rs = gain / loss.replace(0, np.nan)
            res['rsi_14'] = (100 - (100 / (1 + rs))).fillna(50)

        # Future Return Targets (For training models only, shifted strictly forward)
        for h in horizons:
            res[f'future_return_{h}d'] = (close.shift(-h) - close) / close
            res[f'future_direction_{h}d'] = np.where(res[f'future_return_{h}d'] > 0, 1, 0)

        return res
