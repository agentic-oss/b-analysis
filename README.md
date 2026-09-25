# Daily Indian Stock Market Data & Deep Analysis Pipeline

An automated, production-grade market intelligence engine designed for Indian equities (NSE & BSE) and major sector indices. The system runs on every trading day to fetch, validate, analyze, score, pattern-match, and archive high-quality market observations for research and predictive machine-learning modeling.

---

## Key Features

- **Ingestion & Data Quality Infrastructure:** Robust provider layer using `yfinance` with retry logic, rate-limit backoff, and full data quality auditing (`data/quality/YYYY-MM-DD.json`).
- **Comprehensive Technical Analysis:** Deterministic calculation of Trend (SMA/EMA), Momentum (RSI, Stoch RSI, MACD), Volatility (ATR, Bollinger Bands, Historical Volatility), Volume dynamics (Relative Volume, OBV, A/D), and Price Structure (Gaps, Breakouts/Breakdowns, Support/Resistance).
- **Market Regime Analysis:** Rule-based classification (Strong Bullish, Bullish, Neutral, Bearish, Strong Bearish) based on NIFTY/Bank NIFTY moving average alignment and market-wide breadth (% stocks > 20/50/200 DMA, A/D ratio).
- **Sector Performance Rankings:** Sector relative strength vs NIFTY, momentum scores, and sector rotation tracking.
- **Transparent Stock Composite Scoring (0–100):** Multi-factor scoring engine with configurable weights and human-interpretable labels (Very Strong to Very Weak).
- **Fundamental Analysis Support:** Valuation, profitability, growth, leverage, and institutional holdings evaluation.
- **Historical Analogue Pattern Search:** Empirical forward return distributions (1D, 3D, 5D, 10D, 20D win rate, expected returns, max gain/loss) based on similar historical market setups.
- **Point-In-Time Feature Store:** Reusable ML feature dataset with strict look-ahead bias prevention.
- **Probabilistic Predictions & Backtesting Engine:** TimeSeriesSplit walk-forward validation and backtest simulation with transaction cost and slippage models.
- **Automated Reporting & Git Integration:** Automatically generates Markdown research reports (`reports/daily/YYYY-MM-DD.md`) and machine-readable JSON exports (`data/analysis/daily/YYYY-MM-DD.json`) and commits them via GitHub Actions.

---

## Directory Structure

```
├── config/
│   ├── config.json             # Pipeline parameters, indicator periods & scoring weights
│   ├── stocks.json             # Stock and index universe definitions
│   └── holidays.json           # NSE market holiday calendar
├── data/
│   ├── raw/                    # Raw OHLCV CSV archives
│   ├── processed/              # Parquet & CSV historical price/index stores
│   ├── features/               # Point-in-time engineered ML feature sets
│   ├── analysis/daily/         # Machine-readable daily JSON outputs
│   ├── predictions/            # Prediction outputs
│   └── quality/                # Daily data quality diagnostic reports
├── docs/
│   ├── architecture.md         # Architecture and design choices
│   ├── data-schema.md          # Input/output schemas and data contracts
│   ├── methodology.md          # Indicators, scoring, and regime rules
│   ├── prediction.md           # Analogue pattern search & ML design
│   └── backtesting.md          # Backtest engine assumptions and metrics
├── reports/
│   └── daily/                  # Human-readable daily Markdown reports
├── scripts/
│   └── commit_results.py       # Git commit automation helper
├── src/
│   ├── ingestion/              # Data fetching abstractions & providers
│   ├── validation/             # Data quality checking & auditing
│   ├── storage/                # Parquet/CSV/JSON storage manager
│   ├── indicators/             # Deterministic technical indicators
│   ├── market/                 # Market regime & breadth engine
│   ├── sectors/                # Sector performance & ranking
│   ├── fundamentals/           # Fundamental ratios & scoring
│   ├── scoring/                # Composite stock scoring engine
│   ├── patterns/               # Historical analogue pattern matching
│   ├── features/               # Point-in-time ML feature store builder
│   ├── modeling/               # Probabilistic predictors & ML models
│   ├── backtesting/            # Strategy backtesting engine
│   ├── reporting/              # Markdown & JSON report generator
│   └── pipeline/               # Daily pipeline orchestrator
└── tests/                      # Automated unit & integration tests
```

---

## Setup & Running Locally

### Installation

```bash
# Install required Python packages
pip install yfinance pandas numpy scikit-learn pyarrow pytest
```

### Running the Daily Pipeline

```bash
# Run for current date
PYTHONPATH=. python3 src/pipeline/daily_pipeline.py

# Run for a specific historical trading date
PYTHONPATH=. python3 src/pipeline/daily_pipeline.py --date 2026-01-15

# Run in sample mode (fast execution on sample universe)
PYTHONPATH=. python3 src/pipeline/daily_pipeline.py --date 2026-01-15 --sample
```

### Running Tests

```bash
PYTHONPATH=. pytest tests/
```

---

## GitHub Actions Automation

The pipeline is scheduled via `.github/workflows/daily-market-analysis.yml` to execute on market trading days at 12:30 UTC (18:00 IST). It can also be manually triggered using `workflow_dispatch`.

---

## Financial Analysis & Security Disclaimers

> **Disclaimer:** All generated signals, scores, and forward probabilities are empirical research outputs and statistical estimates. They do NOT guarantee future price action or constitute financial advice.

> **Security Note:** Secrets, credentials, and private keys are strictly excluded from git tracking.
