"""Volatility signal generator."""

from typing import List

from .base import SignalGenerator
from ..core.models import FibonacciSignal
from ..analysis.context import FibonacciContext


class ATRVolatilityFibSignals(SignalGenerator):
    """Fibonacci + ATR-based volatility signals."""

    def generate(self, ctx: FibonacciContext) -> List[FibonacciSignal]:
        signals = []

        if ctx.close is None or len(ctx.df) < 14:
            return signals

        # Calculate ATR
        atr = ctx.tolerance_calc.calculate_atr()
        if atr <= 0:
            return signals

        atr_pct = atr / ctx.close * 100

        levels = ctx.get_fib_levels()
        tolerance = ctx.get_tolerance()

        for level in levels.values():
            if not ctx.price_at_level(ctx.close, level, tolerance):
                continue

            # High volatility at Fibonacci
            if atr_pct > 3:
                signals.append(FibonacciSignal(
                    signal=f"FIB {level.name} + HIGH ATR VOLATILITY",
                    description=f"High volatility (ATR: {atr_pct:.1f}%) at {level.name}",
                    strength='SIGNIFICANT',
                    category='FIB_ATR',
                    timeframe=ctx.interval,
                    value=level.price,
                    metadata={'atr': atr, 'atr_pct': atr_pct}
                ))

            # Low volatility (potential breakout setup)
            elif atr_pct < 1:
                signals.append(FibonacciSignal(
                    signal=f"FIB {level.name} + LOW ATR (COILING)",
                    description=f"Low volatility coiling at {level.name} (ATR: {atr_pct:.1f}%)",
                    strength='MODERATE',
                    category='FIB_ATR_COIL',
                    timeframe=ctx.interval,
                    value=level.price,
                    metadata={'atr': atr, 'atr_pct': atr_pct}
                ))

        return signals
