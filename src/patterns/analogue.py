import numpy as np
import pandas as pd
from typing import Dict, Any, List

class PatternAnalogueFinder:
    """Finds historical market setups similar to the current state and computes forward outcome statistics."""

    def __init__(self, top_k: int = 25, distance_threshold: float = 2.5):
        self.top_k = top_k
        self.distance_threshold = distance_threshold

    def find_analogues(self, df: pd.DataFrame, horizons: List[int] = [1, 3, 5, 10, 20]) -> Dict[str, Any]:
        """
        Finds historical analogue bars and calculates empirical forward stats.
        """
        if df.empty or len(df) < 60:
            return {
                "observations": 0,
                "horizons": {f"{h}d": {} for h in horizons}
            }

        df = df.copy().reset_index(drop=True)

        # Features to compare: RSI 14, dist_sma_20, relative_volume, 5d return, volatility_20d
        feature_cols = ['rsi_14', 'dist_sma_20', 'relative_volume', 'volatility_20d']
        for col in feature_cols:
            if col not in df.columns:
                df[col] = 0.0

        # Calculate 5d return feature if missing
        df['ret_5d'] = df['close'].pct_change(5).fillna(0.0)
        cols_to_norm = feature_cols + ['ret_5d']

        # Normalize features (z-score)
        norm_df = (df[cols_to_norm] - df[cols_to_norm].mean()) / (df[cols_to_norm].std().replace(0, 1))

        current_vector = norm_df.iloc[-1].values

        # Candidate historical indices (must be at least max horizon away from end, and not in recent 20 bars)
        max_h = max(horizons)
        max_idx = len(df) - max_h - 1

        if max_idx < 30:
            return {
                "observations": 0,
                "horizons": {f"{h}d": {} for h in horizons}
            }

        hist_vectors = norm_df.iloc[20:max_idx].values
        distances = np.linalg.norm(hist_vectors - current_vector, axis=1)

        # Find top_k closest matches
        sorted_indices = np.argsort(distances)
        top_matches = sorted_indices[:self.top_k]

        # Adjust index shift back to original df
        match_df_indices = top_matches + 20

        stats = {"observations": len(match_df_indices), "horizons": {}}

        for h in horizons:
            fwd_returns = []
            for idx in match_df_indices:
                if idx + h < len(df):
                    ret = (df['close'].iloc[idx + h] - df['close'].iloc[idx]) / df['close'].iloc[idx]
                    fwd_returns.append(ret)

            if fwd_returns:
                arr = np.array(fwd_returns) * 100.0 # Convert to percentage
                stats["horizons"][f"{h}d"] = {
                    "avg_return": float(round(np.mean(arr), 2)),
                    "median_return": float(round(np.median(arr), 2)),
                    "win_rate": float(round(np.mean(arr > 0), 2)),
                    "loss_rate": float(round(np.mean(arr < 0), 2)),
                    "max_gain": float(round(np.max(arr), 2)),
                    "max_loss": float(round(np.min(arr), 2)),
                    "forward_std": float(round(np.std(arr), 2))
                }
            else:
                stats["horizons"][f"{h}d"] = {}

        return stats
