"""Confluence signal generator."""

from typing import List

from .base import SignalGenerator
from ..core.models import FibonacciSignal, FibonacciType
from ..analysis.context import FibonacciContext


class RetraceExtensionConfluenceSignals(SignalGenerator):
    """Detects when retracement and extension levels converge."""

    def generate(self, ctx: FibonacciContext) -> List[FibonacciSignal]:
        signals = []

        if ctx.close is None:
            return signals

        levels = ctx.get_fib_levels()
        retraces = [l for l in levels.values() if l.fib_type == FibonacciType.RETRACE]
        extensions = [l for l in levels.values() if l.fib_type == FibonacciType.EXTENSION]

        tolerance = ctx.get_tolerance('wide')

        for retrace in retraces:
            for ext in extensions:
                # Check if levels converge
                if retrace.price > 0 and abs(retrace.price - ext.price) / retrace.price < 0.03:
                    # Check if price is at confluence
                    avg_price = (retrace.price + ext.price) / 2
                    if abs(ctx.close - avg_price) / ctx.close < tolerance:
                        signals.append(FibonacciSignal(
                            signal=f"FIB {retrace.name} + {ext.name} CONFLUENCE",
                            description=f"Retracement {retrace.name} converges with extension {ext.name}",
                            strength='EXTREME',
                            category='FIB_RET_EXT_CONFLUENCE',
                            timeframe=ctx.interval,
                            value=avg_price,
                            metadata={
                                'retrace_level': retrace.name,
                                'extension_level': ext.name
                            }
                        ))

        return signals
