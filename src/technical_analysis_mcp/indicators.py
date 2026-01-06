"""Technical indicator calculations.

Pure functions for calculating all technical indicators from OHLCV data.
Each function operates on pandas DataFrames and returns calculated values.
"""

import logging

import numpy as np
import pandas as pd

from .config import (
    ADX_PERIOD,
    ATR_PERIOD,
    BOLLINGER_PERIOD,
    BOLLINGER_STD,
    MA_PERIODS,
    MACD_FAST,
    MACD_SIGNAL,
    MACD_SLOW,
    RSI_PERIOD,
    STOCHASTIC_D_PERIOD,
    STOCHASTIC_K_PERIOD,
    VOLUME_MA_LONG,
    VOLUME_MA_SHORT,
)

logger = logging.getLogger(__name__)


def calculate_sma(series: pd.Series, period: int) -> pd.Series:
    """Calculate Simple Moving Average.

    Args:
        series: Price series to calculate SMA on.
        period: Number of periods for the moving average.

    Returns:
        Series containing SMA values.
    """
    return series.rolling(window=period).mean()


def calculate_ema(series: pd.Series, period: int) -> pd.Series:
    """Calculate Exponential Moving Average.

    Args:
        series: Price series to calculate EMA on.
        period: Number of periods for the moving average.

    Returns:
        Series containing EMA values.
    """
    return series.ewm(span=period, adjust=False).mean()


def calculate_moving_averages(df: pd.DataFrame, periods: tuple[int, ...] = MA_PERIODS) -> pd.DataFrame:
    """Calculate all moving averages for given periods.

    Args:
        df: DataFrame with 'Close' column.
        periods: Tuple of periods to calculate MAs for.

    Returns:
        DataFrame with SMA and EMA columns added.
    """
    result = df.copy()

    for period in periods:
        result[f"SMA_{period}"] = calculate_sma(result["Close"], period)
        result[f"EMA_{period}"] = calculate_ema(result["Close"], period)

    logger.debug("Calculated moving averages for periods: %s", periods)
    return result


def calculate_rsi(df: pd.DataFrame, period: int = RSI_PERIOD) -> pd.DataFrame:
    """Calculate Relative Strength Index.

    Safe implementation that prevents division-by-zero in strong uptrends.

    Args:
        df: DataFrame with 'Close' column.
        period: RSI period (default 14).

    Returns:
        DataFrame with RSI column added.
    """
    result = df.copy()

    delta = result["Close"].diff()
    gain = delta.where(delta > 0, 0).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

    # Add small epsilon (1e-10) to prevent division by zero in strong uptrends
    # where loss = 0 (prices only increase, no decreases)
    rs = gain / (loss + 1e-10)
    result["RSI"] = 100 - (100 / (1 + rs))

    logger.debug("Calculated RSI with period %d", period)
    return result


def calculate_macd(
    df: pd.DataFrame,
    fast: int = MACD_FAST,
    slow: int = MACD_SLOW,
    signal: int = MACD_SIGNAL,
) -> pd.DataFrame:
    """Calculate MACD (Moving Average Convergence Divergence).

    Args:
        df: DataFrame with 'Close' column.
        fast: Fast EMA period (default 12).
        slow: Slow EMA period (default 26).
        signal: Signal line period (default 9).

    Returns:
        DataFrame with MACD, MACD_Signal, and MACD_Hist columns added.
    """
    result = df.copy()

    exp_fast = calculate_ema(result["Close"], fast)
    exp_slow = calculate_ema(result["Close"], slow)

    result["MACD"] = exp_fast - exp_slow
    result["MACD_Signal"] = calculate_ema(result["MACD"], signal)
    result["MACD_Hist"] = result["MACD"] - result["MACD_Signal"]

    logger.debug("Calculated MACD (%d, %d, %d)", fast, slow, signal)
    return result


def calculate_bollinger_bands(
    df: pd.DataFrame,
    period: int = BOLLINGER_PERIOD,
    std_dev: float = BOLLINGER_STD,
) -> pd.DataFrame:
    """Calculate Bollinger Bands.

    Args:
        df: DataFrame with 'Close' column.
        period: Period for middle band SMA (default 20).
        std_dev: Number of standard deviations (default 2.0).

    Returns:
        DataFrame with BB_Upper, BB_Middle, BB_Lower, and BB_Width columns added.
    """
    result = df.copy()

    result["BB_Middle"] = calculate_sma(result["Close"], period)
    bb_std = result["Close"].rolling(window=period).std()

    result["BB_Upper"] = result["BB_Middle"] + (bb_std * std_dev)
    result["BB_Lower"] = result["BB_Middle"] - (bb_std * std_dev)
    result["BB_Width"] = result["BB_Upper"] - result["BB_Lower"]

    logger.debug("Calculated Bollinger Bands (%d, %.1f)", period, std_dev)
    return result


def calculate_stochastic(
    df: pd.DataFrame,
    k_period: int = STOCHASTIC_K_PERIOD,
    d_period: int = STOCHASTIC_D_PERIOD,
) -> pd.DataFrame:
    """Calculate Stochastic Oscillator.

    Args:
        df: DataFrame with 'High', 'Low', 'Close' columns.
        k_period: Period for %K (default 14).
        d_period: Period for %D smoothing (default 3).

    Returns:
        DataFrame with Stoch_K and Stoch_D columns added.
    """
    result = df.copy()

    low_min = result["Low"].rolling(window=k_period).min()
    high_max = result["High"].rolling(window=k_period).max()

    result["Stoch_K"] = 100 * ((result["Close"] - low_min) / (high_max - low_min))
    result["Stoch_D"] = result["Stoch_K"].rolling(window=d_period).mean()

    logger.debug("Calculated Stochastic (%d, %d)", k_period, d_period)
    return result


def calculate_adx(df: pd.DataFrame, period: int = ADX_PERIOD) -> pd.DataFrame:
    """Calculate Average Directional Index and Directional Indicators.

    Args:
        df: DataFrame with 'High', 'Low', 'Close' columns.
        period: ADX period (default 14).

    Returns:
        DataFrame with ADX, Plus_DI, and Minus_DI columns added.
    """
    result = df.copy()

    high_low = result["High"] - result["Low"]
    high_close = np.abs(result["High"] - result["Close"].shift())
    low_close = np.abs(result["Low"] - result["Close"].shift())

    ranges = pd.concat([high_low, high_close, low_close], axis=1)
    true_range = ranges.max(axis=1)

    plus_dm = result["High"].diff()
    minus_dm = -result["Low"].diff()
    plus_dm = plus_dm.where(plus_dm > 0, 0)
    minus_dm = minus_dm.where(minus_dm > 0, 0)

    tr_sum = true_range.rolling(period).sum()
    plus_di = 100 * (plus_dm.rolling(period).sum() / tr_sum)
    minus_di = 100 * (minus_dm.rolling(period).sum() / tr_sum)

    dx = 100 * np.abs(plus_di - minus_di) / (plus_di + minus_di)
    result["ADX"] = dx.rolling(period).mean()
    result["Plus_DI"] = plus_di
    result["Minus_DI"] = minus_di

    logger.debug("Calculated ADX with period %d", period)
    return result


def calculate_atr(df: pd.DataFrame, period: int = ATR_PERIOD) -> pd.DataFrame:
    """Calculate Average True Range.

    Args:
        df: DataFrame with 'High', 'Low', 'Close' columns.
        period: ATR period (default 14).

    Returns:
        DataFrame with ATR column added.
    """
    result = df.copy()

    high_low = result["High"] - result["Low"]
    high_close = np.abs(result["High"] - result["Close"].shift())
    low_close = np.abs(result["Low"] - result["Close"].shift())

    ranges = pd.concat([high_low, high_close, low_close], axis=1)
    true_range = ranges.max(axis=1)

    result["ATR"] = true_range.rolling(period).mean()

    logger.debug("Calculated ATR with period %d", period)
    return result


def calculate_volume_indicators(
    df: pd.DataFrame,
    short_period: int = VOLUME_MA_SHORT,
    long_period: int = VOLUME_MA_LONG,
) -> pd.DataFrame:
    """Calculate volume-based indicators.

    Args:
        df: DataFrame with 'Volume' and 'Close' columns.
        short_period: Short volume MA period (default 20).
        long_period: Long volume MA period (default 50).

    Returns:
        DataFrame with Volume_MA_20, Volume_MA_50, and OBV columns added.
    """
    result = df.copy()

    result["Volume_MA_20"] = result["Volume"].rolling(window=short_period).mean()
    result["Volume_MA_50"] = result["Volume"].rolling(window=long_period).mean()

    result["OBV"] = (np.sign(result["Close"].diff()) * result["Volume"]).fillna(0).cumsum()

    logger.debug("Calculated volume indicators")
    return result


def calculate_price_changes(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate price change metrics.

    Args:
        df: DataFrame with 'Close' column.

    Returns:
        DataFrame with Price_Change, Price_Change_5d, and Volatility columns added.
    """
    result = df.copy()

    result["Price_Change"] = result["Close"].pct_change() * 100
    result["Price_Change_5d"] = (
        (result["Close"] - result["Close"].shift(5)) / result["Close"].shift(5)
    ) * 100

    result["Volatility"] = result["Close"].pct_change().rolling(20).std() * np.sqrt(252) * 100

    logger.debug("Calculated price change metrics")
    return result


def calculate_distance_from_ma(df: pd.DataFrame, periods: tuple[int, ...] = (10, 20, 50, 200)) -> pd.DataFrame:
    """Calculate distance from moving averages as percentage.

    Args:
        df: DataFrame with 'Close' and SMA columns.
        periods: Periods to calculate distance from.

    Returns:
        DataFrame with Dist_SMA_* columns added.
    """
    result = df.copy()

    for period in periods:
        sma_col = f"SMA_{period}"
        if sma_col in result.columns:
            result[f"Dist_SMA_{period}"] = (
                (result["Close"] - result[sma_col]) / result[sma_col]
            ) * 100

    logger.debug("Calculated distance from MAs for periods: %s", periods)
    return result


def calculate_all_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate all technical indicators.

    Orchestrates the calculation of all indicators in the correct order.

    Args:
        df: DataFrame with OHLCV data (Open, High, Low, Close, Volume).

    Returns:
        DataFrame with all indicator columns added.
    """
    logger.info("Calculating all indicators for %d rows", len(df))

    result = df.copy()

    result = calculate_moving_averages(result)
    result = calculate_rsi(result)
    result = calculate_macd(result)
    result = calculate_bollinger_bands(result)
    result = calculate_stochastic(result)
    result = calculate_adx(result)
    result = calculate_atr(result)
    result = calculate_volume_indicators(result)
    result = calculate_price_changes(result)
    result = calculate_distance_from_ma(result)

    logger.info("Completed indicator calculations: %d columns", len(result.columns))
    return result


def calculate_indicators_dict(df: pd.DataFrame) -> dict[str, float]:
    """Extract all calculated indicators as a dictionary from the last row.

    Used to get current indicator values for reporting and analysis.

    Args:
        df: DataFrame with all indicators calculated via calculate_all_indicators.

    Returns:
        Dictionary of indicator names to current values (last row).
    """
    if df.empty:
        logger.warning("Cannot extract indicators from empty DataFrame")
        return {}

    latest = df.iloc[-1]
    indicators = {}

    # Core indicators
    if "RSI" in df.columns:
        indicators["rsi"] = float(latest["RSI"])
    if "MACD" in df.columns:
        indicators["macd"] = float(latest["MACD"])
    if "MACD_Signal" in df.columns:
        indicators["macd_signal"] = float(latest["MACD_Signal"])
    if "MACD_Hist" in df.columns:
        indicators["macd_hist"] = float(latest["MACD_Hist"])

    # Moving averages
    if "SMA_20" in df.columns:
        indicators["sma20"] = float(latest["SMA_20"])
    if "SMA_50" in df.columns:
        indicators["sma50"] = float(latest["SMA_50"])
    if "EMA_20" in df.columns:
        indicators["ema20"] = float(latest["EMA_20"])

    # Bollinger Bands
    if "BB_Upper" in df.columns:
        indicators["bb_upper"] = float(latest["BB_Upper"])
    if "BB_Mid" in df.columns:
        indicators["bb_mid"] = float(latest["BB_Mid"])
    if "BB_Lower" in df.columns:
        indicators["bb_lower"] = float(latest["BB_Lower"])

    # Oscillators
    if "Stoch_K" in df.columns:
        indicators["stoch_k"] = float(latest["Stoch_K"])
    if "Stoch_D" in df.columns:
        indicators["stoch_d"] = float(latest["Stoch_D"])

    # Trend indicators
    if "ADX" in df.columns:
        indicators["adx"] = float(latest["ADX"])
    if "Plus_DI" in df.columns:
        indicators["plus_di"] = float(latest["Plus_DI"])
    if "Minus_DI" in df.columns:
        indicators["minus_di"] = float(latest["Minus_DI"])

    # Volatility
    if "ATR" in df.columns:
        indicators["atr"] = float(latest["ATR"])

    # Volume
    if "Volume_MA_20" in df.columns:
        indicators["vol_avg"] = int(latest["Volume_MA_20"])
    if "Volume" in df.columns:
        indicators["volume"] = int(latest["Volume"])
        if "Volume_MA_20" in df.columns:
            indicators["vol_ratio"] = float(latest["Volume"] / latest["Volume_MA_20"])

    logger.debug("Extracted %d indicator values", len(indicators))
    return indicators
