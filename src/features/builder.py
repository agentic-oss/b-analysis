"""
Feature Engineering Module for Machine Learning Datasets.
Constructs clean point-in-time feature matrix and target columns without look-ahead bias.
"""

from typing import Dict, List, Any, Optional
import pandas as pd
import numpy as np


class FeatureEngineer:
    """Generates feature datasets and future return target columns for time-series ML modeling."""

    def build_features(
        self,
        df: pd.DataFrame,
        ticker: str,
        sector_name: str = "Market",
        market_regime: str = "Neutral"
    ) -> pd.DataFrame:
        """Constructs features and target columns for historical dataset.

        LOOK-AHEAD BIAS PREVENTION GUARANTEE:
        Features at row index T depend solely on values up to and including index T.
        Target variables (future_return_1d, future_return_5d, etc.) are generated using
        forward price shifts (lead values) and are strictly stored in target columns.
        During training, target columns are isolated from predictor feature matrices.
        """
        if df.empty or len(df) < 20:
            return pd.DataFrame()

        df = df.copy().sort_values("date").reset_index(drop=True)

        f_df = pd.DataFrame()
        f_df["date"] = df["date"]
        f_df["ticker"] = ticker
        f_df["sector"] = sector_name

        # Core Prices & Volume Features
        f_df["price_open"] = df["open"]
        f_df["price_high"] = df["high"]
        f_df["price_low"] = df["low"]
        f_df["price_close"] = df["close"]
        f_df["volume"] = df["volume"]

        # Historical Returns
        f_df["return_1d"] = df["close"].pct_change(1) * 100
        f_df["return_5d"] = df["close"].pct_change(5) * 100
        f_df["return_20d"] = df["close"].pct_change(20) * 100

        # Technical Indicators (if present in input)
        f_df["rsi_14"] = df.get("rsi_14", 50.0)
        f_df["stoch_rsi"] = df.get("stoch_rsi", 50.0)
        f_df["macd"] = df.get("macd", 0.0)
        f_df["macd_signal"] = df.get("macd_signal", 0.0)
        f_df["macd_hist"] = df.get("macd_hist", 0.0)
        f_df["atr_14"] = df.get("atr_14", 0.0)
        f_df["volatility_20d"] = df.get("volatility_20d", 0.0)

        # Distance from Moving Averages
        close = df["close"]
        f_df["dist_sma_20"] = df.get("dist_sma_20", ((close - df["close"].rolling(20, min_periods=1).mean()) / df["close"].rolling(20, min_periods=1).mean()) * 100)
        f_df["dist_sma_50"] = df.get("dist_sma_50", ((close - df["close"].rolling(50, min_periods=1).mean()) / df["close"].rolling(50, min_periods=1).mean()) * 100)
        f_df["dist_sma_200"] = df.get("dist_sma_200", ((close - df["close"].rolling(200, min_periods=1).mean()) / df["close"].rolling(200, min_periods=1).mean()) * 100)

        f_df["relative_volume"] = df.get("relative_volume", 1.0)
        f_df["dist_52w_high"] = df.get("dist_52w_high", 0.0)
        f_df["dist_52w_low"] = df.get("dist_52w_low", 0.0)
        f_df["market_regime"] = market_regime

        # --- TARGET COLUMNS (FORWARD LOOKING FOR ML TRAINING) ---
        # Note: Targets shift backwards (leading values) to measure performance after date T
        for h in [1, 3, 5, 10, 20]:
            fwd_close = df["close"].shift(-h)
            f_df[f"future_return_{h}d"] = ((fwd_close - close) / close) * 100

        f_df["target_direction_5d"] = (f_df["future_return_5d"] > 0).astype(int)

        return f_df
