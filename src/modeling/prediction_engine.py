import pandas as pd
import numpy as np
from typing import Dict, Any, List, Tuple
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, mean_absolute_error, root_mean_squared_error

class PredictionEngine:
    """
    Generates probabilistic market predictions using strong statistical baselines
    and walk-forward time-series validation (no random shuffling to prevent data leakage).
    """

    def evaluate_walk_forward(self, feature_df: pd.DataFrame, horizon: str = "1d") -> Dict[str, Any]:
        """
        Walk-forward validation for directional signal accuracy.
        """
        target_col = f'future_return_{horizon}'
        if feature_df.empty or target_col not in feature_df.columns:
            return {"status": "insufficient_data"}

        clean = feature_df.dropna(subset=[target_col]).copy()
        if len(clean) < 100:
            return {"status": "insufficient_history", "num_rows": len(clean)}

        feature_cols = [
            'return_1d', 'return_5d', 'return_20d', 'rsi_14', 'macd', 'atr',
            'volatility_20d', 'relative_volume', 'distance_from_52w_high', 'distance_from_52w_low'
        ]
        available_cols = [c for c in feature_cols if c in clean.columns]
        X = clean[available_cols].fillna(0.0)
        y = (clean[target_col] > 0).astype(int) # Binary classification: 1 if positive return, 0 if negative

        # Time-series split (70% train, 30% test chronologically)
        split_idx = int(len(X) * 0.70)
        X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
        y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]

        if len(X_test) < 10 or len(np.unique(y_train)) < 2:
            return {"status": "split_error"}

        model = RandomForestClassifier(n_estimators=50, max_depth=5, random_state=42)
        model.fit(X_train, y_train)

        preds = model.predict(X_test)
        probs = model.predict_proba(X_test)[:, 1] if hasattr(model, "predict_proba") else preds

        acc = float(accuracy_score(y_test, preds))
        prec = float(precision_score(y_test, preds, zero_division=0))
        rec = float(recall_score(y_test, preds, zero_division=0))
        f1 = float(f1_score(y_test, preds, zero_division=0))
        mae = float(mean_absolute_error(clean[target_col].iloc[split_idx:], probs - 0.5))

        return {
            "status": "success",
            "horizon": horizon,
            "train_samples": len(X_train),
            "test_samples": len(X_test),
            "accuracy": round(acc, 4),
            "precision": round(prec, 4),
            "recall": round(rec, 4),
            "f1_score": round(f1, 4),
            "mae": round(mae, 4)
        }

    def generate_forward_signals(self, analogue_stats: Dict[str, Any], stock_score: float) -> Dict[str, Any]:
        """
        Combines historical analogue probabilities with stock scores to produce
        probabilistic forward directional biases and confidence levels.
        Separates facts, analogue stats, and statistical inferences.
        """
        horizons = ["1d", "3d", "5d", "10d", "20d"]
        signals = {}

        for h in horizons:
            h_stat = analogue_stats.get("horizons", {}).get(h, {})
            pos_prob = h_stat.get("positive_prob", 0.50)
            avg_ret = h_stat.get("avg_return", 0.0)

            # Combined probability incorporating component score signal
            blended_prob = (pos_prob * 0.70) + ((stock_score / 100.0) * 0.30)
            blended_prob = max(0.0, min(1.0, blended_prob))

            # Directional Bias Label
            if blended_prob >= 0.65:
                bias = "Bullish"
            elif blended_prob >= 0.55:
                bias = "Slightly Bullish"
            elif blended_prob <= 0.35:
                bias = "Bearish"
            elif blended_prob <= 0.45:
                bias = "Slightly Bearish"
            else:
                bias = "Neutral"

            # Confidence score (0-100) based on distance from 0.50 and sample size
            dist_from_neutral = abs(blended_prob - 0.50)
            num_matches = analogue_stats.get("num_matches", 0)
            sample_confidence = min(1.0, num_matches / 20.0)
            confidence = round(min(100.0, (dist_from_neutral * 200.0 * 0.7 + sample_confidence * 30.0)), 1)

            signals[h] = {
                "directional_bias": bias,
                "confidence": confidence,
                "blended_positive_probability": round(float(blended_prob), 4),
                "historical_analogue_probability": pos_prob,
                "expected_average_return": avg_ret
            }

        return {
            "signals": signals,
            "disclaimer": "Forward signals represent probabilistic research estimates, not guaranteed price predictions."
        }
