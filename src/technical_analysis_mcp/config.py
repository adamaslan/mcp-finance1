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
# SWING TRADING CONFIG: Extended periods for multi-day trend analysis
DEFAULT_PERIOD: Final[str] = "3mo"
VALID_PERIODS: Final[tuple[str, ...]] = (
    "15m", "1h", "4h", "1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max"
)
MAX_RETRY_ATTEMPTS: Final[int] = 3
RETRY_BACKOFF_SECONDS: Final[float] = 1.0

# Indicator Periods - OPTIMIZED FOR SWING TRADING
MA_PERIODS: Final[tuple[int, ...]] = (5, 10, 20, 50, 100, 200)
RSI_PERIOD: Final[int] = 24  # Swing trading: smoother, fewer whipsaws (was 14)
MACD_FAST: Final[int] = 20  # Swing trading: longer periods (was 12)
MACD_SLOW: Final[int] = 50  # Swing trading: longer periods (was 26)
MACD_SIGNAL: Final[int] = 20  # Swing trading: longer signal line (was 9)
BOLLINGER_PERIOD: Final[int] = 20
BOLLINGER_STD: Final[float] = 2.0
STOCHASTIC_K_PERIOD: Final[int] = 14
STOCHASTIC_D_PERIOD: Final[int] = 3
ADX_PERIOD: Final[int] = 25  # Swing trading: stronger trend identification (was 14)
ATR_PERIOD: Final[int] = 14  # Keep for stop loss calculations
VOLUME_MA_SHORT: Final[int] = 20
VOLUME_MA_LONG: Final[int] = 50

# Minimum data requirements
MIN_DATA_POINTS: Final[int] = 50
MIN_DATA_POINTS_200MA: Final[int] = 200

# API Configuration
GEMINI_API_KEY: str | None = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL: Final[str] = "gemini-2.0-flash"

# Analysis Limits - SWING TRADING OPTIMIZATION
# Reduce signal count to prevent analysis paralysis (was 50)
MAX_SIGNALS_RETURNED: Final[int] = 12
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

# Timeframe-specific ATR multiples for stops - SWING TRADING ADJUSTED
# Wider stops for larger price movements typical in swing trading
STOP_ATR_SWING: Final[float] = 2.5  # Swing trades: 2.5 ATR stop (was 2.0, increased for volatility)
STOP_ATR_DAY: Final[float] = 1.5  # Day trades: 1.5 ATR stop
STOP_ATR_SCALP: Final[float] = 1.0  # Scalp trades: 1 ATR stop

# Risk-to-Reward Requirements - SWING TRADING OPTIMIZED
MIN_RR_RATIO: Final[float] = 2.0  # Minimum 2:1 R:R for swing trades (was 1.5)
PREFERRED_RR_RATIO: Final[float] = 3.0  # Preferred 3:1 R:R for swing trades (was 2.0)

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

# Options Integration (Full Suggestions) - SWING TRADING OPTIMIZED
OPTION_MIN_EXPECTED_MOVE: Final[float] = 4.0  # Min 4% move for swing option consideration (was 3%)
OPTION_SWING_MIN_DTE: Final[int] = 35  # Minimum 35 DTE for swing options (was 30)
OPTION_SWING_MAX_DTE: Final[int] = 60  # Maximum 60 DTE for swing options (was 45)
OPTION_CALL_DELTA_MIN: Final[float] = 0.35  # Min delta for calls (wider range, was 0.40)
OPTION_CALL_DELTA_MAX: Final[float] = 0.70  # Max delta for calls (wider range, was 0.60)
OPTION_PUT_DELTA_MIN: Final[float] = -0.70  # Min delta for puts (wider range, was -0.60)
OPTION_PUT_DELTA_MAX: Final[float] = -0.35  # Max delta for puts (wider range, was -0.40)
OPTION_SPREAD_WIDTH_ATR: Final[float] = 1.5  # Spread width as ATR multiple (was 1.0)

# ============================================================================
# SWING TRADING CONFIGURATION SUMMARY
# ============================================================================
# Updated February 5, 2026 for swing trading optimization
#
# KEY CHANGES FROM DAY TRADING DEFAULTS:
# ✓ DEFAULT_PERIOD: 1mo → 3mo (captures multi-week trends)
# ✓ RSI_PERIOD: 14 → 24 (less whipsaw, clearer signals)
# ✓ MACD: (12,26,9) → (20,50,20) (longer-term trend identification)
# ✓ ADX_PERIOD: 14 → 25 (stronger trend confirmation)
# ✓ STOP_ATR_SWING: 2.0 → 2.5 ATR (accommodate larger price swings)
# ✓ MAX_SIGNALS_RETURNED: 50 → 12 (focus on quality, prevent paralysis)
# ✓ MIN_RR_RATIO: 1.5:1 → 2.0:1 (higher reward threshold)
# ✓ PREFERRED_RR_RATIO: 2.0:1 → 3.0:1 (quality setups)
# ✓ Fibonacci window: 50 → 150 bars (multi-day swing highs/lows)
# ✓ Fibonacci tolerance: 1% → 2% (balance sensitivity vs noise)
# ✓ options min_volume: 10 → 75 (ensure adequate liquidity)
# ✓ lookback_days: 90 → 180 (robust signal validation)
# ✓ Options DTE: 30-45 → 35-60 days (swing duration)
# ✓ Options delta: narrower → wider (more flexibility)
