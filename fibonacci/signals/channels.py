"""Channel signal generator."""

from typing import List

from .base import SignalGenerator
from ..core.models import FibonacciSignal, FibonacciType
from ..analysis.context import FibonacciContext


class ChannelSignals(SignalGenerator):
    """Detects price within Fibonacci channels/zones."""

    def generate(self, ctx: FibonacciContext) -> List[FibonacciSignal]:
        signals = []

        if ctx.close is None:
            return signals

        levels = ctx.get_fib_levels()

        # Group by type
        retracements = sorted(
            [l for l in levels.values() if l.fib_type == FibonacciType.RETRACE],
            key=lambda x: x.ratio
        )
        extensions = sorted(
            [l for l in levels.values() if l.fib_type == FibonacciType.EXTENSION],
            key=lambda x: x.ratio
        )

        # Retracement channels
        for i in range(len(retracements) - 1):
            lower = retracements[i]
            upper = retracements[i + 1]

            if lower.price <= ctx.close <= upper.price:
                # Determine position within channel
                channel_range = upper.price - lower.price
                if channel_range > 0:
                    position = (ctx.close - lower.price) / channel_range
                    position_label = (
                        "LOWER" if position < 0.33 else
                        "MIDDLE" if position < 0.66 else
                        "UPPER"
                    )

                    signals.append(FibonacciSignal(
                        signal=f"FIB CHANNEL {lower.name}-{upper.name} {position_label}",
                        description=f"Price in {position_label.lower()} {lower.name}-{upper.name} channel",
                        strength='MODERATE',
                        category='FIB_CHANNEL',
                        timeframe=ctx.interval,
                        value=(lower.price + upper.price) / 2,
                        metadata={
                            'channel_position': position,
                            'lower_level': lower.name,
                            'upper_level': upper.name
                        }
                    ))

        # Extension channels
        for i in range(len(extensions) - 1):
            lower = extensions[i]
            upper = extensions[i + 1]

            if lower.price <= ctx.close <= upper.price:
                signals.append(FibonacciSignal(
                    signal=f"FIB EXT ZONE {lower.name}-{upper.name}",
                    description=f"Price in extension zone {lower.name}-{upper.name}",
                    strength='SIGNIFICANT',
                    category='FIB_EXT_CHANNEL',
                    timeframe=ctx.interval,
                    value=(lower.price + upper.price) / 2,
                    metadata={
                        'lower_level': lower.name,
                        'upper_level': upper.name
                    }
                ))

        return signals
