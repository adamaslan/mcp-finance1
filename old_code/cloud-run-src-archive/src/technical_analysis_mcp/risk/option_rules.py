"""Vehicle selection (stock vs options) with full option suggestions.

Implements stock-first approach: default to stock trading, suggest options only
for swing trades with sufficient expected move and full suggestions
(DTE range, delta range, spread width).
"""

from .models import Timeframe, Vehicle, VolatilityRegime
from .protocols import VehicleSelector
from ..config import (
    OPTION_MIN_EXPECTED_MOVE,
    OPTION_SWING_MIN_DTE,
    OPTION_SWING_MAX_DTE,
    OPTION_CALL_DELTA_MIN,
    OPTION_CALL_DELTA_MAX,
    OPTION_PUT_DELTA_MIN,
    OPTION_PUT_DELTA_MAX,
    OPTION_SPREAD_WIDTH_ATR,
)


class DefaultVehicleSelector:
    """Selects trade vehicle (stock vs options) with full suggestions."""

    def __init__(
        self,
        min_move_for_options: float = OPTION_MIN_EXPECTED_MOVE,
        swing_min_dte: int = OPTION_SWING_MIN_DTE,
        swing_max_dte: int = OPTION_SWING_MAX_DTE,
    ):
        """Initialize vehicle selector.

        Args:
            min_move_for_options: Minimum expected % move for options
            swing_min_dte: Minimum days to expiration for swing options
            swing_max_dte: Maximum days to expiration for swing options
        """
        self._min_move = min_move_for_options
        self._swing_min_dte = swing_min_dte
        self._swing_max_dte = swing_max_dte

    def select(
        self,
        timeframe: Timeframe,
        volatility_regime: VolatilityRegime,
        bias: str,
        expected_move_percent: float,
    ) -> tuple[Vehicle, dict | None]:
        """Select appropriate trade vehicle.

        Stock-first approach:
        - Default to stock
        - Options only for swing trades with sufficient expected move
        - Vertical spreads for defined risk in high volatility
        - Include full suggestions: DTE range, delta range, spread width

        Args:
            timeframe: Selected trading timeframe
            volatility_regime: Current volatility classification
            bias: Trade bias ("bullish" or "bearish")
            expected_move_percent: Expected price move percentage

        Returns:
            Tuple of (Vehicle, suggestions_dict) where suggestions_dict
            contains DTE range, delta range, and spread width for options
        """
        # Default to stock for all non-swing timeframes
        if timeframe != Timeframe.SWING:
            return (Vehicle.STOCK, None)

        # Check if move is large enough for options consideration
        if expected_move_percent < self._min_move:
            return (Vehicle.STOCK, None)

        # Swing trades with sufficient move - suggest options
        suggestions = {
            "dte_range": (self._swing_min_dte, self._swing_max_dte),
            "expected_move_percent": expected_move_percent,
        }

        # Medium volatility - suggest directional options
        if volatility_regime == VolatilityRegime.MEDIUM:
            if bias == "bullish":
                vehicle = Vehicle.OPTION_CALL
                suggestions["delta_range"] = (
                    OPTION_CALL_DELTA_MIN,
                    OPTION_CALL_DELTA_MAX,
                )
                suggestions["reasoning"] = "Consider ATM calls for directional bullish play"
            else:  # bearish
                vehicle = Vehicle.OPTION_PUT
                suggestions["delta_range"] = (
                    OPTION_PUT_DELTA_MIN,
                    OPTION_PUT_DELTA_MAX,
                )
                suggestions["reasoning"] = "Consider ATM puts for directional bearish play"

            return (vehicle, suggestions)

        # High volatility - suggest spreads for defined risk
        if volatility_regime == VolatilityRegime.HIGH:
            if bias == "bullish":
                vehicle = Vehicle.OPTION_SPREAD
                suggestions["spread_type"] = "Bull Call Spread"
                suggestions["delta_range"] = (
                    OPTION_CALL_DELTA_MIN,
                    OPTION_CALL_DELTA_MAX,
                )
                suggestions["reasoning"] = (
                    "High volatility suitable for spreads; consider bull call "
                    "spread for defined risk"
                )
            else:  # bearish
                vehicle = Vehicle.OPTION_SPREAD
                suggestions["spread_type"] = "Bear Call Spread"
                suggestions["delta_range"] = (
                    OPTION_PUT_DELTA_MIN,
                    OPTION_PUT_DELTA_MAX,
                )
                suggestions["reasoning"] = (
                    "High volatility suitable for spreads; consider bear put "
                    "spread for defined risk"
                )

            # Add spread width suggestion (in dollars, based on ATR equivalent)
            # This is approximate - actual width depends on entry price
            suggestions["spread_width_info"] = (
                f"Width typically 1x ATR equivalent for {expected_move_percent:.1f}% "
                "expected move"
            )

            return (vehicle, suggestions)

        # Low volatility - stick with stock
        return (Vehicle.STOCK, None)
