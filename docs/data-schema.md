# Data Schema & Storage Architecture

## 1. Daily Analysis Output (`data/analysis/daily/YYYY-MM-DD.json`)

```json
{
  "date": "YYYY-MM-DD",
  "market": {
    "regime": "Bullish",
    "nifty_trend": "Uptrend",
    "nifty_return_1d": 0.005,
    "nifty_volatility_20d": 0.12,
    "pct_above_50dma": 65.0,
    "advance_decline_ratio": 1.5
  },
  "sectors": [
    {
      "rank": 1,
      "sector": "Information Technology",
      "daily_return": 1.2,
      "weekly_return": 3.4,
      "momentum_score": 78.5
    }
  ],
  "stocks": [
    {
      "symbol": "RELIANCE",
      "exchange": "NSE",
      "sector": "Energy",
      "close": 2850.0,
      "daily_return_pct": 1.1,
      "composite_score": 82.5,
      "label": "Very Strong",
      "sub_scores": {
        "technical_score": 85.0,
        "momentum_score": 80.0,
        "volume_score": 75.0,
        "relative_strength_score": 80.0,
        "volatility_score": 70.0,
        "sector_score": 88.0,
        "fundamental_score": 74.0
      },
      "signals": ["BOLLINGER_BREAKOUT"],
      "forward_probabilities": {
        "5d": {
          "positive_return_prob": 68.0,
          "avg_forward_return_pct": 2.1
        }
      }
    }
  ],
  "quality": {
    "records_processed": 500,
    "records_valid": 498,
    "warnings": [],
    "errors": []
  }
}
```

## 2. Processed Historical Prices (`data/processed/prices/{SYMBOL}_prices.parquet`)

Columns:
- `Date`: Timestamp
- `Open`, `High`, `Low`, `Close`, `Adj Close`: Float
- `Volume`: Integer
- `Ticker`: String
- `SMA_5`, `SMA_20`, `SMA_50`, `SMA_200`: Float
- `RSI_14`, `MACD`, `MACD_Hist`: Float
- `Volatility_20d`, `BB_Upper`, `BB_Lower`: Float

## 3. Feature Matrix (`data/features/daily/{SYMBOL}_features.parquet`)

Contains all point-in-time technical/market features plus future target columns (`future_return_1d`, `future_return_5d`, `future_target_direction_5d`).
