"""
Historical Pattern Analogue Matching Engine.
Identifies historical setups similar to current stock state (RSI, Volatility, MA Alignment, Volume)
and computes forward empirical return distributions (1D, 3D, 5D, 10D, 20D).
"""

from typing import Dict, List, Any
import numpy as np
import pandas as pd


class PatternAnalogueMatcher:
    """Finds historical analogues and calculates empirical forward return statistics."""

    def find_analogues_and_forward_returns(
        self, df: pd.DataFrame, horizons: List[int] = [1, 3, 5, 10, 20]
    ) -> Dict[str, Any]:
        """Calculates historical conditional probability statistics for the current technical setup."""
        if df.empty or len(df) < 60:
            return {
                "observations_count": 0,
                "forward_probabilities": {},
                "summary": "Insufficient historical data for analogue matching."
            }

        current = df.iloc[-1]
        c_rsi = current.get("rsi_14", 50.0)
        c_rel_vol = current.get("relative_volume", 1.0)
        c_dist_sma20 = current.get("dist_sma_20", 0.0)

        # Historical window excludes the recent horizon period to avoid look-ahead bias
        max_horizon = max(horizons)
        hist_df = df.iloc[:-max_horizon].copy()

        # Find historical dates matching technical setup criteria
        rsi_match = (hist_df["rsi_14"] >= c_rsi - 5.0) & (hist_df["rsi_14"] <= c_rsi + 5.0)
        vol_match = (hist_df["relative_volume"] >= c_rel_vol * 0.7) & (hist_df["relative_volume"] <= c_rel_vol * 1.3)
        sma_match = (hist_df["dist_sma_20"] >= c_dist_sma20 - 3.0) & (hist_df["dist_sma_20"] <= c_dist_sma20 + 3.0)

        matching_indices = hist_df[rsi_match & vol_match & sma_match].index.tolist()

        # Fallback if strict criteria yield few matches (< 10)
        if len(matching_indices) < 10:
            matching_indices = hist_df[rsi_match & sma_match].index.tolist()

        if len(matching_indices) < 5:
            matching_indices = hist_df[rsi_match].index.tolist()

        prob_results = {}
        for h in horizons:
            fwd_returns = []
            for idx in matching_indices:
                if idx + h < len(df):
                    price_now = df.iloc[idx]["close"]
                    price_fwd = df.iloc[idx + h]["close"]
                    if price_now > 0:
                        fwd_ret = ((price_fwd - price_now) / price_now) * 100
                        fwd_returns.append(fwd_ret)

            if fwd_returns:
                arr = np.array(fwd_returns)
                win_pct = (np.sum(arr > 0) / len(arr)) * 100
                loss_pct = (np.sum(arr < 0) / len(arr)) * 100

                # Directional bias
                bias = "Bullish" if win_pct >= 60 else ("Slightly Bullish" if win_pct >= 52 else ("Bearish" if win_pct <= 40 else ("Slightly Bearish" if win_pct <= 48 else "Neutral")))

                prob_results[f"{h}d"] = {
                    "horizon_days": h,
                    "avg_forward_return": round(float(np.mean(arr)), 2),
                    "median_forward_return": round(float(np.median(arr)), 2),
                    "positive_probability": round(float(win_pct), 2),
                    "negative_probability": round(float(loss_pct), 2),
                    "max_observed_gain": round(float(np.max(arr)), 2),
                    "max_observed_loss": round(float(np.min(arr)), 2),
                    "forward_std_dev": round(float(np.std(arr)), 2),
                    "directional_bias": bias,
                    "confidence": round(min(max(abs(win_pct - 50.0) * 2, 20.0), 90.0), 2)
                }

        return {
            "observations_count": len(matching_indices),
            "forward_probabilities": prob_results
        }
