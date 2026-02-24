#!/usr/bin/env python3
"""Fetch all 50 industries once and store full historical data.

This script intelligently fetches each ETF once (returning full history),
then stores it for all requested dates. Much more efficient than
fetching per day.

Usage:
    python scripts/fetch_and_store_all_industries.py

Environment Variables Required:
    - ALPHA_VANTAGE_KEY
    - GCP_PROJECT_ID
"""

import asyncio
import logging
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "cloud-run" / "src"))

from technical_analysis_mcp.industry_tracker.industry_mapper import IndustryMapper
from technical_analysis_mcp.industry_tracker.etf_data_fetcher import ETFDataFetcher
from technical_analysis_mcp.industry_tracker.performance_calculator import PerformanceCalculator
from technical_analysis_mcp.industry_tracker.firebase_cache import FirebaseCache

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s: %(message)s",
)
logger = logging.getLogger(__name__)


class OptimizedIndustryDataFetcher:
    """Fetch all industries once, store full history efficiently."""

    def __init__(self, alpha_vantage_key: str, gcp_project_id: str):
        """Initialize fetcher.

        Args:
            alpha_vantage_key: Alpha Vantage API key.
            gcp_project_id: GCP project ID.
        """
        self.fetcher = ETFDataFetcher(api_key=alpha_vantage_key, rate_limit_delay=12.0)
        self.mapper = IndustryMapper()
        self.calculator = PerformanceCalculator()
        self.cache = FirebaseCache(project_id=gcp_project_id)
        self.db = self.cache._db

    async def fetch_all_industries(self) -> dict[str, pd.DataFrame]:
        """Fetch full history for all 50 industries.

        Returns:
            Dict mapping industry name -> DataFrame with historical data.
        """
        logger.info("Fetching full historical data for all 50 industries")
        logger.info("This uses 50 API calls (1 per industry), spread over 2 days with free tier")

        all_data = {}
        failed = []

        for industry in self.mapper.get_all_industries():
            try:
                etf = self.mapper.get_etf(industry)
                if not etf:
                    logger.warning("No ETF mapping for %s", industry)
                    continue

                logger.info("Fetching %s (%s)", industry, etf)
                df = await self.fetcher.fetch_daily_adjusted(etf, outputsize="full")
                all_data[industry] = df
                logger.info("✓ %s: %d days of data", industry, len(df))

            except Exception as e:
                logger.error("✗ Failed to fetch %s: %s", industry, e)
                failed.append((industry, str(e)))

        logger.info("=" * 60)
        logger.info("Fetch Summary:")
        logger.info("  Successful: %d/50", len(all_data))
        logger.info("  Failed: %d/50", len(failed))

        if failed:
            logger.info("Failed industries:")
            for industry, error in failed[:5]:
                logger.info("  - %s: %s", industry, error)

        return all_data

    async def store_historical_snapshots(
        self,
        all_data: dict[str, pd.DataFrame],
        num_days: int = 30,
    ) -> dict:
        """Store historical snapshots for the past N days.

        Args:
            all_data: Dict of industry -> DataFrame with historical data.
            num_days: Number of days to store (default: 30).

        Returns:
            Summary stats.
        """
        logger.info("Storing %d days of snapshots for %d industries", num_days, len(all_data))

        end_date = datetime.utcnow().date()
        start_date = end_date - timedelta(days=num_days - 1)

        total_snapshots = 0
        total_dates = 0

        # For each date in range
        current_date = start_date
        while current_date <= end_date:
            logger.info("Processing date: %s", current_date.isoformat())

            collection_name = f"industry_history/{current_date.isoformat()}"
            batch = self.db.batch()
            batch_size = 0

            # For each industry, extract data for this date
            for industry, df in all_data.items():
                try:
                    # Filter data for this date
                    date_str = current_date.isoformat()
                    if date_str not in df.index:
                        # Date not in data (weekend, holiday, or future)
                        continue

                    row = df.loc[date_str]

                    # Calculate multi-horizon returns
                    returns = self.calculator.calculate_returns(df, current_date)

                    etf = self.mapper.get_etf(industry)

                    performance = {
                        "industry": industry,
                        "etf": etf,
                        "date": date_str,
                        "price": float(row["adjusted_close"]),
                        "volume": int(row["volume"]),
                        "returns": returns,
                        "snapshot_timestamp": datetime.utcnow().isoformat(),
                    }

                    # Store in Firestore
                    doc_ref = self.db.collection(collection_name).document(industry)
                    batch.set(doc_ref, performance)
                    batch_size += 1
                    total_snapshots += 1

                except Exception as e:
                    logger.debug("Error processing %s for %s: %s", industry, current_date, e)
                    continue

            # Commit batch
            if batch_size > 0:
                batch.commit()
                logger.info("Stored %d industries for %s", batch_size, current_date.isoformat())
                total_dates += 1

            current_date += timedelta(days=1)

        logger.info("=" * 60)
        logger.info("Storage Summary:")
        logger.info("  Dates processed: %d", total_dates)
        logger.info("  Total snapshots: %d", total_snapshots)

        return {
            "dates_processed": total_dates,
            "total_snapshots": total_snapshots,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
        }


async def main():
    """Main execution."""
    av_key = os.getenv("ALPHA_VANTAGE_KEY")
    gcp_project = os.getenv("GCP_PROJECT_ID")

    if not av_key:
        logger.error("ALPHA_VANTAGE_KEY not set")
        sys.exit(1)

    if not gcp_project:
        logger.error("GCP_PROJECT_ID not set")
        sys.exit(1)

    fetcher = OptimizedIndustryDataFetcher(av_key, gcp_project)

    # Fetch all data (50 API calls)
    logger.info("\n" + "=" * 60)
    logger.info("PHASE 1: FETCH ALL INDUSTRIES")
    logger.info("=" * 60)
    all_data = await fetcher.fetch_all_industries()

    if not all_data:
        logger.error("No data fetched. Check API key and network connectivity.")
        sys.exit(1)

    # Store historical snapshots
    logger.info("\n" + "=" * 60)
    logger.info("PHASE 2: STORE HISTORICAL SNAPSHOTS")
    logger.info("=" * 60)
    result = await fetcher.store_historical_snapshots(all_data, num_days=30)

    # Print final summary
    logger.info("\n" + "=" * 60)
    logger.info("FINAL SUMMARY")
    logger.info("=" * 60)
    logger.info("API calls made: ~50 (1 per industry)")
    logger.info("Timeline with free tier: ~2 days (25 calls/day)")
    logger.info("Dates with data: %d", result["dates_processed"])
    logger.info("Total snapshots stored: %d", result["total_snapshots"])
    logger.info("Date range: %s to %s", result["start_date"], result["end_date"])
    logger.info("\n✓ Next: Run visualization script")
    logger.info("  python scripts/visualize_industry_data.py --days 30")


if __name__ == "__main__":
    asyncio.run(main())
