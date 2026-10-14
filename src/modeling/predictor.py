import logging
from typing import Dict, Any, Tuple
import pandas as pd
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, mean_absolute_error, mean_squared_error

logger = logging.getLogger(__name__)

class PredictionModule:
    """
    Predictive modeling engine implementing baseline statistical and machine learning models
    using strict walk-forward / temporal time-series splitting (NO random shuffling).
    """

    def train_and_evaluate(self, feature_matrix: pd.DataFrame, target_horizon: str = "1d") -> Dict[str, Any]:
        """
        Trains statistical models (Logistic Regression, Random Forest) on time-series split
        to predict binary 1-day direction (positive vs negative return).
        """
        target_col = f"future_return_{target_horizon}"
        if feature_matrix.empty or target_col not in feature_matrix.columns:
            return {"status": "insufficient_data", "metrics": {}}

        # Clean non-null rows where target and key features exist
        df = feature_matrix.dropna(subset=[target_col, "rsi_14", "macd", "return_1d", "volatility_20d"]).copy()
        if len(df) < 60:
            return {"status": "insufficient_data", "sample_size": len(df)}

        df = df.sort_values("Date").reset_index(drop=True)

        feature_cols = [
            "return_1d", "return_5d", "return_20d", "rsi_14", "stoch_rsi",
            "macd", "macd_signal", "macd_hist", "atr_14", "volatility_20d",
            "relative_volume", "dist_sma_20", "dist_sma_50", "dist_sma_200"
        ]
        feature_cols = [c for c in feature_cols if c in df.columns]

        X = df[feature_cols].fillna(0)
        y = (df[target_col] > 0).astype(int)

        # Walk-forward time-series train/test split (80% train, 20% out-of-sample test)
        split_idx = int(len(X) * 0.8)
        X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
        y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]
        raw_y_test = df[target_col].iloc[split_idx:]

        if len(X_test) < 5 or y_train.nunique() < 2:
            return {"status": "insufficient_out_of_sample_data"}

        metrics = {}

        # 1. Historical Baseline (Always predicting majority class of train set)
        majority_class = y_train.mode()[0]
        base_preds = np.full_like(y_test, majority_class)
        metrics["historical_prob_baseline"] = {
            "accuracy": round(float(accuracy_score(y_test, base_preds)), 4),
            "sample_size": len(y_test)
        }

        # 2. Logistic Regression
        lr = LogisticRegression(max_iter=1000)
        lr.fit(X_train, y_train)
        lr_preds = lr.predict(X_test)
        metrics["logistic_regression"] = {
            "accuracy": round(float(accuracy_score(y_test, lr_preds)), 4),
            "precision": round(float(precision_score(y_test, lr_preds, zero_division=0)), 4),
            "recall": round(float(recall_score(y_test, lr_preds, zero_division=0)), 4),
            "f1": round(float(f1_score(y_test, lr_preds, zero_division=0)), 4)
        }

        # 3. Random Forest
        rf = RandomForestClassifier(n_estimators=50, random_state=42, max_depth=5)
        rf.fit(X_train, y_train)
        rf_preds = rf.predict(X_test)
        metrics["random_forest"] = {
            "accuracy": round(float(accuracy_score(y_test, rf_preds)), 4),
            "precision": round(float(precision_score(y_test, rf_preds, zero_division=0)), 4),
            "recall": round(float(recall_score(y_test, rf_preds, zero_division=0)), 4),
            "f1": round(float(f1_score(y_test, rf_preds, zero_division=0)), 4),
            "mae": round(float(mean_absolute_error(y_test, rf_preds)), 4),
            "rmse": round(float(np.sqrt(mean_squared_error(y_test, rf_preds))), 4)
        }

        return {
            "status": "success",
            "target_horizon": target_horizon,
            "train_samples": len(X_train),
            "test_samples": len(X_test),
            "metrics": metrics
        }
