# Analytical Methodology & Scoring Engine

## 1. Multi-Factor Equity Composite Scoring Framework

The stock scoring system evaluates tracked equities on a 0–100 scale using a transparent multi-component model with the following default weights:

$$\text{Composite Score} = \sum_{k \in \text{Components}} \text{Score}_k \times \text{Weight}_k$$

| Factor Component | Weight | Calculation Methodology & Inputs |
|---|---|---|
| **Technical Trend** | 25% | Position relative to moving averages: Price > SMA 20 (+25 pts), Price > SMA 50 (+25 pts), Price > SMA 200 (+25 pts), EMA 20 > SMA 50 (+25 pts). |
| **Momentum** | 20% | Combines RSI 14 (50–70: +20 pts, >70: +10 pts, <30: -20 pts), MACD crossover (+/- 15 pts), and 10-day Rate of Change (+/- 15 pts). |
| **Volume** | 15% | Relative Volume (Volume / 20D SMA): $\ge 2.0x \rightarrow 90$, $\ge 1.2x \rightarrow 75$, $\ge 0.8x \rightarrow 50$, $< 0.8x \rightarrow 30$. |
| **Relative Strength** | 15% | Distance from 52-week high and 1-day price return relative to NIFTY 50 benchmark performance. |
| **Volatility** | 10% | 20-day annualized historical volatility penalty: $<20\% \rightarrow 80$, $20–35\% \rightarrow 60$, $35–50\% \rightarrow 40$, $>50\% \rightarrow 20$. |
| **Market Regime** | 10% | Inherited market environment classification: Strong Bullish (90), Bullish (75), Neutral (50), Bearish (30), Strong Bearish (10). |
| **Fundamental** | 5% | Evaluation of valuation (P/E, P/B), profitability (ROE, profit margins), solvency (D/E), and revenue growth. |

### Score Category Labels
- **80–100:** Very Strong
- **65–79:** Strong
- **50–64:** Neutral
- **35–49:** Weak
- **0–34:** Very Weak

---

## 2. Market Regime Classification Rules

The market environment is classified by analyzing the NIFTY 50 benchmark trend alignment and market breadth across the entire tracked equity universe.

### NIFTY Trend Score (0 to 4 points):
- NIFTY Close > 20 SMA (+1)
- NIFTY Close > 50 SMA (+1)
- NIFTY Close > 200 SMA (+1)
- NIFTY 50 SMA > 200 SMA (+1)

### Market Breadth Score:
$$\text{Breadth Score} = (0.4 \times \% \text{ Above 20 DMA}) + (0.4 \times \% \text{ Above 50 DMA}) + (0.2 \times \% \text{ Above 200 DMA})$$

### Regime Decision Matrix:
- **Strong Bullish:** NIFTY Trend Score $\ge 3$ AND Market Breadth Score $\ge 65$
- **Bullish:** NIFTY Trend Score $\ge 2$ AND Market Breadth Score $\ge 50$
- **Strong Bearish:** NIFTY Trend Score $\le 1$ AND Market Breadth Score $\le 35$
- **Bearish:** NIFTY Trend Score $\le 1$ OR Market Breadth Score $\le 45$
- **Neutral:** All other conditions
