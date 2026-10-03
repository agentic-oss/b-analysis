# Daily Indian Stock Market Data & Deep Analysis Pipeline

An automated production-quality pipeline running every trading day to fetch Indian stock market data (NSE & BSE), perform technical, market-regime, sector, fundamental, and historical analogue analysis, generate probabilistic directional signals, construct ML features without look-ahead bias, run backtests, and publish daily reports.

---

## Key Features

- **Configurable Universe**: Dynamic configuration of indices (NIFTY 50, NIFTY Bank, NIFTY IT, etc.) and stock tickers in `config/stocks.json`.
- **Market Data Ingestion & Validation**: Abstraction layer supporting `yfinance` with rate-limiting, retries, OHLC logic checks, anomaly detection, and daily data quality auditing (`data/quality/YYYY-MM-DD.json`).
- **Storage Architecture**: Structured historical datasets stored in Parquet/CSV format for raw, processed, features, analysis, and reports.
- **Technical & Fundamental Analysis**: Complete technical suite (SMAs, EMAs, RSI, Stoch RSI, MACD, ATR, Hist Vol, Bollinger Bands, OBV, A/D, Breakouts, Crosses) and financial fundamentals scoring.
- **Market Regime & Sector Analysis**: Rule-based classification of market health (Strong Bullish to Strong Bearish), advance/decline ratio, DMA breadth, and sector relative strength rankings.
- **Historical Pattern Analogue Engine**: Matches current RSI, volatility, and trend setups with historical instances to construct empirical probability distributions for 1D, 3D, 5D, 10D, and 20D forward returns.
- **ML Feature Engineering & Baseline Predictor**: Builds reusable ML datasets strictly preventing look-ahead bias, accompanied by a walk-forward time-series predictor.
- **Backtesting Suite**: Strategy execution engine incorporating realistic transaction costs and slippage.
- **Automated Reporting & CI/CD**: Daily Markdown (`reports/daily/YYYY-MM-DD.md`) and JSON (`data/analysis/daily/YYYY-MM-DD.json`) report generation with scheduled GitHub Actions automation.

---

## Quick Start & Local Execution

### 1. Installation

```bash
pip install -r requirements.txt # or install yfinance pandas numpy scikit-learn pyarrow pytest
```

### 2. Run Daily Pipeline

To execute the pipeline for today or a specific date:

```bash
PYTHONPATH=. python3 src/pipeline/daily_pipeline.py --date 2026-09-30
```

### 3. Run Test Suite

```bash
PYTHONPATH=. pytest tests/
```

---

## Project Architecture & Methodology Documentation

For in-depth explanations of system design and algorithms:

- [Architecture Overview](docs/architecture.md)
- [Data Schema Specifications](docs/data-schema.md)
- [Technical & Scoring Methodology](docs/methodology.md)
- [Prediction & ML Engineering](docs/prediction.md)
- [Backtesting Framework](docs/backtesting.md)

---

## Safeguards & Disclaimer

This system is an empirical analytics and financial research tool. Predictions are probabilistic signals derived from statistical research rather than guaranteed price forecasts.
