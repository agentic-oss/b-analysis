import numpy as np
import pandas as pd
from typing import Dict, Any, List, Tuple
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score


class BaselineMLModels:
    """Baseline Machine Learning models for stock direction prediction using walk-forward validation."""

    def __init__(self, model_type: str = "random_forest"):
        self.model_type = model_type
        if model_type == "logistic_regression":
            self.model = LogisticRegression(max_iter=1000)
        elif model_type == "gradient_boosting":
            self.model = GradientBoostingClassifier(n_estimators=100, random_state=42)
        else: # Default Random Forest
            self.model = RandomForestClassifier(n_estimators=100, random_state=42)

    def train_walk_forward(
        self,
        features_df: pd.DataFrame,
        feature_cols: List[str],
        target_col: str = "future_return_5d",
        min_train_size: int = 100,
        test_size: int = 20
    ) -> Dict[str, Any]:
        """
        Executes Walk-Forward (Time-Series Split) evaluation without random shuffling or look-ahead bias.
        Target is binary: 1 if future return > 0 else 0.
        """
        df = features_df.dropna(subset=feature_cols + [target_col]).copy()
        if len(df) < min_train_size + test_size:
            return {"error": "Insufficient samples for walk-forward evaluation"}

        # Binary direction target
        df['target_binary'] = (df[target_col] > 0).astype(int)

        y_true_all = []
        y_pred_all = []
        y_prob_all = []

        # Walk forward iteration
        start_idx = min_train_size
        while start_idx + test_size <= len(df):
            train_data = df.iloc[:start_idx]
            test_data = df.iloc[start_idx : start_idx + test_size]

            X_train = train_data[feature_cols]
            y_train = train_data['target_binary']

            X_test = test_data[feature_cols]
            y_test = test_data['target_binary']

            # Fit model on historical fold
            self.model.fit(X_train, y_train)

            preds = self.model.predict(X_test)
            probs = self.model.predict_proba(X_test)[:, 1] if hasattr(self.model, "predict_proba") else preds

            y_true_all.extend(y_test.values)
            y_pred_all.extend(preds)
            y_prob_all.extend(probs)

            start_idx += test_size

        if not y_true_all:
            return {"error": "No folds evaluated"}

        y_true = np.array(y_true_all)
        y_pred = np.array(y_pred_all)
        y_prob = np.array(y_prob_all)

        acc = accuracy_score(y_true, y_pred)
        prec = precision_score(y_true, y_pred, zero_division=0)
        rec = recall_score(y_true, y_pred, zero_division=0)
        f1 = f1_score(y_true, y_pred, zero_division=0)

        try:
            auc = roc_auc_score(y_true, y_prob)
        except Exception:
            auc = 0.5

        return {
            "model_type": self.model_type,
            "target": target_col,
            "samples_evaluated": len(y_true),
            "accuracy": float(round(acc, 4)),
            "precision": float(round(prec, 4)),
            "recall": float(round(rec, 4)),
            "f1_score": float(round(f1, 4)),
            "roc_auc": float(round(auc, 4))
        }
