# System Architecture

## Overview
The Daily Indian Stock Market Data & Deep Analysis Pipeline is an end-to-end Python engine that executes every market day to ingest, validate, store, analyze, and generate probabilistic research reports for Indian equities (NSE & BSE).

## Module Architecture

```
                                  ┌───────────────────────────┐
                                  │   yfinance / Data API     │
                                  └─────────────┬─────────────┘
                                                │
                                                ▼
                                  ┌───────────────────────────┐
                                  │   Ingestion & Validation  │
                                  │ (MarketDataProvider,     │
                                  │  DataValidator)           │
                                  └─────────────┬─────────────┘
                                                │
                                                ▼
                                  ┌───────────────────────────┐
                                  │  Storage & History        │
                                  │ (StorageManager,          │
                                  │  HistoryManager)          │
                                  └─────────────┬─────────────┘
                                                │
                                                ▼
                                  ┌───────────────────────────┐
                                  │ Technical & Feature Engine│
                                  │ (TechnicalIndicators,     │
                                  │  FeatureBuilder)          │
                                  └─────────────┬─────────────┘
                                                │
                                                ▼
                 ┌──────────────────────────────┼──────────────────────────────┐
                 │                              │                              │
                 ▼                              ▼                              ▼
  ┌─────────────────────────────┐┌─────────────────────────────┐┌─────────────────────────────┐
  │   Market Regime & Sectors   ││   Fundamental Analysis     ││     Historical Patterns     │
  │ (MarketRegime, SectorRank)  ││ (FundamentalAnalyzer)       ││ (AnalogueFinder)            │
  └──────────────┬──────────────┘└──────────────┬──────────────┘└──────────────┬──────────────┘
                 │                              │                              │
                 └──────────────────────────────┼──────────────────────────────┘
                                                │
                                                ▼
                                  ┌───────────────────────────┐
                                  │  Scoring & Signal Engine  │
                                  │ (StockScorer, Signals)    │
                                  └─────────────┬─────────────┘
                                                │
                                                ▼
                                  ┌───────────────────────────┐
                                  │ Prediction & Backtesting  │
                                  │ (BaselinePredictor,       │
                                  │  BacktestEngine)          │
                                  └─────────────┬─────────────┘
                                                │
                                                ▼
                                  ┌───────────────────────────┐
                                  │   Report Generator        │
                                  │ (JSON & Markdown Outputs) │
                                  └───────────────────────────┘
```

## Key Module Responsibilities

1. **`src/ingestion/`**: Encapsulates API access behind `MarketDataProvider` interface with rate-limiting, retries, exponential backoff, and logging.
2. **`src/validation/`**: Performs data validation on raw input without modifying data and writes data quality reports to `data/quality/YYYY-MM-DD.json`.
3. **`src/storage/`**: Manages partitioned dataset storage in Parquet and CSV/JSON formats and ensures continuous historical updates without duplicate records.
4. **`src/indicators/`**: Deterministic calculations of Trend, Momentum, Volatility, Volume, Price Structure indicators, and technical event detection.
5. **`src/features/`**: Feature matrix building strictly without look-ahead bias and separation of future targets (`future_return_1d`, `5d`, `20d`).
6. **`src/market/`**: Rule-based classification of overall market regime (Strong Bullish to Strong Bearish) based on NIFTY 50 and market breadth metrics.
7. **`src/sectors/`**: Calculates sector daily/weekly/monthly returns, relative strength vs NIFTY, and momentum rankings.
8. **`src/fundamentals/`**: Evaluates valuation, profitability, growth, and leverage metrics.
9. **`src/patterns/`**: Matches current stock states against historical setups to derive empirical forward return statistics over 1D to 20D horizons.
10. **`src/scoring/`**: Generates a 0-100 composite score and probabilistic forward movement signals.
11. **`src/modeling/` & `src/backtesting/`**: Trains baseline ML models using temporal walk-forward splits and runs backtests accounting for transaction costs and slippage.
12. **`src/reporting/`**: Produces human-readable daily Markdown reports (`reports/daily/YYYY-MM-DD.md`) and machine-readable JSON exports (`data/analysis/daily/YYYY-MM-DD.json`).
