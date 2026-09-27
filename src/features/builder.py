"""
Feature engineering module without look-ahead bias for ML model training and dataset generation.
"""
from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np


class FeatureEngine:
    """
    Engineers point-in-time features and historical target columns.
    Ensures zero look-ahead bias by computing targets strictly from future dates relative to date T.
    """

    @staticmethod
    def build_feature_set(
        stock_df: pd.DataFrame,
        market_df: Optional[pd.DataFrame] = None,
        sector_df: Optional[pd.DataFrame] = None
    ) -> pd.DataFrame:
        """
        Combines stock technicals with market and sector indicators.
        Adds future return targets for ML training (forward returns strictly shifted back).
        """
        if stock_df.empty:
            return pd.DataFrame()

        df = stock_df.copy().sort_values("Date").reset_index(drop=True)

        # Merge market indicators if provided
        if market_df is not None and not market_df.empty:
            m_cols = [c for c in market_df.columns if c not in ["Date"]]
            m_renamed = market_df[["Date"] + m_cols].rename(
                columns={c: f"market_{c}" for c in m_cols}
            )
            df = pd.merge(df, m_renamed, on="Date", how="left")

        # Merge sector indicators if provided
        if sector_df is not None and not sector_df.empty:
            s_cols = [c for c in sector_df.columns if c not in ["Date"]]
            s_renamed = sector_df[["Date"] + s_cols].rename(
                columns={c: f"sector_{c}" for c in s_cols}
            )
            df = pd.merge(df, s_renamed, on="Date", how="left")

        # Compute future return targets strictly without look-ahead leakage in feature columns:
        # Target for date T = (Close on T+N - Close on T) / Close on T
        # Shifting close by -N means date T row gets value of T+N
        close = df["Close"]
        df["future_return_1d"] = close.shift(-1) / close - 1.0
        df["future_return_3d"] = close.shift(-3) / close - 1.0
        df["future_return_5d"] = close.shift(-5) / close - 1.0
        df["future_return_10d"] = close.shift(-10) / close - 1.0
        df["future_return_20d"] = close.shift(-20) / close - 1.0

        return df
