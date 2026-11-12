"""Horizontally scrolling live ticker tape component built with pure CSS."""

from typing import Any, Dict
import streamlit as st
import config


def render_ticker_strip(quotes: Dict[str, Dict[str, Any]]) -> None:
    """Render continuous auto-scrolling ticker strip."""
    if not quotes:
        return

    items_html = []
    for symbol, q in quotes.items():
        price = q.get("price", 0.0)
        pct = q.get("percent_change", 0.0)
        curr = config.get_currency_symbol(symbol)
        is_pos = pct >= 0
        sign = "+" if is_pos else ""
        badge_class = "badge-gain" if is_pos else "badge-loss"
        arrow = "▲" if is_pos else "▼"

        # Explicitly zero leading whitespace to prevent Markdown code block interpretation
        item_str = (
            f'<div class="ticker-item">'
            f'<span class="ticker-symbol">{symbol}</span>'
            f'<span class="ticker-price">{curr}{price:,.2f}</span>'
            f'<span class="{badge_class}">{arrow} {sign}{pct:.2f}%</span>'
            f'</div>'
        )
        items_html.append(item_str)

    track_content = "".join(items_html)
    # Duplicate track for seamless infinite scroll
    combined_track = track_content + track_content

    html_content = (
        f'<div class="ticker-strip-wrapper">'
        f'<div class="ticker-track">{combined_track}</div>'
        f'</div>'
    )
    st.markdown(html_content, unsafe_allow_html=True)
