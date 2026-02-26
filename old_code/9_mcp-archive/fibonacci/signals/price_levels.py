"""Price level signal generator."""

from typing import List

from .base import SignalGenerator
from ..core.models import FibonacciSignal
from ..analysis.context import FibonacciContext


class PriceLevelSignals(SignalGenerator):
    """Generates signals for price at Fibonacci levels."""

    def generate(self, ctx: FibonacciContext) -> List[FibonacciSignal]:
        signals = []

        if ctx.close is None:
            return signals

        for window in [20, 50, 100, 200]:
            if window > len(ctx.df):
                continue

            levels = ctx.get_fib_levels(window)
            tolerance = ctx.get_tolerance()

            for key, level in levels.items():
                if ctx.price_at_level(ctx.close, level, tolerance):
                    window_label = f"{window}P" if window != 50 else ""
                    signals.append(FibonacciSignal(
                        signal=f"FIB {level.fib_type.value} {level.name}{window_label}",
                        description=f"Price at {level.name} {level.fib_type.value.lower()} "
                                   f"({window}-period swing)",
                        strength=level.strength.value,
                        category='FIB_PRICE_LEVEL',
                        timeframe=ctx.interval,
                        value=level.price,
                        metadata={
                            'distance_pct': abs(ctx.close - level.price) / ctx.close * 100,
                            'window': window,
                            'ratio': level.ratio
                        }
                    ))

        return signals
