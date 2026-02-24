"""Data fetching and caching for market data.

Provides abstractions for fetching stock data from Finnhub (primary),
Alpha Vantage (second), and yfinance (last resort fallback) with
caching, retry logic, and proper error handling.
"""

import logging
import os
import time
from datetime import datetime, timezone
from typing import Any, Protocol

import finnhub
import httpx
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

# Map yfinance-style periods to (Finnhub resolution, lookback days)
_PERIOD_TO_FINNHUB: dict[str, tuple[str, int]] = {
    "1d": ("5", 1),        # 5-min bars for 1 day
    "5d": ("15", 5),       # 15-min bars for 5 days
    "1mo": ("D", 30),      # daily bars for 1 month
    "3mo": ("D", 90),      # daily bars for 3 months
    "6mo": ("D", 180),     # daily bars for 6 months
    "1y": ("D", 365),      # daily bars for 1 year
    "2y": ("W", 730),      # weekly bars for 2 years
    "5y": ("W", 1825),     # weekly bars for 5 years
    "10y": ("M", 3650),    # monthly bars for 10 years
    "ytd": ("D", 365),     # daily bars, will be trimmed to YTD
    "max": ("W", 7300),    # weekly bars for ~20 years
}

# Alpha Vantage function mapping by period
_PERIOD_TO_AV: dict[str, tuple[str, str | None, str]] = {
    # (function, interval_param, outputsize)
    "1d": ("TIME_SERIES_INTRADAY", "5min", "compact"),
    "5d": ("TIME_SERIES_INTRADAY", "15min", "compact"),
    "1mo": ("TIME_SERIES_DAILY", None, "compact"),
    "3mo": ("TIME_SERIES_DAILY", None, "compact"),
    "6mo": ("TIME_SERIES_DAILY", None, "full"),
    "1y": ("TIME_SERIES_DAILY", None, "full"),
    "2y": ("TIME_SERIES_WEEKLY", None, "full"),
    "5y": ("TIME_SERIES_WEEKLY", None, "full"),
    "10y": ("TIME_SERIES_MONTHLY", None, "full"),
    "ytd": ("TIME_SERIES_DAILY", None, "full"),
    "max": ("TIME_SERIES_WEEKLY", None, "full"),
}

_AV_BASE_URL = "https://www.alphavantage.co/query"

_AV_TIME_SERIES_KEYS: dict[str, Any] = {
    "TIME_SERIES_INTRADAY": lambda iv: f"Time Series ({iv})",
    "TIME_SERIES_DAILY": lambda _: "Time Series (Daily)",
    "TIME_SERIES_WEEKLY": lambda _: "Weekly Time Series",
    "TIME_SERIES_MONTHLY": lambda _: "Monthly Time Series",
}


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
    """Fetches OHLCV data from Finnhub (primary) with Alpha Vantage fallback.

    Replaces YFinanceDataFetcher to eliminate yfinance rate-limiting issues.
    Implements the DataFetcher protocol.
    """

    def __init__(
        self,
        finnhub_key: str,
        alpha_vantage_key: str,
        max_retries: int = MAX_RETRY_ATTEMPTS,
        backoff_seconds: float = RETRY_BACKOFF_SECONDS,
    ):
        """Initialize the data fetcher.

        Args:
            finnhub_key: Finnhub API key.
            alpha_vantage_key: Alpha Vantage API key.
            max_retries: Maximum retry attempts on failure.
            backoff_seconds: Base backoff time between retries.
        """
        self._finnhub = finnhub.Client(api_key=finnhub_key)
        self._av_key = alpha_vantage_key
        self._http = httpx.Client(timeout=30)
        self._max_retries = max_retries
        self._backoff = backoff_seconds
        self._yf_last_call: float = 0.0
        self._yf_min_interval: float = 2.0  # Min 2s between yfinance calls

    def fetch(self, symbol: str, period: str = DEFAULT_PERIOD) -> pd.DataFrame:
        """Fetch OHLCV data with Finnhub first, Alpha Vantage fallback.

        Args:
            symbol: Ticker symbol (e.g., 'AAPL').
            period: Time period (e.g., '1mo', '3mo', '1y').

        Returns:
            DataFrame with Open, High, Low, Close, Volume columns
            and a DatetimeIndex.

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
                df = self._fetch_finnhub(symbol, period)
                if df is not None and not df.empty:
                    return self._validate_and_return(df, symbol, period, "finnhub")

                df = self._fetch_alpha_vantage(symbol, period)
                if df is not None and not df.empty:
                    return self._validate_and_return(df, symbol, period, "alpha_vantage")

                df = self._fetch_yfinance(symbol, period)
                if df is not None and not df.empty:
                    return self._validate_and_return(df, symbol, period, "yfinance")

                raise DataFetchError(
                    symbol, period,
                    "Finnhub, Alpha Vantage, and yfinance all failed",
                )

            except (DataFetchError, InsufficientDataError):
                raise
            except Exception as e:
                last_error = e
                logger.warning(
                    "Fetch attempt %d/%d for %s failed: %s",
                    attempt, self._max_retries, symbol, e,
                )
                if attempt < self._max_retries:
                    sleep_time = self._backoff * (2 ** (attempt - 1))
                    time.sleep(sleep_time)

        raise DataFetchError(
            symbol, period,
            f"Failed after {self._max_retries} attempts: {last_error}",
        )

    def _validate_and_return(
        self, df: pd.DataFrame, symbol: str, period: str, source: str,
    ) -> pd.DataFrame:
        """Validate data and return if sufficient.

        Args:
            df: DataFrame with OHLCV data.
            symbol: Ticker symbol.
            period: Requested period.
            source: Data source name for logging.

        Returns:
            Validated DataFrame.

        Raises:
            InsufficientDataError: If not enough data points.
        """
        if len(df) < MIN_DATA_POINTS:
            raise InsufficientDataError(
                symbol,
                required_periods=MIN_DATA_POINTS,
                available_periods=len(df),
            )

        logger.info(
            "Fetched %d rows for %s (period: %s) from %s",
            len(df), symbol, period, source,
        )
        return df

    def _fetch_finnhub(self, symbol: str, period: str) -> pd.DataFrame | None:
        """Fetch OHLCV data from Finnhub stock candles API.

        Args:
            symbol: Ticker symbol.
            period: Time period.

        Returns:
            DataFrame with OHLCV data or None on failure.
        """
        mapping = _PERIOD_TO_FINNHUB.get(period)
        if not mapping:
            return None

        resolution, lookback_days = mapping
        now = int(time.time())
        from_ts = now - (lookback_days * 86400)

        try:
            raw = self._finnhub.stock_candles(symbol, resolution, from_ts, now)
        except Exception as e:
            logger.info("Finnhub candle fetch failed for %s/%s: %s", symbol, period, e)
            return None

        if not isinstance(raw, dict) or raw.get("s") != "ok":
            logger.info("Finnhub returned no data for %s/%s", symbol, period)
            return None

        timestamps = raw.get("t", [])
        if not timestamps:
            return None

        df = pd.DataFrame({
            "Open": raw.get("o", []),
            "High": raw.get("h", []),
            "Low": raw.get("l", []),
            "Close": raw.get("c", []),
            "Volume": raw.get("v", []),
        })

        df.index = pd.to_datetime(
            [datetime.fromtimestamp(ts, tz=timezone.utc) for ts in timestamps]
        )
        df.index.name = "Date"

        # Trim to YTD if requested
        if period == "ytd":
            year_start = datetime(datetime.now().year, 1, 1, tzinfo=timezone.utc)
            df = df[df.index >= year_start]

        logger.info("Finnhub: %d candles for %s/%s", len(df), symbol, period)
        return df

    def _fetch_alpha_vantage(self, symbol: str, period: str) -> pd.DataFrame | None:
        """Fetch OHLCV data from Alpha Vantage as fallback.

        Args:
            symbol: Ticker symbol.
            period: Time period.

        Returns:
            DataFrame with OHLCV data or None on failure.
        """
        mapping = _PERIOD_TO_AV.get(period)
        if not mapping:
            return None

        av_func, av_interval, outputsize = mapping

        params: dict[str, str] = {
            "function": av_func,
            "symbol": symbol,
            "apikey": self._av_key,
            "outputsize": outputsize,
        }
        if av_interval:
            params["interval"] = av_interval

        try:
            resp = self._http.get(_AV_BASE_URL, params=params)
            resp.raise_for_status()
            data = resp.json()
        except (httpx.HTTPError, ValueError) as e:
            logger.info("Alpha Vantage request failed for %s/%s: %s", symbol, period, e)
            return None

        if "Information" in data or "Error Message" in data:
            logger.info(
                "Alpha Vantage error for %s/%s: %s",
                symbol, period,
                data.get("Information") or data.get("Error Message"),
            )
            return None

        ts_key_fn = _AV_TIME_SERIES_KEYS.get(av_func)
        if not ts_key_fn:
            return None

        ts_key = ts_key_fn(av_interval)
        time_series = data.get(ts_key, {})

        if not time_series:
            return None

        rows = []
        for dt_str, vals in sorted(time_series.items()):
            rows.append({
                "Date": pd.Timestamp(dt_str),
                "Open": float(vals.get("1. open", 0)),
                "High": float(vals.get("2. high", 0)),
                "Low": float(vals.get("3. low", 0)),
                "Close": float(vals.get("4. close", 0)),
                "Volume": int(vals.get("5. volume", 0)),
            })

        df = pd.DataFrame(rows)
        df = df.set_index("Date")

        # Trim based on period lookback
        finnhub_mapping = _PERIOD_TO_FINNHUB.get(period)
        if finnhub_mapping:
            _, lookback_days = finnhub_mapping
            cutoff = pd.Timestamp.now() - pd.Timedelta(days=lookback_days)
            df = df[df.index >= cutoff]

        if period == "ytd":
            year_start = pd.Timestamp(datetime.now().year, 1, 1)
            df = df[df.index >= year_start]

        logger.info("Alpha Vantage: %d candles for %s/%s", len(df), symbol, period)
        return df

    def _fetch_yfinance(self, symbol: str, period: str) -> pd.DataFrame | None:
        """Fetch OHLCV data from yfinance as last-resort fallback.

        Used when both Finnhub (403 on candles) and Alpha Vantage
        (rate limited) fail.

        Args:
            symbol: Ticker symbol.
            period: Time period (e.g. '3mo', '1y').

        Returns:
            DataFrame with OHLCV data or None on failure.
        """
        try:
            import yfinance as yf
        except ImportError:
            logger.info("yfinance not installed, skipping fallback")
            return None

        # Rate limit: wait if needed to stay under Yahoo's limits
        elapsed = time.time() - self._yf_last_call
        if elapsed < self._yf_min_interval:
            time.sleep(self._yf_min_interval - elapsed)

        try:
            self._yf_last_call = time.time()
            ticker = yf.Ticker(symbol)
            df = ticker.history(period=period)
        except Exception as e:
            logger.info("yfinance fetch failed for %s/%s: %s", symbol, period, e)
            return None

        if df is None or df.empty:
            return None

        # Normalize column names to match expected format
        col_map = {
            "Stock Splits": None,
            "Dividends": None,
            "Capital Gains": None,
        }
        df = df.drop(columns=[c for c in col_map if c in df.columns], errors="ignore")

        # Ensure standard column names
        rename = {}
        for col in ["Open", "High", "Low", "Close", "Volume"]:
            lower = col.lower()
            if lower in df.columns and col not in df.columns:
                rename[lower] = col
        if rename:
            df = df.rename(columns=rename)

        logger.info("yfinance: %d candles for %s/%s", len(df), symbol, period)
        return df


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
        if fetcher is None:
            finnhub_key = os.getenv("FINNHUB_API_KEY", "")
            alpha_vantage_key = os.getenv("ALPHA_VANTAGE_KEY", "")
            fetcher = FinnhubAlphaDataFetcher(
                finnhub_key=finnhub_key,
                alpha_vantage_key=alpha_vantage_key,
            )
        self._fetcher = fetcher
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
            logger.info("Cache hit for %s", cache_key)
            return self._cache[cache_key].copy()

        logger.info("Cache miss for %s", cache_key)
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
            logger.info("Analysis cache hit for %s", cache_key)
            result = result.copy()
            result["cached"] = True
        else:
            logger.info("Analysis cache miss for %s", cache_key)

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
        logger.info("Cached analysis for %s", cache_key)

    def clear(self) -> None:
        """Clear all cached results."""
        self._cache.clear()
        logger.info("Analysis cache cleared")


def create_data_fetcher(use_cache: bool = True) -> DataFetcher:
    """Factory function to create a data fetcher.

    Reads FINNHUB_API_KEY and ALPHA_VANTAGE_KEY from environment variables.

    Args:
        use_cache: Whether to use caching.

    Returns:
        Configured data fetcher instance.

    Raises:
        RuntimeError: If required API keys are not set.
    """
    finnhub_key = os.getenv("FINNHUB_API_KEY", "")
    alpha_vantage_key = os.getenv("ALPHA_VANTAGE_KEY", "")

    if not finnhub_key and not alpha_vantage_key:
        raise RuntimeError(
            "At least one of FINNHUB_API_KEY or ALPHA_VANTAGE_KEY must be set. "
            "See .env.example for required configuration."
        )

    fetcher = FinnhubAlphaDataFetcher(
        finnhub_key=finnhub_key,
        alpha_vantage_key=alpha_vantage_key,
    )

    if use_cache:
        return CachedDataFetcher(fetcher)

    return fetcher
