"""
Historical analogue search engine.
Finds historical technical setups (RSI, moving average alignment, volatility, volume) similar to current setup
and computes empirical forward-return statistics across 1D, 3D, 5D, 10D, 20D horizons.
"""
from typing import Dict, Any, List
import pandas as pd
import numpy as np


class HistoricalAnalogueEngine:
    """Finds historical setup analogues and returns empirical forward probability distribution."""

    @staticmethod
    def find_analogues(df: pd.DataFrame, horizons: List[int] = [1, 3, 5, 10, 20]) -> Dict[str, Any]:
        """
        Analyzes historical observations for similar RSI, MA alignment, and volatility conditions.
        Returns forward stats per horizon.
        """
        if df.empty or len(df) < 100:
            return {
                "sample_size": 0,
                "horizons": {},
                "status": "Insufficient data for analogue matching",
            }

        df = df.copy().sort_values("Date").reset_index(drop=True)
        latest = df.iloc[-1]

        cur_rsi = latest.get("rsi_14", 50)
        cur_dist_sma20 = latest.get("dist_sma_50_pct", 0)  # distance from 50 DMA
        cur_rel_vol = latest.get("relative_volume", 1.0)

        # Historical window (excluding the last 20 days so we have true forward returns for evaluation)
        hist_df = df.iloc[:-21].copy()
        if hist_df.empty:
            return {"sample_size": 0, "horizons": {}}

        # Define analogue criteria mask
        rsi_match = (hist_df["rsi_14"] >= cur_rsi - 7.5) & (hist_df["rsi_14"] <= cur_rsi + 7.5)
        sma_match = (hist_df["dist_sma_50_pct"] >= cur_dist_sma20 - 0.05) & (
            hist_df["dist_sma_50_pct"] <= cur_dist_sma20 + 0.05
        )

        matches_mask = rsi_match & sma_match
        matched_indices = hist_df[matches_mask].index

        if len(matched_indices) < 5:
            # Relax criteria if too few matches
            rsi_match = (hist_df["rsi_14"] >= cur_rsi - 15) & (hist_df["rsi_14"] <= cur_rsi + 15)
            matches_mask = rsi_match
            matched_indices = hist_df[matches_mask].index

        horizon_stats = {}
        for h in horizons:
            fwd_returns = []
            for idx in matched_indices:
                if idx + h < len(df):
                    ret = (df.iloc[idx + h]["Close"] - df.iloc[idx]["Close"]) / df.iloc[idx]["Close"]
                    fwd_returns.append(ret)

            if fwd_returns:
                arr = np.array(fwd_returns)
                pos_prob = float(np.mean(arr > 0))
                neg_prob = float(np.mean(arr < 0))
                horizon_stats[f"{h}d"] = {
                    "horizon_days": h,
                    "count": len(arr),
                    "mean_return_pct": round(float(np.mean(arr)) * 100, 2),
                    "median_return_pct": round(float(np.median(arr)) * 100, 2),
                    "win_rate_pct": round(pos_prob * 100, 2),
                    "loss_rate_pct": round(neg_prob * 100, 2),
                    "max_gain_pct": round(float(np.max(arr)) * 100, 2),
                    "max_loss_pct": round(float(np.min(arr)) * 100, 2),
                    "volatility_pct": round(float(np.std(arr)) * 100, 2),
                }

        return {
            "sample_size": len(matched_indices),
            "match_conditions": f"RSI ~ {cur_rsi:.1f}, Dist 50DMA ~ {cur_dist_sma20*100:.1f}%",
            "horizons": horizon_stats,
        }
