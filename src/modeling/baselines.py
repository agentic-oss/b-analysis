import pandas as pd
import numpy as np
import logging
from typing import Dict, Any, List, Tuple
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, mean_absolute_error

logger = logging.getLogger(__name__)

class PredictionResearchLayer:
    """
    Statistical and Machine Learning baseline modeling using strictly walk-forward / time-series splits
    to prevent temporal data leakage.
    """

    @staticmethod
    def train_evaluate_walk_forward(
        df_features: pd.DataFrame,
        target_col: str = "target_direction_5d",
        n_splits: int = 3
    ) -> Dict[str, Any]:
        """
        Walk-forward temporal validation split evaluation.
        """
        # Drop rows with missing features or missing future targets
        clean_df = df_features.dropna(subset=[target_col]).copy()

        feature_cols = [
            c for c in clean_df.columns if c not in [
                'date', 'ticker', 'open', 'high', 'low', 'close', 'volume'
            ] and not c.startswith('target_')
        ]

        if len(clean_df) < 50 or len(feature_cols) == 0:
            return {
                "model": "RandomForestClassifier",
                "accuracy": 0.5,
                "precision": 0.5,
                "recall": 0.5,
                "f1": 0.5,
                "directional_accuracy": 50.0,
                "note": "Insufficient clean historical records for ML split validation"
            }

        X = clean_df[feature_cols].fillna(0)
        y = clean_df[target_col].astype(int)

        # Time-series walk-forward splits
        split_size = len(clean_df) // (n_splits + 1)
        accuracies = []
        precisions = []
        recalls = []
        f1s = []

        for i in range(1, n_splits + 1):
            train_idx = range(0, i * split_size)
            test_idx = range(i * split_size, (i + 1) * split_size)

            X_train, y_train = X.iloc[train_idx], y.iloc[train_idx]
            X_test, y_test = X.iloc[test_idx], y.iloc[test_idx]

            if len(np.unique(y_train)) < 2:
                continue

            model = RandomForestClassifier(n_estimators=50, max_depth=5, random_state=42)
            model.fit(X_train, y_train)
            preds = model.predict(X_test)

            accuracies.append(accuracy_score(y_test, preds))
            precisions.append(precision_score(y_test, preds, zero_division=0))
            recalls.append(recall_score(y_test, preds, zero_division=0))
            f1s.append(f1_score(y_test, preds, zero_division=0))

        mean_acc = float(np.mean(accuracies)) if accuracies else 0.5
        mean_prec = float(np.mean(precisions)) if precisions else 0.5
        mean_rec = float(np.mean(recalls)) if recalls else 0.5
        mean_f1 = float(np.mean(f1s)) if f1s else 0.5

        return {
            "model": "RandomForestClassifier (Walk-Forward)",
            "accuracy": round(mean_acc, 4),
            "precision": round(mean_prec, 4),
            "recall": round(mean_rec, 4),
            "f1": round(mean_f1, 4),
            "directional_accuracy": round(mean_acc * 100, 2)
        }

    @staticmethod
    def generate_directional_bias(
        composite_score: float,
        analogue_probs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Combines composite score and empirical analogue probabilities into probabilistic directional signals.
        Separates factual observation, indicator output, analogue statistics, and probabilistic inference.
        """
        horizons_signal = {}

        for h in ["1d", "3d", "5d", "10d", "20d"]:
            h_data = analogue_probs.get("horizons", {}).get(h, {})
            win_rate = h_data.get("win_rate_pct", 50.0)

            # Weighted combination of composite score & historical analogue win rate
            combined_conf = (composite_score * 0.5) + (win_rate * 0.5)

            if combined_conf >= 70:
                bias = "Bullish"
            elif combined_conf >= 58:
                bias = "Slightly Bullish"
            elif combined_conf <= 30:
                bias = "Bearish"
            elif combined_conf <= 42:
                bias = "Slightly Bearish"
            else:
                bias = "Neutral"

            horizons_signal[h] = {
                "directional_bias": bias,
                "confidence_score": round(combined_conf, 1),
                "historical_win_rate_pct": win_rate,
                "historical_sample_size": h_data.get("sample_size", 0)
            }

        return horizons_signal
