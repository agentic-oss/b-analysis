import os
import json
import logging
import pandas as pd
from typing import Dict, Any, Optional

from src.ingestion.provider import YFinanceProvider
from src.validation.validator import DataValidator
from src.storage.storage_manager import StorageManager
from src.storage.history_manager import HistoryManager
from src.indicators.technical import TechnicalIndicators
from src.indicators.events import TechnicalEvents
from src.features.feature_builder import FeatureBuilder
from src.market.regime import MarketRegimeAnalyzer
from src.sectors.sector_analysis import SectorAnalyzer
from src.fundamentals.fundamental_analysis import FundamentalAnalyzer
from src.patterns.analogue_finder import AnalogueFinder
from src.scoring.stock_scorer import StockScorer
from src.scoring.signals import SignalGenerator
from src.modeling.predictor import BaselinePredictor
from src.backtesting.engine import BacktestEngine
from src.reporting.report_generator import ReportGenerator

logger = logging.getLogger(__name__)

class DailyPipeline:
    """Master orchestrator for the Daily Indian Stock Market Data & Deep Analysis Pipeline."""

    def __init__(self, stocks_config_path: str = "config/stocks.json", config_path: str = "config/config.json"):
        self.stocks_config_path = stocks_config_path
        self.config_path = config_path

        # Load configuration
        with open(stocks_config_path, "r") as f:
            self.stocks_config = json.load(f)

        with open(config_path, "r") as f:
            self.sys_config = json.load(f)

        self.provider = YFinanceProvider(
            max_retries=self.sys_config["provider"].get("max_retries", 3),
            backoff_factor=self.sys_config["provider"].get("backoff_factor", 1.5),
            timeout=self.sys_config["provider"].get("timeout", 30)
        )
        self.validator = DataValidator(quality_report_dir="data/quality")
        self.storage = StorageManager(base_dir=self.sys_config["storage"].get("base_dir", "data"))
        self.history = HistoryManager(storage_manager=self.storage)
        self.reporter = ReportGenerator(reports_dir="reports/daily", data_analysis_dir="data/analysis/daily")

    def run(self, date_str: Optional[str] = None, lookback_days: int = 365) -> Dict[str, Any]:
        """
        Executes daily end-to-end pipeline:
        1. Data Ingestion
        2. Validation
        3. Storage & History update
        4. Technical Analysis & Feature Generation
        5. Market Regime & Sector Analysis
        6. Fundamentals Analysis
        7. Pattern Analogue Analysis & Composite Scoring
        8. Probabilistic Signal Generation
        9. Prediction Baseline & Backtesting Evaluation
        10. Daily Report Generation
        """
        if not date_str:
            date_str = pd.Timestamp.now().strftime("%Y-%m-%d")

        logger.info(f"Starting Daily Pipeline run for date: {date_str}")
        start_date = (pd.Timestamp(date_str) - pd.Timedelta(days=lookback_days)).strftime("%Y-%m-%d")

        # 1. Fetch & Store Index Data
        index_dfs = {}
        for idx in self.stocks_config.get("indices", []):
            if not idx.get("enabled", True):
                continue
            sym = idx["symbol"]
            df_idx = self.provider.get_index_data(sym, start_date=start_date, end_date=date_str)
            if not df_idx.empty:
                index_dfs[sym] = df_idx
                self.storage.save_raw_daily(df_idx, date_str, sym)

        nifty_symbol = "^NSEI"
        nifty_df = index_dfs.get(nifty_symbol, pd.DataFrame())

        # Sector Indices Mapping
        sector_dfs = {}
        for idx in self.stocks_config.get("indices", []):
            if idx["symbol"] != nifty_symbol and idx["symbol"] in index_dfs:
                sector_dfs[idx["name"]] = index_dfs[idx["symbol"]]

        # 2. Fetch, Validate, & Store Stock Data
        stock_dfs = {}
        stock_features = {}
        validation_results = []
        stock_analysis_outputs = []

        stocks_to_process = [s for s in self.stocks_config.get("stocks", []) if s.get("enabled", True)]

        for stk in stocks_to_process:
            symbol = stk["symbol"]
            ticker = stk.get("ticker", f"{symbol}.NS")
            sector_name = stk.get("sector", "General")

            # Fetch OHLCV
            df_stk = self.provider.get_historical_prices(ticker, start_date=start_date, end_date=date_str)

            # Validate
            val_res = self.validator.validate(df_stk, ticker)
            validation_results.append(val_res)

            if df_stk.empty or len(df_stk) < 5:
                logger.warning(f"Skipping downstream processing for {ticker} due to insufficient data")
                continue

            # Save raw daily observation
            self.storage.save_raw_daily(df_stk, date_str, ticker)

            # Update continuous history
            full_history = self.history.update_history(df_stk, category="prices")
            stock_df = full_history[full_history["ticker"] == ticker].sort_values("date").reset_index(drop=True)
            stock_dfs[symbol] = stock_df

            # Calculate Technical Indicators
            stock_calc = TechnicalIndicators.calculate_all(stock_df)
            events = TechnicalEvents.identify_events(stock_calc)

            # Feature Engineering without look-ahead bias
            feat_df = FeatureBuilder.build_features(stock_calc)
            stock_features[symbol] = feat_df

            # Fundamentals
            fund_raw = self.provider.get_fundamental_data(ticker)
            fund_eval = FundamentalAnalyzer.evaluate(fund_raw)

            # Analogue Pattern Matching
            analogues = AnalogueFinder.find_analogues(stock_calc)

            stock_analysis_outputs.append({
                "symbol": symbol,
                "ticker": ticker,
                "exchange": stk.get("exchange", "NSE"),
                "sector": sector_name,
                "stock_calc": stock_calc,
                "features": feat_df,
                "technical_events": events,
                "fundamental_eval": fund_eval,
                "analogues": analogues
            })

        # Save Daily Data Quality Report
        self.validator.generate_daily_quality_report(date_str, validation_results)

        # 3. Market Regime & Sector Analysis
        market_regime = MarketRegimeAnalyzer.analyze_regime(nifty_df, stock_dfs)
        sector_rankings = SectorAnalyzer.analyze_sectors(sector_dfs, nifty_df)

        # Map Sector momentum to stock
        sector_map = {sec["sector"]: sec for sec in sector_rankings}

        # 4. Composite Scoring, Signals, Prediction & Backtest per Stock
        final_stock_results = []
        for s_out in stock_analysis_outputs:
            sym = s_out["symbol"]
            sec_name = s_out["sector"]
            sec_info = sector_map.get(sec_name, {"momentum_score": 50.0})

            # Calculate Composite Score
            score = StockScorer.calculate_score(
                s_out["stock_calc"],
                market_regime,
                sec_info,
                fundamental_score=s_out["fundamental_eval"]["fundamental_score"]
            )

            # Probabilistic Signals
            signals = SignalGenerator.generate_signals(score, s_out["analogues"])

            # Baseline Prediction Evaluation
            pred_eval = BaselinePredictor.train_and_evaluate_walk_forward(s_out["features"])

            # Backtest Strategy
            s_out["features"]["signal"] = (s_out["features"]["rsi_14"] < 40).astype(int) - (s_out["features"]["rsi_14"] > 70).astype(int)
            backtest_res = BacktestEngine().run_backtest(s_out["features"], signal_col="signal")

            final_stock_results.append({
                "symbol": sym,
                "ticker": s_out["ticker"],
                "exchange": s_out["exchange"],
                "sector": sec_name,
                "score": score,
                "technical_events": s_out["technical_events"],
                "fundamental_analysis": s_out["fundamental_eval"],
                "historical_analogues": s_out["analogues"],
                "signals": signals,
                "prediction_model": pred_eval,
                "backtest_metrics": backtest_res
            })

        # Master Output Object
        pipeline_output = {
            "date": date_str,
            "pipeline_timestamp": pd.Timestamp.now().isoformat(),
            "data_quality": {
                "records_processed": sum(r["records_processed"] for r in validation_results),
                "records_valid": sum(r["records_valid"] for r in validation_results),
                "warnings": [w for r in validation_results for w in r.get("warnings", [])],
                "errors": [e for r in validation_results for e in r.get("errors", [])]
            },
            "market": market_regime,
            "sectors": sector_rankings,
            "stocks": final_stock_results
        }

        # 5. Generate Daily Markdown & JSON Reports
        json_file = self.reporter.generate_json_output(date_str, pipeline_output)
        md_file = self.reporter.generate_markdown_report(date_str, pipeline_output)

        logger.info(f"Daily Pipeline execution completed successfully for {date_str}.")
        return pipeline_output
