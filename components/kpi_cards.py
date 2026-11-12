"""KPI Cards component displaying real-time metrics, ranges, and volume analysis."""

from typing import Any, Dict, Optional
import streamlit as st
import config


def _format_compact(val: Optional[float], prefix: str = "") -> str:
    """Format large numerical values into readable human format (K, M, B, T)."""
    if val is None or val == 0:
        return "N/A"
    abs_val = abs(val)
    if abs_val >= 1e12:
        return f"{prefix}{val / 1e12:.2f}T"
    if abs_val >= 1e9:
        return f"{prefix}{val / 1e9:.2f}B"
    if abs_val >= 1e6:
        return f"{prefix}{val / 1e6:.2f}M"
    if abs_val >= 1e3:
        return f"{prefix}{val / 1e3:.2f}K"
    return f"{prefix}{val:,.2f}"


def render_kpi_cards(quote: Dict[str, Any]) -> None:
    """Render the 4-card metric strip."""
    if not quote:
        st.warning("Awaiting market quote data...")
        return

    symbol = quote.get("symbol", "")
    avatar = config.get_symbol_avatar(symbol)
    currency = quote.get("currency", "$")
    price = quote.get("price", 0.0)
    change = quote.get("change", 0.0)
    pct_change = quote.get("percent_change", 0.0)
    day_high = quote.get("day_high", price)
    day_low = quote.get("day_low", price)
    volume = quote.get("volume", 0)
    avg_vol = quote.get("avg_volume", volume)
    high_52 = quote.get("fifty_two_week_high", day_high)
    low_52 = quote.get("fifty_two_week_low", day_low)
    market_cap = quote.get("market_cap")

    is_positive = change >= 0
    change_sign = "+" if is_positive else ""
    badge_class = "badge-gain" if is_positive else "badge-loss"
    diff_indicator = "▲" if is_positive else "▼"

    # Compute Day range bar percent
    day_span = day_high - day_low
    day_pos_pct = ((price - day_low) / day_span * 100.0) if day_span > 0 else 50.0
    day_pos_pct = max(0.0, min(100.0, day_pos_pct))

    # Compute 52-week range percent
    span_52 = high_52 - low_52
    pos_52_pct = ((price - low_52) / span_52 * 100.0) if span_52 > 0 else 50.0
    pos_52_pct = max(0.0, min(100.0, pos_52_pct))

    vol_ratio = (volume / avg_vol * 100.0) if avg_vol > 0 else 100.0

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        html1 = (
            f'<div class="fintech-card">'
            f'<div class="kpi-header">'
            f'<span class="kpi-title">{symbol} Price</span>'
            f'<div class="kpi-icon-badge">{avatar}</div>'
            f'</div>'
            f'<div class="kpi-value">{currency}{price:,.2f}</div>'
            f'<div class="kpi-subtext">'
            f'<span class="{badge_class}">'
            f'{diff_indicator} {change_sign}{change:,.2f} ({change_sign}{pct_change:.2f}%)'
            f'</span>'
            f'</div>'
            f'</div>'
        )
        st.markdown(html1, unsafe_allow_html=True)

    with col2:
        html2 = (
            f'<div class="fintech-card">'
            f'<div class="kpi-header">'
            f'<span class="kpi-title">Day Session Range</span>'
            f'<div class="kpi-icon-badge">📊</div>'
            f'</div>'
            f'<div class="kpi-value" style="font-size: 1.35rem; font-weight: 600;">{currency}{day_low:,.2f} – {currency}{day_high:,.2f}</div>'
            f'<div class="range-bar-container">'
            f'<div class="range-bar-fill" style="width: {day_pos_pct:.1f}%;"></div>'
            f'</div>'
            f'<div class="range-labels">'
            f'<span>Low: {currency}{day_low:,.2f}</span>'
            f'<span>High: {currency}{day_high:,.2f}</span>'
            f'</div>'
            f'</div>'
        )
        st.markdown(html2, unsafe_allow_html=True)

    with col3:
        vol_formatted = _format_compact(volume)
        avg_formatted = _format_compact(avg_vol)
        vol_note_color = "var(--gain-color)" if vol_ratio >= 100 else "var(--text-muted)"
        html3 = (
            f'<div class="fintech-card">'
            f'<div class="kpi-header">'
            f'<span class="kpi-title">Trading Volume</span>'
            f'<div class="kpi-icon-badge">📈</div>'
            f'</div>'
            f'<div class="kpi-value">{vol_formatted}</div>'
            f'<div class="kpi-subtext">'
            f'<span style="color: {vol_note_color}; font-family: var(--font-mono); font-weight: 700;">{vol_ratio:.1f}%</span> '
            f'<span style="color: var(--text-muted);">of 30D avg ({avg_formatted})</span>'
            f'</div>'
            f'</div>'
        )
        st.markdown(html3, unsafe_allow_html=True)

    with col4:
        mcap_str = _format_compact(market_cap, prefix=currency) if market_cap else "Large Cap"
        html4 = (
            f'<div class="fintech-card">'
            f'<div class="kpi-header">'
            f'<span class="kpi-title">Market Cap / 52W</span>'
            f'<div class="kpi-icon-badge">🌐</div>'
            f'</div>'
            f'<div class="kpi-value">{mcap_str}</div>'
            f'<div class="range-bar-container">'
            f'<div class="range-bar-fill" style="width: {pos_52_pct:.1f}%;"></div>'
            f'</div>'
            f'<div class="range-labels">'
            f'<span>52W L: {currency}{low_52:,.2f}</span>'
            f'<span>52W H: {currency}{high_52:,.2f}</span>'
            f'</div>'
            f'</div>'
        )
        st.markdown(html4, unsafe_allow_html=True)
