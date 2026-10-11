# Data Schema Specification

## 1. Machine-Readable Daily Analysis Schema (`data/analysis/daily/YYYY-MM-DD.json`)

```json
{
  "date": "YYYY-MM-DD",
  "market": {
    "date": "YYYY-MM-DD",
    "regime": "Strong Bullish | Bullish | Neutral | Bearish | Strong Bearish",
    "confidence_score": 75.0,
    "nifty_close": 22000.0,
    "nifty_return_1d": 0.005,
    "nifty_trend": "Bullish",
    "nifty_volatility": 0.12,
    "banknifty_trend": "Bullish",
    "breadth": {
      "total_stocks": 14,
      "advances": 10,
      "declines": 4,
      "advance_decline_ratio": 2.5,
      "pct_above_20dma": 71.43,
      "pct_above_50dma": 64.29,
      "pct_above_200dma": 78.57,
      "new_52w_highs": 2,
      "new_52w_lows": 0
    }
  },
  "sectors": [
    {
      "sector": "NIFTY BANK",
      "return_1d": 1.2,
      "return_5d": 2.5,
      "return_20d": 5.0,
      "relative_strength_1d": 0.7,
      "rsi_14": 62.5,
      "volatility_20d": 0.14,
      "momentum_score": 3.2,
      "rank": 1,
      "leaders": ["HDFCBANK", "ICICIBANK"],
      "laggards": ["SBIN"]
    }
  ],
  "stocks": [
    {
      "symbol": "RELIANCE",
      "technical_score": 82.5,
      "composite_label": "Very Strong",
      "component_scores": {
        "technical_trend_score": 85.0,
        "momentum_score": 78.0,
        "volume_score": 80.0,
        "relative_strength_score": 85.0,
        "volatility_score": 70.0,
        "market_regime_score": 75.0,
        "sector_score": 75.0,
        "fundamental_score": 74.0
      },
      "fundamental_score": 74.0,
      "signals": {
        "date": "YYYY-MM-DD",
        "close": 2950.0,
        "return_1d": 0.015,
        "rsi_14": 64.2,
        "macd": 12.5,
        "macd_signal": 10.1,
        "macd_hist": 2.4,
        "atr_14": 35.0,
        "volatility_20d": 0.18,
        "volatility_regime": "Normal",
        "relative_volume": 1.45,
        "events": ["20-Day High Breakout"]
      },
      "historical_analogues": {
        "matches_count": 18,
        "forward_statistics": {
          "5d": {
            "observations": 18,
            "positive_probability": 72.22,
            "negative_probability": 27.78,
            "average_return_pct": 2.15,
            "median_return_pct": 1.85,
            "max_observed_gain_pct": 7.50,
            "max_observed_loss_pct": -3.20,
            "forward_volatility": 2.10
          }
        }
      },
      "forward_probabilities": {
        "status": "success",
        "horizon_days": 5,
        "directional_bias": "Bullish",
        "confidence": 68.0,
        "probability_up": 84.0,
        "metrics": {
          "accuracy": 0.65,
          "precision": 0.68,
          "recall": 0.70,
          "f1_score": 0.69,
          "roc_auc": 0.71
        }
      }
    }
  ]
}
```

## 2. Daily Quality Report Schema (`data/quality/YYYY-MM-DD.json`)

```json
{
  "date": "YYYY-MM-DD",
  "records_processed": 500,
  "records_valid": 498,
  "warnings": [
    "[RELIANCE] Detected 1 volume anomaly dates exceeding 5.0 std dev."
  ],
  "errors": []
}
```
