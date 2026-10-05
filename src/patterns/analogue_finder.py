"""
Historical Analogue Pattern Matcher and Empirical Forward Return Engine.
"""

from typing import Dict, List, Any
import pandas as pd
import numpy as np


class HistoricalAnalogueFinder:
    """Finds historical market setups similar to today's state and calculates empirical forward statistics."""

    @staticmethod
    def find_analogues(
        df: pd.DataFrame, horizons: List[int] = [1, 3, 5, 10, 20]
    ) -> Dict[str, Any]:
        """
        Scans historical observations for similar RSI (+-7.5), volatility (+-25%),
        and SMA20 alignment state. Calculates empirical forward statistics over horizons.
        """
        if df.empty or len(df) < 100:
            return {
                "observations_count": 0,
                "horizons": {},
                "note": "Insufficient historical depth for pattern matching (min 100 days required)."
            }

        df = df.copy().reset_index(drop=True)
        latest = df.iloc[-1]

        target_rsi = latest.get("rsi_14", 50)
        target_vol = latest.get("volatility_20d", 0.2)
        target_above_sma20 = latest["close"] > latest.get("sma_20", latest["close"])

        # Compare with historical days (excluding recent horizon window to prevent overlap/leakage)
        max_h = max(horizons)
        search_df = df.iloc[:-max_h].copy()

        # Filtering conditions for matching setups
        rsi_match = (search_df["rsi_14"] >= target_rsi - 7.5) & (search_df["rsi_14"] <= target_rsi + 7.5)
        vol_match = (search_df["volatility_20d"] >= target_vol * 0.75) & (search_df["volatility_20d"] <= target_vol * 1.25)
        sma_match = (search_df["close"] > search_df["sma_20"]) == target_above_sma20

        matching_indices = search_df[rsi_match & vol_match & sma_match].index.tolist()

        if len(matching_indices) < 5:
            # Relax constraint to RSI + SMA if exact match count too low
            matching_indices = search_df[rsi_match & sma_match].index.tolist()

        obs_count = len(matching_indices)
        horizon_stats = {}

        for h in horizons:
            fwd_returns = []
            for idx in matching_indices:
                if idx + h < len(df):
                    curr_close = df.iloc[idx]["close"]
                    fwd_close = df.iloc[idx + h]["close"]
                    if curr_close > 0:
                        ret = (fwd_close - curr_close) / curr_close
                        fwd_returns.append(ret)

            if fwd_returns:
                fwd_arr = np.array(fwd_returns)
                pos_count = np.sum(fwd_arr > 0)
                neg_count = np.sum(fwd_arr < 0)
                tot = len(fwd_arr)

                horizon_stats[f"{h}d"] = {
                    "horizon_days": h,
                    "sample_size": tot,
                    "avg_forward_return_pct": round(float(np.mean(fwd_arr)) * 100, 2),
                    "median_forward_return_pct": round(float(np.median(fwd_arr)) * 100, 2),
                    "positive_probability_pct": round(float(pos_count / tot) * 100, 1),
                    "negative_probability_pct": round(float(neg_count / tot) * 100, 1),
                    "max_observed_gain_pct": round(float(np.max(fwd_arr)) * 100, 2),
                    "max_observed_loss_pct": round(float(np.min(fwd_arr)) * 100, 2),
                    "forward_volatility_pct": round(float(np.std(fwd_arr)) * 100, 2)
                }

        return {
            "observations_count": obs_count,
            "horizons": horizon_stats
        }
