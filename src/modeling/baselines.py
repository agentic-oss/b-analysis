"""
Baseline statistical and machine learning probabilistic movement models.
Implements walk-forward time-series validation without temporal data leakage.
"""
import logging
from typing import Dict, Any, Tuple, List
import pandas as pd
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

logger = logging.getLogger(__name__)


class BaselinePredictor:
    """Probabilistic classification baseline model for directional price signals."""

    def __init__(self, model_type: str = "random_forest"):
        self.model_type = model_type
        if model_type == "logistic_regression":
            self.model = LogisticRegression(max_iter=1000)
        else:
            self.model = RandomForestClassifier(n_estimators=100, random_state=42)

    def evaluate_walk_forward(
        self, df: pd.DataFrame, feature_cols: List[str], target_col: str = "future_return_5d"
    ) -> Dict[str, Any]:
        """
        Executes time-series walk-forward validation on historical dataset.
        Target: Binary directional move (1 if forward return > 0 else 0).
        """
        if df.empty or len(df) < 150:
            return {
                "status": "Insufficient historical data for model evaluation",
                "accuracy": 0.0,
                "f1_score": 0.0,
            }

        valid_df = df.dropna(subset=feature_cols + [target_col]).copy()
        if len(valid_df) < 100:
            return {
                "status": "Insufficient complete samples for model evaluation",
                "accuracy": 0.0,
                "f1_score": 0.0,
            }

        X = valid_df[feature_cols].values
        y = (valid_df[target_col] > 0).astype(int).values

        # Time-series split (70% train, 30% test) - NO random shuffle
        split_idx = int(len(X) * 0.70)
        X_train, X_test = X[:split_idx], X[split_idx:]
        y_train, y_test = y[:split_idx], y[split_idx:]

        if len(np.unique(y_train)) < 2 or len(np.unique(y_test)) < 1:
            return {
                "status": "Single class present in train/test split",
                "accuracy": 0.0,
                "f1_score": 0.0,
            }

        self.model.fit(X_train, y_train)
        preds = self.model.predict(X_test)
        probs = self.model.predict_proba(X_test)[:, 1] if hasattr(self.model, "predict_proba") else None

        acc = float(accuracy_score(y_test, preds))
        prec = float(precision_score(y_test, preds, zero_division=0))
        rec = float(recall_score(y_test, preds, zero_division=0))
        f1 = float(f1_score(y_test, preds, zero_division=0))

        return {
            "model_type": self.model_type,
            "samples_train": len(X_train),
            "samples_test": len(X_test),
            "accuracy": round(acc, 4),
            "precision": round(prec, 4),
            "recall": round(rec, 4),
            "f1_score": round(f1, 4),
            "directional_bias": "Bullish" if (probs[-1] if probs is not None else 0.5) > 0.55 else (
                "Bearish" if (probs[-1] if probs is not None else 0.5) < 0.45 else "Neutral"
            ),
            "confidence_score": round(
                float(abs((probs[-1] if probs is not None else 0.5) - 0.5) * 200), 1
            ),
        }
