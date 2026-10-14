# Daily Indian Stock Market Data & Deep Analysis Pipeline

An automated, production-quality pipeline for daily data ingestion, validation, technical & fundamental analysis, historical pattern analogue matching, feature engineering, statistical modeling, backtesting, and report generation for Indian equities and indices (NSE & BSE).

---

## Key Capabilities

1. **Market Data Ingestion:**
   - Ingests daily price OHLCV, volume, indices, and corporate actions using an abstract provider model (`MarketDataProvider`).
   - Standardized configurable provider (`YFinanceDataProvider`) with retries, exponential backoff, rate limiting, and failure logging.

2. **Data Validation & Quality Assurance:**
   - Detects negative prices, impossible OHLC (e.g. High < Low or Close > High), duplicates, volume spikes, and extreme price gaps.
   - Generates structured quality reports (`data/quality/YYYY-MM-DD.json`) without modifying or hiding raw data errors.

3. **Storage & Dataset Architecture:**
   - Partitioned data storage in Parquet and CSV (`data/raw/`, `data/processed/`, `data/features/`, `data/analysis/`, `data/predictions/`, `reports/`).
   - Metadata embedded on every record (`ticker`, `exchange`, `trading_date`, `provider`, `ingestion_timestamp`).
   - Idempotent update/append strategy preventing duplicate rows on repeated executions.

4. **Technical & Fundamental Analysis:**
   - **Trend:** SMA (5, 10, 20, 50, 100, 200), EMA (9, 20, 50, 200).
   - **Momentum:** RSI 14, Stochastic RSI, MACD, ROC, Momentum.
   - **Volatility:** ATR 14, 20-day Historical Volatility, Bollinger Bands.
   - **Volume:** Relative Volume, OBV, Accumulation/Distribution.
   - **Price Structure & Events:** Golden/Death Cross, Breakouts/Breakdowns, Unusual Volume detection.
   - **Fundamentals:** P/E, P/B, EPS, Margin, Growth, Debt/Equity scoring.

5. **Market Regime & Sector Analysis:**
   - Classifies market regime into **Strong Bullish**, **Bullish**, **Neutral**, **Bearish**, **Strong Bearish** using NIFTY 50/Bank NIFTY trends and market breadth (A/D ratio, % stocks above 20/50/200 DMA, new highs/lows).
   - Sector rankings based on momentum and relative strength vs NIFTY 50.

6. **Composite Stock Scoring (0-100):**
   - Transparent composite score combining technical trend (25%), momentum (20%), volume (15%), relative strength (15%), volatility (10%), market regime (5%), sector rank (5%), and fundamentals (5%).
   - Categorized as *Very Strong (80-100)*, *Strong (65-79)*, *Neutral (50-64)*, *Weak (35-49)*, *Very Weak (0-34)*.

7. **Historical Analogue Analysis & Future Signals:**
   - Matches current stock setup against historical technical precedents.
   - Calculates empirical forward statistics across 1D, 3D, 5D, 10D, 20D horizons (mean/median return, positive/negative probabilities, max gain/loss).
   - Generates probabilistic directional signals with confidence scores (0-100).

8. **Feature Engineering & Leakage Prevention:**
   - Point-in-time tabular feature matrix generation for downstream ML models.
   - Strict separation between feature matrix $X$ and future return targets $Y$ to prevent look-ahead bias.

9. **Modeling & Backtesting:**
   - Out-of-sample prediction research using walk-forward time-series splits (Logistic Regression, Random Forest baselines).
   - Backtesting engine accounting for transaction fees, slippage, position sizing, Sharpe ratio, and max drawdown.

10. **Daily Reporting & Automation:**
    - Generates human-readable Markdown reports (`reports/daily/YYYY-MM-DD.md`) and machine-readable JSON outputs (`data/analysis/daily/YYYY-MM-DD.json`).
    - GitHub Actions workflow (`.github/workflows/daily-market-analysis.yml`) scheduled for Indian market hours with trading holiday filtering.

---

## Directory Structure

```
├── .github/
│   └── workflows/
│       └── daily-market-analysis.yml
├── config/
│   ├── config.json
│   ├── holidays.json
│   └── stocks.json
├── data/
│   ├── processed/
│   │   └── prices/
│   ├── features/
│   │   └── daily/
│   ├── quality/
│   └── analysis/
│       └── daily/
├── docs/
│   ├── architecture.md
│   ├── backtesting.md
│   ├── data-schema.md
│   ├── methodology.md
│   └── prediction.md
├── reports/
│   └── daily/
├── scripts/
│   └── git_auto_commit.py
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
│   │   └── daily_pipeline.py
│   ├── reporting/
│   ├── scoring/
│   ├── sectors/
│   ├── storage/
│   └── validation/
└── tests/
    └── test_pipeline.py
```

---

## Running Locally

1. **Install dependencies:**
   ```bash
   pip install yfinance pandas numpy scikit-learn pyarrow pytest requests
   ```

2. **Run tests:**
   ```bash
   PYTHONPATH=. pytest tests/
   ```

3. **Run daily pipeline:**
   ```bash
   PYTHONPATH=. python3 src/pipeline/daily_pipeline.py --date 2026-03-06
   ```

---

## Documentation Links

- [Architecture Overview](docs/architecture.md)
- [Data Schema Reference](docs/data-schema.md)
- [Scoring & Indicator Methodology](docs/methodology.md)
- [ML Feature Engineering & Prediction Research](docs/prediction.md)
- [Backtesting Framework](docs/backtesting.md)
