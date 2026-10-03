import logging
from typing import Dict, Any, List
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

class FeatureBuilder:
    """Builds historical feature set and targets strictly avoiding look-ahead bias."""

    @staticmethod
    def build_features(df: pd.DataFrame, ticker: str = "", horizons: List[int] = [1, 3, 5, 10, 20]) -> pd.DataFrame:
        """
        Calculates features available at time T and creates forward target columns (future_return_Nd).
        Features for date T rely solely on data available up to date T.
        Targets for date T look forward to T+N.
        """
        if df.empty or len(df) < 5:
            return pd.DataFrame()

        df = df.copy()
        if "ticker" not in df.columns:
            df["ticker"] = ticker

        # Ensure sorted
        df = df.sort_values("date").reset_index(drop=True)

        feature_cols = [
            "open", "high", "low", "close", "volume",
            "return_1d", "return_5d", "return_20d",
            "rsi_14", "stoch_rsi", "macd", "macd_signal", "macd_histogram",
            "atr_14", "volatility_20d",
            "sma_5", "sma_20", "sma_50", "sma_200",
            "ema_9", "ema_20", "ema_50", "ema_200",
            "relative_volume", "dist_52w_high", "dist_52w_low",
            "gap_pct", "intraday_range"
        ]

        existing_feature_cols = [c for c in feature_cols if c in df.columns]
        out_df = df[["date", "ticker"] + existing_feature_cols].copy()

        # Generate future targets (Future return over N days)
        # Note: Targets are explicitly separated from input features during ML training.
        for h in horizons:
            out_df[f"future_return_{h}d"] = (df["close"].shift(-h) - df["close"]) / df["close"]
            out_df[f"target_direction_{h}d"] = (out_df[f"future_return_{h}d"] > 0).astype(int)

        return out_df
