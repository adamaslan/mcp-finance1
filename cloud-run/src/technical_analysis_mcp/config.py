"""Configuration and constants for Technical Analysis MCP Server.

Centralizes all configuration values for easy modification and testing.
"""

import os
from enum import Enum
from typing import Final


# Cache Configuration
CACHE_TTL_SECONDS: Final[int] = 300  # 5 minutes
CACHE_MAX_SIZE: Final[int] = 100  # Maximum symbols to cache

# Data Fetching
DEFAULT_PERIOD: Final[str] = "1mo"
VALID_PERIODS: Final[tuple[str, ...]] = (
    "1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max"
)
MAX_RETRY_ATTEMPTS: Final[int] = 3
RETRY_BACKOFF_SECONDS: Final[float] = 1.0

# Indicator Periods
MA_PERIODS: Final[tuple[int, ...]] = (5, 10, 20, 50, 100, 200)
RSI_PERIOD: Final[int] = 14
MACD_FAST: Final[int] = 12
MACD_SLOW: Final[int] = 26
MACD_SIGNAL: Final[int] = 9
BOLLINGER_PERIOD: Final[int] = 20
BOLLINGER_STD: Final[float] = 2.0
STOCHASTIC_K_PERIOD: Final[int] = 14
STOCHASTIC_D_PERIOD: Final[int] = 3
ADX_PERIOD: Final[int] = 14
ATR_PERIOD: Final[int] = 14
VOLUME_MA_SHORT: Final[int] = 20
VOLUME_MA_LONG: Final[int] = 50

# Minimum data requirements
MIN_DATA_POINTS: Final[int] = 50
MIN_DATA_POINTS_200MA: Final[int] = 200

# API Configuration
GEMINI_API_KEY: str | None = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL: Final[str] = "gemini-2.0-flash-exp"

# Analysis Limits
MAX_SIGNALS_RETURNED: Final[int] = 50
MAX_SYMBOLS_COMPARE: Final[int] = 10
MAX_SYMBOLS_SCREEN: Final[int] = 100


class SignalStrength(str, Enum):
    """Signal strength levels."""

    STRONG_BULLISH = "STRONG BULLISH"
    BULLISH = "BULLISH"
    NEUTRAL = "NEUTRAL"
    BEARISH = "BEARISH"
    STRONG_BEARISH = "STRONG BEARISH"
    SIGNIFICANT = "SIGNIFICANT"
    VERY_SIGNIFICANT = "VERY SIGNIFICANT"
    TRENDING = "TRENDING"


class SignalCategory(str, Enum):
    """Signal categories for classification."""

    MA_CROSS = "MA_CROSS"
    MA_TREND = "MA_TREND"
    RSI = "RSI"
    MACD = "MACD"
    BOLLINGER = "BOLLINGER"
    STOCHASTIC = "STOCHASTIC"
    VOLUME = "VOLUME"
    TREND = "TREND"
    PRICE_ACTION = "PRICE_ACTION"
    ADX = "ADX"


# Ranking Configuration
STRENGTH_SCORES: dict[str, int] = {
    "EXTREME": 85,
    "STRONG": 75,
    "SIGNIFICANT": 65,
    "VERY": 65,
    "BULLISH": 55,
    "BEARISH": 55,
}

CATEGORY_BONUSES: dict[SignalCategory, int] = {
    SignalCategory.MA_CROSS: 10,
    SignalCategory.MACD: 10,
    SignalCategory.VOLUME: 10,
}

MAX_RULE_BASED_SCORE: Final[int] = 95

# RSI Thresholds
RSI_OVERSOLD: Final[float] = 30.0
RSI_OVERBOUGHT: Final[float] = 70.0
RSI_EXTREME_OVERSOLD: Final[float] = 20.0
RSI_EXTREME_OVERBOUGHT: Final[float] = 80.0

# Stochastic Thresholds
STOCH_OVERSOLD: Final[float] = 20.0
STOCH_OVERBOUGHT: Final[float] = 80.0

# Volume Thresholds
VOLUME_SPIKE_2X: Final[float] = 2.0
VOLUME_SPIKE_3X: Final[float] = 3.0

# ADX Thresholds
ADX_TRENDING: Final[float] = 25.0
ADX_STRONG_TREND: Final[float] = 40.0

# Price Action Thresholds
LARGE_MOVE_PERCENT: Final[float] = 5.0

# ============================================================================
# Risk Assessment Configuration (Risk Layer)
# ============================================================================

# Volatility Regime Thresholds (ATR as % of price)
VOLATILITY_LOW_THRESHOLD: Final[float] = 1.5  # < 1.5% = LOW
VOLATILITY_HIGH_THRESHOLD: Final[float] = 3.0  # > 3.0% = HIGH

# Stop Distance Validation (in ATR multiples)
STOP_MIN_ATR_MULTIPLE: Final[float] = 0.5  # Minimum: 0.5 ATR
STOP_MAX_ATR_MULTIPLE: Final[float] = 3.0  # Maximum: 3.0 ATR

# Timeframe-specific ATR multiples for stops
STOP_ATR_SWING: Final[float] = 2.0  # Swing trades: 2 ATR stop
STOP_ATR_DAY: Final[float] = 1.5  # Day trades: 1.5 ATR stop
STOP_ATR_SCALP: Final[float] = 1.0  # Scalp trades: 1 ATR stop

# Risk-to-Reward Requirements
MIN_RR_RATIO: Final[float] = 1.5  # Minimum 1.5:1 R:R
PREFERRED_RR_RATIO: Final[float] = 2.0  # Preferred 2:1 R:R

# Trend Thresholds
ADX_TRENDING_THRESHOLD: Final[float] = 25.0  # ADX > 25 = trending
ADX_STRONG_TREND_THRESHOLD: Final[float] = 40.0  # ADX > 40 = strong trend
ADX_NO_TREND_THRESHOLD: Final[float] = 20.0  # ADX < 20 = no trend

# Trade Plan Output Limits
MAX_TRADE_PLANS: Final[int] = 3  # Maximum trade plans per analysis

# Suppression Thresholds
MAX_CONFLICTING_SIGNALS_RATIO: Final[float] = 0.4  # If >40% signals conflict, suppress

# Volume Requirements
MIN_VOLUME_RATIO: Final[float] = 0.5  # Current volume >= 50% of average

# Options Integration (Full Suggestions)
OPTION_MIN_EXPECTED_MOVE: Final[float] = 3.0  # Min 3% move for options consideration
OPTION_SWING_MIN_DTE: Final[int] = 30  # Minimum 30 DTE for swing options
OPTION_SWING_MAX_DTE: Final[int] = 45  # Maximum 45 DTE for swing options
OPTION_CALL_DELTA_MIN: Final[float] = 0.40  # Min delta for calls
OPTION_CALL_DELTA_MAX: Final[float] = 0.60  # Max delta for calls
OPTION_PUT_DELTA_MIN: Final[float] = -0.60  # Min delta for puts
OPTION_PUT_DELTA_MAX: Final[float] = -0.40  # Max delta for puts
OPTION_SPREAD_WIDTH_ATR: Final[float] = 1.0  # Spread width as ATR multiple
