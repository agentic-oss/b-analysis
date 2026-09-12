import numpy as np
import pandas as pd
from typing import Dict, Any

class SignalGenerator:
    """
    Generates probabilistic forward-looking movement signals (1D, 3D, 5D, 10D, 20D)
    by combining historical analogue statistics and composite scores into explicit
    directional bias and confidence levels.
    """

    @staticmethod
    def generate_signals(score_data: Dict[str, Any], analogue_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculates directional bias and confidence for 1D, 3D, 5D, 10D, 20D horizons.
        Labels: Bullish, Slightly Bullish, Neutral, Slightly Bearish, Bearish.
        Confidence: 0 - 100 scale.
        """
        composite_score = score_data.get("composite_score", 50.0)
        horizons_info = analogue_data.get("horizons", {})

        signals = {}

        for h_key in ["1d", "3d", "5d", "10d", "20d"]:
            h_stat = horizons_info.get(h_key, {})
            sample_size = h_stat.get("sample_size", 0)
            pos_prob = h_stat.get("positive_return_probability", 50.0)
            avg_fwd_ret = h_stat.get("avg_forward_return_pct", 0.0)

            # Combine score (40%) and empirical positive probability (60%)
            prob_metric = (composite_score * 0.40) + (pos_prob * 0.60)

            # Directional Bias
            if prob_metric >= 68.0:
                bias = "Bullish"
            elif prob_metric >= 55.0:
                bias = "Slightly Bullish"
            elif prob_metric <= 32.0:
                bias = "Bearish"
            elif prob_metric <= 45.0:
                bias = "Slightly Bearish"
            else:
                bias = "Neutral"

            # Confidence calculation (based on sample size and signal strength)
            sample_confidence = min(100.0, (sample_size / 20.0) * 100.0)
            directional_strength = abs(prob_metric - 50.0) * 2.0
            confidence = float(np.clip(0.40 * sample_confidence + 0.60 * directional_strength, 20.0, 95.0))

            signals[h_key] = {
                "horizon": h_key,
                "directional_bias": bias,
                "confidence": round(confidence, 1),
                "empirical_positive_probability": round(pos_prob, 2),
                "expected_average_return_pct": round(avg_fwd_ret, 2),
                "inference_type": "Probabilistic Historical Analogue + Technical Scoring"
            }

        return signals
