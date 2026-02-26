"""Industry Brief Generator - Main module for industry performance analysis.

Fetches ETF data and generates industry performance summaries for multiple time horizons.

Data resolution chain (per PERSISTENT_STORAGE_EFFICIENCY.md):
1. Firestore persistent store (permanent, zero API cost)
2. Finnhub API
3. Alpha Vantage API
4. yfinance (free fallback)
"""

import asyncio
import logging
import os
import pandas as pd
from typing import Optional

from .industry_mapper import IndustryMapper
from .performance_calculator import PerformanceCalculator
from .etf_data_fetcher import ETFDataFetcher, ETFDataError

logger = logging.getLogger(__name__)


class IndustryBriefError(Exception):
    """Raised when industry brief operations fail."""
    pass


class IndustryBrief:
    """Generate industry performance briefs using real ETF data.

    Uses ETFDataFetcher with PersistentETFStore so that after the initial
    load, all 50 ETF reads come from Firestore with zero API calls.
    """

    def __init__(self):
        """Initialize industry brief generator.

        Attempts to connect PersistentETFStore (Firestore). If GCP is
        unavailable, falls back gracefully to API sources only.
        """
        self._mapper = IndustryMapper()
        self._calculator = PerformanceCalculator()

        # Layer 1: Try to connect Firestore persistent store
        persistent_store = None
        try:
            from .persistent_store import PersistentETFStore
            persistent_store = PersistentETFStore()
            logger.info("PersistentETFStore connected — reads will use Firestore first")
        except Exception as e:
            logger.warning(
                "PersistentETFStore unavailable, using API sources only: %s", e
            )

        # Wire ETFDataFetcher with all layers
        self._fetcher = ETFDataFetcher(
            api_key=os.getenv("ALPHA_VANTAGE_KEY", ""),
            finnhub_key=os.getenv("FINNHUB_API_KEY", ""),
            persistent_store=persistent_store,
        )

    def fetch_etf_data(self, etf_ticker: str, days: int = 2520) -> Optional[pd.DataFrame]:
        """Fetch historical ETF data via the multi-source resolution chain.

        Resolution order:
        1. Firestore persistent store (if connected)
        2. Finnhub API
        3. Alpha Vantage API
        4. yfinance

        Args:
            etf_ticker: ETF ticker symbol (e.g., 'IGV').
            days: Unused — ETFDataFetcher fetches full available history.

        Returns:
            DataFrame with 'adjusted_close' and 'volume' columns, sorted
            newest-first. None if all sources fail.
        """
        try:
            # ETFDataFetcher.fetch_daily_adjusted is async; run synchronously here
            try:
                loop = asyncio.get_running_loop()
                # Already inside an event loop — run in a thread to avoid nesting
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                    future = pool.submit(
                        asyncio.run,
                        self._fetcher.fetch_daily_adjusted(etf_ticker),
                    )
                    df = future.result()
            except RuntimeError:
                # No running loop — safe to call asyncio.run directly
                df = asyncio.run(self._fetcher.fetch_daily_adjusted(etf_ticker))

            if df is None or df.empty:
                logger.warning("No data found for %s", etf_ticker)
                return None

            logger.info("Fetched %d rows for %s", len(df), etf_ticker)
            return df

        except ETFDataError as e:
            logger.error("Failed to fetch data for %s: %s", etf_ticker, e)
            return None
        except Exception as e:
            logger.error("Failed to fetch data for %s: %s", etf_ticker, e)
            return None

    def calculate_all_industry_performance(self) -> list[dict]:
        """Calculate performance for all 50 industries.

        Returns:
            List of performance dicts with returns for all horizons.

        Raises:
            IndustryBriefError: If calculation fails.
        """
        industries = self._mapper.get_all_industries()
        performances = []
        failed = []

        for industry in industries:
            etf = self._mapper.get_etf(industry)
            if not etf:
                logger.warning("No ETF mapping for %s", industry)
                failed.append(industry)
                continue

            df = self.fetch_etf_data(etf)
            if df is None or df.empty:
                logger.warning("No data available for %s (%s)", industry, etf)
                failed.append(industry)
                continue

            try:
                perf = self._calculator.calculate_industry_performance(
                    industry=industry,
                    etf=etf,
                    df=df,
                )
                performances.append(perf)
                logger.info("Calculated performance for %s", industry)
            except Exception as e:
                logger.error("Failed to calculate performance for %s: %s", industry, e)
                failed.append(industry)

        logger.info(
            "Performance calculation complete: %d succeeded, %d failed",
            len(performances), len(failed),
        )

        return performances

    def get_top_performers(
        self,
        performances: list[dict],
        horizon: str = "1m",
        top_n: int = 10,
    ) -> list[dict]:
        """Get top N industries for a specific horizon.

        Args:
            performances: List of performance dicts.
            horizon: Time horizon (e.g., '1w', '2w', '1m').
            top_n: Number of top performers to return.

        Returns:
            List of top performer dicts with rankings.
        """
        top = self._calculator.get_best_performers(performances, horizon, top_n)
        for i, perf in enumerate(top, 1):
            perf['rank'] = i
        return top

    def get_worst_performers(
        self,
        performances: list[dict],
        horizon: str = "1m",
        bottom_n: int = 10,
    ) -> list[dict]:
        """Get worst N industries for a specific horizon.

        Args:
            performances: List of performance dicts.
            horizon: Time horizon.
            bottom_n: Number of worst performers to return.

        Returns:
            List of worst performer dicts with rankings.
        """
        worst = self._calculator.get_worst_performers(performances, horizon, bottom_n)
        for i, perf in enumerate(worst, 1):
            perf['rank'] = i
        return worst

    def generate_brief(self, horizon: str = "1m", top_n: int = 10) -> dict:
        """Generate complete industry brief.

        Args:
            horizon: Time horizon for analysis.
            top_n: Number of top/worst performers to include.

        Returns:
            Brief dict with top/worst performers and metrics.
        """
        logger.info("Generating industry brief for horizon=%s", horizon)

        performances = self.calculate_all_industry_performance()

        if not performances:
            raise IndustryBriefError("Failed to calculate any industry performance data")

        top_performers = self.get_top_performers(performances, horizon, top_n)
        worst_performers = self.get_worst_performers(performances, horizon, top_n)
        avg_return = self._calculator.calculate_average_return(performances, horizon)

        valid_returns = [
            p["returns"][horizon]
            for p in performances
            if p.get("returns", {}).get(horizon) is not None
        ]

        positive_count = sum(1 for r in valid_returns if r > 0.5)
        negative_count = sum(1 for r in valid_returns if r < -0.5)
        neutral_count = len(valid_returns) - positive_count - negative_count

        return {
            "horizon": horizon,
            "top_performers": top_performers,
            "worst_performers": worst_performers,
            "metrics": {
                "total_industries": len(self._mapper.get_all_industries()),
                "industries_with_data": len(performances),
                "average_return": avg_return,
                "positive_count": positive_count,
                "negative_count": negative_count,
                "neutral_count": neutral_count,
            },
        }
