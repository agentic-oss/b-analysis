# Data Schema Documentation

## 1. Daily Analysis Machine-Readable JSON Schema (`data/analysis/daily/YYYY-MM-DD.json`)

```json
{
  "date": "YYYY-MM-DD",
  "market": {
    "market_regime": "Strong Bullish | Bullish | Neutral | Bearish | Strong Bearish",
    "confidence": 85,
    "regime_score": 6.5,
    "details": {
      "nifty_close": 24500.0,
      "nifty_rsi_14": 62.5,
      "nifty_volatility_20d": 0.14,
      "total_stocks_analyzed": 20,
      "advances": 14,
      "declines": 6,
      "advance_decline_ratio": 2.33,
      "pct_above_20dma": 70.0,
      "pct_above_50dma": 65.0,
      "pct_above_200dma": 80.0,
      "new_highs_20d": 3,
      "new_lows_20d": 0
    }
  },
  "sectors": [
    {
      "symbol": "^CNXIT",
      "name": "NIFTY IT",
      "daily_return": 1.2,
      "weekly_return": 2.5,
      "monthly_return": 4.1,
      "relative_strength_1d": 0.5,
      "momentum_score": 68.5,
      "rank": 1
    }
  ],
  "stocks": [
    {
      "symbol": "RELIANCE",
      "exchange": "NSE",
      "sector": "NIFTY Energy",
      "latest_close": 1250.0,
      "daily_return_pct": 0.85,
      "composite_score": 78.4,
      "score_label": "Strong",
      "score_components": {
        "technical_trend_score": 85.0,
        "momentum_score": 75.0,
        "volume_score": 70.0,
        "relative_strength_score": 65.0,
        "volatility_score": 80.0,
        "market_regime_score": 70.0,
        "sector_score": 68.5,
        "fundamental_score": 75.0
      },
      "technical_events": {
        "golden_cross": false,
        "death_cross": false,
        "breakout_20d": true,
        "breakdown_20d": false,
        "unusual_volume": false
      },
      "historical_analogues": {
        "observations_found": 35,
        "forward_statistics": {
          "5d": {
            "mean_forward_return_pct": 1.45,
            "win_rate_pct": 68.5,
            "max_observed_gain_pct": 5.2,
            "max_observed_loss_pct": -2.1
          }
        }
      },
      "forward_signals": {
        "5d": {
          "horizon": "5-day directional bias",
          "directional_bias": "Bullish",
          "confidence_score": 72,
          "implied_bullish_probability_pct": 72.46,
          "historical_win_rate_pct": 68.5
        }
      }
    }
  ]
}
```

---

## 2. Engineered ML Feature Matrix Schema (`data/features/daily/YYYY-MM-DD.parquet`)

| Column Name | Type | Description |
|---|---|---|
| `ticker` | String | Equity symbol |
| `Date` | String | Trading date (YYYY-MM-DD) |
| `price_open` | Float | Open price |
| `price_high` | Float | High price |
| `price_low` | Float | Low price |
| `price_close` | Float | Close price |
| `volume` | Float | Trading volume |
| `return_1d` | Float | 1-day percentage return |
| `return_5d` | Float | 5-day percentage return |
| `return_20d` | Float | 20-day percentage return |
| `rsi_14` | Float | 14-period RSI |
| `macd` | Float | MACD line value |
| `macd_signal` | Float | MACD signal line value |
| `macd_hist` | Float | MACD histogram value |
| `atr_14` | Float | 14-period Average True Range |
| `volatility_20d` | Float | 20-day annualized volatility |
| `sma_20` | Float | 20-day Simple Moving Average |
| `sma_50` | Float | 50-day Simple Moving Average |
| `sma_200` | Float | 200-day Simple Moving Average |
| `relative_volume` | Float | Volume / 20-day Volume SMA |
| `market_return_1d` | Float | NIFTY 1-day percentage return |
| `sector_return_1d` | Float | Sector index 1-day return |
| `composite_score` | Float | Composite score (0-100) |
| `future_return_1d` | Float | Target: Forward 1-day return |
| `future_return_5d` | Float | Target: Forward 5-day return |
| `future_return_20d` | Float | Target: Forward 20-day return |
