"""
Fibonacci Analysis Context
===========================
Context object containing all data needed for signal generation.
Avoids passing many parameters and enables caching.
"""

from typing import Optional, Dict, Callable
import pandas as pd

from ..core.registry import FibonacciLevelRegistry
from ..core.models import FibonacciLevel
from .swing_detector import SwingPointDetector
from .tolerance import AdaptiveTolerance


class FibonacciContext:
    """
    Context object containing all data needed for signal generation.
    Avoids passing many parameters and enables caching.
    """

    def __init__(
        self,
        df: pd.DataFrame,
        interval: str,
        current: pd.Series,
        prev: pd.Series,
        safe_float_fn: Callable
    ):
        """
        Initialize Fibonacci analysis context.

        Args:
            df: DataFrame with OHLCV price data
            interval: Timeframe interval (e.g., '1d', '1h')
            current: Current bar data
            prev: Previous bar data
            safe_float_fn: Function to safely convert values to float
        """
        self.df = df
        self.interval = interval
        self.current = current
        self.prev = prev
        self._safe_float = safe_float_fn

        # Initialize helpers
        self.swing_detector = SwingPointDetector(df)
        self.tolerance_calc = AdaptiveTolerance(df)
        self.fib_registry = FibonacciLevelRegistry()

        # Cache commonly used values
        self._close: Optional[float] = None
        self._prev_close: Optional[float] = None
        self._fib_levels: Optional[Dict[str, FibonacciLevel]] = None
        self._swing_data: Dict[int, Dict] = {}

    @property
    def close(self) -> Optional[float]:
        """Current close price."""
        if self._close is None:
            self._close = self._safe_float(self.current.get('Close'))
        return self._close

    @property
    def prev_close(self) -> Optional[float]:
        """Previous close price."""
        if self._prev_close is None:
            self._prev_close = self._safe_float(self.prev.get('Close'))
        return self._prev_close

    def get_fib_levels(self, window: int = 50) -> Dict[str, FibonacciLevel]:
        """
        Get Fibonacci levels calculated for given window.

        Args:
            window: Lookback period for swing detection

        Returns:
            Dictionary of Fibonacci levels with calculated prices
        """
        if window in self._swing_data:
            return self._swing_data[window]['levels']

        high, low, high_idx, low_idx = self.swing_detector.detect_swings(window)
        swing_range = high - low

        if swing_range <= 0:
            return {}

        levels = self.fib_registry.get_all_levels()

        for level in levels.values():
            level.calculate_price(low, high)

        self._swing_data[window] = {
            'high': high,
            'low': low,
            'high_idx': high_idx,
            'low_idx': low_idx,
            'range': swing_range,
            'levels': levels
        }

        return levels

    def get_swing_data(self, window: int = 50) -> Dict:
        """
        Get full swing data for window.

        Args:
            window: Lookback period for swing detection

        Returns:
            Dictionary with swing high, low, indices, and range
        """
        if window not in self._swing_data:
            self.get_fib_levels(window)
        return self._swing_data.get(window, {})

    def get_tolerance(self, tolerance_type: str = 'standard') -> float:
        """
        Get adaptive tolerance.

        Args:
            tolerance_type: One of 'tight', 'standard', 'wide', 'very_wide'

        Returns:
            Adjusted tolerance value
        """
        return self.tolerance_calc.get_tolerance(tolerance_type)

    def price_at_level(
        self,
        price: float,
        level: FibonacciLevel,
        tolerance: Optional[float] = None
    ) -> bool:
        """
        Check if price is at Fibonacci level within tolerance.

        Args:
            price: Price to check
            level: Fibonacci level to compare against
            tolerance: Tolerance threshold (uses adaptive if None)

        Returns:
            True if price is within tolerance of level
        """
        if tolerance is None:
            tolerance = self.get_tolerance()

        if price <= 0 or level.price <= 0:
            return False

        diff = abs(price - level.price) / price
        return diff < tolerance

    def price_crossed_level(
        self,
        prev_price: float,
        curr_price: float,
        level: FibonacciLevel
    ) -> str:
        """
        Check if price crossed a level.

        Args:
            prev_price: Previous price
            curr_price: Current price
            level: Fibonacci level to check

        Returns:
            'UP' if crossed upward, 'DOWN' if crossed downward, 'NONE' otherwise
        """
        if prev_price < level.price <= curr_price:
            return 'UP'
        if prev_price > level.price >= curr_price:
            return 'DOWN'
        return 'NONE'
