"""Pydantic data models for Technical Analysis MCP Server.

Defines immutable data structures for signals, indicators, and analysis results.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from .config import SignalCategory, SignalStrength


class Signal(BaseModel):
    """A detected trading signal.

    Attributes:
        signal: Short name of the signal (e.g., 'GOLDEN CROSS').
        description: Detailed description of what triggered the signal.
        strength: Signal strength classification.
        category: Signal category for grouping.
        ai_score: AI-assigned score from 1-100 (optional).
        ai_reasoning: Brief explanation from AI ranking (optional).
        rank: Position in ranked signal list (optional).
    """

    model_config = ConfigDict(frozen=True)

    signal: str
    description: str
    strength: str
    category: str
    ai_score: int | None = None
    ai_reasoning: str | None = None
    rank: int | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "signal": self.signal,
            "desc": self.description,
            "strength": self.strength,
            "category": self.category,
            "ai_score": self.ai_score,
            "ai_reasoning": self.ai_reasoning,
            "rank": self.rank,
        }


class Indicators(BaseModel):
    """Technical indicator values for a security.

    Attributes:
        rsi: Relative Strength Index (0-100).
        macd: MACD line value.
        macd_signal: MACD signal line value.
        macd_histogram: MACD histogram value.
        adx: Average Directional Index.
        plus_di: Positive Directional Indicator.
        minus_di: Negative Directional Indicator.
        stoch_k: Stochastic %K.
        stoch_d: Stochastic %D.
        bb_upper: Bollinger Band upper.
        bb_middle: Bollinger Band middle (20 SMA).
        bb_lower: Bollinger Band lower.
        atr: Average True Range.
        volume: Current volume.
        volume_ma_20: 20-period volume moving average.
    """

    model_config = ConfigDict(frozen=True)

    rsi: float
    macd: float
    macd_signal: float
    macd_histogram: float
    adx: float
    plus_di: float
    minus_di: float
    stoch_k: float
    stoch_d: float
    bb_upper: float
    bb_middle: float
    bb_lower: float
    atr: float
    volume: int
    volume_ma_20: float


class IndicatorsSummary(BaseModel):
    """Simplified indicator summary for API responses.

    Attributes:
        rsi: Relative Strength Index.
        macd: MACD line value.
        adx: Average Directional Index.
        volume: Current volume.
    """

    model_config = ConfigDict(frozen=True)

    rsi: float
    macd: float
    adx: float
    volume: int


class AnalysisSummary(BaseModel):
    """Summary statistics for an analysis.

    Attributes:
        total_signals: Total number of signals detected.
        bullish: Count of bullish signals.
        bearish: Count of bearish signals.
        avg_score: Average AI score across all signals.
    """

    model_config = ConfigDict(frozen=True)

    total_signals: int
    bullish: int
    bearish: int
    avg_score: float


class AnalysisResult(BaseModel):
    """Complete analysis result for a security.

    Attributes:
        symbol: Ticker symbol.
        timestamp: When the analysis was performed.
        price: Current price.
        change: Percent change.
        signals: List of detected signals.
        summary: Analysis summary statistics.
        indicators: Key indicator values.
        cached: Whether this result came from cache.
    """

    model_config = ConfigDict(frozen=True)

    symbol: str
    timestamp: datetime
    price: float
    change: float
    signals: tuple[Signal, ...]
    summary: AnalysisSummary
    indicators: IndicatorsSummary
    cached: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "symbol": self.symbol,
            "timestamp": self.timestamp.isoformat(),
            "price": self.price,
            "change": self.change,
            "signals": [s.to_dict() for s in self.signals],
            "summary": {
                "total_signals": self.summary.total_signals,
                "bullish": self.summary.bullish,
                "bearish": self.summary.bearish,
                "avg_score": self.summary.avg_score,
            },
            "indicators": {
                "rsi": self.indicators.rsi,
                "macd": self.indicators.macd,
                "adx": self.indicators.adx,
                "volume": self.indicators.volume,
            },
            "cached": self.cached,
        }


class ComparisonItem(BaseModel):
    """Single item in a security comparison.

    Attributes:
        symbol: Ticker symbol.
        score: Average signal score.
        bullish: Count of bullish signals.
        bearish: Count of bearish signals.
        price: Current price.
        change: Percent change.
    """

    model_config = ConfigDict(frozen=True)

    symbol: str
    score: float
    bullish: int
    bearish: int
    price: float
    change: float


class ComparisonResult(BaseModel):
    """Result of comparing multiple securities.

    Attributes:
        comparison: List of compared securities.
        metric: Metric used for comparison.
        winner: Top-ranked security.
    """

    model_config = ConfigDict(frozen=True)

    comparison: tuple[ComparisonItem, ...]
    metric: str
    winner: ComparisonItem | None


class ScreenMatch(BaseModel):
    """A security that matched screening criteria.

    Attributes:
        symbol: Ticker symbol.
        score: Signal score.
        signals: Total signal count.
        price: Current price.
        rsi: RSI value.
    """

    model_config = ConfigDict(frozen=True)

    symbol: str
    score: float
    signals: int
    price: float
    rsi: float


class ScreeningCriteria(BaseModel):
    """Criteria for screening securities.

    Attributes:
        rsi_min: Minimum RSI value.
        rsi_max: Maximum RSI value.
        min_score: Minimum signal score.
        min_bullish: Minimum bullish signal count.
    """

    model_config = ConfigDict(frozen=True)

    rsi_min: float | None = None
    rsi_max: float | None = None
    min_score: float | None = None
    min_bullish: int | None = None


class ScreeningResult(BaseModel):
    """Result of screening securities.

    Attributes:
        universe: Name of the screened universe.
        total_screened: Total securities screened.
        matches: Securities matching criteria.
        criteria: Criteria used for screening.
    """

    model_config = ConfigDict(frozen=True)

    universe: str
    total_screened: int
    matches: tuple[ScreenMatch, ...]
    criteria: dict[str, Any]


class MutableSignal(BaseModel):
    """Mutable version of Signal for building during detection.

    Use this during signal detection, then convert to immutable Signal.
    """

    signal: str
    description: str
    strength: str
    category: str
    ai_score: int | None = None
    ai_reasoning: str | None = None
    rank: int | None = None

    def to_immutable(self) -> Signal:
        """Convert to immutable Signal."""
        return Signal(
            signal=self.signal,
            description=self.description,
            strength=self.strength,
            category=self.category,
            ai_score=self.ai_score,
            ai_reasoning=self.ai_reasoning,
            rank=self.rank,
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "signal": self.signal,
            "desc": self.description,
            "strength": self.strength,
            "category": self.category,
            "ai_score": self.ai_score,
            "ai_reasoning": self.ai_reasoning,
            "rank": self.rank,
        }
