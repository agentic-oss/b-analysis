import numpy as np
import pandas as pd
from typing import Dict, Any, List
from src.indicators.technical import TechnicalIndicators

class AnalogueFinder:
    """
    Finds historical situations in a stock's past performance similar to its current market state.
    Calculates forward statistics (mean, median, positive/negative probabilities, min/max returns)
    over 1, 3, 5, 10, 20 trading days to establish empirical probability frameworks.
    """

    @staticmethod
    def find_analogues(df: pd.DataFrame, horizons: List[int] = [1, 3, 5, 10, 20]) -> Dict[str, Any]:
        """
        Expects df with calculated technical indicators.
        Compares current row (latest) with past historical rows.
        """
        if df.empty or len(df) < 50:
            return {
                "num_analogues": 0,
                "horizons": {f"{h}d": {} for h in horizons},
                "matched_conditions": []
            }

        df_calc = TechnicalIndicators.calculate_all(df) if "rsi_14" not in df.columns else df.copy()

        # Current state parameters
        latest = df_calc.iloc[-1]
        cur_rsi = latest.get("rsi_14", 50.0)
        cur_vol = latest.get("volatility_20d", 0.20)
        cur_dist_sma20 = latest.get("dist_sma_20", 0.0)

        # Look back over historical data excluding the recent window (last 20 days to avoid self-overlap)
        history = df_calc.iloc[:-25].copy()
        if history.empty:
            return {
                "num_analogues": 0,
                "horizons": {f"{h}d": {} for h in horizons},
                "matched_conditions": []
            }

        # Filtering matching historical states
        # Conditions: RSI within +/- 7.5, dist_sma20 within +/- 3%, volatility within +/- 25% relative
        rsi_match = (history["rsi_14"] >= cur_rsi - 7.5) & (history["rsi_14"] <= cur_rsi + 7.5)
        dist_match = (history["dist_sma_20"] >= cur_dist_sma20 - 0.03) & (history["dist_sma_20"] <= cur_dist_sma20 + 0.03)

        matches = history[rsi_match & dist_match]

        # If too few matches, relax constraints
        if len(matches) < 5:
            rsi_match = (history["rsi_14"] >= cur_rsi - 12.0) & (history["rsi_14"] <= cur_rsi + 12.0)
            matches = history[rsi_match]

        analogue_indices = matches.index.tolist()
        num_analogues = len(analogue_indices)

        horizon_stats = {}

        for h in horizons:
            fwd_returns = []
            for idx in analogue_indices:
                if idx + h < len(df_calc):
                    p_entry = df_calc.iloc[idx]["close"]
                    p_exit = df_calc.iloc[idx + h]["close"]
                    ret = (p_exit - p_entry) / p_entry
                    fwd_returns.append(ret)

            if len(fwd_returns) > 0:
                rets = np.array(fwd_returns)
                pos_prob = float(np.mean(rets > 0)) * 100
                neg_prob = float(np.mean(rets < 0)) * 100
                avg_ret = float(np.mean(rets)) * 100
                med_ret = float(np.median(rets)) * 100
                max_gain = float(np.max(rets)) * 100
                max_loss = float(np.min(rets)) * 100
                fwd_vol = float(np.std(rets)) * 100
            else:
                pos_prob, neg_prob, avg_ret, med_ret, max_gain, max_loss, fwd_vol = 50.0, 50.0, 0.0, 0.0, 0.0, 0.0, 0.0

            horizon_stats[f"{h}d"] = {
                "sample_size": len(fwd_returns),
                "avg_forward_return_pct": round(avg_ret, 2),
                "median_forward_return_pct": round(med_ret, 2),
                "positive_return_probability": round(pos_prob, 2),
                "negative_return_probability": round(neg_prob, 2),
                "max_observed_gain_pct": round(max_gain, 2),
                "max_observed_loss_pct": round(max_loss, 2),
                "forward_volatility_pct": round(fwd_vol, 2)
            }

        return {
            "num_analogues": num_analogues,
            "horizons": horizon_stats,
            "matched_conditions": ["RSI +/- 7.5", "Dist SMA20 +/- 3%"]
        }
