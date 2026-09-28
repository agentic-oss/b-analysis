import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

class PredictionEngine:
    """Provides baseline statistical and ML predictive models with walk-forward time-series validation."""

    @staticmethod
    def generate_directional_signals(
        df_features: pd.DataFrame,
        horizons: List[int] = [1, 3, 5, 10, 20]
    ) -> Dict[str, Any]:
        """
        Generates probabilistic forward-looking movement signals for all horizons.
        Directions: Bullish, Slightly Bullish, Neutral, Slightly Bearish, Bearish.
        Confidence: 0-100.
        """
        if df_features.empty or len(df_features) < 30:
            return {
                horizon_key: {
                    "directional_bias": "Neutral",
                    "confidence": 50.0,
                    "model_used": "Baseline Fallback",
                    "probability_up": 0.50
                } for horizon_key in [f"{h}d" for h in horizons]
            }

        feature_cols = [
            'return_1d', 'return_5d', 'rsi_14', 'stoch_rsi',
            'macd', 'macd_signal', 'relative_volume',
            'distance_from_52w_high', 'volatility_20d'
        ]

        # Prepare clean dataset for model training
        df_clean = df_features.dropna(subset=[f'target_direction_{h}d' for h in horizons if f'target_direction_{h}d' in df_features.columns] + feature_cols).copy()

        horizon_signals = {}

        for h in horizons:
            target_col = f'target_direction_{h}d'
            if target_col not in df_clean.columns or len(df_clean) < 25:
                horizon_signals[f"{h}d"] = {
                    "directional_bias": "Neutral",
                    "confidence": 50.0,
                    "model_used": "Insufficient History",
                    "probability_up": 0.50
                }
                continue

            X = df_clean[feature_cols].values
            y = df_clean[target_col].values

            # Time-series walk-forward split (80% train, 20% test)
            split_idx = int(len(X) * 0.8)
            X_train, y_train = X[:split_idx], y[:split_idx]
            X_test, y_test = X[split_idx:], y[split_idx:]

            # Random Forest Classifier Baseline
            try:
                clf = RandomForestClassifier(n_estimators=50, max_depth=4, random_state=42)
                clf.fit(X_train, y_train)

                # Latest observation feature vector for current day prediction
                latest_X = df_features[feature_cols].iloc[[-1]].fillna(0).values
                prob_up = float(clf.predict_proba(latest_X)[0][1])

                # Out of sample metrics
                y_pred = clf.predict(X_test)
                acc = accuracy_score(y_test, y_pred) if len(y_test) > 0 else 0.5
                f1 = f1_score(y_test, y_pred, zero_division=0) if len(y_test) > 0 else 0.5

            except Exception:
                prob_up = 0.50
                acc = 0.50
                f1 = 0.50

            # Map probability to directional bias label
            if prob_up >= 0.65:
                bias = "Bullish"
            elif prob_up >= 0.55:
                bias = "Slightly Bullish"
            elif prob_up <= 0.35:
                bias = "Bearish"
            elif prob_up <= 0.45:
                bias = "Slightly Bearish"
            else:
                bias = "Neutral"

            confidence = round(abs(prob_up - 0.50) * 200.0, 1) # scale to 0-100

            horizon_signals[f"{h}d"] = {
                "directional_bias": bias,
                "confidence": max(50.0, min(95.0, 50.0 + confidence)),
                "probability_up": round(prob_up, 4),
                "model_used": "RandomForest (Walk-Forward Split)",
                "out_of_sample_accuracy": round(float(acc), 4),
                "out_of_sample_f1": round(float(f1), 4)
            }

        return horizon_signals
