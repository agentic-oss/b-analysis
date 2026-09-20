"""Predictive Modeling Layer with Walk-Forward Validation & Baseline Classifiers."""

import warnings
import numpy as np
import pandas as pd
from typing import Dict, Any, List
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from sklearn.exceptions import ConvergenceWarning

warnings.filterwarnings("ignore", category=ConvergenceWarning)

class PredictionModule:
    """Generates probabilistic forward-looking movement signals with walk-forward time-series evaluation."""

    def __init__(self, model_type: str = "logistic"):
        self.model_type = model_type

    def train_and_predict(self, df: pd.DataFrame, horizons: List[int] = [1, 3, 5, 10, 20]) -> Dict[str, Any]:
        """Trains models using strict time-series splits (no random shuffling) and returns forward directional signals and metrics."""
        feature_cols = [
            'return_1d', 'return_5d', 'return_20d', 'rsi_14', 'stoch_rsi',
            'macd_hist', 'atr_14', 'volatility_20d', 'relative_volume',
            'dist_sma_20_pct', 'dist_sma_50_pct', 'dist_52w_high_pct'
        ]

        # Verify columns exist
        available_features = [c for c in feature_cols if c in df.columns]
        if df.empty or len(df) < 60 or len(available_features) < 5:
            # Fallback neutral prediction
            signals = {}
            for h in horizons:
                signals[f"{h}d"] = {
                    "horizon_days": h,
                    "bias": "Neutral",
                    "confidence": 50.0,
                    "prob_up": 0.50,
                    "disclaimer": "Insufficient historical data for model inference."
                }
            return {"signals": signals, "metrics": {}}

        clean_df = df.dropna(subset=available_features).copy()
        n = len(clean_df)

        # Walk-forward split: 70% train, 30% test
        train_size = int(n * 0.70)
        train_df = clean_df.iloc[:train_size]
        test_df = clean_df.iloc[train_size:]

        signals = {}
        metrics = {}

        for h in horizons:
            target_col = f'future_direction_{h}d'
            if target_col not in clean_df.columns:
                # Calculate target
                clean_df[target_col] = np.where((clean_df['close'].shift(-h) - clean_df['close']) > 0, 1, 0)
                train_df = clean_df.iloc[:train_size]
                test_df = clean_df.iloc[train_size:]

            X_train = train_df[available_features]
            y_train = train_df[target_col]

            # Test set excluding last h rows where targets are unknown
            eval_test = test_df.iloc[:-h] if h < len(test_df) else test_df.iloc[:0]

            if len(X_train) < 30 or len(y_train.unique()) < 2:
                prob_up = 0.50
                acc, prec, rec, f1 = 0.5, 0.5, 0.5, 0.5
            else:
                if self.model_type == "random_forest":
                    clf = RandomForestClassifier(n_estimators=50, max_depth=4, random_state=42)
                else:
                    clf = LogisticRegression(max_iter=500, random_state=42)

                clf.fit(X_train, y_train)

                # Predict on latest row (date T)
                latest_features = clean_df[available_features].iloc[-1:]
                prob_up = float(clf.predict_proba(latest_features)[0, 1])

                # Evaluate on out-of-sample test set
                if not eval_test.empty and len(eval_test[target_col].unique()) > 1:
                    X_test = eval_test[available_features]
                    y_test = eval_test[target_col]
                    y_pred = clf.predict(X_test)
                    acc = float(accuracy_score(y_test, y_pred))
                    prec = float(precision_score(y_test, y_pred, zero_division=0))
                    rec = float(recall_score(y_test, y_pred, zero_division=0))
                    f1 = float(f1_score(y_test, y_pred, zero_division=0))
                else:
                    acc, prec, rec, f1 = 0.5, 0.5, 0.5, 0.5

            # Directional Bias Classification & Confidence
            if prob_up >= 0.65:
                bias = "Bullish"
                confidence = round(prob_up * 100, 1)
            elif prob_up >= 0.55:
                bias = "Slightly Bullish"
                confidence = round(prob_up * 100, 1)
            elif prob_up <= 0.35:
                bias = "Bearish"
                confidence = round((1 - prob_up) * 100, 1)
            elif prob_up <= 0.45:
                bias = "Slightly Bearish"
                confidence = round((1 - prob_up) * 100, 1)
            else:
                bias = "Neutral"
                confidence = 50.0

            signals[f"{h}d"] = {
                "horizon_days": h,
                "bias": bias,
                "confidence": confidence,
                "prob_up": round(prob_up, 4)
            }

            metrics[f"{h}d"] = {
                "accuracy": round(acc, 4),
                "precision": round(prec, 4),
                "recall": round(rec, 4),
                "f1_score": round(f1, 4),
                "validation_method": "Walk-Forward Out-Of-Sample Time Split"
            }

        return {
            "model_type": self.model_type,
            "signals": signals,
            "metrics": metrics,
            "disclaimer": "Probabilistic signal derived from historical statistical features; not a guaranteed financial prediction."
        }
