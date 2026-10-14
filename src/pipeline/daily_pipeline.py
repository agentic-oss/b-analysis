import os
import json
import argparse
import logging
from datetime import datetime, timezone
import pandas as pd

from src.ingestion.yfinance_provider import YFinanceDataProvider
from src.validation.validator import DataValidator
from src.storage.store import DataStore
from src.indicators.technical import TechnicalIndicators
from src.market.regime import MarketRegimeAnalyzer
from src.sectors.analyzer import SectorAnalyzer
from src.fundamentals.analyzer import FundamentalAnalyzer
from src.scoring.composite import CompositeScorer
from src.patterns.analogues import HistoricalAnalogueAnalyzer, FutureSignalEngine
from src.features.pipeline import FeaturePipeline
from src.modeling.predictor import PredictionModule
from src.backtesting.engine import BacktestEngine
from src.reporting.generator import ReportGenerator

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)

class DailyPipeline:
    """Orchestrates the complete Daily Indian Stock Market Data & Deep Analysis Pipeline."""

    def __init__(self, config_dir: str = "config"):
        self.config_dir = config_dir
        with open(os.path.join(config_dir, "stocks.json")) as f:
            self.stocks_config = json.load(f)
        with open(os.path.join(config_dir, "config.json")) as f:
            self.app_config = json.load(f)

        self.provider = YFinanceDataProvider()
        self.validator = DataValidator()
        self.store = DataStore()
        self.regime_analyzer = MarketRegimeAnalyzer()
        self.sector_analyzer = SectorAnalyzer()
        self.fund_analyzer = FundamentalAnalyzer()
        self.scorer = CompositeScorer(weights=self.app_config.get("scoring", {}).get("weights"))
        self.analogue_analyzer = HistoricalAnalogueAnalyzer()
        self.signal_engine = FutureSignalEngine()
        self.feature_pipeline = FeaturePipeline()
        self.predictor = PredictionModule()
        self.backtester = BacktestEngine()
        self.reporter = ReportGenerator()

    def run(self, target_date: str):
        logger.info(f"Starting daily pipeline execution for date: {target_date}")

        stock_items = [s for s in self.stocks_config.get("stocks", []) if s.get("enabled", True)]
        index_items = [i for i in self.stocks_config.get("indices", []) if i.get("enabled", True)]

        start_date = "2024-01-01"

        all_warnings = []
        all_errors = []
        processed_stock_dfs = {}
        processed_index_dfs = {}

        # 1. Fetch & Validate Indices Data
        for idx in index_items:
            sym = idx["symbol"]
            name = idx["name"]
            logger.info(f"Ingesting index data for {name} ({sym})")
            raw_df = self.provider.get_index_data(sym, start_date, target_date)
            valid_df, w, e = self.validator.validate_symbol_data(raw_df, sym)
            all_warnings.extend(w)
            all_errors.extend(e)
            if not valid_df.empty:
                ind_df = TechnicalIndicators.compute_all(valid_df)
                self.store.save_processed_prices(sym, ind_df)
                processed_index_dfs[name] = ind_df

        # 2. Fetch & Validate Equities Data
        total_records = 0
        valid_records = 0

        for st in stock_items:
            sym = st["symbol"]
            ticker = st["ticker"]
            logger.info(f"Ingesting stock data for {ticker} ({sym})")
            raw_df = self.provider.get_historical_prices(sym, start_date, target_date)
            valid_df, w, e = self.validator.validate_symbol_data(raw_df, sym)
            all_warnings.extend(w)
            all_errors.extend(e)

            total_records += len(raw_df)
            valid_records += len(valid_df)

            if not valid_df.empty:
                ind_df = TechnicalIndicators.compute_all(valid_df)
                self.store.save_processed_prices(ticker, ind_df)
                processed_stock_dfs[ticker] = ind_df

        # 3. Save Quality Report
        quality_report_path = os.path.join("data", "quality", f"{target_date}.json")
        self.validator.generate_quality_report(
            target_date=target_date,
            all_warnings=all_warnings,
            all_errors=all_errors,
            total_records=total_records,
            valid_records=valid_records,
            output_path=quality_report_path
        )
        with open(quality_report_path) as qf:
            quality_data = json.load(qf)

        # 4. Market Regime Analysis
        nifty_df = processed_index_dfs.get("NIFTY 50", pd.DataFrame())
        bank_nifty_df = processed_index_dfs.get("NIFTY BANK", pd.DataFrame())
        market_regime = self.regime_analyzer.analyze(nifty_df, bank_nifty_df, processed_stock_dfs)

        # 5. Sector Analysis
        sector_index_dfs = {k: v for k, v in processed_index_dfs.items() if k not in ["NIFTY 50"]}
        sectors_analysis = self.sector_analyzer.analyze_sectors(sector_index_dfs, nifty_df)
        sector_rank_map = {s["sector"]: s for s in sectors_analysis}

        # 6. Per-Stock Deep Analysis & Scoring
        stock_analysis_list = []
        for st in stock_items:
            ticker = st["ticker"]
            sym = st["symbol"]
            sec_name = st.get("sector")
            df = processed_stock_dfs.get(ticker, pd.DataFrame())
            if df.empty:
                continue

            # Fundamentals
            raw_fund = self.provider.get_fundamental_data(sym)
            fund_res = self.fund_analyzer.analyze(raw_fund)

            # Composite Score
            sec_info = sector_rank_map.get(f"NIFTY {sec_name.upper()}", {}) if sec_name else None
            score_res = self.scorer.compute_stock_score(
                stock_df=df,
                market_regime_score=market_regime.get("score", 50),
                sector_rank_info=sec_info,
                fundamental_score=fund_res["score"]
            )

            # Historical Analogues & Future Signals
            analogues = self.analogue_analyzer.find_analogues(df)
            signals = self.signal_engine.generate_signals(analogues, composite_score=score_res["composite_score"])

            latest = df.iloc[-1]
            stock_analysis_list.append({
                "symbol": ticker,
                "exchange": st.get("exchange", "NSE"),
                "composite_score": score_res["composite_score"],
                "label": score_res["label"],
                "components": score_res["components"],
                "fundamental_score": fund_res["score"],
                "market_regime": market_regime.get("regime"),
                "return_1d": float(latest.get("return_1d", 0.0) or 0.0),
                "breakout_20d": bool(latest.get("breakout_20d", False)),
                "breakdown_20d": bool(latest.get("breakdown_20d", False)),
                "unusual_volume": bool(latest.get("unusual_volume", False)),
                "historical_analogues": analogues,
                "future_signals": signals
            })

        # 7. Feature Matrix Construction & Predictions
        feature_matrix = self.feature_pipeline.build_feature_matrix(processed_stock_dfs)
        if not feature_matrix.empty:
            self.store.save_features(target_date, feature_matrix)

        prediction_metrics = self.predictor.train_and_evaluate(feature_matrix) if not feature_matrix.empty else {}

        # 8. Machine-Readable JSON Output
        daily_output = {
            "date": target_date,
            "pipeline_timestamp": datetime.now(timezone.utc).isoformat(),
            "market": market_regime,
            "sectors": sectors_analysis,
            "stocks": stock_analysis_list,
            "prediction_metrics": prediction_metrics
        }
        self.store.save_daily_analysis(target_date, daily_output)

        # 9. Human-Readable Markdown Report Output
        markdown_report = self.reporter.generate_markdown_report(
            date_str=target_date,
            market_data=market_regime,
            sectors_data=sectors_analysis,
            stock_results=stock_analysis_list,
            quality_data=quality_data,
            prediction_metrics=prediction_metrics
        )
        self.store.save_daily_report(target_date, markdown_report)

        logger.info(f"Daily pipeline completed successfully for {target_date}!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Daily Indian Stock Market Analysis Pipeline")
    parser.add_argument("--date", type=str, default=datetime.now().strftime("%Y-%m-%d"), help="Target date in YYYY-MM-DD format")
    args = parser.parse_args()

    pipeline = DailyPipeline()
    pipeline.run(args.date)
