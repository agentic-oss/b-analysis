from typing import Dict, List, Any, Optional
import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)


class HistoricalAnalogueEngine:
    """
    Finds historical analogue setups similar to current stock state.
    Calculates empirical probability statistics across forward horizons (1D, 3D, 5D, 10D, 20D):
    - Observations count
    - Mean & Median forward returns
    - Win / Loss probability
    - Max observed gain / loss
    - Directional bias & confidence score
    """

    def find_analogues_and_forward_stats(
        self,
        df: pd.DataFrame,
        horizons: List[int] = [1, 3, 5, 10, 20],
        rsi_window: float = 7.0,
        vol_window: float = 0.05,
    ) -> Dict[str, Any]:
        if df.empty or len(df) < 60:
            return {
                "matches_found": 0,
                "forward_probabilities": {},
                "directional_bias": {"1d": "Neutral", "3d": "Neutral", "5d": "Neutral", "10d": "Neutral", "20d": "Neutral"},
                "confidence": 50.0,
            }

        clean_df = df.dropna(subset=["close", "rsi_14", "volatility_20d"]).copy().reset_index(drop=True)
        if len(clean_df) < 30:
            return {
                "matches_found": 0,
                "forward_probabilities": {},
                "directional_bias": {"1d": "Neutral", "3d": "Neutral", "5d": "Neutral", "10d": "Neutral", "20d": "Neutral"},
                "confidence": 50.0,
            }

        last_row = clean_df.iloc[-1]
        curr_rsi = float(last_row.get("rsi_14", 50.0))
        curr_vol = float(last_row.get("volatility_20d", 0.20))
        curr_rel_vol = float(last_row.get("relative_volume", 1.0))

        # Search historical windows (excluding recent days to prevent leakage in target horizons)
        max_horizon = max(horizons)
        search_df = clean_df.iloc[:-max_horizon].copy()

        rsi_match = (search_df["rsi_14"] >= curr_rsi - rsi_window) & (search_df["rsi_14"] <= curr_rsi + rsi_window)
        vol_match = (search_df["volatility_20d"] >= curr_vol * (1 - vol_window)) & (search_df["volatility_20d"] <= curr_vol * (1 + vol_window))

        matches_idx = search_df[rsi_match & vol_match].index.tolist()

        # Fallback if too few matches: relax condition
        if len(matches_idx) < 5:
            matches_idx = search_df[rsi_match].index.tolist()

        fwd_stats = {}
        directional_bias = {}

        total_matches = len(matches_idx)

        for h in horizons:
            fwd_returns = []
            for idx in matches_idx:
                if idx + h < len(clean_df):
                    p_entry = clean_df.iloc[idx]["close"]
                    p_exit = clean_df.iloc[idx + h]["close"]
                    fwd_ret = (p_exit - p_entry) / p_entry
                    fwd_returns.append(fwd_ret)

            if fwd_returns:
                returns_arr = np.array(fwd_returns)
                pos_prob = float(np.mean(returns_arr > 0))
                neg_prob = float(np.mean(returns_arr < 0))
                avg_ret = float(np.mean(returns_arr))
                med_ret = float(np.median(returns_arr))
                max_gain = float(np.max(returns_arr))
                max_loss = float(np.min(returns_arr))
                fwd_vol = float(np.std(returns_arr))

                fwd_stats[f"{h}d"] = {
                    "observations": len(returns_arr),
                    "mean_return": round(avg_ret * 100, 2),
                    "median_return": round(med_ret * 100, 2),
                    "win_probability": round(pos_prob * 100, 1),
                    "loss_probability": round(neg_prob * 100, 1),
                    "max_gain": round(max_gain * 100, 2),
                    "max_loss": round(max_loss * 100, 2),
                    "forward_volatility": round(fwd_vol * 100, 2),
                }

                # Directional bias determination
                if pos_prob >= 0.65 and avg_ret > 0.01:
                    bias = "Bullish"
                elif pos_prob >= 0.55:
                    bias = "Slightly Bullish"
                elif neg_prob >= 0.65 and avg_ret < -0.01:
                    bias = "Bearish"
                elif neg_prob >= 0.55:
                    bias = "Slightly Bearish"
                else:
                    bias = "Neutral"

                directional_bias[f"{h}d"] = bias
            else:
                directional_bias[f"{h}d"] = "Neutral"

        # Overall confidence (0-100) based on match count
        confidence = float(min(100.0, max(30.0, total_matches * 3.0)))

        return {
            "matches_found": total_matches,
            "forward_probabilities": fwd_stats,
            "directional_bias": directional_bias,
            "confidence": round(confidence, 1),
            "disclaimer": "Historical analogue forward statistics are empirical probabilities for research purposes, not guaranteed price forecasts."
        }
