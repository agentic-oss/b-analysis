import logging
from typing import Dict, Any, List, Tuple
import pandas as pd
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

logger = logging.getLogger(__name__)

class MarketPredictor:
    """Probabilistic prediction & baseline ML models using walk-forward validation."""

    def __init__(self, model_type: str = "random_forest"):
        self.model_type = model_type

    def train_evaluate_walk_forward(self, feature_df: pd.DataFrame, target_col: str = "target_direction_5d") -> Tuple[Any, Dict[str, Any]]:
        """Walk-forward time-series train/test evaluation without random shuffling."""
        if feature_df.empty or target_col not in feature_df.columns:
            return None, {}

        df = feature_df.dropna(subset=[target_col]).copy()
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        ignore_cols = [c for c in numeric_cols if c.startswith("future_") or c.startswith("target_")]
        feature_cols = [c for c in numeric_cols if c not in ignore_cols]

        if len(df) < 100 or len(feature_cols) == 0:
            return None, {"metrics": "Insufficient data"}

        df = df.dropna(subset=feature_cols)
        split_idx = int(len(df) * 0.8)

        train_df = df.iloc[:split_idx]
        test_df = df.iloc[split_idx:]

        X_train, y_train = train_df[feature_cols], train_df[target_col]
        X_test, y_test = test_df[feature_cols], test_df[target_col]

        if self.model_type == "logistic_regression":
            model = LogisticRegression(max_iter=500)
        else:
            model = RandomForestClassifier(n_estimators=50, max_depth=5, random_state=42)

        model.fit(X_train, y_train)
        preds = model.predict(X_test)
        probs = model.predict_proba(X_test)[:, 1] if hasattr(model, "predict_proba") else preds

        metrics = {
            "accuracy": round(float(accuracy_score(y_test, preds)), 4),
            "precision": round(float(precision_score(y_test, preds, zero_division=0)), 4),
            "recall": round(float(recall_score(y_test, preds, zero_division=0)), 4),
            "f1": round(float(f1_score(y_test, preds, zero_division=0)), 4),
            "train_samples": len(X_train),
            "test_samples": len(X_test)
        }

        return model, metrics

    @staticmethod
    def generate_directional_bias(analogues_stats: Dict[str, Any], ml_metrics: Dict[str, Any] = None) -> Dict[str, Any]:
        """Combines empirical analogue statistics and probabilistic signals into directional bias."""
        signals = {}
        for h in ["1d", "3d", "5d", "10d", "20d"]:
            stats = analogues_stats.get("forward_stats", {}).get(h, {})
            pos_prob = stats.get("positive_probability", 50.0)

            if pos_prob >= 65:
                bias = "Bullish"
            elif pos_prob >= 55:
                bias = "Slightly Bullish"
            elif pos_prob <= 35:
                bias = "Bearish"
            elif pos_prob <= 45:
                bias = "Slightly Bearish"
            else:
                bias = "Neutral"

            confidence = round(abs(pos_prob - 50) * 2, 1) + 50
            signals[h] = {
                "directional_bias": bias,
                "confidence": confidence,
                "historical_win_rate": pos_prob
            }

        return signals
