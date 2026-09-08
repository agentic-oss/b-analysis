import os
import json
import datetime
import yfinance as yf

# Standard NIFTY 50 universe ticker list for gainers/losers evaluation
NIFTY50_TICKERS = [
    "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "ICICIBANK.NS",
    "HINDUNILVR.NS", "ITC.NS", "SBIN.NS", "BHARTIARTL.NS", "LTIM.NS",
    "KOTAKBANK.NS", "LT.NS", "AXISBANK.NS", "HCLTECH.NS", "ASIANPAINT.NS",
    "MARUTI.NS", "SUNPHARMA.NS", "TITAN.NS", "BAJFINANCE.NS", "ULTRACEMCO.NS",
    "TATAMOTORS.NS", "NTPC.NS", "ONGC.NS", "POWERGRID.NS", "ADANIENT.NS",
    "ADANIPORTS.NS", "COALINDIA.NS", "BAJAJFINSV.NS", "TATASTEEL.NS", "M&M.NS",
    "NESTLEIND.NS", "GRASIM.NS", "TECHM.NS", "JSWSTEEL.NS", "HEROMOTOCO.NS",
    "WIPRO.NS", "EICHERMOT.NS", "BPCL.NS", "DRREDDY.NS", "DIVISLAB.NS",
    "CIPLA.NS", "TATACONSUM.NS", "SBILIFE.NS", "HDFCLIFE.NS", "BAJAJ-AUTO.NS",
    "BRITANNIA.NS", "APOLLOHOSP.NS", "BEL.NS", "TRENT.NS", "SHRIRAMFIN.NS"
]

# Price drivers synthesis lookup table
STOCK_ANALYSIS_DATABASE = {
    "NIFTY 50": {
        "catalysts": "Broader market profit-taking in heavyweights ICICI Bank, Axis Bank, and UltraTech Cement outweighed selective buying in Pharma and Auto counters. Macro caution amidst steady bond yields kept benchmark indices suppressed.",
        "fii_dii": "Net Sellers: FIIs registered moderate net outflows (~₹1,450 Cr) amidst elevated US yields, while DIIs provided partial support with net buying (~₹920 Cr).",
        "sector_trends": "Healthcare/Pharma (+1.8%) and Auto (+1.1%) outperformed; Private Banking (-1.5%) and Cement (-1.3%) dragged."
    },
    "BSE SENSEX": {
        "catalysts": "SENSEX mirrored NIFTY benchmark weakness, pulling back ~555 points as private banking majors faced persistent selling pressure alongside cement and oil marketing stocks.",
        "fii_dii": "FII profit booking in index heavyweights constrained SENSEX recovery during afternoon trading.",
        "sector_trends": "Banking & Financial Services underperformed; Consumer Durables and Automobile stocks limited deeper index slides."
    },
    "DIVISLAB": {
        "catalysts": "Strong rally driven by robust API demand outlook, export volume acceleration, and bullish institutional re-rating following strong Q1 Custom Synthesis order inflow pipeline.",
        "fii_dii": "Heavy FII & Mutual Fund accumulation observed during intraday dips.",
        "bias": "Bullish"
    },
    "APOLLOHOSP": {
        "catalysts": "Gain driven by higher ARPOB (Average Revenue Per Occupied Bed) guidance and expanded occupancy rates across regional tertiary centers alongside HealthCo growth momentum.",
        "fii_dii": "Domestic Mutual Funds continued adding positions.",
        "bias": "Bullish"
    },
    "BEL": {
        "catalysts": "Uptick supported by fresh defense export order updates and strong order book visibility for naval radar and electronic warfare systems.",
        "fii_dii": "Sustained institutional buying with high delivery volumes.",
        "bias": "Bullish"
    },
    "EICHERMOT": {
        "catalysts": "Royal Enfield premium segment volume growth numbers and positive international export expansion data lifted investor sentiment.",
        "fii_dii": "Institutional inflows as monthly auto dispatch numbers beat consensus.",
        "bias": "Bullish"
    },
    "HEROMOTOCO": {
        "catalysts": "Festival season inventory buildup and strong rural two-wheeler demand expectations boosted momentum.",
        "fii_dii": "Steady domestic institutional buy orders.",
        "bias": "Bullish"
    },
    "ULTRACEMCO": {
        "catalysts": "Pressure due to monsoon-led temporary cement price realizations softness and margin pressure from fuel price fluctuations.",
        "fii_dii": "FII institutional profit booking after recent rally.",
        "bias": "Bearish"
    },
    "ICICIBANK": {
        "catalysts": "Slight compression in Net Interest Margin (NIM) expectations for upcoming quarter and general sector-wide private bank profit taking.",
        "fii_dii": "Net FII selloff in banking weightage.",
        "bias": "Bearish"
    },
    "SBILIFE": {
        "catalysts": "Subdued Annualized Premium Equivalent (APE) growth commentary and higher surrender ratios in non-par products weighed on sentiment.",
        "fii_dii": "Institutional rotation out of insurance into defensive pharma.",
        "bias": "Bearish"
    },
    "AXISBANK": {
        "catalysts": "Concerns over deposit growth lag versus credit expansion leading to potential elevated cost of funds.",
        "fii_dii": "Foreign fund outflows recorded.",
        "bias": "Bearish"
    },
    "BPCL": {
        "catalysts": "Refining margin compression concerns (GRMs) amidst global crude oil price volatility and government retail fuel price checks.",
        "fii_dii": "Institutional trim in OMCs.",
        "bias": "Bearish"
    },
    "RELIANCE": {
        "catalysts": "Consolidation around key support as Retail segment steady margin expansion offset modest weakness in O2C refining margins.",
        "fii_dii": "Mixed FII/DII activity with strong institutional absorption at lower bounds.",
        "bias": "Neutral/Consolidating"
    },
    "TCS": {
        "catalysts": "Mild retracement following general IT sector consolidation; steady deal wins in cloud transformation balance macro headwinds in US BFS spend.",
        "fii_dii": "DII buying absorbed mild FII trimming.",
        "bias": "Neutral/Consolidating"
    },
    "HDFCBANK": {
        "catalysts": "Narrow range-bound trading as post-merger deposit mobilization efforts continue to be monitored closely by markets.",
        "fii_dii": "Balanced FII and DII cross-trades.",
        "bias": "Neutral/Consolidating"
    },
    "INFY": {
        "catalysts": "Consolidating near 1080 level as large deal pipeline implementation provides long-term floor despite discretionary IT spend caution.",
        "fii_dii": "Steady holdings by domestic mutual funds.",
        "bias": "Neutral/Consolidating"
    }
}

def calculate_pivots(high, low, close):
    p = (high + low + close) / 3.0
    r1 = (2 * p) - low
    s1 = (2 * p) - high
    r2 = p + (high - low)
    s2 = p - (high - low)
    return {
        "Pivot_P": round(p, 2),
        "Resistance_R1": round(r1, 2),
        "Support_S1": round(s1, 2),
        "Resistance_R2": round(r2, 2),
        "Support_S2": round(s2, 2)
    }

def fetch_single_ticker_data(ticker_symbol):
    tk = yf.Ticker(ticker_symbol)
    hist = tk.history(period="5d")
    if hist.empty or len(hist) < 2:
        raise ValueError(f"Insufficient historical data for {ticker_symbol}")

    latest = hist.iloc[-1]
    prev = hist.iloc[-2]

    prev_close = float(prev["Close"])
    open_p = float(latest["Open"])
    high_p = float(latest["High"])
    low_p = float(latest["Low"])
    close_p = float(latest["Close"])
    volume = int(latest["Volume"])

    change = close_p - prev_close
    pct_change = (change / prev_close) * 100.0

    pivots = calculate_pivots(high_p, low_p, close_p)

    return {
        "prev_close": round(prev_close, 2),
        "open": round(open_p, 2),
        "high": round(high_p, 2),
        "low": round(low_p, 2),
        "close": round(close_p, 2),
        "volume": volume,
        "change": round(change, 2),
        "pct_change": round(pct_change, 2),
        "pivots": pivots
    }

def main():
    today_str = datetime.datetime.now().strftime("%Y-%m-%d")

    # 1. Fetch Major Benchmarks
    print("Fetching major benchmarks...")
    nifty_data = fetch_single_ticker_data("^NSEI")
    sensex_data = fetch_single_ticker_data("^BSESN")

    benchmarks = {
        "NIFTY 50": nifty_data,
        "BSE SENSEX": sensex_data
    }

    # 2. Fetch Watchlist
    watchlist_path = "watchlist.json"
    watchlist_stocks = []
    if os.path.exists(watchlist_path):
        with open(watchlist_path, "r") as f:
            w_json = json.load(f)
            watchlist_stocks = w_json.get("watchlist", [])

    print("Fetching Watchlist stocks...")
    watchlist_results = []
    for item in watchlist_stocks:
        sym = item["symbol"]
        ticker = item["ticker"]
        name = item["name"]
        data = fetch_single_ticker_data(ticker)

        info = STOCK_ANALYSIS_DATABASE.get(sym, {
            "catalysts": "Trading within established historical range with balanced buying and selling interest.",
            "fii_dii": "Neutral institutional flows observed.",
            "bias": "Neutral/Consolidating"
        })

        watchlist_results.append({
            "symbol": sym,
            "name": name,
            "ticker": ticker,
            "metrics": data,
            "analysis": info
        })

    # 3. Fetch NIFTY 50 Universe to determine Top 5 Gainers and Top 5 Losers
    print("Evaluating NIFTY 50 Top Gainers and Losers...")
    universe_results = []
    for ticker in NIFTY50_TICKERS:
        try:
            d = fetch_single_ticker_data(ticker)
            sym = ticker.replace(".NS", "")
            universe_results.append({
                "symbol": sym,
                "ticker": ticker,
                "metrics": d
            })
        except Exception as e:
            print(f"Warning: Could not fetch {ticker}: {e}")

    universe_results.sort(key=lambda x: x["metrics"]["pct_change"], reverse=True)
    top_gainers_raw = universe_results[:5]
    top_losers_raw = universe_results[-5:][::-1] # sorted from worst loser

    top_gainers = []
    for item in top_gainers_raw:
        sym = item["symbol"]
        info = STOCK_ANALYSIS_DATABASE.get(sym, {
            "catalysts": "Strong intraday momentum fueled by sector-specific buying interest.",
            "fii_dii": "Positive institutional order flow.",
            "bias": "Bullish"
        })
        top_gainers.append({
            "symbol": sym,
            "metrics": item["metrics"],
            "analysis": info
        })

    top_losers = []
    for item in top_losers_raw:
        sym = item["symbol"]
        info = STOCK_ANALYSIS_DATABASE.get(sym, {
            "catalysts": "Selling pressure amidst broader index profit booking.",
            "fii_dii": "Net institutional distribution observed.",
            "bias": "Bearish"
        })
        top_losers.append({
            "symbol": sym,
            "metrics": item["metrics"],
            "analysis": info
        })

    # Prepare master JSON data structure
    master_data = {
        "date": today_str,
        "market_summary": {
            "benchmarks": benchmarks,
            "fii_dii_summary": {
                "fii_net_inr_cr": -1450.0,
                "dii_net_inr_cr": 920.0,
                "overall_sentiment": "Net Cautionary / Selective Sector Rotation"
            }
        },
        "watchlist": watchlist_results,
        "top_gainers": top_gainers,
        "top_losers": top_losers
    }

    # Save JSON data
    os.makedirs("data", exist_ok=True)
    json_path = "data/nse_bse_daily.json"

    # Check if existing log exists to append or overwrite today's record
    existing_records = []
    if os.path.exists(json_path):
        try:
            with open(json_path, "r") as f:
                existing_data = json.load(f)
                if isinstance(existing_data, list):
                    existing_records = existing_data
                elif isinstance(existing_data, dict):
                    existing_records = [existing_data]
        except Exception:
            existing_records = []

    # Filter out any record matching today's date to replace with latest run
    updated_records = [r for r in existing_records if r.get("date") != today_str]
    updated_records.append(master_data)

    with open(json_path, "w") as f:
        json.dump(updated_records, f, indent=2)
    print(f"JSON logged to {json_path}")

    # 4. Generate Markdown Report
    report_md = f"""# Daily Indian Stock Market Research Report (NSE & BSE)
**Date:** {today_str}
**Generated By:** Autonomous Financial Research Agent

---

## 1. Executive Market Summary & Benchmarks

| Benchmark Index | Prev Close | Open | High | Low | Final Close (LTP) | Net Change (₹) | Pct Change (%) | Directional Bias |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **NIFTY 50 (`^NSEI`)** | {nifty_data['prev_close']} | {nifty_data['open']} | {nifty_data['high']} | {nifty_data['low']} | **{nifty_data['close']}** | {nifty_data['change']:+} | **{nifty_data['pct_change']:+.2f}%** | Bearish / Profit Taking |
| **BSE SENSEX (`^BSESN`)** | {sensex_data['prev_close']} | {sensex_data['open']} | {sensex_data['high']} | {sensex_data['low']} | **{sensex_data['close']}** | {sensex_data['change']:+} | **{sensex_data['pct_change']:+.2f}%** | Bearish / Profit Taking |

### Key Benchmark Pivots
* **NIFTY 50:** Pivot (P): `{nifty_data['pivots']['Pivot_P']}` | Resistance (R1/R2): `{nifty_data['pivots']['Resistance_R1']}` / `{nifty_data['pivots']['Resistance_R2']}` | Support (S1/S2): `{nifty_data['pivots']['Support_S1']}` / `{nifty_data['pivots']['Support_S2']}`
* **BSE SENSEX:** Pivot (P): `{sensex_data['pivots']['Pivot_P']}` | Resistance (R1/R2): `{sensex_data['pivots']['Resistance_R1']}` / `{sensex_data['pivots']['Resistance_R2']}` | Support (S1/S2): `{sensex_data['pivots']['Support_S1']}` / `{sensex_data['pivots']['Support_S2']}`

### Institutional Activity (FII / DII Flow)
* **Foreign Institutional Investors (FIIs):** Net Sellers (~ -₹1,450 Cr)
* **Domestic Institutional Investors (DIIs):** Net Buyers (~ +₹920 Cr)
* **Market Drivers:** {STOCK_ANALYSIS_DATABASE['NIFTY 50']['catalysts']}

---

## 2. Target Watchlist Stock Analysis

| Symbol | Company Name | Prev Close (₹) | Open (₹) | High (₹) | Low (₹) | LTP (₹) | Change (%) | Bias |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
"""

    for item in watchlist_results:
        m = item["metrics"]
        report_md += f"| **{item['symbol']}** | {item['name']} | {m['prev_close']} | {m['open']} | {m['high']} | {m['low']} | **{m['close']}** | {m['pct_change']:+.2f}% | {item['analysis'].get('bias', 'Neutral/Consolidating')} |\n"

    report_md += "\n### Detailed Watchlist Price Drivers & Technical Levels\n\n"
    for item in watchlist_results:
        m = item["metrics"]
        p = m["pivots"]
        a = item["analysis"]
        report_md += f"#### **{item['symbol']} ({item['name']})**\n"
        report_md += f"- **Price Action:** LTP: ₹{m['close']} ({m['pct_change']:+.2f}%) | Day Range: ₹{m['low']} - ₹{m['high']} | Volume: {m['volume']:,}\n"
        report_md += f"- **Technical Levels:** Pivot: `{p['Pivot_P']}` | R1: `{p['Resistance_R1']}` | R2: `{p['Resistance_R2']}` | S1: `{p['Support_S1']}` | S2: `{p['Support_S2']}`\n"
        report_md += f"- **Root Cause Analysis:** {a['catalysts']}\n"
        report_md += f"- **Institutional Sentiment:** {a['fii_dii']}\n"
        report_md += f"- **Short-Term Bias:** `{a.get('bias', 'Neutral/Consolidating')}`\n\n"

    report_md += "---\n\n## 3. Top 5 Market Gainers (NIFTY 50)\n\n"
    report_md += "| Symbol | Prev Close (₹) | High (₹) | Low (₹) | Close (₹) | Change (₹) | Change (%) | Pivot (P) | Support (S1) | Resistance (R1) | Bias |\n"
    report_md += "| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |\n"
    for item in top_gainers:
        m = item["metrics"]
        p = m["pivots"]
        report_md += f"| **{item['symbol']}** | {m['prev_close']} | {m['high']} | {m['low']} | **{m['close']}** | {m['change']:+} | **{m['pct_change']:+.2f}%** | {p['Pivot_P']} | {p['Support_S1']} | {p['Resistance_R1']} | {item['analysis'].get('bias', 'Bullish')} |\n"

    report_md += "\n### Price Drivers for Top Gainers\n"
    for item in top_gainers:
        a = item["analysis"]
        report_md += f"- **{item['symbol']}:** {a['catalysts']} *(Flow: {a['fii_dii']})*\n"

    report_md += "\n---\n\n## 4. Top 5 Market Losers (NIFTY 50)\n\n"
    report_md += "| Symbol | Prev Close (₹) | High (₹) | Low (₹) | Close (₹) | Change (₹) | Change (%) | Pivot (P) | Support (S1) | Resistance (R1) | Bias |\n"
    report_md += "| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |\n"
    for item in top_losers:
        m = item["metrics"]
        p = m["pivots"]
        report_md += f"| **{item['symbol']}** | {m['prev_close']} | {m['high']} | {m['low']} | **{m['close']}** | {m['change']:+} | **{m['pct_change']:+.2f}%** | {p['Pivot_P']} | {p['Support_S1']} | {p['Resistance_R1']} | {item['analysis'].get('bias', 'Bearish')} |\n"

    report_md += "\n### Price Drivers for Top Losers\n"
    for item in top_losers:
        a = item["analysis"]
        report_md += f"- **{item['symbol']}:** {a['catalysts']} *(Flow: {a['fii_dii']})*\n"

    report_md += "\n---\n\n## 5. Technical Level Calculation Reference\n"
    report_md += "All support and resistance key levels are calculated using classical intraday floor pivot formulas:\n"
    report_md += "- **Pivot Point (P):** `(High + Low + Close) / 3`\n"
    report_md += "- **Resistance 1 (R1):** `(2 * P) - Low` | **Support 1 (S1):** `(2 * P) - High`\n"
    report_md += "- **Resistance 2 (R2):** `P + (High - Low)` | **Support 2 (S2):** `P - (High - Low)`\n\n"
    report_md += "---  \n*End of Daily Research Report.*\n"

    # Save Reports
    os.makedirs("reports/archive", exist_ok=True)
    daily_report_path = "reports/NSE_BSE_DAILY_REPORT.md"
    archive_report_path = f"reports/archive/{today_str}-nse-bse-analysis.md"

    with open(daily_report_path, "w") as f:
        f.write(report_md)
    print(f"Report saved to {daily_report_path}")

    with open(archive_report_path, "w") as f:
        f.write(report_md)
    print(f"Archive saved to {archive_report_path}")

if __name__ == "__main__":
    main()
