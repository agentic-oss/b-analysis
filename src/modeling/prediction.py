"""
Prediction research layer and baseline probabilistic forecast models using
walk-forward time-series validation.
"""

import logging
from typing import Dict, Any, List, Tuple
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

logger = logging.getLogger(__name__)


class ProbabilisticForecastModel:
    """
    Combines statistical baseline, historical analogues, and ML classifiers
    to generate directional probabilistic signals without guaranteeing future price.
    """

    def __init__(self, horizons: List[int] = [1, 3, 5, 10, 20]):
        self.horizons = horizons

    def generate_directional_signals(
        self,
        stock_df: pd.DataFrame,
        analogues_res: Dict[str, Any],
        composite_score_res: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generates probabilistic signal forecasts for 1D, 3D, 5D, 10D, 20D.
        """
        signals = {}
        comp_score = composite_score_res.get("composite_score", 50.0)
        analogue_horizons = analogues_res.get("horizons", {})

        for h in self.horizons:
            key = f"{h}d"
            a_data = analogue_horizons.get(key, {})
            pos_prob = a_data.get("pos_probability_pct", 50.0)
            avg_ret = a_data.get("avg_forward_return", 0.0)

            # Combined confidence score blending composite score and analogue probability
            blended_prob = (pos_prob * 0.6) + (comp_score * 0.4)
            confidence = round(abs(blended_prob - 50.0) * 2.0, 1)

            if blended_prob >= 65.0:
                bias = "Bullish"
            elif blended_prob >= 55.0:
                bias = "Slightly Bullish"
            elif blended_prob <= 35.0:
                bias = "Bearish"
            elif blended_prob <= 45.0:
                bias = "Slightly Bearish"
            else:
                bias = "Neutral"

            signals[key] = {
                "horizon_days": h,
                "directional_bias": bias,
                "confidence_score": confidence,
                "estimated_positive_prob_pct": round(blended_prob, 1),
                "historical_analogue_avg_return_pct": avg_ret,
                "disclaimer": "Probabilistic statistical signal; not a guaranteed price prediction."
            }

        return signals

    def evaluate_walk_forward_baseline(
        self,
        feature_df: pd.DataFrame,
        target_col: str = "future_direction_5d",
        min_train_size: int = 100,
        step_size: int = 20
    ) -> Dict[str, Any]:
        """
        Executes Walk-Forward Time-Series Validation (No Random Splitting!).
        """
        clean_df = feature_df.dropna(subset=[target_col]).copy()
        if len(clean_df) < min_train_size + step_size:
            return {"error": "Insufficient data for walk-forward validation."}

        feature_cols = [
            "return_1d", "return_5d", "return_20d", "rsi_14", "stoch_rsi",
            "macd", "macd_signal", "macd_hist", "atr", "volatility_20d",
            "relative_volume", "distance_from_52w_high", "distance_from_52w_low"
        ]
        feature_cols = [c for c in feature_cols if c in clean_df.columns]

        X = clean_df[feature_cols].fillna(0.0)
        y = clean_df[target_col].astype(int)

        y_true_all = []
        y_pred_all = []

        # Walk-forward expansion window
        scaler = StandardScaler()
        for i in range(min_train_size, len(clean_df), step_size):
            X_train, y_train = X.iloc[:i], y.iloc[:i]
            X_test, y_test = X.iloc[i:i+step_size], y.iloc[i:i+step_size]

            if len(X_test) == 0 or len(np.unique(y_train)) < 2:
                continue

            X_train_scaled = scaler.fit_transform(X_train)
            X_test_scaled = scaler.transform(X_test)

            model = LogisticRegression(max_iter=500, random_state=42)
            model.fit(X_train_scaled, y_train)

            preds = model.predict(X_test_scaled)
            y_true_all.extend(y_test)
            y_pred_all.extend(preds)

        if not y_true_all:
            return {"error": "Validation produced no test predictions."}

        acc = accuracy_score(y_true_all, y_pred_all)
        prec = precision_score(y_true_all, y_pred_all, zero_division=0)
        rec = recall_score(y_true_all, y_pred_all, zero_division=0)
        f1 = f1_score(y_true_all, y_pred_all, zero_division=0)

        return {
            "validation_type": "Walk-Forward Time-Series Split",
            "sample_count": len(y_true_all),
            "target": target_col,
            "accuracy": round(float(acc), 4),
            "precision": round(float(prec), 4),
            "recall": round(float(rec), 4),
            "f1_score": round(float(f1), 4)
        }
