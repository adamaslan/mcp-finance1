"""Alpha Vantage ETF historical data fetcher.

Fetches daily adjusted close prices for ETFs with error handling
and rate limiting.
"""

import logging
import time
from typing import Optional
import httpx
import pandas as pd
from datetime import datetime

logger = logging.getLogger(__name__)


class ETFDataError(Exception):
    """Raised when ETF data cannot be fetched."""
    pass


class ETFDataFetcher:
    """Fetch historical ETF data from Alpha Vantage."""

    def __init__(self, api_key: str, rate_limit_delay: float = 12.0):
        """Initialize ETF data fetcher.

        Args:
            api_key: Alpha Vantage API key.
            rate_limit_delay: Seconds to wait between API calls (free tier: 5/min = 12s).

        Raises:
            ValueError: If api_key is empty.
        """
        if not api_key:
            raise ValueError("Alpha Vantage API key is required")

        self._api_key = api_key
        self._rate_limit = rate_limit_delay
        self._base_url = "https://www.alphavantage.co/query"
        self._last_call_time = 0.0

    async def fetch_daily_adjusted(
        self,
        symbol: str,
        outputsize: str = "full",
    ) -> pd.DataFrame:
        """Fetch daily adjusted close prices for an ETF.

        Args:
            symbol: ETF ticker symbol.
            outputsize: 'compact' (100 days) or 'full' (20+ years).

        Returns:
            DataFrame with columns: date, adjusted_close, volume.
            Indexed by date (newest first).

        Raises:
            ETFDataError: If data fetch fails or API returns error.
        """
        symbol = symbol.upper().strip()
        logger.info("Fetching daily adjusted data for %s (outputsize=%s)", symbol, outputsize)

        # Rate limiting
        await self._enforce_rate_limit()

        params = {
            "function": "TIME_SERIES_DAILY_ADJUSTED",
            "symbol": symbol,
            "outputsize": outputsize,
            "apikey": self._api_key,
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(self._base_url, params=params)
                response.raise_for_status()
                data = response.json()

        except httpx.HTTPError as e:
            raise ETFDataError(f"HTTP error fetching {symbol}: {e}") from e
        except Exception as e:
            raise ETFDataError(f"Error fetching {symbol}: {e}") from e

        # Check for API errors
        if "Error Message" in data:
            raise ETFDataError(f"Alpha Vantage error for {symbol}: {data['Error Message']}")

        if "Note" in data:
            raise ETFDataError(
                f"Alpha Vantage rate limit hit for {symbol}. "
                f"Free tier allows 5 calls/minute, 500/day."
            )

        # Extract time series data
        time_series_key = "Time Series (Daily)"
        if time_series_key not in data:
            raise ETFDataError(
                f"No time series data for {symbol}. "
                f"Response keys: {list(data.keys())}"
            )

        time_series = data[time_series_key]
        if not time_series:
            raise ETFDataError(f"Empty time series for {symbol}")

        # Convert to DataFrame
        df = self._parse_time_series(time_series, symbol)

        logger.info("Fetched %d days of data for %s (range: %s to %s)",
                    len(df), symbol, df.index[-1], df.index[0])

        return df

    def _parse_time_series(self, time_series: dict, symbol: str) -> pd.DataFrame:
        """Parse Alpha Vantage time series JSON to DataFrame.

        Args:
            time_series: Time series dict from Alpha Vantage.
            symbol: ETF symbol for logging.

        Returns:
            DataFrame with date index and adjusted_close, volume columns.
        """
        records = []
        for date_str, values in time_series.items():
            try:
                date = pd.to_datetime(date_str)
                adjusted_close = float(values.get("5. adjusted close", 0))
                volume = int(values.get("6. volume", 0))

                records.append({
                    "date": date,
                    "adjusted_close": adjusted_close,
                    "volume": volume,
                })
            except (ValueError, KeyError) as e:
                logger.warning("Skipping invalid data for %s on %s: %s", symbol, date_str, e)
                continue

        if not records:
            raise ETFDataError(f"No valid records parsed for {symbol}")

        df = pd.DataFrame(records)
        df.set_index("date", inplace=True)
        df.sort_index(ascending=False, inplace=True)  # Newest first

        return df

    async def _enforce_rate_limit(self) -> None:
        """Enforce rate limiting between API calls.

        Alpha Vantage free tier: 5 calls/minute, 500 calls/day.
        """
        current_time = time.time()
        elapsed = current_time - self._last_call_time

        if elapsed < self._rate_limit:
            wait_time = self._rate_limit - elapsed
            logger.debug("Rate limiting: waiting %.1fs before next API call", wait_time)
            time.sleep(wait_time)

        self._last_call_time = time.time()

    async def fetch_multiple(
        self,
        symbols: list[str],
        outputsize: str = "full",
    ) -> dict[str, pd.DataFrame]:
        """Fetch data for multiple ETFs sequentially (respects rate limits).

        Args:
            symbols: List of ETF ticker symbols.
            outputsize: 'compact' or 'full'.

        Returns:
            Dict mapping symbol → DataFrame.
            Failed symbols are logged but not included.
        """
        results = {}

        for symbol in symbols:
            try:
                df = await self.fetch_daily_adjusted(symbol, outputsize)
                results[symbol] = df
            except ETFDataError as e:
                logger.error("Failed to fetch %s: %s", symbol, e)
                # Continue fetching other symbols

        logger.info("Successfully fetched %d/%d symbols", len(results), len(symbols))
        return results

    def get_latest_price(self, df: pd.DataFrame) -> Optional[float]:
        """Extract latest adjusted close price from DataFrame.

        Args:
            df: DataFrame from fetch_daily_adjusted().

        Returns:
            Latest price or None if DataFrame is empty.
        """
        if df.empty:
            return None
        return float(df.iloc[0]["adjusted_close"])

    def get_price_at(self, df: pd.DataFrame, days_ago: int) -> Optional[float]:
        """Get price N trading days ago.

        Args:
            df: DataFrame from fetch_daily_adjusted().
            days_ago: Number of trading days in the past (0 = today).

        Returns:
            Price N days ago or None if insufficient data.
        """
        if df.empty or days_ago >= len(df):
            return None
        return float(df.iloc[days_ago]["adjusted_close"])
