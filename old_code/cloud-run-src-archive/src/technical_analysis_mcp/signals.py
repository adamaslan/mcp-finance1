"""Trading signal detection.

Detects trading signals from calculated indicators using the Protocol pattern
for extensibility. Each detector focuses on a specific category of signals.
"""

import logging
from typing import Protocol

import pandas as pd

from .config import (
    ADX_TRENDING,
    LARGE_MOVE_PERCENT,
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


def get_default_detectors() -> list[SignalDetector]:
    """Get the default list of signal detectors.

    Returns:
        List of all standard signal detectors.
    """
    return [
        MovingAverageSignalDetector(),
        RSISignalDetector(),
        MACDSignalDetector(),
        BollingerBandSignalDetector(),
        StochasticSignalDetector(),
        VolumeSignalDetector(),
        TrendSignalDetector(),
        PriceActionSignalDetector(),
    ]


def detect_all_signals(
    df: pd.DataFrame,
    detectors: list[SignalDetector] | None = None,
) -> list[MutableSignal]:
    """Detect all trading signals from indicator data.

    Orchestrates multiple signal detectors to find all relevant signals.

    Args:
        df: DataFrame with calculated indicators.
        detectors: List of signal detectors to use. Defaults to all standard detectors.

    Returns:
        List of all detected signals.
    """
    if detectors is None:
        detectors = get_default_detectors()

    signals: list[MutableSignal] = []

    for detector in detectors:
        try:
            detected = detector.detect(df)
            signals.extend(detected)
            logger.debug(
                "Detector %s found %d signals",
                detector.__class__.__name__,
                len(detected),
            )
        except Exception as e:
            logger.warning(
                "Detector %s failed: %s",
                detector.__class__.__name__,
                e,
            )

    logger.info("Detected %d total signals", len(signals))
    return signals
