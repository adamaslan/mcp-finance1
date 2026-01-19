"""Stop-loss distance calculation and validation.

Calculates ATR-based stop-loss levels with validation to ensure
stops are neither too wide nor too tight for the selected timeframe.
"""

import pandas as pd
from .models import Timeframe, StopLevel, SuppressionCode
from .protocols import StopCalculator
from ..config import (
    STOP_MIN_ATR_MULTIPLE,
    STOP_MAX_ATR_MULTIPLE,
    STOP_ATR_SWING,
    STOP_ATR_DAY,
    STOP_ATR_SCALP,
)


class ATRStopCalculator:
    """Calculates and validates ATR-based stop levels."""

    def __init__(
        self,
        min_atr: float = STOP_MIN_ATR_MULTIPLE,
        max_atr: float = STOP_MAX_ATR_MULTIPLE,
    ):
        """Initialize stop calculator.

        Args:
            min_atr: Minimum ATR multiple for valid stops
            max_atr: Maximum ATR multiple for valid stops
        """
        self._min_atr = min_atr
        self._max_atr = max_atr
        self._timeframe_multipliers = {
            Timeframe.SWING: STOP_ATR_SWING,
            Timeframe.DAY: STOP_ATR_DAY,
            Timeframe.SCALP: STOP_ATR_SCALP,
        }

    def calculate(
        self,
        df: pd.DataFrame,
        bias: str,
        timeframe: Timeframe,
    ) -> StopLevel:
        """Calculate ATR-based stop level.

        Args:
            df: DataFrame with Close, High, Low, and ATR columns
            bias: Trade bias ("bullish" or "bearish")
            timeframe: Selected trading timeframe

        Returns:
            StopLevel with price, distance %, ATR multiple, and validity
        """
        current = df.iloc[-1]
        price = float(current["Close"])
        atr = float(current.get("ATR", price * 0.02))  # Fallback default

        if price <= 0 or atr <= 0:
            # Return invalid stop on bad data
            return StopLevel(
                price=price,
                distance_percent=0,
                atr_multiple=0,
                is_valid=False,
                rejection_reason=SuppressionCode.INSUFFICIENT_DATA,
            )

        # Get ATR multiple based on timeframe
        atr_multiple = self._timeframe_multipliers.get(
            timeframe, STOP_ATR_DAY
        )

        # Calculate stop distance in dollars
        stop_distance = atr * atr_multiple

        # Calculate stop price based on bias
        if bias == "bullish":
            stop_price = price - stop_distance
        else:  # bearish
            stop_price = price + stop_distance

        distance_percent = (stop_distance / price) * 100

        # Validate stop distance
        is_valid = True
        rejection_reason = None

        if atr_multiple < self._min_atr:
            is_valid = False
            rejection_reason = SuppressionCode.STOP_TOO_TIGHT
        elif atr_multiple > self._max_atr:
            is_valid = False
            rejection_reason = SuppressionCode.STOP_TOO_WIDE

        return StopLevel(
            price=stop_price,
            distance_percent=distance_percent,
            atr_multiple=atr_multiple,
            is_valid=is_valid,
            rejection_reason=rejection_reason,
        )
