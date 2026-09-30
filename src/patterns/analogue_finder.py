import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional

class AnalogueFinder:
    """
    Identifies historical market situations statistically similar to current market state
    and calculates forward performance (1D, 3D, 5D, 10D, 20D) to construct empirical forward probability distributions.
    """

    def __init__(self, rsi_tolerance: float = 7.5, volatility_tolerance: float = 0.10, top_k: int = 30):
        self.rsi_tolerance = rsi_tolerance
        self.volatility_tolerance = volatility_tolerance
        self.top_k = top_k

    def find_analogues(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Calculates historical analogues for a single stock history.
        `df` must contain date, close, rsi_14, volatility_20d, dist_sma_20, dist_sma_50, relative_volume, daily_return.
        """
        horizons = [1, 3, 5, 10, 20]
        empty_res = {
            "num_matches": 0,
            "horizons": {f"{h}d": {"avg_return": 0.0, "median_return": 0.0, "positive_prob": 0.0, "negative_prob": 0.0, "max_gain": 0.0, "max_loss": 0.0, "volatility": 0.0} for h in horizons}
        }

        if df.empty or len(df) < 100:
            return empty_res

        df = df.copy().reset_index(drop=True)
        latest = df.iloc[-1]

        # Calculate future forward returns for historical rows
        for h in horizons:
            df[f'fwd_ret_{h}d'] = (df['close'].shift(-h) - df['close']) / df['close']

        # Historical candidate rows (exclude current row and rows without required forward window)
        # Prevent look-ahead leakage by excluding recent rows where forward returns are not yet known
        max_h = max(horizons)
        candidates = df.iloc[:-max_h].copy()

        if candidates.empty:
            return empty_res

        # Filter candidates based on technical similarity matching (RSI, Volatility, SMA distance)
        curr_rsi = latest.get('rsi_14', 50.0)
        curr_vol = latest.get('volatility_20d', 0.20)
        curr_dist_20 = latest.get('dist_sma_20', 0.0)

        matches = candidates[
            (candidates['rsi_14'].between(curr_rsi - self.rsi_tolerance, curr_rsi + self.rsi_tolerance)) &
            (candidates['volatility_20d'].between(curr_vol - self.volatility_tolerance, curr_vol + self.volatility_tolerance)) &
            (candidates['dist_sma_20'].between(curr_dist_20 - 0.05, curr_dist_20 + 0.05))
        ]

        if len(matches) < 5:
            # Fall back to broader RSI & distance match if too few matches
            matches = candidates[
                (candidates['rsi_14'].between(curr_rsi - 15.0, curr_rsi + 15.0))
            ]

        if matches.empty:
            return empty_res

        # Select top K closest historical instances
        dist = (
            ((matches['rsi_14'] - curr_rsi) / 100.0) ** 2 +
            ((matches['volatility_20d'] - curr_vol) / (curr_vol + 1e-5)) ** 2 +
            ((matches['dist_sma_20'] - curr_dist_20)) ** 2
        )
        matches = matches.assign(dist=dist).sort_values('dist').head(self.top_k)

        num_matches = len(matches)
        horizon_stats = {}

        for h in horizons:
            col = f'fwd_ret_{h}d'
            returns = matches[col].dropna()
            if len(returns) == 0:
                horizon_stats[f"{h}d"] = {
                    "avg_return": 0.0,
                    "median_return": 0.0,
                    "positive_prob": 0.0,
                    "negative_prob": 0.0,
                    "max_gain": 0.0,
                    "max_loss": 0.0,
                    "volatility": 0.0
                }
            else:
                avg_ret = float(returns.mean())
                med_ret = float(returns.median())
                pos_prob = float((returns > 0).mean())
                neg_prob = float((returns < 0).mean())
                max_gain = float(returns.max())
                max_loss = float(returns.min())
                vol = float(returns.std()) if len(returns) > 1 else 0.0

                horizon_stats[f"{h}d"] = {
                    "avg_return": round(avg_ret, 4),
                    "median_return": round(med_ret, 4),
                    "positive_prob": round(pos_prob, 4),
                    "negative_prob": round(neg_prob, 4),
                    "max_gain": round(max_gain, 4),
                    "max_loss": round(max_loss, 4),
                    "volatility": round(vol, 4)
                }

        return {
            "num_matches": num_matches,
            "horizons": horizon_stats
        }
