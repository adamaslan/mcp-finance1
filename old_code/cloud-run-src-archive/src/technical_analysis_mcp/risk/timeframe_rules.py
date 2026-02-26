"""Timeframe selection rules.

Selects a single active trading timeframe (swing, day, or scalp) based on
market conditions (volatility, trend strength, signals).
"""

from typing import Any
from .models import Timeframe, VolatilityRegime
from .protocols import TimeframeSelector
from ..config import ADX_NO_TREND_THRESHOLD


class DefaultTimeframeSelector:
    """Selects single active timeframe based on market conditions."""

    def select(
        self,
        volatility_regime: VolatilityRegime,
        adx: float,
        signals: list[Any],
    ) -> Timeframe:
        """Select ONE active timeframe.

        Selection logic:
        1. High volatility + momentum → Scalp trades
        2. Medium volatility with trend → Day trades
        3. Low volatility + trend → Swing trades
        4. No trend → Swing (but may be suppressed later)

        Args:
            volatility_regime: Current volatility classification
            adx: Average Directional Index value
            signals: Ranked signals for context (not used in base version)

        Returns:
            Single selected Timeframe (only one can be active)
        """
        # High volatility strongly suggests scalping
        if volatility_regime == VolatilityRegime.HIGH:
            return Timeframe.SCALP

        # Medium volatility - prefer day trading
        if volatility_regime == VolatilityRegime.MEDIUM:
            return Timeframe.DAY

        # Low volatility - swing is most appropriate
        if volatility_regime == VolatilityRegime.LOW:
            # Swing trades still need some trend
            if adx >= ADX_NO_TREND_THRESHOLD:
                return Timeframe.SWING
            # No trend + low vol = poor setup, but return SWING anyway
            # (will be suppressed by suppression layer)
            return Timeframe.SWING

        # Default fallback
        return Timeframe.DAY
