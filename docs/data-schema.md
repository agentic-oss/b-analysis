# Data Schema Documentation

## Daily Analysis Output (`data/analysis/daily/YYYY-MM-DD.json`)

```json
{
  "date": "YYYY-MM-DD",
  "market": {
    "regime": "Strong Bullish | Bullish | Neutral | Bearish | Strong Bearish",
    "regime_score": 82.5,
    "pct_above_20dma": 85.0,
    "advance_decline_ratio": 2.5,
    "advances": 12,
    "declines": 3,
    "new_highs_20d": 4,
    "new_lows_20d": 0
  },
  "sectors": [
    {
      "rank": 1,
      "sector": "NIFTY IT",
      "daily_return": 1.5,
      "weekly_return": 3.2,
      "relative_strength_1d": 0.8,
      "momentum_score": 12.0
    }
  ],
  "stocks": [
    {
      "symbol": "RELIANCE",
      "name": "Reliance Industries Ltd",
      "sector": "Energy",
      "technical_score": 82.0,
      "score_label": "Very Strong",
      "rsi_14": 62.5,
      "volatility_regime": "Normal",
      "signals": {
        "golden_cross": false,
        "breakout_20d": true,
        "unusual_volume": false
      },
      "historical_analogue_matches": 30,
      "forward_probabilities": {
        "1d": { "avg_forward_return": 0.4, "positive_probability": 60.0 },
        "5d": { "avg_forward_return": 1.5, "positive_probability": 68.0, "directional_bias": "Bullish", "confidence": 72.0 }
      }
    }
  ]
}
```
