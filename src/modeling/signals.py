from typing import Dict, Any, List

class ProbabilisticSignalGenerator:
    """Combines composite scoring and historical analogue probabilities to synthesize probabilistic directional bias."""

    DISCLAIMER = (
        "RESEARCH SIGNAL DISCLAIMER: These outputs are probabilistic directional signals derived from "
        "historical pattern statistics and technical rules. They do NOT constitute financial advice or "
        "guaranteed price predictions."
    )

    def generate_signals(
        self,
        composite_score: int,
        analogue_stats: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generates 1d, 3d, 5d, 10d, 20d directional bias and confidence (0-100).
        """
        horizons_stats = analogue_stats.get("horizons", {})
        signals = {}

        for h in [1, 3, 5, 10, 20]:
            h_key = f"{h}d"
            h_data = horizons_stats.get(h_key, {})

            win_rate = h_data.get("win_rate", 0.5)
            avg_ret = h_data.get("avg_return", 0.0)

            # Combine score bias and historical analogue win rate
            # Base directional score centered at 0 (-100 to +100)
            score_bias = (composite_score - 50) / 50.0  # -1.0 to +1.0
            analogue_bias = (win_rate - 0.5) * 2.0      # -1.0 to +1.0

            combined_bias = 0.5 * score_bias + 0.5 * analogue_bias

            if combined_bias >= 0.4:
                label = "Bullish"
            elif combined_bias >= 0.15:
                label = "Slightly Bullish"
            elif combined_bias >= -0.15:
                label = "Neutral"
            elif combined_bias >= -0.4:
                label = "Slightly Bearish"
            else:
                label = "Bearish"

            # Confidence based on strength of combined bias and number of historical observations
            obs_cnt = analogue_stats.get("observations", 0)
            obs_factor = min(1.0, obs_cnt / 25.0)
            confidence = int(round(min(90, (50 + abs(combined_bias) * 35) * (0.7 + 0.3 * obs_factor))))

            signals[h_key] = {
                "directional_bias": label,
                "confidence": max(10, confidence),
                "historical_win_rate": win_rate,
                "expected_return_pct": avg_ret
            }

        return {
            "forward_horizons": signals,
            "disclaimer": self.DISCLAIMER
        }
