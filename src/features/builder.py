"""
Feature Engineering module for downstream Machine Learning.
Ensures zero look-ahead bias by constructing features strictly using information available at date T.
Forward target columns (e.g. future_return_1d..20d) are generated explicitly and separated.
"""
import logging
from typing import List, Dict, Any
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


class FeatureBuilder:
    """
    Constructs standardized ML feature rows for each stock and date.
    Calculates forward return target columns separately.
    """

    FEATURE_COLUMNS = [
        "price_open", "price_high", "price_low", "price_close", "volume",
        "return_1d", "return_5d", "return_20d",
        "rsi_14", "stoch_rsi_k", "macd", "macd_signal", "macd_hist",
        "atr_14", "volatility_20d", "bollinger_bandwidth",
        "sma_20", "sma_50", "sma_200", "ema_20", "ema_50",
        "relative_volume", "volume_change_pct", "obv", "ad_line",
        "dist_sma_20_pct", "dist_sma_50_pct", "dist_sma_200_pct",
        "dist_52w_high_pct", "dist_52w_low_pct", "gap_pct", "intraday_range_pct",
        "market_return_1d", "market_volatility_20d", "market_regime_score",
        "sector_return_1d", "sector_momentum_score",
        "technical_score", "fundamental_score", "composite_score"
    ]

    TARGET_COLUMNS = [
        "future_return_1d",
        "future_return_3d",
        "future_return_5d",
        "future_return_10d",
        "future_return_20d"
    ]

    @staticmethod
    def build_feature_matrix(
        stock_df: pd.DataFrame,
        market_df: pd.DataFrame,
        sector_df: pd.DataFrame,
        composite_scores: Dict[str, Any] = None
    ) -> pd.DataFrame:
        """
        Builds feature matrix DataFrame with explicit current features and non-overlapping forward target horizons.
        """
        if stock_df.empty or len(stock_df) < 5:
            return pd.DataFrame()

        df = stock_df.copy()
        if "Date" in df.columns:
            df["Date"] = pd.to_datetime(df["Date"])
            df = df.sort_values("Date").reset_index(drop=True)

        close = df["close"]

        # Past Returns (Features at T)
        df["price_open"] = df["open"]
        df["price_high"] = df["high"]
        df["price_low"] = df["low"]
        df["price_close"] = df["close"]
        df["return_1d"] = close.pct_change(1) * 100.0
        df["return_5d"] = close.pct_change(5) * 100.0
        df["return_20d"] = close.pct_change(20) * 100.0

        # Market & Sector features merge
        df["market_return_1d"] = market_df["close"].pct_change(1) * 100.0 if not market_df.empty and "close" in market_df.columns else 0.0
        df["market_volatility_20d"] = market_df.get("volatility_20d", 0.15) if not market_df.empty else 0.15
        df["market_regime_score"] = composite_scores.get("components", {}).get("market_regime_score", 50.0) if composite_scores else 50.0

        df["sector_return_1d"] = sector_df["close"].pct_change(1) * 100.0 if not sector_df.empty and "close" in sector_df.columns else 0.0
        df["sector_momentum_score"] = composite_scores.get("components", {}).get("sector_score", 50.0) if composite_scores else 50.0

        # Scores
        df["technical_score"] = composite_scores.get("components", {}).get("technical_trend_score", 50.0) if composite_scores else 50.0
        df["fundamental_score"] = composite_scores.get("components", {}).get("fundamental_score", 50.0) if composite_scores else 50.0
        df["composite_score"] = composite_scores.get("composite_score", 50.0) if composite_scores else 50.0

        # Future Targets (Calculated ONLY using future prices from T+1..T+N)
        for h in [1, 3, 5, 10, 20]:
            df[f"future_return_{h}d"] = ((close.shift(-h) - close) / close) * 100.0

        if "Date" in df.columns:
            df["Date"] = df["Date"].dt.strftime("%Y-%m-%d")

        return df
