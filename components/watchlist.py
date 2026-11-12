"""Watchlist management and Top Gainers / Losers component (TailAdmin style)."""

from typing import Any, Callable, Dict, List
import streamlit as st
import config


def render_watchlist_panel(
    watchlist_symbols: List[str],
    quotes: Dict[str, Dict[str, Any]],
    current_symbol: str,
    on_select_symbol: Callable[[str], None],
) -> None:
    """Render right-panel tabs for My Stocks Watchlist and Session Leaders."""
    tabs = st.tabs(["My Stocks", "Market Movers"])

    # Tab 1: Watchlist (My Stocks)
    with tabs[0]:
        header_html = (
            f'<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">'
            f'<span style="font-size: 0.85rem; font-weight: 700; color: var(--text-primary); text-transform: uppercase; letter-spacing: 0.05em;">Watchlist Assets</span>'
            f'<span style="font-size: 0.75rem; color: var(--text-muted); background: #F1F5F9; padding: 2px 8px; border-radius: 999px; font-weight: 600;">{len(watchlist_symbols)} tracked</span>'
            f'</div>'
        )
        st.markdown(header_html, unsafe_allow_html=True)

        if not watchlist_symbols:
            st.info("Watchlist is empty. Add symbols using the input below.")
        else:
            for sym in watchlist_symbols:
                q = quotes.get(sym, {})
                price = q.get("price", 0.0)
                pct = q.get("percent_change", 0.0)
                curr = config.get_currency_symbol(sym)
                avatar = config.get_symbol_avatar(sym)
                is_pos = pct >= 0
                sign = "+" if is_pos else ""
                badge_class = "badge-gain" if is_pos else "badge-loss"
                is_active = (sym == current_symbol)

                row_col1, row_col2, row_col3 = st.columns([0.48, 0.36, 0.16])
                with row_col1:
                    border_style = "border-left: 3px solid #3B82F6; padding-left: 6px;" if is_active else ""
                    c_name = config.get_company_name(sym)
                    col1_html = (
                        f'<div style="{border_style} display: flex; align-items: center; gap: 8px;">'
                        f'<div style="width: 28px; height: 28px; border-radius: 6px; background: #F1F5F9; display: flex; align-items: center; justify-content: center; font-size: 0.95rem;">{avatar}</div>'
                        f'<div>'
                        f'<div style="font-weight: 700; color: var(--text-primary); font-size: 0.92rem;">{sym}</div>'
                        f'<div style="font-size: 0.72rem; color: var(--text-muted); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 110px;">{c_name}</div>'
                        f'</div>'
                        f'</div>'
                    )
                    st.markdown(col1_html, unsafe_allow_html=True)
                with row_col2:
                    col2_html = (
                        f'<div style="text-align: right;">'
                        f'<div style="font-family: var(--font-mono); font-weight: 700; color: var(--text-primary); font-size: 0.92rem;">{curr}{price:,.2f}</div>'
                        f'<div class="{badge_class}" style="font-size: 0.75rem; display: inline-block;">{sign}{pct:.2f}%</div>'
                        f'</div>'
                    )
                    st.markdown(col2_html, unsafe_allow_html=True)
                with row_col3:
                    if st.button("View" if not is_active else "Live", key=f"sel_{sym}", disabled=is_active):
                        on_select_symbol(sym)
                        st.rerun()

        # Add symbol control
        st.markdown("<hr style='border-color: #E2E8F0; margin: 12px 0;'>", unsafe_allow_html=True)
        col_in, col_btn = st.columns([0.7, 0.3])
        with col_in:
            new_sym = st.text_input(
                "Add Symbol",
                placeholder="e.g. NVDA, AMZN",
                label_visibility="collapsed",
                key="new_watchlist_sym",
            )
        with col_btn:
            if st.button("Add", use_container_width=True):
                if new_sym and new_sym.strip().upper() not in watchlist_symbols:
                    watchlist_symbols.append(new_sym.strip().upper())
                    st.session_state["watchlist"] = watchlist_symbols
                    st.rerun()

    # Tab 2: Top Gainers / Losers
    with tabs[1]:
        st.markdown(
            f'<div style="font-size: 0.85rem; font-weight: 700; color: var(--text-primary); text-transform: uppercase; margin-bottom: 10px;">Session Leaders</div>',
            unsafe_allow_html=True,
        )

        all_quotes = list(quotes.values())
        if not all_quotes:
            st.info("No quote telemetry available for mover analysis.")
            return

        sorted_quotes = sorted(all_quotes, key=lambda x: x.get("percent_change", 0.0), reverse=True)
        gainers = [q for q in sorted_quotes if q.get("percent_change", 0.0) >= 0][:3]
        losers = [q for q in sorted_quotes if q.get("percent_change", 0.0) < 0][-3:]

        st.caption("Top Gainers")
        for g in gainers:
            g_sym = g.get("symbol", "")
            g_price = g.get("price", 0.0)
            g_pct = g.get("percent_change", 0.0)
            g_curr = config.get_currency_symbol(g_sym)
            c1, c2 = st.columns([0.6, 0.4])
            with c1:
                st.markdown(f"**{g_sym}** <span style='font-size: 0.8rem; color: var(--text-muted);'>({g_curr}{g_price:,.2f})</span>", unsafe_allow_html=True)
            with c2:
                st.markdown(f"<span class='badge-gain'>▲ +{g_pct:.2f}%</span>", unsafe_allow_html=True)

        st.caption("Top Losers")
        for l in losers:
            l_sym = l.get("symbol", "")
            l_price = l.get("price", 0.0)
            l_pct = l.get("percent_change", 0.0)
            l_curr = config.get_currency_symbol(l_sym)
            c1, c2 = st.columns([0.6, 0.4])
            with c1:
                st.markdown(f"**{l_sym}** <span style='font-size: 0.8rem; color: var(--text-muted);'>({l_curr}{l_price:,.2f})</span>", unsafe_allow_html=True)
            with c2:
                st.markdown(f"<span class='badge-loss'>▼ {l_pct:.2f}%</span>", unsafe_allow_html=True)
