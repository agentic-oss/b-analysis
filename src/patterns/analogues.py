import pandas as pd
import numpy as np
from typing import Dict, Any, List

class HistoricalPatternMatcher:
    """
    Identifies historical market setups similar to current stock state
    (RSI, Volatility, Moving Average distance, Volume behavior)
    and calculates forward returns empirical statistics over 1D, 3D, 5D, 10D, 20D horizons.
    """

    @staticmethod
    def find_analogues(df: pd.DataFrame, horizons: List[int] = [1, 3, 5, 10, 20]) -> Dict[str, Any]:
        if df.empty or len(df) < 60:
            return {
                "observations_count": 0,
                "horizons": {f"{h}d": {} for h in horizons}
            }

        df = df.sort_values('date').copy()
        current_state = df.iloc[-1]

        curr_rsi = current_state.get('rsi_14', 50.0)
        curr_rvol = current_state.get('relative_volume', 1.0)
        curr_dist_sma20 = current_state.get('dist_sma_20', 0.0)

        # Exclude the most recent 25 days from historical analogues to prevent evaluating incomplete forward horizons
        history = df.iloc[:-25].copy()
        if history.empty:
            return {"observations_count": 0, "horizons": {f"{h}d": {} for h in horizons}}

        # Similarity criteria: RSI within +/- 7.5, RVOL within +/- 0.5, SMA20 distance within +/- 3%
        rsi_match = (history['rsi_14'] - curr_rsi).abs() <= 7.5
        rvol_match = (history['relative_volume'] - curr_rvol).abs() <= 0.5
        dist_match = (history['dist_sma_20'] - curr_dist_sma20).abs() <= 0.03

        matches_mask = rsi_match & rvol_match & dist_match
        matched_indices = history[matches_mask].index

        # If too few matches, relax constraints slightly
        if len(matched_indices) < 5:
            rsi_match = (history['rsi_14'] - curr_rsi).abs() <= 15.0
            matched_indices = history[rsi_match].index

        obs_count = len(matched_indices)
        horizon_results = {}

        for h in horizons:
            forward_returns = []
            for idx in matched_indices:
                loc = df.index.get_loc(idx)
                if loc + h < len(df):
                    p_start = df.iloc[loc]['close']
                    p_future = df.iloc[loc + h]['close']
                    ret = (p_future - p_start) / p_start
                    forward_returns.append(ret)

            if forward_returns:
                arr = np.array(forward_returns)
                mean_ret = float(np.mean(arr))
                median_ret = float(np.median(arr))
                pos_prob = float(np.sum(arr > 0) / len(arr))
                neg_prob = float(np.sum(arr < 0) / len(arr))
                max_gain = float(np.max(arr))
                max_loss = float(np.min(arr))
                fwd_vol = float(np.std(arr))
            else:
                mean_ret = median_ret = pos_prob = neg_prob = max_gain = max_loss = fwd_vol = 0.0

            horizon_results[f"{h}d"] = {
                "sample_size": len(forward_returns),
                "mean_return_pct": round(mean_ret * 100, 2),
                "median_return_pct": round(median_ret * 100, 2),
                "win_rate_pct": round(pos_prob * 100, 2),
                "loss_rate_pct": round(neg_prob * 100, 2),
                "max_gain_pct": round(max_gain * 100, 2),
                "max_loss_pct": round(max_loss * 100, 2),
                "forward_volatility_pct": round(fwd_vol * 100, 2)
            }

        return {
            "observations_count": obs_count,
            "horizons": horizon_results
        }
