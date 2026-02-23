"""Data fetching and caching for market data.

Provides abstractions for fetching stock data from Finnhub (primary)
and Alpha Vantage (fallback) with caching, retry logic, and proper error handling.
No yfinance dependency.
"""

import logging
import os
import time
from typing import Any, Protocol

import pandas as pd
from cachetools import TTLCache

from .config import (
    CACHE_MAX_SIZE,
    CACHE_TTL_SECONDS,
    DEFAULT_PERIOD,
    MAX_RETRY_ATTEMPTS,
    MIN_DATA_POINTS,
    RETRY_BACKOFF_SECONDS,
    VALID_PERIODS,
)
from .exceptions import DataFetchError, InsufficientDataError, InvalidSymbolError

logger = logging.getLogger(__name__)


class DataFetcher(Protocol):
    """Protocol for data fetching strategies."""

    def fetch(self, symbol: str, period: str) -> pd.DataFrame:
        """Fetch OHLCV data for a symbol.

        Args:
            symbol: Ticker symbol.
            period: Time period (e.g., '1mo', '3mo').

        Returns:
            DataFrame with OHLCV data.
        """
        ...


class FinnhubAlphaDataFetcher:
    """Fetches market data from Finnhub (primary) or Alpha Vantage (fallback) with retry logic."""

    def __init__(
        self,
        finnhub_key: str | None = None,
        alpha_vantage_key: str | None = None,
        max_retries: int = MAX_RETRY_ATTEMPTS,
        backoff_seconds: float = RETRY_BACKOFF_SECONDS,
    ):
        """Initialize the data fetcher.

        Args:
            finnhub_key: Finnhub API key (from env if not provided).
            alpha_vantage_key: Alpha Vantage API key (from env if not provided).
            max_retries: Maximum retry attempts on failure.
            backoff_seconds: Base backoff time between retries.
        """
        self._finnhub_key = finnhub_key or os.getenv("FINNHUB_API_KEY", "")
        self._alpha_vantage_key = alpha_vantage_key or os.getenv("ALPHA_VANTAGE_KEY", "")
        self._max_retries = max_retries
        self._backoff = backoff_seconds

        if not self._finnhub_key:
            logger.warning("FINNHUB_API_KEY not set - Finnhub data fetching will fail")

    def fetch(self, symbol: str, period: str = DEFAULT_PERIOD) -> pd.DataFrame:
        """Fetch OHLCV data from yfinance with retries.

        Args:
            symbol: Ticker symbol (e.g., 'AAPL').
            period: Time period (e.g., '1mo', '3mo', '1y').

        Returns:
            DataFrame with Open, High, Low, Close, Volume columns.

        Raises:
            InvalidSymbolError: If symbol is empty or invalid.
            DataFetchError: If fetching fails after retries.
            InsufficientDataError: If not enough data points returned.
        """
        if not symbol:
            raise InvalidSymbolError("")

        symbol = symbol.upper().strip()

        if period not in VALID_PERIODS:
            logger.warning("Invalid period '%s', using default '%s'", period, DEFAULT_PERIOD)
            period = DEFAULT_PERIOD

        last_error: Exception | None = None

        for attempt in range(1, self._max_retries + 1):
            try:
                df = self._fetch_data(symbol, period)

                if df.empty:
                    raise DataFetchError(symbol, period, f"No data returned for {symbol}")

                if len(df) < MIN_DATA_POINTS:
                    raise InsufficientDataError(
                        symbol,
                        required_periods=MIN_DATA_POINTS,
                        available_periods=len(df),
                    )

                logger.info("Fetched %d rows for %s (period: %s)", len(df), symbol, period)
                return df

            except (DataFetchError, InsufficientDataError):
                raise
            except Exception as e:
                last_error = e
                logger.warning(
                    "Fetch attempt %d/%d for %s failed: %s",
                    attempt,
                    self._max_retries,
                    symbol,
                    e,
                )
                if attempt < self._max_retries:
                    sleep_time = self._backoff * (2 ** (attempt - 1))
                    time.sleep(sleep_time)

        raise DataFetchError(symbol, period, f"Failed after {self._max_retries} attempts: {last_error}")

    def _fetch_data(self, symbol: str, period: str) -> pd.DataFrame:
        """Perform the actual Finnhub/AV fetch.

        Args:
            symbol: Ticker symbol.
            period: Time period.

        Returns:
            Raw DataFrame from Finnhub or Alpha Vantage.

        Raises:
            DataFetchError: If both Finnhub and AV fail.
        """
        import finnhub
        import httpx

        # Try Finnhub first
        if self._finnhub_key:
            try:
                client = finnhub.Client(api_key=self._finnhub_key)
                # Map period to Finnhub resolution/lookback
                period_map = {
                    "1d": ("5", 1),
                    "5d": ("15", 5),
                    "1mo": ("D", 30),
                    "3mo": ("D", 90),
                    "6mo": ("D", 180),
                    "1y": ("D", 365),
                    "2y": ("W", 730),
                    "5y": ("W", 1825),
                    "10y": ("M", 3650),
                    "max": ("W", 7300),
                }
                resolution, lookback = period_map.get(period, ("D", 365))

                candles = client.stock_candle(symbol, resolution)

                if not candles or "o" not in candles:
                    raise DataFetchError(symbol, period, "No candle data from Finnhub")

                df = pd.DataFrame({
                    "Open": candles["o"],
                    "High": candles["h"],
                    "Low": candles["l"],
                    "Close": candles["c"],
                    "Volume": candles.get("v", [0] * len(candles["c"])),
                })
                df.index = pd.to_datetime(candles.get("t", range(len(df))), unit="s")
                return df
            except Exception as e:
                logger.warning("Finnhub fetch failed for %s: %s, trying Alpha Vantage", symbol, e)

        # Fallback to Alpha Vantage
        if self._alpha_vantage_key:
            try:
                av_url = "https://www.alphavantage.co/query"
                params = {
                    "function": "TIME_SERIES_DAILY",
                    "symbol": symbol,
                    "apikey": self._alpha_vantage_key,
                    "outputsize": "full"
                }
                with httpx.Client() as client:
                    resp = client.get(av_url, params=params)
                    data = resp.json()

                if "Time Series (Daily)" not in data:
                    raise DataFetchError(symbol, period, "No time series from Alpha Vantage")

                ts_data = data["Time Series (Daily)"]
                dates = []
                opens = []
                highs = []
                lows = []
                closes = []
                volumes = []

                for date_str, ohlcv in ts_data.items():
                    dates.append(pd.to_datetime(date_str))
                    opens.append(float(ohlcv["1. open"]))
                    highs.append(float(ohlcv["2. high"]))
                    lows.append(float(ohlcv["3. low"]))
                    closes.append(float(ohlcv["4. close"]))
                    volumes.append(int(float(ohlcv["5. volume"])))

                df = pd.DataFrame({
                    "Open": opens,
                    "High": highs,
                    "Low": lows,
                    "Close": closes,
                    "Volume": volumes,
                }, index=dates)
                df = df.sort_index()
                return df
            except Exception as e:
                logger.warning("Alpha Vantage fetch failed for %s: %s", symbol, e)
                raise DataFetchError(symbol, period, f"Both Finnhub and Alpha Vantage failed: {e}")

        raise DataFetchError(symbol, period, "No API keys configured for data fetching")


class CachedDataFetcher:
    """Wraps a DataFetcher with TTL caching."""

    def __init__(
        self,
        fetcher: DataFetcher | None = None,
        cache_ttl: int = CACHE_TTL_SECONDS,
        cache_size: int = CACHE_MAX_SIZE,
    ):
        """Initialize cached data fetcher.

        Args:
            fetcher: Underlying data fetcher. Defaults to FinnhubAlphaDataFetcher.
            cache_ttl: Cache time-to-live in seconds.
            cache_size: Maximum number of items in cache.
        """
        self._fetcher = fetcher or FinnhubAlphaDataFetcher()
        self._cache: TTLCache[str, pd.DataFrame] = TTLCache(maxsize=cache_size, ttl=cache_ttl)

    def fetch(self, symbol: str, period: str = DEFAULT_PERIOD) -> pd.DataFrame:
        """Fetch data with caching.

        Args:
            symbol: Ticker symbol.
            period: Time period.

        Returns:
            DataFrame with OHLCV data (may be cached).
        """
        cache_key = f"{symbol.upper()}:{period}"

        if cache_key in self._cache:
            logger.debug("Cache hit for %s", cache_key)
            return self._cache[cache_key].copy()

        logger.debug("Cache miss for %s", cache_key)
        df = self._fetcher.fetch(symbol, period)
        self._cache[cache_key] = df.copy()

        return df

    def clear_cache(self) -> None:
        """Clear all cached data."""
        self._cache.clear()
        logger.info("Data cache cleared")

    def cache_stats(self) -> dict[str, Any]:
        """Get cache statistics.

        Returns:
            Dictionary with cache stats.
        """
        return {
            "current_size": len(self._cache),
            "max_size": self._cache.maxsize,
            "ttl_seconds": self._cache.ttl,
        }


class AnalysisResultCache:
    """Cache for complete analysis results."""

    def __init__(
        self,
        cache_ttl: int = CACHE_TTL_SECONDS,
        cache_size: int = CACHE_MAX_SIZE,
    ):
        """Initialize analysis result cache.

        Args:
            cache_ttl: Cache time-to-live in seconds.
            cache_size: Maximum number of items in cache.
        """
        self._cache: TTLCache[str, dict[str, Any]] = TTLCache(maxsize=cache_size, ttl=cache_ttl)

    def get(self, symbol: str, period: str) -> dict[str, Any] | None:
        """Get cached analysis result.

        Args:
            symbol: Ticker symbol.
            period: Time period.

        Returns:
            Cached result or None if not found.
        """
        cache_key = f"{symbol.upper()}:{period}"
        result = self._cache.get(cache_key)

        if result:
            logger.debug("Analysis cache hit for %s", cache_key)
            result = result.copy()
            result["cached"] = True
        else:
            logger.debug("Analysis cache miss for %s", cache_key)

        return result

    def set(self, symbol: str, period: str, result: dict[str, Any]) -> None:
        """Store analysis result in cache.

        Args:
            symbol: Ticker symbol.
            period: Time period.
            result: Analysis result to cache.
        """
        cache_key = f"{symbol.upper()}:{period}"
        self._cache[cache_key] = result.copy()
        logger.debug("Cached analysis for %s", cache_key)

    def clear(self) -> None:
        """Clear all cached results."""
        self._cache.clear()
        logger.info("Analysis cache cleared")


def create_data_fetcher(use_cache: bool = True) -> DataFetcher:
    """Factory function to create a data fetcher.

    Args:
        use_cache: Whether to use caching.

    Returns:
        Configured data fetcher instance.
    """
    fetcher = YFinanceDataFetcher()

    if use_cache:
        return CachedDataFetcher(fetcher)

    return fetcher
