"""Momentum signal generator."""

from typing import List

from .base import SignalGenerator
from ..core.models import FibonacciSignal
from ..analysis.context import FibonacciContext


class PriceActionMomentumSignals(SignalGenerator):
    """Price momentum signals at Fibonacci levels."""

    def generate(self, ctx: FibonacciContext) -> List[FibonacciSignal]:
        signals = []

        if ctx.close is None or len(ctx.df) < 5:
            return signals

        # Calculate momentum
        close_5_ago = ctx._safe_float(ctx.df['Close'].iloc[-5])
        if close_5_ago is None or close_5_ago <= 0:
            return signals

        momentum_pct = (ctx.close - close_5_ago) / close_5_ago * 100

        levels = ctx.get_fib_levels()
        tolerance = ctx.get_tolerance()

        for level in levels.values():
            if not ctx.price_at_level(ctx.close, level, tolerance):
                continue

            # Strong upward momentum at Fibonacci
            if momentum_pct > 3:
                signals.append(FibonacciSignal(
                    signal=f"FIB {level.name} + STRONG UP MOMENTUM",
                    description=f"Strong bullish momentum ({momentum_pct:.1f}%) at {level.name}",
                    strength='SIGNIFICANT',
                    category='FIB_MOMENTUM',
                    timeframe=ctx.interval,
                    value=level.price,
                    metadata={'momentum_pct': momentum_pct, 'direction': 'BULLISH'}
                ))

            # Strong downward momentum at Fibonacci
            elif momentum_pct < -3:
                signals.append(FibonacciSignal(
                    signal=f"FIB {level.name} + STRONG DOWN MOMENTUM",
                    description=f"Strong bearish momentum ({momentum_pct:.1f}%) at {level.name}",
                    strength='SIGNIFICANT',
                    category='FIB_MOMENTUM',
                    timeframe=ctx.interval,
                    value=level.price,
                    metadata={'momentum_pct': momentum_pct, 'direction': 'BEARISH'}
                ))

            # Momentum stalling at Fibonacci (potential reversal)
            elif abs(momentum_pct) < 0.5:
                signals.append(FibonacciSignal(
                    signal=f"FIB {level.name} MOMENTUM STALL",
                    description=f"Momentum stalling at {level.name} Fibonacci",
                    strength='MODERATE',
                    category='FIB_MOMENTUM_STALL',
                    timeframe=ctx.interval,
                    value=level.price,
                    metadata={'momentum_pct': momentum_pct}
                ))

        return signals
