import logging
from typing import Dict, Any, List
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

class FeaturePipeline:
    """
    Constructs tabular feature matrices for ML model training and inference.

    LEAKAGE PREVENTION GUARANTEES:
    1. Features for date T use strictly information available on or before date T.
    2. Future return target columns (future_return_1d, 3d, 5d, 10d, 20d) are calculated
       using future close prices shifted backward (e.g. shift(-1)) and are strictly separated
       from the feature matrix X during model training.
    """

    def build_feature_matrix(self, stock_dfs: Dict[str, pd.DataFrame], sector_ranks: List[Dict[str, Any]] = None) -> pd.DataFrame:
        """
        Combines historical data for multiple stocks into a single consolidated
        tabular feature DataFrame with technical, market, and future target columns.
        """
        all_rows = []

        for symbol, df in stock_dfs.items():
            if df.empty or len(df) < 20:
                continue

            sdf = df.copy().sort_values("Date").reset_index(drop=True)

            # Calculate future return targets (shifted into the future, strictly for target variable Y)
            for h in [1, 3, 5, 10, 20]:
                sdf[f"future_return_{h}d"] = (sdf["close"].shift(-h) - sdf["close"]) / sdf["close"]

            feature_cols = [
                "Date", "symbol", "open", "high", "low", "close", "volume",
                "return_1d", "return_5d", "return_20d", "gap_pct", "intraday_range",
                "sma_20", "sma_50", "sma_200", "ema_20", "ema_50",
                "rsi_14", "stoch_rsi", "macd", "macd_signal", "macd_hist",
                "atr_14", "volatility_20d", "bollinger_bandwidth",
                "relative_volume", "dist_sma_20", "dist_sma_50", "dist_sma_200",
                "dist_52w_high", "dist_52w_low",
                "future_return_1d", "future_return_3d", "future_return_5d",
                "future_return_10d", "future_return_20d"
            ]

            existing_cols = [c for c in feature_cols if c in sdf.columns]
            all_rows.append(sdf[existing_cols])

        if not all_rows:
            return pd.DataFrame()

        combined = pd.concat(all_rows, ignore_index=True)
        return combined

    def get_point_in_time_features(self, combined_df: pd.DataFrame, target_date: str) -> pd.DataFrame:
        """
        Extracts point-in-time features strictly for target_date.
        Ensures no future target columns or future rows are exposed to feature evaluation.
        """
        if combined_df.empty:
            return pd.DataFrame()

        filtered = combined_df[combined_df["Date"] == target_date].copy()
        target_cols = [c for c in filtered.columns if c.startswith("future_return_")]
        return filtered.drop(columns=target_cols, errors="ignore")
