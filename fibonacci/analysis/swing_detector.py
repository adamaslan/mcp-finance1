"""
Swing Point Detection for Fibonacci Analysis
=============================================
Detects swing highs and lows across multiple lookback windows.
Provides dynamic swing point detection for robust Fibonacci analysis.
"""

from typing import Dict, Tuple
import pandas as pd


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

    def detect_swings(self, window: int = 50) -> Tuple[float, float, int, int]:
        """
        Detect swing high and low within window.

        Args:
            window: Lookback period for swing detection

        Returns:
            Tuple of (swing_high, swing_low, high_idx, low_idx)
        """
        if window in self._cache:
            return self._cache[window]

        if len(self.df) < window:
            window = len(self.df)

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
        high_val, low_val, high_idx, low_idx = self.detect_swings(window)

        # If low came before high, likely uptrend
        if low_idx < high_idx:
            return 'UP'
        return 'DOWN'

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
