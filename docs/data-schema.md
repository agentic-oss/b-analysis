# Data Schema Specifications

## 1. Daily Analysis JSON Schema (`data/analysis/daily/YYYY-MM-DD.json`)

```json
{
  "date": "2025-01-10",
  "market": {
    "date": "2025-01-10",
    "regime": "Bullish",
    "regime_score": 7.5,
    "nifty_close": 24000.0,
    "nifty_return_1d": 0.005,
    "nifty_trend": "Uptrend",
    "nifty_volatility": 0.14,
    "banknifty_trend": "Uptrend",
    "breadth": {
      "total_stocks": 25,
      "advances": 18,
      "declines": 7,
      "advance_decline_ratio": 2.57,
      "above_20_dma_pct": 68.0,
      "above_50_dma_pct": 60.0,
      "above_200_dma_pct": 72.0
    }
  },
  "sectors": [
    {
      "symbol": "^CNXIT",
      "name": "NIFTY IT",
      "daily_return": 1.2,
      "weekly_return": 2.5,
      "momentum_score": 65.0,
      "rank": 1
    }
  ],
  "stocks": [
    {
      "symbol": "RELIANCE",
      "technical_score": 78.5,
      "label": "Strong",
      "score_components": {
        "technical_trend_score": 85.0,
        "momentum_score": 80.0,
        "volume_score": 70.0,
        "relative_strength_score": 65.0,
        "market_regime_score": 75.0,
        "sector_score": 60.0,
        "fundamental_score": 70.0
      },
      "signals": {
        "golden_cross": false,
        "breakout": true,
        "trend_state": "Strong Uptrend"
      },
      "historical_analogues": {
        "analogue_count": 45,
        "forward_outcomes": {
          "5d": {
            "avg_return": 1.45,
            "pos_return_prob": 68.2
          }
        }
      },
      "forward_probabilities": {
        "5d": {
          "directional_bias": "Bullish",
          "confidence_score": 68
        }
      }
    }
  ]
}
```

## 2. Feature Dataset Schema (`data/features/daily/YYYY-MM-DD.parquet`)

Columns:
- `ticker`, `exchange`, `date`
- `price_open`, `price_high`, `price_low`, `price_close`, `volume`
- `return_1d`, `return_5d`, `return_20d`
- `rsi_14`, `macd`, `macd_signal`, `atr_14`, `volatility_20d`
- `sma_20`, `sma_50`, `sma_200`, `ema_20`, `ema_50`
- `relative_volume`, `distance_from_52w_high`, `distance_from_52w_low`
- `market_return_1d`, `sector_return_1d`, `market_volatility`, `breadth_above_50dma_pct`
- `technical_score`, `fundamental_score`
- Target Columns: `future_return_1d`, `future_return_3d`, `future_return_5d`, `future_return_10d`, `future_return_20d`
