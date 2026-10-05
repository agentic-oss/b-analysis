"""
Feature Builder for Historical Dataset and Machine Learning Training.
Guarantees NO look-ahead bias: features for date T rely solely on information up to date T.
"""

from typing import Dict, List, Optional
import pandas as pd
import numpy as np


class FeatureBuilder:
    """Builds tabular feature set for machine learning models without look-ahead bias."""

    @staticmethod
    def build_feature_set(
        stock_df: pd.DataFrame,
        ticker: str,
        sector_df: Optional[pd.DataFrame] = None,
        nifty_df: Optional[pd.DataFrame] = None,
        regime_info: Optional[Dict] = None
    ) -> pd.DataFrame:
        """
        Engineers ML features for every trading day.
        Includes backward features and future targets (for ML training).
        """
        if stock_df.empty or len(stock_df) < 20:
            return pd.DataFrame()

        df = stock_df.copy().sort_values("date").reset_index(drop=True)
        df["ticker"] = ticker

        # Benchmark/Sector returns aligned strictly by date
        if nifty_df is not None and not nifty_df.empty and "return_1d" in nifty_df.columns:
            nifty_map = nifty_df.set_index("date")["return_1d"].to_dict()
            df["market_return_1d"] = df["date"].map(nifty_map).fillna(0)
        else:
            df["market_return_1d"] = 0.0

        if sector_df is not None and not sector_df.empty and "return_1d" in sector_df.columns:
            sector_map = sector_df.set_index("date")["return_1d"].to_dict()
            df["sector_return_1d"] = df["date"].map(sector_map).fillna(0)
        else:
            df["sector_return_1d"] = 0.0

        # Feature set (all historical / backward-looking)
        feature_cols = [
            "ticker", "date", "open", "high", "low", "close", "volume",
            "return_1d", "return_5d", "return_20d", "rsi_14", "stoch_rsi",
            "macd", "macd_signal", "macd_hist", "atr_14", "volatility_20d",
            "sma_20", "sma_50", "sma_200", "ema_20", "ema_50", "relative_volume",
            "dist_sma_20", "dist_sma_50", "dist_sma_200", "dist_52w_high", "dist_52w_low",
            "market_return_1d", "sector_return_1d"
        ]

        # Ensure all columns exist
        for col in feature_cols:
            if col not in df.columns:
                df[col] = 0.0

        out_df = df[feature_cols].copy()

        # Target columns for training ML models (strictly forward-shifted)
        out_df["future_return_1d"] = (df["close"].shift(-1) - df["close"]) / df["close"]
        out_df["future_return_3d"] = (df["close"].shift(-3) - df["close"]) / df["close"]
        out_df["future_return_5d"] = (df["close"].shift(-5) - df["close"]) / df["close"]
        out_df["future_return_10d"] = (df["close"].shift(-10) - df["close"]) / df["close"]
        out_df["future_return_20d"] = (df["close"].shift(-20) - df["close"]) / df["close"]

        # Classification targets (direction)
        out_df["future_dir_1d"] = np.where(out_df["future_return_1d"] > 0, 1, 0)
        out_df["future_dir_5d"] = np.where(out_df["future_return_5d"] > 0, 1, 0)

        return out_df
