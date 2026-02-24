#!/usr/bin/env python3
"""Build 1 month of historical industry performance data in Firestore.

This script fetches real daily snapshots of all 50 industries over 30 days,
storing each day's performance snapshot in a timestamped collection.

Usage:
    python scripts/build_historical_industry_data.py

Firestore Structure:
    industry_history/
        2024-11-22/                    # Date collection
            Software                   # Industry document
            Biotechnology
            ...
        2024-11-23/
            Software
            ...

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

# Add src to path (mcp-finance1/cloud-run/src for technical_analysis_mcp modules)
sys.path.insert(0, str(Path(__file__).parent.parent / "cloud-run" / "src"))

from technical_analysis_mcp.industry_tracker.api_service import IndustryService, IndustryServiceError
from technical_analysis_mcp.industry_tracker.firebase_cache import FirebaseCache

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s: %(message)s",
)
logger = logging.getLogger(__name__)


class HistoricalDataBuilder:
    """Build historical industry performance snapshots."""

    def __init__(
        self,
        alpha_vantage_key: str,
        gcp_project_id: str,
        days: int = 30,
    ):
        """Initialize historical data builder.

        Args:
            alpha_vantage_key: Alpha Vantage API key.
            gcp_project_id: GCP project ID.
            days: Number of historical days to build (default: 30).
        """
        self.service = IndustryService(
            alpha_vantage_key=alpha_vantage_key,
            gcp_project_id=gcp_project_id,
        )
        self.cache = FirebaseCache(project_id=gcp_project_id)
        self.days = days

        # Custom Firestore client for historical collections
        self.db = self.cache._db

    async def build_historical_snapshots(self) -> dict:
        """Build daily snapshots for the past N days.

        Returns:
            Dict with summary stats.
        """
        logger.info("Building %d days of historical industry data", self.days)

        end_date = datetime.utcnow().date()
        start_date = end_date - timedelta(days=self.days - 1)

        total_days = 0
        total_industries = 0
        errors = []

        # Process each day
        current_date = start_date
        while current_date <= end_date:
            try:
                logger.info("Processing date: %s", current_date.isoformat())

                # Fetch fresh data for all industries
                result = await self.service.refresh_all_industries(batch_size=5)

                if result["success_count"] == 0:
                    logger.error("Failed to fetch any industries for %s", current_date)
                    errors.append({
                        "date": current_date.isoformat(),
                        "error": "No successful fetches",
                    })
                    current_date += timedelta(days=1)
                    continue

                # Store snapshot in dated collection
                snapshot_count = await self._store_daily_snapshot(
                    date=current_date,
                    performances=result["performances"],
                )

                total_days += 1
                total_industries += snapshot_count

                logger.info(
                    "Stored %d industries for %s (total: %d/%d days)",
                    snapshot_count,
                    current_date.isoformat(),
                    total_days,
                    self.days,
                )

                # Rate limiting: Wait 2 minutes between days to avoid hitting API limits
                if current_date < end_date:
                    logger.info("Waiting 2 minutes before next day...")
                    await asyncio.sleep(120)

            except Exception as e:
                logger.error("Error processing %s: %s", current_date, e)
                errors.append({
                    "date": current_date.isoformat(),
                    "error": str(e),
                })

            current_date += timedelta(days=1)

        logger.info(
            "Historical data build complete: %d days, %d total snapshots",
            total_days,
            total_industries,
        )

        return {
            "days_processed": total_days,
            "total_snapshots": total_industries,
            "errors": errors,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
        }

    async def _store_daily_snapshot(
        self,
        date: datetime.date,
        performances: list[dict],
    ) -> int:
        """Store a single day's industry snapshot.

        Args:
            date: Date of snapshot.
            performances: List of industry performance dicts.

        Returns:
            Number of industries stored.
        """
        collection_name = f"industry_history/{date.isoformat()}"
        count = 0

        batch = self.db.batch()

        for perf in performances:
            industry = perf.get("industry")
            if not industry:
                continue

            # Add snapshot timestamp
            perf["snapshot_date"] = date.isoformat()
            perf["snapshot_timestamp"] = datetime.utcnow().isoformat()

            # Store in dated sub-collection
            doc_ref = self.db.collection(collection_name).document(industry)
            batch.set(doc_ref, perf)
            count += 1

            # Also update main cache for current day
            if date == datetime.utcnow().date():
                cache_ref = self.db.collection("industry_cache").document(industry)
                batch.set(cache_ref, perf)

        # Commit batch
        batch.commit()

        return count

    async def get_historical_snapshot(
        self,
        date: datetime.date,
    ) -> list[dict]:
        """Retrieve all industries for a specific date.

        Args:
            date: Date to retrieve.

        Returns:
            List of industry performance dicts.
        """
        collection_name = f"industry_history/{date.isoformat()}"
        docs = self.db.collection(collection_name).stream()

        return [doc.to_dict() for doc in docs]

    async def get_date_range(
        self,
        start_date: datetime.date,
        end_date: datetime.date,
    ) -> dict[str, list[dict]]:
        """Retrieve snapshots for a date range.

        Args:
            start_date: Start date (inclusive).
            end_date: End date (inclusive).

        Returns:
            Dict mapping date ISO string → list of industry dicts.
        """
        results = {}

        current_date = start_date
        while current_date <= end_date:
            snapshot = await self.get_historical_snapshot(current_date)
            if snapshot:
                results[current_date.isoformat()] = snapshot

            current_date += timedelta(days=1)

        return results


async def main():
    """Main execution."""
    # Load environment
    av_key = os.getenv("ALPHA_VANTAGE_KEY")
    gcp_project = os.getenv("GCP_PROJECT_ID")

    if not av_key:
        logger.error("ALPHA_VANTAGE_KEY not set")
        sys.exit(1)

    if not gcp_project:
        logger.error("GCP_PROJECT_ID not set")
        sys.exit(1)

    # Build historical data
    builder = HistoricalDataBuilder(
        alpha_vantage_key=av_key,
        gcp_project_id=gcp_project,
        days=30,  # 1 month
    )

    result = await builder.build_historical_snapshots()

    # Print summary
    logger.info("=" * 60)
    logger.info("HISTORICAL DATA BUILD SUMMARY")
    logger.info("=" * 60)
    logger.info("Date Range: %s to %s", result["start_date"], result["end_date"])
    logger.info("Days Processed: %d", result["days_processed"])
    logger.info("Total Snapshots: %d", result["total_snapshots"])
    logger.info("Errors: %d", len(result["errors"]))

    if result["errors"]:
        logger.warning("Failed dates:")
        for err in result["errors"]:
            logger.warning("  %s: %s", err["date"], err["error"])

    logger.info("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
