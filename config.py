"""Application configuration and constants for the Real-Time Stock Market Dashboard."""

import os
from typing import Dict, List
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# App settings
APP_TITLE = "Real-Time Stock Market Dashboard"
APP_SUBTITLE = "Fintech Intelligence Platform"

# Supported Symbols & Realistic Defaults
DEFAULT_SYMBOLS: List[str] = [
    "AAPL",
    "MSFT",
    "TSLA",
    "RELIANCE.NS",
    "TCS.NS",
    "INFY.NS",
]

DEFAULT_SYMBOL: str = "AAPL"

DEFAULT_WATCHLIST: List[str] = [
    "AAPL",
    "MSFT",
    "TSLA",
    "RELIANCE.NS",
    "TCS.NS",
    "INFY.NS",
]

# Quick selection catalog with human-readable company names
SYMBOL_CATALOG: Dict[str, Dict[str, str]] = {
    "AAPL": {"name": "Apple Inc.", "exchange": "NASDAQ", "currency": "$", "avatar": "🍎"},
    "MSFT": {"name": "Microsoft Corp.", "exchange": "NASDAQ", "currency": "$", "avatar": "💻"},
    "TSLA": {"name": "Tesla, Inc.", "exchange": "NASDAQ", "currency": "$", "avatar": "⚡"},
    "NVDA": {"name": "NVIDIA Corp.", "exchange": "NASDAQ", "currency": "$", "avatar": "🟢"},
    "GOOGL": {"name": "Alphabet Inc.", "exchange": "NASDAQ", "currency": "$", "avatar": "🔍"},
    "AMZN": {"name": "Amazon.com, Inc.", "exchange": "NASDAQ", "currency": "$", "avatar": "📦"},
    "RELIANCE.NS": {"name": "Reliance Industries", "exchange": "NSE", "currency": "₹", "avatar": "🇮🇳"},
    "TCS.NS": {"name": "Tata Consultancy Services", "exchange": "NSE", "currency": "₹", "avatar": "🇮🇳"},
    "INFY.NS": {"name": "Infosys Limited", "exchange": "NSE", "currency": "₹", "avatar": "🇮🇳"},
    "HDFCBANK.NS": {"name": "HDFC Bank Limited", "exchange": "NSE", "currency": "₹", "avatar": "🏦"},
    "TATAMOTORS.NS": {"name": "Tata Motors Ltd", "exchange": "NSE", "currency": "₹", "avatar": "🚗"},
    "ICICIBANK.NS": {"name": "ICICI Bank Ltd", "exchange": "NSE", "currency": "₹", "avatar": "🏦"},
}

# Range and Interval configurations
VALID_RANGES: List[str] = ["1d", "5d", "1mo", "6mo", "1y", "5y"]
RANGE_LABELS: Dict[str, str] = {
    "1d": "1D",
    "5d": "5D",
    "1mo": "1M",
    "6mo": "6M",
    "1y": "1Y",
    "5y": "5Y",
}

# Default interval mapping per range to ensure valid data from API
RANGE_DEFAULT_INTERVALS: Dict[str, str] = {
    "1d": "1m",
    "5d": "5m",
    "1mo": "15m",
    "6mo": "1d",
    "1y": "1d",
    "5y": "1d",
}

VALID_INTERVALS: List[str] = ["1m", "5m", "15m", "1d"]

# Auto refresh intervals (seconds)
AUTO_REFRESH_INTERVALS: List[int] = [5, 15, 30, 60]
DEFAULT_REFRESH_INTERVAL: int = 15

# Modern TailAdmin Theme Design System Palette
COLOR_BG: str = "#F4F7FB"
COLOR_CARD: str = "#FFFFFF"
COLOR_BORDER: str = "#E2E8F0"
COLOR_BORDER_HOVER: str = "#CBD5E1"
COLOR_ACCENT: str = "#3B82F6"
COLOR_ACCENT_HOVER: str = "#2563EB"
COLOR_GAIN: str = "#10B981"
COLOR_GAIN_BG: str = "rgba(16, 185, 129, 0.12)"
COLOR_LOSS: str = "#EF4444"
COLOR_LOSS_BG: str = "rgba(239, 68, 68, 0.12)"
COLOR_TEXT_PRIMARY: str = "#1E293B"
COLOR_TEXT_MUTED: str = "#64748B"
COLOR_GRID: str = "#F1F5F9"
COLOR_CROSSHAIR: str = "#3B82F6"

# Sidebar Dark Slate Palette
COLOR_SIDEBAR_BG: str = "#1C2434"
COLOR_SIDEBAR_TEXT: str = "#DEE4EE"
COLOR_SIDEBAR_MUTED: str = "#8A99AD"
COLOR_SIDEBAR_BORDER: str = "#2E3A4B"

# Indicator Colors
COLOR_SMA: str = "#F59E0B"  # Amber
COLOR_EMA: str = "#06B6D4"  # Cyan
COLOR_BOLLINGER_BAND: str = "rgba(59, 130, 246, 0.08)"
COLOR_BOLLINGER_LINE: str = "#60A5FA"
COLOR_VWAP: str = "#8B5CF6"  # Purple

# API & Networking settings
DEFAULT_TIMEOUT_SECONDS: int = 10
MAX_RETRIES: int = 3
BACKOFF_FACTOR: float = 0.5
USER_AGENT: str = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)

# Optional Provider Keys
TWELVE_DATA_API_KEY: str = os.getenv("TWELVE_DATA_API_KEY", "")
FINNHUB_API_KEY: str = os.getenv("FINNHUB_API_KEY", "")
PRIMARY_DATA_PROVIDER: str = os.getenv("PRIMARY_DATA_PROVIDER", "yahoo").lower()

# Cache settings
CACHE_TTL_QUOTE_SECONDS: int = 10
CACHE_TTL_HISTORY_SECONDS: int = 30


def get_currency_symbol(symbol: str) -> str:
    """Return currency symbol for a stock ticker."""
    clean_sym = symbol.strip().upper()
    if clean_sym.endswith(".NS") or clean_sym.endswith(".BO"):
        return "₹"
    return "$"


def get_company_name(symbol: str) -> str:
    """Return friendly company name or the clean symbol itself."""
    clean_sym = symbol.strip().upper()
    return SYMBOL_CATALOG.get(clean_sym, {}).get("name", clean_sym)


def get_symbol_avatar(symbol: str) -> str:
    """Return visual avatar or initial emoji for stock."""
    clean_sym = symbol.strip().upper()
    return SYMBOL_CATALOG.get(clean_sym, {}).get("avatar", "📊")
