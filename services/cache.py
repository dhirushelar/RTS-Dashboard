"""Caching layer for market data provider functions using Streamlit caching primitives."""

from typing import Any, Dict, List, Optional, Tuple
import pandas as pd
import streamlit as st

import config
from services.data_provider import DataProvider, get_provider


@st.cache_data(ttl=config.CACHE_TTL_HISTORY_SECONDS, show_spinner=False)
def fetch_cached_history(
    symbol: str,
    range_period: str = "1d",
    interval: str = "5m",
) -> Tuple[pd.DataFrame, Optional[str]]:
    """Retrieve historical market data with short TTL caching."""
    provider: DataProvider = get_provider()
    return provider.get_history(symbol=symbol, range_period=range_period, interval=interval)


@st.cache_data(ttl=config.CACHE_TTL_QUOTE_SECONDS, show_spinner=False)
def fetch_cached_quote(symbol: str) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """Retrieve single ticker quote with short TTL caching."""
    provider: DataProvider = get_provider()
    return provider.get_quote(symbol=symbol)


@st.cache_data(ttl=config.CACHE_TTL_QUOTE_SECONDS, show_spinner=False)
def fetch_cached_multi_quotes(symbols: List[str]) -> Dict[str, Dict[str, Any]]:
    """Retrieve multiple stock quotes for watchlist and tickers."""
    provider: DataProvider = get_provider()
    return provider.get_multi_quotes(symbols=symbols)


@st.cache_data(ttl=300, show_spinner=False)
def search_cached_symbols(query: str) -> List[Dict[str, str]]:
    """Search symbol suggestions with 5-minute TTL caching."""
    provider: DataProvider = get_provider()
    return provider.search_symbols(query=query)


def clear_market_cache() -> None:
    """Manually clear all cached market data to trigger a fresh network fetch."""
    fetch_cached_history.clear()
    fetch_cached_quote.clear()
    fetch_cached_multi_quotes.clear()
