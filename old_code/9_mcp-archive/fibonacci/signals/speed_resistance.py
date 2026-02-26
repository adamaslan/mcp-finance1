"""Speed resistance signal generator."""

from typing import List

from .base import SignalGenerator
from ..core.models import FibonacciSignal
from ..analysis.context import FibonacciContext


class FibonacciSpeedResistanceSignals(SignalGenerator):
    """
    Speed resistance lines (1/3 and 2/3 of move).
    These are key levels for trend strength assessment.
    """

    def generate(self, ctx: FibonacciContext) -> List[FibonacciSignal]:
        signals = []

        if ctx.close is None:
            return signals

        swing_data = ctx.get_swing_data()
        if not swing_data:
            return signals

        low = swing_data['low']
        high = swing_data['high']
        swing_range = swing_data['range']

        if swing_range <= 0:
            return signals

        tolerance = ctx.get_tolerance()

        # Speed resistance levels
        speed_levels = [
            (1/3, 'SPEED 1/3', 'First speed resistance'),
            (2/3, 'SPEED 2/3', 'Second speed resistance'),
            (1/4, 'SPEED 1/4', 'Quarter speed line'),
            (3/4, 'SPEED 3/4', 'Three-quarter speed line')
        ]

        for ratio, name, desc in speed_levels:
            level_price = low + (ratio * swing_range)

            if abs(ctx.close - level_price) / ctx.close < tolerance:
                signals.append(FibonacciSignal(
                    signal=f"FIB {name}",
                    description=f"Price at {desc} ({ratio*100:.1f}%)",
                    strength='MODERATE',
                    category='FIB_SPEED_RESISTANCE',
                    timeframe=ctx.interval,
                    value=level_price,
                    metadata={'ratio': ratio, 'speed_type': name}
                ))

        return signals
