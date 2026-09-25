"""Probabilistic Predictive Modeling Module."""

import logging
from typing import Dict, List, Any, Optional, Tuple
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score, mean_absolute_error
from sklearn.model_selection import TimeSeriesSplit

logger = logging.getLogger(__name__)


class ProbabilisticPredictor:
    """Trains probabilistic baseline statistical/ML models using TimeSeriesSplit validation.

    Generates directional probabilities (Bullish/Bearish/Neutral) and confidence scores.
    """

    def __init__(self, model_type: str = "random_forest"):
        self.model_type = model_type
        self.feature_cols = [
            "return_1d", "return_5d", "return_20d",
            "rsi_14", "stoch_rsi", "macd", "macd_hist",
            "atr_14", "volatility_20d", "relative_volume",
            "dist_52w_high_pct", "dist_52w_low_pct"
        ]

    def _get_model(self):
        if self.model_type == "logistic_regression":
            return LogisticRegression(max_iter=1000, random_state=42)
        return RandomForestClassifier(n_estimators=100, max_depth=5, random_state=42)

    def train_and_evaluate(
        self,
        feature_df: pd.DataFrame,
        horizon_days: int = 5
    ) -> Dict[str, Any]:
        """Train model using walk-forward TimeSeriesSplit and return out-of-sample metrics."""
        target_col = f"future_return_{horizon_days}d"

        if feature_df.empty or target_col not in feature_df.columns:
            return {"status": "error", "message": f"Missing target column {target_col}"}

        clean_df = feature_df.dropna(subset=self.feature_cols + [target_col]).copy()
        if len(clean_df) < 100:
            return {"status": "error", "message": "Insufficient clean samples (<100) for ML training"}

        X = clean_df[self.feature_cols].values
        # Classify target: 1 if positive return, 0 if negative return
        y = (clean_df[target_col].values > 0).astype(int)

        tscv = TimeSeriesSplit(n_splits=5)
        accuracy_scores = []
        f1_scores = []

        for train_idx, test_idx in tscv.split(X):
            X_train, X_test = X[train_idx], X[test_idx]
            y_train, y_test = y[train_idx], y[test_idx]

            model = self._get_model()
            model.fit(X_train, y_train)
            preds = model.predict(X_test)

            accuracy_scores.append(accuracy_score(y_test, preds))
            f1_scores.append(f1_score(y_test, preds, zero_division=0))

        # Fit final model on full historical dataset
        final_model = self._get_model()
        final_model.fit(X, y)

        return {
            "status": "success",
            "horizon_days": horizon_days,
            "samples": len(clean_df),
            "out_of_sample_accuracy": round(float(np.mean(accuracy_scores)), 4),
            "out_of_sample_f1": round(float(np.mean(f1_scores)), 4),
            "final_model": final_model
        }

    def predict_forward_signals(
        self,
        latest_features: Dict[str, Any],
        historical_analogue_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Combine empirical analogue stats and model predictions into probabilistic forward signals."""
        horizons = [1, 3, 5, 10, 20]
        predictions = {}

        analogues = historical_analogue_data.get("horizons", {})

        for h in horizons:
            h_key = f"{h}d"
            a_data = analogues.get(h_key, {})
            win_rate = a_data.get("win_rate_pct", 50.0)
            avg_ret = a_data.get("avg_forward_return", 0.0)

            # Combine win rate and expected return into directional bias label
            if win_rate >= 65.0 and avg_ret > 0.5:
                bias = "Bullish"
                confidence = min(100, int(win_rate))
            elif win_rate >= 55.0 and avg_ret > 0.1:
                bias = "Slightly Bullish"
                confidence = int(win_rate)
            elif win_rate <= 35.0 and avg_ret < -0.5:
                bias = "Bearish"
                confidence = min(100, int(100 - win_rate))
            elif win_rate <= 45.0 and avg_ret < -0.1:
                bias = "Slightly Bearish"
                confidence = int(100 - win_rate)
            else:
                bias = "Neutral"
                confidence = 50

            predictions[h_key] = {
                "horizon_days": h,
                "directional_bias": bias,
                "confidence": confidence,
                "empirical_win_rate_pct": win_rate,
                "avg_expected_return_pct": avg_ret,
                "sample_count": a_data.get("sample_count", 0)
            }

        return predictions
