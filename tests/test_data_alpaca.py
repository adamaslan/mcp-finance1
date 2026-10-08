"""Alpaca-first fetch chain for FinnhubAlphaDataFetcher (no network)."""
import sys
import types
from pathlib import Path
from unittest.mock import patch

import pandas as pd
import pytest

_PKG_DIR = Path(__file__).resolve().parents[1] / "src" / "technical_analysis_mcp"
# Register a bare package so data.py loads without the package __init__, which pulls
# in the full signal stack. These tests only exercise the fetch chain.
if "technical_analysis_mcp" not in sys.modules or not hasattr(
    sys.modules["technical_analysis_mcp"], "data"
):
    _pkg = types.ModuleType("technical_analysis_mcp")
    _pkg.__path__ = [str(_PKG_DIR)]
    sys.modules["technical_analysis_mcp"] = _pkg

from technical_analysis_mcp import data  # noqa: E402
from technical_analysis_mcp.exceptions import DataFetchError  # noqa: E402


def _bars(n: int = 60) -> pd.DataFrame:
    idx = pd.bdate_range("2025-01-01", periods=n)
    return pd.DataFrame(
        {"Open": 1.0, "High": 2.0, "Low": 0.5, "Close": 1.5, "Volume": 100}, index=idx
    )


@pytest.fixture
def fetcher():
    return data.FinnhubAlphaDataFetcher(alpha_vantage_key="", max_retries=1)


def test_alpaca_is_first_source(fetcher):
    with patch.object(data.alpaca_md, "is_configured", return_value=True), \
         patch.object(data.alpaca_md, "daily_bars_frames", return_value={"AAPL": _bars()}), \
         patch.object(fetcher, "_fetch_yfinance") as yf:
        df = fetcher.fetch("AAPL", "6mo")
    assert len(df) == 60
    yf.assert_not_called()


def test_long_period_is_resampled_to_weekly(fetcher):
    with patch.object(data.alpaca_md, "is_configured", return_value=True), \
         patch.object(data.alpaca_md, "daily_bars_frames", return_value={"AAPL": _bars(200)}):
        df = fetcher._fetch_alpaca("AAPL", "2y")
    assert len(df) < 200
    assert df["High"].max() == 2.0


def test_intraday_skips_alpaca(fetcher):
    with patch.object(data.alpaca_md, "is_configured", return_value=True), \
         patch.object(data.alpaca_md, "daily_bars_frames") as bars:
        assert fetcher._fetch_alpaca("AAPL", "1d") is None
    bars.assert_not_called()


def test_yfinance_skipped_on_datacenter_host(fetcher):
    with patch.object(data.alpaca_md, "is_configured", return_value=False), \
         patch.object(data.alpaca_md, "on_datacenter_host", return_value=True), \
         patch.object(fetcher, "_fetch_yfinance") as yf:
        with pytest.raises(DataFetchError):
            fetcher.fetch("AAPL", "6mo")
    yf.assert_not_called()


def test_yfinance_fallback_allowed_locally(fetcher):
    with patch.object(data.alpaca_md, "is_configured", return_value=False), \
         patch.object(data.alpaca_md, "on_datacenter_host", return_value=False), \
         patch.object(fetcher, "_fetch_yfinance", return_value=_bars()) as yf:
        df = fetcher.fetch("AAPL", "6mo")
    assert len(df) == 60
    yf.assert_called_once()
