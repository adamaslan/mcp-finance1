"""Geometric signal generators (arcs and fans)."""

from typing import List

from .base import SignalGenerator
from ..core.models import FibonacciSignal
from ..analysis.context import FibonacciContext


class FibonacciArcSignals(SignalGenerator):
    """Fibonacci arc signal detection."""

    def generate(self, ctx: FibonacciContext) -> List[FibonacciSignal]:
        signals = []

        if ctx.close is None:
            return signals

        swing_data = ctx.get_swing_data()
        if not swing_data:
            return signals

        low = swing_data['low']
        swing_range = swing_data['range']
        current_bar = len(ctx.df)
        pivot_bar = swing_data['low_idx']
        time_since_pivot = current_bar - pivot_bar if pivot_bar < current_bar else 1

        arc_ratios = [0.236, 0.382, 0.500, 0.618, 0.786, 1.0]
        tolerance = ctx.get_tolerance('wide')

        for arc_ratio in arc_ratios:
            # Arc extends outward in both price and time
            time_factor = 1 + (time_since_pivot / len(ctx.df)) if len(ctx.df) > 0 else 1
            arc_price = low + (arc_ratio * swing_range * time_factor)

            if abs(ctx.close - arc_price) / ctx.close < tolerance:
                signals.append(FibonacciSignal(
                    signal=f"FIB ARC {arc_ratio*100:.1f}%",
                    description=f"Price touching {arc_ratio*100:.1f}% Fibonacci arc",
                    strength='MODERATE',
                    category='FIB_ARC',
                    timeframe=ctx.interval,
                    value=arc_price,
                    metadata={'arc_ratio': arc_ratio, 'time_factor': time_factor}
                ))

        return signals


class FibonacciFanSignals(SignalGenerator):
    """Fibonacci fan line signal detection."""

    def generate(self, ctx: FibonacciContext) -> List[FibonacciSignal]:
        signals = []

        if ctx.close is None:
            return signals

        swing_data = ctx.get_swing_data()
        if not swing_data:
            return signals

        low = swing_data['low']
        swing_range = swing_data['range']
        time_diff = len(ctx.df) - 50

        fan_ratios = [0.236, 0.382, 0.500, 0.618, 0.786]
        tolerance = ctx.get_tolerance('wide')

        for fan_ratio in fan_ratios:
            fan_price = low + (fan_ratio * swing_range) * (time_diff / 50) if time_diff > 0 else low
            fan_strength = 'SIGNIFICANT' if fan_ratio in [0.618, 0.786] else 'MODERATE'

            if abs(ctx.close - fan_price) / ctx.close < tolerance:
                signals.append(FibonacciSignal(
                    signal=f"FIB FAN {fan_ratio*100:.1f}%",
                    description=f"Price at {fan_ratio*100:.1f}% Fibonacci fan line",
                    strength=fan_strength,
                    category='FIB_FAN',
                    timeframe=ctx.interval,
                    value=fan_price,
                    metadata={'fan_ratio': fan_ratio}
                ))

        return signals
