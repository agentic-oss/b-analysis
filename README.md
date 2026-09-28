# Indian Stock Market Data & Deep Analysis Pipeline

An automated, production-grade daily research pipeline and dataset builder for Indian stock equities (NSE/BSE) and NIFTY indices. Every trading day, the pipeline ingests raw price data, validates data quality, calculates comprehensive technical & fundamental features, assesses market regime and sector performance, matches historical analogues, generates probabilistic directional movement signals, and saves machine/human-readable outputs.

---

## Key Features

- **Ingestion Abstraction:** Configurable `MarketDataProvider` (powered by `yfinance` with retries, fallback handling, and rate limiting).
- **Data Validation & Quality Auditing:** Automatic OHLC logic checks, anomaly detection (price jumps, volume spikes), zero-price filters, and daily quality reports in `data/quality/YYYY-MM-DD.json`.
- **Partitioned Data Storage Engine:** Structured raw (`data/raw/YYYY/MM/YYYY-MM-DD/`) and processed (`data/processed/prices/*.parquet`) storage supporting append/update strategies without data duplication.
- **Technical & Pattern Engine:** Calculates 25+ technical indicators (SMA, EMA, RSI, Stoch RSI, MACD, ATR, Volatility, Bollinger Bands, OBV, A/D Line) and identifies active chart patterns (Golden/Death Cross, 20-day Breakouts, Squeezes, Unusual Volume).
- **Rule-Based Market Regime:** Evaluates benchmark trend alignment (NIFTY 50, Bank NIFTY) and multi-factor market breadth (% above 20/50/200 DMA, Advance/Decline ratio, 20-day new highs/lows) to classify the environment into *Strong Bullish, Bullish, Neutral, Bearish, or Strong Bearish*.
- **Sector Rotation & Ranking:** Evaluates performance, relative strength vs NIFTY, and momentum across major NIFTY sector indices (IT, Bank, Auto, Pharma, FMCG, Metal, Energy, Realty, Financial Services).
- **Transparent Composite Stock Scoring:** Multi-factor stock score (0–100) with separate component weights (Technical Trend, Momentum, Volume, Relative Strength, Volatility, Market Regime, Fundamental).
- **Historical Analogue Engine:** Matches similar historical market setups and calculates forward return empirical probabilities over 1D, 3D, 5D, 10D, and 20D horizons.
- **ML Feature Engineering (Anti-Lookahead Bias):** Reusable feature datasets (`data/features/daily/YYYY-MM-DD.parquet`) designed for machine learning models, with strictly separated forward return target columns.
- **Baseline Machine Learning & Backtesting:** Random Forest walk-forward classification for directional probability estimation, and backtesting framework accounting for transaction costs and slippage.
- **Automated Outputs & GitHub Actions:** Generates structured daily JSON (`data/analysis/daily/YYYY-MM-DD.json`) and Markdown research reports (`reports/daily/YYYY-MM-DD.md`) scheduled via GitHub Actions.

---

## Directory Structure

```
.github/workflows/
  daily-market-analysis.yml
config/
  config.json
  stocks.json
  holidays.json
data/
  raw/
  processed/
  features/
  analysis/
  quality/
reports/
  daily/
docs/
  architecture.md
  data-schema.md
  methodology.md
  prediction.md
  backtesting.md
src/
  ingestion/
    provider.py
  validation/
    validator.py
  storage/
    store.py
  indicators/
    technical.py
  market/
    regime.py
  sectors/
    sector_analysis.py
  fundamentals/
    fundamental_analysis.py
  scoring/
    composite_score.py
  patterns/
    historical_analogue.py
  features/
    engineer.py
  modeling/
    predictions.py
  backtesting/
    engine.py
  reporting/
    markdown_report.py
    json_output.py
  pipeline/
    daily_pipeline.py
  utils/
    logger.py
    git_utils.py
tests/
```

---

## Getting Started

### Installation

```bash
# Clone the repository
git clone https://github.com/your-username/b-analysis.git
cd b-analysis

# Install required Python packages
pip install pandas numpy yfinance scikit-learn pyarrow pytest requests pyyaml
```

### Running Locally

Execute the daily pipeline for a specific date or default to today:

```bash
# Run for a specific historical date
PYTHONPATH=. python3 src/pipeline/daily_pipeline.py --date 2026-03-27

# Run for today with auto-commit enabled
PYTHONPATH=. python3 src/pipeline/daily_pipeline.py --commit
```

### Running Tests

Run the unit test suite:

```bash
PYTHONPATH=. pytest tests/
```

---

## Documentation

For detailed methodology, schema specifications, and architectural documentation, refer to the `docs/` folder:

- [`docs/architecture.md`](docs/architecture.md): System architecture and data pipeline design.
- [`docs/data-schema.md`](docs/data-schema.md): Schema reference for JSON analysis, quality reports, and Parquet feature files.
- [`docs/methodology.md`](docs/methodology.md): Scoring methodology, market regime classification rules, and sector rankings.
- [`docs/prediction.md`](docs/prediction.md): Probabilistic prediction framework, analogue matching, and anti-lookahead bias safeguards.
- [`docs/backtesting.md`](docs/backtesting.md): Backtesting engine logic, transaction cost assumptions, and evaluation metrics.

---

## Disclaimers & Financial Safeguards

This system is strictly a quantitative research tool and empirical dataset generator. Forward-looking signals and probability estimates are non-guaranteed statistical inferences, not financial predictions or investment recommendations.
