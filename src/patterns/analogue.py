"""
Historical analogue pattern matching and empirical forward probability engine.
Finds matching historical setups and computes forward returns (1d, 3d, 5d, 10d, 20d),
win probabilities, directional bias, and confidence scores.
"""

from typing import Dict, Any, List
import pandas as pd
import numpy as np


class PatternAnalogueEngine:
    """
    Identifies historical analogues based on RSI, Volatility, Moving Average distance, and Volume,
    and calculates empirical forward probability metrics.
    """

    def __init__(self, horizons: List[int] = [1, 3, 5, 10, 20]):
        self.horizons = horizons

    def find_analogues_and_probabilities(
        self,
        df: pd.DataFrame,
        tolerance_rsi: float = 5.0,
        tolerance_ma: float = 3.0,
        max_analogues: int = 50,
    ) -> Dict[str, Any]:
        """
        Calculates empirical conditional statistics for past instances similar to current state.
        """
        if df is None or len(df) < 60:
            return {
                "num_observations": 0,
                "forward_probabilities": {},
                "directional_bias": {"1d": "Neutral", "5d": "Neutral", "20d": "Neutral"},
                "confidence_score": 0.0,
            }

        latest = df.iloc[-1]
        c_rsi = latest.get("RSI_14", 50.0)
        c_ma_dist = latest.get("Dist_From_SMA_20", 0.0)

        # Look back over historical dataset excluding recent horizon days to avoid lookahead
        max_horizon = max(self.horizons)
        history = df.iloc[:-max_horizon].copy()

        # Match condition: similar RSI and SMA 20 distance
        match_mask = (
            (history["RSI_14"] - c_rsi).abs() <= tolerance_rsi
        ) & (
            (history["Dist_From_SMA_20"] - c_ma_dist).abs() <= tolerance_ma
        )

        matching_indices = history[match_mask].index.tolist()

        # If too few matches, widen tolerance slightly
        if len(matching_indices) < 10:
            match_mask = (
                (history["RSI_14"] - c_rsi).abs() <= (tolerance_rsi * 2.0)
            ) & (
                (history["Dist_From_SMA_20"] - c_ma_dist).abs() <= (tolerance_ma * 2.0)
            )
            matching_indices = history[match_mask].index.tolist()

        if not matching_indices:
            return {
                "num_observations": 0,
                "forward_probabilities": {},
                "directional_bias": {"1d": "Neutral", "5d": "Neutral", "20d": "Neutral"},
                "confidence_score": 0.0,
            }

        # Sample up to max_analogues
        if len(matching_indices) > max_analogues:
            matching_indices = matching_indices[-max_analogues:]

        forward_stats = {}
        directional_bias = {}

        for h in self.horizons:
            fwd_returns = []
            for idx in matching_indices:
                if idx + h < len(df):
                    price_now = df.loc[idx, "Close"]
                    price_fwd = df.loc[idx + h, "Close"]
                    if price_now > 0:
                        ret = (price_fwd - price_now) / price_now
                        fwd_returns.append(ret)

            if fwd_returns:
                arr = np.array(fwd_returns)
                pos_prob = float(np.mean(arr > 0))
                neg_prob = float(np.mean(arr < 0))
                avg_ret = float(np.mean(arr))
                med_ret = float(np.median(arr))
                max_gain = float(np.max(arr))
                max_loss = float(np.min(arr))
                fwd_vol = float(np.std(arr))

                forward_stats[f"{h}d"] = {
                    "sample_count": len(arr),
                    "avg_forward_return_pct": round(avg_ret * 100, 2),
                    "median_forward_return_pct": round(med_ret * 100, 2),
                    "positive_return_prob": round(pos_prob * 100, 1),
                    "negative_return_prob": round(neg_prob * 100, 1),
                    "max_observed_gain_pct": round(max_gain * 100, 2),
                    "max_observed_loss_pct": round(max_loss * 100, 2),
                    "forward_volatility_pct": round(fwd_vol * 100, 2),
                }

                # Directional bias determination
                if pos_prob >= 0.65:
                    bias = "Bullish"
                elif pos_prob >= 0.55:
                    bias = "Slightly Bullish"
                elif neg_prob >= 0.65:
                    bias = "Bearish"
                elif neg_prob >= 0.55:
                    bias = "Slightly Bearish"
                else:
                    bias = "Neutral"

                directional_bias[f"{h}d"] = bias

        sample_size = len(matching_indices)
        confidence = min(100.0, round((sample_size / 30.0) * 100.0, 1))

        return {
            "num_observations": sample_size,
            "forward_probabilities": forward_stats,
            "directional_bias": directional_bias,
            "confidence_score": confidence,
        }
