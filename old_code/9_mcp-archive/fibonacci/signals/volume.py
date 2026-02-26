"""Volume confirmation signal generator."""

from typing import List

from .base import SignalGenerator
from ..core.models import FibonacciSignal
from ..analysis.context import FibonacciContext


class VolumeConfirmationSignals(SignalGenerator):
    """Volume-confirmed Fibonacci signals."""

    def generate(self, ctx: FibonacciContext) -> List[FibonacciSignal]:
        signals = []

        if ctx.close is None or 'Volume' not in ctx.df.columns:
            return signals

        volume = ctx._safe_float(ctx.current.get('Volume'))
        if volume is None or volume <= 0:
            return signals

        # Calculate volume metrics
        if len(ctx.df) >= 20:
            avg_volume = ctx.df['Volume'].iloc[-20:].mean()
            if avg_volume <= 0:
                return signals

            volume_ratio = volume / avg_volume

            levels = ctx.get_fib_levels()
            tolerance = ctx.get_tolerance()

            # Find nearest level
            nearest = min(
                levels.values(),
                key=lambda l: abs(l.price - ctx.close) if l.price > 0 else float('inf')
            )

            if ctx.price_at_level(ctx.close, nearest, tolerance):
                if volume_ratio > 1.5:
                    strength = (
                        'EXTREME' if volume_ratio > 3.0 else
                        'STRONG' if volume_ratio > 2.0 else
                        'SIGNIFICANT'
                    )

                    signals.append(FibonacciSignal(
                        signal=f"FIB {nearest.name} + VOLUME {volume_ratio:.1f}X",
                        description=f"{nearest.name} Fibonacci with {volume_ratio:.1f}x average volume",
                        strength=strength,
                        category='FIB_VOLUME',
                        timeframe=ctx.interval,
                        value=nearest.price,
                        metadata={
                            'volume_ratio': volume_ratio,
                            'fib_level': nearest.name
                        }
                    ))

                # Volume spike
                if volume_ratio > 2.5:
                    signals.append(FibonacciSignal(
                        signal="FIB + VOLUME SPIKE",
                        description=f"Fibonacci level with extreme volume spike ({volume_ratio:.1f}x)",
                        strength='EXTREME',
                        category='FIB_VOLUME_SPIKE',
                        timeframe=ctx.interval,
                        value=ctx.close,
                        metadata={'volume_ratio': volume_ratio}
                    ))

        return signals
