"""Trendline confluence signal generator."""

from typing import List
import numpy as np

from .base import SignalGenerator
from ..core.models import FibonacciSignal
from ..analysis.context import FibonacciContext


class TrendLineConfluenceSignals(SignalGenerator):
    """Detects when Fibonacci levels align with trend lines."""

    def generate(self, ctx: FibonacciContext) -> List[FibonacciSignal]:
        signals = []

        if ctx.close is None or len(ctx.df) < 20:
            return signals

        # Calculate simple trend lines using linear regression
        closes = ctx.df['Close'].iloc[-20:].values
        x = np.arange(len(closes))

        # Linear regression
        slope, intercept = np.polyfit(x, closes, 1)
        trend_value = slope * (len(closes) - 1) + intercept

        levels = ctx.get_fib_levels()
        tolerance = ctx.get_tolerance('wide')

        for level in levels.values():
            # Check if trend line value is near Fibonacci level
            if abs(trend_value - level.price) / trend_value < tolerance:
                # And price is also near this area
                if abs(ctx.close - level.price) / ctx.close < tolerance * 2:
                    trend_direction = 'UPTREND' if slope > 0 else 'DOWNTREND'

                    signals.append(FibonacciSignal(
                        signal=f"FIB {level.name} + TRENDLINE CONFLUENCE",
                        description=f"{level.name} Fibonacci aligns with {trend_direction.lower()} line",
                        strength='SIGNIFICANT',
                        category='FIB_TRENDLINE',
                        timeframe=ctx.interval,
                        value=level.price,
                        metadata={
                            'trend_direction': trend_direction,
                            'slope': slope,
                            'trend_value': trend_value
                        }
                    ))

        return signals
