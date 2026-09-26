"""
Historical Pattern Search & Empirical Forward Outcome Analysis module.
Finds historical technical analogues for a stock and computes forward empirical probabilities.
"""

import logging
from typing import Dict, Any, List
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def find_historical_analogues(
    stock_df: pd.DataFrame,
    horizons: List[int] = [1, 3, 5, 10, 20],
    rsi_tolerance: float = 7.0,
    vol_tolerance: float = 10.0,
    max_analogues: int = 50
) -> Dict[str, Any]:
    """
    Finds historical analogue setups matching current technical state (RSI, Volatility, Trend),
    and evaluates empirical forward return distributions over specified horizons.
    """
    if stock_df.empty or len(stock_df) < 50:
        return {
            "num_analogues": 0,
            "horizons": {}
        }

    latest = stock_df.iloc[-1]
    curr_rsi = latest.get("rsi_14", 50.0)
    curr_vol = latest.get("volatility_20d", 15.0)
    curr_above_sma20 = latest["Close"] > latest.get("sma_20", latest["Close"])

    # Historical lookup excludes the recent window (last 20 days) to prevent look-ahead and overlap
    historical_df = stock_df.iloc[:-25].copy()
    if historical_df.empty:
        return {"num_analogues": 0, "horizons": {}}

    # Distance metric based on normalized RSI, volatility, and trend alignment
    rsi_diff = (historical_df["rsi_14"] - curr_rsi).abs()
    vol_diff = (historical_df["volatility_20d"] - curr_vol).abs()
    sma_match = (historical_df["Close"] > historical_df["sma_20"]) == curr_above_sma20

    # Filter candidate matches
    candidates = historical_df[
        (rsi_diff <= rsi_tolerance) &
        (vol_diff <= vol_tolerance) &
        (sma_match)
    ]

    if len(candidates) < 3:
        # Relax tolerance slightly if too few analogues
        candidates = historical_df[
            (rsi_diff <= rsi_tolerance * 1.5) &
            (vol_diff <= vol_tolerance * 1.5)
        ]

    analogue_indices = candidates.index[:max_analogues]
    num_found = len(analogue_indices)

    horizon_results = {}
    for h in horizons:
        forward_returns = []
        for idx in analogue_indices:
            # Row position in stock_df
            pos = stock_df.index.get_loc(idx)
            if pos + h < len(stock_df):
                curr_p = stock_df["Close"].iloc[pos]
                fut_p = stock_df["Close"].iloc[pos + h]
                ret = (fut_p - curr_p) / curr_p * 100.0
                forward_returns.append(ret)

        if forward_returns:
            arr = np.array(forward_returns)
            pos_pct = round(float((arr > 0).mean() * 100.0), 1)
            neg_pct = round(float((arr < 0).mean() * 100.0), 1)
            horizon_results[f"{h}d"] = {
                "count": len(arr),
                "avg_forward_return": round(float(np.mean(arr)), 2),
                "median_forward_return": round(float(np.median(arr)), 2),
                "pos_probability_pct": pos_pct,
                "neg_probability_pct": neg_pct,
                "max_gain": round(float(np.max(arr)), 2),
                "max_loss": round(float(np.min(arr)), 2),
                "forward_volatility": round(float(np.std(arr)), 2)
            }
        else:
            horizon_results[f"{h}d"] = {
                "count": 0,
                "avg_forward_return": 0.0,
                "median_forward_return": 0.0,
                "pos_probability_pct": 50.0,
                "neg_probability_pct": 50.0,
                "max_gain": 0.0,
                "max_loss": 0.0,
                "forward_volatility": 0.0
            }

    return {
        "num_analogues": num_found,
        "horizons": horizon_results
    }
