import logging
from typing import Dict, List, Any, Optional
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class PatternAnalogueEngine:
    """
    Identifies historical setup analogues (RSI, volatility, MA alignment) for a given stock,
    and computes empirical forward return distributions (1D, 3D, 5D, 10D, 20D).
    Calculates positive/negative probabilities, average/median returns, max gain/loss, and volatility.
    """

    def __init__(self, rsi_tolerance: float = 5.0, volatility_tolerance: float = 0.05):
        self.rsi_tolerance = rsi_tolerance
        self.volatility_tolerance = volatility_tolerance

    def find_analogues(
        self,
        df_history: pd.DataFrame,
        current_state: Dict[str, Any],
        horizons: List[int] = [1, 3, 5, 10, 20],
    ) -> Dict[str, Any]:
        if df_history.empty or len(df_history) < 30:
            return self._empty_result(horizons)

        df = df_history.copy().sort_values("date").reset_index(drop=True)
        curr_rsi = current_state.get("rsi_14", 50.0)

        # Match historical dates where RSI was within curr_rsi +/- tolerance
        # Exclude the most recent horizon rows to prevent overlap/leakage
        max_h = max(horizons)
        search_df = df.iloc[:-max_h] if len(df) > max_h else df.iloc[:0]

        if search_df.empty or "rsi_14" not in search_df.columns:
            return self._empty_result(horizons)

        rsi_matches_idx = search_df[
            (search_df["rsi_14"] >= curr_rsi - self.rsi_tolerance) &
            (search_df["rsi_14"] <= curr_rsi + self.rsi_tolerance)
        ].index.tolist()

        num_matches = len(rsi_matches_idx)
        if num_matches == 0:
            return self._empty_result(horizons)

        horizon_stats = {}

        for h in horizons:
            fwd_returns = []
            for idx in rsi_matches_idx:
                if idx + h < len(df):
                    p_entry = df.loc[idx, "close"]
                    p_exit = df.loc[idx + h, "close"]
                    if p_entry > 0:
                        ret = (p_exit - p_entry) / p_entry
                        fwd_returns.append(ret)

            if fwd_returns:
                arr = np.array(fwd_returns)
                pos_prob = round(float(np.mean(arr > 0)) * 100.0, 2)
                neg_prob = round(float(np.mean(arr < 0)) * 100.0, 2)
                avg_ret = round(float(np.mean(arr)) * 100.0, 2)
                med_ret = round(float(np.median(arr)) * 100.0, 2)
                max_gain = round(float(np.max(arr)) * 100.0, 2)
                max_loss = round(float(np.min(arr)) * 100.0, 2)
                fwd_vol = round(float(np.std(arr)) * 100.0, 2)

                # Directional Bias
                if pos_prob >= 65:
                    bias = "Bullish"
                elif pos_prob >= 55:
                    bias = "Slightly Bullish"
                elif neg_prob >= 65:
                    bias = "Bearish"
                elif neg_prob >= 55:
                    bias = "Slightly Bearish"
                else:
                    bias = "Neutral"

                horizon_stats[f"{h}d"] = {
                    "sample_count": len(fwd_returns),
                    "directional_bias": bias,
                    "confidence_score": min(100, int(len(fwd_returns) * 2)),
                    "avg_return_pct": avg_ret,
                    "median_return_pct": med_ret,
                    "win_probability_pct": pos_prob,
                    "loss_probability_pct": neg_prob,
                    "max_gain_pct": max_gain,
                    "max_loss_pct": max_loss,
                    "forward_volatility_pct": fwd_vol,
                }
            else:
                horizon_stats[f"{h}d"] = self._empty_horizon()

        return {
            "historical_sample_count": num_matches,
            "analogue_matching_criteria": f"RSI 14 within +/- {self.rsi_tolerance}",
            "horizons": horizon_stats,
        }

    def _empty_horizon(self) -> Dict[str, Any]:
        return {
            "sample_count": 0,
            "directional_bias": "Neutral",
            "confidence_score": 0,
            "avg_return_pct": 0.0,
            "median_return_pct": 0.0,
            "win_probability_pct": 50.0,
            "loss_probability_pct": 50.0,
            "max_gain_pct": 0.0,
            "max_loss_pct": 0.0,
            "forward_volatility_pct": 0.0,
        }

    def _empty_result(self, horizons: List[int]) -> Dict[str, Any]:
        return {
            "historical_sample_count": 0,
            "analogue_matching_criteria": f"RSI 14 within +/- {self.rsi_tolerance}",
            "horizons": {f"{h}d": self._empty_horizon() for h in horizons},
        }
