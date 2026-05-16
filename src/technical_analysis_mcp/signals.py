"""Trading signal detection.

Detects trading signals from calculated indicators using the Protocol pattern
for extensibility. Each detector focuses on a specific category of signals.
"""

import logging
import signal as _signal
import time
from typing import Protocol

import pandas as pd

from .config import (
    ADX_TRENDING,
    DETECTOR_TIMEOUT_MS,
    LARGE_MOVE_PERCENT,
    MAX_DETECTOR_FAILURES,
    RSI_EXTREME_OVERSOLD,
    RSI_OVERBOUGHT,
    RSI_OVERSOLD,
    STOCH_OVERBOUGHT,
    STOCH_OVERSOLD,
    VOLUME_SPIKE_2X,
    VOLUME_SPIKE_3X,
    SignalCategory,
    SignalStrength,
)
from .models import MutableSignal

logger = logging.getLogger(__name__)


class SignalDetector(Protocol):
    """Protocol for signal detection strategies."""

    def detect(self, df: pd.DataFrame) -> list[MutableSignal]:
        """Detect signals from indicator data.

        Args:
            df: DataFrame with calculated indicators.

        Returns:
            List of detected signals.
        """
        ...


class MovingAverageSignalDetector:
    """Detects moving average crossover and alignment signals."""

    def detect(self, df: pd.DataFrame) -> list[MutableSignal]:
        """Detect MA-based signals."""
        if len(df) < 2:
            return []

        signals: list[MutableSignal] = []
        current = df.iloc[-1]
        prev = df.iloc[-2]

        signals.extend(self._detect_ma_crossovers(current, prev, df))
        signals.extend(self._detect_price_ma_crosses(current, prev))
        signals.extend(self._detect_ma_alignment(current))

        return signals

    def _detect_ma_crossovers(
        self, current: pd.Series, prev: pd.Series, df: pd.DataFrame
    ) -> list[MutableSignal]:
        """Detect golden cross and death cross."""
        signals: list[MutableSignal] = []

        if len(df) <= 200:
            return signals

        if "SMA_50" not in current.index or "SMA_200" not in current.index:
            return signals

        if prev["SMA_50"] <= prev["SMA_200"] and current["SMA_50"] > current["SMA_200"]:
            signals.append(
                MutableSignal(
                    signal="GOLDEN CROSS",
                    description="50 MA crossed above 200 MA",
                    strength=SignalStrength.STRONG_BULLISH.value,
                    category=SignalCategory.MA_CROSS.value,
                )
            )

        if prev["SMA_50"] >= prev["SMA_200"] and current["SMA_50"] < current["SMA_200"]:
            signals.append(
                MutableSignal(
                    signal="DEATH CROSS",
                    description="50 MA crossed below 200 MA",
                    strength=SignalStrength.STRONG_BEARISH.value,
                    category=SignalCategory.MA_CROSS.value,
                )
            )

        return signals

    def _detect_price_ma_crosses(
        self, current: pd.Series, prev: pd.Series
    ) -> list[MutableSignal]:
        """Detect price crossing above/below moving averages."""
        signals: list[MutableSignal] = []

        if "SMA_20" not in current.index:
            return signals

        if prev["Close"] <= prev["SMA_20"] and current["Close"] > current["SMA_20"]:
            signals.append(
                MutableSignal(
                    signal="PRICE ABOVE 20 MA",
                    description="Price crossed above 20-day MA",
                    strength=SignalStrength.BULLISH.value,
                    category=SignalCategory.MA_CROSS.value,
                )
            )

        if prev["Close"] >= prev["SMA_20"] and current["Close"] < current["SMA_20"]:
            signals.append(
                MutableSignal(
                    signal="PRICE BELOW 20 MA",
                    description="Price crossed below 20-day MA",
                    strength=SignalStrength.BEARISH.value,
                    category=SignalCategory.MA_CROSS.value,
                )
            )

        return signals

    def _detect_ma_alignment(self, current: pd.Series) -> list[MutableSignal]:
        """Detect bullish/bearish MA alignment patterns."""
        signals: list[MutableSignal] = []

        required = ["SMA_10", "SMA_20", "SMA_50"]
        if not all(col in current.index for col in required):
            return signals

        if current["SMA_10"] > current["SMA_20"] > current["SMA_50"]:
            signals.append(
                MutableSignal(
                    signal="MA ALIGNMENT BULLISH",
                    description="10 > 20 > 50 SMA",
                    strength=SignalStrength.STRONG_BULLISH.value,
                    category=SignalCategory.MA_TREND.value,
                )
            )

        if current["SMA_10"] < current["SMA_20"] < current["SMA_50"]:
            signals.append(
                MutableSignal(
                    signal="MA ALIGNMENT BEARISH",
                    description="10 < 20 < 50 SMA",
                    strength=SignalStrength.STRONG_BEARISH.value,
                    category=SignalCategory.MA_TREND.value,
                )
            )

        return signals


class RSISignalDetector:
    """Detects RSI-based overbought/oversold signals."""

    def detect(self, df: pd.DataFrame) -> list[MutableSignal]:
        """Detect RSI signals."""
        if len(df) < 1 or "RSI" not in df.columns:
            return []

        signals: list[MutableSignal] = []
        current = df.iloc[-1]
        rsi = current["RSI"]

        if rsi < RSI_EXTREME_OVERSOLD:
            signals.append(
                MutableSignal(
                    signal="RSI EXTREME OVERSOLD",
                    description=f"RSI at {rsi:.1f}",
                    strength=SignalStrength.STRONG_BULLISH.value,
                    category=SignalCategory.RSI.value,
                )
            )
        elif rsi < RSI_OVERSOLD:
            signals.append(
                MutableSignal(
                    signal="RSI OVERSOLD",
                    description=f"RSI at {rsi:.1f}",
                    strength=SignalStrength.BULLISH.value,
                    category=SignalCategory.RSI.value,
                )
            )

        if rsi > RSI_OVERBOUGHT:
            signals.append(
                MutableSignal(
                    signal="RSI OVERBOUGHT",
                    description=f"RSI at {rsi:.1f}",
                    strength=SignalStrength.BEARISH.value,
                    category=SignalCategory.RSI.value,
                )
            )

        return signals


class MACDSignalDetector:
    """Detects MACD crossover signals."""

    def detect(self, df: pd.DataFrame) -> list[MutableSignal]:
        """Detect MACD signals."""
        if len(df) < 2:
            return []

        required = ["MACD", "MACD_Signal"]
        if not all(col in df.columns for col in required):
            return []

        signals: list[MutableSignal] = []
        current = df.iloc[-1]
        prev = df.iloc[-2]

        if prev["MACD"] <= prev["MACD_Signal"] and current["MACD"] > current["MACD_Signal"]:
            signals.append(
                MutableSignal(
                    signal="MACD BULL CROSS",
                    description="MACD crossed above signal",
                    strength=SignalStrength.BULLISH.value,
                    category=SignalCategory.MACD.value,
                )
            )

        if prev["MACD"] >= prev["MACD_Signal"] and current["MACD"] < current["MACD_Signal"]:
            signals.append(
                MutableSignal(
                    signal="MACD BEAR CROSS",
                    description="MACD crossed below signal",
                    strength=SignalStrength.BEARISH.value,
                    category=SignalCategory.MACD.value,
                )
            )

        if prev["MACD"] <= 0 and current["MACD"] > 0:
            signals.append(
                MutableSignal(
                    signal="MACD ZERO CROSS UP",
                    description="MACD crossed above zero",
                    strength=SignalStrength.BULLISH.value,
                    category=SignalCategory.MACD.value,
                )
            )

        if prev["MACD"] >= 0 and current["MACD"] < 0:
            signals.append(
                MutableSignal(
                    signal="MACD ZERO CROSS DOWN",
                    description="MACD crossed below zero",
                    strength=SignalStrength.BEARISH.value,
                    category=SignalCategory.MACD.value,
                )
            )

        return signals


class BollingerBandSignalDetector:
    """Detects Bollinger Band touch and squeeze signals."""

    def detect(self, df: pd.DataFrame) -> list[MutableSignal]:
        """Detect Bollinger Band signals."""
        if len(df) < 1:
            return []

        required = ["BB_Upper", "BB_Lower", "BB_Width"]
        if not all(col in df.columns for col in required):
            return []

        signals: list[MutableSignal] = []
        current = df.iloc[-1]

        if current["Close"] <= current["BB_Lower"] * 1.01:
            signals.append(
                MutableSignal(
                    signal="AT LOWER BB",
                    description=f"Price at ${current['BB_Lower']:.2f}",
                    strength=SignalStrength.BULLISH.value,
                    category=SignalCategory.BOLLINGER.value,
                )
            )

        if current["Close"] >= current["BB_Upper"] * 0.99:
            signals.append(
                MutableSignal(
                    signal="AT UPPER BB",
                    description=f"Price at ${current['BB_Upper']:.2f}",
                    strength=SignalStrength.BEARISH.value,
                    category=SignalCategory.BOLLINGER.value,
                )
            )

        return signals


class StochasticSignalDetector:
    """Detects Stochastic oscillator signals."""

    def detect(self, df: pd.DataFrame) -> list[MutableSignal]:
        """Detect Stochastic signals."""
        if len(df) < 1 or "Stoch_K" not in df.columns:
            return []

        signals: list[MutableSignal] = []
        current = df.iloc[-1]
        stoch_k = current["Stoch_K"]

        if stoch_k < STOCH_OVERSOLD:
            signals.append(
                MutableSignal(
                    signal="STOCHASTIC OVERSOLD",
                    description=f"K at {stoch_k:.1f}",
                    strength=SignalStrength.BULLISH.value,
                    category=SignalCategory.STOCHASTIC.value,
                )
            )

        if stoch_k > STOCH_OVERBOUGHT:
            signals.append(
                MutableSignal(
                    signal="STOCHASTIC OVERBOUGHT",
                    description=f"K at {stoch_k:.1f}",
                    strength=SignalStrength.BEARISH.value,
                    category=SignalCategory.STOCHASTIC.value,
                )
            )

        return signals


class VolumeSignalDetector:
    """Detects volume-based signals."""

    def detect(self, df: pd.DataFrame) -> list[MutableSignal]:
        """Detect volume signals."""
        if len(df) < 1:
            return []

        required = ["Volume", "Volume_MA_20"]
        if not all(col in df.columns for col in required):
            return []

        signals: list[MutableSignal] = []
        current = df.iloc[-1]

        volume_ratio = current["Volume"] / current["Volume_MA_20"]

        if volume_ratio > VOLUME_SPIKE_3X:
            signals.append(
                MutableSignal(
                    signal="EXTREME VOLUME 3X",
                    description=f"Vol: {current['Volume']:,.0f}",
                    strength=SignalStrength.VERY_SIGNIFICANT.value,
                    category=SignalCategory.VOLUME.value,
                )
            )
        elif volume_ratio > VOLUME_SPIKE_2X:
            signals.append(
                MutableSignal(
                    signal="VOLUME SPIKE 2X",
                    description=f"Vol: {current['Volume']:,.0f}",
                    strength=SignalStrength.SIGNIFICANT.value,
                    category=SignalCategory.VOLUME.value,
                )
            )

        return signals


class TrendSignalDetector:
    """Detects ADX-based trend strength signals."""

    def detect(self, df: pd.DataFrame) -> list[MutableSignal]:
        """Detect trend signals."""
        if len(df) < 1:
            return []

        required = ["ADX", "Close", "SMA_50"]
        if not all(col in df.columns for col in required):
            return []

        signals: list[MutableSignal] = []
        current = df.iloc[-1]

        if current["ADX"] > ADX_TRENDING:
            trend = "UP" if current["Close"] > current["SMA_50"] else "DOWN"
            signals.append(
                MutableSignal(
                    signal=f"STRONG {trend}TREND",
                    description=f"ADX: {current['ADX']:.1f}",
                    strength=SignalStrength.TRENDING.value,
                    category=SignalCategory.TREND.value,
                )
            )

        return signals


class PriceActionSignalDetector:
    """Detects price action signals."""

    def detect(self, df: pd.DataFrame) -> list[MutableSignal]:
        """Detect price action signals."""
        if len(df) < 1 or "Price_Change" not in df.columns:
            return []

        signals: list[MutableSignal] = []
        current = df.iloc[-1]
        price_change = current["Price_Change"]

        if price_change > LARGE_MOVE_PERCENT:
            signals.append(
                MutableSignal(
                    signal="LARGE GAIN",
                    description=f"+{price_change:.1f}% today",
                    strength=SignalStrength.STRONG_BULLISH.value,
                    category=SignalCategory.PRICE_ACTION.value,
                )
            )

        if price_change < -LARGE_MOVE_PERCENT:
            signals.append(
                MutableSignal(
                    signal="LARGE LOSS",
                    description=f"{price_change:.1f}% today",
                    strength=SignalStrength.STRONG_BEARISH.value,
                    category=SignalCategory.PRICE_ACTION.value,
                )
            )

        return signals


_MA_CROSS_PAIRS = [
    (5, 10), (5, 20), (5, 50), (10, 20), (10, 50), (10, 100),
    (20, 50), (20, 100), (20, 200), (50, 100), (50, 200),
]
_RSI_PERIODS = [5, 10, 14, 20, 30]
_RSI_OS_OB = [(20, 80), (25, 75), (30, 70)]
_MACD_PARAMS = [(10, 20, 5), (19, 39, 9), (20, 50, 10)]
_HL_LOOKBACKS = [20, 50, 100, 200, 252]
_HL_PROXIMITIES = [0.01, 0.02, 0.05]
_MA_DIST_PERIODS = [5, 10, 20, 50, 100, 200]
_MA_DIST_THRESHOLDS = [5, 10, 15, 20]
_SR_PROXIMITIES = [0.005, 0.01, 0.02]


def _sf(val) -> float | None:
    """Safe float — returns None on NaN/Inf/None."""
    try:
        import math
        v = float(val)
        return None if (math.isnan(v) or math.isinf(v)) else v
    except Exception:
        return None


class ExpandedMACrossDetector:
    """Detects crossovers across 11 fast/slow SMA pairs."""

    def detect(self, df: pd.DataFrame) -> list[MutableSignal]:
        if len(df) < 2:
            return []
        signals: list[MutableSignal] = []
        current = df.iloc[-1]
        prev = df.iloc[-2]
        for fast, slow in _MA_CROSS_PAIRS:
            cf, cs = f"SMA_{fast}", f"SMA_{slow}"
            if cf not in current.index or cs not in current.index:
                continue
            cur_f, cur_s = _sf(current[cf]), _sf(current[cs])
            pre_f, pre_s = _sf(prev[cf]), _sf(prev[cs])
            if None in (cur_f, cur_s, pre_f, pre_s):
                continue
            if pre_f <= pre_s and cur_f > cur_s:
                label = "GOLDEN CROSS" if (fast, slow) == (50, 200) else f"{fast}/{slow} MA BULL CROSS"
                strength = SignalStrength.STRONG_BULLISH.value if (fast, slow) == (50, 200) else SignalStrength.BULLISH.value
                signals.append(MutableSignal(signal=label, description=f"{fast} SMA crossed above {slow} SMA", strength=strength, category=SignalCategory.MA_CROSS.value))
            elif pre_f >= pre_s and cur_f < cur_s:
                label = "DEATH CROSS" if (fast, slow) == (50, 200) else f"{fast}/{slow} MA BEAR CROSS"
                strength = SignalStrength.STRONG_BEARISH.value if (fast, slow) == (50, 200) else SignalStrength.BEARISH.value
                signals.append(MutableSignal(signal=label, description=f"{fast} SMA crossed below {slow} SMA", strength=strength, category=SignalCategory.MA_CROSS.value))
        return signals


class MultiRSIDetector:
    """RSI signals across multiple periods and OS/OB levels."""

    def detect(self, df: pd.DataFrame) -> list[MutableSignal]:
        if len(df) < 2:
            return []
        signals: list[MutableSignal] = []
        current = df.iloc[-1]
        prev = df.iloc[-2]
        for p in _RSI_PERIODS:
            col = f"RSI_{p}" if f"RSI_{p}" in current.index else ("RSI" if p == 14 else None)
            if col is None or col not in current.index:
                continue
            rsi = _sf(current[col])
            prev_rsi = _sf(prev[col])
            if rsi is None:
                continue
            for os_lvl, ob_lvl in _RSI_OS_OB:
                if rsi < os_lvl:
                    signals.append(MutableSignal(signal=f"RSI{p} OVERSOLD (<{os_lvl})", description=f"RSI({p}): {rsi:.1f}", strength=SignalStrength.BULLISH.value, category=SignalCategory.RSI.value))
                elif rsi > ob_lvl:
                    signals.append(MutableSignal(signal=f"RSI{p} OVERBOUGHT (>{ob_lvl})", description=f"RSI({p}): {rsi:.1f}", strength=SignalStrength.BEARISH.value, category=SignalCategory.RSI.value))
            if prev_rsi is not None:
                if prev_rsi < 50 <= rsi:
                    signals.append(MutableSignal(signal=f"RSI{p} CROSSED 50 BULL", description=f"RSI({p}) crossed above 50: {rsi:.1f}", strength=SignalStrength.BULLISH.value, category=SignalCategory.RSI.value))
                elif prev_rsi > 50 >= rsi:
                    signals.append(MutableSignal(signal=f"RSI{p} CROSSED 50 BEAR", description=f"RSI({p}) crossed below 50: {rsi:.1f}", strength=SignalStrength.BEARISH.value, category=SignalCategory.RSI.value))
        return signals


class MultiMACDDetector:
    """MACD signals across additional parameter sets beyond the default."""

    def detect(self, df: pd.DataFrame) -> list[MutableSignal]:
        if len(df) < 2:
            return []
        signals: list[MutableSignal] = []
        current = df.iloc[-1]
        prev = df.iloc[-2]
        for fast, slow, sig in _MACD_PARAMS:
            tag = f"_{fast}_{slow}_{sig}"
            macd_col, sig_col, hist_col = f"MACD{tag}", f"MACD_Signal{tag}", f"MACD_Hist{tag}"
            if macd_col not in current.index or sig_col not in current.index:
                continue
            macd, macd_sig = _sf(current[macd_col]), _sf(current[sig_col])
            prev_macd, prev_sig = _sf(prev[macd_col]), _sf(prev[sig_col])
            if None in (macd, macd_sig, prev_macd, prev_sig):
                continue
            if prev_macd <= prev_sig and macd > macd_sig:
                signals.append(MutableSignal(signal=f"MACD({fast},{slow},{sig}) BULL CROSS", description="MACD crossed above signal line", strength=SignalStrength.STRONG_BULLISH.value, category=SignalCategory.MACD.value))
            elif prev_macd >= prev_sig and macd < macd_sig:
                signals.append(MutableSignal(signal=f"MACD({fast},{slow},{sig}) BEAR CROSS", description="MACD crossed below signal line", strength=SignalStrength.STRONG_BEARISH.value, category=SignalCategory.MACD.value))
            if prev_macd <= 0 < macd:
                signals.append(MutableSignal(signal=f"MACD({fast},{slow},{sig}) ZERO BULL", description="MACD crossed above zero", strength=SignalStrength.BULLISH.value, category=SignalCategory.MACD.value))
            elif prev_macd >= 0 > macd:
                signals.append(MutableSignal(signal=f"MACD({fast},{slow},{sig}) ZERO BEAR", description="MACD crossed below zero", strength=SignalStrength.BEARISH.value, category=SignalCategory.MACD.value))
            if hist_col in current.index:
                hist, prev_hist = _sf(current[hist_col]), _sf(prev[hist_col])
                if hist is not None and prev_hist is not None:
                    if prev_hist <= 0 < hist:
                        signals.append(MutableSignal(signal=f"MACD({fast},{slow},{sig}) HIST BULL", description="MACD histogram turned positive", strength=SignalStrength.BULLISH.value, category=SignalCategory.MACD.value))
                    elif prev_hist >= 0 > hist:
                        signals.append(MutableSignal(signal=f"MACD({fast},{slow},{sig}) HIST BEAR", description="MACD histogram turned negative", strength=SignalStrength.BEARISH.value, category=SignalCategory.MACD.value))
        return signals


class BBExpansionDetector:
    """Bollinger Band breakout signals: price above/below band, %B extremes, band rides."""

    def detect(self, df: pd.DataFrame) -> list[MutableSignal]:
        if len(df) < 2:
            return []
        signals: list[MutableSignal] = []
        current = df.iloc[-1]
        prev = df.iloc[-2]
        close = _sf(current.get("Close"))
        prev_close = _sf(prev.get("Close"))
        if close is None:
            return signals
        for p in (10, 20, 30, 50):
            for sd in (1.5, 2.0, 2.5, 3.0):
                sd_tag = str(sd).replace(".", "_")
                upper_col = f"BB_{p}_{sd_tag}_Upper"
                lower_col = f"BB_{p}_{sd_tag}_Lower"
                pct_col = f"BB_{p}_{sd_tag}_Pct"
                if upper_col not in current.index or lower_col not in current.index:
                    continue
                upper = _sf(current[upper_col])
                lower = _sf(current[lower_col])
                if upper is None or lower is None:
                    continue
                label = f"BB({p},{sd})"
                if close > upper:
                    signals.append(MutableSignal(signal=f"ABOVE UPPER {label}", description=f"Price {close:.2f} above upper band {upper:.2f}", strength=SignalStrength.EXTREME_BULLISH.value, category=SignalCategory.BB_BREAKOUT.value))
                elif close < lower:
                    signals.append(MutableSignal(signal=f"BELOW LOWER {label}", description=f"Price {close:.2f} below lower band {lower:.2f}", strength=SignalStrength.EXTREME_BEARISH.value, category=SignalCategory.BB_BREAKOUT.value))
                if pct_col in current.index:
                    pct_b = _sf(current[pct_col])
                    if pct_b is not None:
                        if pct_b > 1.0:
                            signals.append(MutableSignal(signal=f"{label} %B > 1", description=f"%B={pct_b:.2f} (overbought)", strength=SignalStrength.BEARISH.value, category=SignalCategory.BB_BREAKOUT.value))
                        elif pct_b < 0.0:
                            signals.append(MutableSignal(signal=f"{label} %B < 0", description=f"%B={pct_b:.2f} (oversold)", strength=SignalStrength.BULLISH.value, category=SignalCategory.BB_BREAKOUT.value))
                if prev_close is not None and upper_col in prev.index:
                    prev_upper = _sf(prev[upper_col])
                    if prev_upper is not None and prev_close > prev_upper and close > upper:
                        signals.append(MutableSignal(signal=f"{label} RIDING UPPER BAND", description="2 consecutive closes above upper band", strength=SignalStrength.STRONG_BULLISH.value, category=SignalCategory.BB_BREAKOUT.value))
        return signals


class StochasticCrossDetector:
    """Stochastic %K/%D cross signals in OS/OB zones."""

    def detect(self, df: pd.DataFrame) -> list[MutableSignal]:
        if len(df) < 2 or "Stoch_K" not in df.columns:
            return []
        signals: list[MutableSignal] = []
        current = df.iloc[-1]
        prev = df.iloc[-2]
        k = _sf(current.get("Stoch_K"))
        d = _sf(current.get("Stoch_D", k))
        pk = _sf(prev.get("Stoch_K", k))
        pd_ = _sf(prev.get("Stoch_D", d))
        if None in (k, d, pk, pd_):
            return signals
        if pk <= pd_ and k > d and k < 30:
            signals.append(MutableSignal(signal="STOCH BULL CROSS (OVERSOLD)", description=f"%K ({k:.1f}) crossed above %D in oversold zone", strength=SignalStrength.STRONG_BULLISH.value, category=SignalCategory.STOCHASTIC.value))
        elif pk >= pd_ and k < d and k > 70:
            signals.append(MutableSignal(signal="STOCH BEAR CROSS (OVERBOUGHT)", description=f"%K ({k:.1f}) crossed below %D in overbought zone", strength=SignalStrength.STRONG_BEARISH.value, category=SignalCategory.STOCHASTIC.value))
        return signals


class IchimokuDetector:
    """Ichimoku Cloud signals: TK cross, price vs cloud, kumo color."""

    def detect(self, df: pd.DataFrame) -> list[MutableSignal]:
        if len(df) < 2:
            return []
        cols = ["Ichimoku_Tenkan", "Ichimoku_Kijun", "Ichimoku_SpanA", "Ichimoku_SpanB"]
        if not all(c in df.columns for c in cols):
            return []
        signals: list[MutableSignal] = []
        current = df.iloc[-1]
        prev = df.iloc[-2]
        tenkan = _sf(current["Ichimoku_Tenkan"])
        kijun = _sf(current["Ichimoku_Kijun"])
        span_a = _sf(current["Ichimoku_SpanA"])
        span_b = _sf(current["Ichimoku_SpanB"])
        close = _sf(current["Close"])
        if None in (tenkan, kijun, span_a, span_b, close):
            return signals
        prev_tenkan = _sf(prev["Ichimoku_Tenkan"]) or tenkan
        prev_kijun = _sf(prev["Ichimoku_Kijun"]) or kijun
        cloud_top = max(span_a, span_b)
        cloud_bot = min(span_a, span_b)
        if prev_tenkan <= prev_kijun and tenkan > kijun:
            signals.append(MutableSignal(signal="ICHIMOKU TK BULL CROSS", description=f"Tenkan ({tenkan:.2f}) crossed above Kijun ({kijun:.2f})", strength=SignalStrength.STRONG_BULLISH.value, category=SignalCategory.ICHIMOKU.value))
        elif prev_tenkan >= prev_kijun and tenkan < kijun:
            signals.append(MutableSignal(signal="ICHIMOKU TK BEAR CROSS", description=f"Tenkan ({tenkan:.2f}) crossed below Kijun ({kijun:.2f})", strength=SignalStrength.STRONG_BEARISH.value, category=SignalCategory.ICHIMOKU.value))
        if close > cloud_top:
            signals.append(MutableSignal(signal="PRICE ABOVE KUMO", description=f"Close ${close:.2f} above cloud top ${cloud_top:.2f}", strength=SignalStrength.BULLISH.value, category=SignalCategory.ICHIMOKU.value))
        elif close < cloud_bot:
            signals.append(MutableSignal(signal="PRICE BELOW KUMO", description=f"Close ${close:.2f} below cloud bottom ${cloud_bot:.2f}", strength=SignalStrength.BEARISH.value, category=SignalCategory.ICHIMOKU.value))
        else:
            signals.append(MutableSignal(signal="PRICE INSIDE KUMO", description=f"Close ${close:.2f} inside cloud (indecision)", strength=SignalStrength.NEUTRAL.value, category=SignalCategory.ICHIMOKU.value))
        if span_a > span_b:
            signals.append(MutableSignal(signal="BULLISH KUMO", description=f"Green cloud: SpanA ({span_a:.2f}) > SpanB ({span_b:.2f})", strength=SignalStrength.BULLISH.value, category=SignalCategory.ICHIMOKU.value))
        else:
            signals.append(MutableSignal(signal="BEARISH KUMO", description=f"Red cloud: SpanA ({span_a:.2f}) < SpanB ({span_b:.2f})", strength=SignalStrength.BEARISH.value, category=SignalCategory.ICHIMOKU.value))
        return signals


class OBVCMFDetector:
    """OBV divergence, OBV/EMA cross, and CMF signals."""

    def detect(self, df: pd.DataFrame) -> list[MutableSignal]:
        if len(df) < 20:
            return []
        signals: list[MutableSignal] = []
        current = df.iloc[-1]
        prev = df.iloc[-2]
        # OBV divergence over 20 bars
        if "OBV" in df.columns:
            recent = df.tail(20)
            price_chg = _sf(recent["Close"].iloc[-1]) or 0
            price_start = _sf(recent["Close"].iloc[0]) or price_chg
            obv_chg = (_sf(recent["OBV"].iloc[-1]) or 0) - (_sf(recent["OBV"].iloc[0]) or 0)
            price_delta = price_chg - price_start
            if price_delta > 0 and obv_chg < 0:
                signals.append(MutableSignal(signal="OBV BEARISH DIVERGENCE", description="Price rising but OBV falling", strength=SignalStrength.BEARISH.value, category=SignalCategory.OBV_CMF.value))
            elif price_delta < 0 and obv_chg > 0:
                signals.append(MutableSignal(signal="OBV BULLISH DIVERGENCE", description="Price falling but OBV rising (accumulation)", strength=SignalStrength.STRONG_BULLISH.value, category=SignalCategory.OBV_CMF.value))
        # OBV / EMA cross
        if "OBV" in df.columns and "OBV_EMA" in df.columns:
            obv = _sf(current.get("OBV"))
            obv_ema = _sf(current.get("OBV_EMA"))
            p_obv = _sf(prev.get("OBV", obv))
            p_ema = _sf(prev.get("OBV_EMA", obv_ema))
            if None not in (obv, obv_ema, p_obv, p_ema):
                if p_obv <= p_ema and obv > obv_ema:
                    signals.append(MutableSignal(signal="OBV BULL CROSS EMA", description="OBV crossed above its 20-period EMA", strength=SignalStrength.BULLISH.value, category=SignalCategory.OBV_CMF.value))
                elif p_obv >= p_ema and obv < obv_ema:
                    signals.append(MutableSignal(signal="OBV BEAR CROSS EMA", description="OBV crossed below its 20-period EMA", strength=SignalStrength.BEARISH.value, category=SignalCategory.OBV_CMF.value))
        # CMF
        if "CMF" in df.columns:
            cmf = _sf(current.get("CMF"))
            prev_cmf = _sf(prev.get("CMF", cmf))
            if cmf is not None:
                if cmf > 0.1:
                    signals.append(MutableSignal(signal="CMF STRONG BUYING", description=f"Chaikin Money Flow: {cmf:.3f} (accumulation)", strength=SignalStrength.BULLISH.value, category=SignalCategory.OBV_CMF.value))
                elif cmf < -0.1:
                    signals.append(MutableSignal(signal="CMF STRONG SELLING", description=f"Chaikin Money Flow: {cmf:.3f} (distribution)", strength=SignalStrength.BEARISH.value, category=SignalCategory.OBV_CMF.value))
                if prev_cmf is not None:
                    if prev_cmf <= 0 < cmf:
                        signals.append(MutableSignal(signal="CMF CROSSED POSITIVE", description=f"CMF turned positive: {cmf:.3f}", strength=SignalStrength.BULLISH.value, category=SignalCategory.OBV_CMF.value))
                    elif prev_cmf >= 0 > cmf:
                        signals.append(MutableSignal(signal="CMF CROSSED NEGATIVE", description=f"CMF turned negative: {cmf:.3f}", strength=SignalStrength.BEARISH.value, category=SignalCategory.OBV_CMF.value))
        return signals


class HLProximityDetector:
    """Signals when price is near multi-period highs or lows."""

    def detect(self, df: pd.DataFrame) -> list[MutableSignal]:
        if len(df) < 1:
            return []
        signals: list[MutableSignal] = []
        current = df.iloc[-1]
        close = _sf(current.get("Close"))
        if close is None:
            return signals
        for lb in _HL_LOOKBACKS:
            high_col, low_col = f"High_{lb}b", f"Low_{lb}b"
            if high_col not in current.index or low_col not in current.index:
                continue
            high_val = _sf(current[high_col])
            low_val = _sf(current[low_col])
            if high_val is None or low_val is None:
                continue
            for prox in _HL_PROXIMITIES:
                if high_val != 0 and close >= high_val * (1 - prox):
                    strength = SignalStrength.EXTREME_BULLISH.value if prox <= 0.01 else SignalStrength.BULLISH.value
                    signals.append(MutableSignal(signal=f"WITHIN {int(prox*100)}% OF {lb}b HIGH", description=f"Close {close:.2f} within {prox*100:.0f}% of {lb}-bar high {high_val:.2f}", strength=strength, category=SignalCategory.RANGE.value))
                if low_val != 0 and close <= low_val * (1 + prox):
                    strength = SignalStrength.EXTREME_BEARISH.value if prox <= 0.01 else SignalStrength.BEARISH.value
                    signals.append(MutableSignal(signal=f"WITHIN {int(prox*100)}% OF {lb}b LOW", description=f"Close {close:.2f} within {prox*100:.0f}% of {lb}-bar low {low_val:.2f}", strength=strength, category=SignalCategory.RANGE.value))
        return signals


class MADistanceExpandedDetector:
    """Signals when price is extended far from key SMAs."""

    def detect(self, df: pd.DataFrame) -> list[MutableSignal]:
        if len(df) < 1:
            return []
        signals: list[MutableSignal] = []
        current = df.iloc[-1]
        for p in _MA_DIST_PERIODS:
            dist_col = f"Dist_SMA_{p}"
            if dist_col not in current.index:
                continue
            dist = _sf(current[dist_col])
            if dist is None:
                continue
            for thresh in _MA_DIST_THRESHOLDS:
                if dist > thresh:
                    signals.append(MutableSignal(signal=f">{thresh}% ABOVE {p}SMA", description=f"{dist:.1f}% above {p}-period SMA", strength=SignalStrength.BEARISH.value, category=SignalCategory.MA_DISTANCE.value))
                elif dist < -thresh:
                    signals.append(MutableSignal(signal=f">{thresh}% BELOW {p}SMA", description=f"{abs(dist):.1f}% below {p}-period SMA", strength=SignalStrength.BULLISH.value, category=SignalCategory.MA_DISTANCE.value))
        return signals


class VolumeDivergenceDetector:
    """Volume divergence and multi-MA spike signals."""

    def detect(self, df: pd.DataFrame) -> list[MutableSignal]:
        if len(df) < 10:
            return []
        signals: list[MutableSignal] = []
        current = df.iloc[-1]
        vol = _sf(current.get("Volume"))
        if vol is None:
            return signals
        for vm in (5, 10, 20, 50):
            col = f"Volume_MA_{vm}"
            if col not in current.index:
                continue
            vol_ma = _sf(current[col])
            if vol_ma is None or vol_ma == 0:
                continue
            ratio = vol / vol_ma
            if ratio > 3.0:
                signals.append(MutableSignal(signal=f"VOLUME SPIKE >3x (MA{vm})", description=f"Volume {ratio:.1f}x the {vm}-bar average", strength=SignalStrength.VERY_SIGNIFICANT.value, category=SignalCategory.VOLUME.value))
            elif ratio > 2.0:
                signals.append(MutableSignal(signal=f"VOLUME SPIKE >2x (MA{vm})", description=f"Volume {ratio:.1f}x the {vm}-bar average", strength=SignalStrength.SIGNIFICANT.value, category=SignalCategory.VOLUME.value))
            elif ratio > 1.5:
                signals.append(MutableSignal(signal=f"VOLUME SPIKE >1.5x (MA{vm})", description=f"Volume {ratio:.1f}x the {vm}-bar average", strength=SignalStrength.SIGNIFICANT.value, category=SignalCategory.VOLUME.value))
        # 10-bar volume divergence
        if len(df) >= 10:
            price_chg = (_sf(df["Close"].iloc[-1]) or 0) - (_sf(df["Close"].iloc[-10]) or 0)
            vol_chg = (_sf(df["Volume"].iloc[-1]) or 0) - (_sf(df["Volume"].iloc[-10]) or 0)
            if price_chg > 0 and vol_chg < 0:
                signals.append(MutableSignal(signal="VOLUME BEARISH DIVERGENCE (10b)", description="Price rising but volume falling over 10 bars", strength=SignalStrength.BEARISH.value, category=SignalCategory.VOLUME.value))
            elif price_chg < 0 and vol_chg > 0:
                signals.append(MutableSignal(signal="VOLUME BULLISH DIVERGENCE (10b)", description="Price falling but volume rising over 10 bars", strength=SignalStrength.BULLISH.value, category=SignalCategory.VOLUME.value))
        return signals


def get_default_detectors() -> list[SignalDetector]:
    """Get the default list of signal detectors.

    Returns:
        List of all standard signal detectors.
    """
    return [
        MovingAverageSignalDetector(),
        ExpandedMACrossDetector(),
        RSISignalDetector(),
        MultiRSIDetector(),
        MACDSignalDetector(),
        MultiMACDDetector(),
        BollingerBandSignalDetector(),
        BBExpansionDetector(),
        StochasticSignalDetector(),
        StochasticCrossDetector(),
        VolumeSignalDetector(),
        VolumeDivergenceDetector(),
        TrendSignalDetector(),
        PriceActionSignalDetector(),
        IchimokuDetector(),
        OBVCMFDetector(),
        HLProximityDetector(),
        MADistanceExpandedDetector(),
    ]


def _run_detector_with_timeout(
    detector: SignalDetector,
    df: pd.DataFrame,
    timeout_ms: int,
) -> list[MutableSignal]:
    """Run a detector with a wall-clock timeout.

    Falls back gracefully — returns [] if the timeout is exceeded or if the
    detector throws.  Uses SIGALRM on POSIX; on non-POSIX platforms the
    timeout is checked via elapsed time after the call (best-effort).
    """
    name = detector.__class__.__name__
    timeout_s = timeout_ms / 1000.0

    # POSIX path: use SIGALRM for hard preemption
    try:
        import signal as _sig
        has_sigalrm = hasattr(_sig, "SIGALRM")
    except ImportError:
        has_sigalrm = False

    if has_sigalrm:
        def _timeout_handler(signum, frame):
            raise TimeoutError(f"Detector {name} exceeded {timeout_ms}ms")

        old_handler = _signal.signal(_signal.SIGALRM, _timeout_handler)
        _signal.setitimer(_signal.ITIMER_REAL, timeout_s)
        try:
            result = detector.detect(df)
        finally:
            _signal.setitimer(_signal.ITIMER_REAL, 0)
            _signal.signal(_signal.SIGALRM, old_handler)
        return result

    # Non-POSIX path: call then check elapsed time; log overrun but don't discard
    t0 = time.monotonic()
    result = detector.detect(df)
    elapsed_ms = (time.monotonic() - t0) * 1000
    if elapsed_ms > timeout_ms:
        logger.warning("Detector %s took %.0f ms (limit %d ms)", name, elapsed_ms, timeout_ms)
    return result


class SignalList(list):
    """list[MutableSignal] with extra robustness metadata.

    Fully backwards-compatible with every existing caller that treats the
    return value of detect_all_signals() as a plain list.  New callers can
    read .degraded and .warnings.
    """

    degraded: bool
    warnings: list[str]

    def __new__(cls, signals: list[MutableSignal], degraded: bool, warnings: list[str]):
        obj = super().__new__(cls, signals)
        obj.degraded = degraded
        obj.warnings = warnings
        return obj

    def __init__(self, signals: list[MutableSignal], degraded: bool, warnings: list[str]):
        super().__init__(signals)


def detect_all_signals(
    df: pd.DataFrame,
    detectors: list[SignalDetector] | None = None,
    timeout_ms: int = DETECTOR_TIMEOUT_MS,
    max_failures: int = MAX_DETECTOR_FAILURES,
) -> "SignalList":
    """Detect all trading signals from indicator data.

    Orchestrates multiple signal detectors, isolating each one so that a
    single failure or timeout cannot crash the pipeline.

    Backwards-compatible: returns a SignalList which behaves exactly like
    list[MutableSignal] but also exposes .degraded and .warnings attributes.

    Args:
        df: DataFrame with calculated indicators.
        detectors: Detectors to run. Defaults to all standard detectors.
        timeout_ms: Per-detector wall-clock budget in milliseconds.
        max_failures: Number of detector failures that marks result degraded.

    Returns:
        SignalList — a list of MutableSignal objects with .degraded and
        .warnings attributes carrying robustness metadata.
    """
    if detectors is None:
        detectors = get_default_detectors()

    signals: list[MutableSignal] = []
    failure_count = 0
    warnings: list[str] = []

    for detector in detectors:
        name = detector.__class__.__name__
        try:
            detected = _run_detector_with_timeout(detector, df, timeout_ms)
            signals.extend(detected)
            logger.debug("Detector %s found %d signals", name, len(detected))
        except TimeoutError:
            failure_count += 1
            warnings.append(f"detector_timeout:{name}")
            logger.warning("Detector %s timed out after %d ms", name, timeout_ms)
        except Exception as e:
            failure_count += 1
            warnings.append(f"detector_error:{name}:{type(e).__name__}")
            logger.warning("Detector %s failed: %s", name, e)

    degraded = failure_count >= max_failures
    if degraded:
        logger.error(
            "%d/%d detectors failed — marking result degraded",
            failure_count,
            len(detectors),
        )

    logger.info(
        "Detected %d total signals (%d detector failures, degraded=%s)",
        len(signals),
        failure_count,
        degraded,
    )
    return SignalList(signals, degraded, warnings)
