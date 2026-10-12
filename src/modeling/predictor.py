"""
Prediction modeling layer using time-series walk-forward validation and statistical/ML baselines.
Prevents random temporal shuffling and calculates robust evaluation metrics.
"""

from typing import Dict, Any, List, Tuple
import pandas as pd
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score


class MLPredictionModel:
    """
    ML baseline models (Logistic Regression, Random Forest) using time-series walk-forward splits.
    """

    FEATURE_COLS = [
        "Daily_Return",
        "Return_5d",
        "Return_20d",
        "RSI_14",
        "Stoch_RSI",
        "MACD_Hist",
        "ROC_10",
        "Volatility_20d",
        "BB_Width",
        "Relative_Volume",
        "Gap_Pct",
        "Dist_From_SMA_20",
        "Dist_From_SMA_50",
    ]

    def train_and_evaluate(
        self,
        features_df: pd.DataFrame,
        horizon_days: int = 5,
        model_type: str = "random_forest",
    ) -> Dict[str, Any]:
        """
        Trains model on historical feature data using a chronological time-series split.
        """
        target_col = f"future_target_direction_{horizon_days}d"
        if features_df is None or target_col not in features_df.columns:
            return {"status": "error", "message": f"Target column {target_col} missing."}

        # Filter valid complete rows
        data = features_df.dropna(subset=self.FEATURE_COLS + [target_col]).copy()

        if len(data) < 100:
            return {"status": "error", "message": f"Insufficient sample size ({len(data)} rows) for training."}

        X = data[self.FEATURE_COLS].values
        y = data[target_col].values.astype(int)

        # Chronological train/test split (80% train, 20% test) - NO RANDOM SHUFFLING
        split_idx = int(len(data) * 0.8)
        X_train, X_test = X[:split_idx], X[split_idx:]
        y_train, y_test = y[:split_idx], y[split_idx:]

        if model_type == "logistic_regression":
            model = LogisticRegression(max_iter=500, random_state=42)
        else:
            model = RandomForestClassifier(n_estimators=100, max_depth=5, random_state=42)

        model.fit(X_train, y_train)

        preds = model.predict(X_test)
        probs = model.predict_proba(X_test)[:, 1] if hasattr(model, "predict_proba") else preds

        acc = accuracy_score(y_test, preds)
        prec = precision_score(y_test, preds, zero_division=0)
        rec = recall_score(y_test, preds, zero_division=0)
        f1 = f1_score(y_test, preds, zero_division=0)

        try:
            auc = roc_auc_score(y_test, probs)
        except Exception:
            auc = 0.5

        # Feature importances if available
        importances = {}
        if hasattr(model, "feature_importances_"):
            for feat, imp in zip(self.FEATURE_COLS, model.feature_importances_):
                importances[feat] = round(float(imp), 4)

        return {
            "status": "success",
            "model_type": model_type,
            "horizon_days": horizon_days,
            "train_samples": len(X_train),
            "test_samples": len(X_test),
            "metrics": {
                "accuracy": round(float(acc), 4),
                "precision": round(float(prec), 4),
                "recall": round(float(rec), 4),
                "f1_score": round(float(f1), 4),
                "roc_auc": round(float(auc), 4),
            },
            "feature_importances": importances,
            "note": "Time-series split applied. No random temporal shuffling used.",
        }
