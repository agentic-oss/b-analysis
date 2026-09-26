"""
Feature Engineering module creating point-in-time machine learning features
and forward target variables while strictly preventing look-ahead bias.
"""

import logging
from typing import Dict, Any, List, Optional
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def generate_ml_features_and_targets(
    stock_df: pd.DataFrame,
    symbol: str,
    market_df: Optional[pd.DataFrame] = None,
    sector_df: Optional[pd.DataFrame] = None,
    horizons: List[int] = [1, 3, 5, 10, 20]
) -> pd.DataFrame:
    """
    Generates point-in-time feature matrix where every row t contains ONLY information
    known on or before day t.

    Forward targets (future_return_Xd) are calculated looking forward from day t,
    and must only be used as target labels during model training, NOT as input features!
    """
    if stock_df.empty or len(stock_df) < 20:
        return pd.DataFrame()

    df = stock_df.copy()

    # Base features
    feat = pd.DataFrame(index=df.index)
    feat["date"] = df["Date"]
    feat["symbol"] = symbol

    feat["price_open"] = df["Open"]
    feat["price_high"] = df["High"]
    feat["price_low"] = df["Low"]
    feat["price_close"] = df["Close"]
    feat["volume"] = df["Volume"]

    # Historical returns
    feat["return_1d"] = df["Close"].pct_change(1)
    feat["return_5d"] = df["Close"].pct_change(5)
    feat["return_20d"] = df["Close"].pct_change(20)

    # Technical indicators
    feat["rsi_14"] = df.get("rsi_14", 50.0)
    feat["stoch_rsi"] = df.get("stoch_rsi", 0.5)
    feat["macd"] = df.get("macd", 0.0)
    feat["macd_signal"] = df.get("macd_signal", 0.0)
    feat["macd_hist"] = df.get("macd_hist", 0.0)
    feat["atr"] = df.get("atr_14", 0.0)
    feat["volatility_20d"] = df.get("volatility_20d", 0.0)

    feat["sma_20"] = df.get("sma_20", df["Close"])
    feat["sma_50"] = df.get("sma_50", df["Close"])
    feat["sma_200"] = df.get("sma_200", df["Close"])
    feat["ema_20"] = df.get("ema_20", df["Close"])
    feat["ema_50"] = df.get("ema_50", df["Close"])

    feat["relative_volume"] = df.get("relative_volume", 1.0)
    feat["distance_from_52w_high"] = df.get("dist_52w_high_pct", 0.0)
    feat["distance_from_52w_low"] = df.get("dist_52w_low_pct", 0.0)

    # Benchmark & Sector market context features
    if market_df is not None and not market_df.empty and "daily_return" in market_df.columns:
        mkt_aligned = market_df.set_index("Date")["daily_return"].reindex(df["Date"]).values
        mkt_vol_aligned = market_df.set_index("Date")["volatility_20d"].reindex(df["Date"]).values if "volatility_20d" in market_df.columns else 15.0
        feat["market_return_1d"] = mkt_aligned
        feat["market_volatility"] = mkt_vol_aligned
    else:
        feat["market_return_1d"] = 0.0
        feat["market_volatility"] = 15.0

    if sector_df is not None and not sector_df.empty and "daily_return" in sector_df.columns:
        sec_aligned = sector_df.set_index("Date")["daily_return"].reindex(df["Date"]).values
        feat["sector_return_1d"] = sec_aligned
    else:
        feat["sector_return_1d"] = 0.0

    # Separate Forward Target columns (STRICTLY FOR MODEL TRAINING TARGETS)
    for h in horizons:
        feat[f"future_return_{h}d"] = df["Close"].shift(-h) / df["Close"] - 1.0
        feat[f"future_direction_{h}d"] = (feat[f"future_return_{h}d"] > 0).astype(int)

    return feat
