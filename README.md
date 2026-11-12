# Real-Time Stock Market Dashboard

A sleek, modern, high-performance fintech dashboard designed with the **Linear / Vercel** design language. Built with Python 3.11+, Streamlit, Pandas, NumPy, Plotly, and Requests.

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://rts-dashboard.streamlit.app/)

🌐 **Live Production URL**: [https://rts-dashboard.streamlit.app/](https://rts-dashboard.streamlit.app/)

---

## TailAdmin Design System (Permanent Theme)

- **Dark Navy Sidebar (`#1C2434`)**: High-contrast, clean navigation menu with category sections (`ACTIVE ASSET`, `TIMEFRAME & RESOLUTION`, `TECHNICAL OVERLAYS`, `REAL-TIME STREAMING`), dark input surfaces, and subtle blue active accents.
- **Clean Canvas (`#F4F7FB`)**: Soft slate-gray background providing contrast against content cards.
- **Pure White Cards (`#FFFFFF`)**: Floating cards with 14-16px border-radius, 1px border (`#E2E8F0`), and soft elevation shadows (`box-shadow: 0 2px 8px rgba(0, 0, 0, 0.03)`).
- **Dual Typography**: **Plus Jakarta Sans** and **Inter** for clean headings and interface controls; **JetBrains Mono** with tabular numerals for digits and market metrics.
- **Financial Semantics**: Emerald green (`#10B981`) for positive returns, and Crimson rose (`#EF4444`) for losses.
- **Fully Mobile Responsive**: Dynamic layout with media queries (`@media (max-width: 768px)`) that stacks cards cleanly on mobile screens with touch-friendly controls.

---

## Features

- **Live Scrolling Ticker Tape**: Infinite CSS hardware-accelerated scrolling tape displaying real-time quotes, avatars, and price changes.
- **Top KPI Cards**: 4-card metric strip featuring asset avatar, current price, day range bar, volume comparison against 30-day average, and 52-week position.
- **Interactive Plotly Charts**: Candlestick, Line, and Area views with volume subplot, range sliders, crosshairs, and toggleable indicators (SMA, EMA, Bollinger Bands, VWAP).
- **Secondary Analytics**: Dedicated subplots for **RSI(14)** (shaded 30/70 boundary zones) and **MACD(12, 26, 9)**.
- **Watchlist & Movers**: Interactive watchlist with one-click asset switching, quick additions, and session top gainers/losers.
- **Comparative Benchmarking**: Multi-stock normalized performance comparison.
- **Technical Consensus Summary**: Momentum index gauge from -100 to +100 with Buy/Neutral/Sell breakdown.

---

## Quickstart & Installation

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run the application
streamlit run app.py

# 3. Run unit tests
pytest
```
