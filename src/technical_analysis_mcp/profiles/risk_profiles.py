"""Pre-defined risk profile configurations."""

from typing import Any
from dataclasses import replace

from .base_config import (
    UserConfig,
    RiskProfile,
    IndicatorConfig,
    RiskConfig,
    MomentumConfig,
    SignalConfig,
)


# ============ RISKY PROFILE ============
# For aggressive traders seeking higher returns with higher risk tolerance
RISKY_CONFIG = UserConfig(
    risk_profile=RiskProfile.RISKY,
    indicators=IndicatorConfig(
        # More sensitive RSI thresholds (enter earlier)
        rsi_oversold=35.0,  # Enter sooner on dips
        rsi_overbought=65.0,  # Exit sooner on rallies
        rsi_extreme_oversold=25.0,
        rsi_extreme_overbought=75.0,
        # Tighter Bollinger Bands (more signals)
        bollinger_std=1.5,
        # Faster stochastic
        stochastic_k=9,
        stochastic_d=3,
    ),
    risk=RiskConfig(
        # Lower R:R acceptable (more trades)
        min_rr_ratio=1.2,
        preferred_rr_ratio=1.5,
        # Tighter stops (smaller losses, more frequent stops)
        stop_min_atr=0.3,
        stop_max_atr=2.0,
        stop_atr_swing=1.5,
        stop_atr_day=1.0,
        stop_atr_scalp=0.5,
        # Higher volatility tolerance
        volatility_high=4.0,
        # Trade even weak trends
        adx_trending=20.0,
        adx_no_trend=15.0,
        # Higher position sizing
        max_position_risk_pct=3.0,
        max_portfolio_heat=10.0,
        # More tolerant of conflicting signals
        max_conflicting_ratio=0.5,
    ),
    momentum=MomentumConfig(
        # Momentum more important for risky traders
        momentum_weight_in_score=0.25,
        momentum_confirmation_required=False,  # Don't require confirmation
        trend_momentum_bonus=15.0,
    ),
    signals=SignalConfig(
        max_signals_returned=75,  # See more signals
        max_trade_plans=5,  # Generate more trade ideas
        # Weight momentum and volume higher
        weight_technical=0.35,
        weight_momentum=0.25,
        weight_volume=0.20,
        weight_trend=0.10,
        weight_risk_reward=0.10,
    ),
)


# ============ NEUTRAL PROFILE ============
# Balanced approach for most traders (all default values)
NEUTRAL_CONFIG = UserConfig(
    risk_profile=RiskProfile.NEUTRAL,
    # All default values from base_config.py
)


# ============ AVERSE PROFILE ============
# Conservative approach prioritizing capital preservation
AVERSE_CONFIG = UserConfig(
    risk_profile=RiskProfile.AVERSE,
    indicators=IndicatorConfig(
        # More extreme RSI thresholds (wait for better entries)
        rsi_oversold=25.0,  # Wait for deeper oversold
        rsi_overbought=75.0,  # Let winners run longer
        rsi_extreme_oversold=15.0,
        rsi_extreme_overbought=85.0,
        # Wider Bollinger Bands (fewer false signals)
        bollinger_std=2.5,
        # Slower stochastic
        stochastic_k=21,
        stochastic_d=5,
    ),
    risk=RiskConfig(
        # Higher R:R required (better quality trades)
        min_rr_ratio=2.0,
        preferred_rr_ratio=3.0,
        max_rr_ratio=6.0,
        # Wider stops (give trades room to breathe)
        stop_min_atr=1.0,
        stop_max_atr=4.0,
        stop_atr_swing=2.5,
        stop_atr_day=2.0,
        stop_atr_scalp=1.5,
        # Lower volatility tolerance
        volatility_low=1.0,
        volatility_high=2.5,
        # Only trade strong trends
        adx_trending=30.0,
        adx_strong_trend=45.0,
        adx_no_trend=25.0,
        # Smaller position sizing
        max_position_risk_pct=1.0,
        max_portfolio_heat=4.0,
        # Less tolerant of conflicting signals
        max_conflicting_ratio=0.25,
        # Higher volume requirements
        min_volume_ratio=0.8,
    ),
    momentum=MomentumConfig(
        # Require momentum confirmation
        momentum_confirmation_required=True,
        momentum_weight_in_score=0.20,
        # Larger thresholds for "strong" momentum
        momentum_strong_threshold=4.0,
        # Bigger penalty for divergence
        trend_momentum_penalty=-10.0,
    ),
    signals=SignalConfig(
        max_signals_returned=30,  # Focus on fewer, higher-quality signals
        max_trade_plans=2,  # Only the best trade ideas
        # Weight trend and R:R higher
        weight_technical=0.35,
        weight_momentum=0.15,
        weight_volume=0.15,
        weight_trend=0.20,
        weight_risk_reward=0.15,
    ),
)


# Profile lookup
RISK_PROFILES = {
    RiskProfile.RISKY: RISKY_CONFIG,
    RiskProfile.NEUTRAL: NEUTRAL_CONFIG,
    RiskProfile.AVERSE: AVERSE_CONFIG,
}


def get_profile(profile: RiskProfile | str) -> UserConfig:
    """Get configuration for a risk profile.

    Args:
        profile: RiskProfile enum or string ("risky", "neutral", "averse")

    Returns:
        UserConfig for the specified profile
    """
    if isinstance(profile, str):
        profile = RiskProfile(profile)
    return RISK_PROFILES.get(profile, NEUTRAL_CONFIG)


def get_profile_with_overrides(
    profile: RiskProfile | str,
    overrides: dict[str, Any] | None = None,
) -> UserConfig:
    """Get profile with user-specific overrides applied.

    Args:
        profile: Base risk profile
        overrides: Dictionary of parameter overrides
            Example: {"rsi_oversold": 28, "min_rr_ratio": 1.8}

    Returns:
        UserConfig with overrides actually applied to nested dataclass fields

    Example:
        >>> config = get_profile_with_overrides("neutral", {"rsi_oversold": 28})
        >>> assert config.indicators.rsi_oversold == 28  # ACTUALLY CHANGED
    """
    base = get_profile(profile)

    if not overrides:
        return base

    # Separate overrides by nested config type
    indicator_overrides = {}
    risk_overrides = {}
    momentum_overrides = {}
    signal_overrides = {}

    for key, value in overrides.items():
        # Map override keys to their nested config sections
        if key.startswith("rsi_") or key.startswith("macd_") or key.startswith("bollinger_") or key.startswith("stochastic_") or key.startswith("adx_") or key.startswith("atr_") or key == "ma_periods":
            indicator_overrides[key] = value
        elif key.startswith("stop_") or key.startswith("volatility_") or key.startswith("adx_") or key in ["min_rr_ratio", "preferred_rr_ratio", "max_rr_ratio", "max_position_risk_pct", "max_portfolio_heat", "max_conflicting_ratio", "min_volume_ratio"]:
            risk_overrides[key] = value
        elif key.startswith("momentum_") or key.startswith("trend_"):
            momentum_overrides[key] = value
        elif key.startswith("weight_") or key in ["max_signals_returned", "max_trade_plans", "category_weights"]:
            signal_overrides[key] = value

    # Apply overrides to nested dataclasses using dataclasses.replace()
    new_indicators = replace(base.indicators, **indicator_overrides) if indicator_overrides else base.indicators
    new_risk = replace(base.risk, **risk_overrides) if risk_overrides else base.risk
    new_momentum = replace(base.momentum, **momentum_overrides) if momentum_overrides else base.momentum
    new_signals = replace(base.signals, **signal_overrides) if signal_overrides else base.signals

    # Create new UserConfig with applied overrides
    return UserConfig(
        risk_profile=base.risk_profile,
        indicators=new_indicators,
        risk=new_risk,
        momentum=new_momentum,
        signals=new_signals,
        custom_overrides=overrides,  # Track what was customized
    )
