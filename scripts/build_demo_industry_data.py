#!/usr/bin/env python3
"""Build demo 3 months of synthetic industry performance data in Firestore.

Creates realistic-looking historical data based on economic patterns
for testing and demonstration purposes.

Usage:
    python scripts/build_demo_industry_data.py

This generates:
- 90 days of historical snapshots
- All 50 industries with varied returns
- Realistic correlations between related industries
- Economic cycle patterns (risk-on/off regimes)
"""

import asyncio
import logging
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
import numpy as np

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from industry_tracker.industry_mapper import IndustryMapper
from industry_tracker.firebase_cache import FirebaseCache

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s: %(message)s",
)
logger = logging.getLogger(__name__)


class DemoDataBuilder:
    """Build synthetic industry performance data for demo/testing."""

    # Sector groupings for correlated behavior
    SECTOR_GROUPS = {
        "Technology": ["Software", "Semiconductors", "Cloud Computing", "Artificial Intelligence", "Internet", "Hardware", "Cybersecurity"],
        "Healthcare": ["Biotechnology", "Pharmaceuticals", "Healthcare Providers", "Medical Devices", "Managed Care", "Healthcare REIT"],
        "Financials": ["Banks", "Insurance", "Asset Management", "Fintech", "REITs", "Payments", "Regional Banks"],
        "Consumer": ["Retail", "E-Commerce", "Restaurants", "Apparel", "Automotive", "Luxury Goods", "Consumer Staples", "Consumer Discretionary"],
        "Energy": ["Oil & Gas", "Renewable Energy", "Mining", "Steel", "Chemicals"],
        "Industrials": ["Aerospace & Defense", "Transportation", "Construction", "Logistics", "Industrials"],
        "Real Estate": ["Real Estate", "Infrastructure", "Homebuilders", "Commercial Real Estate"],
        "Communications": ["Media", "Entertainment", "Social Media", "Telecommunications"],
        "Other": ["Utilities", "Agriculture", "Cannabis", "ESG"],
    }

    def __init__(self, gcp_project_id: str = "ttb-lang1", days: int = 90):
        """Initialize demo data builder.

        Args:
            gcp_project_id: GCP project ID.
            days: Number of days to generate (default: 90).
        """
        self.cache = FirebaseCache(project_id=gcp_project_id)
        self.mapper = IndustryMapper()
        self.days = days
        self.db = self.cache._db

    async def generate_synthetic_data(self) -> dict:
        """Generate synthetic 3-month industry performance data.

        Returns:
            Dict with summary stats.
        """
        logger.info("Generating %d days of synthetic industry data", self.days)

        end_date = datetime.utcnow().date()
        start_date = end_date - timedelta(days=self.days - 1)

        # Initialize random seed for reproducibility
        np.random.seed(42)

        # Generate base sector returns (random walk)
        sector_returns = self._generate_sector_returns()

        total_days = 0
        total_industries = 0

        # Process each day
        current_date = start_date
        while current_date <= end_date:
            try:
                logger.info("Generating data for: %s", current_date.isoformat())

                # Generate all industry data for this day
                day_performances = self._generate_day_performances(
                    date=current_date,
                    sector_returns=sector_returns,
                )

                # Store in Firestore
                snapshot_count = await self._store_daily_snapshot(
                    date=current_date,
                    performances=day_performances,
                )

                total_days += 1
                total_industries += snapshot_count

                logger.info(
                    "Generated %d industries for %s",
                    snapshot_count,
                    current_date.isoformat(),
                )

            except Exception as e:
                logger.error("Error generating data for %s: %s", current_date, e)

            current_date += timedelta(days=1)

        logger.info(
            "Synthetic data generation complete: %d days, %d total snapshots",
            total_days,
            total_industries,
        )

        return {
            "days_generated": total_days,
            "total_snapshots": total_industries,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "note": "This is synthetic demo data for testing purposes",
        }

    def _generate_sector_returns(self) -> dict:
        """Generate random walk sector returns over time.

        Returns:
            Dict mapping sector → array of daily returns.
        """
        # Base returns for each sector (random walk)
        sector_returns = {}

        for sector in self.SECTOR_GROUPS.keys():
            # Random walk: cumulative sum of random increments
            daily_shocks = np.random.normal(0, 0.5, self.days)  # 0.5% std dev per day
            cumulative = np.cumsum(daily_shocks)
            sector_returns[sector] = cumulative

        # Add economic cycle: cyclical vs defensive spread
        cyclical_sectors = ["Technology", "Consumer", "Industrials"]
        defensive_sectors = ["Utilities", "Healthcare", "Financials"]

        # Create regime shifts: risk-on, neutral, risk-off
        regime = np.random.choice([1, 0, -1], self.days, p=[0.4, 0.4, 0.2])  # 40% risk-on, 40% neutral, 20% risk-off

        for sector in cyclical_sectors:
            sector_returns[sector] += regime * 2  # Cyclicals amplify regime signal

        for sector in defensive_sectors:
            sector_returns[sector] -= regime * 1  # Defensives dampen it

        return sector_returns

    def _generate_day_performances(
        self,
        date: datetime.date,
        sector_returns: dict,
    ) -> list[dict]:
        """Generate performance data for all industries on a given day.

        Args:
            date: Date for which to generate data.
            sector_returns: Dict of sector cumulative returns.

        Returns:
            List of performance dicts for all 50 industries.
        """
        day_index = (date - (datetime.utcnow().date() - timedelta(days=self.days - 1))).days
        day_index = max(0, min(day_index, self.days - 1))

        performances = []

        # Generate data for each industry
        for industry in self.mapper.get_all_industries():
            etf = self.mapper.get_etf(industry)
            if not etf:
                continue

            # Find sector for this industry
            sector = None
            for sect, industries in self.SECTOR_GROUPS.items():
                if industry in industries:
                    sector = sect
                    break

            # Base return from sector + idiosyncratic noise
            base_return = sector_returns.get(sector, np.array([0]))[day_index] if sector else 0
            idiosyncratic = np.random.normal(0, 1.0)  # 1% std dev idiosyncratic
            return_1m = base_return + idiosyncratic

            # Create returns at different horizons (autocorrelated)
            returns = {
                "2w": return_1m * 0.5 + np.random.normal(0, 0.3),
                "1m": return_1m,
                "2m": return_1m * 1.2 + np.random.normal(0, 0.5),
                "3m": return_1m * 1.5 + np.random.normal(0, 0.7),
                "6m": return_1m * 2.0 + np.random.normal(0, 1.0),
                "52w": return_1m * 4.0 + np.random.normal(0, 2.0),
                "2y": return_1m * 6.0 + np.random.normal(0, 3.0),
                "3y": return_1m * 8.0 + np.random.normal(0, 4.0),
                "5y": return_1m * 12.0 + np.random.normal(0, 6.0),
                "10y": return_1m * 20.0 + np.random.normal(0, 10.0),
            }

            # Round to 2 decimals
            returns = {k: round(v, 2) for k, v in returns.items()}

            performance = {
                "industry": industry,
                "etf": etf,
                "updated": datetime.utcnow().isoformat(),
                "snapshot_date": date.isoformat(),
                "snapshot_timestamp": datetime.utcnow().isoformat(),
                "returns": returns,
            }

            performances.append(performance)

        return performances

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

            # Store in dated sub-collection
            doc_ref = self.db.collection(collection_name).document(industry)
            batch.set(doc_ref, perf)
            count += 1

        # Commit batch
        batch.commit()

        return count


async def main():
    """Main execution."""
    # Load environment
    gcp_project = os.getenv("GCP_PROJECT_ID", "ttb-lang1")

    logger.info("Using GCP Project: %s", gcp_project)

    # Build synthetic data
    builder = DemoDataBuilder(gcp_project_id=gcp_project, days=90)
    result = await builder.generate_synthetic_data()

    # Print summary
    logger.info("=" * 60)
    logger.info("SYNTHETIC DATA GENERATION SUMMARY")
    logger.info("=" * 60)
    logger.info("Date Range: %s to %s", result["start_date"], result["end_date"])
    logger.info("Days Generated: %d", result["days_generated"])
    logger.info("Total Snapshots: %d", result["total_snapshots"])
    logger.info("Note: %s", result["note"])
    logger.info("=" * 60)
    logger.info("")
    logger.info("Next: Run visualization script")
    logger.info("  python scripts/visualize_industry_data.py --days 90")


if __name__ == "__main__":
    asyncio.run(main())
