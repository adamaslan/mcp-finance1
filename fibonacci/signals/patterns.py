"""Pattern-based signal generators (harmonic and candlestick)."""

from typing import List, Dict, Tuple

from .base import SignalGenerator
from ..core.models import FibonacciSignal
from ..analysis.context import FibonacciContext


class HarmonicPatternSignals(SignalGenerator):
    """
    Detects harmonic pattern completion at Fibonacci levels.
    Patterns: Gartley, Bat, Butterfly, Crab, Shark
    """

    # Harmonic pattern Fibonacci ratios
    PATTERNS = {
        'GARTLEY': {
            'XAB': (0.618, 0.618),
            'ABC': (0.382, 0.886),
            'BCD': (1.272, 1.618),
            'XAD': (0.786, 0.786)
        },
        'BAT': {
            'XAB': (0.382, 0.500),
            'ABC': (0.382, 0.886),
            'BCD': (1.618, 2.618),
            'XAD': (0.886, 0.886)
        },
        'BUTTERFLY': {
            'XAB': (0.786, 0.786),
            'ABC': (0.382, 0.886),
            'BCD': (1.618, 2.618),
            'XAD': (1.270, 1.618)
        },
        'CRAB': {
            'XAB': (0.382, 0.618),
            'ABC': (0.382, 0.886),
            'BCD': (2.240, 3.618),
            'XAD': (1.618, 1.618)
        },
        'SHARK': {
            'XAB': (0.886, 1.130),
            'ABC': (1.130, 1.618),
            'BCD': (1.618, 2.240),
            'XAD': (0.886, 1.130)
        }
    }

    def generate(self, ctx: FibonacciContext) -> List[FibonacciSignal]:
        signals = []

        if ctx.close is None or len(ctx.df) < 50:
            return signals

        # Find potential XABCD points
        swing_data = ctx.get_swing_data(50)
        if not swing_data:
            return signals

        # Simplified harmonic detection - check if current price
        # is at a harmonic pattern completion ratio

        levels = ctx.get_fib_levels()
        tolerance = ctx.get_tolerance('wide')

        for pattern_name, ratios in self.PATTERNS.items():
            xad_ratio = ratios['XAD'][0]  # Use first ratio

            # Check if price is at XAD completion level
            harmonic_level = swing_data['low'] + (xad_ratio * swing_data['range'])

            if abs(ctx.close - harmonic_level) / ctx.close < tolerance:
                signals.append(FibonacciSignal(
                    signal=f"FIB HARMONIC {pattern_name} COMPLETION",
                    description=f"Potential {pattern_name} pattern completion at {xad_ratio*100:.1f}%",
                    strength='SIGNIFICANT',
                    category='FIB_HARMONIC',
                    timeframe=ctx.interval,
                    value=harmonic_level,
                    metadata={
                        'pattern': pattern_name,
                        'xad_ratio': xad_ratio
                    }
                ))

        return signals


class CandlePatternAtFibSignals(SignalGenerator):
    """Detects candlestick reversal patterns at Fibonacci levels."""

    def generate(self, ctx: FibonacciContext) -> List[FibonacciSignal]:
        signals = []

        if ctx.close is None or len(ctx.df) < 3:
            return signals

        # Current candle data
        open_price = ctx._safe_float(ctx.current.get('Open'))
        high = ctx._safe_float(ctx.current.get('High'))
        low = ctx._safe_float(ctx.current.get('Low'))
        close = ctx.close

        if any(v is None for v in [open_price, high, low]):
            return signals

        body = abs(close - open_price)
        upper_wick = high - max(close, open_price)
        lower_wick = min(close, open_price) - low
        candle_range = high - low

        if candle_range <= 0:
            return signals

        levels = ctx.get_fib_levels()
        tolerance = ctx.get_tolerance()

        for level in levels.values():
            if not ctx.price_at_level(close, level, tolerance * 2):
                continue

            # Hammer/Pin bar (bullish reversal)
            if lower_wick > body * 2 and upper_wick < body * 0.5:
                if low <= level.price:
                    signals.append(FibonacciSignal(
                        signal=f"FIB {level.name} + HAMMER",
                        description=f"Bullish hammer at {level.name} Fibonacci",
                        strength='SIGNIFICANT',
                        category='FIB_CANDLE_REVERSAL',
                        timeframe=ctx.interval,
                        value=level.price,
                        metadata={'pattern': 'HAMMER', 'direction': 'BULLISH'}
                    ))

            # Shooting star (bearish reversal)
            if upper_wick > body * 2 and lower_wick < body * 0.5:
                if high >= level.price:
                    signals.append(FibonacciSignal(
                        signal=f"FIB {level.name} + SHOOTING STAR",
                        description=f"Bearish shooting star at {level.name} Fibonacci",
                        strength='SIGNIFICANT',
                        category='FIB_CANDLE_REVERSAL',
                        timeframe=ctx.interval,
                        value=level.price,
                        metadata={'pattern': 'SHOOTING_STAR', 'direction': 'BEARISH'}
                    ))

            # Doji at Fibonacci
            if body < candle_range * 0.1:
                signals.append(FibonacciSignal(
                    signal=f"FIB {level.name} + DOJI",
                    description=f"Indecision doji at {level.name} Fibonacci",
                    strength='MODERATE',
                    category='FIB_CANDLE_REVERSAL',
                    timeframe=ctx.interval,
                    value=level.price,
                    metadata={'pattern': 'DOJI'}
                ))

            # Engulfing patterns (need previous candle)
            prev_open = ctx._safe_float(ctx.prev.get('Open'))
            prev_close = ctx._safe_float(ctx.prev.get('Close'))

            if prev_open is not None and prev_close is not None:
                prev_body = abs(prev_close - prev_open)

                # Bullish engulfing
                if (close > open_price and  # Current is bullish
                    prev_close < prev_open and  # Previous is bearish
                    open_price < prev_close and  # Opens below prev close
                    close > prev_open):  # Closes above prev open
                    signals.append(FibonacciSignal(
                        signal=f"FIB {level.name} + BULLISH ENGULFING",
                        description=f"Bullish engulfing at {level.name} Fibonacci",
                        strength='SIGNIFICANT',
                        category='FIB_CANDLE_REVERSAL',
                        timeframe=ctx.interval,
                        value=level.price,
                        metadata={'pattern': 'BULLISH_ENGULFING'}
                    ))

                # Bearish engulfing
                if (close < open_price and  # Current is bearish
                    prev_close > prev_open and  # Previous is bullish
                    open_price > prev_close and  # Opens above prev close
                    close < prev_open):  # Closes below prev open
                    signals.append(FibonacciSignal(
                        signal=f"FIB {level.name} + BEARISH ENGULFING",
                        description=f"Bearish engulfing at {level.name} Fibonacci",
                        strength='SIGNIFICANT',
                        category='FIB_CANDLE_REVERSAL',
                        timeframe=ctx.interval,
                        value=level.price,
                        metadata={'pattern': 'BEARISH_ENGULFING'}
                    ))

        return signals
