# Analytical Methodology

## Overview
This document outlines the core mathematical and statistical methodologies implemented across technical analysis, market regime detection, sector analysis, historical analogue search, composite stock scoring, and forward signal generation.

---

## 1. Technical Indicators & Price Structure

### Trend Indicators
* **Simple Moving Average (SMA)**:
  $$SMA_p(t) = \frac{1}{p} \sum_{i=0}^{p-1} Close(t-i)$$
  Calculated for periods $p \in \{5, 10, 20, 50, 100, 200\}$.

* **Exponential Moving Average (EMA)**:
  $$EMA_p(t) = Close(t) \cdot \alpha + EMA_p(t-1) \cdot (1 - \alpha), \quad \alpha = \frac{2}{p + 1}$$
  Calculated for periods $p \in \{9, 20, 50, 200\}$.

### Momentum Indicators
* **Relative Strength Index (RSI 14)**:
  $$RS = \frac{\text{Average Gain over 14 periods}}{\text{Average Loss over 14 periods}}$$
  $$RSI = 100 - \frac{100}{1 + RS}$$

* **Stochastic RSI**:
  $$StochRSI = \frac{RSI - RSI_{min, 14}}{RSI_{max, 14} - RSI_{min, 14}}$$

* **MACD**:
  $$MACD = EMA_{12} - EMA_{26}$$
  $$Signal = EMA_9(MACD)$$
  $$Histogram = MACD - Signal$$

### Volatility Indicators
* **Average True Range (ATR 14)**:
  $$TR = \max(High - Low, |High - Close_{t-1}|, |Low - Close_{t-1}|)$$
  $$ATR_{14} = \text{Rolling 14-period mean of } TR$$

* **Historical Volatility (20-day Annualized)**:
  $$\sigma_{20d} = \text{std}(\ln(Close_t / Close_{t-1})) \cdot \sqrt{252}$$

---

## 2. Market Regime Framework

Market environment classification relies on benchmark NIFTY 50 price alignment relative to key moving averages (20, 50, 200 DMA) combined with broad market breadth (percentage of tracked stocks above 50 DMA):

* **Strong Bullish**: NIFTY > 50 DMA & 200 DMA, Market Breadth $\ge 70\%$
* **Bullish**: NIFTY > 50 DMA, Market Breadth $\ge 50\%$
* **Neutral**: NIFTY mixed vs DMAs, Market Breadth $40\% - 50\%$
* **Bearish**: NIFTY < 50 DMA or Market Breadth $< 45\%$
* **Strong Bearish**: NIFTY < 50 & 200 DMA, Market Breadth $\le 30\%$

---

## 3. Sector Rankings & Relative Strength

Sector rankings order sector performance by combining short-term and multi-week momentum relative to the benchmark NIFTY 50 index:

$$\text{Relative Strength}_{20d} = Return_{20d}(\text{Sector}) - Return_{20d}(\text{NIFTY})$$

$$\text{Momentum Score} = \text{Clip}\left(50 + 200 \cdot Ret_{1d} + 150 \cdot Ret_{5d} + 100 \cdot Ret_{20d}, 0, 100\right)$$

---

## 4. Composite Stock Scoring (0–100)

Every stock receives a transparent score based on explicit weights:

$$\text{Score} = 0.20 \cdot S_{Trend} + 0.20 \cdot S_{Mom} + 0.15 \cdot S_{Vol} + 0.15 \cdot S_{RS} + 0.10 \cdot S_{Volat} + 0.10 \cdot S_{Regime} + 0.10 \cdot S_{Sector}$$

---

## 5. Historical Analogue Pattern Matching

To evaluate empirical forward probabilities, the engine queries the stock's historical time series (excluding the recent 25 days to avoid self-overlap) for trading days matching current conditions:

1. **RSI Condition**: $RSI_{hist} \in [RSI_{current} - 7.5, RSI_{current} + 7.5]$
2. **MA Distance Condition**: $DistSMA20_{hist} \in [DistSMA20_{current} - 0.03, DistSMA20_{current} + 0.03]$

For all matching historical dates $t_m$, forward returns over horizons $h \in \{1, 3, 5, 10, 20\}$ days are measured:

$$R_{fwd, h} = \frac{Close(t_m + h) - Close(t_m)}{Close(t_m)}$$

From this sample set, empirical statistics are stored:
* Positive return probability $P(R_{fwd, h} > 0)$
* Mean & median forward returns
* Maximum gain and loss
* Forward volatility
