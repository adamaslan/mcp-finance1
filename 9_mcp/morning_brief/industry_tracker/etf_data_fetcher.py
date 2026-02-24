"""ETF Data Fetcher - Multi-source data acquisition for ETF prices.

Supports three data sources with fallback chain:
1. Persistent Store (Firestore) - Zero-cost reads, full history
2. Finnhub API - Real-time, minimal quota consumption
3. Alpha Vantage API - Fallback for comprehensive history
4. yfinance - Free backup source (no API key needed)
"""

import logging
from typing import Optional
import pandas as pd

logger = logging.getLogger(__name__)


class ETFDataError(Exception):
    """Raised when ETF data fetch fails."""
    pass


class ETFDataFetcher:
    """Fetch historical ETF data from multiple sources with intelligent fallback."""

    def __init__(
        self,
        api_key: str = "",
        finnhub_key: str = "",
        persistent_store=None,
    ):
        """Initialize ETF data fetcher.

        Args:
            api_key: Alpha Vantage API key.
            finnhub_key: Finnhub API key (optional, preferred if available).
            persistent_store: Optional PersistentETFStore instance for cached reads.
        """
        self._alpha_key = api_key
        self._finnhub_key = finnhub_key
        self._persistent = persistent_store
        logger.info(
            "ETFDataFetcher initialized (finnhub=%s, persistent=%s, alpha=%s)",
            bool(finnhub_key), persistent_store is not None, bool(api_key)
        )

    async def fetch_daily_adjusted(
        self,
        symbol: str,
        outputsize: str = "compact",
    ) -> pd.DataFrame:
        """Fetch daily adjusted close prices with smart fallback.

        Priority chain:
        1. Persistent store (Firestore) if available
        2. Finnhub API if key is set
        3. Alpha Vantage API if key is set
        4. yfinance (free, no auth needed)

        Args:
            symbol: ETF ticker symbol (e.g., 'IGV').
            outputsize: 'compact' (last 100 days) or 'full' (all history).

        Returns:
            DataFrame with columns: date, adjusted_close, volume
            Sorted newest-first, ready for PerformanceCalculator.

        Raises:
            ETFDataError: If all sources fail.
        """
        symbol = symbol.upper()
        logger.info("Fetching %s (size=%s)", symbol, outputsize)

        # Try 1: Persistent store (zero-cost reads from Firestore)
        if self._persistent:
            try:
                df = self._persistent.load_history(symbol)
                if df is not None and not df.empty:
                    logger.info("✓ Fetched %s from persistent store (%d days)", symbol, len(df))
                    return df
            except Exception as e:
                logger.debug("Persistent store fetch failed for %s: %s", symbol, e)

        # Try 2: Finnhub API (preferred - minimal quota, real-time)
        if self._finnhub_key:
            try:
                df = await self._fetch_finnhub(symbol)
                if df is not None and not df.empty:
                    logger.info("✓ Fetched %s from Finnhub API (%d days)", symbol, len(df))
                    return df
            except Exception as e:
                logger.debug("Finnhub fetch failed for %s: %s", symbol, e)

        # Try 3: Alpha Vantage API (fallback - slower, quota-limited)
        if self._alpha_key:
            try:
                df = await self._fetch_alpha_vantage(symbol, outputsize)
                if df is not None and not df.empty:
                    logger.info("✓ Fetched %s from Alpha Vantage (%d days)", symbol, len(df))
                    return df
            except Exception as e:
                logger.debug("Alpha Vantage fetch failed for %s: %s", symbol, e)

        # Try 4: yfinance (free fallback, no auth needed)
        try:
            df = await self._fetch_yfinance(symbol)
            if df is not None and not df.empty:
                logger.info("✓ Fetched %s from yfinance (%d days)", symbol, len(df))
                return df
        except Exception as e:
            logger.debug("yfinance fetch failed for %s: %s", symbol, e)

        raise ETFDataError(f"All data sources failed for {symbol}")

    async def _fetch_finnhub(self, symbol: str) -> Optional[pd.DataFrame]:
        """Fetch from Finnhub API.

        Args:
            symbol: ETF ticker.

        Returns:
            DataFrame or None if fetch fails.
        """
        try:
            import httpx

            url = "https://finnhub.io/api/v1/quote"
            params = {"symbol": symbol, "token": self._finnhub_key}

            async with httpx.AsyncClient() as client:
                response = await client.get(url, params=params, timeout=10)
                response.raise_for_status()
                data = response.json()

                if "c" not in data:
                    logger.warning("No price data in Finnhub response for %s", symbol)
                    return None

                # Convert to DataFrame format
                return pd.DataFrame({
                    "date": [pd.Timestamp.now()],
                    "adjusted_close": [float(data.get("c", 0))],
                    "volume": [int(data.get("v", 0))],
                })

        except Exception as e:
            logger.error("Finnhub fetch failed for %s: %s", symbol, e)
            return None

    async def _fetch_alpha_vantage(
        self,
        symbol: str,
        outputsize: str = "full",
    ) -> Optional[pd.DataFrame]:
        """Fetch from Alpha Vantage API.

        Args:
            symbol: ETF ticker.
            outputsize: 'compact' or 'full'.

        Returns:
            DataFrame or None if fetch fails.
        """
        try:
            import httpx

            url = "https://www.alphavantage.co/query"
            params = {
                "function": "TIME_SERIES_DAILY_ADJUSTED",
                "symbol": symbol,
                "outputsize": outputsize,
                "apikey": self._alpha_key,
            }

            async with httpx.AsyncClient() as client:
                response = await client.get(url, params=params, timeout=30)
                response.raise_for_status()
                data = response.json()

                if "Time Series (Daily)" not in data:
                    logger.warning("No time series in Alpha Vantage response for %s", symbol)
                    return None

                ts = data["Time Series (Daily)"]
                records = []

                for date_str, day_data in ts.items():
                    records.append({
                        "date": pd.to_datetime(date_str),
                        "adjusted_close": float(day_data.get("5. adjusted close", 0)),
                        "volume": int(day_data.get("6. volume", 0)),
                    })

                if not records:
                    return None

                df = pd.DataFrame(records)
                df.sort_values("date", ascending=False, inplace=True)
                df.reset_index(drop=True, inplace=True)

                return df

        except Exception as e:
            logger.error("Alpha Vantage fetch failed for %s: %s", symbol, e)
            return None

    async def _fetch_yfinance(self, symbol: str) -> Optional[pd.DataFrame]:
        """Fetch from yfinance (free, no auth).

        Args:
            symbol: ETF ticker.

        Returns:
            DataFrame or None if fetch fails.
        """
        try:
            import yfinance as yf

            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="10y")

            if hist.empty:
                logger.warning("No data from yfinance for %s", symbol)
                return None

            # Rename columns to match expected format
            hist.columns = hist.columns.str.lower()

            df = hist.reset_index()
            df.columns = df.columns.str.lower()

            if 'close' in df.columns:
                df['adjusted_close'] = df['close']
            elif 'adj close' in df.columns:
                df['adjusted_close'] = df['adj close']

            # Sort newest first
            df = df.sort_values('date', ascending=False).reset_index(drop=True)

            logger.info("yfinance fetch successful for %s (%d days)", symbol, len(df))
            return df[['date', 'adjusted_close', 'volume']].copy()

        except Exception as e:
            logger.error("yfinance fetch failed for %s: %s", symbol, e)
            return None
