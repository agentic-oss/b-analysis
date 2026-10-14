# Data Schema Reference

## 1. Daily Analysis JSON Schema (`data/analysis/daily/YYYY-MM-DD.json`)

```json
{
  "date": "YYYY-MM-DD",
  "pipeline_timestamp": "ISO-8601 UTC string",
  "market": {
    "regime": "Strong Bullish | Bullish | Neutral | Bearish | Strong Bearish",
    "score": 0.0,
    "nifty_trend": "Strong Bullish | Bullish | Neutral | Bearish | Strong Bearish",
    "bank_nifty_trend": "Bullish | Bearish | Neutral",
    "nifty_return_1d": 0.0,
    "nifty_return_20d": 0.0,
    "market_breadth": {
      "advance_decline_ratio": 1.0,
      "pct_above_20dma": 50.0,
      "pct_above_50dma": 50.0,
      "pct_above_200dma": 50.0,
      "new_20d_highs": 0,
      "new_20d_lows": 0
    },
    "rules_triggered": []
  },
  "sectors": [
    {
      "sector": "NIFTY IT",
      "daily_return": 0.0,
      "weekly_return": 0.0,
      "monthly_return": 0.0,
      "rs_vs_nifty_1d": 0.0,
      "rs_vs_nifty_20d": 0.0,
      "momentum_score": 50.0,
      "rank": 1
    }
  ],
  "stocks": [
    {
      "symbol": "RELIANCE",
      "exchange": "NSE",
      "composite_score": 75.0,
      "label": "Strong",
      "components": {
        "technical_trend": 80.0,
        "momentum": 70.0,
        "volume": 60.0,
        "relative_strength": 65.0,
        "volatility": 75.0,
        "market_regime": 70.0,
        "sector": 65.0,
        "fundamental": 60.0
      },
      "fundamental_score": 60.0,
      "market_regime": "Bullish",
      "return_1d": 0.012,
      "breakout_20d": false,
      "breakdown_20d": false,
      "unusual_volume": false,
      "historical_analogues": {
        "num_observations": 45,
        "stats_by_horizon": {
          "20d": {
            "horizon_days": 20,
            "sample_size": 45,
            "mean_forward_return": 2.5,
            "median_forward_return": 2.1,
            "positive_probability": 65.0,
            "negative_probability": 35.0,
            "max_observed_gain": 12.0,
            "max_observed_loss": -8.0,
            "forward_volatility": 4.5
          }
        }
      },
      "future_signals": {
        "20d": {
          "directional_bias": "Bullish",
          "confidence": 75,
          "historical_sample_size": 45,
          "positive_return_probability": 65.0,
          "expected_return_pct": 2.5
        }
      }
    }
  ],
  "prediction_metrics": {}
}
```

## 2. Quality Report Schema (`data/quality/YYYY-MM-DD.json`)

```json
{
  "date": "YYYY-MM-DD",
  "records_processed": 500,
  "records_valid": 498,
  "warnings_count": 2,
  "errors_count": 0,
  "warnings": [
    {
      "symbol": "RELIANCE.NS",
      "type": "VOLUME_SPIKE",
      "message": "Volume spike detected on dates: ['2026-03-05']"
    }
  ],
  "errors": []
}
```
