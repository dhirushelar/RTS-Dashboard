"""Technical analysis indicators implemented with pure Pandas and NumPy."""

from typing import Any, Dict, Optional, Tuple
import numpy as np
import pandas as pd


def compute_sma(series: pd.Series, period: int = 20) -> pd.Series:
    """Calculate Simple Moving Average (SMA).

    Args:
        series: Price series (e.g. Close).
        period: Number of periods for rolling window.

    Returns:
        pd.Series containing computed SMA.
    """
    if series.empty or period <= 0:
        return pd.Series(index=series.index, dtype=float)
    return series.rolling(window=period, min_periods=1).mean()


def compute_ema(series: pd.Series, period: int = 20, adjust: bool = False) -> pd.Series:
    """Calculate Exponential Moving Average (EMA).

    Args:
        series: Price series (e.g. Close).
        period: Span of exponential window.
        adjust: Whether to use adjusted weights in ewm.

    Returns:
        pd.Series containing computed EMA.
    """
    if series.empty or period <= 0:
        return pd.Series(index=series.index, dtype=float)
    return series.ewm(span=period, adjust=adjust).mean()


def compute_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    """Calculate Relative Strength Index (RSI) using Wilder's smoothing.

    Args:
        series: Price series (e.g. Close).
        period: Lookback window (default 14).

    Returns:
        pd.Series containing RSI values bound between 0 and 100.
    """
    if series.empty or len(series) < 2 or period <= 0:
        return pd.Series(index=series.index, dtype=float)

    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    # Wilder's exponential smoothing (alpha = 1 / period)
    avg_gain = gain.ewm(alpha=1.0 / period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1.0 / period, adjust=False).mean()

    # Avoid division by zero
    rs = avg_gain / avg_loss.replace(0, np.nan)
    rsi = 100.0 - (100.0 / (1.0 + rs))

    # Handle zero-loss (100) or flat price (50) edge cases
    rsi = rsi.where(avg_loss != 0, 100.0)
    rsi = rsi.where((avg_gain != 0) | (avg_loss != 0), 50.0)
    return rsi.fillna(50.0)


def compute_macd(
    series: pd.Series,
    fast: int = 12,
    slow: int = 26,
    signal: int = 9,
) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """Calculate Moving Average Convergence Divergence (MACD).

    Args:
        series: Price series (e.g. Close).
        fast: Fast EMA period (default 12).
        slow: Slow EMA period (default 26).
        signal: Signal EMA period (default 9).

    Returns:
        Tuple of (macd_line, signal_line, histogram).
    """
    if series.empty:
        empty = pd.Series(index=series.index, dtype=float)
        return empty, empty, empty

    ema_fast = compute_ema(series, period=fast)
    ema_slow = compute_ema(series, period=slow)
    macd_line = ema_fast - ema_slow
    signal_line = compute_ema(macd_line, period=signal)
    histogram = macd_line - signal_line

    return macd_line, signal_line, histogram


def compute_bollinger_bands(
    series: pd.Series,
    period: int = 20,
    std_dev: float = 2.0,
) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """Calculate Bollinger Bands (Upper, Middle, Lower).

    Args:
        series: Price series (e.g. Close).
        period: Moving average window (default 20).
        std_dev: Standard deviation multiplier (default 2.0).

    Returns:
        Tuple of (upper_band, middle_band, lower_band).
    """
    if series.empty or period <= 0:
        empty = pd.Series(index=series.index, dtype=float)
        return empty, empty, empty

    middle_band = series.rolling(window=period, min_periods=1).mean()
    rolling_std = series.rolling(window=period, min_periods=1).std(ddof=0).fillna(0.0)

    upper_band = middle_band + (rolling_std * std_dev)
    lower_band = middle_band - (rolling_std * std_dev)

    return upper_band, middle_band, lower_band


def compute_vwap(df: pd.DataFrame) -> pd.Series:
    """Calculate Volume Weighted Average Price (VWAP).

    Args:
        df: DataFrame containing ['High', 'Low', 'Close', 'Volume'] and optionally 'Datetime'.

    Returns:
        pd.Series containing computed VWAP.
    """
    required_cols = {"High", "Low", "Close", "Volume"}
    if df.empty or not required_cols.issubset(df.columns):
        return pd.Series(index=df.index, dtype=float)

    typical_price = (df["High"] + df["Low"] + df["Close"]) / 3.0
    tp_vol = typical_price * df["Volume"]

    # If datetime column exists, reset VWAP at start of each trading session/date
    if "Datetime" in df.columns and pd.api.types.is_datetime64_any_dtype(df["Datetime"]):
        dates = df["Datetime"].dt.date
        cum_tp_vol = tp_vol.groupby(dates).cumsum()
        cum_vol = df["Volume"].groupby(dates).cumsum()
    else:
        cum_tp_vol = tp_vol.cumsum()
        cum_vol = df["Volume"].cumsum()

    vwap = cum_tp_vol / cum_vol.replace(0, np.nan)
    return vwap.fillna(typical_price)


def compute_daily_returns(series: pd.Series) -> pd.Series:
    """Calculate percentage change return series."""
    if series.empty:
        return pd.Series(index=series.index, dtype=float)
    return series.pct_change().fillna(0.0) * 100.0


def generate_technical_summary(df: pd.DataFrame) -> Dict[str, Any]:
    """Aggregate multiple technical signals into Buy/Neutral/Sell summary.

    Signals analyzed:
    - RSI(14): < 30 Oversold (Buy), > 70 Overbought (Sell)
    - MACD: MACD > Signal Line & Histogram > 0 (Buy), MACD < Signal (Sell)
    - SMA(20) vs Close: Close > SMA (Buy), Close < SMA (Sell)
    - EMA(20) vs Close: Close > EMA (Buy), Close < EMA (Sell)
    - Bollinger Bands: Close <= Lower Band (Buy), Close >= Upper Band (Sell)

    Returns:
        Dict with overall verdict, score (-100 to 100), counts, and details.
    """
    if df.empty or "Close" not in df.columns or len(df) < 5:
        return {
            "verdict": "NEUTRAL",
            "score": 0,
            "buy_count": 0,
            "neutral_count": 5,
            "sell_count": 0,
            "total_indicators": 5,
            "details": [],
        }

    close = df["Close"]
    curr_price = float(close.iloc[-1])

    # 1. RSI
    rsi_series = compute_rsi(close, period=14)
    curr_rsi = float(rsi_series.iloc[-1]) if not rsi_series.empty else 50.0
    if curr_rsi < 35:
        rsi_signal = "BUY"
    elif curr_rsi > 65:
        rsi_signal = "SELL"
    else:
        rsi_signal = "NEUTRAL"

    # 2. MACD
    macd, sig, hist = compute_macd(close)
    curr_macd = float(macd.iloc[-1])
    curr_sig = float(sig.iloc[-1])
    curr_hist = float(hist.iloc[-1])
    if curr_macd > curr_sig and curr_hist > 0:
        macd_signal = "BUY"
    elif curr_macd < curr_sig and curr_hist < 0:
        macd_signal = "SELL"
    else:
        macd_signal = "NEUTRAL"

    # 3. SMA(20)
    sma20 = compute_sma(close, period=20)
    curr_sma20 = float(sma20.iloc[-1])
    if curr_price > curr_sma20 * 1.002:
        sma_signal = "BUY"
    elif curr_price < curr_sma20 * 0.998:
        sma_signal = "SELL"
    else:
        sma_signal = "NEUTRAL"

    # 4. EMA(20)
    ema20 = compute_ema(close, period=20)
    curr_ema20 = float(ema20.iloc[-1])
    if curr_price > curr_ema20 * 1.002:
        ema_signal = "BUY"
    elif curr_price < curr_ema20 * 0.998:
        ema_signal = "SELL"
    else:
        ema_signal = "NEUTRAL"

    # 5. Bollinger Bands
    upper, mid, lower = compute_bollinger_bands(close, period=20)
    curr_upper = float(upper.iloc[-1])
    curr_lower = float(lower.iloc[-1])
    if curr_price <= curr_lower * 1.01:
        bb_signal = "BUY"
    elif curr_price >= curr_upper * 0.99:
        bb_signal = "SELL"
    else:
        bb_signal = "NEUTRAL"

    signals = [
        {"indicator": "RSI (14)", "value": f"{curr_rsi:.1f}", "signal": rsi_signal},
        {"indicator": "MACD (12,26,9)", "value": f"{curr_hist:+.2f}", "signal": macd_signal},
        {"indicator": "SMA (20)", "value": f"{curr_sma20:.2f}", "signal": sma_signal},
        {"indicator": "EMA (20)", "value": f"{curr_ema20:.2f}", "signal": ema_signal},
        {"indicator": "Bollinger Bands", "value": f"{curr_lower:.1f} - {curr_upper:.1f}", "signal": bb_signal},
    ]

    buy_cnt = sum(1 for s in signals if s["signal"] == "BUY")
    sell_cnt = sum(1 for s in signals if s["signal"] == "SELL")
    neutral_cnt = len(signals) - buy_cnt - sell_cnt

    # Score calculation from -100 to +100
    score = int(((buy_cnt - sell_cnt) / len(signals)) * 100)

    if score >= 60:
        verdict = "STRONG BUY"
    elif score >= 20:
        verdict = "BUY"
    elif score <= -60:
        verdict = "STRONG SELL"
    elif score <= -20:
        verdict = "SELL"
    else:
        verdict = "NEUTRAL"

    return {
        "verdict": verdict,
        "score": score,
        "buy_count": buy_cnt,
        "neutral_count": neutral_cnt,
        "sell_count": sell_cnt,
        "total_indicators": len(signals),
        "details": signals,
    }
