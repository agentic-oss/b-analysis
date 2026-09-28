import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional

class HistoricalAnalogueEngine:
    """Finds historical analogues matching current technical/volatility/volume setup and computes forward empirical probabilities."""

    @staticmethod
    def find_analogues_and_forward_returns(
        df_stock: pd.DataFrame,
        horizons: List[int] = [1, 3, 5, 10, 20],
        rsi_window: float = 7.0,
        vol_window: float = 0.08,
        rel_vol_window: float = 0.5
    ) -> Dict[str, Any]:
        """
        Scans historical observations for a stock to find days with similar setups:
        - Similar RSI (+/- rsi_window)
        - Similar 20-day volatility (+/- vol_window)
        - Similar relative volume (+/- rel_vol_window)

        Calculates empirical forward return statistics over 1D, 3D, 5D, 10D, 20D horizons.
        """
        if df_stock.empty or len(df_stock) < 50:
            return {
                "historical_matches_count": 0,
                "horizons": {},
                "explanation": "Insufficient historical data for analogue matching"
            }

        df = df_stock.sort_values('date').copy().reset_index(drop=True)
        latest = df.iloc[-1]

        curr_rsi = float(latest.get('rsi_14', 50.0))
        curr_vol = float(latest.get('volatility_20d', 0.20))
        curr_rel_vol = float(latest.get('relative_volume', 1.0))

        # We exclude recent rows that don't have full forward lookahead for evaluation
        max_h = max(horizons)
        search_space = df.iloc[:-max_h].copy() if len(df) > max_h else pd.DataFrame()

        if search_space.empty:
            return {
                "historical_matches_count": 0,
                "horizons": {},
                "explanation": "Not enough history prior to recent lookahead horizon"
            }

        # Filter analogue rows
        matches_mask = (
            (search_space['rsi_14'] >= curr_rsi - rsi_window) & (search_space['rsi_14'] <= curr_rsi + rsi_window) &
            (search_space['volatility_20d'] >= curr_vol - vol_window) & (search_space['volatility_20d'] <= curr_vol + vol_window) &
            (search_space['relative_volume'] >= curr_rel_vol - rel_vol_window) & (search_space['relative_volume'] <= curr_rel_vol + rel_vol_window)
        )

        match_indices = search_space[matches_mask].index.tolist()

        if len(match_indices) < 3:
            # Fallback to looser criteria if too few matches
            matches_mask = (
                (search_space['rsi_14'] >= curr_rsi - (rsi_window * 1.8)) & (search_space['rsi_14'] <= curr_rsi + (rsi_window * 1.8))
            )
            match_indices = search_space[matches_mask].index.tolist()

        horizon_stats = {}
        for h in horizons:
            fwd_returns = []
            for idx in match_indices:
                if idx + h < len(df):
                    price_curr = df.iloc[idx]['close']
                    price_fwd = df.iloc[idx + h]['close']
                    ret = (price_fwd - price_curr) / price_curr
                    fwd_returns.append(ret)

            if fwd_returns:
                returns_arr = np.array(fwd_returns)
                win_prob = float(np.mean(returns_arr > 0))
                loss_prob = float(np.mean(returns_arr < 0))

                horizon_stats[f"{h}d"] = {
                    "observations": len(fwd_returns),
                    "mean_forward_return": round(float(np.mean(returns_arr)) * 100.0, 2),
                    "median_forward_return": round(float(np.median(returns_arr)) * 100.0, 2),
                    "win_probability": round(win_prob * 100.0, 1),
                    "loss_probability": round(loss_prob * 100.0, 1),
                    "max_gain": round(float(np.max(returns_arr)) * 100.0, 2),
                    "max_loss": round(float(np.min(returns_arr)) * 100.0, 2),
                    "std_dev": round(float(np.std(returns_arr)) * 100.0, 2)
                }

        return {
            "historical_matches_count": len(match_indices),
            "matched_setup": {
                "rsi_14": round(curr_rsi, 2),
                "volatility_20d": round(curr_vol, 4),
                "relative_volume": round(curr_rel_vol, 2)
            },
            "horizons": horizon_stats
        }
