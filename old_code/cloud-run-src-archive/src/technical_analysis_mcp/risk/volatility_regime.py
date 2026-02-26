"""Volatility regime classification.

Classifies current market volatility as LOW, MEDIUM, or HIGH based on
ATR as a percentage of the current price.
"""

import pandas as pd
from .models import VolatilityRegime
from .protocols import VolatilityClassifier
from ..config import VOLATILITY_LOW_THRESHOLD, VOLATILITY_HIGH_THRESHOLD


class ATRVolatilityClassifier:
    """Classifies volatility regime based on ATR as percentage of price."""

    def __init__(
        self,
        low_threshold: float = VOLATILITY_LOW_THRESHOLD,
        high_threshold: float = VOLATILITY_HIGH_THRESHOLD,
    ):
        """Initialize volatility classifier.

        Args:
            low_threshold: ATR % below this is LOW volatility
            high_threshold: ATR % above this is HIGH volatility
        """
        self._low_threshold = low_threshold
        self._high_threshold = high_threshold

    def classify(self, df: pd.DataFrame) -> VolatilityRegime:
        """Classify volatility using ATR percentage.

        Args:
            df: DataFrame with OHLCV data and ATR calculated

        Returns:
            VolatilityRegime classification (LOW, MEDIUM, or HIGH)
        """
        if "ATR" not in df.columns:
            return VolatilityRegime.MEDIUM  # Default fallback

        current = df.iloc[-1]
        atr = current["ATR"]
        price = current["Close"]

        if price <= 0:
            return VolatilityRegime.MEDIUM  # Safety check

        atr_percent = (atr / price) * 100

        if atr_percent < self._low_threshold:
            return VolatilityRegime.LOW
        elif atr_percent > self._high_threshold:
            return VolatilityRegime.HIGH
        else:
            return VolatilityRegime.MEDIUM
