# Data Schema Specifications

## 1. Machine-Readable Daily Analysis Schema (`data/analysis/daily/YYYY-MM-DD.json`)

```json
{
  "date": "2025-01-10",
  "generated_at": "2025-01-10T17:00:00.000000",
  "market": {
    "regime": "Bullish",
    "composite_score": 65.0,
    "nifty_close": 22450.5,
    "nifty_1d_return": 0.45,
    "nifty_trend": "Uptrend",
    "nifty_volatility_20d": 14.2,
    "banknifty_close": 48200.0,
    "banknifty_1d_return": 0.60,
    "banknifty_trend": "Uptrend",
    "breadth": {
      "advance_decline_ratio": 1.45,
      "advances": 29,
      "declines": 20,
      "unchanged": 1,
      "pct_above_20dma": 68.0,
      "pct_above_50dma": 72.0,
      "pct_above_200dma": 80.0,
      "new_20d_highs": 4,
      "new_20d_lows": 0
    }
  },
  "sectors": [
    {
      "sector": "NIFTY Bank",
      "close": 48200.0,
      "daily_return": 0.60,
      "weekly_return": 1.80,
      "monthly_return": 3.40,
      "relative_strength_1d": 0.15,
      "relative_strength_5d": 0.90,
      "momentum_score": 74.5,
      "rank": 1
    }
  ],
  "stocks": [
    {
      "symbol": "RELIANCE",
      "close": 2850.0,
      "daily_return": 0.85,
      "trend": "Strong Uptrend",
      "rsi_14": 62.4,
      "volatility_20d": 16.5,
      "relative_volume": 1.35,
      "composite_score": 78.5,
      "label": "Strong",
      "score_components": {
        "technical_trend": 85.0,
        "momentum": 75.0,
        "volume": 70.0,
        "relative_strength": 80.0,
        "volatility": 70.0,
        "market_regime": 65.0,
        "sector": 74.5,
        "fundamental": 68.0
      },
      "signals": {
        "golden_cross": false,
        "death_cross": false,
        "breakout": true,
        "breakdown": false,
        "unusual_volume": false,
        "support_level": 2720.0,
        "resistance_level": 2890.0,
        "trend": "Strong Uptrend"
      },
      "signals_forecast": {
        "1d": {
          "horizon_days": 1,
          "directional_bias": "Slightly Bullish",
          "confidence_score": 18.0,
          "estimated_positive_prob_pct": 59.0
        }
      }
    }
  ],
  "data_quality": {
    "records_processed": 500,
    "records_valid": 500,
    "total_warnings": 0,
    "total_errors": 0
  }
}
```

## 2. Quality Report Schema (`data/quality/YYYY-MM-DD.json`)

```json
{
  "date": "2025-01-10",
  "generated_at": "2025-01-10T17:00:00.000000",
  "records_processed": 500,
  "records_valid": 500,
  "total_warnings": 0,
  "total_errors": 0,
  "warnings": [],
  "errors": []
}
```
