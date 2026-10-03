import logging
from typing import Dict, Any, List
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

class HistoricalAnalogueAnalyzer:
    """Finds historical setup analogues (RSI, volatility, moving average alignment) and statistics."""

    @staticmethod
    def find_analogues(df: pd.DataFrame, horizons: List[int] = [1, 3, 5, 10, 20]) -> Dict[str, Any]:
        if df.empty or len(df) < 50:
            return {
                "observations": 0,
                "forward_stats": {}
            }

        df = df.copy().reset_index(drop=True)
        latest = df.iloc[-1]

        latest_rsi = latest.get("rsi_14", 50)
        latest_vol = latest.get("volatility_20d", 0.2)
        latest_above_sma20 = latest["close"] > latest.get("sma_20", latest["close"])

        # Find historical days (excluding last 20 days to avoid current regime overlapping)
        hist_df = df.iloc[:-25].copy()

        rsi_match = (hist_df["rsi_14"] >= latest_rsi - 7) & (hist_df["rsi_14"] <= latest_rsi + 7)
        vol_match = (hist_df["volatility_20d"] >= latest_vol * 0.7) & (hist_df["volatility_20d"] <= latest_vol * 1.3)
        sma_match = (hist_df["close"] > hist_df["sma_20"]) == latest_above_sma20

        matches = hist_df[rsi_match & vol_match & sma_match]
        obs_count = len(matches)

        forward_stats = {}
        if obs_count >= 5:
            for h in horizons:
                forward_returns = []
                for idx in matches.index:
                    if idx + h < len(df):
                        entry_price = df.iloc[idx]["close"]
                        exit_price = df.iloc[idx + h]["close"]
                        f_ret = (exit_price - entry_price) / entry_price
                        forward_returns.append(f_ret)

                if forward_returns:
                    returns_arr = np.array(forward_returns)
                    pos_prob = float(np.mean(returns_arr > 0))
                    neg_prob = float(np.mean(returns_arr < 0))
                    avg_ret = float(np.mean(returns_arr))
                    med_ret = float(np.median(returns_arr))
                    max_gain = float(np.max(returns_arr))
                    max_loss = float(np.min(returns_arr))

                    forward_stats[f"{h}d"] = {
                        "avg_return": round(avg_ret * 100, 2),
                        "median_return": round(med_ret * 100, 2),
                        "positive_probability": round(pos_prob * 100, 1),
                        "negative_probability": round(neg_prob * 100, 1),
                        "max_gain": round(max_gain * 100, 2),
                        "max_loss": round(max_loss * 100, 2)
                    }

        return {
            "observations": obs_count,
            "forward_stats": forward_stats
        }
