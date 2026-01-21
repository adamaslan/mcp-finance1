"""Golden Pocket signal generator."""

from typing import List

from .base import SignalGenerator
from ..core.models import FibonacciSignal
from ..analysis.context import FibonacciContext


class GoldenPocketSignals(SignalGenerator):
    """
    Detects price in the 'Golden Pocket' zone (61.8% - 65% retracement).
    This is considered a high-probability reversal zone.
    """

    def generate(self, ctx: FibonacciContext) -> List[FibonacciSignal]:
        signals = []

        if ctx.close is None:
            return signals

        for window in [20, 50, 100]:
            if window > len(ctx.df):
                continue

            swing_data = ctx.get_swing_data(window)
            if not swing_data:
                continue

            low = swing_data['low']
            high = swing_data['high']
            swing_range = swing_data['range']

            if swing_range <= 0:
                continue

            # Golden pocket boundaries
            pocket_low = low + (0.618 * swing_range)
            pocket_high = low + (0.65 * swing_range)

            if pocket_low <= ctx.close <= pocket_high:
                # Calculate position within pocket
                pocket_position = (ctx.close - pocket_low) / (pocket_high - pocket_low)

                signals.append(FibonacciSignal(
                    signal=f"FIB GOLDEN POCKET ({window}P)",
                    description=f"Price in Golden Pocket zone (61.8%-65%) on {window}-period swing",
                    strength='SIGNIFICANT',
                    category='FIB_GOLDEN_POCKET',
                    timeframe=ctx.interval,
                    value=(pocket_low + pocket_high) / 2,
                    metadata={
                        'window': window,
                        'pocket_position': pocket_position,
                        'pocket_low': pocket_low,
                        'pocket_high': pocket_high
                    }
                ))

        return signals
