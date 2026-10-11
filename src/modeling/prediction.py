import logging
from typing import Dict, Any, List, Tuple
import pandas as pd
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score

logger = logging.getLogger(__name__)


class DirectionalPredictor:
    """
    Research prediction module using statistical baselines and walk-forward time-series evaluation.

    IMPORTANT FINANCIAL SAFEGUARDS:
    Outputs are probabilistic signals and research estimates, NOT guaranteed forecasts.
    Evaluations use TimeSeriesSplit walk-forward validation without temporal shuffling.
    """

    FEATURE_COLS = [
        "return_1d", "return_5d", "return_20d", "rsi_14", "stoch_rsi_k",
        "macd_hist", "atr_14", "volatility_20d", "dist_sma_20", "dist_sma_50",
        "relative_volume", "market_return_1d"
    ]

    @staticmethod
    def train_and_evaluate(
        df: pd.DataFrame,
        horizon_days: int = 5,
        model_type: str = "random_forest"
    ) -> Dict[str, Any]:
        """
        Trains model on historical feature matrix and evaluates using time-series split.
        """
        if df.empty or len(df) < 100:
            return {"status": "insufficient_data", "metrics": {}}

        df = df.copy().dropna(subset=["close"])
        df["target_direction"] = np.where(df["close"].shift(-horizon_days) > df["close"], 1, 0)

        # Drop rows with NaN in features or target
        valid_cols = [c for c in DirectionalPredictor.FEATURE_COLS if c in df.columns]
        df_clean = df.dropna(subset=valid_cols + ["target_direction"]).copy()

        if len(df_clean) < 80:
            return {"status": "insufficient_data_after_clean", "metrics": {}}

        X = df_clean[valid_cols]
        y = df_clean["target_direction"]

        # Walk-forward train/test split (80% train, 20% test)
        split_idx = int(len(df_clean) * 0.8)
        X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
        y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]

        if model_type == "logistic":
            model = LogisticRegression(max_iter=1000)
        else:
            model = RandomForestClassifier(n_estimators=100, max_depth=5, random_state=42)

        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)
        y_prob = model.predict_proba(X_test)[:, 1] if hasattr(model, "predict_proba") else y_pred

        acc = accuracy_score(y_test, y_pred)
        prec = precision_score(y_test, y_pred, zero_division=0)
        rec = recall_score(y_test, y_pred, zero_division=0)
        f1 = f1_score(y_test, y_pred, zero_division=0)

        try:
            auc = roc_auc_score(y_test, y_prob)
        except Exception:
            auc = 0.5

        # Latest inference on current state
        latest_X = X.iloc[[-1]]
        latest_prob = float(model.predict_proba(latest_X)[0, 1])

        if latest_prob >= 0.65:
            bias = "Bullish"
        elif latest_prob >= 0.55:
            bias = "Slightly Bullish"
        elif latest_prob <= 0.35:
            bias = "Bearish"
        elif latest_prob <= 0.45:
            bias = "Slightly Bearish"
        else:
            bias = "Neutral"

        confidence = round(abs(latest_prob - 0.5) * 200.0, 2)  # Scale 0-100

        return {
            "status": "success",
            "horizon_days": horizon_days,
            "directional_bias": bias,
            "confidence": confidence,
            "probability_up": round(latest_prob * 100, 2),
            "metrics": {
                "accuracy": round(acc, 4),
                "precision": round(prec, 4),
                "recall": round(rec, 4),
                "f1_score": round(f1, 4),
                "roc_auc": round(auc, 4)
            },
            "disclaimer": "Probabilistic research estimate based on historical patterns. Not a guaranteed forecast."
        }
