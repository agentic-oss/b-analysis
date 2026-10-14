import logging
from typing import Dict, Any, List
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

class HistoricalAnalogueAnalyzer:
    """
    Identifies historical technical analogues matching current stock state
    (RSI, MA alignment, Volatility, Relative Volume) and computes empirical forward returns.
    """

    def __init__(self, horizons: List[int] = None):
        self.horizons = horizons or [1, 3, 5, 10, 20]

    def find_analogues(self, df: pd.DataFrame, target_idx: int = -1) -> Dict[str, Any]:
        """
        Finds historical days with technical setup similar to the target row
        and calculates empirical forward statistics.
        """
        if df.empty or len(df) < 60:
            return {"num_observations": 0, "stats_by_horizon": {}}

        target_idx = target_idx if target_idx >= 0 else len(df) + target_idx
        target_row = df.iloc[target_idx]

        rsi_target = target_row.get("rsi_14", 50) or 50
        vol_target = target_row.get("volatility_20d", 0.2) or 0.2
        rel_vol_target = target_row.get("relative_volume", 1.0) or 1.0
        above_sma20_target = target_row.get("close", 0) > target_row.get("sma_20", 0)

        # Exclude the last 20 rows from analogue search to allow full forward return calculations
        search_max_idx = max(0, len(df) - max(self.horizons) - 1)
        analogues = []

        for i in range(20, search_max_idx):
            row = df.iloc[i]
            rsi = row.get("rsi_14", 50) or 50
            vol = row.get("volatility_20d", 0.2) or 0.2
            rel_vol = row.get("relative_volume", 1.0) or 1.0
            above_sma20 = row.get("close", 0) > row.get("sma_20", 0)

            # Similarity conditions
            if abs(rsi - rsi_target) <= 7.5 and abs(vol - vol_target) <= 0.10 and (above_sma20 == above_sma20_target):
                analogues.append(i)

        stats_by_horizon = {}
        for h in self.horizons:
            fwd_returns = []
            for idx in analogues:
                if idx + h < len(df):
                    p_start = df.iloc[idx]["close"]
                    p_end = df.iloc[idx + h]["close"]
                    ret = (p_end - p_start) / (p_start + 1e-9)
                    fwd_returns.append(ret)

            if fwd_returns:
                arr = np.array(fwd_returns)
                pos_prob = float(np.mean(arr > 0))
                neg_prob = float(np.mean(arr < 0))
                stats_by_horizon[f"{h}d"] = {
                    "horizon_days": h,
                    "sample_size": len(arr),
                    "mean_forward_return": round(float(np.mean(arr) * 100), 2),
                    "median_forward_return": round(float(np.median(arr) * 100), 2),
                    "positive_probability": round(pos_prob * 100, 2),
                    "negative_probability": round(neg_prob * 100, 2),
                    "max_observed_gain": round(float(np.max(arr) * 100), 2),
                    "max_observed_loss": round(float(np.min(arr) * 100), 2),
                    "forward_volatility": round(float(np.std(arr) * 100), 2)
                }

        return {
            "num_observations": len(analogues),
            "stats_by_horizon": stats_by_horizon
        }


class FutureSignalEngine:
    """
    Generates probabilistic forward-looking bias (Bullish to Bearish) with confidence scores (0-100)
    based on historical analogues and empirical probabilities.
    """

    def generate_signals(self, analogue_results: Dict[str, Any], composite_score: float) -> Dict[str, Any]:
        """
        Maps empirical analogue forward statistics to directional signals:
        - Bullish
        - Slightly Bullish
        - Neutral
        - Slightly Bearish
        - Bearish
        """
        signals = {}
        stats = analogue_results.get("stats_by_horizon", {})

        for horizon, h_stats in stats.items():
            pos_prob = h_stats.get("positive_probability", 50.0)
            mean_ret = h_stats.get("mean_forward_return", 0.0)

            # Combined score: probability weight + composite score influence
            signal_score = (pos_prob * 0.7) + (composite_score * 0.3)

            if signal_score >= 65:
                bias = "Bullish"
            elif signal_score >= 55:
                bias = "Slightly Bullish"
            elif signal_score <= 35:
                bias = "Bearish"
            elif signal_score <= 45:
                bias = "Slightly Bearish"
            else:
                bias = "Neutral"

            confidence = min(100, max(0, int(abs(signal_score - 50) * 2 + min(50, h_stats.get("sample_size", 0)))))

            signals[horizon] = {
                "directional_bias": bias,
                "confidence": confidence,
                "historical_sample_size": h_stats.get("sample_size", 0),
                "positive_return_probability": pos_prob,
                "expected_return_pct": mean_ret
            }

        return signals
