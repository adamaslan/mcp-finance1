"""API Service layer for industry performance tracking.

Orchestrates all components and provides business logic for REST endpoints.
"""

import logging
from typing import Optional
import asyncio

from .industry_mapper import IndustryMapper
from .etf_data_fetcher import ETFDataFetcher, ETFDataError
from .performance_calculator import PerformanceCalculator
from .firebase_cache import FirebaseCache, FirebaseCacheError
from .summary_generator import SummaryGenerator
from .persistent_store import PersistentETFStore, PersistentStoreError

logger = logging.getLogger(__name__)


class IndustryServiceError(Exception):
    """Raised when industry service operations fail."""
    pass


class IndustryService:
    """High-level service for industry performance tracking."""

    def __init__(
        self,
        alpha_vantage_key: str,
        gcp_project_id: Optional[str] = None,
        finnhub_key: str = "",
    ):
        """Initialize industry service.

        Args:
            alpha_vantage_key: Alpha Vantage API key.
            gcp_project_id: GCP project ID for Firebase (optional).
            finnhub_key: Optional Finnhub API key for primary data source.

        Raises:
            IndustryServiceError: If initialization fails.
        """
        try:
            self._mapper = IndustryMapper()

            # Initialize persistent store for zero-API-cost reads
            try:
                self._persistent = PersistentETFStore(project_id=gcp_project_id)
                logger.info("Persistent ETF store initialized")
            except PersistentStoreError as e:
                logger.warning("Persistent store unavailable (will use API): %s", e)
                self._persistent = None

            self._fetcher = ETFDataFetcher(
                api_key=alpha_vantage_key,
                finnhub_key=finnhub_key,
                persistent_store=self._persistent,
            )
            self._calculator = PerformanceCalculator()
            self._cache = FirebaseCache(project_id=gcp_project_id)
            self._summary = SummaryGenerator()

            logger.info("IndustryService initialized (finnhub=%s, persistent=%s)",
                        bool(finnhub_key), self._persistent is not None)

        except Exception as e:
            raise IndustryServiceError(f"Failed to initialize service: {e}") from e

    async def get_all_industries(self) -> list[dict[str, str]]:
        """Get list of all 50 industries and their ETFs.

        Returns:
            List of {"industry": str, "etf": str} dicts.
        """
        return self._mapper.get_industry_etf_pairs()

    async def get_industry_performance(
        self,
        industry: str,
        use_cache: bool = True,
    ) -> dict:
        """Get performance data for a single industry.

        Args:
            industry: Industry name.
            use_cache: If True, return cached data if available.

        Returns:
            Performance dict with returns for all horizons.

        Raises:
            IndustryServiceError: If industry not found or data fetch fails.
        """
        # Validate industry
        etf = self._mapper.get_etf(industry)
        if not etf:
            raise IndustryServiceError(f"Industry not found: {industry}")

        # Check cache first
        if use_cache:
            cached = self._cache.read(industry)
            if cached:
                logger.info("Returning cached data for %s", industry)
                return cached

        # Fetch fresh data
        logger.info("Fetching fresh data for %s (%s)", industry, etf)
        return await self._compute_industry_performance(industry, etf)

    async def refresh_industry(self, industry: str) -> dict:
        """Recompute and update cache for a single industry.

        Args:
            industry: Industry name.

        Returns:
            Updated performance dict.

        Raises:
            IndustryServiceError: If refresh fails.
        """
        etf = self._mapper.get_etf(industry)
        if not etf:
            raise IndustryServiceError(f"Industry not found: {industry}")

        logger.info("Refreshing %s (%s)", industry, etf)

        # Compute fresh performance
        performance = await self._compute_industry_performance(industry, etf)

        # Update cache
        try:
            self._cache.write(industry, performance)
            logger.info("Cache updated for %s", industry)
        except FirebaseCacheError as e:
            logger.error("Failed to update cache for %s: %s", industry, e)
            # Don't fail the request - return the data anyway

        return performance

    async def refresh_all_industries(
        self,
        batch_size: int = 10,
    ) -> dict:
        """Recompute and update cache for all 50 industries.

        Uses batch Firestore reads to check which industries are stale,
        then only refreshes those that need updating.

        Args:
            batch_size: Number of concurrent fetches (max 10 to respect rate limits).

        Returns:
            Dict with success/failure counts and updated performances.

        Raises:
            IndustryServiceError: If refresh fails.
        """
        logger.info("Starting full refresh of all 50 industries")

        industries = self._mapper.get_all_industries()

        # Batch-read existing cache to identify stale entries
        try:
            cached_data = self._cache.read_batch(industries)
            stale = [
                ind for ind in industries
                if ind not in cached_data or self._cache.is_stale(ind, max_age_seconds=86400)
            ]
            logger.info(
                "Batch cache check: %d cached, %d stale, %d need refresh",
                len(cached_data), len(stale), len(stale),
            )
        except Exception as e:
            logger.warning("Batch cache check failed, refreshing all: %s", e)
            stale = industries

        semaphore = asyncio.Semaphore(min(batch_size, 10))

        successes = []
        failures = []

        async def refresh_one(industry: str) -> None:
            async with semaphore:
                try:
                    perf = await self.refresh_industry(industry)
                    successes.append(perf)
                except Exception as e:
                    logger.error("Failed to refresh %s: %s", industry, e)
                    failures.append({"industry": industry, "error": str(e)})

        # Only refresh stale entries
        await asyncio.gather(*[refresh_one(ind) for ind in stale])

        logger.info("Refresh complete: %d succeeded, %d failed", len(successes), len(failures))

        return {
            "success_count": len(successes),
            "failure_count": len(failures),
            "skipped_fresh": len(industries) - len(stale),
            "performances": successes,
            "failures": failures,
        }

    async def get_morning_summary(
        self,
        horizon: str = "1m",
        force_refresh: bool = False,
    ) -> dict:
        """Get morning summary with top/bottom performers and narrative.

        Args:
            horizon: Time horizon for analysis (default: 1 month).
            force_refresh: If True, refresh all data before generating summary.

        Returns:
            Morning summary dict.

        Raises:
            IndustryServiceError: If summary generation fails.
        """
        logger.info("Generating morning summary (horizon=%s, refresh=%s)", horizon, force_refresh)

        # Optionally refresh all data first
        if force_refresh:
            await self.refresh_all_industries()

        # Load all cached performances
        try:
            performances = self._cache.read_all()
        except FirebaseCacheError as e:
            raise IndustryServiceError(f"Failed to load cached data: {e}") from e

        if not performances:
            raise IndustryServiceError(
                "No cached data available. Run POST /refresh-all first."
            )

        # Generate summary
        summary = self._summary.generate_morning_summary(performances, horizon)

        logger.info("Morning summary generated with %d industries", len(performances))
        return summary

    async def _compute_industry_performance(
        self,
        industry: str,
        etf: str,
    ) -> dict:
        """Compute performance for a single industry.

        Args:
            industry: Industry name.
            etf: ETF ticker.

        Returns:
            Performance dict.

        Raises:
            IndustryServiceError: If computation fails.
        """
        try:
            # Fetch full historical data
            df = await self._fetcher.fetch_daily_adjusted(etf, outputsize="full")

            # Calculate multi-horizon returns
            performance = self._calculator.calculate_industry_performance(
                industry=industry,
                etf=etf,
                df=df,
            )

            return performance

        except ETFDataError as e:
            raise IndustryServiceError(
                f"Failed to fetch data for {industry} ({etf}): {e}"
            ) from e
        except Exception as e:
            raise IndustryServiceError(
                f"Failed to compute performance for {industry}: {e}"
            ) from e

    async def get_cache_status(self) -> dict:
        """Get cache status and staleness info.

        Returns:
            Dict with cache status metrics.
        """
        try:
            total_cached = self._cache.count_cached()
            total_industries = self._mapper.get_count()

            stale_count = 0
            for industry in self._mapper.get_all_industries():
                if self._cache.is_stale(industry, max_age_seconds=86400):
                    stale_count += 1

            return {
                "total_industries": total_industries,
                "cached_count": total_cached,
                "stale_count": stale_count,
                "coverage_percent": round((total_cached / total_industries) * 100, 1),
            }

        except Exception as e:
            logger.error("Failed to get cache status: %s", e)
            return {
                "total_industries": 50,
                "cached_count": 0,
                "stale_count": 0,
                "coverage_percent": 0.0,
                "error": str(e),
            }

    async def get_top_performers(
        self,
        horizon: str = "1m",
        top_n: int = 10,
    ) -> list[dict]:
        """Get top N performing industries for a horizon.

        Args:
            horizon: Time horizon.
            top_n: Number of top performers.

        Returns:
            List of top performer dicts.
        """
        performances = self._cache.read_all()
        return self._calculator.get_best_performers(performances, horizon, top_n)

    async def get_worst_performers(
        self,
        horizon: str = "1m",
        bottom_n: int = 10,
    ) -> list[dict]:
        """Get bottom N performing industries for a horizon.

        Args:
            horizon: Time horizon.
            bottom_n: Number of worst performers.

        Returns:
            List of worst performer dicts.
        """
        performances = self._cache.read_all()
        return self._calculator.get_worst_performers(performances, horizon, bottom_n)

    async def get_persistent_status(self) -> dict:
        """Get persistent storage status for all ETFs.

        Returns:
            Dict with storage status and per-ETF metadata.
        """
        if self._persistent is None:
            return {"available": False, "error": "Persistent store not initialized"}

        try:
            all_etfs = self._mapper.get_all_etfs()
            stored_metadata = self._persistent.get_all_metadata()
            stored_symbols = {m["symbol"] for m in stored_metadata}

            return {
                "available": True,
                "total_etfs": len(all_etfs),
                "stored_count": len(stored_metadata),
                "missing_count": len(all_etfs) - len(stored_symbols),
                "missing_symbols": [e for e in all_etfs if e not in stored_symbols],
                "stored": stored_metadata,
            }
        except Exception as e:
            logger.error("Failed to get persistent status: %s", e)
            return {"available": True, "error": str(e)}

    async def daily_update_all(self) -> dict:
        """Run daily delta update for all ETFs with stored history.

        Appends only new trading days since last update. Uses yfinance
        (no quota) for delta fetches. Designed to be called by Cloud
        Scheduler or cron job once per trading day.

        Returns:
            Summary dict with update counts.
        """
        if self._persistent is None:
            raise IndustryServiceError("Persistent store not available")

        all_pairs = self._mapper.get_industry_etf_pairs()
        updated = 0
        skipped = 0
        errors = []

        for pair in all_pairs:
            etf = pair["etf"]
            industry = pair["industry"]
            try:
                # Load existing data (from persistent store, costs 0 API calls)
                df = await self._fetcher.fetch_daily_adjusted(etf)

                # Recompute performance and update cache
                performance = self._calculator.calculate_industry_performance(
                    industry=industry, etf=etf, df=df,
                )
                self._cache.write(industry, performance)
                updated += 1
            except Exception as e:
                logger.error("Daily update failed for %s (%s): %s", industry, etf, e)
                errors.append({"industry": industry, "etf": etf, "error": str(e)})
                skipped += 1

        logger.info("Daily update complete: %d updated, %d errors", updated, len(errors))

        return {
            "updated": updated,
            "skipped": skipped,
            "errors": errors,
        }
