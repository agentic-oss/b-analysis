"""
Daily Stock Market Data & Analysis Pipeline Orchestrator.
Coordinates Ingestion, Validation, Storage, Technical Indicators, Market Regime,
Sector Analysis, Fundamental Analysis, Scoring, Analogues, Features, Modeling, and Reporting.
"""

import os
import json
import logging
import argparse
from datetime import datetime
from typing import Dict, Any, List

from src.ingestion.factory import get_market_data_provider
from src.validation.validator import DataValidator
from src.storage.manager import StorageManager
from src.indicators.engine import TechnicalIndicators
from src.market.regime import MarketRegimeAnalyzer
from src.sectors.analyzer import SectorAnalyzer
from src.fundamentals.analyzer import FundamentalAnalyzer
from src.scoring.engine import CompositeScorer
from src.patterns.analogue import PatternAnalogueEngine
from src.features.builder import FeatureEngineer
from src.reporting.generator import ReportGenerator

logger = logging.getLogger("daily_pipeline")


def setup_logging(level_name: str = "INFO"):
    logging.basicConfig(
        level=getattr(logging, level_name.upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )


def load_json_config(path: str) -> Dict[str, Any]:
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


class DailyPipeline:
    def __init__(
        self,
        stocks_config_path: str = "config/stocks.json",
        config_path: str = "config/config.json",
        holidays_path: str = "config/holidays.json",
    ):
        self.stocks_config = load_json_config(stocks_config_path)
        self.app_config = load_json_config(config_path)
        self.holidays_config = load_json_config(holidays_path)

        self.provider = get_market_data_provider(self.app_config.get("data_provider", "yfinance"))
        self.validator = DataValidator()
        self.storage = StorageManager()
        self.indicators = TechnicalIndicators()
        self.regime_analyzer = MarketRegimeAnalyzer()
        self.sector_analyzer = SectorAnalyzer()
        self.fundamental_analyzer = FundamentalAnalyzer()
        self.scorer = CompositeScorer(self.app_config.get("score_weights"))
        self.analogue_engine = PatternAnalogueEngine()
        self.feature_engineer = FeatureEngineer()
        self.reporter = ReportGenerator()

    def is_trading_day(self, date_str: str) -> bool:
        holidays = self.holidays_config.get("holidays", [])
        if date_str in holidays:
            logger.info(f"{date_str} is listed as a trading holiday. Skipping execution.")
            return False

        dt = datetime.strptime(date_str, "%Y-%m-%d")
        if dt.weekday() >= 5:  # Saturday = 5, Sunday = 6
            logger.info(f"{date_str} is a weekend ({dt.strftime('%A')}). Skipping execution.")
            return False

        return True

    def run(self, date_str: str, force: bool = False) -> Dict[str, Any]:
        logger.info(f"Starting Daily Pipeline for date: {date_str}")

        if not force and not self.is_trading_day(date_str):
            return {"status": "skipped", "reason": f"{date_str} is not a trading day."}

        validation_reports = []
        stock_dfs = {}
        index_dfs = {}
        sector_dfs = {}
        fundamentals_map = {}

        # 1. Ingest Indices
        indices_list = self.stocks_config.get("indices", [])
        for idx_cfg in indices_list:
            if not idx_cfg.get("enabled", True):
                continue
            symbol = idx_cfg["symbol"]
            name = idx_cfg.get("name", symbol)
            df_idx = self.provider.get_index_data(symbol)
            valid_df, val_rep = self.validator.validate_df(df_idx, symbol)
            validation_reports.append(val_rep)

            if not valid_df.empty:
                calc_df = self.indicators.calculate_all(valid_df)
                index_dfs[symbol] = calc_df
                if symbol == "^NSEI":
                    index_dfs["NIFTY50"] = calc_df
                if idx_cfg.get("sector") and idx_cfg["sector"] != "Broad Market":
                    sector_dfs[idx_cfg["sector"]] = calc_df

        # 2. Ingest Stocks & Fundamentals
        stocks_list = self.stocks_config.get("stocks", [])
        for stk_cfg in stocks_list:
            if not stk_cfg.get("enabled", True):
                continue
            symbol = stk_cfg["symbol"]
            ticker = stk_cfg.get("ticker", symbol)

            # Prices
            df_stk = self.provider.get_historical_prices(ticker)
            valid_df, val_rep = self.validator.validate_df(df_stk, symbol)
            validation_reports.append(val_rep)

            if not valid_df.empty:
                calc_df = self.indicators.calculate_all(valid_df)
                stock_dfs[symbol] = calc_df

                # Save to processed historical dataset
                self.storage.update_processed_dataset(
                    calc_df, category="prices", filename=f"{symbol}_prices"
                )

            # Fundamentals
            fund_raw = self.provider.get_fundamentals(ticker)
            fund_eval = self.fundamental_analyzer.analyze(fund_raw)
            fundamentals_map[symbol] = fund_eval

        # 3. Market Regime Analysis
        nifty_df = index_dfs.get("^NSEI", index_dfs.get("NIFTY50"))
        market_regime = self.regime_analyzer.analyze(nifty_df, stock_dfs)

        # 4. Sector Analysis
        sector_rankings = self.sector_analyzer.analyze_sectors(sector_dfs, nifty_df)
        sector_map = {s["sector"]: s for s in sector_rankings}

        # 5. Stock-level deep analysis & scoring & analogues & features
        analyzed_stocks = []

        for stk_cfg in stocks_list:
            symbol = stk_cfg["symbol"]
            if symbol not in stock_dfs:
                continue

            stk_df = stock_dfs[symbol]
            sector_name = stk_cfg.get("sector", "General")
            s_info = sector_map.get(sector_name)
            f_info = fundamentals_map.get(symbol)

            # Scoring
            score_res = self.scorer.score_stock(stk_df, market_regime, s_info, f_info)

            # Signal Detection
            sig_res = self.indicators.detect_signals(stk_df)

            # Pattern Analogues & Probabilities
            analogue_res = self.analogue_engine.find_analogues_and_probabilities(stk_df)

            # Feature Engineering Matrix
            feat_df = self.feature_engineer.create_features_and_targets(
                stk_df,
                market_regime_return=market_regime.get("nifty_return_1d", 0.0),
                sector_return=s_info.get("daily_return", 0.0) if s_info else 0.0,
            )

            # Save features for future ML modeling
            self.storage.save_dataframe(
                feat_df,
                filepath_without_ext=os.path.join(self.storage.get_features_dir("daily"), f"{symbol}_features"),
                formats=["parquet", "csv"],
            )

            latest_row = stk_df.iloc[-1]
            analyzed_stocks.append({
                "symbol": symbol,
                "exchange": stk_cfg.get("exchange", "NSE"),
                "sector": sector_name,
                "close": float(latest_row["Close"]),
                "daily_return_pct": float(latest_row.get("Daily_Return", 0.0)) * 100,
                "composite_score": score_res["composite_score"],
                "label": score_res["label"],
                "sub_scores": score_res["sub_scores"],
                "signals": sig_res.get("signals", []),
                "events": sig_res.get("events", []),
                "trend_alignment": sig_res.get("trend_alignment", "Neutral"),
                "relative_volume": sig_res.get("relative_volume", 1.0),
                "num_analogues": analogue_res.get("num_observations", 0),
                "forward_probabilities": analogue_res.get("forward_probabilities", {}),
                "directional_bias": analogue_res.get("directional_bias", {}),
                "analogue_confidence": analogue_res.get("confidence_score", 0.0),
                "fundamental_summary": f_info,
            })

        # Quality Report
        quality_summary = DataValidator.create_daily_quality_report(date_str, validation_reports)
        self.storage.save_json(
            quality_summary, os.path.join(self.storage.get_quality_dir(), f"{date_str}.json")
        )

        # Build combined analysis dictionary
        combined_analysis = {
            "date": date_str,
            "market": market_regime,
            "sectors": sector_rankings,
            "stocks": analyzed_stocks,
            "quality": quality_summary,
            "pipeline_timestamp": datetime.now().isoformat(),
        }

        # 6. Save Machine-Readable JSON Analysis Output
        json_path = os.path.join(self.storage.get_analysis_dir("daily"), f"{date_str}.json")
        json_output = self.reporter.generate_json_schema_data(date_str, combined_analysis)
        self.storage.save_json(json_output, json_path)

        # 7. Save Human-Readable Markdown Daily Report
        md_content = self.reporter.generate_markdown_report(date_str, combined_analysis)
        md_path = os.path.join(self.storage.get_reports_dir("daily"), f"{date_str}.md")
        self.storage.save_markdown(md_content, md_path)

        logger.info(f"Pipeline finished successfully for {date_str}. JSON: {json_path}, Report: {md_path}")
        return {"status": "success", "json_output": json_path, "report_output": md_path}


def main():
    parser = argparse.ArgumentParser(description="Run Daily Indian Stock Market Analysis Pipeline")
    parser.add_argument("--date", type=str, default=datetime.today().strftime("%Y-%m-%d"), help="Trading date YYYY-MM-DD")
    parser.add_argument("--force", action="store_true", help="Force run even if weekend/holiday")
    args = parser.parse_args()

    setup_logging()
    pipeline = DailyPipeline()
    res = pipeline.run(args.date, force=args.force)
    print(f"Result: {res['status']}")


if __name__ == "__main__":
    main()
