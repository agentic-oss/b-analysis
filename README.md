# Daily Indian Stock Market Data & Deep Analysis Pipeline

An automated, long-running Indian stock-market research dataset and deep analysis engine. Every trading day, the system fetches market data, validates observations, stores processed historical records, performs technical/fundamental/regime/sector analysis, computes composite scores, matches historical analogue patterns, generates leak-free feature matrices, trains baseline ML models, runs backtests, and publishes human-readable reports and machine-readable JSON schemas.

---

## Key Features

1. **Configurable Stock Universe**: Stock indices and equities configured dynamically via `config/stocks.json`.
2. **Robust Ingestion & Validation**: Abstraction layer (`MarketDataProvider`) with retries, rate-limiting, and data-quality checks (`DataValidator`).
3. **Structured Historical Storage**: Dual Parquet & CSV/JSON storage under `data/` preserving historical observations without overwriting.
4. **Deterministic Technical Indicators**: Moving averages, RSI, Stochastic RSI, MACD, ATR, Bollinger Bands, OBV, A/D, Gap %, and 52-week distances.
5. **Market Regime & Sector Analysis**: NIFTY trend analysis, market breadth (% above 50 DMA, advance/decline ratio, new highs/lows), and sector rankings.
6. **Transparent Composite Scoring**: 0-100 score combining Technical, Momentum, Volume, Relative Strength, Volatility, Sector, and Fundamentals with 5-tier classification labels.
7. **Historical Pattern Analogues**: Conditional empirical probability framework calculating forward returns (1d, 3d, 5d, 10d, 20d) and win rates for historical setup matches.
8. **Anti-Leakage Feature Engineering**: Point-in-time feature matrix generation with separate future prediction targets for machine learning.
9. **Prediction Research & Backtesting**: Time-series walk-forward ML models and backtesting engine with transaction fees and slippage.
10. **Automated Git & CI/CD**: Daily scheduled execution via GitHub Actions (`.github/workflows/daily-market-analysis.yml`) with automated Git commits.

---

## Project Structure

```
.
├── config/
│   ├── config.json         # General system & model parameters
│   ├── holidays.json       # Indian trading holidays calendar
│   └── stocks.json         # Configurable stock & index universe
├── data/
│   ├── raw/                # YYYY/MM/YYYY-MM-DD raw data snapshots
│   ├── processed/          # Cleaned historical prices & indices (Parquet & CSV)
│   ├── features/           # Point-in-time ML feature matrices
│   ├── analysis/           # Machine-readable daily JSON outputs
│   ├── predictions/        # ML predictions & model metrics
│   └── quality/            # Daily data quality reports
├── docs/                   # Detailed documentation
│   ├── architecture.md
│   ├── data-schema.md
│   ├── methodology.md
│   ├── prediction.md
│   └── backtesting.md
├── reports/
│   └── daily/              # Human-readable Markdown reports (YYYY-MM-DD.md)
├── src/
│   ├── ingestion/          # MarketDataProvider interface & implementation
│   ├── validation/         # Data quality validator
│   ├── storage/            # Parquet/JSON/CSV storage manager
│   ├── indicators/         # Technical indicators & signal detection
│   ├── market/             # Market regime & breadth analyzer
│   ├── sectors/            # Sector ranking & relative strength
│   ├── fundamentals/       # Fundamental financial analyzer
│   ├── scoring/            # 0-100 composite scoring engine
│   ├── patterns/           # Historical analogue pattern matcher
│   ├── features/           # Anti-leakage ML feature matrix builder
│   ├── modeling/           # Walk-forward ML prediction models
│   ├── backtesting/        # Strategy backtesting engine
│   ├── reporting/          # Markdown and JSON report generator
│   └── pipeline/           # Main orchestrator & git commit script
├── tests/                  # Pytest test suite
└── README.md
```

---

## Setup & Local Execution

### Prerequisites

Python 3.10+ with required libraries:

```bash
pip install yfinance pandas scikit-learn pyarrow pytest
```

### Running the Daily Pipeline Locally

To run the pipeline for today's trading date:

```bash
PYTHONPATH=. python3 src/pipeline/daily_pipeline.py
```

To run for a specific target date or force execution on a non-trading day:

```bash
PYTHONPATH=. python3 src/pipeline/daily_pipeline.py --date 2026-03-30 --force
```

### Running Automated Tests

```bash
PYTHONPATH=. pytest tests/ -v
```

---

## GitHub Actions Automation

The pipeline is scheduled via `.github/workflows/daily-market-analysis.yml` to run every trading day after market close (11:30 UTC / 17:00 IST). It can also be manually triggered using `workflow_dispatch`.

---

## Financial Safeguards & Research Disclaimers

This system is an **analytics and research dataset engine**. Forward-looking outputs and directional biases represent empirical conditional probabilities derived from past analogues and statistical models. **They do not constitute financial advice or guaranteed price predictions.**
