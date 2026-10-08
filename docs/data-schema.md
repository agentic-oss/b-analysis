# Data Schema Specification

## 1. Daily Analysis Output (`data/analysis/daily/YYYY-MM-DD.json`)
```json
{
  "date": "YYYY-MM-DD",
  "pipeline_timestamp": "ISO-8601 UTC",
  "market": {
    "nifty_trend": "Strong Uptrend | Uptrend | Strong Downtrend | Downtrend",
    "bank_nifty_trend": "Uptrend | Downtrend",
    "classification": "Strong Bullish | Bullish | Neutral | Bearish | Strong Bearish",
    "breadth": {
      "total_tracked": 15,
      "pct_above_20_dma": 80.0,
      "pct_above_50_dma": 70.0,
      "pct_above_200_dma": 60.0,
      "advances": 10,
      "declines": 5,
      "advance_decline_ratio": 2.0,
      "new_highs": 2,
      "new_lows": 0
    }
  },
  "sectors": [
    {
      "sector": "NIFTY IT",
      "daily_return_pct": 1.2,
      "weekly_return_pct": 2.5,
      "monthly_return_pct": 5.0,
      "relative_strength_vs_nifty": 0.8,
      "momentum_score": 3.4,
      "rank": 1
    }
  ],
  "stocks": [
    {
      "symbol": "RELIANCE",
      "exchange": "NSE",
      "sector": "NIFTY Energy",
      "technical_score": 82.5,
      "score_label": "Very Strong",
      "score_components": {
        "technical_trend_score": 100,
        "momentum_score": 80,
        "volume_score": 75,
        "relative_strength_score": 85,
        "market_sector_score": 70
      },
      "daily_return_pct": 1.5,
      "rsi_14": 62.4,
      "volatility": "Normal",
      "signals": {
        "breakout": false,
        "breakdown": false,
        "unusual_volume": true,
        "golden_cross": false,
        "death_cross": false
      },
      "historical_analogues": {
        "historical_sample_count": 150,
        "horizons": {
          "5d": {
            "sample_count": 150,
            "directional_bias": "Bullish",
            "win_probability_pct": 68.0,
            "avg_return_pct": 1.8,
            "max_gain_pct": 12.0,
            "max_loss_pct": -5.5
          }
        }
      }
    }
  ]
}
```

## 2. Quality Report (`data/quality/YYYY-MM-DD.json`)
```json
{
  "date": "YYYY-MM-DD",
  "records_processed": 5000,
  "records_valid": 5000,
  "warnings": [],
  "errors": []
}
```
