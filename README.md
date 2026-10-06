# Daily Indian Stock Market Data & Deep Analysis Pipeline

An automated, research-oriented production pipeline for daily Indian stock market data ingestion, validation, technical & fundamental analysis, market regime detection, historical pattern matching, probabilistic signals, and machine learning feature storage.

## Features

- **Configurable Stock Universe**: Managed via `config/stocks.json` supporting NSE/BSE equities, NIFTY 50, NIFTY Next 50, NIFTY 500, and sector indices.
- **Data Ingestion**: Abstraction around market data providers (`MarketDataProvider` and `YFinanceProvider`) with retries, rate limiting, and error handling.
- **Data Validation & Quality**: Checks OHLC sanity, negative prices, volume spikes, price gaps, and outputs structured quality reports in `data/quality/YYYY-MM-DD.json`.
- **Historical Storage Engine**: Persistence architecture supporting Parquet and CSV exports without data overwrites or duplicate records.
- **Technical Analysis Engine**: Full indicator set (SMA, EMA, RSI, Stoch RSI, MACD, ATR, OBV, A/D, BB, Volatility) and technical event detection (Golden/Death Crosses, 20-day Breakouts/Breakdowns, Volume Spikes).
- **Market Regime & Sector Analysis**: Broad market regime classification (Strong Bullish to Strong Bearish), advance/decline breadth metrics, and sector relative strength rankings.
- **Transparent Composite Scoring**: 0–100 stock score combining Trend, Momentum, Volume, RS, Volatility, Regime, and Fundamental health.
- **Historical Pattern Analogues**: empirical pattern matching against historical setups to calculate 1d, 3d, 5d, 10d, and 20d forward returns, win rates, and drawdowns.
- **Probabilistic Forward Signals**: Categorical directional bias (Bullish to Bearish) and confidence metrics cleanly separated from empirical facts.
- **ML Feature Storage (No Look-Ahead Bias)**: Daily standardized ML feature sets saved to `data/features/daily/YYYY-MM-DD.parquet` for downstream forecasting models.
- **Backtesting & ML Baselines**: Realistic backtesting simulation engine and walk-forward time-series ML models.
- **Daily Reporting**: Generates machine-readable `data/analysis/daily/YYYY-MM-DD.json` and human-readable `reports/daily/YYYY-MM-DD.md`.
- **Automated CI/CD**: Scheduled GitHub Actions workflow (`.github/workflows/daily-market-analysis.yml`).

## Project Structure

```
├── .github/workflows/daily-market-analysis.yml
├── config/
│   ├── config.json
│   ├── holidays.json
│   └── stocks.json
├── docs/
│   ├── architecture.md
│   ├── backtesting.md
│   ├── data-schema.md
│   ├── methodology.md
│   └── prediction.md
├── src/
│   ├── backtesting/
│   ├── features/
│   ├── fundamentals/
│   ├── indicators/
│   ├── ingestion/
│   ├── market/
│   ├── modeling/
│   ├── patterns/
│   ├── pipeline/
│   ├── reporting/
│   ├── scoring/
│   ├── sectors/
│   ├── storage/
│   └── validation/
├── tests/
└── README.md
```

## Quick Start

### Installation

```bash
pip install yfinance pandas numpy scikit-learn pyarrow pytest
```

### Running the Daily Pipeline Locally

To run the pipeline for today's date:

```bash
PYTHONPATH=. python3 src/pipeline/daily_pipeline.py
```

To run for a specific trading date:

```bash
PYTHONPATH=. python3 src/pipeline/daily_pipeline.py --date 2025-02-28
```

### Running Tests

```bash
PYTHONPATH=. pytest tests/
```

## License

MIT License
