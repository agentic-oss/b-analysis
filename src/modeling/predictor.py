import numpy as np
import pandas as pd
from typing import Dict, Any, Tuple
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, mean_absolute_error, mean_squared_error
from src.features.feature_builder import FeatureBuilder

class BaselinePredictor:
    """
    ML Prediction research layer using strict time-series walk-forward evaluation (no random shuffling).
    Implements baseline models (Historical Probabilities, Logistic Regression, Random Forest).
    """

    @staticmethod
    def train_and_evaluate_walk_forward(df_features: pd.DataFrame, target_horizon: str = "future_return_5d") -> Dict[str, Any]:
        """
        Walk-forward temporal train/test split evaluation.
        """
        feat_cols = FeatureBuilder.get_feature_column_names()

        # Keep only rows where both features and target are non-null
        cols_needed = [c for c in feat_cols if c in df_features.columns] + [target_horizon]
        clean_df = df_features.dropna(subset=cols_needed).copy()

        if len(clean_df) < 50:
            return {
                "model_name": "RandomForestClassifier",
                "target": target_horizon,
                "status": "Insufficient samples for walk-forward evaluation",
                "metrics": {}
            }

        # Features X and binary target y (1 if forward return > 0 else 0)
        X = clean_df[cols_needed[:-1]].values
        y = (clean_df[target_horizon] > 0).astype(int).values

        # Time-series split: First 70% train, last 30% test (walk-forward test)
        split_idx = int(len(clean_df) * 0.70)
        X_train, X_test = X[:split_idx], X[split_idx:]
        y_train, y_test = y[:split_idx], y[split_idx:]

        if len(np.unique(y_train)) < 2 or len(np.unique(y_test)) < 2:
            return {
                "model_name": "RandomForestClassifier",
                "target": target_horizon,
                "status": "Single class target in split window",
                "metrics": {}
            }

        model = RandomForestClassifier(n_estimators=50, max_depth=5, random_state=42)
        model.fit(X_train, y_train)

        preds = model.predict(X_test)
        preds_proba = model.predict_proba(X_test)[:, 1]

        acc = float(accuracy_score(y_test, preds))
        prec = float(precision_score(y_test, preds, zero_division=0))
        rec = float(recall_score(y_test, preds, zero_division=0))
        f1 = float(f1_score(y_test, preds, zero_division=0))

        # Directional accuracy
        dir_acc = float(np.mean(preds == y_test))

        return {
            "model_name": "RandomForestClassifier",
            "target": target_horizon,
            "train_samples": len(X_train),
            "test_samples": len(X_test),
            "metrics": {
                "accuracy": round(acc, 4),
                "precision": round(prec, 4),
                "recall": round(rec, 4),
                "f1_score": round(f1, 4),
                "directional_accuracy": round(dir_acc, 4)
            },
            "limitations": "Trained on technical feature set; probabilistic research metric only."
        }
