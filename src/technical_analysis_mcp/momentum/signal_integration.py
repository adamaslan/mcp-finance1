"""Integration of momentum into signal ranking and scoring."""

from typing import Dict, Any, List
import logging

from .calculator import MomentumResult, MomentumState

logger = logging.getLogger(__name__)


class SignalMomentumIntegrator:
    """Integrate momentum analysis into signal ranking and scoring."""

    @staticmethod
    def apply_momentum_to_signals(
        signals: List[Dict[str, Any]],
        momentum: MomentumResult,
        momentum_weight: float = 0.15,
        trend_momentum_bonus: float = 10.0,
        trend_momentum_penalty: float = -5.0,
        momentum_confirmation_required: bool = False,
    ) -> List[Dict[str, Any]]:
        """Apply momentum analysis to signal scores.

        Args:
            signals: List of signal dictionaries with 'score' and 'strength' keys
            momentum: MomentumResult from calculator
            momentum_weight: Weight of momentum in overall score (0-0.5)
            trend_momentum_bonus: Bonus for momentum alignment
            trend_momentum_penalty: Penalty for momentum divergence
            momentum_confirmation_required: Require momentum confirmation for signals

        Returns:
            List of signals with momentum adjustments applied
        """
        momentum_adjusted_signals = []

        for signal in signals:
            # Calculate momentum adjustment based on signal alignment
            momentum_adjustment = SignalMomentumIntegrator._calc_momentum_adjustment(
                signal, momentum, trend_momentum_bonus, trend_momentum_penalty
            )

            # Apply momentum weight
            weighted_momentum = momentum_adjustment * momentum_weight

            # Get original score
            base_score = signal.get("score", 50)

            # Calculate final score
            final_score = base_score + weighted_momentum + momentum.signal_modifier
            final_score = max(0, min(100, final_score))

            # Apply confirmation requirement if specified
            if momentum_confirmation_required:
                if momentum.confirmation_status != "confirmed":
                    final_score *= 0.7  # Penalize unconfirmed signals

            # Create adjusted signal
            adjusted = {
                **signal,
                "base_score": base_score,
                "momentum_impact": weighted_momentum,
                "momentum_adjustment_reason": SignalMomentumIntegrator._get_adjustment_reason(
                    signal, momentum
                ),
                "momentum_status": momentum.confirmation_status,
                "score": final_score,
            }

            momentum_adjusted_signals.append(adjusted)

        # Sort by adjusted score
        momentum_adjusted_signals.sort(key=lambda x: x["score"], reverse=True)

        return momentum_adjusted_signals

    @staticmethod
    def _calc_momentum_adjustment(
        signal: Dict[str, Any],
        momentum: MomentumResult,
        bonus: float,
        penalty: float,
    ) -> float:
        """Calculate momentum adjustment for a single signal.

        Args:
            signal: Signal dictionary with 'strength' key
            momentum: MomentumResult
            bonus: Bonus for alignment
            penalty: Penalty for divergence

        Returns:
            Score adjustment value
        """
        strength = signal.get("strength", "NEUTRAL")

        # Check signal alignment with momentum
        signal_bullish = strength in ("STRONG_BULLISH", "BULLISH")
        signal_bearish = strength in ("STRONG_BEARISH", "BEARISH")

        momentum_bullish = momentum.momentum_state in (
            MomentumState.STRONG_UP,
            MomentumState.UP,
        )
        momentum_bearish = momentum.momentum_state in (
            MomentumState.STRONG_DOWN,
            MomentumState.DOWN,
        )

        # Alignment bonus
        if (signal_bullish and momentum_bullish) or (
            signal_bearish and momentum_bearish
        ):
            return bonus

        # Divergence penalty
        if (signal_bullish and momentum_bearish) or (
            signal_bearish and momentum_bullish
        ):
            return penalty

        # No alignment/divergence
        return 0.0

    @staticmethod
    def _get_adjustment_reason(
        signal: Dict[str, Any], momentum: MomentumResult
    ) -> str:
        """Generate human-readable reason for momentum adjustment.

        Args:
            signal: Signal dictionary
            momentum: MomentumResult

        Returns:
            Explanation string
        """
        strength = signal.get("strength", "NEUTRAL")
        signal_bullish = strength in ("STRONG_BULLISH", "BULLISH")
        signal_bearish = strength in ("STRONG_BEARISH", "BEARISH")

        momentum_bullish = momentum.momentum_state in (
            MomentumState.STRONG_UP,
            MomentumState.UP,
        )
        momentum_bearish = momentum.momentum_state in (
            MomentumState.STRONG_DOWN,
            MomentumState.DOWN,
        )

        if (signal_bullish and momentum_bullish) or (
            signal_bearish and momentum_bearish
        ):
            return "Confirmed by momentum"

        if (signal_bullish and momentum_bearish) or (
            signal_bearish and momentum_bullish
        ):
            return f"Caution: Signal conflicts with {momentum.momentum_state.value} momentum"

        return "Momentum neutral"

    @staticmethod
    def generate_momentum_summary(momentum: MomentumResult) -> Dict[str, Any]:
        """Generate a summary of momentum impact on signals.

        Args:
            momentum: MomentumResult

        Returns:
            Dictionary with momentum impact summary
        """
        # Determine signal bias impact
        if momentum.momentum_state in (MomentumState.STRONG_UP, MomentumState.UP):
            bias_impact = "Bullish signals boosted, bearish signals penalized"
            primary_bias = "bullish"
        elif momentum.momentum_state in (
            MomentumState.STRONG_DOWN,
            MomentumState.DOWN,
        ):
            bias_impact = "Bearish signals boosted, bullish signals penalized"
            primary_bias = "bearish"
        else:
            bias_impact = "Mixed signals, momentum stalling"
            primary_bias = "neutral"

        # Trend warning
        trend_warning = None
        if momentum.momentum_trend.value.startswith("decelerating"):
            trend_warning = "Momentum decelerating - watch for reversal"
        elif momentum.momentum_trend.value.startswith("reversing"):
            trend_warning = "Momentum reversing - potential trend change"
        elif momentum.momentum_trend == "FLAT":
            trend_warning = "Momentum flat - choppy conditions"

        # Recommendation
        if momentum.has_divergence:
            divergence_note = f"{momentum.divergence_type.capitalize()} divergence detected"
        else:
            divergence_note = None

        return {
            "primary_momentum_state": momentum.momentum_state.value,
            "momentum_strength": f"{momentum.momentum_strength:.0f}/100",
            "consistency": f"{momentum.momentum_consistency*100:.0f}%",
            "bias_impact": bias_impact,
            "primary_bias": primary_bias,
            "trend_warning": trend_warning,
            "divergence_note": divergence_note,
            "confirmation_status": momentum.confirmation_status,
            "signal_modifier": f"{momentum.signal_modifier:+.1f}",
        }
