"""Data fetching and caching for market data.

Provides abstractions for fetching stock data from Alpaca (primary),
Alpha Vantage (intraday and second), and yfinance (local-only last resort) with
caching, retry logic, and proper error handling.
"""

import logging
import os
import time
from datetime import datetime, timezone
from typing import Any, Protocol

import httpx
import pandas as pd
from cachetools import TTLCache

from . import alpaca_md
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

# Map yfinance-style periods to (lookback days, resample rule). Alpaca serves daily
# bars; longer periods are resampled from them. Intraday periods go to Alpha Vantage.
_PERIOD_TO_ALPACA: dict[str, tuple[int, str | None]] = {
    "1mo": (30, None),
    "3mo": (90, None),
    "6mo": (180, None),
    "1y": (365, None),
    "2y": (730, "W-FRI"),
    "5y": (1825, "W-FRI"),
    "10y": (3650, "ME"),
    "ytd": (365, None),
    "max": (7300, "W-FRI"),
}
_INTRADAY_PERIODS = {"1d": 1, "5d": 5}
_LOOKBACK_DAYS: dict[str, int] = {
    **{p: d for p, (d, _) in _PERIOD_TO_ALPACA.items()},
    **_INTRADAY_PERIODS,
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
    """Fetches OHLCV data from Alpaca (primary) with Alpha Vantage + yfinance fallback.

    Implements the DataFetcher protocol with 3-source fallback chain:
    1. Alpaca (primary; daily bars, resampled for long periods)
    2. Alpha Vantage (fallback, limited free tier)
    3. yfinance (last resort, local runs only; Yahoo blocks cloud IPs)
    """

    def __init__(
        self,
        finnhub_key: str | None = None,
        alpha_vantage_key: str | None = None,
        max_retries: int = MAX_RETRY_ATTEMPTS,
        backoff_seconds: float = RETRY_BACKOFF_SECONDS,
    ):
        """Initialize the data fetcher.

        Args:
            finnhub_key: Unused; kept for call-site compatibility (Finnhub candles are paid).
            alpha_vantage_key: Alpha Vantage API key (from env if not provided).
            max_retries: Maximum retry attempts on failure.
            backoff_seconds: Base backoff time between retries.
        """
        self._alpha_vantage_key = alpha_vantage_key or os.getenv("ALPHA_VANTAGE_KEY", "")
        self._max_retries = max_retries
        self._backoff = backoff_seconds

        if not alpaca_md.is_configured():
            logger.warning("ALPACA_API_KEY/ALPACA_API_SECRET not set - Alpaca data fetching is off")

        # Initialize HTTP client for Alpha Vantage
        self._http = httpx.Client(timeout=30)

        # Rate limiting for yfinance (2s minimum between calls)
        self._yf_last_call: float = 0.0
        self._yf_min_interval: float = 2.0

    def fetch(self, symbol: str, period: str = DEFAULT_PERIOD) -> pd.DataFrame:
        """Fetch OHLCV data with 3-source fallback: Alpaca → AV → yfinance (local only).

        Args:
            symbol: Ticker symbol (e.g., 'AAPL').
            period: Time period (e.g., '1mo', '3mo', '1y').

        Returns:
            DataFrame with Open, High, Low, Close, Volume columns
            and a DatetimeIndex.

        Raises:
            InvalidSymbolError: If symbol is empty or invalid.
            DataFetchError: If all 3 sources fail after retries.
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
                df = self._fetch_alpaca(symbol, period)
                if df is not None and not df.empty:
                    return self._validate_and_return(df, symbol, period, "alpaca")
                if period in _PERIOD_TO_ALPACA:
                    alpaca_md.warn_fallback(f"{period} bars", [symbol], "no Alpaca bars")

                # Fall back to Alpha Vantage
                df = self._fetch_alpha_vantage(symbol, period)
                if df is not None and not df.empty:
                    return self._validate_and_return(df, symbol, period, "alpha_vantage")

                # Last resort: yfinance, never from a cloud host (Yahoo blocks those IPs)
                if not alpaca_md.on_datacenter_host():
                    df = self._fetch_yfinance(symbol, period)
                    if df is not None and not df.empty:
                        return self._validate_and_return(df, symbol, period, "yfinance")

                raise DataFetchError(
                    symbol, period,
                    "Alpaca, Alpha Vantage, and yfinance (local only) all failed",
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

    def _fetch_alpaca(self, symbol: str, period: str) -> pd.DataFrame | None:
        """Fetch daily bars from Alpaca (SIP, split-adjusted), resampled for long periods.

        Intraday periods are not served here; they fall through to Alpha Vantage.

        Args:
            symbol: Ticker symbol.
            period: Time period.

        Returns:
            DataFrame with OHLCV data or None on failure.
        """
        mapping = _PERIOD_TO_ALPACA.get(period)
        if not mapping or not alpaca_md.is_configured():
            return None

        lookback_days, resample_rule = mapping
        try:
            frames = alpaca_md.daily_bars_frames([symbol], days=lookback_days)
        except (alpaca_md.AlpacaError, OSError) as e:
            logger.warning("Alpaca bars failed for %s/%s: %s", symbol, period, e)
            return None

        df = frames.get(symbol)
        if df is None or df.empty:
            return None

        if resample_rule:
            df = df.resample(resample_rule).agg({
                "Open": "first", "High": "max", "Low": "min",
                "Close": "last", "Volume": "sum",
            }).dropna(subset=["Close"])

        if period == "ytd":
            df = df[df.index >= pd.Timestamp(datetime.now().year, 1, 1)]

        df.index.name = "Date"
        logger.info("Alpaca: %d bars for %s/%s", len(df), symbol, period)
        return df

    def _fetch_alpha_vantage(self, symbol: str, period: str) -> pd.DataFrame | None:
        """Fetch OHLCV data from Alpha Vantage as fallback.

        Args:
            symbol: Ticker symbol.
            period: Time period.

        Returns:
            DataFrame with OHLCV data or None on failure.
        """
        if not self._alpha_vantage_key:
            return None

        mapping = _PERIOD_TO_AV.get(period)
        if not mapping:
            return None

        av_func, av_interval, outputsize = mapping

        params: dict[str, str] = {
            "function": av_func,
            "symbol": symbol,
            "apikey": self._alpha_vantage_key,
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
        lookback_days = _LOOKBACK_DAYS.get(period)
        if lookback_days:
            cutoff = pd.Timestamp.now() - pd.Timedelta(days=lookback_days)
            df = df[df.index >= cutoff]

        if period == "ytd":
            year_start = pd.Timestamp(datetime.now().year, 1, 1)
            df = df[df.index >= year_start]

        logger.info("Alpha Vantage: %d candles for %s/%s", len(df), symbol, period)
        return df

    def _fetch_yfinance(self, symbol: str, period: str) -> pd.DataFrame | None:
        """Fetch OHLCV data from yfinance as last-resort fallback.

        Used when both Alpaca and Alpha Vantage fail, on local hosts only.

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
            fetcher: Underlying data fetcher. Defaults to FinnhubAlphaDataFetcher.
            cache_ttl: Cache time-to-live in seconds.
            cache_size: Maximum number of items in cache.
        """
        if fetcher is None:
            fetcher = FinnhubAlphaDataFetcher(
                alpha_vantage_key=os.getenv("ALPHA_VANTAGE_KEY", ""),
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

    Reads ALPACA_API_KEY/ALPACA_API_SECRET and ALPHA_VANTAGE_KEY from environment variables.

    Args:
        use_cache: Whether to use caching.

    Returns:
        Configured data fetcher instance.

    Raises:
        RuntimeError: If required API keys are not set.
    """
    alpha_vantage_key = os.getenv("ALPHA_VANTAGE_KEY", "")

    if not alpaca_md.is_configured() and not alpha_vantage_key:
        raise RuntimeError(
            "Set ALPACA_API_KEY and ALPACA_API_SECRET (primary) or ALPHA_VANTAGE_KEY. "
            "See .env.example for required configuration."
        )

    fetcher = FinnhubAlphaDataFetcher(alpha_vantage_key=alpha_vantage_key)

    if use_cache:
        return CachedDataFetcher(fetcher)

    return fetcher
