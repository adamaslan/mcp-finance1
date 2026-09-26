"""
Swing Point Detection for Fibonacci Analysis
=============================================
Detects swing highs and lows across multiple lookback windows.
Provides dynamic swing point detection for robust Fibonacci analysis.
"""

from typing import Dict, Tuple
import pandas as pd

from .legs import SwingLeg, recent_leg

ANCHOR_PIVOTS = 'confirmed_pivots'
ANCHOR_EXTREMES = 'window_extremes'


class SwingPointDetector:
    """
    Detects swing highs and lows across multiple lookback windows.
    Provides dynamic swing point detection for robust Fibonacci analysis.
    """

    def __init__(self, df: pd.DataFrame):
        """
        Initialize swing detector with price data.

        Args:
            df: DataFrame with OHLCV price data (must contain High, Low columns)
        """
        self.df = df
        self._cache: Dict[int, Tuple[float, float, int, int]] = {}
        self._legs: Dict[int, SwingLeg | None] = {}

    def detect_swings(self, window: int = 50) -> Tuple[float, float, int, int]:
        """
        Detect the swing high and low that anchor the Fibonacci levels.

        Anchors on the most recent confirmed-pivot leg of at least 3 x ATR inside
        the window. When no such leg exists, falls back to the window's max High
        and min Low; ``anchor_source`` reports which one was used.

        Args:
            window: Lookback period for swing detection

        Returns:
            Tuple of (swing_high, swing_low, high_idx, low_idx), indices as labels
        """
        if window in self._cache:
            return self._cache[window]

        if len(self.df) < window:
            window = len(self.df)

        leg = self._leg(window)
        if leg is not None:
            index = self.df.index
            self._cache[window] = (leg.high, leg.low, index[leg.high_index], index[leg.low_index])
            return self._cache[window]

        highs = self.df['High'].iloc[-window:]
        lows = self.df['Low'].iloc[-window:]

        high_val = highs.max()
        low_val = lows.min()
        high_idx = highs.idxmax() if hasattr(highs, 'idxmax') else highs.argmax()
        low_idx = lows.idxmin() if hasattr(lows, 'idxmin') else lows.argmin()

        self._cache[window] = (high_val, low_val, high_idx, low_idx)
        return self._cache[window]

    def get_trend_direction(self, window: int = 50) -> str:
        """
        Determine if we're in uptrend or downtrend based on swing sequence.

        Args:
            window: Lookback period for trend assessment

        Returns:
            'UP' if uptrend, 'DOWN' if downtrend
        """
        leg = self._leg(min(window, len(self.df)))
        if leg is not None:
            return 'UP' if leg.is_up else 'DOWN'

        # Compare bar positions, not index labels: labels may be timestamps or
        # integers in any order, and only position says which extreme came first.
        if window > len(self.df):
            window = len(self.df)
        high_pos = int(self.df['High'].iloc[-window:].to_numpy().argmax())
        low_pos = int(self.df['Low'].iloc[-window:].to_numpy().argmin())
        if low_pos < high_pos:
            return 'UP'
        return 'DOWN'

    def anchor_source(self, window: int = 50) -> str:
        """Which anchor ``detect_swings`` uses for this window."""
        return ANCHOR_PIVOTS if self._leg(min(window, len(self.df))) is not None else ANCHOR_EXTREMES

    def _leg(self, window: int) -> SwingLeg | None:
        if window not in self._legs:
            self._legs[window] = recent_leg(self.df, window)
        return self._legs[window]

    def get_multiple_swings(self, windows: list[int] | None = None) -> Dict[int, Tuple[float, float, int, int]]:
        """
        Get swings for multiple timeframe windows.

        Args:
            windows: List of lookback windows (defaults to [20, 50, 100, 200])

        Returns:
            Dictionary mapping window size to swing data tuples
        """
        if windows is None:
            windows = [20, 50, 100, 200]

        return {w: self.detect_swings(w) for w in windows if w <= len(self.df)}
