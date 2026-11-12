"""Technical Analysis Summary and Recommendation Meter component (TailAdmin style)."""

from typing import Any, Dict
import streamlit as st


def render_technical_summary_card(summary: Dict[str, Any]) -> None:
    """Render technical verdict, score gauge, and breakdown of indicator signals."""
    if not summary:
        return

    verdict = summary.get("verdict", "NEUTRAL")
    score = summary.get("score", 0)
    buy_cnt = summary.get("buy_count", 0)
    neu_cnt = summary.get("neutral_count", 0)
    sell_cnt = summary.get("sell_count", 0)
    details = summary.get("details", [])

    # Badge styling
    badge_map = {
        "STRONG BUY": "badge-strong-buy",
        "BUY": "badge-buy",
        "NEUTRAL": "badge-neutral",
        "SELL": "badge-sell",
        "STRONG SELL": "badge-strong-sell",
    }
    badge_class = badge_map.get(verdict, "badge-neutral")

    # Score normalized to 0-100% for the gauge bar (where -100 -> 0%, 0 -> 50%, +100 -> 100%)
    gauge_pct = (score + 100) / 2.0

    card_html = (
        f'<div class="fintech-card" style="margin-bottom: 12px;">'
        f'<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px;">'
        f'<div>'
        f'<span class="kpi-title">Technical Consensus</span>'
        f'<div style="font-size: 1.1rem; font-weight: 700; color: var(--text-primary); margin-top: 2px;">Market Momentum</div>'
        f'</div>'
        f'<span class="{badge_class}">{verdict}</span>'
        f'</div>'
        f'<div style="margin-bottom: 10px;">'
        f'<div style="display: flex; justify-content: space-between; font-size: 0.75rem; color: var(--text-muted); font-family: var(--font-mono); font-weight: 600;">'
        f'<span style="color: var(--loss-color);">STRONG SELL (-100)</span>'
        f'<span>NEUTRAL (0)</span>'
        f'<span style="color: var(--gain-color);">STRONG BUY (+100)</span>'
        f'</div>'
        f'<div class="range-bar-container" style="height: 8px; margin-top: 6px;">'
        f'<div class="range-bar-fill" style="width: {gauge_pct:.1f}%; background: linear-gradient(90deg, var(--loss-color), #F59E0B, var(--gain-color));"></div>'
        f'</div>'
        f'<div style="text-align: center; margin-top: 8px; font-family: var(--font-mono); font-size: 0.85rem; color: var(--text-primary); font-weight: 600;">'
        f'Consensus Score: <span style="font-weight: 800; color: #3B82F6;">{score:+d}</span> / 100'
        f'</div>'
        f'</div>'
        f'<div style="display: flex; justify-content: space-around; background: #F8FAFC; border: 1px solid #E2E8F0; padding: 10px; border-radius: 10px; margin-top: 12px; font-size: 0.85rem;">'
        f'<span style="color: var(--gain-color); font-weight: 700;">{buy_cnt} Buy</span>'
        f'<span style="color: var(--text-muted); font-weight: 700;">{neu_cnt} Neutral</span>'
        f'<span style="color: var(--loss-color); font-weight: 700;">{sell_cnt} Sell</span>'
        f'</div>'
        f'</div>'
    )
    st.markdown(card_html, unsafe_allow_html=True)

    # Detailed indicator signals breakdown expander/table
    with st.expander("Indicator Breakdown", expanded=False):
        for item in details:
            ind_name = item["indicator"]
            val = item["value"]
            sig = item["signal"]
            sig_class = badge_map.get(sig, "badge-neutral")
            col1, col2, col3 = st.columns([0.45, 0.35, 0.20])
            with col1:
                st.markdown(f"<span style='font-size: 0.85rem; font-weight: 600; color: var(--text-primary);'>{ind_name}</span>", unsafe_allow_html=True)
            with col2:
                st.markdown(f"<span style='font-family: var(--font-mono); font-size: 0.85rem; color: var(--text-muted);'>{val}</span>", unsafe_allow_html=True)
            with col3:
                st.markdown(f"<span class='{sig_class}' style='font-size: 0.75rem; padding: 2px 8px;'>{sig}</span>", unsafe_allow_html=True)
