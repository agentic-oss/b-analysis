"""Historical Analogue Pattern Matching Engine."""

import pandas as pd
import numpy as np
from typing import Dict, Any, List

class HistoricalAnalogueAnalyzer:
    """Finds historical analogues matching current technical/volatility/regime setup and computes empirical statistics."""

    def find_analogues(self, stock_df: pd.DataFrame, current_idx: int = -1, max_matches: int = 30) -> Dict[str, Any]:
        """Scans historical data for dates with similar RSI, volatility, and price structure.

        Calculates forward empirical statistics (1D, 3D, 5D, 10D, 20D forward returns).
        """
        if stock_df.empty or len(stock_df) < 50:
            return {
                "observations_count": 0,
                "horizons": {}
            }

        target_row = stock_df.iloc[current_idx]
        target_rsi = target_row.get('rsi_14', 50.0)
        target_vol = target_row.get('volatility_20d', 0.15)
        target_dist_sma20 = target_row.get('dist_sma_20_pct', 0.0)

        # Historical search space (exclude last 20 days so forward returns exist)
        history_limit = len(stock_df) - 20
        if history_limit <= 30:
            return {"observations_count": 0, "horizons": {}}

        hist_df = stock_df.iloc[:history_limit].copy()

        # Distance metric (RSI, Volatility, SMA20 distance)
        rsi_diff = ((hist_df['rsi_14'] - target_rsi) / 10.0) ** 2
        vol_diff = ((hist_df['volatility_20d'] - target_vol) / 0.05) ** 2
        sma_diff = ((hist_df['dist_sma_20_pct'] - target_dist_sma20) / 2.0) ** 2

        distance = np.sqrt(rsi_diff + vol_diff + sma_diff)
        hist_df['analogue_distance'] = distance

        # Get top matches
        matches = hist_df.sort_values(by='analogue_distance').head(max_matches)

        horizons = [1, 3, 5, 10, 20]
        stats_by_horizon = {}

        close_series = stock_df['close']

        for h in horizons:
            fwd_returns = []
            for match_idx in matches.index:
                if match_idx + h < len(stock_df):
                    ret = (close_series.iloc[match_idx + h] - close_series.iloc[match_idx]) / close_series.iloc[match_idx]
                    fwd_returns.append(ret)

            if fwd_returns:
                arr = np.array(fwd_returns)
                mean_ret = float(np.mean(arr))
                med_ret = float(np.median(arr))
                pos_prob = float(np.mean(arr > 0))
                neg_prob = float(np.mean(arr < 0))
                max_gain = float(np.max(arr))
                max_loss = float(np.min(arr))
                fwd_vol = float(np.std(arr))

                stats_by_horizon[f"{h}d"] = {
                    "horizon_days": h,
                    "avg_forward_return_pct": round(mean_ret * 100, 2),
                    "median_forward_return_pct": round(med_ret * 100, 2),
                    "win_rate_pct": round(pos_prob * 100, 2),
                    "loss_rate_pct": round(neg_prob * 100, 2),
                    "max_gain_pct": round(max_gain * 100, 2),
                    "max_loss_pct": round(max_loss * 100, 2),
                    "forward_volatility_pct": round(fwd_vol * 100, 2)
                }

        return {
            "observations_count": len(matches),
            "match_criteria": "RSI 14, 20D Volatility, and 20 DMA Distance Euclidean Similarity",
            "horizons": stats_by_horizon
        }
