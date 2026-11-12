"""Main application entry point for the Real-Time Stock Market Dashboard (TailAdmin theme)."""

import datetime as dt
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
import streamlit as st

import config
from charts.plots import (
    build_comparison_chart,
    build_macd_chart,
    build_main_price_chart,
    build_rsi_chart,
)
from components.kpi_cards import render_kpi_cards
from components.summary import render_technical_summary_card
from components.ticker_strip import render_ticker_strip
from components.watchlist import render_watchlist_panel
from services.cache import (
    clear_market_cache,
    fetch_cached_history,
    fetch_cached_multi_quotes,
)
from analytics.indicators import generate_technical_summary

logger = logging.getLogger(__name__)

# Configure Streamlit page layout
st.set_page_config(
    page_title=f"{config.APP_TITLE} | RTS Terminal",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)


# Interactive Chart Config supporting two-finger pinch-zoom, trackpad scroll zoom & touch gestures
PLOTLY_CONFIG: Dict[str, Any] = {
    "scrollZoom": True,
    "displayModeBar": True,
    "displaylogo": False,
    "modeBarButtonsToAdd": ["zoomIn2d", "zoomOut2d", "autoScale2d", "resetScale2d"],
    "modeBarButtonsToRemove": ["lasso2d", "select2d"],
    "responsive": True,
}


def load_css() -> None:
    """Inject external design system stylesheet."""
    css_path = Path(__file__).parent / "assets" / "style.css"
    if css_path.exists():
        with open(css_path, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


def init_session_state() -> None:
    """Initialize state variables if not already set."""
    if "active_symbol" not in st.session_state:
        st.session_state["active_symbol"] = config.DEFAULT_SYMBOL
    if "watchlist" not in st.session_state:
        st.session_state["watchlist"] = list(config.DEFAULT_WATCHLIST)
    if "range_period" not in st.session_state:
        st.session_state["range_period"] = "1d"
    if "interval" not in st.session_state:
        st.session_state["interval"] = "5m"
    if "chart_type" not in st.session_state:
        st.session_state["chart_type"] = "Candle"
    if "show_sma" not in st.session_state:
        st.session_state["show_sma"] = True
    if "show_ema" not in st.session_state:
        st.session_state["show_ema"] = False
    if "show_bollinger" not in st.session_state:
        st.session_state["show_bollinger"] = False
    if "show_vwap" not in st.session_state:
        st.session_state["show_vwap"] = True
    if "auto_refresh" not in st.session_state:
        st.session_state["auto_refresh"] = True
    if "refresh_interval" not in st.session_state:
        st.session_state["refresh_interval"] = config.DEFAULT_REFRESH_INTERVAL
    if "compare_symbols" not in st.session_state:
        st.session_state["compare_symbols"] = ["AAPL", "MSFT", "TSLA"]


def set_active_symbol(sym: str) -> None:
    """Callback to switch primary active ticker."""
    st.session_state["active_symbol"] = sym


def render_sidebar() -> None:
    """Render sleek modern white sidebar with crisp high-contrast controls."""
    with st.sidebar:
        brand_html = (
            f'<div style="display: flex; align-items: center; gap: 12px; margin-top: 0px; margin-bottom: 14px; padding: 0;">'
            f'<div style="background: linear-gradient(135deg, #3B82F6, #1D4ED8); width: 36px; height: 36px; border-radius: 10px; display: flex; align-items: center; justify-content: center; font-size: 1.15rem; box-shadow: 0 4px 10px rgba(59, 130, 246, 0.35);">'
            f'📈'
            f'</div>'
            f'<div>'
            f'<div style="font-weight: 800; font-size: 1.18rem; letter-spacing: -0.02em; color: #0F172A; line-height: 1.12;">Dashboard</div>'
            f'<div style="font-size: 0.68rem; color: #64748B; letter-spacing: 0.08em; font-weight: 700; text-transform: uppercase;">FINTECH TERMINAL</div>'
            f'</div>'
            f'</div>'
        )
        st.markdown(brand_html, unsafe_allow_html=True)

        # 1. Target Stock Dropdown
        st.markdown('<div class="sidebar-section-title">ACTIVE ASSET</div>', unsafe_allow_html=True)
        all_catalog = list(config.SYMBOL_CATALOG.keys())
        current_sym = st.session_state["active_symbol"]
        idx = all_catalog.index(current_sym) if current_sym in all_catalog else 0

        selected = st.selectbox(
            "Select Ticker",
            options=all_catalog,
            index=idx,
            format_func=lambda s: f"{config.get_symbol_avatar(s)} {s} — {config.get_company_name(s)}",
            label_visibility="collapsed",
        )
        if selected != current_sym:
            st.session_state["active_symbol"] = selected
            st.rerun()

        st.markdown("<hr style='border-color: #F1F5F9; margin: 16px 0;'>", unsafe_allow_html=True)

        # 2. Timeframe & Interval
        st.markdown('<div class="sidebar-section-title">TIMEFRAME & RESOLUTION</div>', unsafe_allow_html=True)
        col_rng, col_int = st.columns(2)
        with col_rng:
            range_choice = st.selectbox(
                "Range",
                options=config.VALID_RANGES,
                index=config.VALID_RANGES.index(st.session_state["range_period"]),
                format_func=lambda r: config.RANGE_LABELS.get(r, r.upper()),
            )
            if range_choice != st.session_state["range_period"]:
                st.session_state["range_period"] = range_choice
                st.session_state["interval"] = config.RANGE_DEFAULT_INTERVALS.get(range_choice, "1d")
                st.rerun()

        with col_int:
            interval_choice = st.selectbox(
                "Interval",
                options=config.VALID_INTERVALS,
                index=config.VALID_INTERVALS.index(st.session_state["interval"]) if st.session_state["interval"] in config.VALID_INTERVALS else 0,
            )
            if interval_choice != st.session_state["interval"]:
                st.session_state["interval"] = interval_choice
                st.rerun()

        st.markdown("<hr style='border-color: #F1F5F9; margin: 16px 0;'>", unsafe_allow_html=True)

        # 3. Technical Indicator Overlays
        st.markdown('<div class="sidebar-section-title">TECHNICAL OVERLAYS</div>', unsafe_allow_html=True)
        st.session_state["show_sma"] = st.checkbox("SMA (20)", value=st.session_state["show_sma"])
        st.session_state["show_ema"] = st.checkbox("EMA (20)", value=st.session_state["show_ema"])
        st.session_state["show_bollinger"] = st.checkbox("Bollinger Bands (20, 2)", value=st.session_state["show_bollinger"])
        st.session_state["show_vwap"] = st.checkbox("VWAP", value=st.session_state["show_vwap"])

        st.markdown("<hr style='border-color: #F1F5F9; margin: 16px 0;'>", unsafe_allow_html=True)

        # 4. Live Polling Settings
        st.markdown('<div class="sidebar-section-title">REAL-TIME STREAMING</div>', unsafe_allow_html=True)
        st.session_state["auto_refresh"] = st.toggle("Live Telemetry", value=st.session_state["auto_refresh"])
        if st.session_state["auto_refresh"]:
            st.session_state["refresh_interval"] = st.select_slider(
                "Update Frequency",
                options=config.AUTO_REFRESH_INTERVALS,
                value=st.session_state["refresh_interval"],
                format_func=lambda s: f"{s}s",
            )


def render_top_bar(quote: Optional[Dict[str, Any]]) -> None:
    """Render floating top header bar with live status and sync controls."""
    col_left, col_right = st.columns([0.68, 0.32])

    is_open = quote.get("is_market_open", False) if quote else False
    status_label = quote.get("market_status", "Market Active") if quote else "Market Active"
    status_class = "market-status-open" if is_open else "market-status-closed"
    dot_class = "dot-green" if is_open else "dot-gray"
    now_str = dt.datetime.now().strftime("%H:%M:%S")

    with col_left:
        bar_html = (
            f'<div class="top-bar-container">'
            f'<div style="display: flex; align-items: center; gap: 14px;">'
            f'<span class="market-status-pill {status_class}">'
            f'<span class="pulsing-dot {dot_class}"></span>'
            f'{status_label}'
            f'</span>'
            f'<span style="font-size: 0.82rem; color: #64748B; font-family: var(--font-mono);">'
            f'Real-Time Feed | Last Sync: {now_str}'
            f'</span>'
            f'</div>'
            f'</div>'
        )
        st.markdown(bar_html, unsafe_allow_html=True)

    with col_right:
        r_col1, r_col2 = st.columns([0.5, 0.5])
        with r_col2:
            if st.button("🔄 Sync Now", use_container_width=True):
                clear_market_cache()
                st.rerun()


def run_dashboard_body() -> None:
    """Core dashboard body executing inside live updating fragment."""
    active_sym = st.session_state["active_symbol"]
    range_val = st.session_state["range_period"]
    interval_val = st.session_state["interval"]
    watchlist_syms = st.session_state["watchlist"]

    # 1. Fetch live quotes for active symbol and watchlist
    symbols_to_fetch = list(set([active_sym] + watchlist_syms + st.session_state["compare_symbols"]))
    quotes_dict = fetch_cached_multi_quotes(symbols_to_fetch)
    active_quote = quotes_dict.get(active_sym)

    # 2. Render Top Bar & Scrolling Ticker Strip
    render_top_bar(active_quote)
    render_ticker_strip(quotes_dict)

    # 3. Render KPI 4-Card Strip (Matching top cards in reference)
    render_kpi_cards(active_quote)

    st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)

    # 4. Fetch Historical Candle Data
    with st.spinner(f"Loading {active_sym} live telemetry..."):
        df_history, error_msg = fetch_cached_history(
            symbol=active_sym,
            range_period=range_val,
            interval=interval_val,
        )

    # Error handling display
    if error_msg:
        st.markdown(
            f'<div class="error-banner"><span>⚠️</span><div>{error_msg}</div></div>',
            unsafe_allow_html=True,
        )

    # 5. Main Layout: Left Main Chart (65%), Right Watchlist (35%)
    main_col, right_col = st.columns([0.65, 0.35], gap="medium")

    with main_col:
        # Chart Card
        st.markdown(
            f'<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">'
            f'<div>'
            f'<span style="font-size: 0.85rem; font-weight: 700; color: #1E293B; text-transform: uppercase; letter-spacing: 0.05em;">{active_sym} Interactive Chart</span>'
            f'</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

        c_type_col, chip_col = st.columns([0.35, 0.65])
        with c_type_col:
            st.session_state["chart_type"] = st.radio(
                "Chart Style",
                options=["Candle", "Line", "Area"],
                horizontal=True,
                index=["Candle", "Line", "Area"].index(st.session_state["chart_type"]),
                label_visibility="collapsed",
            )
        with chip_col:
            chips = ["1d", "5d", "1mo", "6mo", "1y", "5y"]
            chip_cols = st.columns(len(chips))
            for i, chip in enumerate(chips):
                with chip_cols[i]:
                    label = config.RANGE_LABELS.get(chip, chip)
                    is_sel = (chip == range_val)
                    if st.button(label, key=f"chip_{chip}", disabled=is_sel, use_container_width=True):
                        st.session_state["range_period"] = chip
                        st.session_state["interval"] = config.RANGE_DEFAULT_INTERVALS.get(chip, "1d")
                        st.rerun()

        # Render Main Price & Volume Chart
        fig_main = build_main_price_chart(
            df=df_history,
            symbol=active_sym,
            chart_type=st.session_state["chart_type"],
            show_sma=st.session_state["show_sma"],
            show_ema=st.session_state["show_ema"],
            show_bollinger=st.session_state["show_bollinger"],
            show_vwap=st.session_state["show_vwap"],
        )
        st.plotly_chart(fig_main, use_container_width=True, config=PLOTLY_CONFIG)
        st.caption("🔍 Tip: Use 2-finger scroll on trackpad or pinch on mobile to zoom in/out • Double-click/tap to reset")

    with right_col:
        # Watchlist & Movers panel
        render_watchlist_panel(
            watchlist_symbols=watchlist_syms,
            quotes=quotes_dict,
            current_symbol=active_sym,
            on_select_symbol=set_active_symbol,
        )

    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

    # 6. Lower Row: RSI(14) and MACD Indicators
    rsi_col, macd_col = st.columns(2, gap="medium")
    with rsi_col:
        st.markdown(
            '<div class="kpi-title" style="margin-left: 4px; margin-bottom: 4px;">Relative Strength Index (RSI 14)</div>',
            unsafe_allow_html=True,
        )
        fig_rsi = build_rsi_chart(df_history, period=14)
        st.plotly_chart(fig_rsi, use_container_width=True, config=PLOTLY_CONFIG)

    with macd_col:
        st.markdown(
            '<div class="kpi-title" style="margin-left: 4px; margin-bottom: 4px;">MACD (12, 26, 9) Momentum</div>',
            unsafe_allow_html=True,
        )
        fig_macd = build_macd_chart(df_history)
        st.plotly_chart(fig_macd, use_container_width=True, config=PLOTLY_CONFIG)

    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

    # 7. Bottom Row: Compare Stocks & Technical Consensus Summary
    comp_col, summ_col = st.columns([0.60, 0.40], gap="medium")

    with comp_col:
        st.markdown(
            '<div class="kpi-title" style="margin-left: 4px; margin-bottom: 4px;">Comparative Performance (% Normalization)</div>',
            unsafe_allow_html=True,
        )
        comp_histories: Dict[str, Any] = {}
        for c_sym in st.session_state["compare_symbols"]:
            c_df, _ = fetch_cached_history(c_sym, range_period=range_val, interval=interval_val)
            if not c_df.empty:
                comp_histories[c_sym] = c_df

        fig_comp = build_comparison_chart(comp_histories)
        st.plotly_chart(fig_comp, use_container_width=True, config=PLOTLY_CONFIG)

        new_compare = st.multiselect(
            "Selected Benchmarks",
            options=list(config.SYMBOL_CATALOG.keys()),
            default=st.session_state["compare_symbols"],
            max_selections=4,
            label_visibility="collapsed",
        )
        if new_compare != st.session_state["compare_symbols"]:
            st.session_state["compare_symbols"] = new_compare
            st.rerun()

    with summ_col:
        tech_summary = generate_technical_summary(df_history)
        render_technical_summary_card(tech_summary)


def main() -> None:
    """Initialize environment, styles, and assemble application layout."""
    init_session_state()
    load_css()
    render_sidebar()

    refresh_rate = st.session_state["refresh_interval"] if st.session_state["auto_refresh"] else None

    @st.fragment(run_every=refresh_rate)
    def live_fragment() -> None:
        run_dashboard_body()

    live_fragment()


if __name__ == "__main__":
    main()
