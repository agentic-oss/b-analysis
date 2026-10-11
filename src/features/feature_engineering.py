import logging
from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


class FeatureEngineer:
    """
    Constructs normalized machine-learning feature sets and forward targets.

    PREVENTION OF LOOK-AHEAD BIAS / DATA LEAKAGE:
    Features for observation date T are strictly computed using information available up to date T.
    Target variables (e.g. future_return_1d) represent values occurring on dates T+1, T+3, T+5, etc.,
    and must ONLY be used as labels during offline model training, NEVER as inputs to feature matrices.
    """

    FEATURE_COLUMNS = [
        "price_open", "price_high", "price_low", "price_close", "volume",
        "return_1d", "return_5d", "return_20d",
        "rsi_14", "stoch_rsi_k", "macd", "macd_signal", "macd_hist",
        "atr_14", "volatility_20d",
        "sma_20", "sma_50", "sma_200", "ema_20", "ema_50",
        "dist_sma_20", "dist_sma_50", "dist_sma_200",
        "relative_volume", "distance_from_52w_high", "distance_from_52w_low",
        "market_return_1d", "sector_return_1d", "market_volatility",
        "breadth_pct_above_50dma", "technical_score", "fundamental_score"
    ]

    TARGET_COLUMNS = [
        "future_return_1d",
        "future_return_3d",
        "future_return_5d",
        "future_return_10d",
        "future_return_20d"
    ]

    @staticmethod
    def build_features(
        stock_df: pd.DataFrame,
        nifty_df: pd.DataFrame,
        sector_df: Optional[pd.DataFrame] = None,
        include_targets: bool = False
    ) -> pd.DataFrame:
        """Constructs standardized feature columns for ML modeling."""
        if stock_df.empty:
            return pd.DataFrame()

        df = stock_df.copy()

        # Map basic prices and returns
        df["price_open"] = df["open"]
        df["price_high"] = df["high"]
        df["price_low"] = df["low"]
        df["price_close"] = df["close"]
        df["distance_from_52w_high"] = df.get("dist_52w_high", 0.0)
        df["distance_from_52w_low"] = df.get("dist_52w_low", 0.0)

        # Merge NIFTY market context
        if not nifty_df.empty and "date" in nifty_df.columns:
            nifty_sub = nifty_df[["date", "return_1d", "volatility_20d"]].rename(
                columns={"return_1d": "market_return_1d", "volatility_20d": "market_volatility"}
            )
            df = pd.merge(df, nifty_sub, on="date", how="left")
        else:
            df["market_return_1d"] = 0.0
            df["market_volatility"] = 0.0

        # Merge Sector context
        if sector_df is not None and not sector_df.empty and "date" in sector_df.columns:
            sec_sub = sector_df[["date", "return_1d"]].rename(columns={"return_1d": "sector_return_1d"})
            df = pd.merge(df, sec_sub, on="date", how="left")
        else:
            df["sector_return_1d"] = 0.0

        df["breadth_pct_above_50dma"] = 50.0
        df["technical_score"] = 50.0
        df["fundamental_score"] = 50.0

        # Optional Forward Targets (For Model Training ONLY)
        if include_targets:
            c = df["close"]
            df["future_return_1d"] = c.shift(-1) / c - 1.0
            df["future_return_3d"] = c.shift(-3) / c - 1.0
            df["future_return_5d"] = c.shift(-5) / c - 1.0
            df["future_return_10d"] = c.shift(-10) / c - 1.0
            df["future_return_20d"] = c.shift(-20) / c - 1.0

        return df
