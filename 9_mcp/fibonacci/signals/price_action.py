"""Price action signal generators (bounces and breakouts)."""

from typing import List

from .base import SignalGenerator
from ..core.models import FibonacciSignal, FibonacciType
from ..analysis.context import FibonacciContext


class BounceSignals(SignalGenerator):
    """Detects bounces off Fibonacci levels."""

    def generate(self, ctx: FibonacciContext) -> List[FibonacciSignal]:
        signals = []

        if ctx.close is None or ctx.prev_close is None:
            return signals

        if len(ctx.df) < 3:
            return signals

        levels = ctx.get_fib_levels()

        for key, level in levels.items():
            if level.fib_type not in [FibonacciType.RETRACE, FibonacciType.EXTENSION]:
                continue

            # Bullish bounce: price dipped below then closed above
            low = ctx._safe_float(ctx.current.get('Low'))
            if low is not None and low <= level.price < ctx.close:
                if ctx.close > ctx.prev_close:
                    signals.append(FibonacciSignal(
                        signal=f"FIB {level.name} BULLISH BOUNCE",
                        description=f"Bullish bounce off {level.name} Fibonacci level",
                        strength='SIGNIFICANT',
                        category='FIB_BOUNCE',
                        timeframe=ctx.interval,
                        value=level.price,
                        metadata={'bounce_type': 'BULLISH'}
                    ))

            # Bearish bounce: price spiked above then closed below
            high = ctx._safe_float(ctx.current.get('High'))
            if high is not None and high >= level.price > ctx.close:
                if ctx.close < ctx.prev_close:
                    signals.append(FibonacciSignal(
                        signal=f"FIB {level.name} BEARISH BOUNCE",
                        description=f"Bearish rejection from {level.name} Fibonacci level",
                        strength='SIGNIFICANT',
                        category='FIB_BOUNCE',
                        timeframe=ctx.interval,
                        value=level.price,
                        metadata={'bounce_type': 'BEARISH'}
                    ))

        return signals


class BreakoutSignals(SignalGenerator):
    """Detects breakouts through Fibonacci levels."""

    def generate(self, ctx: FibonacciContext) -> List[FibonacciSignal]:
        signals = []

        if ctx.close is None or ctx.prev_close is None:
            return signals

        levels = ctx.get_fib_levels()
        tolerance = ctx.get_tolerance('tight')

        for key, level in levels.items():
            cross = ctx.price_crossed_level(ctx.prev_close, ctx.close, level)

            if cross == 'UP':
                # Check for decisive break (>1% beyond level)
                break_pct = (ctx.close - level.price) / level.price
                if break_pct > 0.01:
                    strength = 'EXTREME' if break_pct > 0.02 else 'SIGNIFICANT'
                    signals.append(FibonacciSignal(
                        signal=f"FIB {level.name} BULLISH BREAKOUT",
                        description=f"Decisive break above {level.name} Fibonacci",
                        strength=strength,
                        category='FIB_BREAKOUT',
                        timeframe=ctx.interval,
                        value=level.price,
                        metadata={
                            'breakout_type': 'BULLISH',
                            'break_pct': break_pct * 100
                        }
                    ))

            elif cross == 'DOWN':
                break_pct = (level.price - ctx.close) / level.price
                if break_pct > 0.01:
                    strength = 'EXTREME' if break_pct > 0.02 else 'SIGNIFICANT'
                    signals.append(FibonacciSignal(
                        signal=f"FIB {level.name} BEARISH BREAKDOWN",
                        description=f"Decisive break below {level.name} Fibonacci",
                        strength=strength,
                        category='FIB_BREAKOUT',
                        timeframe=ctx.interval,
                        value=level.price,
                        metadata={
                            'breakout_type': 'BEARISH',
                            'break_pct': break_pct * 100
                        }
                    ))

        return signals
