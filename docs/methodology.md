# Analysis Methodology & Quantitative Models

## 1. Indicator Mathematics

- **Relative Strength Index (RSI 14)**:
  $$\text{RSI} = 100 - \frac{100}{1 + \text{RS}}, \quad \text{RS} = \frac{\text{EMA}_{14}(\text{Gain})}{\text{EMA}_{14}(\text{Loss})}$$
- **Moving Average Convergence Divergence (MACD)**:
  $$\text{MACD} = \text{EMA}_{12}(\text{Close}) - \text{EMA}_{26}(\text{Close})$$
  $$\text{Signal} = \text{EMA}_{9}(\text{MACD}), \quad \text{Histogram} = \text{MACD} - \text{Signal}$$
- **Average True Range (ATR 14)**:
  $$\text{TR} = \max(\text{High} - \text{Low}, |\text{High} - \text{Close}_{\text{prev}}|, |\text{Low} - \text{Close}_{\text{prev}}|)$$
  $$\text{ATR} = \text{EMA}_{14}(\text{TR})$$
- **Historical Volatility (20d)**:
  $$\sigma_{20d} = \text{StdDev}(\ln(\text{Close}_t / \text{Close}_{t-1})) \times \sqrt{252}$$

---

## 2. Historical Pattern Analogue Matching

The system extracts similar historical technical setups for each stock by calculating a normalized distance vector across history:

$$d(t_{\text{hist}}, t_{\text{curr}}) = \sqrt{ \left(\frac{\Delta \text{RSI}}{20}\right)^2 + \left(\frac{\Delta \text{Vol}}{0.10}\right)^2 + \left(\frac{\Delta \text{Dist}_{SMA20}}{5}\right)^2 + \left(\frac{\Delta \text{RelVol}}{1.0}\right)^2 }$$

Matches with $d < 1.5$ are collected and tracked over forward horizons $H \in \{1, 3, 5, 10, 20\}$ trading days. Forward return distributions yield:
- Win Rate ($\% > 0$)
- Loss Rate ($\% < 0$)
- Mean / Median Return
- Max Observed Drawdown & Gain
