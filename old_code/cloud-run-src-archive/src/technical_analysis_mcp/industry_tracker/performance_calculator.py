"""Performance calculator for multi-horizon returns analysis.

Computes returns across 10 time horizons using Pandas for efficient
vectorized operations.
"""

import logging
from typing import Optional
import pandas as pd
from datetime import datetime

logger = logging.getLogger(__name__)


class PerformanceCalculator:
    """Calculate multi-horizon performance metrics for ETFs."""

    # Time horizons in trading days
    HORIZONS = {
        "2w": 10,      # 2 weeks
        "1m": 21,      # 1 month
        "2m": 42,      # 2 months
        "3m": 63,      # 3 months
        "6m": 126,     # 6 months
        "52w": 252,    # 52 weeks (1 year)
        "2y": 504,     # 2 years
        "3y": 756,     # 3 years
        "5y": 1260,    # 5 years
        "10y": 2520,   # 10 years
    }

    @classmethod
    def calculate_returns(
        cls,
        df: pd.DataFrame,
        latest_price: Optional[float] = None,
    ) -> dict[str, Optional[float]]:
        """Calculate returns across all time horizons.

        Args:
            df: DataFrame with 'adjusted_close' column, indexed by date (newest first).
            latest_price: Optional override for latest price (default: use df.iloc[0]).

        Returns:
            Dict mapping horizon → return percentage (or None if insufficient data).

        Example:
            {
                "2w": 2.5,    # +2.5% over 2 weeks
                "1m": 5.2,    # +5.2% over 1 month
                "3m": -1.3,   # -1.3% over 3 months
                "10y": None,  # Not enough data
            }
        """
        if df.empty:
            logger.warning("Empty DataFrame - returning all None")
            return {horizon: None for horizon in cls.HORIZONS.keys()}

        # Get latest price
        if latest_price is None:
            latest_price = float(df.iloc[0]["adjusted_close"])

        returns = {}

        for horizon_key, trading_days in cls.HORIZONS.items():
            if trading_days >= len(df):
                # Not enough historical data for this horizon
                returns[horizon_key] = None
                logger.debug("Insufficient data for %s (%d days, need %d)",
                            horizon_key, len(df), trading_days)
            else:
                # Get price N trading days ago
                past_price = float(df.iloc[trading_days]["adjusted_close"])

                if past_price == 0:
                    returns[horizon_key] = None
                    logger.warning("Zero price found for %s, returning None", horizon_key)
                else:
                    # Calculate percentage return
                    pct_return = ((latest_price - past_price) / past_price) * 100
                    returns[horizon_key] = round(pct_return, 2)

        return returns

    @classmethod
    def calculate_industry_performance(
        cls,
        industry: str,
        etf: str,
        df: pd.DataFrame,
    ) -> dict:
        """Calculate full performance object for an industry.

        Args:
            industry: Industry name.
            etf: ETF ticker.
            df: Historical price DataFrame.

        Returns:
            Performance dict ready for Firebase cache:
            {
                "industry": str,
                "etf": str,
                "updated": ISO timestamp,
                "returns": {
                    "2w": float | null,
                    "1m": float | null,
                    ...
                }
            }
        """
        returns = cls.calculate_returns(df)

        return {
            "industry": industry,
            "etf": etf,
            "updated": datetime.utcnow().isoformat(),
            "returns": returns,
        }

    @classmethod
    def get_best_performers(
        cls,
        performances: list[dict],
        horizon: str = "1m",
        top_n: int = 5,
    ) -> list[dict]:
        """Get top N best-performing industries for a horizon.

        Args:
            performances: List of performance dicts from calculate_industry_performance().
            horizon: Time horizon key (e.g., '1m', '3m').
            top_n: Number of top performers to return.

        Returns:
            List of top N performance dicts, sorted descending by return.
        """
        if horizon not in cls.HORIZONS:
            logger.warning("Invalid horizon %s, using '1m'", horizon)
            horizon = "1m"

        # Filter out industries with no data for this horizon
        valid = [
            p for p in performances
            if p.get("returns", {}).get(horizon) is not None
        ]

        # Sort descending by return
        sorted_perfs = sorted(
            valid,
            key=lambda p: p["returns"][horizon],
            reverse=True,
        )

        return sorted_perfs[:top_n]

    @classmethod
    def get_worst_performers(
        cls,
        performances: list[dict],
        horizon: str = "1m",
        bottom_n: int = 5,
    ) -> list[dict]:
        """Get bottom N worst-performing industries for a horizon.

        Args:
            performances: List of performance dicts.
            horizon: Time horizon key.
            bottom_n: Number of worst performers to return.

        Returns:
            List of bottom N performance dicts, sorted ascending by return.
        """
        if horizon not in cls.HORIZONS:
            logger.warning("Invalid horizon %s, using '1m'", horizon)
            horizon = "1m"

        # Filter valid data
        valid = [
            p for p in performances
            if p.get("returns", {}).get(horizon) is not None
        ]

        # Sort ascending (worst first)
        sorted_perfs = sorted(
            valid,
            key=lambda p: p["returns"][horizon],
        )

        return sorted_perfs[:bottom_n]

    @classmethod
    def find_52week_extremes(
        cls,
        performances: list[dict],
    ) -> dict[str, list[dict]]:
        """Find industries at 52-week highs or lows.

        An industry is at a 52-week high if its 52w return > all shorter horizons.
        An industry is at a 52-week low if its 52w return < all shorter horizons.

        Args:
            performances: List of performance dicts.

        Returns:
            Dict with 'highs' and 'lows' lists of industries.
        """
        highs = []
        lows = []

        shorter_horizons = ["2w", "1m", "2m", "3m", "6m"]

        for perf in performances:
            returns = perf.get("returns", {})

            # Need 52w data
            week_52_return = returns.get("52w")
            if week_52_return is None:
                continue

            # Get all shorter horizon returns
            shorter_returns = [
                returns.get(h) for h in shorter_horizons
                if returns.get(h) is not None
            ]

            if not shorter_returns:
                continue

            # Check if 52w is max (high) or min (low)
            max_shorter = max(shorter_returns)
            min_shorter = min(shorter_returns)

            if week_52_return > max_shorter:
                highs.append(perf)
            elif week_52_return < min_shorter:
                lows.append(perf)

        return {
            "highs": highs,
            "lows": lows,
        }

    @classmethod
    def calculate_average_return(
        cls,
        performances: list[dict],
        horizon: str = "1m",
    ) -> Optional[float]:
        """Calculate average return across all industries for a horizon.

        Args:
            performances: List of performance dicts.
            horizon: Time horizon key.

        Returns:
            Average return percentage or None if no valid data.
        """
        valid_returns = [
            p["returns"][horizon]
            for p in performances
            if p.get("returns", {}).get(horizon) is not None
        ]

        if not valid_returns:
            return None

        return round(sum(valid_returns) / len(valid_returns), 2)

    @classmethod
    def get_horizon_days(cls, horizon: str) -> Optional[int]:
        """Get trading days for a horizon key.

        Args:
            horizon: Horizon key (e.g., '1m', '3m').

        Returns:
            Number of trading days or None if invalid horizon.
        """
        return cls.HORIZONS.get(horizon)

    @classmethod
    def get_all_horizons(cls) -> list[str]:
        """Get list of all horizon keys.

        Returns:
            List of horizon keys in order.
        """
        return list(cls.HORIZONS.keys())
