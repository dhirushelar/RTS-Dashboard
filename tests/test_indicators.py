"""Unit tests for technical analysis indicators."""

import numpy as np
import pandas as pd
import pytest

from analytics.indicators import (
    compute_bollinger_bands,
    compute_daily_returns,
    compute_ema,
    compute_macd,
    compute_rsi,
    compute_sma,
    compute_vwap,
    generate_technical_summary,
)


def test_sma_calculation():
    """Verify SMA calculation against known mathematical values."""
    prices = pd.Series([10.0, 20.0, 30.0, 40.0, 50.0])
    sma3 = compute_sma(prices, period=3)

    # First value min_periods=1 -> 10.0
    assert sma3.iloc[0] == 10.0
    # Window of 3 for index 2: (10 + 20 + 30) / 3 = 20.0
    assert sma3.iloc[2] == 20.0
    # Window of 3 for index 4: (30 + 40 + 50) / 3 = 40.0
    assert sma3.iloc[4] == 40.0


def test_ema_calculation():
    """Verify EMA responds faster than SMA to recent price changes."""
    prices = pd.Series([10.0, 10.0, 10.0, 20.0, 30.0, 50.0])
    ema = compute_ema(prices, period=3)
    sma = compute_sma(prices, period=3)

    assert len(ema) == len(prices)
    # With a sharp upward spike, EMA should be higher or reactive
    assert ema.iloc[-1] > sma.iloc[-2]


def test_rsi_bounds_and_trends():
    """Verify RSI remains within [0, 100] and detects strong trends."""
    # Monotonically increasing prices -> RSI should be high (> 70)
    up_prices = pd.Series([float(x) for x in range(1, 30)])
    rsi_up = compute_rsi(up_prices, period=14)
    assert not rsi_up.isna().all()
    assert (rsi_up >= 0.0).all() and (rsi_up <= 100.0).all()
    assert rsi_up.iloc[-1] > 70.0

    # Monotonically decreasing prices -> RSI should be low (< 30)
    down_prices = pd.Series([float(30 - x) for x in range(1, 30)])
    rsi_down = compute_rsi(down_prices, period=14)
    assert rsi_down.iloc[-1] < 30.0


def test_macd_relationship():
    """Verify MACD histogram is strictly macd_line minus signal_line."""
    np.random.seed(42)
    prices = pd.Series(100.0 + np.cumsum(np.random.randn(60)))
    macd, signal, hist = compute_macd(prices, fast=12, slow=26, signal=9)

    assert len(macd) == len(prices)
    assert len(signal) == len(prices)
    assert len(hist) == len(prices)

    # Histogram should strictly equal macd - signal
    diff = (macd - signal) - hist
    assert np.allclose(diff.dropna(), 0.0, atol=1e-8)


def test_bollinger_bands():
    """Verify Upper Band >= Middle Band >= Lower Band."""
    np.random.seed(123)
    prices = pd.Series(50.0 + np.cumsum(np.random.randn(40)))
    upper, mid, lower = compute_bollinger_bands(prices, period=20, std_dev=2.0)

    assert len(upper) == len(prices)
    assert (upper >= mid).all()
    assert (mid >= lower).all()

    # Bandwidth should be 4 * std_dev
    rolling_std = prices.rolling(20, min_periods=1).std(ddof=0)
    expected_width = rolling_std * 4.0
    actual_width = upper - lower
    assert np.allclose(actual_width, expected_width, atol=1e-6)


def test_vwap_calculation():
    """Verify VWAP weighting with volume."""
    df = pd.DataFrame({
        "High": [10.0, 12.0, 14.0],
        "Low": [8.0, 10.0, 12.0],
        "Close": [9.0, 11.0, 13.0],
        "Volume": [100, 200, 300],
    })
    # Typical prices: (10+8+9)/3 = 9.0, (12+10+11)/3 = 11.0, (14+12+13)/3 = 13.0
    # Cum TP*V: 9*100=900, 900 + 11*200 = 3100, 3100 + 13*300 = 7000
    # Cum V: 100, 300, 600
    # VWAP: 9.0, 3100/300 = 10.3333, 7000/600 = 11.6667
    vwap = compute_vwap(df)
    assert np.isclose(vwap.iloc[0], 9.0)
    assert np.isclose(vwap.iloc[1], 3100.0 / 300.0)
    assert np.isclose(vwap.iloc[2], 7000.0 / 600.0)


def test_daily_returns():
    """Verify daily return percentage calculation."""
    prices = pd.Series([100.0, 105.0, 94.5])
    returns = compute_daily_returns(prices)
    assert returns.iloc[0] == 0.0
    assert np.isclose(returns.iloc[1], 5.0)
    assert np.isclose(returns.iloc[2], -10.0)


def test_technical_summary():
    """Verify technical summary aggregation and schema."""
    dates = pd.date_range("2026-01-01", periods=50, freq="D")
    df = pd.DataFrame({
        "Datetime": dates,
        "Open": np.linspace(100, 150, 50),
        "High": np.linspace(101, 152, 50),
        "Low": np.linspace(99, 149, 50),
        "Close": np.linspace(100, 150, 50),
        "Volume": [1000] * 50,
    })
    summary = generate_technical_summary(df)

    assert "verdict" in summary
    assert summary["verdict"] in {"STRONG BUY", "BUY", "NEUTRAL", "SELL", "STRONG SELL"}
    assert -100 <= summary["score"] <= 100
    assert summary["total_indicators"] == 5
    assert summary["buy_count"] + summary["neutral_count"] + summary["sell_count"] == 5
    assert len(summary["details"]) == 5


def test_indicators_edge_cases():
    """Ensure indicators gracefully handle empty inputs without throwing exceptions."""
    empty_series = pd.Series(dtype=float)
    assert compute_sma(empty_series).empty
    assert compute_ema(empty_series).empty
    assert compute_rsi(empty_series).empty

    m, s, h = compute_macd(empty_series)
    assert m.empty and s.empty and h.empty

    u, mid, low = compute_bollinger_bands(empty_series)
    assert u.empty and mid.empty and low.empty

    empty_df = pd.DataFrame()
    assert compute_vwap(empty_df).empty
