"""
Sector Analysis module calculating sector performance, relative strength vs NIFTY,
momentum scores, sector rotation, and sector rankings.
"""

import logging
from typing import Dict, Any, List
import pandas as pd

logger = logging.getLogger(__name__)


def analyze_sectors(
    sector_dfs: Dict[str, pd.DataFrame],
    nifty_df: pd.DataFrame
) -> List[Dict[str, Any]]:
    """
    Calculates sector metrics and generates ranked sector analysis list.
    """
    nifty_ret_1d = 0.0
    nifty_ret_5d = 0.0
    nifty_ret_20d = 0.0

    if not nifty_df.empty and len(nifty_df) >= 20:
        latest_c = nifty_df["Close"].iloc[-1]
        nifty_ret_1d = nifty_df["Close"].pct_change(1).iloc[-1] * 100.0
        nifty_ret_5d = (latest_c - nifty_df["Close"].iloc[-6]) / nifty_df["Close"].iloc[-6] * 100.0
        nifty_ret_20d = (latest_c - nifty_df["Close"].iloc[-21]) / nifty_df["Close"].iloc[-21] * 100.0

    sector_results = []

    for name, df in sector_dfs.items():
        if df.empty or len(df) < 20:
            continue

        latest_c = df["Close"].iloc[-1]
        ret_1d = df["Close"].pct_change(1).iloc[-1] * 100.0
        ret_5d = (latest_c - df["Close"].iloc[-6]) / df["Close"].iloc[-6] * 100.0 if len(df) >= 6 else ret_1d
        ret_20d = (latest_c - df["Close"].iloc[-21]) / df["Close"].iloc[-21] * 100.0 if len(df) >= 21 else ret_5d

        # Relative Strength vs NIFTY
        rs_1d = round(ret_1d - nifty_ret_1d, 2)
        rs_5d = round(ret_5d - nifty_ret_5d, 2)
        rs_20d = round(ret_20d - nifty_ret_20d, 2)

        # Volatility
        vol_20d = round(df.get("volatility_20d", pd.Series([15.0])).iloc[-1], 2)

        # Volume Trend
        rel_vol = round(df.get("relative_volume", pd.Series([1.0])).iloc[-1], 2)

        # Composite Sector Momentum Score (0-100)
        # Combination of 1D return (20%), 5D return (30%), 20D return (30%), Relative Strength (20%)
        raw_score = 50.0 + (ret_1d * 2.0) + (ret_5d * 1.5) + (ret_20d * 0.8) + (rs_5d * 1.0)
        momentum_score = round(max(0.0, min(100.0, raw_score)), 1)

        sector_results.append({
            "sector": name,
            "close": float(round(latest_c, 2)),
            "daily_return": round(ret_1d, 2),
            "weekly_return": round(ret_5d, 2),
            "monthly_return": round(ret_20d, 2),
            "relative_strength_1d": rs_1d,
            "relative_strength_5d": rs_5d,
            "relative_strength_20d": rs_20d,
            "volatility_20d": vol_20d,
            "relative_volume": rel_vol,
            "momentum_score": momentum_score
        })

    # Sort sectors by momentum score descending
    sector_results.sort(key=lambda x: x["momentum_score"], reverse=True)

    # Assign rank
    for idx, sec in enumerate(sector_results, start=1):
        sec["rank"] = idx

    return sector_results
