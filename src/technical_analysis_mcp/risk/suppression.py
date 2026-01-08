"""Suppression evaluation with machine-readable codes.

Evaluates all conditions that should suppress trade output and provides
machine-readable suppression codes with explanations.
"""

from typing import Any
from .models import (
    RiskAssessment,
    SuppressionReason,
    SuppressionCode,
    VolatilityRegime,
)
from .protocols import SuppressionEvaluator
from ..config import (
    MIN_RR_RATIO,
    ADX_TRENDING_THRESHOLD,
    VOLATILITY_HIGH_THRESHOLD,
    MAX_CONFLICTING_SIGNALS_RATIO,
)


class DefaultSuppressionEvaluator:
    """Evaluates all conditions that should suppress trade output."""

    def __init__(
        self,
        min_rr: float = MIN_RR_RATIO,
        adx_trend: float = ADX_TRENDING_THRESHOLD,
    ):
        """Initialize suppression evaluator.

        Args:
            min_rr: Minimum R:R ratio for favorable trades
            adx_trend: ADX threshold for confirming trend
        """
        self._min_rr = min_rr
        self._adx_trend = adx_trend

    def evaluate(
        self,
        assessment: RiskAssessment,
        signals: list[Any],
    ) -> tuple[SuppressionReason, ...]:
        """Evaluate all suppression conditions.

        Args:
            assessment: Current risk assessment
            signals: Ranked signals from detection phase

        Returns:
            Tuple of suppression reasons (empty if none suppressed)
        """
        reasons = []

        # Check R:R favorability
        if not assessment.risk_reward.is_favorable:
            reasons.append(
                SuppressionReason(
                    code=SuppressionCode.RR_UNFAVORABLE,
                    message=(
                        f"R:R ratio {assessment.risk_reward.ratio:.2f}:1 "
                        f"below minimum {self._min_rr}:1"
                    ),
                    threshold=self._min_rr,
                    actual=assessment.risk_reward.ratio,
                )
            )

        # Check stop level validity
        if not assessment.stop.is_valid and assessment.stop.rejection_reason:
            reasons.append(
                SuppressionReason(
                    code=assessment.stop.rejection_reason,
                    message=(
                        f"Stop distance invalid: {assessment.stop.atr_multiple:.2f} ATR "
                        f"(must be 0.5-3.0 ATR)"
                    ),
                    threshold=3.0,
                    actual=assessment.stop.atr_multiple,
                )
            )

        # Check for clear invalidation level
        if assessment.invalidation is None:
            reasons.append(
                SuppressionReason(
                    code=SuppressionCode.NO_CLEAR_INVALIDATION,
                    message="No clear support/resistance structure for stop placement",
                )
            )

        # Check volatility extremes
        if assessment.metrics.volatility_regime == VolatilityRegime.HIGH:
            reasons.append(
                SuppressionReason(
                    code=SuppressionCode.VOLATILITY_TOO_HIGH,
                    message=(
                        f"Volatility regime HIGH ({assessment.metrics.atr_percent:.2f}% ATR) "
                        f"exceeds threshold ({VOLATILITY_HIGH_THRESHOLD}%)"
                    ),
                    threshold=VOLATILITY_HIGH_THRESHOLD,
                    actual=assessment.metrics.atr_percent,
                )
            )

        # Check for trending condition
        if not assessment.metrics.is_trending:
            reasons.append(
                SuppressionReason(
                    code=SuppressionCode.NO_TREND,
                    message=(
                        f"ADX {assessment.metrics.adx:.1f} below trending "
                        f"threshold {self._adx_trend}"
                    ),
                    threshold=self._adx_trend,
                    actual=assessment.metrics.adx,
                )
            )

        # Check for conflicting signals
        if signals:
            bullish_count = sum(
                1 for s in signals if "BULLISH" in str(getattr(s, 'strength', ''))
            )
            bearish_count = sum(
                1 for s in signals if "BEARISH" in str(getattr(s, 'strength', ''))
            )
            total = bullish_count + bearish_count

            if total > 0:
                conflict_ratio = min(bullish_count, bearish_count) / total
                if conflict_ratio > MAX_CONFLICTING_SIGNALS_RATIO:
                    reasons.append(
                        SuppressionReason(
                            code=SuppressionCode.CONFLICTING_SIGNALS,
                            message=(
                                f"Signals conflicting: {bullish_count} bullish vs "
                                f"{bearish_count} bearish (conflict ratio {conflict_ratio:.1%})"
                            ),
                            threshold=MAX_CONFLICTING_SIGNALS_RATIO,
                            actual=conflict_ratio,
                        )
                    )

        return tuple(reasons)
