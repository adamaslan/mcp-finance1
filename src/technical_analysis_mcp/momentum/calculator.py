"""Enhanced momentum calculation and tracking."""

from dataclasses import dataclass
from enum import Enum
from typing import Optional
import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)


class MomentumState(str, Enum):
    """Momentum classification states."""

    STRONG_UP = "strong_up"  # > +3% (configurable)
    UP = "up"  # +1% to +3%
    STALL = "stall"  # -0.5% to +0.5%
    DOWN = "down"  # -3% to -1%
    STRONG_DOWN = "strong_down"  # < -3%


class MomentumTrend(str, Enum):
    """Multi-period momentum trend."""

    ACCELERATING_UP = "accelerating_up"  # Momentum increasing positive
    DECELERATING_UP = "decelerating_up"  # Momentum positive but slowing
    REVERSING_UP = "reversing_up"  # Negative momentum turning positive
    ACCELERATING_DOWN = "accelerating_down"  # Momentum increasing negative
    DECELERATING_DOWN = "decelerating_down"  # Momentum negative but improving
    REVERSING_DOWN = "reversing_down"  # Positive momentum turning negative
    FLAT = "flat"  # No clear momentum trend


@dataclass(frozen=True)
class MomentumResult:
    """Complete momentum analysis result.

    Attributes:
        momentum_pct: Current momentum as percentage change
        momentum_state: Classified momentum state (strong_up, up, stall, etc.)
        momentum_5: 5-bar momentum percentage
        momentum_10: 10-bar momentum percentage
        momentum_20: 20-bar momentum percentage
        momentum_trend: Overall momentum trend across periods
        momentum_consistency: 0-1 score of how consistent momentum is
        momentum_strength: Normalized 0-100 strength score
        price_trend: Current price trend ("up", "down", "flat")
        has_divergence: Whether price/momentum divergence detected
        divergence_type: Type of divergence ("bullish", "bearish", None)
        signal_modifier: Score adjustment for signals (-20 to +20)
        confirmation_status: "confirmed", "divergent", "neutral"
    """

    # Current momentum
    momentum_pct: float
    momentum_state: MomentumState

    # Multi-period momentum
    momentum_5: float
    momentum_10: float
    momentum_20: float
    momentum_trend: MomentumTrend

    # Momentum quality
    momentum_consistency: float  # 0-1
    momentum_strength: float  # 0-100

    # Divergence detection
    price_trend: str  # "up", "down", "flat"
    has_divergence: bool
    divergence_type: Optional[str]  # "bullish", "bearish", None

    # Signal integration
    signal_modifier: float  # -20 to +20
    confirmation_status: str  # "confirmed", "divergent", "neutral"

    def to_dict(self) -> dict:
        """Export to dictionary for JSON serialization.

        Returns:
            Dictionary representation of momentum result
        """
        return {
            "current_pct": self.momentum_pct,
            "state": self.momentum_state.value,
            "5_bar": self.momentum_5,
            "10_bar": self.momentum_10,
            "20_bar": self.momentum_20,
            "trend": self.momentum_trend.value,
            "consistency": self.momentum_consistency,
            "strength": self.momentum_strength,
            "price_trend": self.price_trend,
            "has_divergence": self.has_divergence,
            "divergence_type": self.divergence_type,
            "signal_modifier": self.signal_modifier,
            "confirmation_status": self.confirmation_status,
        }


class MomentumCalculator:
    """Calculate and track momentum across multiple timeframes."""

    def __init__(
        self,
        strong_threshold: float = 3.0,
        stall_threshold: float = 0.5,
        periods: tuple[int, ...] = (5, 10, 20),
    ):
        """Initialize momentum calculator.

        Args:
            strong_threshold: Threshold for "strong" momentum (%)
            stall_threshold: Threshold for momentum stall (%)
            periods: Periods to calculate momentum for
        """
        self.strong_threshold = strong_threshold
        self.stall_threshold = stall_threshold
        self.periods = periods

    def calculate(self, df: pd.DataFrame) -> MomentumResult:
        """Calculate comprehensive momentum analysis.

        Args:
            df: DataFrame with 'Close' column and datetime index

        Returns:
            MomentumResult with all momentum metrics

        Raises:
            ValueError: If DataFrame is too small or missing Close column
        """
        if "Close" not in df.columns:
            raise ValueError("DataFrame must contain 'Close' column")

        if len(df) < max(self.periods) + 1:
            raise ValueError(
                f"DataFrame too small: need at least {max(self.periods) + 1} rows"
            )

        close = df["Close"]

        # Calculate momentum for each period
        momentum_values = {}
        for period in self.periods:
            if len(close) >= period + 1:
                mom = (
                    (close.iloc[-1] - close.iloc[-period - 1])
                    / close.iloc[-period - 1]
                    * 100
                )
                momentum_values[period] = mom
            else:
                momentum_values[period] = 0.0

        # Primary momentum (shortest period)
        primary_period = self.periods[0]
        momentum_pct = momentum_values.get(primary_period, 0.0)

        # Classify state
        momentum_state = self._classify_state(momentum_pct)

        # Calculate momentum trend (comparing periods)
        momentum_trend = self._calculate_trend(momentum_values)

        # Calculate consistency (how aligned are different periods)
        consistency = self._calculate_consistency(momentum_values)

        # Normalize strength (0-100)
        strength = min(100, abs(momentum_pct) / self.strong_threshold * 50 + 50)

        # Detect price trend
        price_trend = self._detect_price_trend(close)

        # Check for divergence
        has_divergence, divergence_type = self._detect_divergence(
            momentum_pct, price_trend
        )

        # Calculate signal modifier
        signal_modifier = self._calculate_modifier(
            momentum_state, momentum_trend, has_divergence
        )

        # Determine confirmation status
        confirmation_status = self._get_confirmation_status(
            momentum_state, price_trend, has_divergence
        )

        return MomentumResult(
            momentum_pct=momentum_pct,
            momentum_state=momentum_state,
            momentum_5=momentum_values.get(5, 0.0),
            momentum_10=momentum_values.get(10, 0.0),
            momentum_20=momentum_values.get(20, 0.0),
            momentum_trend=momentum_trend,
            momentum_consistency=consistency,
            momentum_strength=strength,
            price_trend=price_trend,
            has_divergence=has_divergence,
            divergence_type=divergence_type,
            signal_modifier=signal_modifier,
            confirmation_status=confirmation_status,
        )

    def _classify_state(self, momentum_pct: float) -> MomentumState:
        """Classify momentum into state.

        Args:
            momentum_pct: Momentum percentage

        Returns:
            Classified momentum state
        """
        if momentum_pct > self.strong_threshold:
            return MomentumState.STRONG_UP
        elif momentum_pct > self.stall_threshold:
            return MomentumState.UP
        elif momentum_pct < -self.strong_threshold:
            return MomentumState.STRONG_DOWN
        elif momentum_pct < -self.stall_threshold:
            return MomentumState.DOWN
        else:
            return MomentumState.STALL

    def _calculate_trend(
        self, momentum_values: dict[int, float]
    ) -> MomentumTrend:
        """Determine momentum trend from multi-period values.

        Args:
            momentum_values: Dictionary of momentum by period

        Returns:
            Momentum trend classification
        """
        if len(momentum_values) < 2:
            return MomentumTrend.FLAT

        periods = sorted(momentum_values.keys())
        short = momentum_values[periods[0]]
        long = momentum_values[periods[-1]]

        # Both positive
        if short > 0 and long > 0:
            if short > long:
                return MomentumTrend.ACCELERATING_UP
            else:
                return MomentumTrend.DECELERATING_UP

        # Both negative
        if short < 0 and long < 0:
            if short < long:
                return MomentumTrend.ACCELERATING_DOWN
            else:
                return MomentumTrend.DECELERATING_DOWN

        # Crossover
        if short > 0 and long < 0:
            return MomentumTrend.REVERSING_UP
        if short < 0 and long > 0:
            return MomentumTrend.REVERSING_DOWN

        return MomentumTrend.FLAT

    def _calculate_consistency(
        self, momentum_values: dict[int, float]
    ) -> float:
        """Calculate how consistent momentum is across periods.

        Args:
            momentum_values: Dictionary of momentum by period

        Returns:
            Consistency score 0-1
        """
        values = list(momentum_values.values())
        if len(values) < 2:
            return 1.0

        # Check if all same sign
        all_positive = all(v > 0 for v in values)
        all_negative = all(v < 0 for v in values)

        if all_positive or all_negative:
            # Calculate variance as inconsistency measure
            variance = np.var(values)
            mean = abs(np.mean(values))
            if mean > 0:
                cv = variance / mean  # Coefficient of variation
                return max(0, min(1, 1 - cv / 10))  # Normalize to 0-1
            return 1.0
        else:
            # Mixed signs = lower consistency
            return 0.3

    def _detect_price_trend(self, close: pd.Series) -> str:
        """Detect price trend direction.

        Args:
            close: Close price series

        Returns:
            Trend classification: "up", "down", "flat"
        """
        if len(close) < 20:
            return "flat"

        # Simple trend: compare current to 20-period SMA
        sma20 = close.rolling(20).mean().iloc[-1]
        current = close.iloc[-1]

        pct_from_sma = (current - sma20) / sma20 * 100

        if pct_from_sma > 2:
            return "up"
        elif pct_from_sma < -2:
            return "down"
        return "flat"

    def _detect_divergence(
        self,
        momentum_pct: float,
        price_trend: str,
    ) -> tuple[bool, Optional[str]]:
        """Detect momentum/price divergence.

        Args:
            momentum_pct: Momentum percentage
            price_trend: Current price trend

        Returns:
            Tuple of (has_divergence, divergence_type)
        """
        # Bullish divergence: price down but momentum turning up
        if price_trend == "down" and momentum_pct > 0:
            return True, "bullish"

        # Bearish divergence: price up but momentum turning down
        if price_trend == "up" and momentum_pct < 0:
            return True, "bearish"

        return False, None

    def _calculate_modifier(
        self,
        state: MomentumState,
        trend: MomentumTrend,
        has_divergence: bool,
    ) -> float:
        """Calculate signal score modifier based on momentum.

        Args:
            state: Momentum state
            trend: Momentum trend
            has_divergence: Whether divergence detected

        Returns:
            Score modifier (-20 to +20)
        """
        modifier = 0.0

        # State contribution
        state_modifiers = {
            MomentumState.STRONG_UP: 10.0,
            MomentumState.UP: 5.0,
            MomentumState.STALL: 0.0,
            MomentumState.DOWN: -5.0,
            MomentumState.STRONG_DOWN: -10.0,
        }
        modifier += state_modifiers.get(state, 0.0)

        # Trend contribution
        trend_modifiers = {
            MomentumTrend.ACCELERATING_UP: 5.0,
            MomentumTrend.DECELERATING_UP: 2.0,
            MomentumTrend.REVERSING_UP: 8.0,  # Potential reversal signal
            MomentumTrend.ACCELERATING_DOWN: -5.0,
            MomentumTrend.DECELERATING_DOWN: -2.0,
            MomentumTrend.REVERSING_DOWN: -8.0,
        }
        modifier += trend_modifiers.get(trend, 0.0)

        # Divergence adjustment (for signals going against divergence)
        if has_divergence:
            modifier *= 0.7  # Reduce modifier if divergence detected

        return max(-20, min(20, modifier))

    def _get_confirmation_status(
        self,
        state: MomentumState,
        price_trend: str,
        has_divergence: bool,
    ) -> str:
        """Get momentum confirmation status for signals.

        Args:
            state: Momentum state
            price_trend: Current price trend
            has_divergence: Whether divergence detected

        Returns:
            Confirmation status: "confirmed", "divergent", "neutral"
        """
        if has_divergence:
            return "divergent"

        # Check alignment
        bullish_momentum = state in (MomentumState.STRONG_UP, MomentumState.UP)
        bearish_momentum = state in (MomentumState.STRONG_DOWN, MomentumState.DOWN)

        if (bullish_momentum and price_trend == "up") or (
            bearish_momentum and price_trend == "down"
        ):
            return "confirmed"

        return "neutral"
