"""Data fetching and caching for market data.

Provides abstractions for fetching stock data from yfinance with
caching, retry logic, and proper error handling.
"""

import logging
import time
from typing import Any, Protocol

import pandas as pd
import yfinance as yf
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


class YFinanceDataFetcher:
    """Fetches market data from Yahoo Finance with retry logic."""

    def __init__(
        self,
        max_retries: int = MAX_RETRY_ATTEMPTS,
        backoff_seconds: float = RETRY_BACKOFF_SECONDS,
    ):
        """Initialize the data fetcher.

        Args:
            max_retries: Maximum retry attempts on failure.
            backoff_seconds: Base backoff time between retries.
        """
        self._max_retries = max_retries
        self._backoff = backoff_seconds

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
        """Perform the actual yfinance fetch.

        Args:
            symbol: Ticker symbol.
            period: Time period.

        Returns:
            Raw DataFrame from yfinance.
        """
        ticker = yf.Ticker(symbol)
        return ticker.history(period=period)


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
            fetcher: Underlying data fetcher. Defaults to YFinanceDataFetcher.
            cache_ttl: Cache time-to-live in seconds.
            cache_size: Maximum number of items in cache.
        """
        self._fetcher = fetcher or YFinanceDataFetcher()
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
