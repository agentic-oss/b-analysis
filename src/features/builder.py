"""
Feature engineering module designed for machine learning readiness.
Constructs strictly point-in-time features (no lookahead bias) and separate future targets.

ANTI-LEAKAGE DESIGN PRINCIPLE:
Every feature row at date T uses strictly information available on or before date T.
Future targets (e.g. future_return_1d, future_return_5d) shift prices backwards so that
row T contains the price returns that occur *after* date T. Model training MUST split
data along time boundaries without random shuffling.
"""

from typing import List, Optional
import pandas as pd
import numpy as np


class FeatureEngineer:
    """
    Generates point-in-time feature matrix and future prediction targets.
    """

    FEATURE_COLUMNS = [
        "Open",
        "High",
        "Low",
        "Close",
        "Volume",
        "Daily_Return",
        "Return_5d",
        "Return_20d",
        "RSI_14",
        "Stoch_RSI",
        "MACD",
        "MACD_Signal",
        "MACD_Hist",
        "ROC_10",
        "ATR_14",
        "Volatility_20d",
        "BB_Width",
        "Relative_Volume",
        "Gap_Pct",
        "Intraday_Range_Pct",
        "Dist_From_SMA_20",
        "Dist_From_SMA_50",
        "Dist_From_SMA_200",
        "Dist_From_52W_High",
        "Dist_From_52W_Low",
    ]

    TARGET_HORIZONS = [1, 3, 5, 10, 20]

    def create_features_and_targets(
        self,
        df: pd.DataFrame,
        market_regime_return: float = 0.0,
        sector_return: float = 0.0,
    ) -> pd.DataFrame:
        """
        Calculates point-in-time features and target columns for a single stock DataFrame.
        """
        if df is None or df.empty:
            return pd.DataFrame()

        res = df.copy()

        # 1. Ensure required point-in-time features exist
        for col in self.FEATURE_COLUMNS:
            if col not in res.columns:
                res[col] = np.nan

        # Add market & sector context
        res["market_return_1d"] = market_regime_return
        res["sector_return_1d"] = sector_return

        # 2. Construct future prediction targets (LOOKAHEAD FREE for feature calculation)
        # Note: Targets shift price into the future relative to row T.
        c = res["Close"]
        for h in self.TARGET_HORIZONS:
            # Future return over h days: (Close_{T+h} - Close_T) / Close_T
            res[f"future_return_{h}d"] = (c.shift(-h) - c) / c
            # Binary target: 1 if positive return, 0 otherwise
            res[f"future_target_direction_{h}d"] = np.where(
                res[f"future_return_{h}d"].isna(),
                np.nan,
                np.where(res[f"future_return_{h}d"] > 0, 1, 0),
            )

        return res
