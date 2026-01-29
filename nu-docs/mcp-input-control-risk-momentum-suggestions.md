# MCP Finance: User Input Control, Risk Profiles & Momentum Integration

## Executive Summary

This document proposes a comprehensive enhancement to the MCP Finance system that enables:
1. **Wide-range user control** over all 9 MCP server inputs
2. **Risk profile-based recommendations** (Risky, Risk-Neutral, Risk-Averse)
3. **Momentum tracking** integrated into signal generation
4. **Central backend configuration** for testing before frontend deployment

---

## Table of Contents

1. [Current State Analysis](#1-current-state-analysis)
2. [Central Configuration Architecture](#2-central-configuration-architecture)
3. [Risk Profile System](#3-risk-profile-system)
4. [Momentum Tracking Enhancement](#4-momentum-tracking-enhancement)
5. [User Input Control by MCP Server](#5-user-input-control-by-mcp-server)
6. [Backend Testing Framework](#6-backend-testing-framework)
7. [Implementation Roadmap](#7-implementation-roadmap)
8. [API Contract Examples](#8-api-contract-examples)

---

## 1. Current State Analysis

### 1.1 Existing Configuration (`config.py`)

**Currently Hardcoded Parameters:**
```python
# Indicator Settings
RSI_PERIOD = 14
RSI_OVERSOLD = 30.0
RSI_OVERBOUGHT = 70.0
MACD_FAST = 12, MACD_SLOW = 26, MACD_SIGNAL = 9
BOLLINGER_PERIOD = 20, BOLLINGER_STD = 2.0
ADX_PERIOD = 14

# Risk Settings
MIN_RR_RATIO = 1.5              # Minimum risk:reward
STOP_MIN_ATR_MULTIPLE = 0.5     # Minimum stop distance
STOP_MAX_ATR_MULTIPLE = 3.0     # Maximum stop distance
ADX_TRENDING_THRESHOLD = 25.0   # Trend confirmation
VOLATILITY_HIGH_THRESHOLD = 3.0 # High volatility regime
```

**Problems:**
- No user-configurable risk tolerance
- Fixed thresholds don't adapt to different trading styles
- Momentum not weighted in signal scoring
- No central config for A/B testing different settings

### 1.2 The 9 MCP Servers & Current Inputs

| Server | Current Inputs | Missing User Controls |
|--------|----------------|----------------------|
| `analyze_security` | symbol, period, use_ai | Risk profile, custom RSI/MACD thresholds |
| `compare_securities` | symbols[], metric, period | Risk-adjusted comparison, momentum weighting |
| `screen_securities` | universe, criteria, limit | Risk profile filters, momentum criteria |
| `get_trade_plan` | symbol, period | Risk tolerance, position sizing hints |
| `scan_trades` | universe, max_results, period | Risk profile, momentum filters |
| `portfolio_risk` | positions[], period | Risk tolerance, hedge aggressiveness |
| `morning_brief` | watchlist[], region, period | Risk profile summary, momentum highlights |
| `analyze_fibonacci` | symbol, period, window | Risk-adjusted level significance |
| `options_risk_analysis` | symbol, expiration, type | Risk profile option strategies |

---

## 2. Central Configuration Architecture

### 2.1 Configuration Hierarchy

```
┌─────────────────────────────────────────────────────────────────┐
│                    USER PROFILE LAYER                          │
│  (Per-user preferences stored in database)                     │
│  - risk_profile: "risky" | "neutral" | "averse"                │
│  - custom_overrides: { RSI_OVERSOLD: 25, ... }                 │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                  RISK PROFILE PRESETS                          │
│  (Backend presets per risk tolerance)                          │
│  - RISKY_CONFIG: aggressive thresholds                         │
│  - NEUTRAL_CONFIG: balanced thresholds                         │
│  - AVERSE_CONFIG: conservative thresholds                      │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    DEFAULT CONFIG                              │
│  (Existing config.py - fallback)                               │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 New Configuration Files

#### `src/technical_analysis_mcp/profiles/base_config.py`

```python
"""Base configuration with all configurable parameters."""

from dataclasses import dataclass, field
from typing import Dict, Any, Literal
from enum import Enum


class RiskProfile(str, Enum):
    """User risk tolerance profiles."""
    RISKY = "risky"           # Aggressive, higher risk tolerance
    NEUTRAL = "neutral"       # Balanced approach
    AVERSE = "averse"         # Conservative, capital preservation


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
    min_rr_ratio: float = 1.5           # Minimum acceptable R:R
    preferred_rr_ratio: float = 2.0     # Target R:R
    max_rr_ratio: float = 5.0           # Cap for unrealistic targets

    # Stop-Loss Settings (ATR multiples)
    stop_min_atr: float = 0.5           # Minimum stop distance
    stop_max_atr: float = 3.0           # Maximum stop distance
    stop_atr_swing: float = 2.0         # Swing trade stop
    stop_atr_day: float = 1.5           # Day trade stop
    stop_atr_scalp: float = 1.0         # Scalp trade stop

    # Volatility Thresholds
    volatility_low: float = 1.5         # Low volatility ceiling
    volatility_high: float = 3.0        # High volatility floor

    # Trend Requirements
    adx_trending: float = 25.0          # Trending threshold
    adx_strong_trend: float = 40.0      # Strong trend threshold
    adx_no_trend: float = 20.0          # No trend ceiling

    # Position Sizing Hints
    max_position_risk_pct: float = 2.0  # Max risk per trade (% of portfolio)
    max_portfolio_heat: float = 6.0     # Max total open risk (%)

    # Suppression Thresholds
    max_conflicting_ratio: float = 0.4  # Max bullish/bearish conflict
    min_volume_ratio: float = 0.5       # Min volume vs 20-day average


@dataclass(frozen=True)
class MomentumConfig:
    """Momentum tracking configuration."""

    # Momentum Calculation
    momentum_period: int = 5            # Lookback bars for momentum
    momentum_strong_threshold: float = 3.0   # Strong momentum %
    momentum_stall_threshold: float = 0.5    # Momentum stall %

    # Momentum Signal Weighting
    momentum_weight_in_score: float = 0.15   # Weight in overall signal score
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
    weight_technical: float = 0.40      # Technical signal weight
    weight_momentum: float = 0.20       # Momentum weight
    weight_volume: float = 0.15         # Volume confirmation weight
    weight_trend: float = 0.15          # Trend strength weight
    weight_risk_reward: float = 0.10    # R:R quality weight

    # Signal Category Priorities
    category_weights: Dict[str, float] = field(default_factory=lambda: {
        "MA_CROSS": 1.2,
        "MACD": 1.1,
        "RSI": 1.0,
        "VOLUME": 1.0,
        "BOLLINGER": 0.9,
        "STOCHASTIC": 0.9,
        "TREND": 0.8,
        "PRICE_ACTION": 0.7,
    })


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
```

#### `src/technical_analysis_mcp/profiles/risk_profiles.py`

```python
"""Pre-defined risk profile configurations."""

from .base_config import (
    UserConfig, RiskProfile, IndicatorConfig,
    RiskConfig, MomentumConfig, SignalConfig
)


# ============ RISKY PROFILE ============
# For aggressive traders seeking higher returns with higher risk tolerance
RISKY_CONFIG = UserConfig(
    risk_profile=RiskProfile.RISKY,
    indicators=IndicatorConfig(
        # More sensitive RSI thresholds (enter earlier)
        rsi_oversold=35.0,           # Enter sooner on dips
        rsi_overbought=65.0,         # Exit sooner on rallies
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
        max_signals_returned=75,      # See more signals
        max_trade_plans=5,            # Generate more trade ideas
        # Weight momentum and volume higher
        weight_technical=0.35,
        weight_momentum=0.25,
        weight_volume=0.20,
        weight_trend=0.10,
        weight_risk_reward=0.10,
    ),
)


# ============ NEUTRAL PROFILE ============
# Balanced approach for most traders
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
        rsi_oversold=25.0,           # Wait for deeper oversold
        rsi_overbought=75.0,         # Let winners run longer
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
        max_signals_returned=30,      # Focus on fewer, higher-quality signals
        max_trade_plans=2,            # Only the best trade ideas
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
    """Get configuration for a risk profile."""
    if isinstance(profile, str):
        profile = RiskProfile(profile)
    return RISK_PROFILES.get(profile, NEUTRAL_CONFIG)


def get_profile_with_overrides(
    profile: RiskProfile | str,
    overrides: dict[str, Any] | None = None,
) -> UserConfig:
    """Get profile with user-specific overrides applied."""
    base = get_profile(profile)

    if not overrides:
        return base

    # Create new config with overrides
    # (Implementation depends on how granular overrides need to be)
    return UserConfig(
        risk_profile=base.risk_profile,
        indicators=base.indicators,
        risk=base.risk,
        momentum=base.momentum,
        signals=base.signals,
        custom_overrides=overrides,
    )
```

### 2.3 Configuration Manager

```python
# src/technical_analysis_mcp/profiles/config_manager.py

"""Central configuration management with caching and validation."""

from typing import Optional, Dict, Any
from dataclasses import asdict
import json
import logging

from .base_config import UserConfig, RiskProfile
from .risk_profiles import get_profile, get_profile_with_overrides

logger = logging.getLogger(__name__)


class ConfigManager:
    """Manages user configurations with caching and validation."""

    def __init__(self):
        self._cache: Dict[str, UserConfig] = {}
        self._session_overrides: Dict[str, Dict[str, Any]] = {}

    def get_config(
        self,
        user_id: Optional[str] = None,
        risk_profile: RiskProfile | str = RiskProfile.NEUTRAL,
        session_overrides: Optional[Dict[str, Any]] = None,
    ) -> UserConfig:
        """Get effective configuration for a user/session.

        Priority:
        1. Session overrides (temporary, per-request)
        2. User saved preferences (from database)
        3. Risk profile preset
        4. Default config

        Args:
            user_id: User identifier for saved preferences
            risk_profile: Base risk profile to use
            session_overrides: Temporary overrides for this request

        Returns:
            Complete UserConfig with all overrides applied
        """
        # Start with risk profile preset
        config = get_profile(risk_profile)

        # Apply user saved preferences (if user_id provided)
        if user_id:
            user_prefs = self._load_user_preferences(user_id)
            if user_prefs:
                config = get_profile_with_overrides(
                    risk_profile,
                    user_prefs
                )

        # Apply session overrides (temporary, per-request)
        if session_overrides:
            config = get_profile_with_overrides(
                config.risk_profile,
                {**config.custom_overrides, **session_overrides}
            )

        return config

    def set_session_override(
        self,
        session_id: str,
        key: str,
        value: Any,
    ) -> None:
        """Set a temporary session override."""
        if session_id not in self._session_overrides:
            self._session_overrides[session_id] = {}
        self._session_overrides[session_id][key] = value
        logger.info(f"Session override set: {session_id}.{key} = {value}")

    def clear_session_overrides(self, session_id: str) -> None:
        """Clear all session overrides."""
        self._session_overrides.pop(session_id, None)

    def _load_user_preferences(
        self,
        user_id: str
    ) -> Optional[Dict[str, Any]]:
        """Load user preferences from database/cache.

        TODO: Implement database integration
        """
        return self._cache.get(user_id, {}).custom_overrides

    def save_user_preferences(
        self,
        user_id: str,
        preferences: Dict[str, Any],
    ) -> None:
        """Save user preferences.

        TODO: Implement database persistence
        """
        logger.info(f"Saving preferences for user {user_id}: {preferences}")
        # For now, just cache
        if user_id not in self._cache:
            self._cache[user_id] = get_profile(RiskProfile.NEUTRAL)
        # Merge preferences
        # TODO: Proper database save

    def export_config(self, config: UserConfig) -> Dict[str, Any]:
        """Export configuration as dictionary (for API responses)."""
        return asdict(config)

    def validate_overrides(
        self,
        overrides: Dict[str, Any]
    ) -> tuple[bool, list[str]]:
        """Validate user-provided overrides.

        Returns:
            Tuple of (is_valid, list of validation errors)
        """
        errors = []

        # RSI bounds check
        if "rsi_oversold" in overrides:
            if not 0 < overrides["rsi_oversold"] < 50:
                errors.append("rsi_oversold must be between 0 and 50")

        if "rsi_overbought" in overrides:
            if not 50 < overrides["rsi_overbought"] < 100:
                errors.append("rsi_overbought must be between 50 and 100")

        # R:R bounds check
        if "min_rr_ratio" in overrides:
            if not 0.5 <= overrides["min_rr_ratio"] <= 5.0:
                errors.append("min_rr_ratio must be between 0.5 and 5.0")

        # Stop ATR bounds
        if "stop_max_atr" in overrides:
            if not 1.0 <= overrides["stop_max_atr"] <= 10.0:
                errors.append("stop_max_atr must be between 1.0 and 10.0")

        # Momentum weight
        if "momentum_weight_in_score" in overrides:
            if not 0.0 <= overrides["momentum_weight_in_score"] <= 0.5:
                errors.append("momentum_weight must be between 0 and 0.5")

        return (len(errors) == 0, errors)


# Global singleton
_config_manager = ConfigManager()

def get_config_manager() -> ConfigManager:
    """Get the global configuration manager."""
    return _config_manager
```

---

## 3. Risk Profile System

### 3.1 Risk Profile Comparison

| Parameter | Risky | Neutral | Averse |
|-----------|-------|---------|--------|
| **RSI Oversold** | 35 | 30 | 25 |
| **RSI Overbought** | 65 | 70 | 75 |
| **Min R:R Ratio** | 1.2:1 | 1.5:1 | 2.0:1 |
| **Stop ATR (Swing)** | 1.5 ATR | 2.0 ATR | 2.5 ATR |
| **Volatility Tolerance** | High (4%) | Medium (3%) | Low (2.5%) |
| **ADX Trending** | 20 | 25 | 30 |
| **Position Risk** | 3% | 2% | 1% |
| **Portfolio Heat** | 10% | 6% | 4% |
| **Signal Conflict Tolerance** | 50% | 40% | 25% |
| **Momentum Weight** | 25% | 20% | 20% |
| **Max Trade Plans** | 5 | 3 | 2 |

### 3.2 Risk Profile Selection Flow

```
┌─────────────────────────────────────────────────────────────┐
│                     USER SELECTION                         │
│                                                             │
│   ┌─────────┐    ┌─────────────┐    ┌────────────┐         │
│   │  RISKY  │    │   NEUTRAL   │    │   AVERSE   │         │
│   │         │    │  (default)  │    │            │         │
│   │ Higher  │    │  Balanced   │    │ Capital    │         │
│   │ returns │    │  approach   │    │ preserve   │         │
│   └────┬────┘    └──────┬──────┘    └─────┬──────┘         │
│        │               │                  │                │
└────────┼───────────────┼──────────────────┼────────────────┘
         │               │                  │
         ▼               ▼                  ▼
┌─────────────────────────────────────────────────────────────┐
│                  LOAD PROFILE CONFIG                        │
│                                                             │
│   RISKY_CONFIG     NEUTRAL_CONFIG     AVERSE_CONFIG        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
         │               │                  │
         └───────────────┼──────────────────┘
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                APPLY USER OVERRIDES                         │
│                                                             │
│   User's custom_overrides dict merged with profile         │
│   Example: { "rsi_oversold": 28, "min_rr_ratio": 1.8 }     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              EFFECTIVE CONFIGURATION                        │
│                                                             │
│   Complete UserConfig used by all 9 MCP servers            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 3.3 Risk-Adjusted Signal Output

```python
# Example output showing risk profile impact

# RISKY profile analysis of AAPL
{
    "symbol": "AAPL",
    "risk_profile": "risky",
    "risk_profile_impact": {
        "trades_found": 5,              # More trades shown
        "avg_rr_ratio": 1.4,            # Lower R:R accepted
        "volatility_regime": "medium",   # Would be "high" for neutral
        "signals_shown": 75,            # More signals visible
    },
    "trade_plans": [
        {
            "bias": "bullish",
            "entry": 185.50,
            "stop": 183.25,              # Tighter stop (1.5 ATR)
            "target": 188.20,
            "risk_reward": 1.2,          # Acceptable for risky
            "position_risk_pct": 2.5,    # Larger position allowed
            "risk_profile_note": "Trade qualifies under RISKY profile; would be suppressed under NEUTRAL (R:R < 1.5)"
        }
    ]
}

# AVERSE profile analysis of same AAPL
{
    "symbol": "AAPL",
    "risk_profile": "averse",
    "risk_profile_impact": {
        "trades_found": 1,              # Fewer, higher quality
        "avg_rr_ratio": 2.3,            # Higher R:R required
        "volatility_regime": "high",     # More cautious classification
        "signals_shown": 30,            # Focus on strongest signals
    },
    "trade_plans": [
        {
            "bias": "bullish",
            "entry": 184.00,             # Wait for better entry
            "stop": 180.00,              # Wider stop (2.5 ATR)
            "target": 192.00,
            "risk_reward": 2.0,          # Meets higher threshold
            "position_risk_pct": 1.0,    # Smaller position
            "risk_profile_note": "Trade qualifies under AVERSE profile with strong momentum confirmation"
        }
    ],
    "suppressed_trades": [
        {
            "reason": "R:R below 2.0 threshold",
            "would_qualify_under": ["risky", "neutral"]
        }
    ]
}
```

---

## 4. Momentum Tracking Enhancement

### 4.1 Current Momentum State

**Existing** (in `fibonacci/signals/momentum.py`):
- 5-bar momentum calculation
- Only used at Fibonacci levels
- Not integrated into main signal scoring

**Gaps**:
- Momentum not considered in `analyze_security`
- No momentum filter in `scan_trades`
- No trend-momentum divergence detection
- No momentum weighting in signal ranking

### 4.2 Enhanced Momentum Module

```python
# src/technical_analysis_mcp/momentum/calculator.py

"""Enhanced momentum calculation and tracking."""

from dataclasses import dataclass
from enum import Enum
from typing import Optional
import pandas as pd
import numpy as np


class MomentumState(str, Enum):
    """Momentum classification states."""
    STRONG_UP = "strong_up"           # > +3% (configurable)
    UP = "up"                         # +1% to +3%
    STALL = "stall"                   # -0.5% to +0.5%
    DOWN = "down"                     # -3% to -1%
    STRONG_DOWN = "strong_down"       # < -3%


class MomentumTrend(str, Enum):
    """Multi-period momentum trend."""
    ACCELERATING_UP = "accelerating_up"     # Momentum increasing positive
    DECELERATING_UP = "decelerating_up"     # Momentum positive but slowing
    REVERSING_UP = "reversing_up"           # Negative momentum turning positive
    ACCELERATING_DOWN = "accelerating_down" # Momentum increasing negative
    DECELERATING_DOWN = "decelerating_down" # Momentum negative but improving
    REVERSING_DOWN = "reversing_down"       # Positive momentum turning negative
    FLAT = "flat"                           # No clear momentum trend


@dataclass(frozen=True)
class MomentumResult:
    """Complete momentum analysis result."""

    # Current momentum
    momentum_pct: float                      # Raw momentum %
    momentum_state: MomentumState            # Classified state

    # Multi-period momentum
    momentum_5: float                        # 5-bar momentum
    momentum_10: float                       # 10-bar momentum
    momentum_20: float                       # 20-bar momentum
    momentum_trend: MomentumTrend            # Overall trend

    # Momentum quality
    momentum_consistency: float              # 0-1, how consistent
    momentum_strength: float                 # Normalized 0-100

    # Divergence detection
    price_trend: str                         # "up", "down", "flat"
    has_divergence: bool                     # Momentum vs price divergence
    divergence_type: Optional[str]           # "bullish", "bearish", None

    # Signal integration
    signal_modifier: float                   # Score modifier (-20 to +20)
    confirmation_status: str                 # "confirmed", "divergent", "neutral"


class MomentumCalculator:
    """Calculate and track momentum across multiple timeframes."""

    def __init__(
        self,
        strong_threshold: float = 3.0,
        stall_threshold: float = 0.5,
        periods: tuple[int, ...] = (5, 10, 20),
    ):
        self.strong_threshold = strong_threshold
        self.stall_threshold = stall_threshold
        self.periods = periods

    def calculate(self, df: pd.DataFrame) -> MomentumResult:
        """Calculate comprehensive momentum analysis.

        Args:
            df: DataFrame with 'Close' column

        Returns:
            MomentumResult with all momentum metrics
        """
        close = df["Close"]

        # Calculate momentum for each period
        momentum_values = {}
        for period in self.periods:
            if len(close) >= period + 1:
                mom = (close.iloc[-1] - close.iloc[-period-1]) / close.iloc[-period-1] * 100
                momentum_values[period] = mom
            else:
                momentum_values[period] = 0.0

        # Primary momentum (shortest period)
        primary_period = self.periods[0]
        momentum_pct = momentum_values.get(primary_period, 0.0)

        # Classify state
        momentum_state = self._classify_state(momentum_pct)

        # Calculate momentum trend (comparing periods)
        momentum_trend = self._calculate_trend(momentum_values)

        # Calculate consistency (how aligned are different periods)
        consistency = self._calculate_consistency(momentum_values)

        # Normalize strength (0-100)
        strength = min(100, abs(momentum_pct) / self.strong_threshold * 50 + 50)

        # Detect price trend
        price_trend = self._detect_price_trend(close)

        # Check for divergence
        has_divergence, divergence_type = self._detect_divergence(
            momentum_pct, price_trend
        )

        # Calculate signal modifier
        signal_modifier = self._calculate_modifier(
            momentum_state, momentum_trend, has_divergence
        )

        # Determine confirmation status
        confirmation_status = self._get_confirmation_status(
            momentum_state, price_trend, has_divergence
        )

        return MomentumResult(
            momentum_pct=momentum_pct,
            momentum_state=momentum_state,
            momentum_5=momentum_values.get(5, 0.0),
            momentum_10=momentum_values.get(10, 0.0),
            momentum_20=momentum_values.get(20, 0.0),
            momentum_trend=momentum_trend,
            momentum_consistency=consistency,
            momentum_strength=strength,
            price_trend=price_trend,
            has_divergence=has_divergence,
            divergence_type=divergence_type,
            signal_modifier=signal_modifier,
            confirmation_status=confirmation_status,
        )

    def _classify_state(self, momentum_pct: float) -> MomentumState:
        """Classify momentum into state."""
        if momentum_pct > self.strong_threshold:
            return MomentumState.STRONG_UP
        elif momentum_pct > self.stall_threshold:
            return MomentumState.UP
        elif momentum_pct < -self.strong_threshold:
            return MomentumState.STRONG_DOWN
        elif momentum_pct < -self.stall_threshold:
            return MomentumState.DOWN
        else:
            return MomentumState.STALL

    def _calculate_trend(
        self,
        momentum_values: dict[int, float]
    ) -> MomentumTrend:
        """Determine momentum trend from multi-period values."""
        if len(momentum_values) < 2:
            return MomentumTrend.FLAT

        periods = sorted(momentum_values.keys())
        short = momentum_values[periods[0]]
        long = momentum_values[periods[-1]]

        # Both positive
        if short > 0 and long > 0:
            if short > long:
                return MomentumTrend.ACCELERATING_UP
            else:
                return MomentumTrend.DECELERATING_UP

        # Both negative
        if short < 0 and long < 0:
            if short < long:
                return MomentumTrend.ACCELERATING_DOWN
            else:
                return MomentumTrend.DECELERATING_DOWN

        # Crossover
        if short > 0 and long < 0:
            return MomentumTrend.REVERSING_UP
        if short < 0 and long > 0:
            return MomentumTrend.REVERSING_DOWN

        return MomentumTrend.FLAT

    def _calculate_consistency(
        self,
        momentum_values: dict[int, float]
    ) -> float:
        """Calculate how consistent momentum is across periods."""
        values = list(momentum_values.values())
        if len(values) < 2:
            return 1.0

        # Check if all same sign
        all_positive = all(v > 0 for v in values)
        all_negative = all(v < 0 for v in values)

        if all_positive or all_negative:
            # Calculate variance as inconsistency measure
            variance = np.var(values)
            mean = abs(np.mean(values))
            if mean > 0:
                cv = variance / mean  # Coefficient of variation
                return max(0, 1 - cv / 10)  # Normalize
            return 1.0
        else:
            # Mixed signs = lower consistency
            return 0.3

    def _detect_price_trend(self, close: pd.Series) -> str:
        """Detect price trend direction."""
        if len(close) < 20:
            return "flat"

        # Simple trend: compare current to 20-period SMA
        sma20 = close.rolling(20).mean().iloc[-1]
        current = close.iloc[-1]

        pct_from_sma = (current - sma20) / sma20 * 100

        if pct_from_sma > 2:
            return "up"
        elif pct_from_sma < -2:
            return "down"
        return "flat"

    def _detect_divergence(
        self,
        momentum_pct: float,
        price_trend: str,
    ) -> tuple[bool, Optional[str]]:
        """Detect momentum/price divergence."""
        # Bullish divergence: price down but momentum turning up
        if price_trend == "down" and momentum_pct > 0:
            return True, "bullish"

        # Bearish divergence: price up but momentum turning down
        if price_trend == "up" and momentum_pct < 0:
            return True, "bearish"

        return False, None

    def _calculate_modifier(
        self,
        state: MomentumState,
        trend: MomentumTrend,
        has_divergence: bool,
    ) -> float:
        """Calculate signal score modifier based on momentum."""
        modifier = 0.0

        # State contribution
        state_modifiers = {
            MomentumState.STRONG_UP: 10.0,
            MomentumState.UP: 5.0,
            MomentumState.STALL: 0.0,
            MomentumState.DOWN: -5.0,
            MomentumState.STRONG_DOWN: -10.0,
        }
        modifier += state_modifiers.get(state, 0.0)

        # Trend contribution
        trend_modifiers = {
            MomentumTrend.ACCELERATING_UP: 5.0,
            MomentumTrend.DECELERATING_UP: 2.0,
            MomentumTrend.REVERSING_UP: 8.0,    # Potential reversal signal
            MomentumTrend.ACCELERATING_DOWN: -5.0,
            MomentumTrend.DECELERATING_DOWN: -2.0,
            MomentumTrend.REVERSING_DOWN: -8.0,
        }
        modifier += trend_modifiers.get(trend, 0.0)

        # Divergence warning (for signals going against divergence)
        if has_divergence:
            modifier *= 0.7  # Reduce modifier if divergence detected

        return max(-20, min(20, modifier))

    def _get_confirmation_status(
        self,
        state: MomentumState,
        price_trend: str,
        has_divergence: bool,
    ) -> str:
        """Get momentum confirmation status for signals."""
        if has_divergence:
            return "divergent"

        # Check alignment
        bullish_momentum = state in (MomentumState.STRONG_UP, MomentumState.UP)
        bearish_momentum = state in (MomentumState.STRONG_DOWN, MomentumState.DOWN)

        if (bullish_momentum and price_trend == "up") or \
           (bearish_momentum and price_trend == "down"):
            return "confirmed"

        return "neutral"
```

### 4.3 Momentum Integration into Signal Ranking

```python
# src/technical_analysis_mcp/ranking.py (enhanced)

def rank_signals_with_momentum(
    signals: list[Signal],
    momentum: MomentumResult,
    config: UserConfig,
) -> list[RankedSignal]:
    """Rank signals with momentum integration.

    Args:
        signals: Raw detected signals
        momentum: Momentum analysis result
        config: User configuration with weights

    Returns:
        Signals with momentum-adjusted scores
    """
    ranked = []

    for signal in signals:
        # Base score from rule-based ranking
        base_score = calculate_base_score(signal)

        # Momentum adjustment
        momentum_adjustment = 0.0

        # Check signal alignment with momentum
        signal_bullish = signal.strength in ("STRONG_BULLISH", "BULLISH")
        signal_bearish = signal.strength in ("STRONG_BEARISH", "BEARISH")
        momentum_bullish = momentum.momentum_state in (
            MomentumState.STRONG_UP,
            MomentumState.UP
        )
        momentum_bearish = momentum.momentum_state in (
            MomentumState.STRONG_DOWN,
            MomentumState.DOWN
        )

        # Alignment bonus
        if (signal_bullish and momentum_bullish) or \
           (signal_bearish and momentum_bearish):
            momentum_adjustment += config.momentum.trend_momentum_bonus

        # Divergence penalty
        if (signal_bullish and momentum_bearish) or \
           (signal_bearish and momentum_bullish):
            momentum_adjustment += config.momentum.trend_momentum_penalty

        # Apply momentum weight
        weighted_momentum = momentum_adjustment * config.momentum.momentum_weight_in_score

        # Final score
        final_score = base_score + weighted_momentum + momentum.signal_modifier
        final_score = max(0, min(100, final_score))

        # Check momentum confirmation requirement
        if config.momentum.momentum_confirmation_required:
            if momentum.confirmation_status != "confirmed":
                final_score *= 0.7  # Penalize unconfirmed signals

        ranked.append(RankedSignal(
            signal=signal,
            score=final_score,
            momentum_impact=weighted_momentum,
            momentum_status=momentum.confirmation_status,
        ))

    # Sort by score descending
    ranked.sort(key=lambda x: x.score, reverse=True)

    return ranked[:config.signals.max_signals_returned]
```

### 4.4 Momentum in Signal Output

```python
# Example output with momentum tracking

{
    "symbol": "NVDA",
    "momentum": {
        "current_pct": 4.2,
        "state": "strong_up",
        "5_bar": 4.2,
        "10_bar": 6.8,
        "20_bar": 12.3,
        "trend": "decelerating_up",     # Still up but slowing
        "consistency": 0.85,
        "strength": 78,
        "confirmation_status": "confirmed",
        "divergence": null
    },
    "signals": [
        {
            "name": "RSI Bullish Momentum",
            "base_score": 65,
            "momentum_impact": +8,       # Aligned with strong up momentum
            "final_score": 73,
            "momentum_note": "Signal confirmed by strong upward momentum"
        },
        {
            "name": "MACD Bear Cross",
            "base_score": 70,
            "momentum_impact": -12,      # Conflicts with up momentum
            "final_score": 58,
            "momentum_note": "Caution: Signal conflicts with current momentum"
        }
    ],
    "momentum_summary": {
        "bias_impact": "Bullish signals boosted, bearish signals penalized",
        "trend_warning": "Momentum decelerating - watch for reversal",
        "recommendation": "Favor bullish setups with momentum confirmation"
    }
}
```

---

## 5. User Input Control by MCP Server

### 5.1 Input Control Matrix

| MCP Server | New User Inputs | Risk Profile Impact |
|------------|-----------------|---------------------|
| **analyze_security** | risk_profile, custom_rsi, custom_macd, momentum_weight | Thresholds, signal count, scoring |
| **compare_securities** | risk_profile, comparison_metric, momentum_filter | Ranking criteria, trade quality bar |
| **screen_securities** | risk_profile, rsi_range, rr_min, momentum_state | Filter criteria, result count |
| **get_trade_plan** | risk_profile, stop_atr, target_rr, position_size | Stop/target calc, suppression rules |
| **scan_trades** | risk_profile, momentum_filter, min_score | Trade quality bar, suppression |
| **portfolio_risk** | risk_profile, max_heat, hedge_aggressiveness | Risk limits, hedge suggestions |
| **morning_brief** | risk_profile, highlight_momentum, focus_sectors | Content emphasis |
| **analyze_fibonacci** | risk_profile, momentum_at_levels | Level significance weighting |
| **options_risk_analysis** | risk_profile, max_loss_pct, strategy_type | Strategy filtering, Greeks thresholds |

### 5.2 Updated Server Signatures

#### `analyze_security`

```python
async def analyze_security(
    symbol: str,
    period: str = "1mo",
    use_ai: bool = False,
    # NEW PARAMETERS:
    risk_profile: str = "neutral",       # "risky", "neutral", "averse"
    price_override: float | None = None,  # Manual price injection
    custom_config: dict | None = None,    # Override specific settings
    include_momentum: bool = True,        # Include momentum analysis
) -> dict[str, Any]:
    """Analyze security with configurable risk profile and momentum.

    Args:
        symbol: Ticker symbol
        period: Analysis period
        use_ai: Enable AI ranking
        risk_profile: User's risk tolerance ("risky", "neutral", "averse")
        price_override: Manual price for what-if analysis
        custom_config: Override specific config values
            - rsi_oversold: float (10-45)
            - rsi_overbought: float (55-90)
            - min_rr_ratio: float (0.5-5.0)
            - momentum_weight: float (0-0.5)
        include_momentum: Include momentum tracking in response

    Returns:
        Analysis with risk-profile-adjusted signals and momentum
    """
```

#### `get_trade_plan`

```python
async def get_trade_plan(
    symbol: str,
    period: str = "1mo",
    # NEW PARAMETERS:
    risk_profile: str = "neutral",
    timeframe: str | None = None,        # Force "swing", "day", "scalp"
    stop_atr_multiple: float | None = None,  # Override stop distance
    target_rr_ratio: float | None = None,    # Override target R:R
    max_position_risk_pct: float | None = None,  # Position sizing hint
    require_momentum_confirmation: bool | None = None,
) -> dict[str, Any]:
    """Generate trade plan with risk-profile-adjusted parameters.

    Args:
        symbol: Ticker symbol
        period: Analysis period
        risk_profile: Base risk profile to use
        timeframe: Force specific timeframe (overrides auto-detection)
        stop_atr_multiple: Custom stop distance (0.5-5.0 ATR)
        target_rr_ratio: Custom target ratio (1.0-6.0)
        max_position_risk_pct: Max risk per trade (0.5-5.0%)
        require_momentum_confirmation: Require momentum alignment

    Returns:
        Trade plans adjusted for risk profile and custom parameters
    """
```

#### `scan_trades`

```python
async def scan_trades(
    universe: str = "sp500",
    max_results: int = 10,
    period: str = "1mo",
    # NEW PARAMETERS:
    risk_profile: str = "neutral",
    min_score: int | None = None,         # Minimum signal score (0-100)
    momentum_filter: str | None = None,   # "bullish", "bearish", "strong", None
    rr_filter: float | None = None,       # Minimum R:R ratio
    volatility_filter: str | None = None, # "low", "medium", "high", None
    exclude_symbols: list[str] | None = None,
) -> dict[str, Any]:
    """Scan universe with risk-profile-adjusted filters.

    Args:
        universe: Universe to scan
        max_results: Maximum trades to return
        period: Analysis period
        risk_profile: Risk tolerance for suppression rules
        min_score: Only return trades with score >= min_score
        momentum_filter: Filter by momentum state
        rr_filter: Minimum risk:reward ratio
        volatility_filter: Filter by volatility regime
        exclude_symbols: Symbols to exclude from scan

    Returns:
        Qualified trades matching filters and risk profile
    """
```

#### `portfolio_risk`

```python
async def portfolio_risk(
    positions: list[dict],
    period: str = "1mo",
    # NEW PARAMETERS:
    risk_profile: str = "neutral",
    max_portfolio_heat: float | None = None,  # Override max total risk
    hedge_aggressiveness: str = "moderate",   # "none", "moderate", "aggressive"
    correlation_threshold: float = 0.7,       # Correlation warning level
    include_options_hedge: bool = True,
) -> dict[str, Any]:
    """Assess portfolio risk with configurable parameters.

    Args:
        positions: List of {symbol, shares, entry_price}
        period: Analysis period
        risk_profile: Base risk tolerances
        max_portfolio_heat: Custom max total risk %
        hedge_aggressiveness: Hedge suggestion level
        correlation_threshold: Warn if correlation > threshold
        include_options_hedge: Include option hedge suggestions

    Returns:
        Portfolio risk with profile-adjusted warnings and hedges
    """
```

### 5.3 Tool Schema Updates

```python
# Updated tool registration with new input schemas

Tool(
    name="analyze_security",
    description="Analyze security with configurable risk profile and momentum tracking",
    inputSchema={
        "type": "object",
        "properties": {
            "symbol": {
                "type": "string",
                "description": "Ticker symbol (e.g., AAPL, MSFT)"
            },
            "period": {
                "type": "string",
                "enum": ["15m", "1h", "4h", "1d", "5d", "1mo", "3mo", "6mo", "1y"],
                "default": "1mo",
                "description": "Analysis time period"
            },
            "risk_profile": {
                "type": "string",
                "enum": ["risky", "neutral", "averse"],
                "default": "neutral",
                "description": "User risk tolerance profile"
            },
            "price_override": {
                "type": "number",
                "description": "Manual price override for what-if analysis"
            },
            "include_momentum": {
                "type": "boolean",
                "default": True,
                "description": "Include momentum analysis in response"
            },
            "custom_config": {
                "type": "object",
                "description": "Override specific configuration values",
                "properties": {
                    "rsi_oversold": {
                        "type": "number",
                        "minimum": 10,
                        "maximum": 45,
                        "description": "RSI oversold threshold"
                    },
                    "rsi_overbought": {
                        "type": "number",
                        "minimum": 55,
                        "maximum": 90,
                        "description": "RSI overbought threshold"
                    },
                    "min_rr_ratio": {
                        "type": "number",
                        "minimum": 0.5,
                        "maximum": 5.0,
                        "description": "Minimum risk:reward ratio"
                    },
                    "momentum_weight": {
                        "type": "number",
                        "minimum": 0,
                        "maximum": 0.5,
                        "description": "Momentum weight in signal scoring"
                    },
                    "adx_trending": {
                        "type": "number",
                        "minimum": 15,
                        "maximum": 40,
                        "description": "ADX threshold for trending market"
                    }
                }
            }
        },
        "required": ["symbol"]
    }
),

Tool(
    name="scan_trades",
    description="Scan universe for trades with risk-profile filters and momentum",
    inputSchema={
        "type": "object",
        "properties": {
            "universe": {
                "type": "string",
                "enum": ["sp500", "nasdaq100", "etf_large_cap", "etf_sector", "crypto", "tech_leaders"],
                "default": "sp500"
            },
            "max_results": {
                "type": "integer",
                "minimum": 1,
                "maximum": 50,
                "default": 10
            },
            "risk_profile": {
                "type": "string",
                "enum": ["risky", "neutral", "averse"],
                "default": "neutral"
            },
            "min_score": {
                "type": "integer",
                "minimum": 0,
                "maximum": 100,
                "description": "Minimum signal score filter"
            },
            "momentum_filter": {
                "type": "string",
                "enum": ["bullish", "bearish", "strong", "any"],
                "description": "Filter by momentum state"
            },
            "rr_filter": {
                "type": "number",
                "minimum": 1.0,
                "maximum": 5.0,
                "description": "Minimum risk:reward ratio"
            },
            "volatility_filter": {
                "type": "string",
                "enum": ["low", "medium", "high", "any"],
                "description": "Filter by volatility regime"
            }
        }
    }
),
```

---

## 6. Backend Testing Framework

### 6.1 Test Configuration System

```python
# src/technical_analysis_mcp/testing/test_config.py

"""Backend testing configuration for validating config changes."""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from datetime import datetime
import json
import logging

from ..profiles.base_config import UserConfig, RiskProfile
from ..profiles.risk_profiles import get_profile

logger = logging.getLogger(__name__)


@dataclass
class TestScenario:
    """Definition of a test scenario."""

    name: str
    description: str
    config: UserConfig
    symbols: List[str]
    expected_behaviors: Dict[str, Any] = field(default_factory=dict)
    # expected_behaviors example:
    # {
    #     "AAPL": {
    #         "min_trades": 1,
    #         "max_trades": 5,
    #         "rr_range": (1.2, 3.0),
    #         "momentum_state": ["strong_up", "up"]
    #     }
    # }


@dataclass
class TestResult:
    """Result of a test scenario run."""

    scenario_name: str
    timestamp: datetime
    passed: bool
    duration_ms: float
    results_by_symbol: Dict[str, Dict[str, Any]]
    violations: List[str]
    config_used: Dict[str, Any]


class BackendTestRunner:
    """Run tests against different configurations."""

    def __init__(self):
        self._results: List[TestResult] = []

    async def run_scenario(
        self,
        scenario: TestScenario,
    ) -> TestResult:
        """Run a single test scenario.

        Args:
            scenario: Test scenario definition

        Returns:
            Test result with pass/fail and details
        """
        start = datetime.now()
        violations = []
        results_by_symbol = {}

        for symbol in scenario.symbols:
            try:
                # Run analysis with scenario config
                result = await self._analyze_with_config(
                    symbol,
                    scenario.config
                )
                results_by_symbol[symbol] = result

                # Check expected behaviors
                if symbol in scenario.expected_behaviors:
                    symbol_violations = self._check_expectations(
                        result,
                        scenario.expected_behaviors[symbol]
                    )
                    violations.extend(symbol_violations)

            except Exception as e:
                violations.append(f"{symbol}: Error - {str(e)}")
                results_by_symbol[symbol] = {"error": str(e)}

        duration = (datetime.now() - start).total_seconds() * 1000

        test_result = TestResult(
            scenario_name=scenario.name,
            timestamp=start,
            passed=len(violations) == 0,
            duration_ms=duration,
            results_by_symbol=results_by_symbol,
            violations=violations,
            config_used=scenario.config.__dict__,
        )

        self._results.append(test_result)
        return test_result

    async def run_profile_comparison(
        self,
        symbols: List[str],
    ) -> Dict[str, Dict[str, TestResult]]:
        """Run all three risk profiles against symbols and compare.

        Useful for A/B testing profile configurations.
        """
        comparison = {}

        for profile in RiskProfile:
            scenario = TestScenario(
                name=f"profile_{profile.value}",
                description=f"Test {profile.value} profile",
                config=get_profile(profile),
                symbols=symbols,
            )
            result = await self.run_scenario(scenario)
            comparison[profile.value] = result

        return comparison

    async def run_config_sweep(
        self,
        symbol: str,
        param_name: str,
        param_values: List[Any],
        base_profile: RiskProfile = RiskProfile.NEUTRAL,
    ) -> List[Dict[str, Any]]:
        """Sweep a single parameter across values.

        Useful for finding optimal threshold values.

        Example:
            results = await runner.run_config_sweep(
                "AAPL",
                "rsi_oversold",
                [20, 25, 30, 35, 40],
            )
        """
        results = []
        base_config = get_profile(base_profile)

        for value in param_values:
            # Create config with override
            test_config = self._override_param(base_config, param_name, value)

            # Run analysis
            analysis = await self._analyze_with_config(symbol, test_config)

            results.append({
                "param_value": value,
                "trades_found": len(analysis.get("trade_plans", [])),
                "avg_rr": self._calc_avg_rr(analysis),
                "signal_count": len(analysis.get("signals", [])),
                "momentum_state": analysis.get("momentum", {}).get("state"),
            })

        return results

    def generate_report(self) -> str:
        """Generate test report from all results."""
        report = ["# Backend Configuration Test Report", ""]
        report.append(f"Generated: {datetime.now().isoformat()}")
        report.append(f"Total scenarios run: {len(self._results)}")
        report.append("")

        passed = sum(1 for r in self._results if r.passed)
        report.append(f"**Passed**: {passed}/{len(self._results)}")
        report.append("")

        for result in self._results:
            status = "✅ PASS" if result.passed else "❌ FAIL"
            report.append(f"## {result.scenario_name} {status}")
            report.append(f"Duration: {result.duration_ms:.1f}ms")

            if result.violations:
                report.append("### Violations:")
                for v in result.violations:
                    report.append(f"- {v}")

            report.append("")

        return "\n".join(report)

    async def _analyze_with_config(
        self,
        symbol: str,
        config: UserConfig,
    ) -> Dict[str, Any]:
        """Run analyze_security with specific config."""
        # Import here to avoid circular imports
        from ..server import analyze_security_with_config
        return await analyze_security_with_config(symbol, "1mo", config)

    def _check_expectations(
        self,
        result: Dict[str, Any],
        expectations: Dict[str, Any],
    ) -> List[str]:
        """Check if result meets expectations."""
        violations = []

        trades = result.get("trade_plans", [])

        if "min_trades" in expectations:
            if len(trades) < expectations["min_trades"]:
                violations.append(
                    f"Expected min {expectations['min_trades']} trades, got {len(trades)}"
                )

        if "max_trades" in expectations:
            if len(trades) > expectations["max_trades"]:
                violations.append(
                    f"Expected max {expectations['max_trades']} trades, got {len(trades)}"
                )

        if "rr_range" in expectations and trades:
            min_rr, max_rr = expectations["rr_range"]
            for trade in trades:
                rr = trade.get("risk_reward", 0)
                if not (min_rr <= rr <= max_rr):
                    violations.append(
                        f"R:R {rr} outside expected range ({min_rr}, {max_rr})"
                    )

        if "momentum_state" in expectations:
            actual_state = result.get("momentum", {}).get("state")
            if actual_state not in expectations["momentum_state"]:
                violations.append(
                    f"Momentum state {actual_state} not in expected {expectations['momentum_state']}"
                )

        return violations

    def _override_param(
        self,
        config: UserConfig,
        param_name: str,
        value: Any,
    ) -> UserConfig:
        """Create new config with single param override."""
        # Implementation depends on config structure
        return UserConfig(
            risk_profile=config.risk_profile,
            indicators=config.indicators,
            risk=config.risk,
            momentum=config.momentum,
            signals=config.signals,
            custom_overrides={param_name: value},
        )

    def _calc_avg_rr(self, analysis: Dict[str, Any]) -> float:
        """Calculate average R:R from analysis."""
        trades = analysis.get("trade_plans", [])
        if not trades:
            return 0.0
        rrs = [t.get("risk_reward", 0) for t in trades]
        return sum(rrs) / len(rrs)
```

### 6.2 Predefined Test Scenarios

```python
# src/technical_analysis_mcp/testing/scenarios.py

"""Predefined test scenarios for backend validation."""

from .test_config import TestScenario
from ..profiles.risk_profiles import RISKY_CONFIG, NEUTRAL_CONFIG, AVERSE_CONFIG


# ============ PROFILE VALIDATION SCENARIOS ============

SCENARIO_RISKY_GENERATES_MORE_TRADES = TestScenario(
    name="risky_more_trades",
    description="Risky profile should generate more trade opportunities",
    config=RISKY_CONFIG,
    symbols=["AAPL", "MSFT", "GOOGL", "NVDA", "TSLA"],
    expected_behaviors={
        # Expect at least 1 trade per symbol with risky profile
        symbol: {"min_trades": 1, "max_trades": 5}
        for symbol in ["AAPL", "MSFT", "GOOGL", "NVDA", "TSLA"]
    },
)

SCENARIO_AVERSE_HIGHER_RR = TestScenario(
    name="averse_higher_rr",
    description="Averse profile should only show trades with R:R >= 2.0",
    config=AVERSE_CONFIG,
    symbols=["AAPL", "MSFT", "SPY"],
    expected_behaviors={
        symbol: {"rr_range": (2.0, 6.0)}
        for symbol in ["AAPL", "MSFT", "SPY"]
    },
)

SCENARIO_MOMENTUM_INTEGRATION = TestScenario(
    name="momentum_in_output",
    description="All analyses should include momentum data",
    config=NEUTRAL_CONFIG,
    symbols=["AAPL", "QQQ", "NVDA"],
    expected_behaviors={
        symbol: {"momentum_state": ["strong_up", "up", "stall", "down", "strong_down"]}
        for symbol in ["AAPL", "QQQ", "NVDA"]
    },
)


# ============ REGRESSION TEST SCENARIOS ============

SCENARIO_NO_MOCK_DATA = TestScenario(
    name="no_mock_data",
    description="All prices should be real (non-zero, non-100.0 placeholder)",
    config=NEUTRAL_CONFIG,
    symbols=["AAPL", "INVALID_SYMBOL_XYZ"],
    expected_behaviors={
        "AAPL": {"min_trades": 0},  # Should have real data
        "INVALID_SYMBOL_XYZ": {},   # Should fail gracefully, not return mock
    },
)


# ============ EDGE CASE SCENARIOS ============

SCENARIO_HIGH_VOLATILITY = TestScenario(
    name="high_volatility_handling",
    description="Test handling of high-volatility stocks",
    config=NEUTRAL_CONFIG,
    symbols=["GME", "AMC", "COIN"],  # Known volatile stocks
    expected_behaviors={
        # Should either suppress or adjust stops appropriately
    },
)


# All scenarios for batch running
ALL_SCENARIOS = [
    SCENARIO_RISKY_GENERATES_MORE_TRADES,
    SCENARIO_AVERSE_HIGHER_RR,
    SCENARIO_MOMENTUM_INTEGRATION,
    SCENARIO_NO_MOCK_DATA,
    SCENARIO_HIGH_VOLATILITY,
]
```

### 6.3 CLI Test Runner

```python
# scripts/test_backend_config.py

"""CLI tool for testing backend configurations."""

import asyncio
import argparse
import json
from datetime import datetime

from src.technical_analysis_mcp.testing.test_config import BackendTestRunner
from src.technical_analysis_mcp.testing.scenarios import ALL_SCENARIOS
from src.technical_analysis_mcp.profiles.base_config import RiskProfile


async def main():
    parser = argparse.ArgumentParser(description="Test backend configurations")
    parser.add_argument(
        "--mode",
        choices=["scenarios", "compare", "sweep"],
        default="scenarios",
        help="Test mode"
    )
    parser.add_argument(
        "--symbols",
        nargs="+",
        default=["AAPL", "MSFT", "NVDA"],
        help="Symbols to test"
    )
    parser.add_argument(
        "--param",
        help="Parameter to sweep (for sweep mode)"
    )
    parser.add_argument(
        "--values",
        nargs="+",
        type=float,
        help="Values to sweep (for sweep mode)"
    )
    parser.add_argument(
        "--output",
        default=f"test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
        help="Output file for report"
    )

    args = parser.parse_args()
    runner = BackendTestRunner()

    if args.mode == "scenarios":
        print(f"Running {len(ALL_SCENARIOS)} test scenarios...")
        for scenario in ALL_SCENARIOS:
            print(f"  Running: {scenario.name}")
            result = await runner.run_scenario(scenario)
            status = "✅" if result.passed else "❌"
            print(f"    {status} ({result.duration_ms:.1f}ms)")

    elif args.mode == "compare":
        print(f"Comparing risk profiles for {args.symbols}...")
        comparison = await runner.run_profile_comparison(args.symbols)

        print("\nProfile Comparison:")
        for profile, result in comparison.items():
            trades = sum(
                len(r.get("trade_plans", []))
                for r in result.results_by_symbol.values()
            )
            print(f"  {profile}: {trades} total trades found")

    elif args.mode == "sweep":
        if not args.param or not args.values:
            print("Error: --param and --values required for sweep mode")
            return

        print(f"Sweeping {args.param} = {args.values} for {args.symbols[0]}...")
        results = await runner.run_config_sweep(
            args.symbols[0],
            args.param,
            args.values,
        )

        print("\nSweep Results:")
        print(f"{'Value':>10} | {'Trades':>6} | {'Avg R:R':>8} | {'Signals':>8}")
        print("-" * 45)
        for r in results:
            print(
                f"{r['param_value']:>10.2f} | "
                f"{r['trades_found']:>6} | "
                f"{r['avg_rr']:>8.2f} | "
                f"{r['signal_count']:>8}"
            )

    # Generate report
    report = runner.generate_report()
    with open(args.output, "w") as f:
        f.write(report)
    print(f"\nReport saved to: {args.output}")


if __name__ == "__main__":
    asyncio.run(main())
```

### 6.4 Example Test Run

```bash
# Run all predefined scenarios
python scripts/test_backend_config.py --mode scenarios

# Compare risk profiles on specific stocks
python scripts/test_backend_config.py --mode compare --symbols AAPL NVDA TSLA

# Sweep RSI oversold threshold to find optimal value
python scripts/test_backend_config.py --mode sweep \
    --symbols AAPL \
    --param rsi_oversold \
    --values 20 25 30 35 40

# Output:
# Sweeping rsi_oversold = [20.0, 25.0, 30.0, 35.0, 40.0] for AAPL...
#
# Sweep Results:
#      Value | Trades |   Avg R:R | Signals
# ---------------------------------------------
#      20.00 |      1 |     2.35 |       42
#      25.00 |      2 |     2.10 |       48
#      30.00 |      2 |     1.85 |       53
#      35.00 |      3 |     1.62 |       61
#      40.00 |      4 |     1.45 |       68
```

---

## 7. Implementation Roadmap

### Phase 1: Foundation (Week 1-2)

**Backend Only - No Frontend Changes**

| Task | Files | Priority |
|------|-------|----------|
| Create `profiles/` directory structure | New directory | High |
| Implement `base_config.py` | New file | High |
| Implement `risk_profiles.py` | New file | High |
| Implement `config_manager.py` | New file | High |
| Add config parameter to `analyze_security` | `server.py` | High |
| Add config parameter to `get_trade_plan` | `server.py` | High |
| Create `BackendTestRunner` | New file | Medium |
| Create initial test scenarios | New file | Medium |

**Deliverable**: Backend can accept `risk_profile` parameter and produce different outputs.

### Phase 2: Momentum Integration (Week 2-3)

**Backend Only**

| Task | Files | Priority |
|------|-------|----------|
| Implement `MomentumCalculator` | New file | High |
| Integrate momentum into signal ranking | `ranking.py` | High |
| Add momentum to all 9 server outputs | `server.py` | High |
| Add momentum filters to `scan_trades` | `server.py` | Medium |
| Add momentum config options | `base_config.py` | Medium |
| Create momentum test scenarios | `scenarios.py` | Medium |

**Deliverable**: All analyses include momentum tracking; signals are momentum-adjusted.

### Phase 3: Full Parameter Control (Week 3-4)

**Backend Only**

| Task | Files | Priority |
|------|-------|----------|
| Add all new parameters to remaining 7 servers | `server.py` | High |
| Implement parameter validation | `config_manager.py` | High |
| Add price override support | `data.py`, `price_overrides.py` | Medium |
| Create config sweep tool | `test_config.py` | Medium |
| Profile comparison testing | `scenarios.py` | Medium |
| Documentation updates | Various `.md` | Low |

**Deliverable**: All 9 MCP servers accept full parameter customization; testing tools complete.

### Phase 4: Frontend Integration (Week 5+)

**After Backend Fully Tested**

| Task | Files | Priority |
|------|-------|----------|
| Add risk profile selector to settings | Frontend | High |
| Update API routes to pass config | `api/mcp/*` | High |
| Add momentum display to analysis page | Frontend | High |
| Add advanced config panel (Pro+) | Frontend | Medium |
| Add profile comparison view | Frontend | Low |

**Deliverable**: Users can select risk profiles and see momentum data in UI.

---

## 8. API Contract Examples

### 8.1 Request with Risk Profile

```json
// POST /api/mcp/analyze
{
  "symbol": "AAPL",
  "period": "1mo",
  "risk_profile": "risky",
  "include_momentum": true,
  "custom_config": {
    "rsi_oversold": 35,
    "momentum_weight": 0.25
  }
}
```

### 8.2 Response with Momentum & Risk Profile Impact

```json
{
  "symbol": "AAPL",
  "timestamp": "2025-01-29T10:30:00Z",
  "risk_profile": "risky",
  "config_applied": {
    "rsi_oversold": 35,
    "rsi_overbought": 65,
    "min_rr_ratio": 1.2,
    "momentum_weight": 0.25
  },

  "price_data": {
    "current": 185.50,
    "change_pct": 1.2,
    "volume": 52000000,
    "atr": 3.25
  },

  "momentum": {
    "current_pct": 4.2,
    "state": "strong_up",
    "5_bar": 4.2,
    "10_bar": 6.8,
    "20_bar": 12.3,
    "trend": "decelerating_up",
    "consistency": 0.85,
    "strength": 78,
    "confirmation_status": "confirmed",
    "divergence": null
  },

  "signals": [
    {
      "name": "Golden Cross (50/200 MA)",
      "category": "MA_CROSS",
      "strength": "STRONG_BULLISH",
      "base_score": 75,
      "momentum_impact": 12,
      "final_score": 87,
      "momentum_note": "Confirmed by strong upward momentum"
    }
  ],

  "trade_plans": [
    {
      "timeframe": "swing",
      "bias": "bullish",
      "entry": 185.50,
      "stop": 182.00,
      "target": 192.00,
      "risk_reward": 1.9,
      "risk_quality": "medium",
      "position_risk_pct": 2.5,
      "vehicle": "stock",
      "momentum_status": "confirmed",
      "profile_notes": [
        "Trade qualifies under RISKY profile",
        "Would be suppressed under AVERSE (R:R < 2.0)"
      ]
    }
  ],

  "risk_profile_summary": {
    "profile_used": "risky",
    "trades_shown": 3,
    "trades_suppressed": 1,
    "comparison": {
      "neutral_would_show": 2,
      "averse_would_show": 1
    }
  }
}
```

### 8.3 Scan with Filters

```json
// POST /api/mcp/scan
{
  "universe": "sp500",
  "max_results": 20,
  "risk_profile": "neutral",
  "momentum_filter": "bullish",
  "rr_filter": 2.0,
  "volatility_filter": "medium"
}
```

### 8.4 Portfolio Risk with Hedge Suggestions

```json
// POST /api/mcp/portfolio-risk
{
  "positions": [
    {"symbol": "AAPL", "shares": 100, "entry_price": 180.00},
    {"symbol": "NVDA", "shares": 50, "entry_price": 120.00}
  ],
  "risk_profile": "averse",
  "hedge_aggressiveness": "moderate",
  "include_options_hedge": true
}
```

---

## Summary

This document outlines a comprehensive enhancement to the MCP Finance system:

1. **Central Configuration**: Hierarchical config system with risk profiles, user overrides, and session overrides
2. **Risk Profiles**: Three profiles (Risky, Neutral, Averse) with distinct threshold adjustments across all parameters
3. **Momentum Integration**: Full momentum tracking with multi-period analysis, divergence detection, and signal score integration
4. **User Control**: All 9 MCP servers accept configurable parameters for indicators, risk, and output
5. **Backend Testing**: Complete testing framework with scenarios, profile comparison, and parameter sweeping

**Key Benefits**:
- Users get recommendations tailored to their risk tolerance
- Momentum is tracked and influences all signals
- Backend can be fully tested before any frontend changes
- Gradual rollout possible (backend first, then frontend)

**Next Steps**:
1. Review and approve architecture
2. Begin Phase 1 implementation (profiles + config)
3. Set up backend testing infrastructure
4. Iterate on profile thresholds based on testing
