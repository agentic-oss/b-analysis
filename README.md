# Indian Stock Market Data & Deep Analysis Pipeline

An automated, production-quality Daily Indian Stock Market Research Dataset & Analysis Engine for NSE/BSE equities and NIFTY indices. Every trading day adds standard, leakage-free historical observations and multi-perspective technical, fundamental, regime, and historical analogue analysis.

---

## 🛠️ System Architecture

The pipeline consists of clean, decoupled modules designed under `src/`:

- **Data Ingestion (`src/ingestion/`)**: `MarketDataProvider` abstraction implemented with retry logic, rate limiting, and `yfinance` integration.
- **Data Validation (`src/validation/`)**: `DataValidator` performing quality checks (duplicate dates, missing days, impossible OHLC logic, volume spikes >10x median, >30% price return jumps) and writing audit reports to `data/quality/YYYY-MM-DD.json`.
- **Historical Storage Architecture (`src/storage/`)**: Append/update dataset manager supporting Parquet, CSV, and JSON outputs without record duplication.
- **Technical Analysis (`src/indicators/`)**: Deterministic calculations for SMAs (5, 10, 20, 50, 100, 200), EMAs (9, 20, 50, 200), RSI-14, Stochastic RSI, MACD, ATR-14, Annualized Volatility, Bollinger Bands, OBV, A/D, VWAP, Support/Resistance levels, Golden/Death crosses, and 20-day Breakouts/Breakdowns.
- **Fundamental Analysis (`src/fundamentals/`)**: Collection and score calculation for PE, PB, EPS, ROE, Debt/Equity, margins, and growth metrics.
- **Market Regime (`src/market/`)**: Rule-based environment classification (Strong Bullish, Bullish, Neutral, Bearish, Strong Bearish) using NIFTY DMA positioning, Bank NIFTY trends, and market breadth (% stocks > 20/50/200 DMA, A/D ratio).
- **Sector Analysis (`src/sectors/`)**: Sector returns, relative strength vs NIFTY 50, momentum scoring, and rankings.
- **Composite Scoring (`src/scoring/`)**: Transparent composite scoring (0-100) with weighted component sub-scores.
- **Historical Analogue Engine (`src/patterns/`)**: Identifies similar historical technical setups and computes forward empirical probabilities across 1D, 3D, 5D, 10D, and 20D horizons.
- **ML Feature Engineering (`src/features/`)**: Builds leakage-free training datasets where date $T$ strictly uses information available on or before date $T$.
- **Predictive Model Baseline (`src/modeling/`)**: Time-series walk-forward validation (no random shuffling) evaluating baseline ML models (Random Forest).
- **Backtesting Engine (`src/backtesting/`)**: Backtests strategy performance incorporating transaction fees (0.1%), slippage (0.05%), holding periods, Sharpe ratio, and drawdowns.
- **Daily Reporting (`src/reporting/` & `src/pipeline/`)**: Generates Markdown reports (`reports/daily/YYYY-MM-DD.md`) and JSON analysis files (`data/analysis/daily/YYYY-MM-DD.json`).

---

## 🚀 Setup & Installation

### Prerequisites
- Python 3.10+
- `pip`

### Install Dependencies
```bash
pip install -r requirements.txt
```

---

## 🏃 Running Locally

To run the pipeline for today's market date:
```bash
PYTHONPATH=. python3 src/pipeline/daily_pipeline.py
```

To run the pipeline for a specific historical trading date:
```bash
PYTHONPATH=. python3 src/pipeline/daily_pipeline.py --date 2025-01-03
```

---

## ⚙️ Configuration

- **`config/stocks.json`**: Configures tracked indices (NIFTY 50, Bank NIFTY, NIFTY IT, etc.) and stock universe.
- **`config/config.json`**: Configures lookback periods, technical indicator parameters, scoring component weights, analogue parameters, and backtest assumptions.
- **`config/holidays.json`**: Configures official Indian market holidays.

---

## 🤖 GitHub Actions Automation

Configured in `.github/workflows/daily-market-analysis.yml`.
- Scheduled to execute automatically on market trading days at 18:00 IST (12:30 UTC).
- Supports manual execution via `workflow_dispatch`.
- Automatically stages and commits new data artifacts with standard commit messages (`data: daily Indian market analysis YYYY-MM-DD`).

---

## 🧪 Running Tests

To run the test suite:
```bash
PYTHONPATH=. pytest tests/
```

---

## 📖 Documentation

Detailed architectural and methodology documentation is available in `docs/`:
- [`docs/architecture.md`](docs/architecture.md): Full system architecture and component interactions.
- [`docs/data-schema.md`](docs/data-schema.md): Data storage formats, schemas, and file structure.
- [`docs/methodology.md`](docs/methodology.md): Technical indicators, composite stock scoring, sector rankings, and market regime rules.
- [`docs/prediction.md`](docs/prediction.md): Historical analogue pattern matching, empirical forward probabilities, and ML feature leakage prevention.
- [`docs/backtesting.md`](docs/backtesting.md): Backtest framework assumptions, trade execution logic, transaction costs, and metrics.
