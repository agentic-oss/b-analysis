import logging
from typing import Dict, Any, List
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


class HistoricalPatternAnalyzer:
    """Finds historical setup analogues and evaluates forward empirical return statistics."""

    @staticmethod
    def find_analogues(
        df: pd.DataFrame,
        horizons: List[int] = [1, 3, 5, 10, 20],
        rsi_tol: float = 5.0,
        ma_dist_tol: float = 0.03
    ) -> Dict[str, Any]:
        """
        Scans historical dataframe (excluding the latest day T) for setup conditions
        matching day T (RSI, MA configuration, relative volume), and computes forward returns.
        """
        if df.empty or len(df) < 60:
            return {
                "matches_count": 0,
                "forward_statistics": {},
                "message": "Insufficient historical observations for pattern analysis."
            }

        # Latest observation (target condition)
        latest = df.iloc[-1]
        t_rsi = latest.get("rsi_14", 50.0)
        t_dist_sma20 = latest.get("dist_sma_20", 0.0)
        t_rel_vol = latest.get("relative_volume", 1.0)

        # Historical search space: exclude the last max(horizons) rows to prevent overlap/leakage
        max_h = max(horizons)
        history = df.iloc[:-max_h].copy()

        # Match criteria
        rsi_match = (history["rsi_14"] >= t_rsi - rsi_tol) & (history["rsi_14"] <= t_rsi + rsi_tol)
        ma_match = (history["dist_sma_20"] >= t_dist_sma20 - ma_dist_tol) & (history["dist_sma_20"] <= t_dist_sma20 + ma_dist_tol)

        matches = history[rsi_match & ma_match]
        num_matches = len(matches)

        forward_stats = {}
        for h in horizons:
            fwd_returns = []
            for idx in matches.index:
                if idx + h < len(df):
                    p_entry = df.loc[idx, "close"]
                    p_exit = df.loc[idx + h, "close"]
                    ret = (p_exit - p_entry) / p_entry
                    fwd_returns.append(ret)

            if fwd_returns:
                fwd_arr = np.array(fwd_returns)
                win_rate = float(np.mean(fwd_arr > 0))
                loss_rate = float(np.mean(fwd_arr < 0))
                avg_ret = float(np.mean(fwd_arr))
                med_ret = float(np.median(fwd_arr))
                max_gain = float(np.max(fwd_arr))
                max_loss = float(np.min(fwd_arr))
                fwd_vol = float(np.std(fwd_arr))

                forward_stats[f"{h}d"] = {
                    "observations": len(fwd_returns),
                    "positive_probability": round(win_rate * 100, 2),
                    "negative_probability": round(loss_rate * 100, 2),
                    "average_return_pct": round(avg_ret * 100, 2),
                    "median_return_pct": round(med_ret * 100, 2),
                    "max_observed_gain_pct": round(max_gain * 100, 2),
                    "max_observed_loss_pct": round(max_loss * 100, 2),
                    "forward_volatility": round(fwd_vol * 100, 2)
                }

        return {
            "matches_count": num_matches,
            "forward_statistics": forward_stats
        }
