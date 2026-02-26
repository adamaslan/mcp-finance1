"""Time zone signal generator."""

from typing import List

from .base import SignalGenerator
from ..core.models import FibonacciSignal
from ..analysis.context import FibonacciContext
from ..core.registry import FibonacciLevelRegistry


class TimeZoneSignals(SignalGenerator):
    """Fibonacci time zone analysis."""

    def generate(self, ctx: FibonacciContext) -> List[FibonacciSignal]:
        signals = []

        swing_data = ctx.get_swing_data()
        if not swing_data:
            return signals

        current_bar = len(ctx.df)
        pivot_bar = min(swing_data['high_idx'], swing_data['low_idx'])
        bars_from_pivot = current_bar - pivot_bar if pivot_bar < current_bar else 0

        fib_times = FibonacciLevelRegistry.TIME_NUMBERS

        aligned_zones = []

        for fib_num in fib_times:
            # Check if current bar is at or near Fibonacci time from pivot
            if fib_num <= bars_from_pivot:
                remainder = bars_from_pivot % fib_num
                if remainder <= 1 or (fib_num - remainder) <= 1:
                    aligned_zones.append(fib_num)

                    signals.append(FibonacciSignal(
                        signal=f"FIB TIME ZONE {fib_num}",
                        description=f"At {fib_num}-period Fibonacci time zone",
                        strength='SIGNIFICANT' if fib_num >= 21 else 'MODERATE',
                        category='FIB_TIME',
                        timeframe=ctx.interval,
                        value=float(fib_num),
                        metadata={
                            'bars_from_pivot': bars_from_pivot,
                            'fib_number': fib_num
                        }
                    ))

        # Time zone cluster
        if len(aligned_zones) >= 2:
            signals.append(FibonacciSignal(
                signal=f"FIB TIME CLUSTER {len(aligned_zones)}",
                description=f"Multiple time zones aligned: {', '.join(map(str, aligned_zones))}",
                strength='EXTREME',
                category='FIB_TIME_CLUSTER',
                timeframe=ctx.interval,
                value=float(len(aligned_zones)),
                metadata={'aligned_zones': aligned_zones}
            ))

        return signals
