"""Industry Brief Generator - Main module for industry performance analysis.

Fetches ETF data and generates industry performance summaries for multiple time horizons.
"""

import logging
import pandas as pd
from typing import Optional

from .industry_mapper import IndustryMapper
from .performance_calculator import PerformanceCalculator

logger = logging.getLogger(__name__)


class IndustryBriefError(Exception):
    """Raised when industry brief operations fail."""
    pass


class IndustryBrief:
    """Generate industry performance briefs using real ETF data."""

    def __init__(self):
        """Initialize industry brief generator."""
        self._mapper = IndustryMapper()
        self._calculator = PerformanceCalculator()

    def fetch_etf_data(self, etf_ticker: str, days: int = 2520) -> Optional[pd.DataFrame]:
        """Fetch historical ETF data using yfinance.

        Args:
            etf_ticker: ETF ticker symbol (e.g., 'IGV').
            days: Number of trading days to fetch (default: 2520 = ~10 years).

        Returns:
            DataFrame with 'adjusted_close' column, indexed by date (newest first).
            Returns None if fetch fails.
        """
        try:
            import yfinance as yf
        except ImportError:
            raise IndustryBriefError(
                "yfinance not installed. "
                "Install with: mamba install -c conda-forge yfinance"
            )

        try:
            # Fetch data with period param for convenience
            ticker = yf.Ticker(etf_ticker)
            hist = ticker.history(period="10y")

            if hist.empty:
                logger.warning("No data found for %s", etf_ticker)
                return None

            # Prepare DataFrame: reset index, rename column, sort descending
            df = hist.reset_index()
            df.columns = df.columns.str.lower()

            # Rename 'close' to 'adjusted_close' if needed
            if 'close' in df.columns:
                df['adjusted_close'] = df['close']

            # Sort by date descending (newest first)
            df = df.sort_values('date', ascending=False).reset_index(drop=True)

            logger.info("Fetched %d rows for %s", len(df), etf_ticker)
            return df[['date', 'adjusted_close']].copy()

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

            # Fetch ETF data
            df = self.fetch_etf_data(etf)
            if df is None or df.empty:
                logger.warning("No data available for %s (%s)", industry, etf)
                failed.append(industry)
                continue

            # Calculate performance
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
            len(performances), len(failed)
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

        # Add ranking
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

        # Add ranking (1 is worst)
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

        # Calculate all performances
        performances = self.calculate_all_industry_performance()

        if not performances:
            raise IndustryBriefError("Failed to calculate any industry performance data")

        # Get top and worst
        top_performers = self.get_top_performers(performances, horizon, top_n)
        worst_performers = self.get_worst_performers(performances, horizon, top_n)

        # Calculate average return
        avg_return = self._calculator.calculate_average_return(performances, horizon)

        # Count positive/negative
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
