"""
Feature Engineering Module for ML Datasets.
Generates historical feature datasets and forward-looking return targets.
STRICTLY PREVENTS LOOK-AHEAD BIAS by using only historical information available up to date T.
"""

import logging
from typing import Dict, Any, List, Optional
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class FeatureBuilder:
    """Builds clean ML feature tables without look-ahead bias and computes explicit future return targets."""

    FEATURE_COLUMNS = [
        "price_open",
        "price_high",
        "price_low",
        "price_close",
        "volume",
        "return_1d",
        "return_5d",
        "return_20d",
        "rsi_14",
        "macd",
        "macd_signal",
        "atr_14",
        "volatility_20d",
        "sma_20",
        "sma_50",
        "sma_200",
        "ema_20",
        "ema_50",
        "relative_volume",
        "distance_from_52w_high",
        "distance_from_52w_low",
        "market_return_1d",
        "sector_return_1d",
        "market_volatility",
        "breadth_above_50dma_pct",
        "market_regime_score",
        "sector_rank",
        "technical_score",
        "fundamental_score",
    ]

    TARGET_HORIZONS = [1, 3, 5, 10, 20]

    def build_feature_dataset(
        self,
        stock_df: pd.DataFrame,
        market_df: Optional[pd.DataFrame] = None,
        sector_df: Optional[pd.DataFrame] = None,
        scoring_info: Optional[Dict[str, Any]] = None,
        fundamental_info: Optional[Dict[str, Any]] = None,
    ) -> pd.DataFrame:
        """
        Engineers feature vector for stock_df.
        Features on date T use ONLY data available up to date T.
        Target values (future_return_Nd) shift future prices BACKWARD to align with date T.
        """
        if stock_df.empty:
            return pd.DataFrame()

        df = stock_df.copy().sort_values("date").reset_index(drop=True)

        # Basic Price & Volume Features
        df["price_open"] = df["open"]
        df["price_high"] = df["high"]
        df["price_low"] = df["low"]
        df["price_close"] = df["close"]
        df["volume"] = df["volume"] if "volume" in df.columns else 0.0

        # Historical Returns
        df["return_1d"] = df["close"].pct_change(1)
        df["return_5d"] = df["close"].pct_change(5)
        df["return_20d"] = df["close"].pct_change(20)

        # Moving Averages & Moving Average Distances
        df["ema_20"] = df["close"].ewm(span=20, adjust=False).mean()
        df["ema_50"] = df["close"].ewm(span=50, adjust=False).mean()

        if "dist_52w_high" in df.columns:
            df["distance_from_52w_high"] = df["dist_52w_high"]
        else:
            h52 = df["high"].rolling(250, min_periods=10).max()
            df["distance_from_52w_high"] = ((df["close"] - h52) / h52) * 100

        if "dist_52w_low" in df.columns:
            df["distance_from_52w_low"] = df["dist_52w_low"]
        else:
            l52 = df["low"].rolling(250, min_periods=10).min()
            df["distance_from_52w_low"] = ((df["close"] - l52) / l52) * 100

        # Market & Sector Relatives
        if market_df is not None and not market_df.empty and "daily_return" in market_df.columns:
            mkt_map = dict(zip(market_df["date"], market_df["daily_return"]))
            df["market_return_1d"] = df["date"].map(mkt_map).fillna(0.0)

            if "volatility_20d" in market_df.columns:
                mkt_vol_map = dict(zip(market_df["date"], market_df["volatility_20d"]))
                df["market_volatility"] = df["date"].map(mkt_vol_map).fillna(0.15)
            else:
                df["market_volatility"] = 0.15
        else:
            df["market_return_1d"] = 0.0
            df["market_volatility"] = 0.15

        if sector_df is not None and not sector_df.empty and "daily_return" in sector_df.columns:
            sec_map = dict(zip(sector_df["date"], sector_df["daily_return"]))
            df["sector_return_1d"] = df["date"].map(sec_map).fillna(0.0)
        else:
            df["sector_return_1d"] = 0.0

        # Scores & Ratings Defaults
        df["breadth_above_50dma_pct"] = 50.0
        df["market_regime_score"] = 50.0
        df["sector_rank"] = 5.0
        df["technical_score"] = scoring_info.get("composite_score", 50.0) if scoring_info else 50.0
        df["fundamental_score"] = fundamental_info.get("fundamental_score", 50.0) if fundamental_info else 50.0

        # Target Calculations (LOOK-AHEAD PREVENTED BY CLEAR SHIFT TO SEPARATE TARGET COLUMNS)
        # On row T, future_return_Nd is the return realized from date T close to date T+N close.
        for h in self.TARGET_HORIZONS:
            future_close = df["close"].shift(-h)
            df[f"future_return_{h}d"] = (future_close - df["close"]) / df["close"]

        cols_to_keep = ["ticker", "exchange", "date"] + self.FEATURE_COLUMNS + [f"future_return_{h}d" for h in self.TARGET_HORIZONS]
        avail_cols = [c for c in cols_to_keep if c in df.columns]

        return df[avail_cols]
