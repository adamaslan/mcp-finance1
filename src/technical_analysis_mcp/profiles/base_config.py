"""Base configuration with all configurable parameters."""

from dataclasses import dataclass, field
from typing import Dict, Any, Literal
from enum import Enum


class RiskProfile(str, Enum):
    """User risk tolerance profiles."""

    RISKY = "risky"  # Aggressive, higher risk tolerance
    NEUTRAL = "neutral"  # Balanced approach
    AVERSE = "averse"  # Conservative, capital preservation


@dataclass(frozen=True)
class IndicatorConfig:
    """Technical indicator configuration."""

    # RSI Settings
    rsi_period: int = 14
    rsi_oversold: float = 30.0
    rsi_overbought: float = 70.0
    rsi_extreme_oversold: float = 20.0
    rsi_extreme_overbought: float = 80.0

    # MACD Settings
    macd_fast: int = 12
    macd_slow: int = 26
    macd_signal: int = 9

    # Bollinger Bands
    bollinger_period: int = 20
    bollinger_std: float = 2.0

    # Stochastic
    stochastic_k: int = 14
    stochastic_d: int = 3
    stochastic_oversold: float = 20.0
    stochastic_overbought: float = 80.0

    # ADX/ATR
    adx_period: int = 14
    atr_period: int = 14

    # Moving Averages
    ma_periods: tuple[int, ...] = (5, 10, 20, 50, 100, 200)


@dataclass(frozen=True)
class RiskConfig:
    """Risk management configuration."""

    # Risk:Reward Requirements
    min_rr_ratio: float = 1.5  # Minimum acceptable R:R
    preferred_rr_ratio: float = 2.0  # Target R:R
    max_rr_ratio: float = 5.0  # Cap for unrealistic targets

    # Stop-Loss Settings (ATR multiples)
    stop_min_atr: float = 0.5  # Minimum stop distance
    stop_max_atr: float = 3.0  # Maximum stop distance
    stop_atr_swing: float = 2.0  # Swing trade stop
    stop_atr_day: float = 1.5  # Day trade stop
    stop_atr_scalp: float = 1.0  # Scalp trade stop

    # Volatility Thresholds
    volatility_low: float = 1.5  # Low volatility ceiling
    volatility_high: float = 3.0  # High volatility floor

    # Trend Requirements
    adx_trending: float = 25.0  # Trending threshold
    adx_strong_trend: float = 40.0  # Strong trend threshold
    adx_no_trend: float = 20.0  # No trend ceiling

    # Position Sizing Hints
    max_position_risk_pct: float = 2.0  # Max risk per trade (% of portfolio)
    max_portfolio_heat: float = 6.0  # Max total open risk (%)

    # Suppression Thresholds
    max_conflicting_ratio: float = 0.4  # Max bullish/bearish conflict
    min_volume_ratio: float = 0.5  # Min volume vs 20-day average


@dataclass(frozen=True)
class MomentumConfig:
    """Momentum tracking configuration."""

    # Momentum Calculation
    momentum_period: int = 5  # Lookback bars for momentum
    momentum_strong_threshold: float = 3.0  # Strong momentum %
    momentum_stall_threshold: float = 0.5  # Momentum stall %

    # Momentum Signal Weighting
    momentum_weight_in_score: float = 0.15  # Weight in overall signal score
    momentum_confirmation_required: bool = False  # Require momentum alignment

    # Trend-Momentum Alignment
    trend_momentum_bonus: float = 10.0  # Score bonus for alignment
    trend_momentum_penalty: float = -5.0  # Penalty for divergence


@dataclass(frozen=True)
class SignalConfig:
    """Signal generation and ranking configuration."""

    # Output Limits
    max_signals_returned: int = 50
    max_trade_plans: int = 3

    # Ranking Weights (must sum to 1.0)
    weight_technical: float = 0.40  # Technical signal weight
    weight_momentum: float = 0.20  # Momentum weight
    weight_volume: float = 0.15  # Volume confirmation weight
    weight_trend: float = 0.15  # Trend strength weight
    weight_risk_reward: float = 0.10  # R:R quality weight

    # Signal Category Priorities
    category_weights: Dict[str, float] = field(
        default_factory=lambda: {
            "MA_CROSS": 1.2,
            "MACD": 1.1,
            "RSI": 1.0,
            "VOLUME": 1.0,
            "BOLLINGER": 0.9,
            "STOCHASTIC": 0.9,
            "TREND": 0.8,
            "PRICE_ACTION": 0.7,
        }
    )


@dataclass(frozen=True)
class UserConfig:
    """Complete user configuration bundle."""

    risk_profile: RiskProfile = RiskProfile.NEUTRAL
    indicators: IndicatorConfig = field(default_factory=IndicatorConfig)
    risk: RiskConfig = field(default_factory=RiskConfig)
    momentum: MomentumConfig = field(default_factory=MomentumConfig)
    signals: SignalConfig = field(default_factory=SignalConfig)

    # User-specific overrides (partial updates)
    custom_overrides: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Export configuration as dictionary."""
        return {
            "risk_profile": self.risk_profile.value,
            "indicators": {
                "rsi_period": self.indicators.rsi_period,
                "rsi_oversold": self.indicators.rsi_oversold,
                "rsi_overbought": self.indicators.rsi_overbought,
                "macd_fast": self.indicators.macd_fast,
                "macd_slow": self.indicators.macd_slow,
                "macd_signal": self.indicators.macd_signal,
                "bollinger_period": self.indicators.bollinger_period,
                "bollinger_std": self.indicators.bollinger_std,
                "adx_period": self.indicators.adx_period,
                "atr_period": self.indicators.atr_period,
            },
            "risk": {
                "min_rr_ratio": self.risk.min_rr_ratio,
                "preferred_rr_ratio": self.risk.preferred_rr_ratio,
                "stop_min_atr": self.risk.stop_min_atr,
                "stop_max_atr": self.risk.stop_max_atr,
                "stop_atr_swing": self.risk.stop_atr_swing,
                "volatility_low": self.risk.volatility_low,
                "volatility_high": self.risk.volatility_high,
                "adx_trending": self.risk.adx_trending,
                "adx_strong_trend": self.risk.adx_strong_trend,
                "max_position_risk_pct": self.risk.max_position_risk_pct,
                "max_portfolio_heat": self.risk.max_portfolio_heat,
            },
            "momentum": {
                "momentum_period": self.momentum.momentum_period,
                "momentum_strong_threshold": self.momentum.momentum_strong_threshold,
                "momentum_weight_in_score": self.momentum.momentum_weight_in_score,
                "momentum_confirmation_required": self.momentum.momentum_confirmation_required,
            },
            "signals": {
                "max_signals_returned": self.signals.max_signals_returned,
                "max_trade_plans": self.signals.max_trade_plans,
            },
        }
