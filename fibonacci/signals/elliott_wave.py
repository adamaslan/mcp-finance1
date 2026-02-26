"""Elliott Wave signal generator."""

from typing import List

from .base import SignalGenerator
from ..core.models import FibonacciSignal
from ..analysis.context import FibonacciContext


class ElliottWaveSignals(SignalGenerator):
    """Elliott Wave Fibonacci relationship signals."""

    def generate(self, ctx: FibonacciContext) -> List[FibonacciSignal]:
        signals = []

        if ctx.close is None or len(ctx.df) < 100:
            return signals

        tolerance = ctx.get_tolerance('wide')

        # Divide data into wave segments (simplified)
        segment_size = 20
        waves = []

        for i in range(5):
            start_idx = -(100 - i * segment_size)
            end_idx = -(100 - (i + 1) * segment_size) if i < 4 else None

            segment = ctx.df.iloc[start_idx:end_idx] if end_idx else ctx.df.iloc[start_idx:]
            if len(segment) > 0:
                waves.append({
                    'high': segment['High'].max(),
                    'low': segment['Low'].min(),
                    'range': segment['High'].max() - segment['Low'].min()
                })

        if len(waves) < 3:
            return signals

        wave1_range = waves[0]['range']

        if wave1_range <= 0:
            return signals

        # Wave 3 = 1.618x Wave 1
        wave3_target = waves[0]['low'] + (1.618 * wave1_range)
        if abs(ctx.close - wave3_target) / ctx.close < tolerance:
            signals.append(FibonacciSignal(
                signal="ELLIOTT WAVE 3 = 161.8% WAVE 1",
                description="Price at Elliott Wave 3 extension (1.618x Wave 1)",
                strength='SIGNIFICANT',
                category='ELLIOTT_FIB',
                timeframe=ctx.interval,
                value=wave3_target,
                metadata={'wave_ratio': 1.618}
            ))

        # Wave 3 = 2.618x Wave 1 (extended)
        wave3_ext_target = waves[0]['low'] + (2.618 * wave1_range)
        if abs(ctx.close - wave3_ext_target) / ctx.close < tolerance:
            signals.append(FibonacciSignal(
                signal="ELLIOTT WAVE 3 = 261.8% WAVE 1 (EXTENDED)",
                description="Price at extended Wave 3 target (2.618x Wave 1)",
                strength='SIGNIFICANT',
                category='ELLIOTT_FIB',
                timeframe=ctx.interval,
                value=wave3_ext_target,
                metadata={'wave_ratio': 2.618}
            ))

        # Wave 5 = Wave 1 (equality)
        wave5_eq_target = waves[0]['low'] + wave1_range + waves[2]['range'] + wave1_range
        if abs(ctx.close - wave5_eq_target) / ctx.close < tolerance:
            signals.append(FibonacciSignal(
                signal="ELLIOTT WAVE 5 = WAVE 1",
                description="Price at Wave 5 equality with Wave 1",
                strength='MODERATE',
                category='ELLIOTT_FIB',
                timeframe=ctx.interval,
                value=wave5_eq_target,
                metadata={'wave_ratio': 1.0}
            ))

        # Wave 2 retracement check
        if len(waves) >= 2:
            wave2_retrace = waves[1]['range'] / wave1_range if wave1_range > 0 else 0

            if 0.50 <= wave2_retrace <= 0.62:
                signals.append(FibonacciSignal(
                    signal="ELLIOTT WAVE 2 RETRACE 50-61.8%",
                    description=f"Wave 2 retraces {wave2_retrace*100:.1f}% of Wave 1",
                    strength='MODERATE',
                    category='ELLIOTT_FIB',
                    timeframe=ctx.interval,
                    value=wave2_retrace,
                    metadata={'retrace_pct': wave2_retrace}
                ))

            elif 0.38 <= wave2_retrace < 0.50:
                signals.append(FibonacciSignal(
                    signal="ELLIOTT WAVE 2 SHALLOW RETRACE 38.2%",
                    description=f"Shallow Wave 2 retrace ({wave2_retrace*100:.1f}%)",
                    strength='MODERATE',
                    category='ELLIOTT_FIB',
                    timeframe=ctx.interval,
                    value=wave2_retrace,
                    metadata={'retrace_pct': wave2_retrace}
                ))

        return signals
