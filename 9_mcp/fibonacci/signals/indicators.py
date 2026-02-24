"""Technical indicator confluence signal generators."""

from typing import List

from .base import SignalGenerator
from ..core.models import FibonacciSignal, FibonacciType
from ..analysis.context import FibonacciContext


class MovingAverageConfluenceSignals(SignalGenerator):
    """Fibonacci + Moving Average confluence signals."""

    MA_COLUMNS = ['SMA_20', 'SMA_50', 'SMA_100', 'SMA_200', 'EMA_12', 'EMA_26', 'EMA_50']

    def generate(self, ctx: FibonacciContext) -> List[FibonacciSignal]:
        signals = []

        if ctx.close is None:
            return signals

        levels = ctx.get_fib_levels()
        tolerance = ctx.get_tolerance('wide')

        for ma_col in self.MA_COLUMNS:
            if ma_col not in ctx.df.columns:
                continue

            ma_value = ctx._safe_float(ctx.current.get(ma_col))
            if ma_value is None or ma_value <= 0:
                continue

            # Find Fibonacci level closest to MA
            for level in levels.values():
                if abs(ma_value - level.price) / ma_value < tolerance:
                    # Check if price is also near this confluence
                    if abs(ctx.close - level.price) / ctx.close < tolerance * 2:
                        signals.append(FibonacciSignal(
                            signal=f"FIB {level.name} + {ma_col} CONFLUENCE",
                            description=f"{level.name} Fibonacci converging with {ma_col}",
                            strength='SIGNIFICANT',
                            category='FIB_MA_CONFLUENCE',
                            timeframe=ctx.interval,
                            value=level.price,
                            metadata={
                                'ma_type': ma_col,
                                'ma_value': ma_value,
                                'fib_level': level.name
                            }
                        ))

        return signals


class RSIDivergenceSignals(SignalGenerator):
    """Fibonacci + RSI divergence signals."""

    def generate(self, ctx: FibonacciContext) -> List[FibonacciSignal]:
        signals = []

        if ctx.close is None or 'RSI' not in ctx.df.columns:
            return signals

        if len(ctx.df) < 5:
            return signals

        rsi = ctx._safe_float(ctx.current.get('RSI'))
        prev_rsi = ctx._safe_float(ctx.prev.get('RSI'))

        if rsi is None or prev_rsi is None:
            return signals

        swing_data = ctx.get_swing_data()
        if not swing_data:
            return signals

        low = swing_data['low']
        high = swing_data['high']
        swing_range = swing_data['range']

        # Check recent price action for divergence
        price_5_ago = ctx._safe_float(ctx.df['Close'].iloc[-5])
        rsi_5_ago = ctx._safe_float(ctx.df['RSI'].iloc[-5]) if 'RSI' in ctx.df.columns else None

        if price_5_ago is None or rsi_5_ago is None:
            return signals

        # Bullish divergence: price lower, RSI higher (at support levels)
        if ctx.close < price_5_ago and rsi > rsi_5_ago:
            # Check if at Fibonacci support
            if ctx.close < low + (0.5 * swing_range):
                levels = ctx.get_fib_levels()
                for level in levels.values():
                    if level.fib_type == FibonacciType.RETRACE and level.ratio <= 0.618:
                        if ctx.price_at_level(ctx.close, level, ctx.get_tolerance('wide')):
                            signals.append(FibonacciSignal(
                                signal=f"FIB {level.name} + BULLISH RSI DIVERGENCE",
                                description=f"Bullish RSI divergence at {level.name} Fibonacci support",
                                strength='SIGNIFICANT',
                                category='FIB_RSI_DIVERGENCE',
                                timeframe=ctx.interval,
                                value=level.price,
                                metadata={
                                    'divergence_type': 'BULLISH',
                                    'rsi': rsi,
                                    'prev_rsi': rsi_5_ago
                                }
                            ))
                            break

        # Bearish divergence: price higher, RSI lower (at resistance levels)
        if ctx.close > price_5_ago and rsi < rsi_5_ago:
            if ctx.close > low + (0.5 * swing_range):
                levels = ctx.get_fib_levels()
                for level in levels.values():
                    if level.fib_type == FibonacciType.EXTENSION or (
                        level.fib_type == FibonacciType.RETRACE and level.ratio >= 0.618
                    ):
                        if ctx.price_at_level(ctx.close, level, ctx.get_tolerance('wide')):
                            signals.append(FibonacciSignal(
                                signal=f"FIB {level.name} + BEARISH RSI DIVERGENCE",
                                description=f"Bearish RSI divergence at {level.name} Fibonacci resistance",
                                strength='SIGNIFICANT',
                                category='FIB_RSI_DIVERGENCE',
                                timeframe=ctx.interval,
                                value=level.price,
                                metadata={
                                    'divergence_type': 'BEARISH',
                                    'rsi': rsi,
                                    'prev_rsi': rsi_5_ago
                                }
                            ))
                            break

        # Oversold/Overbought at Fibonacci
        levels = ctx.get_fib_levels()
        for level in levels.values():
            if ctx.price_at_level(ctx.close, level, ctx.get_tolerance()):
                if rsi < 30:
                    signals.append(FibonacciSignal(
                        signal=f"FIB {level.name} + RSI OVERSOLD",
                        description=f"RSI oversold ({rsi:.0f}) at {level.name} Fibonacci",
                        strength='SIGNIFICANT',
                        category='FIB_RSI_EXTREME',
                        timeframe=ctx.interval,
                        value=level.price,
                        metadata={'rsi': rsi, 'condition': 'OVERSOLD'}
                    ))
                elif rsi > 70:
                    signals.append(FibonacciSignal(
                        signal=f"FIB {level.name} + RSI OVERBOUGHT",
                        description=f"RSI overbought ({rsi:.0f}) at {level.name} Fibonacci",
                        strength='SIGNIFICANT',
                        category='FIB_RSI_EXTREME',
                        timeframe=ctx.interval,
                        value=level.price,
                        metadata={'rsi': rsi, 'condition': 'OVERBOUGHT'}
                    ))

        return signals


class MACDConfluenceSignals(SignalGenerator):
    """Fibonacci + MACD confluence signals."""

    def generate(self, ctx: FibonacciContext) -> List[FibonacciSignal]:
        signals = []

        if ctx.close is None:
            return signals

        # Check for MACD columns
        macd_cols = {'MACD', 'MACD_Signal', 'MACD_Histogram'}
        if not macd_cols.issubset(set(ctx.df.columns)):
            return signals

        macd = ctx._safe_float(ctx.current.get('MACD'))
        macd_signal = ctx._safe_float(ctx.current.get('MACD_Signal'))
        macd_hist = ctx._safe_float(ctx.current.get('MACD_Histogram'))

        prev_macd = ctx._safe_float(ctx.prev.get('MACD'))
        prev_signal = ctx._safe_float(ctx.prev.get('MACD_Signal'))

        if macd is None or macd_signal is None:
            return signals

        levels = ctx.get_fib_levels()
        tolerance = ctx.get_tolerance()

        # MACD crossover at Fibonacci level
        if prev_macd is not None and prev_signal is not None:
            # Bullish crossover
            if prev_macd < prev_signal and macd > macd_signal:
                for level in levels.values():
                    if ctx.price_at_level(ctx.close, level, tolerance):
                        signals.append(FibonacciSignal(
                            signal=f"FIB {level.name} + MACD BULLISH CROSS",
                            description=f"MACD bullish crossover at {level.name} Fibonacci",
                            strength='SIGNIFICANT',
                            category='FIB_MACD_CROSS',
                            timeframe=ctx.interval,
                            value=level.price,
                            metadata={'cross_type': 'BULLISH', 'macd': macd}
                        ))
                        break

            # Bearish crossover
            if prev_macd > prev_signal and macd < macd_signal:
                for level in levels.values():
                    if ctx.price_at_level(ctx.close, level, tolerance):
                        signals.append(FibonacciSignal(
                            signal=f"FIB {level.name} + MACD BEARISH CROSS",
                            description=f"MACD bearish crossover at {level.name} Fibonacci",
                            strength='SIGNIFICANT',
                            category='FIB_MACD_CROSS',
                            timeframe=ctx.interval,
                            value=level.price,
                            metadata={'cross_type': 'BEARISH', 'macd': macd}
                        ))
                        break

        # MACD histogram reversal at Fibonacci
        if macd_hist is not None and len(ctx.df) >= 3:
            prev_hist = ctx._safe_float(ctx.df['MACD_Histogram'].iloc[-2])
            prev_prev_hist = ctx._safe_float(ctx.df['MACD_Histogram'].iloc[-3])

            if prev_hist is not None and prev_prev_hist is not None:
                # Histogram turning up
                if macd_hist > prev_hist < prev_prev_hist:
                    for level in levels.values():
                        if level.fib_type == FibonacciType.RETRACE:
                            if ctx.price_at_level(ctx.close, level, tolerance):
                                signals.append(FibonacciSignal(
                                    signal=f"FIB {level.name} + MACD HIST REVERSAL UP",
                                    description=f"MACD histogram turning up at {level.name}",
                                    strength='MODERATE',
                                    category='FIB_MACD_HIST',
                                    timeframe=ctx.interval,
                                    value=level.price,
                                    metadata={'histogram': macd_hist}
                                ))
                                break

        return signals


class StochasticConfluenceSignals(SignalGenerator):
    """Fibonacci + Stochastic confluence signals."""

    def generate(self, ctx: FibonacciContext) -> List[FibonacciSignal]:
        signals = []

        if ctx.close is None:
            return signals

        if 'Stoch_K' not in ctx.df.columns or 'Stoch_D' not in ctx.df.columns:
            return signals

        stoch_k = ctx._safe_float(ctx.current.get('Stoch_K'))
        stoch_d = ctx._safe_float(ctx.current.get('Stoch_D'))

        if stoch_k is None or stoch_d is None:
            return signals

        levels = ctx.get_fib_levels()
        tolerance = ctx.get_tolerance()

        for level in levels.values():
            if not ctx.price_at_level(ctx.close, level, tolerance):
                continue

            # Stochastic extreme at Fibonacci
            if stoch_k < 20 and stoch_d < 20:
                signals.append(FibonacciSignal(
                    signal=f"FIB {level.name} + STOCH OVERSOLD",
                    description=f"Stochastic oversold at {level.name} Fibonacci",
                    strength='SIGNIFICANT',
                    category='FIB_STOCH',
                    timeframe=ctx.interval,
                    value=level.price,
                    metadata={'stoch_k': stoch_k, 'stoch_d': stoch_d, 'condition': 'OVERSOLD'}
                ))

            elif stoch_k > 80 and stoch_d > 80:
                signals.append(FibonacciSignal(
                    signal=f"FIB {level.name} + STOCH OVERBOUGHT",
                    description=f"Stochastic overbought at {level.name} Fibonacci",
                    strength='SIGNIFICANT',
                    category='FIB_STOCH',
                    timeframe=ctx.interval,
                    value=level.price,
                    metadata={'stoch_k': stoch_k, 'stoch_d': stoch_d, 'condition': 'OVERBOUGHT'}
                ))

            # Stochastic crossover
            if len(ctx.df) >= 2:
                prev_k = ctx._safe_float(ctx.prev.get('Stoch_K'))
                prev_d = ctx._safe_float(ctx.prev.get('Stoch_D'))

                if prev_k is not None and prev_d is not None:
                    if prev_k < prev_d and stoch_k > stoch_d:  # Bullish cross
                        signals.append(FibonacciSignal(
                            signal=f"FIB {level.name} + STOCH BULLISH CROSS",
                            description=f"Stochastic bullish cross at {level.name}",
                            strength='MODERATE',
                            category='FIB_STOCH_CROSS',
                            timeframe=ctx.interval,
                            value=level.price,
                            metadata={'cross_type': 'BULLISH'}
                        ))

                    elif prev_k > prev_d and stoch_k < stoch_d:  # Bearish cross
                        signals.append(FibonacciSignal(
                            signal=f"FIB {level.name} + STOCH BEARISH CROSS",
                            description=f"Stochastic bearish cross at {level.name}",
                            strength='MODERATE',
                            category='FIB_STOCH_CROSS',
                            timeframe=ctx.interval,
                            value=level.price,
                            metadata={'cross_type': 'BEARISH'}
                        ))

        return signals
