"""Bridge between UserConfig and analysis functions.

This module adapts the UserConfig dataclass to work with the existing
signal detection and ranking code, ensuring configuration overrides
are actually applied throughout the analysis pipeline.
"""

import logging
from typing import Any
from dataclasses import dataclass

from .profiles.base_config import UserConfig
from . import config  # The module-level constants

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ConfigContext:
    """Context object that holds both UserConfig and the dynamic constants it generates.

    This bridges the configurable UserConfig with the hardcoded constants in the
    config module. Instead of using module-level constants directly, functions should
    use ConfigContext to get values that may have been overridden.
    """

    user_config: UserConfig

    # Indicator thresholds (from user_config.indicators)
    rsi_oversold: float
    rsi_overbought: float
    rsi_extreme_oversold: float
    rsi_extreme_overbought: float
    macd_fast: int
    macd_slow: int
    macd_signal: int
    bollinger_period: int
    bollinger_std: float
    stochastic_k: int
    stochastic_d: int
    adx_period: int
    atr_period: int

    # Risk thresholds (from user_config.risk)
    min_rr_ratio: float
    preferred_rr_ratio: float
    stop_min_atr: float
    stop_max_atr: float
    volatility_low: float
    volatility_high: float
    adx_trending: float
    adx_strong_trend: float
    max_position_risk_pct: float
    max_portfolio_heat: float
    max_conflicting_ratio: float
    min_volume_ratio: float

    # Signal thresholds (from user_config.signals)
    max_signals_returned: int
    max_trade_plans: int

    @classmethod
    def from_user_config(cls, user_config: UserConfig) -> "ConfigContext":
        """Create a ConfigContext from a UserConfig.

        Args:
            user_config: The user configuration with potential overrides applied

        Returns:
            ConfigContext with all values extracted from the UserConfig
        """
        return cls(
            user_config=user_config,
            # Indicators
            rsi_oversold=user_config.indicators.rsi_oversold,
            rsi_overbought=user_config.indicators.rsi_overbought,
            rsi_extreme_oversold=user_config.indicators.rsi_extreme_oversold,
            rsi_extreme_overbought=user_config.indicators.rsi_extreme_overbought,
            macd_fast=user_config.indicators.macd_fast,
            macd_slow=user_config.indicators.macd_slow,
            macd_signal=user_config.indicators.macd_signal,
            bollinger_period=user_config.indicators.bollinger_period,
            bollinger_std=user_config.indicators.bollinger_std,
            stochastic_k=user_config.indicators.stochastic_k,
            stochastic_d=user_config.indicators.stochastic_d,
            adx_period=user_config.indicators.adx_period,
            atr_period=user_config.indicators.atr_period,
            # Risk
            min_rr_ratio=user_config.risk.min_rr_ratio,
            preferred_rr_ratio=user_config.risk.preferred_rr_ratio,
            stop_min_atr=user_config.risk.stop_min_atr,
            stop_max_atr=user_config.risk.stop_max_atr,
            volatility_low=user_config.risk.volatility_low,
            volatility_high=user_config.risk.volatility_high,
            adx_trending=user_config.risk.adx_trending,
            adx_strong_trend=user_config.risk.adx_strong_trend,
            max_position_risk_pct=user_config.risk.max_position_risk_pct,
            max_portfolio_heat=user_config.risk.max_portfolio_heat,
            max_conflicting_ratio=user_config.risk.max_conflicting_ratio,
            min_volume_ratio=user_config.risk.min_volume_ratio,
            # Signals
            max_signals_returned=user_config.signals.max_signals_returned,
            max_trade_plans=user_config.signals.max_trade_plans,
        )

    @classmethod
    def default(cls) -> "ConfigContext":
        """Create a ConfigContext with default UserConfig.

        Returns:
            ConfigContext with all default values
        """
        return cls.from_user_config(UserConfig())


def get_config_context(user_config: UserConfig | None = None) -> ConfigContext:
    """Get a ConfigContext, using provided config or default.

    This is the main entry point for getting a context-aware configuration
    that's been validated and properly set up.

    Args:
        user_config: Optional UserConfig with overrides applied.
                    If None, uses default configuration.

    Returns:
        ConfigContext ready to use in analysis functions
    """
    if user_config is None:
        return ConfigContext.default()
    return ConfigContext.from_user_config(user_config)


# ============================================================================
# Compatibility Functions - Use these to replace module-level constant access
# ============================================================================

def get_rsi_oversold(ctx: ConfigContext | None = None) -> float:
    """Get RSI oversold threshold, respecting user config overrides."""
    if ctx:
        return ctx.rsi_oversold
    return config.RSI_OVERSOLD


def get_rsi_overbought(ctx: ConfigContext | None = None) -> float:
    """Get RSI overbought threshold, respecting user config overrides."""
    if ctx:
        return ctx.rsi_overbought
    return config.RSI_OVERBOUGHT


def get_rsi_extreme_oversold(ctx: ConfigContext | None = None) -> float:
    """Get RSI extreme oversold threshold, respecting user config overrides."""
    if ctx:
        return ctx.rsi_extreme_oversold
    return config.RSI_EXTREME_OVERSOLD


def get_rsi_extreme_overbought(ctx: ConfigContext | None = None) -> float:
    """Get RSI extreme overbought threshold, respecting user config overrides."""
    if ctx:
        return ctx.rsi_extreme_overbought
    return config.RSI_EXTREME_OVERBOUGHT


def get_adx_trending(ctx: ConfigContext | None = None) -> float:
    """Get ADX trending threshold, respecting user config overrides."""
    if ctx:
        return ctx.adx_trending
    return config.ADX_TRENDING


def get_max_signals_returned(ctx: ConfigContext | None = None) -> int:
    """Get max signals limit, respecting user config overrides."""
    if ctx:
        return ctx.max_signals_returned
    return config.MAX_SIGNALS_RETURNED


# ============================================================================
# Validation Functions
# ============================================================================

def validate_config_context(ctx: ConfigContext) -> tuple[bool, list[str]]:
    """Validate that a ConfigContext has sensible values.

    Args:
        ctx: ConfigContext to validate

    Returns:
        Tuple of (is_valid, list of validation errors)
    """
    errors = []

    # RSI bounds
    if not (0 < ctx.rsi_extreme_oversold < ctx.rsi_oversold < 50):
        errors.append(
            f"RSI oversold sequence invalid: "
            f"extreme_oversold={ctx.rsi_extreme_oversold}, "
            f"oversold={ctx.rsi_oversold}"
        )

    if not (50 < ctx.rsi_overbought < ctx.rsi_extreme_overbought < 100):
        errors.append(
            f"RSI overbought sequence invalid: "
            f"overbought={ctx.rsi_overbought}, "
            f"extreme_overbought={ctx.rsi_extreme_overbought}"
        )

    # Risk-reward ratio
    if ctx.min_rr_ratio <= 0 or ctx.preferred_rr_ratio <= 0:
        errors.append("R:R ratios must be positive")

    if ctx.min_rr_ratio > ctx.preferred_rr_ratio:
        errors.append("min_rr_ratio must be <= preferred_rr_ratio")

    # Stop distances
    if ctx.stop_min_atr > ctx.stop_max_atr:
        errors.append("stop_min_atr must be <= stop_max_atr")

    # Volatility
    if ctx.volatility_low > ctx.volatility_high:
        errors.append("volatility_low must be <= volatility_high")

    # ADX
    if ctx.adx_trending > ctx.adx_strong_trend:
        errors.append("adx_trending must be <= adx_strong_trend")

    # Position sizing
    if ctx.max_position_risk_pct <= 0 or ctx.max_portfolio_heat <= 0:
        errors.append("Position sizing percentages must be positive")

    # Signal limits
    if ctx.max_signals_returned <= 0 or ctx.max_trade_plans <= 0:
        errors.append("Signal limits must be positive")

    return (len(errors) == 0, errors)
