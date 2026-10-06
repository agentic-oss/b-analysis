# Data Schema Documentation

## 1. Machine-Readable Analysis JSON (`data/analysis/daily/YYYY-MM-DD.json`)

```json
{
  "date": "2025-02-28",
  "market": {
    "regime": "Bullish",
    "regime_score": 30,
    "nifty_close": 22100.5,
    "nifty_trend": "Bullish",
    "nifty_volatility_20d": 0.12,
    "breadth": {
      "total_tracked": 20,
      "advances": 14,
      "declines": 6,
      "ad_ratio": 2.33,
      "pct_above_20dma": 70.0,
      "pct_above_50dma": 65.0,
      "pct_above_200dma": 80.0,
      "new_highs_20d": 3,
      "new_lows_20d": 0
    }
  },
  "sectors": [
    {
      "sector": "NIFTY IT",
      "daily_return": 1.25,
      "weekly_return": 2.4,
      "monthly_return": 5.1,
      "relative_strength_1d": 0.85,
      "relative_strength_20d": 3.2,
      "volatility_20d": 14.2,
      "momentum_score": 82.5,
      "rank": 1
    }
  ],
  "stocks": [
    {
      "symbol": "RELIANCE",
      "composite_score": 78,
      "score_label": "Strong",
      "technical_score": 80,
      "fundamental_score": 70,
      "market_regime": "Bullish",
      "signals": {
        "events": ["Bullish Breakout (20-day high)"],
        "support_level": 2400.0,
        "resistance_level": 2650.0,
        "unusual_volume": false
      },
      "historical_analogues": {
        "observations": 25,
        "horizons": {
          "5d": {
            "avg_return": 1.45,
            "median_return": 1.20,
            "win_rate": 0.68,
            "loss_rate": 0.32,
            "max_gain": 5.80,
            "max_loss": -2.10,
            "forward_std": 1.15
          }
        }
      },
      "forward_probabilities": {
        "forward_horizons": {
          "5d": {
            "directional_bias": "Bullish",
            "confidence": 72,
            "historical_win_rate": 0.68,
            "expected_return_pct": 1.45
          }
        },
        "disclaimer": "RESEARCH SIGNAL DISCLAIMER..."
      }
    }
  ]
}
```

## 2. Data Quality JSON (`data/quality/YYYY-MM-DD.json`)

```json
{
  "date": "2025-02-28",
  "records_processed": 20,
  "records_valid": 20,
  "warnings": [],
  "errors": []
}
```

## 3. Machine Learning Daily Features (`data/features/daily/YYYY-MM-DD.parquet`)

Columns:
- `date`, `symbol`, `price_open`, `price_high`, `price_low`, `price_close`, `volume`
- `return_1d`, `return_5d`, `return_20d`
- `rsi_14`, `macd`, `macd_signal`, `atr`, `volatility_20d`
- `sma_20`, `sma_50`, `sma_200`, `ema_20`, `ema_50`
- `relative_volume`, `distance_from_52w_high`, `distance_from_52w_low`
- `market_return_1d`, `market_volatility`, `breadth`, `market_regime`, `sector_rank`
- `technical_score`, `fundamental_score`
- Target columns (shifted): `future_return_1d`, `future_return_3d`, `future_return_5d`, `future_return_10d`, `future_return_20d`
