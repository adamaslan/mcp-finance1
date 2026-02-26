"""Protocol definitions for risk assessment components.

These Protocols enable extensibility following the existing codebase pattern
(similar to SignalDetector and RankingStrategy).
"""

from typing import Protocol, Any
import pandas as pd
from .models import (
    RiskAssessment,
    VolatilityRegime,
    Timeframe,
    StopLevel,
    TargetLevel,
    RiskReward,
    InvalidationLevel,
    SuppressionReason,
    Vehicle,
)


class VolatilityClassifier(Protocol):
    """Protocol for volatility regime classification."""

    def classify(self, df: pd.DataFrame) -> VolatilityRegime:
        """Classify current volatility regime.

        Args:
            df: DataFrame with ATR and Volatility calculated.

        Returns:
            Volatility regime classification.
        """
        ...


class TimeframeSelector(Protocol):
    """Protocol for timeframe selection."""

    def select(
        self,
        volatility_regime: VolatilityRegime,
        adx: float,
        signals: list[Any],
    ) -> Timeframe:
        """Select optimal trading timeframe.

        Only ONE timeframe should be active at a time.

        Args:
            volatility_regime: Current volatility classification.
            adx: Current ADX value.
            signals: Ranked signals for context.

        Returns:
            Selected trading timeframe.
        """
        ...


class StopCalculator(Protocol):
    """Protocol for stop-loss calculation."""

    def calculate(
        self,
        df: pd.DataFrame,
        bias: str,
        timeframe: Timeframe,
    ) -> StopLevel:
        """Calculate appropriate stop-loss level.

        Args:
            df: DataFrame with price and ATR data.
            bias: Trade bias (bullish/bearish).
            timeframe: Selected timeframe.

        Returns:
            Calculated stop level with validation.
        """
        ...


class TargetCalculator(Protocol):
    """Protocol for target price calculation."""

    def calculate(
        self,
        df: pd.DataFrame,
        bias: str,
        stop: StopLevel,
        min_rr: float,
    ) -> TargetLevel:
        """Calculate target price based on R:R requirements.

        Args:
            df: DataFrame with price and indicator data.
            bias: Trade bias.
            stop: Calculated stop level.
            min_rr: Minimum required R:R ratio.

        Returns:
            Calculated target level.
        """
        ...


class InvalidationDetector(Protocol):
    """Protocol for detecting invalidation levels."""

    def detect(
        self,
        df: pd.DataFrame,
        bias: str,
    ) -> InvalidationLevel | None:
        """Detect structure-based invalidation level.

        Args:
            df: DataFrame with price and moving average data.
            bias: Trade bias.

        Returns:
            Invalidation level if detectable, None otherwise.
        """
        ...


class SuppressionEvaluator(Protocol):
    """Protocol for evaluating suppression conditions."""

    def evaluate(
        self,
        assessment: RiskAssessment,
        signals: list[Any],
    ) -> tuple[SuppressionReason, ...]:
        """Evaluate all suppression conditions.

        Args:
            assessment: Current risk assessment.
            signals: Ranked signals.

        Returns:
            Tuple of suppression reasons (empty if none).
        """
        ...


class VehicleSelector(Protocol):
    """Protocol for selecting trade vehicle."""

    def select(
        self,
        timeframe: Timeframe,
        volatility_regime: VolatilityRegime,
        bias: str,
        expected_move_percent: float,
    ) -> tuple[Vehicle, str | None]:
        """Select appropriate trade vehicle.

        Args:
            timeframe: Selected timeframe.
            volatility_regime: Current volatility.
            bias: Trade bias.
            expected_move_percent: Expected move size.

        Returns:
            Tuple of (vehicle, notes).
        """
        ...
