"""Reusable Plotly figure builders and unified TailAdmin fintech charting templates."""

from typing import Dict, List, Optional
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from analytics.indicators import (
    compute_bollinger_bands,
    compute_ema,
    compute_macd,
    compute_rsi,
    compute_sma,
    compute_vwap,
)
import config


def get_fintech_layout_template() -> go.layout.Template:
    """Construct unified TailAdmin clean fintech layout template for Plotly figures."""
    template = go.layout.Template()
    template.layout = go.Layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(
            family="Plus Jakarta Sans, Inter, -apple-system, sans-serif",
            color=config.COLOR_TEXT_PRIMARY,
            size=12,
        ),
        margin=dict(l=45, r=20, t=30, b=30),
        xaxis=dict(
            showgrid=True,
            gridcolor=config.COLOR_GRID,
            gridwidth=1,
            zeroline=False,
            showline=True,
            linecolor=config.COLOR_BORDER,
            tickfont=dict(family="JetBrains Mono, monospace", size=10, color=config.COLOR_TEXT_MUTED),
            showspikes=True,
            spikethickness=1,
            spikedash="dot",
            spikecolor=config.COLOR_CROSSHAIR,
            spikemode="across",
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor=config.COLOR_GRID,
            gridwidth=1,
            zeroline=False,
            showline=True,
            linecolor=config.COLOR_BORDER,
            tickfont=dict(family="JetBrains Mono, monospace", size=10, color=config.COLOR_TEXT_MUTED),
            showspikes=True,
            spikethickness=1,
            spikedash="dot",
            spikecolor=config.COLOR_CROSSHAIR,
            spikemode="across",
        ),
        hovermode="x unified",
        hoverlabel=dict(
            bgcolor=config.COLOR_CARD,
            bordercolor=config.COLOR_BORDER,
            font=dict(family="JetBrains Mono, monospace", size=11, color=config.COLOR_TEXT_PRIMARY),
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(size=10, color=config.COLOR_TEXT_MUTED),
            bgcolor="rgba(0,0,0,0)",
        ),
    )
    return template


def build_main_price_chart(
    df: pd.DataFrame,
    symbol: str,
    chart_type: str = "Candle",
    show_sma: bool = False,
    show_ema: bool = False,
    show_bollinger: bool = False,
    show_vwap: bool = False,
    show_range_slider: bool = True,
) -> go.Figure:
    """Build multi-subplot main price & volume chart with dynamic overlays."""
    template = get_fintech_layout_template()

    if df.empty or "Close" not in df.columns:
        fig = go.Figure()
        fig.update_layout(
            template=template,
            annotations=[
                dict(
                    text="No market data available for the selected timeframe",
                    xref="paper",
                    yref="paper",
                    showarrow=False,
                    font=dict(size=14, color=config.COLOR_TEXT_MUTED),
                )
            ],
        )
        return fig

    currency = config.get_currency_symbol(symbol)
    fig = make_subplots(
        rows=2,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.03,
        row_heights=[0.75, 0.25],
    )

    x_vals = df["Datetime"]

    # 1. Price Traces
    if chart_type == "Candle":
        fig.add_trace(
            go.Candlestick(
                x=x_vals,
                open=df["Open"],
                high=df["High"],
                low=df["Low"],
                close=df["Close"],
                name=symbol,
                increasing_line_color=config.COLOR_GAIN,
                increasing_fillcolor=config.COLOR_GAIN,
                decreasing_line_color=config.COLOR_LOSS,
                decreasing_fillcolor=config.COLOR_LOSS,
            ),
            row=1,
            col=1,
        )
    elif chart_type == "Area":
        fig.add_trace(
            go.Scatter(
                x=x_vals,
                y=df["Close"],
                mode="lines",
                name=symbol,
                line=dict(color=config.COLOR_ACCENT, width=2.2),
                fill="tozeroy",
                fillcolor="rgba(59, 130, 246, 0.12)",
            ),
            row=1,
            col=1,
        )
    else:  # Line
        fig.add_trace(
            go.Scatter(
                x=x_vals,
                y=df["Close"],
                mode="lines",
                name=symbol,
                line=dict(color=config.COLOR_ACCENT, width=2.2),
            ),
            row=1,
            col=1,
        )

    # 2. Indicator Overlays
    if show_sma:
        sma = compute_sma(df["Close"], period=20)
        fig.add_trace(
            go.Scatter(
                x=x_vals,
                y=sma,
                mode="lines",
                name="SMA 20",
                line=dict(color=config.COLOR_SMA, width=1.5),
            ),
            row=1,
            col=1,
        )

    if show_ema:
        ema = compute_ema(df["Close"], period=20)
        fig.add_trace(
            go.Scatter(
                x=x_vals,
                y=ema,
                mode="lines",
                name="EMA 20",
                line=dict(color=config.COLOR_EMA, width=1.5),
            ),
            row=1,
            col=1,
        )

    if show_bollinger:
        upper, mid, lower = compute_bollinger_bands(df["Close"], period=20)
        fig.add_trace(
            go.Scatter(
                x=x_vals,
                y=upper,
                mode="lines",
                name="BB Upper",
                line=dict(color=config.COLOR_BOLLINGER_LINE, width=1, dash="dot"),
            ),
            row=1,
            col=1,
        )
        fig.add_trace(
            go.Scatter(
                x=x_vals,
                y=lower,
                mode="lines",
                name="BB Lower",
                line=dict(color=config.COLOR_BOLLINGER_LINE, width=1, dash="dot"),
                fill="tonexty",
                fillcolor=config.COLOR_BOLLINGER_BAND,
            ),
            row=1,
            col=1,
        )

    if show_vwap and "Volume" in df.columns:
        vwap = compute_vwap(df)
        fig.add_trace(
            go.Scatter(
                x=x_vals,
                y=vwap,
                mode="lines",
                name="VWAP",
                line=dict(color=config.COLOR_VWAP, width=1.5, dash="dash"),
            ),
            row=1,
            col=1,
        )

    # 3. Volume Subplot
    if "Volume" in df.columns:
        vol_colors = [
            config.COLOR_GAIN if close >= open_val else config.COLOR_LOSS
            for close, open_val in zip(df["Close"], df["Open"])
        ]
        fig.add_trace(
            go.Bar(
                x=x_vals,
                y=df["Volume"],
                name="Volume",
                marker_color=vol_colors,
                opacity=0.65,
            ),
            row=2,
            col=1,
        )

    fig.update_layout(
        template=template,
        height=520,
        dragmode="zoom",
        xaxis_rangeslider_visible=False,
        xaxis=dict(fixedrange=False),
        xaxis2=dict(
            rangeslider=dict(visible=show_range_slider, bgcolor=config.COLOR_CARD, thickness=0.06),
            type="date",
            fixedrange=False,
        ),
        yaxis=dict(title=f"Price ({currency})", tickformat=".2f", fixedrange=False),
        yaxis2=dict(title="Volume", showgrid=False, fixedrange=False),
    )

    return fig


def build_rsi_chart(df: pd.DataFrame, period: int = 14) -> go.Figure:
    """Build dedicated RSI chart with 30/70 shaded boundary zones."""
    template = get_fintech_layout_template()
    fig = go.Figure()

    if df.empty or "Close" not in df.columns:
        fig.update_layout(template=template, height=220)
        return fig

    rsi = compute_rsi(df["Close"], period=period)
    x_vals = df["Datetime"]

    fig.add_hrect(
        y0=30,
        y1=70,
        fillcolor="rgba(59, 130, 246, 0.04)",
        line_width=0,
        layer="below",
    )
    fig.add_hline(y=70, line_dash="dash", line_color=config.COLOR_LOSS, line_width=1, opacity=0.7)
    fig.add_hline(y=30, line_dash="dash", line_color=config.COLOR_GAIN, line_width=1, opacity=0.7)

    fig.add_trace(
        go.Scatter(
            x=x_vals,
            y=rsi,
            mode="lines",
            name=f"RSI ({period})",
            line=dict(color=config.COLOR_ACCENT, width=1.8),
        )
    )

    fig.update_layout(
        template=template,
        height=220,
        yaxis=dict(
            range=[0, 100],
            tickvals=[30, 50, 70],
            title="RSI",
            tickfont=dict(family="JetBrains Mono, monospace", size=10),
        ),
        margin=dict(l=45, r=20, t=15, b=20),
    )
    return fig


def build_macd_chart(
    df: pd.DataFrame,
    fast: int = 12,
    slow: int = 26,
    signal: int = 9,
) -> go.Figure:
    """Build MACD indicator chart with histogram bars and signal lines."""
    template = get_fintech_layout_template()
    fig = go.Figure()

    if df.empty or "Close" not in df.columns:
        fig.update_layout(template=template, height=220)
        return fig

    macd, sig, hist = compute_macd(df["Close"], fast=fast, slow=slow, signal=signal)
    x_vals = df["Datetime"]

    hist_colors = [config.COLOR_GAIN if h >= 0 else config.COLOR_LOSS for h in hist]

    fig.add_trace(
        go.Bar(
            x=x_vals,
            y=hist,
            name="Histogram",
            marker_color=hist_colors,
            opacity=0.75,
        )
    )
    fig.add_trace(
        go.Scatter(
            x=x_vals,
            y=macd,
            mode="lines",
            name=f"MACD ({fast},{slow})",
            line=dict(color=config.COLOR_ACCENT, width=1.5),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=x_vals,
            y=sig,
            mode="lines",
            name=f"Signal ({signal})",
            line=dict(color=config.COLOR_SMA, width=1.5),
        )
    )

    fig.update_layout(
        template=template,
        height=220,
        yaxis=dict(title="MACD", tickfont=dict(family="JetBrains Mono, monospace", size=10)),
        margin=dict(l=45, r=20, t=15, b=20),
    )
    return fig


def build_comparison_chart(history_dict: Dict[str, pd.DataFrame]) -> go.Figure:
    """Build normalized % performance comparison chart for 2-4 stocks."""
    template = get_fintech_layout_template()
    fig = go.Figure()

    palette = [config.COLOR_ACCENT, config.COLOR_GAIN, config.COLOR_SMA, config.COLOR_VWAP]

    idx = 0
    for sym, df in history_dict.items():
        if df.empty or "Close" not in df.columns:
            continue
        base_price = df["Close"].iloc[0]
        if base_price == 0:
            continue
        norm_return = ((df["Close"] - base_price) / base_price) * 100.0
        color = palette[idx % len(palette)]
        fig.add_trace(
            go.Scatter(
                x=df["Datetime"],
                y=norm_return,
                mode="lines",
                name=sym,
                line=dict(color=color, width=2),
            )
        )
        idx += 1

    fig.add_hline(y=0, line_dash="solid", line_color=config.COLOR_BORDER, line_width=1)
    fig.update_layout(
        template=template,
        height=280,
        yaxis=dict(title="Return (%)", tickformat="+.1f", ticksuffix="%"),
        margin=dict(l=45, r=20, t=25, b=25),
    )
    return fig


def build_sparkline(series: pd.Series, is_positive: bool = True) -> go.Figure:
    """Build ultra-light mini sparkline figure for watchlist cards and tables."""
    fig = go.Figure()
    if series.empty:
        return fig

    color = config.COLOR_GAIN if is_positive else config.COLOR_LOSS
    fig.add_trace(
        go.Scatter(
            y=series.values,
            mode="lines",
            line=dict(color=color, width=1.5),
            hoverinfo="none",
        )
    )
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=0, r=0, t=0, b=0),
        height=32,
        width=90,
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
    )
    return fig
