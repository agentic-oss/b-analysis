"""
Historical Pattern Analogue Finder.
Finds historical technical and market conditions similar to current state,
and computes empirical forward-return distribution statistics.
"""

import logging
from typing import Dict, Any, List, Optional
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class PatternAnalogueFinder:
    """Finds historical analogues based on multi-factor similarity and computes empirical forward outcome distributions."""

    HORIZONS = [1, 3, 5, 10, 20]

    def find_analogues(
        self,
        stock_df: pd.DataFrame,
        current_idx: int = -1,
        rsi_tolerance: float = 10.0,
        ma_dist_tolerance: float = 5.0,
        volatility_tolerance: float = 0.10,
        min_analogues: int = 5,
    ) -> Dict[str, Any]:
        """
        Finds historical rows in stock_df similar to stock_df.iloc[current_idx]
        and evaluates empirical forward returns over 1, 3, 5, 10, 20 trading days.
        """
        if stock_df.empty or len(stock_df) < 50:
            return self._empty_response()

        # Handle negative indexing
        if current_idx < 0:
            current_idx = len(stock_df) + current_idx

        target_row = stock_df.iloc[current_idx]
        target_date = target_row["date"]

        target_rsi = target_row.get("rsi_14", 50.0)
        target_ma_dist = target_row.get("dist_sma_20", 0.0)
        target_vol = target_row.get("volatility_20d", 0.15)

        # Candidates must be strictly before current_idx - max(HORIZONS) to prevent look-ahead bias
        max_horizon = max(self.HORIZONS)
        valid_history = stock_df.iloc[: max(0, current_idx - max_horizon)].copy()

        if valid_history.empty:
            return self._empty_response()

        # Compute Similarity Metric
        rsi_diff = (valid_history["rsi_14"] - target_rsi).abs()
        ma_diff = (valid_history["dist_sma_20"] - target_ma_dist).abs()
        vol_diff = (valid_history["volatility_20d"] - target_vol).abs()

        match_mask = (rsi_diff <= rsi_tolerance) & (ma_diff <= ma_dist_tolerance) & (vol_diff <= volatility_tolerance)
        matches = valid_history[match_mask]

        # If too few matches, relax tolerances
        if len(matches) < min_analogues:
            match_mask = (rsi_diff <= rsi_tolerance * 1.8) & (ma_diff <= ma_dist_tolerance * 1.8)
            matches = valid_history[match_mask]

        if matches.empty:
            return self._empty_response()

        # Calculate forward returns for matched historical indices
        forward_stats = {}
        matched_indices = matches.index.tolist()

        for h in self.HORIZONS:
            fwd_returns = []
            for idx in matched_indices:
                p_current = stock_df.iloc[idx]["close"]
                p_future = stock_df.iloc[idx + h]["close"]
                fwd_ret = (p_future - p_current) / p_current
                fwd_returns.append(fwd_ret)

            returns_arr = np.array(fwd_returns)
            pos_prob = float(np.mean(returns_arr > 0))
            neg_prob = float(np.mean(returns_arr < 0))

            forward_stats[f"{h}d"] = {
                "horizon_days": h,
                "observations": len(returns_arr),
                "avg_return": round(float(np.mean(returns_arr)) * 100, 2),
                "median_return": round(float(np.median(returns_arr)) * 100, 2),
                "pos_return_prob": round(pos_prob * 100, 1),
                "neg_return_prob": round(neg_prob * 100, 1),
                "max_gain": round(float(np.max(returns_arr)) * 100, 2),
                "max_loss": round(float(np.min(returns_arr)) * 100, 2),
                "fwd_volatility": round(float(np.std(returns_arr)) * 100, 2),
            }

        return {
            "target_date": target_date,
            "analogue_count": len(matches),
            "similarity_criteria": {
                "target_rsi": round(target_rsi, 1),
                "target_ma_dist_pct": round(target_ma_dist, 2),
                "target_volatility": round(target_vol, 2),
            },
            "forward_outcomes": forward_stats,
        }

    def _empty_response(self) -> Dict[str, Any]:
        empty_outcomes = {}
        for h in self.HORIZONS:
            empty_outcomes[f"{h}d"] = {
                "horizon_days": h,
                "observations": 0,
                "avg_return": 0.0,
                "median_return": 0.0,
                "pos_return_prob": 50.0,
                "neg_return_prob": 50.0,
                "max_gain": 0.0,
                "max_loss": 0.0,
                "fwd_volatility": 0.0,
            }
        return {
            "analogue_count": 0,
            "similarity_criteria": {},
            "forward_outcomes": empty_outcomes,
        }
