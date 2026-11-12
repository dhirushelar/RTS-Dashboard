<div align="center">

# 📈 RTS Terminal — Real-Time Stock Market Dashboard

**A high-performance market intelligence platform built with Python, Streamlit, Pandas, NumPy, and Plotly.**

[![Python Version](https://img.shields.io/badge/Python-3.11%2B-blue?style=flat-square&logo=python)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.35%2B-red?style=flat-square&logo=streamlit)](https://streamlit.io/)
[![Plotly](https://img.shields.io/badge/Plotly-5.18%2B-blueviolet?style=flat-square&logo=plotly)](https://plotly.com/)
[![Tests](https://img.shields.io/badge/Tests-17%20Passed-brightgreen?style=flat-square&logo=pytest)](https://docs.pytest.org/)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)

[**Live Code Repository**](https://github.com/dhirushelar/RTS-Dashboard) • [**Deploy on Streamlit Cloud**](https://share.streamlit.io/deploy?repository=dhirushelar/RTS-Dashboard&branch=main&mainModule=app.py)

</div>

---

## 📌 Overview

**RTS Terminal** is a lightweight, zero-credential stock market intelligence workstation. It combines a clean fintech user experience with quantitative technical analysis, sub-second telemetry polling, and full multi-touch gesture charting.

The application communicates directly with financial market data endpoints using automatic exponential backoff retries, providing reliable price tracking across both US equity markets (NASDAQ, NYSE) and Indian exchanges (NSE, BSE).

---

## ✨ Features

- **⚡ Live Polling Engine (`st.fragment`)**: Automatically polls market telemetry at user-defined intervals (5s, 15s, 30s, 60s) and updates the dashboard without reloading the page.
- **🌐 Zero-Credential Market Data**: Fetches historical OHLCV data and quotes via public endpoints with retry management.
- **💱 Dual-Currency Support**: Automatically switches between USD (`$`) for US equities and INR (`₹`) for Indian equities based on ticker suffix.
- **📊 Interactive Financial Charts**: Multigraph candlestick and volume layouts with style selection (Candles, Line, Area), crosshairs, and range sliders.
- **🔍 Full Trackpad & Touch Gestures**: Two-finger scroll-to-zoom on trackpads, pinch-to-zoom on mobile touchscreens, and double-click zoom reset.
- **🎞️ Continuous Ticker Tape**: Hardware-accelerated CSS animated ticker displaying live asset prices and price movement badges.
- **💳 4-Card Executive KPI Row**: Real-time price tracking, session range bar, volume comparison against 30-day moving averages, and 52-week position.
- **🧭 Quantitative Momentum Consensus**: Combines 5 distinct technical indicators into a single score between -100 and +100 with directional badges.
- **💼 Interactive Watchlist**: Easily track assets, inspect Top Movers (Session Leaders), and quickly change the primary active stock.
- **📈 Normalized Comparison Chart**: Benchmarks comparative percentage performance across 2 to 4 assets from a shared baseline.

---

## 📐 Mathematical Indicators

All technical indicators are implemented directly with NumPy and Pandas:

### 1. Simple Moving Average (SMA)
Calculates the mean close price over an $n$-period rolling window:
$$\text{SMA}_t = \frac{1}{n} \sum_{i=0}^{n-1} P_{t-i}$$

### 2. Exponential Moving Average (EMA)
Applies exponential smoothing to prioritize recent pricing behavior:
$$\text{EMA}_t = \alpha \cdot P_t + (1 - \alpha) \cdot \text{EMA}_{t-1}, \quad \text{where } \alpha = \frac{2}{n + 1}$$

### 3. Relative Strength Index (RSI 14)
Measures the speed and change of price movements using Wilder's smoothing method:
$$\text{RS} = \frac{\text{Average Gain}}{\text{Average Loss}}, \quad \text{RSI} = 100 - \left( \frac{100}{1 + \text{RS}} \right)$$

### 4. Moving Average Convergence Divergence (MACD)
Evaluates moving average momentum divergences:
$$\text{MACD Line} = \text{EMA}_{12}(P) - \text{EMA}_{26}(P)$$
$$\text{Signal Line} = \text{EMA}_{9}(\text{MACD Line})$$
$$\text{Histogram} = \text{MACD Line} - \text{Signal Line}$$

### 5. Bollinger Bands
Constructs dynamic volatility thresholds using standard deviation $\sigma$:
$$\text{Middle} = \text{SMA}_{20}(P), \quad \text{Upper} = \text{Middle} + (2 \cdot \sigma), \quad \text{Lower} = \text{Middle} - (2 \cdot \sigma)$$

### 6. Volume-Weighted Average Price (VWAP)
Weights typical price values by transaction volume with session reset:
$$\text{Typical Price (TP)} = \frac{\text{High} + \text{Low} + \text{Close}}{3}$$
$$\text{VWAP} = \frac{\sum (\text{TP} \cdot \text{Volume})}{\sum \text{Volume}}$$

### 7. Technical Consensus Engine
Aggregates signal conditions across all indicators into a directional index:
$$\text{Score} = \left( \frac{\text{Buy Signals} - \text{Sell Signals}}{\text{Total Evaluated}} \right) \times 100$$

---

## 📁 Repository Structure

```text
RTS-Dashboard/
├── app.py                      # Main application entry point & layout assembly
├── config.py                   # Central constants, symbol catalog, and color settings
├── requirements.txt            # Production Python package dependencies
├── .env.example                # Template for optional custom API credentials
├── .gitignore                  # Git exclusions for environments, caches, and secrets
├── README.md                   # Project documentation
├── .streamlit/
│   └── config.toml             # Streamlit theme and server configuration
├── assets/
│   └── style.css               # Design system styling, typography, and CSS animations
├── services/
│   ├── __init__.py
│   ├── data_provider.py        # API client, retry strategy, and data parser
│   └── cache.py                # Streamlit cache_data wrappers with synchronized TTLs
├── analytics/
│   ├── __init__.py
│   └── indicators.py           # Pure Pandas/NumPy technical indicators
├── charts/
│   ├── __init__.py
│   └── plots.py                # Plotly layout templates, candlestick subplots, and overlays
├── components/
│   ├── __init__.py
│   ├── kpi_cards.py            # 4-card metric strip with day/52W range progress bars
│   ├── watchlist.py            # Interactive watchlist table and session leaders tabs
│   ├── ticker_strip.py         # Hardware-accelerated continuous scrolling ticker tape
│   └── summary.py              # Technical consensus momentum gauge and signal breakdown
└── tests/
    ├── __init__.py
    ├── test_indicators.py       # Mathematical unit tests against ground-truth values
    └── test_data_provider.py    # Unit tests for network parsing and error handling
```

---

## 🛠️ Installation & Setup

### Prerequisites
- Python 3.11+
- Git

### 1. Clone the Repository
```bash
git clone https://github.com/dhirushelar/RTS-Dashboard.git
cd RTS-Dashboard
```

### 2. Set Up Virtual Environment
```bash
python -m venv venv

# On macOS/Linux:
source venv/bin/activate

# On Windows:
venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the Dashboard
```bash
streamlit run app.py
```
Visit **http://localhost:8501** in your browser.

---

## 🧪 Testing

Execute the automated test suite with pytest:

```bash
pytest -v
```

All 17 test cases verify indicator math, edge cases (empty data, flat series), and data parsing routines.

---

## ☁️ Deployment

### Streamlit Community Cloud
1. Push your repository to GitHub.
2. Sign in to [share.streamlit.io](https://share.streamlit.io).
3. Connect your repository (`dhirushelar/RTS-Dashboard`), set the main file to `app.py`, and click **Deploy**.

---

## 📄 License

This project is open-source under the [MIT License](LICENSE).
