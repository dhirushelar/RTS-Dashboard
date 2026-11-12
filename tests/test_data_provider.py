"""Unit tests for financial market data provider."""

from unittest.mock import MagicMock, patch
import pandas as pd
import pytest
import requests

from services.data_provider import (
    FinnhubProvider,
    YahooFinanceProvider,
    get_provider,
)


@pytest.fixture
def mock_chart_payload():
    """Mock standard Yahoo Finance v8 chart response."""
    return {
        "chart": {
            "result": [
                {
                    "meta": {
                        "currency": "USD",
                        "symbol": "AAPL",
                        "regularMarketPrice": 185.50,
                        "previousClose": 180.00,
                        "chartPreviousClose": 180.00,
                        "regularMarketDayHigh": 186.00,
                        "regularMarketDayLow": 179.50,
                        "regularMarketVolume": 50000000,
                        "fiftyTwoWeekHigh": 199.00,
                        "fiftyTwoWeekLow": 140.00,
                        "exchangeName": "NASDAQ",
                        "shortName": "Apple Inc.",
                        "exchangeTimezoneName": "America/New_York",
                        "regularMarketTime": 1715000000,
                        "currentTradingPeriod": {
                            "regular": {
                                "start": 1715000000,
                                "end": 1715030000,
                            }
                        },
                    },
                    "timestamp": [1715000100, 1715000200, 1715000300],
                    "indicators": {
                        "quote": [
                            {
                                "open": [180.5, 181.0, 183.0],
                                "high": [182.0, 183.5, 185.5],
                                "low": [180.0, 181.0, 182.5],
                                "close": [181.0, 183.0, 185.5],
                                "volume": [100000, 120000, 150000],
                            }
                        ]
                    },
                }
            ],
            "error": None,
        }
    }


def test_get_history_success(mock_chart_payload):
    """Test successful retrieval and schema of historical candles."""
    provider = YahooFinanceProvider()
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = mock_chart_payload

    with patch.object(provider.session, "get", return_value=mock_resp):
        df, err = provider.get_history("AAPL", range_period="1d", interval="5m")

        assert err is None
        assert not df.empty
        assert list(df.columns) == ["Datetime", "Open", "High", "Low", "Close", "Volume"]
        assert len(df) == 3
        assert df["Close"].iloc[-1] == 185.5


def test_get_history_not_found():
    """Test 404 response handling."""
    provider = YahooFinanceProvider()
    mock_resp = MagicMock()
    mock_resp.status_code = 404

    with patch.object(provider.session, "get", return_value=mock_resp):
        df, err = provider.get_history("INVALIDTICKER")
        assert df.empty
        assert "not found" in err.lower()


def test_get_history_rate_limited():
    """Test 429 rate limit response handling."""
    provider = YahooFinanceProvider()
    mock_resp = MagicMock()
    mock_resp.status_code = 429

    with patch.object(provider.session, "get", return_value=mock_resp):
        df, err = provider.get_history("AAPL")
        assert df.empty
        assert "rate limit" in err.lower()


def test_get_history_empty_symbol():
    """Test empty symbol validation."""
    provider = YahooFinanceProvider()
    df, err = provider.get_history("")
    assert df.empty
    assert "cannot be empty" in err.lower()


def test_get_quote_success(mock_chart_payload):
    """Test quote extraction and derived fields."""
    provider = YahooFinanceProvider()
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = mock_chart_payload

    with patch.object(provider.session, "get", return_value=mock_resp):
        quote, err = provider.get_quote("AAPL")
        assert err is None
        assert quote is not None
        assert quote["symbol"] == "AAPL"
        assert quote["price"] == 185.50
        assert quote["previous_close"] == 180.00
        assert quote["change"] == 5.50
        assert round(quote["percent_change"], 2) == 3.06
        assert quote["currency"] == "$"
        assert quote["exchange"] == "NASDAQ"
        assert "market_status" in quote


def test_get_quote_indian_currency(mock_chart_payload):
    """Test currency symbol for Indian NSE tickers."""
    provider = YahooFinanceProvider()
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_chart_payload["chart"]["result"][0]["meta"]["symbol"] = "RELIANCE.NS"
    mock_chart_payload["chart"]["result"][0]["meta"]["currency"] = "INR"
    mock_resp.json.return_value = mock_chart_payload

    with patch.object(provider.session, "get", return_value=mock_resp):
        quote, err = provider.get_quote("RELIANCE.NS")
        assert err is None
        assert quote["currency"] == "₹"


def test_search_symbols():
    """Test symbol search suggestion parsing."""
    provider = YahooFinanceProvider()
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "quotes": [
            {"symbol": "TSLA", "shortname": "Tesla, Inc.", "exchDisp": "NASDAQ", "quoteType": "EQUITY"},
            {"symbol": "TSLZ", "shortname": "T-Rex 2X Inverse", "exchDisp": "BATS", "quoteType": "ETF"},
        ]
    }

    with patch.object(provider.session, "get", return_value=mock_resp):
        res = provider.search_symbols("Tesla")
        assert len(res) == 2
        assert res[0]["symbol"] == "TSLA"
        assert res[0]["exchange"] == "NASDAQ"


def test_get_provider_factory():
    """Test provider factory defaults."""
    prov = get_provider()
    assert isinstance(prov, YahooFinanceProvider)
