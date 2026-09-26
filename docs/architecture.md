# Pipeline Architecture & System Design

The **Daily Indian Stock Market Data & Deep Analysis Pipeline** is designed as a modular, decoupled analytical pipeline.

## System Architecture Diagram

```
[ Market Data Provider ] (YFinance / Mock)
          │
          ▼
[ Data Ingestion Layer ] (src/ingestion)
          │
          ▼
[ Data Validation & Quality ] (src/validation) ──► [ Quality Report ] (data/quality/YYYY-MM-DD.json)
          │
          ▼
[ Storage Persistence Engine ] (src/storage) ──► Parquet / CSV Historical Datasets
          │
          ├───────────────────────────┬───────────────────────────┐
          ▼                           ▼                           ▼
[ Technical Indicators ]    [ Market Regime ]           [ Sector Analysis ]
(src/indicators)            (src/market)                (src/sectors)
          │                           │                           │
          └───────────────────────────┼───────────────────────────┘
                                      ▼
                      [ Composite Stock Scoring ]
                      (src/scoring)
                                      │
          ┌───────────────────────────┴───────────────────────────┐
          ▼                                                       ▼
[ Historical Analogue Patterns ]                        [ Feature Engineering ]
(src/patterns)                                          (src/features)
          │                                                       │
          ▼                                                       ▼
[ Probabilistic Forecasts ]                             [ Machine Learning Models ]
(src/modeling)                                          (src/modeling)
          │                                                       │
          └───────────────────────────┬───────────────────────────┘
                                      ▼
                        [ Report Generator Engine ]
                        (src/reporting)
                                      │
          ┌───────────────────────────┴───────────────────────────┐
          ▼                                                       ▼
[ Machine-Readable JSON Analysis ]                      [ Human-Readable Markdown Report ]
(data/analysis/daily/YYYY-MM-DD.json)                   (reports/daily/YYYY-MM-DD.md)
```

## Core Modules

1. **`src/ingestion`**: Provider abstractions (`MarketDataProvider`), handling rate limits, retries, timeouts, and ticker mapping.
2. **`src/validation`**: Data quality checks verifying non-negative prices, OHLC relationships, volume spikes, and date duplicates.
3. **`src/storage`**: Columnar Parquet and CSV persistence supporting continuous deduplicated appends.
4. **`src/indicators`**: Deterministic technical analysis engine calculating SMA, EMA, RSI, Stoch RSI, MACD, ATR, HV, Bollinger Bands, and technical signals.
5. **`src/market`**: Calculates benchmark trends, market breadth (% above 20/50/200 DMA, A/D ratio), and rule-based market regime classification.
6. **`src/sectors`**: Tracks sector performance, relative strength vs NIFTY, momentum scores, and rankings.
7. **`src/fundamentals`**: Valuation, profitability, growth, and health metrics collector.
8. **`src/scoring`**: Transparent 0-100 composite stock rating engine.
9. **`src/patterns`**: Historical analogue setup search and empirical forward probability calculator.
10. **`src/features`**: Point-in-time ML feature matrix creation preventing look-ahead leakage.
11. **`src/modeling`**: Baseline probabilistic forecasts and walk-forward time-series validation.
12. **`src/backtesting`**: Trading strategy simulator with transaction costs and slippage.
13. **`src/reporting`**: Generates daily JSON and Markdown reports.
14. **`src/pipeline`**: Main end-to-end orchestrator script.
