"""Data models for risk assessment and trade planning.

All models are immutable (frozen) for thread-safety and to match
existing codebase patterns.
"""

from enum import Enum
from typing import Final
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class Timeframe(str, Enum):
    """Active trading timeframe - only one can be active at a time."""

    SWING = "swing"  # 2-10 days
    DAY = "day"  # Intraday
    SCALP = "scalp"  # Minutes to hours


class Bias(str, Enum):
    """Directional bias for the trade."""

    BULLISH = "bullish"
    BEARISH = "bearish"
    NEUTRAL = "neutral"


class RiskQuality(str, Enum):
    """Quality rating of the risk profile."""

    HIGH = "high"  # Favorable R:R, clear invalidation
    MEDIUM = "medium"  # Acceptable but not ideal
    LOW = "low"  # Proceed with caution


class VolatilityRegime(str, Enum):
    """Current volatility classification."""

    LOW = "low"  # ATR < 1.5% of price
    MEDIUM = "medium"  # ATR 1.5-3% of price
    HIGH = "high"  # ATR > 3% of price


class Vehicle(str, Enum):
    """Trade expression vehicle."""

    STOCK = "stock"
    OPTION_CALL = "option_call"
    OPTION_PUT = "option_put"
    OPTION_SPREAD = "option_spread"


class SuppressionCode(str, Enum):
    """Machine-readable suppression reason codes."""

    STOP_TOO_WIDE = "STOP_TOO_WIDE"  # Stop > 3 ATR
    STOP_TOO_TIGHT = "STOP_TOO_TIGHT"  # Stop < 0.5 ATR
    RR_UNFAVORABLE = "RR_UNFAVORABLE"  # R:R < 1.5:1
    NO_CLEAR_INVALIDATION = "NO_CLEAR_INVALIDATION"
    VOLATILITY_TOO_HIGH = "VOLATILITY_TOO_HIGH"  # ATR > 3% of price
    VOLATILITY_TOO_LOW = "VOLATILITY_TOO_LOW"  # ATR < 1.5% of price
    NO_TREND = "NO_TREND"  # ADX < 20
    CONFLICTING_SIGNALS = "CONFLICTING_SIGNALS"  # >40% signals conflict
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"
    NEAR_EARNINGS = "NEAR_EARNINGS"  # Future enhancement
    MARKET_CLOSED = "MARKET_CLOSED"  # Future enhancement


class SuppressionReason(BaseModel):
    """Detailed suppression explanation."""

    model_config = ConfigDict(frozen=True)

    code: SuppressionCode
    message: str
    threshold: float | None = None  # What the threshold was
    actual: float | None = None  # What the actual value was


class RiskMetrics(BaseModel):
    """Calculated risk metrics."""

    model_config = ConfigDict(frozen=True)

    atr: float
    atr_percent: float  # ATR as % of price
    volatility_regime: VolatilityRegime
    adx: float
    is_trending: bool  # ADX > 25
    bb_width_percent: float  # BB width as % of price
    volume_ratio: float  # Current volume / 20-day MA


class StopLevel(BaseModel):
    """Calculated stop-loss level."""

    model_config = ConfigDict(frozen=True)

    price: float
    distance_percent: float
    atr_multiple: float
    is_valid: bool
    rejection_reason: SuppressionCode | None = None


class TargetLevel(BaseModel):
    """Calculated target price level."""

    model_config = ConfigDict(frozen=True)

    price: float
    distance_percent: float
    atr_multiple: float


class RiskReward(BaseModel):
    """Risk-to-reward calculation result."""

    model_config = ConfigDict(frozen=True)

    risk_amount: float  # Stop distance in dollars
    reward_amount: float  # Target distance in dollars
    ratio: float  # reward / risk
    is_favorable: bool  # ratio >= 1.5


class InvalidationLevel(BaseModel):
    """Price level that invalidates the trade thesis."""

    model_config = ConfigDict(frozen=True)

    price: float
    type: str  # "support_break", "resistance_break", "ma_cross"
    description: str


class RiskAssessment(BaseModel):
    """Complete risk assessment for a trading opportunity."""

    model_config = ConfigDict(frozen=True)

    symbol: str
    timestamp: str
    current_price: float

    # Risk metrics
    metrics: RiskMetrics

    # Calculated levels
    stop: StopLevel
    target: TargetLevel
    invalidation: InvalidationLevel | None

    # R:R
    risk_reward: RiskReward

    # Overall assessment
    is_qualified: bool  # Did it pass risk checks?
    risk_quality: RiskQuality
    suppressions: tuple[SuppressionReason, ...] = Field(default_factory=tuple)


class TradePlan(BaseModel):
    """Final actionable trade plan output."""

    model_config = ConfigDict(frozen=True)

    # Core identification
    symbol: str
    timestamp: str

    # Trade thesis
    timeframe: Timeframe
    bias: Bias
    risk_quality: RiskQuality

    # Entry/Exit levels
    entry_price: float
    stop_price: float
    target_price: float
    invalidation_price: float

    # Risk metrics
    risk_reward_ratio: float
    expected_move_percent: float
    max_loss_percent: float

    # Vehicle
    vehicle: Vehicle
    vehicle_notes: str | None = None

    # Full option suggestions (when vehicle is option)
    option_dte_range: tuple[int, int] | None = None  # e.g., (30, 45)
    option_delta_range: tuple[float, float] | None = None  # e.g., (0.40, 0.60)
    option_spread_width: float | None = None  # e.g., $5.00

    # Context from signals
    primary_signal: str  # Top ranked signal driving the trade
    supporting_signals: tuple[str, ...] = Field(default_factory=tuple)

    # If suppressed
    is_suppressed: bool = False
    suppression_reasons: tuple[SuppressionReason, ...] = Field(
        default_factory=tuple
    )


class RiskAnalysisResult(BaseModel):
    """Complete risk analysis output."""

    model_config = ConfigDict(frozen=True)

    symbol: str
    timestamp: str

    # Trade plans (0-3)
    trade_plans: tuple[TradePlan, ...] = Field(default_factory=tuple)

    # If no trades, why
    has_trades: bool
    primary_suppression: SuppressionReason | None = None
    all_suppressions: tuple[SuppressionReason, ...] = Field(default_factory=tuple)

    # Raw data for debugging/display
    risk_assessment: RiskAssessment

    # Compatibility with legacy output
    legacy_signals: tuple[dict, ...] = Field(default_factory=tuple)
