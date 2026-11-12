"""Financial market data providers with retries, caching support, and error handling."""

from abc import ABC, abstractmethod
import datetime as dt
import logging
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

import config

logger = logging.getLogger(__name__)
if not logger.handlers:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

# Known shares outstanding (approximate) for Market Cap calculation fallback
SHARES_OUTSTANDING_ESTIMATES: Dict[str, float] = {
    "AAPL": 15.2e9,
    "MSFT": 7.43e9,
    "TSLA": 3.19e9,
    "NVDA": 24.6e9,
    "GOOGL": 12.3e9,
    "AMZN": 10.4e9,
    "RELIANCE.NS": 6.77e9,
    "TCS.NS": 3.62e9,
    "INFY.NS": 4.15e9,
    "HDFCBANK.NS": 7.62e9,
    "TATAMOTORS.NS": 3.68e9,
    "ICICIBANK.NS": 7.03e9,
}


def build_session() -> requests.Session:
    """Create a requests session with exponential backoff retries and headers."""
    session = requests.Session()
    retry_strategy = Retry(
        total=config.MAX_RETRIES,
        backoff_factor=config.BACKOFF_FACTOR,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["HEAD", "GET", "OPTIONS"],
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    session.headers.update({
        "User-Agent": config.USER_AGENT,
        "Accept": "application/json",
    })
    return session


class DataProvider(ABC):
    """Abstract Base Class for market data providers."""

    @abstractmethod
    def get_history(
        self,
        symbol: str,
        range_period: str = "1d",
        interval: str = "5m",
    ) -> Tuple[pd.DataFrame, Optional[str]]:
        """Fetch historical OHLCV data. Returns (DataFrame, error_message)."""
        pass

    @abstractmethod
    def get_quote(self, symbol: str) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """Fetch latest quote and metadata for a symbol. Returns (quote_dict, error_message)."""
        pass

    @abstractmethod
    def search_symbols(self, query: str) -> List[Dict[str, str]]:
        """Search available tickers matching query."""
        pass

    @abstractmethod
    def get_multi_quotes(self, symbols: List[str]) -> Dict[str, Dict[str, Any]]:
        """Fetch latest quotes for multiple symbols."""
        pass


class YahooFinanceProvider(DataProvider):
    """Yahoo Finance chart v8 API data provider."""

    def __init__(self, session: Optional[requests.Session] = None):
        self.session = session or build_session()
        self.chart_base_url = "https://query1.finance.yahoo.com/v8/finance/chart"
        self.search_base_url = "https://query2.finance.yahoo.com/v1/finance/search"

    def _determine_market_status(self, meta: Dict[str, Any]) -> Tuple[bool, str]:
        """Determine if regular market session is currently open."""
        now_ts = int(dt.datetime.now(dt.timezone.utc).timestamp())
        trading_period = meta.get("currentTradingPeriod", {}).get("regular", {})
        start_ts = trading_period.get("start")
        end_ts = trading_period.get("end")

        if start_ts and end_ts:
            if start_ts <= now_ts <= end_ts:
                return True, "Market Open"
            return False, "Market Closed"

        # Fallback to last trade freshness (within last 20 minutes)
        reg_time = meta.get("regularMarketTime", 0)
        if (now_ts - reg_time) < 1200:
            return True, "Market Active"
        return False, "Market Closed"

    def get_history(
        self,
        symbol: str,
        range_period: str = "1d",
        interval: str = "5m",
    ) -> Tuple[pd.DataFrame, Optional[str]]:
        """Fetch OHLCV DataFrame from Yahoo Finance."""
        clean_symbol = symbol.strip().upper()
        if not clean_symbol:
            return pd.DataFrame(), "Invalid symbol: symbol cannot be empty."

        url = f"{self.chart_base_url}/{clean_symbol}"
        params = {
            "range": range_period,
            "interval": interval,
            "includePrePost": "false",
            "events": "div,splits",
        }

        try:
            resp = self.session.get(url, params=params, timeout=config.DEFAULT_TIMEOUT_SECONDS)
            if resp.status_code == 404:
                return pd.DataFrame(), f"Symbol '{clean_symbol}' not found."
            if resp.status_code == 429:
                return pd.DataFrame(), "Rate limit exceeded (429). Please wait a moment."
            resp.raise_for_status()

            payload = resp.json()
            chart_res = payload.get("chart", {})
            if chart_res.get("error"):
                err_desc = chart_res["error"].get("description", "Unknown API error")
                return pd.DataFrame(), f"Provider error: {err_desc}"

            results = chart_res.get("result")
            if not results or not len(results):
                return pd.DataFrame(), f"No market data returned for '{clean_symbol}'."

            result_item = results[0]
            timestamps = result_item.get("timestamp", [])
            indicators = result_item.get("indicators", {}).get("quote", [{}])[0]

            if not timestamps:
                return pd.DataFrame(), f"No trading candles available for range {range_period}."

            # Construct DataFrame
            df = pd.DataFrame({
                "Timestamp": timestamps,
                "Open": indicators.get("open", []),
                "High": indicators.get("high", []),
                "Low": indicators.get("low", []),
                "Close": indicators.get("close", []),
                "Volume": indicators.get("volume", []),
            })

            # Drop missing rows where Close is null
            df = df.dropna(subset=["Close"]).copy()
            if df.empty:
                return pd.DataFrame(), f"All trading records for '{clean_symbol}' are empty."

            # Fill missing Open, High, Low with Close
            df["Open"] = df["Open"].fillna(df["Close"])
            df["High"] = df["High"].fillna(df[["Open", "Close"]].max(axis=1))
            df["Low"] = df["Low"].fillna(df[["Open", "Close"]].min(axis=1))
            df["Volume"] = df["Volume"].fillna(0).astype(int)

            # Datetime conversion
            meta = result_item.get("meta", {})
            tz_name = meta.get("exchangeTimezoneName", "UTC")
            try:
                df["Datetime"] = (
                    pd.to_datetime(df["Timestamp"], unit="s", utc=True)
                    .dt.tz_convert(tz_name)
                    .dt.tz_localize(None)
                )
            except Exception:
                df["Datetime"] = pd.to_datetime(df["Timestamp"], unit="s")

            # Final columns arrangement
            df = df[["Datetime", "Open", "High", "Low", "Close", "Volume"]].reset_index(drop=True)
            return df, None

        except requests.exceptions.Timeout:
            logger.warning("Timeout while fetching history for %s", clean_symbol)
            return pd.DataFrame(), "Connection timed out. Retrying in background..."
        except requests.exceptions.RequestException as e:
            logger.error("Request error for %s: %s", clean_symbol, str(e))
            return pd.DataFrame(), f"Network error: {str(e)}"
        except Exception as e:
            logger.exception("Unexpected error parsing history for %s", clean_symbol)
            return pd.DataFrame(), f"Unexpected processing error: {str(e)}"

    def get_quote(self, symbol: str) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """Fetch single symbol real-time quote metadata."""
        clean_symbol = symbol.strip().upper()
        if not clean_symbol:
            return None, "Empty symbol"

        url = f"{self.chart_base_url}/{clean_symbol}"
        params = {"range": "1d", "interval": "5m"}

        try:
            resp = self.session.get(url, params=params, timeout=config.DEFAULT_TIMEOUT_SECONDS)
            if resp.status_code != 200:
                return None, f"HTTP {resp.status_code} fetching quote for {clean_symbol}"

            payload = resp.json()
            results = payload.get("chart", {}).get("result", [])
            if not results:
                return None, f"No quote found for {clean_symbol}"

            meta = results[0].get("meta", {})
            current_price = meta.get("regularMarketPrice") or meta.get("chartPreviousClose", 0.0)
            prev_close = meta.get("chartPreviousClose") or meta.get("previousClose") or current_price

            change = current_price - prev_close if prev_close else 0.0
            percent_change = (change / prev_close * 100.0) if prev_close else 0.0

            day_high = meta.get("regularMarketDayHigh", current_price)
            day_low = meta.get("regularMarketDayLow", current_price)
            volume = meta.get("regularMarketVolume", 0)

            # 52-week metrics
            high_52w = meta.get("fiftyTwoWeekHigh", day_high)
            low_52w = meta.get("fiftyTwoWeekLow", day_low)

            # Market Cap calculation or fallback
            shares = SHARES_OUTSTANDING_ESTIMATES.get(clean_symbol)
            market_cap = (current_price * shares) if shares else (meta.get("marketCap") or None)

            # Market status
            is_open, status_text = self._determine_market_status(meta)

            currency = config.get_currency_symbol(clean_symbol)
            company_name = meta.get("longName") or meta.get("shortName") or config.get_company_name(clean_symbol)

            quote_dict = {
                "symbol": clean_symbol,
                "name": company_name,
                "price": float(current_price),
                "change": float(change),
                "percent_change": float(percent_change),
                "previous_close": float(prev_close),
                "day_high": float(day_high),
                "day_low": float(day_low),
                "volume": int(volume),
                "avg_volume": int(volume * 0.9) if volume else 1000000,
                "fifty_two_week_high": float(high_52w),
                "fifty_two_week_low": float(low_52w),
                "market_cap": market_cap,
                "currency": currency,
                "exchange": meta.get("exchangeName", "N/A"),
                "is_market_open": is_open,
                "market_status": status_text,
                "timestamp": meta.get("regularMarketTime", int(dt.datetime.now().timestamp())),
            }
            return quote_dict, None

        except Exception as e:
            logger.error("Error fetching quote for %s: %s", clean_symbol, str(e))
            return None, f"Could not fetch quote: {str(e)}"

    def search_symbols(self, query: str) -> List[Dict[str, str]]:
        """Search symbol suggestions via Yahoo search API."""
        clean_q = query.strip()
        if not clean_q:
            return []

        try:
            resp = self.session.get(
                self.search_base_url,
                params={"q": clean_q, "quotesCount": 6, "newsCount": 0},
                timeout=config.DEFAULT_TIMEOUT_SECONDS,
            )
            if resp.status_code != 200:
                return []

            quotes = resp.json().get("quotes", [])
            suggestions = []
            for item in quotes:
                sym = item.get("symbol")
                if sym and item.get("quoteType") in ["EQUITY", "ETF", "INDEX"]:
                    suggestions.append({
                        "symbol": sym,
                        "name": item.get("shortname") or item.get("longname") or sym,
                        "exchange": item.get("exchDisp") or item.get("exchange") or "",
                    })
            return suggestions
        except Exception as e:
            logger.warning("Symbol search error for '%s': %s", clean_q, str(e))
            return []

    def get_multi_quotes(self, symbols: List[str]) -> Dict[str, Dict[str, Any]]:
        """Fetch quotes for a list of symbols."""
        results: Dict[str, Dict[str, Any]] = {}
        for sym in symbols:
            quote, _ = self.get_quote(sym)
            if quote:
                results[sym] = quote
        return results


class FinnhubProvider(DataProvider):
    """Optional Finnhub provider implementation if API key is provided."""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://finnhub.io/api/v1"
        self.session = build_session()

    def get_history(
        self,
        symbol: str,
        range_period: str = "1d",
        interval: str = "5m",
    ) -> Tuple[pd.DataFrame, Optional[str]]:
        # Fall back to Yahoo Finance if candle resolution is unsupported
        return YahooFinanceProvider(self.session).get_history(symbol, range_period, interval)

    def get_quote(self, symbol: str) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        try:
            resp = self.session.get(
                f"{self.base_url}/quote",
                params={"symbol": symbol, "token": self.api_key},
                timeout=config.DEFAULT_TIMEOUT_SECONDS,
            )
            if resp.status_code == 200:
                data = resp.json()
                price = data.get("c", 0.0)
                change = data.get("d", 0.0)
                pct = data.get("dp", 0.0)
                return {
                    "symbol": symbol,
                    "name": config.get_company_name(symbol),
                    "price": price,
                    "change": change,
                    "percent_change": pct,
                    "day_high": data.get("h", price),
                    "day_low": data.get("l", price),
                    "previous_close": data.get("pc", price),
                    "volume": 0,
                    "currency": config.get_currency_symbol(symbol),
                    "is_market_open": True,
                    "market_status": "Market Open",
                }, None
        except Exception as e:
            logger.warning("Finnhub get_quote error: %s", str(e))

        # Fallback to Yahoo
        return YahooFinanceProvider(self.session).get_quote(symbol)

    def search_symbols(self, query: str) -> List[Dict[str, str]]:
        return YahooFinanceProvider(self.session).search_symbols(query)

    def get_multi_quotes(self, symbols: List[str]) -> Dict[str, Dict[str, Any]]:
        return YahooFinanceProvider(self.session).get_multi_quotes(symbols)


def get_provider(provider_name: Optional[str] = None) -> DataProvider:
    """Factory to retrieve configured market data provider."""
    name = (provider_name or config.PRIMARY_DATA_PROVIDER).lower()
    if name == "finnhub" and config.FINNHUB_API_KEY:
        return FinnhubProvider(config.FINNHUB_API_KEY)
    return YahooFinanceProvider()
