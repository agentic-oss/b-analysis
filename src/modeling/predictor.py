"""
Future Movement Signals & Baseline Machine Learning Models module.
Generates probabilistic forward-looking signals and provides walk-forward ML models (Random Forest / Logistic Regression) with temporal validation.
"""
import logging
from typing import Dict, Any, List, Tuple
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

logger = logging.getLogger(__name__)


class PredictorModule:
    """
    Generates probabilistic forward-looking signals and baseline predictive ML metrics.
    """

    @staticmethod
    def generate_forward_signals(
        composite_score: float,
        analogue_stats: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Synthesizes composite stock score and historical analogue probabilities to derive directional bias and confidence.
        Explicitly treats outputs as probabilistic estimates, not guarantees.
        """
        fwd_stats = analogue_stats.get("forward_statistics", {})
        signals = {}

        horizons_map = {
            "1d": "1-day directional bias",
            "3d": "3-day directional bias",
            "5d": "5-day directional bias",
            "10d": "10-day directional bias",
            "20d": "20-day directional bias"
        }

        for h_key, h_label in horizons_map.items():
            h_stat = fwd_stats.get(h_key, {})
            win_rate = h_stat.get("win_rate_pct", 50.0)

            # Combined implied bullish probability (60% analogue win rate + 40% composite score)
            implied_prob = (0.6 * win_rate) + (0.4 * composite_score)
            implied_prob = float(np.clip(implied_prob, 0.0, 100.0))

            # Directional Label
            if implied_prob >= 65.0:
                bias = "Bullish"
            elif implied_prob >= 55.0:
                bias = "Slightly Bullish"
            elif implied_prob <= 35.0:
                bias = "Bearish"
            elif implied_prob <= 45.0:
                bias = "Slightly Bearish"
            else:
                bias = "Neutral"

            # Confidence score (distance from 50% threshold)
            confidence = int(min(100, round(50 + abs(implied_prob - 50) * 1.6)))

            signals[h_key] = {
                "horizon": h_label,
                "directional_bias": bias,
                "confidence_score": confidence,
                "implied_bullish_probability_pct": round(implied_prob, 2),
                "historical_win_rate_pct": win_rate
            }

        return signals

    @staticmethod
    def train_and_evaluate_walk_forward(
        df: pd.DataFrame,
        feature_cols: List[str],
        target_col: str = "future_return_5d"
    ) -> Dict[str, Any]:
        """
        Walk-forward temporal train/test split model evaluation without random shuffling (preventing data leakage).
        """
        if df.empty or len(df) < 100:
            return {
                "model_type": "RandomForestClassifier",
                "status": "Insufficient data for temporal train/test split",
                "metrics": {}
            }

        clean_df = df.dropna(subset=feature_cols + [target_col]).copy()
        if len(clean_df) < 60:
            return {
                "model_type": "RandomForestClassifier",
                "status": "Insufficient clean samples",
                "metrics": {}
            }

        # Create binary target (1 if positive forward return, 0 otherwise)
        y = (clean_df[target_col] > 0).astype(int)
        X = clean_df[feature_cols]

        # Chronological Split (80% train, 20% test)
        split_idx = int(len(X) * 0.8)
        X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
        y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]

        if len(X_test) == 0 or len(y_train.unique()) < 2:
            return {
                "model_type": "RandomForestClassifier",
                "status": "Invalid train/test class distribution",
                "metrics": {}
            }

        model = RandomForestClassifier(n_estimators=50, max_depth=4, random_state=42)
        model.fit(X_train, y_train)

        y_pred = model.predict(X_test)

        acc = float(accuracy_score(y_test, y_pred))
        prec = float(precision_score(y_test, y_pred, zero_division=0))
        rec = float(recall_score(y_test, y_pred, zero_division=0))
        f1 = float(f1_score(y_test, y_pred, zero_division=0))

        return {
            "model_type": "RandomForestClassifier",
            "validation_strategy": "Chronological Walk-Forward Split (80/20)",
            "train_samples": len(X_train),
            "test_samples": len(X_test),
            "metrics": {
                "accuracy": round(acc, 4),
                "precision": round(prec, 4),
                "recall": round(rec, 4),
                "f1_score": round(f1, 4),
                "directional_accuracy_pct": round(acc * 100, 2)
            }
        }
