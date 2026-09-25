# Data Schema Specifications

## 1. Daily Analysis JSON Schema (`data/analysis/daily/YYYY-MM-DD.json`)

```json
{
  "date": "YYYY-MM-DD",
  "market": {
    "date": "YYYY-MM-DD",
    "regime": "Strong Bullish | Bullish | Neutral | Bearish | Strong Bearish",
    "regime_score": 0.0 - 100.0,
    "nifty_close": 0.0,
    "nifty_above_200d": true | false,
    "nifty_above_50d": true | false,
    "bank_nifty_above_50d": true | false,
    "breadth": {
      "advance_decline_ratio": 0.0,
      "pct_above_20dma": 0.0,
      "pct_above_50dma": 0.0,
      "pct_above_200dma": 0.0,
      "new_highs": 0,
      "new_lows": 0
    },
    "rules": []
  },
  "sectors": [
    {
      "sector": "Sector Name",
      "daily_return": 0.0,
      "weekly_return": 0.0,
      "monthly_return": 0.0,
      "relative_strength": 0.0,
      "momentum_score": 0.0,
      "volatility": 0.0,
      "rsi_14": 0.0,
      "rank": 1
    }
  ],
  "stocks": [
    {
      "symbol": "TICKER",
      "exchange": "NSE | BSE",
      "sector": "Sector Name",
      "composite_score": 0.0 - 100.0,
      "label": "Very Strong | Strong | Neutral | Weak | Very Weak",
      "components": {
        "technical_trend": 0.0 - 100.0,
        "momentum": 0.0 - 100.0,
        "volume": 0.0 - 100.0,
        "relative_strength": 0.0 - 100.0,
        "volatility": 0.0 - 100.0,
        "market_regime": 0.0 - 100.0,
        "sector": 0.0 - 100.0,
        "fundamentals": 0.0 - 100.0
      },
      "technical_summary": {},
      "fundamentals": {},
      "historical_analogues": {},
      "forward_probabilities": {}
    }
  ],
  "quality": {
    "records_processed": 0,
    "records_valid": 0,
    "warnings_count": 0,
    "errors_count": 0
  }
}
```

## 2. Data Quality Report Schema (`data/quality/YYYY-MM-DD.json`)

```json
{
  "date": "YYYY-MM-DD",
  "records_processed": 0,
  "records_valid": 0,
  "warnings": [],
  "errors": [],
  "summary_by_ticker": [
    {
      "ticker": "SYMBOL",
      "records_processed": 0,
      "records_valid": 0,
      "warnings": [],
      "errors": []
    }
  ]
}
```
