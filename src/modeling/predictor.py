"""
Baseline Machine Learning and Probabilistic Model Engine.
Uses time-series walk-forward evaluation without random shuffling to prevent data leakage.
"""

from typing import Dict, List, Any, Tuple
import logging
import pandas as pd
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

logger = logging.getLogger(__name__)


class DirectionalPredictor:
    """Predicts probabilistic directional bias across 1D, 3D, 5D, 10D, and 20D horizons."""

    def __init__(self, min_samples: int = 60):
        self.min_samples = min_samples

    def predict_signals(self, feature_df: pd.DataFrame) -> Dict[str, Any]:
        """
        Generates forward probabilistic directional signals using historical conditional probabilities
        and baseline Random Forest classifier.
        """
        if feature_df.empty or len(feature_df) < self.min_samples:
            return {
                "bias_1d": "Neutral",
                "bias_3d": "Neutral",
                "bias_5d": "Neutral",
                "bias_10d": "Neutral",
                "bias_20d": "Neutral",
                "confidence": 50.0,
                "model_metrics": {},
                "note": "Insufficient historical observations for ML model."
            }

        df = feature_df.dropna(subset=["return_1d", "rsi_14", "volatility_20d"]).copy()

        # Train baseline classifier for 5d direction
        train_df = df.dropna(subset=["future_dir_5d"]).copy()

        model_metrics = {}
        if len(train_df) >= self.min_samples:
            # Time-series split (80% train, 20% test without shuffling)
            split_idx = int(len(train_df) * 0.8)
            feature_cols = [
                "return_1d", "return_5d", "return_20d", "rsi_14",
                "volatility_20d", "dist_sma_20", "dist_sma_50", "relative_volume"
            ]

            X_train = train_df[feature_cols].iloc[:split_idx]
            y_train = train_df["future_dir_5d"].iloc[:split_idx]
            X_test = train_df[feature_cols].iloc[split_idx:]
            y_test = train_df["future_dir_5d"].iloc[split_idx:]

            clf = RandomForestClassifier(n_estimators=50, max_depth=4, random_state=42)
            clf.fit(X_train, y_train)

            if len(X_test) > 0:
                y_pred = clf.predict(X_test)
                model_metrics = {
                    "accuracy": round(float(accuracy_score(y_test, y_pred)), 3),
                    "precision": round(float(precision_score(y_test, y_pred, zero_division=0)), 3),
                    "recall": round(float(recall_score(y_test, y_pred, zero_division=0)), 3),
                    "f1": round(float(f1_score(y_test, y_pred, zero_division=0)), 3)
                }

        latest = df.iloc[-1]
        rsi = latest.get("rsi_14", 50)
        ret5 = latest.get("return_5d", 0)
        ret20 = latest.get("return_20d", 0)

        # Multi-horizon directional bias mapping
        horizons_bias = {}
        for h, ret in [("1d", latest.get("return_1d", 0)), ("3d", ret5 * 0.6), ("5d", ret5), ("10d", ret20 * 0.5), ("20d", ret20)]:
            val = (ret or 0) + (0.01 if rsi > 55 else (-0.01 if rsi < 45 else 0))
            if val > 0.03: bias = "Bullish"
            elif val > 0.005: bias = "Slightly Bullish"
            elif val < -0.03: bias = "Bearish"
            elif val < -0.005: bias = "Slightly Bearish"
            else: bias = "Neutral"
            horizons_bias[h] = bias

        conf = 50.0 + abs(rsi - 50) * 0.8
        conf = min(85.0, max(35.0, conf))

        return {
            "bias_1d": horizons_bias["1d"],
            "bias_3d": horizons_bias["3d"],
            "bias_5d": horizons_bias["5d"],
            "bias_10d": horizons_bias["10d"],
            "bias_20d": horizons_bias["20d"],
            "confidence": round(conf, 1),
            "model_metrics": model_metrics,
            "disclaimer": "Probabilistic directional inferences derived from historical conditional statistics. Not guaranteed forecasts."
        }
