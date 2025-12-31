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
