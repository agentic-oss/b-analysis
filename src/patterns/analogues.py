"""
Historical Pattern Analogue Matching Engine.
Identifies historical setups similar to current technical/volatility/volume state and calculates empirical forward return statistics.
"""
import logging
from typing import Dict, Any, List
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


class HistoricalPatternEngine:
    """
    Finds historical analogue trading days for a stock and evaluates empirical forward performance.
    """

    @staticmethod
    def find_analogues(
        df: pd.DataFrame,
        horizons: List[int] = [1, 3, 5, 10, 20],
        max_matches: int = 50
    ) -> Dict[str, Any]:
        """
        Scans historical observations for similar RSI, volatility, moving average distance, and relative volume setups.
        Computes forward return statistics over specified horizons.
        """
        if df.empty or len(df) < 60:
            return {
                "observations_found": 0,
                "forward_statistics": {}
            }

        # Current state vector
        latest = df.iloc[-1]
        curr_rsi = latest.get("rsi_14", 50.0)
        curr_vol = latest.get("volatility_20d", 0.20)
        curr_dist_sma20 = latest.get("dist_sma_20_pct", 0.0)
        curr_rel_vol = latest.get("relative_volume", 1.0)

        # Historical search space (excluding last 20 days to avoid overlap with current state)
        history = df.iloc[:-21].copy()

        if history.empty:
            return {
                "observations_found": 0,
                "forward_statistics": {}
            }

        # Calculate normalized Euclidean distance on feature space
        rsi_diff = (history["rsi_14"] - curr_rsi) / 20.0
        vol_diff = (history["volatility_20d"] - curr_vol) / 0.10
        dist_diff = (history["dist_sma_20_pct"] - curr_dist_sma20) / 5.0
        rvol_diff = (history["relative_volume"] - curr_rel_vol) / 1.0

        distance = np.sqrt(rsi_diff**2 + vol_diff**2 + dist_diff**2 + rvol_diff**2)
        history["distance"] = distance

        # Filter top matches with distance < 1.5
        matches = history[history["distance"] < 1.5].sort_values("distance").head(max_matches)

        if matches.empty:
            return {
                "observations_found": 0,
                "forward_statistics": {}
            }

        forward_stats = {}

        for h in horizons:
            fwd_returns = []
            for idx in matches.index:
                if idx + h < len(df):
                    start_c = df.iloc[idx]["close"]
                    end_c = df.iloc[idx + h]["close"]
                    ret = ((end_c - start_c) / start_c) * 100.0
                    fwd_returns.append(ret)

            if fwd_returns:
                fwd_arr = np.array(fwd_returns)
                pos_arr = fwd_arr[fwd_arr > 0]
                neg_arr = fwd_arr[fwd_arr < 0]

                forward_stats[f"{h}d"] = {
                    "horizon_days": h,
                    "sample_size": len(fwd_arr),
                    "mean_forward_return_pct": round(float(np.mean(fwd_arr)), 2),
                    "median_forward_return_pct": round(float(np.median(fwd_arr)), 2),
                    "win_rate_pct": round(float(len(pos_arr) / len(fwd_arr) * 100), 2),
                    "loss_rate_pct": round(float(len(neg_arr) / len(fwd_arr) * 100), 2),
                    "max_observed_gain_pct": round(float(np.max(fwd_arr)), 2),
                    "max_observed_loss_pct": round(float(np.min(fwd_arr)), 2),
                    "forward_volatility_pct": round(float(np.std(fwd_arr)), 2)
                }

        return {
            "observations_found": len(matches),
            "similarity_metric": "Normalized Euclidean Distance",
            "forward_statistics": forward_stats
        }
