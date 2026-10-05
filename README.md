# Daily Indian Stock Market Data & Deep Analysis Pipeline

An automated, production-quality quantitative research engine and daily analysis pipeline for Indian equities and sector/benchmark indices (NSE & BSE).

## Architecture & Features

- **Ingestion & Provider Abstraction:** Configurable market data providers (`YFinanceProvider`) with exponential backoff retries, rate limiting, and error handling.
- **Data Validation & Quality Layer:** Automatic OHLC integrity checks, duplicate detection, zero/negative price handling, and volume anomaly detection. Output to `data/quality/YYYY-MM-DD.json`.
- **Historical Dataset Storage:** Append/update engine saving raw, processed, and feature data in Parquet, CSV, and JSON formats without overwriting historical observations or introducing duplicate dates.
- **Quantitative Technical Analysis:** Deterministic indicators including SMAs, EMAs, RSI 14, Stoch RSI, MACD, ROC, ATR, Bollinger Bands, OBV, A/D, price structure metrics, moving average crossovers, breakouts/breakdowns, and pivot points.
- **Market Regime & Breadth:** Rule-based classification (`Strong Bullish`, `Bullish`, `Neutral`, `Bearish`, `Strong Bearish`) incorporating benchmark moving averages, Bank NIFTY trend, universe market breadth (% above 20/50/200 DMA), and Advance/Decline ratios.
- **Sector Analysis & Rankings:** Computes performance, relative strength vs NIFTY 50, momentum score, leaders, and laggards for major NIFTY sectors.
- **Transparent Stock Scoring:** Component-weighted 0–100 composite score (Technical Trend, Momentum, Volume, Relative Strength, Volatility, Market Regime, Fundamentals) mapped to human-readable categories (`Very Strong`, `Strong`, `Neutral`, `Weak`, `Very Weak`).
- **Historical Pattern Analogues:** Scans historical observations for similar RSI, volatility, and SMA setups to compute empirical forward return probabilities over 1d, 3d, 5d, 10d, and 20d horizons.
- **ML Feature Engineering (No Look-Ahead Bias):** Generates standardized feature tables and forward-shifted targets specifically engineered for training predictive ML models.
- **Probabilistic Predictions:** Random Forest and statistical models with walk-forward time-series splits evaluating 1D, 3D, 5D, 10D, and 20D directional bias.
- **Backtesting Engine:** Event-driven strategy evaluator accounting for transaction costs, slippage, and position sizing.
- **Reporting Engine:** Generates machine-readable JSON outputs (`data/analysis/daily/YYYY-MM-DD.json`) and Markdown summaries (`reports/daily/YYYY-MM-DD.md`).
- **GitHub Actions Automation:** Scheduled workflow for Indian market trading days with holiday calendar support and manual `workflow_dispatch`.

---

## Setup & Local Execution

### Prerequisites

Python 3.10+

### Installation

```bash
pip install yfinance pandas numpy scikit-learn pyarrow pytest tabulate
```

### Running the Daily Pipeline

To execute the analysis pipeline for today or a specific historical date:

```bash
# Run for today
PYTHONPATH=. python3 src/pipeline/daily_pipeline.py

# Run for a specific date
PYTHONPATH=. python3 src/pipeline/daily_pipeline.py --date 2025-01-10
```

### Running Tests

```bash
PYTHONPATH=. pytest tests/ -v
```

---

## Configuration

- `config/stocks.json`: Configurable universe of indices and stock tickers.
- `config/config.json`: Indicator parameters, score weights, backtest settings, and pipeline options.
- `config/holidays.json`: Scheduled Indian market trading holidays.

---

## Documentation Deep Dive

Detailed documentation is available under `docs/`:
- [`docs/architecture.md`](docs/architecture.md): Complete system architecture and data flow.
- [`docs/data-schema.md`](docs/data-schema.md): Data file structures and JSON schemas.
- [`docs/methodology.md`](docs/methodology.md): Technical indicators, scoring, and regime rules.
- [`docs/prediction.md`](docs/prediction.md): Pattern matching, feature engineering, and ML model design.
- [`docs/backtesting.md`](docs/backtesting.md): Backtesting engine assumptions and execution rules.

---

## Important Safeguard & Disclaimer

This software is designed strictly for financial research, quantitative analytics, and educational data modeling. Forward-looking directional signals represent probabilistic estimates derived from historical analogue statistics. Outputs must **never** be treated as guaranteed forecasts or financial investment advice.
