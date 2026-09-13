# Data Schema Specification

## 1. Machine-Readable Daily Output (`data/analysis/daily/YYYY-MM-DD.json`)

```json
{
  "date": "YYYY-MM-DD",
  "market": {
    "regime": "Strong Bullish | Bullish | Neutral | Bearish | Strong Bearish",
    "nifty_close": 24500.0,
    "nifty_return_1d": 0.005,
    "nifty_trend": "Bullish",
    "banknifty_trend": "Bullish",
    "breadth_pct_above_20dma": 75.0,
    "breadth_pct_above_50dma": 68.0,
    "breadth_pct_above_200dma": 80.0,
    "advance_decline_ratio": 1.5,
    "advances": 15,
    "declines": 10,
    "new_highs_20d": 3,
    "new_lows_20d": 0,
    "explanation": "NIFTY is trading above 50 DMA with positive market breadth."
  },
  "sectors": [
    {
      "rank": 1,
      "sector": "NIFTY IT",
      "daily_return": 1.25,
      "weekly_return": 3.40,
      "monthly_return": 5.10,
      "relative_strength": 0.75,
      "volatility": 14.50,
      "rsi_14": 62.50,
      "momentum_score": 78.40
    }
  ],
  "stocks": [
    {
      "symbol": "RELIANCE.NS",
      "ticker": "RELIANCE",
      "sector": "NIFTY Energy",
      "composite_score": 82.5,
      "label": "Very Strong",
      "score_components": {
        "technical_trend": 80.0,
        "momentum": 85.0,
        "volume": 75.0,
        "relative_strength": 82.0,
        "market_regime": 75.0,
        "sector": 70.0,
        "fundamental": 80.0
      },
      "relative_volume": 1.45,
      "rsi_14": 64.2,
      "breakout_20d": true,
      "breakdown_20d": false,
      "historical_analogues": {
        "observations_count": 14,
        "horizons": {
          "5d": {
            "sample_size": 14,
            "mean_return_pct": 1.85,
            "win_rate_pct": 71.43
          }
        }
      },
      "signals": {
        "5d": {
          "directional_bias": "Bullish",
          "confidence_score": 76.95,
          "historical_win_rate_pct": 71.43
        }
      }
    }
  ],
  "quality": {
    "date": "YYYY-MM-DD",
    "records_processed": 14,
    "records_valid": 14,
    "warnings": [],
    "errors": []
  }
}
```

## 2. Feature Matrix (`data/features/daily/YYYY-MM-DD.parquet`)

Contains point-in-time technical, volume, regime, sector, and fundamental features for every stock. Target columns (`target_future_return_Kd`) are shifted forward to prevent look-ahead bias during model training.
