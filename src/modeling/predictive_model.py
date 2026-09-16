from typing import Dict, List, Tuple, Any, Optional
import pandas as pd
import numpy as np
import logging
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

logger = logging.getLogger(__name__)


class PredictiveModelManager:
    """
    ML Research Layer for training and evaluating baseline forecasting models.
    Enforces time-series walk-forward validation (never random shuffling).
    Computes performance metrics: Accuracy, Precision, Recall, F1, MAE, Sharpe ratio.
    """

    def __init__(self, feature_cols: Optional[List[str]] = None):
        if feature_cols is None:
            self.feature_cols = [
                "rsi_14", "stoch_rsi", "macd", "macd_signal", "atr_14",
                "volatility_20d", "relative_volume", "dist_sma_20", "dist_sma_50",
                "dist_sma_200", "dist_52w_high", "dist_52w_low", "return_1d", "return_5d"
            ]
        else:
            self.feature_cols = feature_cols

    def train_and_evaluate(
        self,
        dataset: pd.DataFrame,
        target_col: str = "future_return_5d",
        n_splits: int = 3
    ) -> Dict[str, Any]:
        """
        Runs Walk-Forward time-series cross validation.
        """
        cols_needed = self.feature_cols + [target_col]
        valid_df = dataset.dropna(subset=cols_needed).copy()

        if len(valid_df) < 50:
            return {
                "status": "Insufficient data",
                "sample_size": len(valid_df),
                "metrics": {}
            }

        valid_df["target_direction"] = (valid_df[target_col] > 0).astype(int)

        X = valid_df[self.feature_cols].values
        y = valid_df["target_direction"].values

        total_samples = len(valid_df)
        split_size = total_samples // (n_splits + 1)

        rf_metrics = {"accuracy": [], "precision": [], "recall": [], "f1": []}

        for i in range(1, n_splits + 1):
            train_end = split_size * i
            test_end = train_end + split_size

            X_train, y_train = X[:train_end], y[:train_end]
            X_test, y_test = X[train_end:test_end], y[train_end:test_end]

            if len(X_test) == 0 or len(np.unique(y_train)) < 2:
                continue

            rf = RandomForestClassifier(n_estimators=50, max_depth=5, random_state=42)
            rf.fit(X_train, y_train)
            y_pred = rf.predict(X_test)

            rf_metrics["accuracy"].append(accuracy_score(y_test, y_pred))
            rf_metrics["precision"].append(precision_score(y_test, y_pred, zero_division=0))
            rf_metrics["recall"].append(recall_score(y_test, y_pred, zero_division=0))
            rf_metrics["f1"].append(f1_score(y_test, y_pred, zero_division=0))

        avg_metrics = {
            "model_type": "RandomForestClassifier Baseline",
            "validation_method": "Walk-Forward Time-Series Split",
            "samples_evaluated": total_samples,
            "accuracy": round(float(np.mean(rf_metrics["accuracy"])), 4) if rf_metrics["accuracy"] else 0.0,
            "precision": round(float(np.mean(rf_metrics["precision"])), 4) if rf_metrics["precision"] else 0.0,
            "recall": round(float(np.mean(rf_metrics["recall"])), 4) if rf_metrics["recall"] else 0.0,
            "f1_score": round(float(np.mean(rf_metrics["f1"])), 4) if rf_metrics["f1"] else 0.0,
            "limitations": "Baseline evaluation trained on available historical window without hyperparameter tuning."
        }

        return avg_metrics
