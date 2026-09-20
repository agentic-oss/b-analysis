# Data Schema Specifications

## Daily Analysis Machine-Readable Output Schema (`data/analysis/daily/YYYY-MM-DD.json`)

```json
{
  "date": "YYYY-MM-DD",
  "market": {
    "regime": "Strong Bullish | Bullish | Neutral | Bearish | Strong Bearish",
    "explanation": "Text explanation of rule triggers",
    "breadth": {
      "total_stocks": 20,
      "advances": 14,
      "declines": 6,
      "unchanged": 0,
      "ad_ratio": 2.33,
      "pct_above_20dma": 70.0,
      "pct_above_50dma": 65.0,
      "pct_above_200dma": 80.0,
      "new_highs_20d": 3,
      "new_lows_20d": 0
    },
    "nifty_summary": {
      "trend": "Uptrend",
      "above_20dma": true,
      "above_50dma": true,
      "above_200dma": true,
      "volatility_20d": 0.125
    }
  },
  "sectors": [
    {
      "rank": 1,
      "sector": "Information Technology",
      "daily_return_pct": 1.5,
      "weekly_return_pct": 2.8,
      "monthly_return_pct": 5.2,
      "relative_strength_1d": 0.8,
      "momentum_score": 12.4
    }
  ],
  "stocks": [
    {
      "symbol": "RELIANCE",
      "ticker": "RELIANCE.NS",
      "exchange": "NSE",
      "sector": "Energy",
      "close": 2850.0,
      "daily_return_pct": 1.2,
      "composite_score": 78.5,
      "score_label": "Strong",
      "components": {
        "technical_trend_score": 100.0,
        "momentum_score": 65.0,
        "volume_score": 60.0,
        "relative_strength_score": 62.0,
        "volatility_score": 80.0,
        "market_regime_score": 90.0,
        "sector_score": 60.0,
        "fundamental_score": 50.0
      },
      "breakout_20d": true,
      "breakdown_20d": false,
      "relative_volume": 1.4,
      "historical_analogues": {
        "observations_count": 30,
        "horizons": {
          "1d": {
            "avg_forward_return_pct": 0.45,
            "win_rate_pct": 62.5
          }
        }
      },
      "forward_probabilities": {
        "signals": {
          "1d": {
            "bias": "Slightly Bullish",
            "confidence": 61.2,
            "prob_up": 0.612
          }
        }
      }
    }
  ],
  "data_quality": {
    "date": "YYYY-MM-DD",
    "records_processed": 20,
    "records_valid": 20,
    "warnings": [],
    "errors": []
  }
}
```
