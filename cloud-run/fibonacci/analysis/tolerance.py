"""
Adaptive Tolerance Calculation for Fibonacci Analysis
=====================================================
Calculates dynamic tolerance based on market volatility.
More volatile markets get wider tolerance bands.
"""

from typing import Optional
import pandas as pd


class AdaptiveTolerance:
    """
    Calculates dynamic tolerance based on market volatility.
    More volatile markets get wider tolerance bands.
    """

    def __init__(self, df: pd.DataFrame, base_tolerance: float = 0.02):
        """
        Initialize tolerance calculator.

        Args:
            df: DataFrame with OHLCV price data
            base_tolerance: Base tolerance percentage (default 2% - swing trading optimized)
        """
        self.df = df
        self.base_tolerance = base_tolerance
        self._atr: Optional[float] = None
        self._volatility_factor: Optional[float] = None

    def calculate_atr(self, period: int = 14) -> float:
        """
        Calculate Average True Range.

        Args:
            period: ATR calculation period

        Returns:
            Average True Range value
        """
        if self._atr is not None:
            return self._atr

        if len(self.df) < period + 1:
            self._atr = 0.0
            return self._atr

        high = self.df['High']
        low = self.df['Low']
        close = self.df['Close'].shift(1)

        tr1 = high - low
        tr2 = abs(high - close)
        tr3 = abs(low - close)

        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        self._atr = tr.iloc[-period:].mean()
        return self._atr

    def get_volatility_factor(self) -> float:
        """
        Get volatility multiplier for tolerance adjustment.

        Returns:
            Volatility factor (clamped between 0.5 and 2.0)
        """
        if self._volatility_factor is not None:
            return self._volatility_factor

        if len(self.df) < 20:
            self._volatility_factor = 1.0
            return self._volatility_factor

        returns = self.df['Close'].pct_change().dropna()
        current_vol = returns.iloc[-20:].std()
        historical_vol = returns.std() if len(returns) > 50 else current_vol

        if historical_vol > 0:
            self._volatility_factor = min(max(current_vol / historical_vol, 0.5), 2.0)
        else:
            self._volatility_factor = 1.0

        return self._volatility_factor

    def get_tolerance(self, tolerance_type: str = 'standard') -> float:
        """
        Get adaptive tolerance based on volatility.

        Args:
            tolerance_type: One of 'tight', 'standard', 'wide', 'very_wide'

        Returns:
            Adjusted tolerance value
        """
        vol_factor = self.get_volatility_factor()

        multipliers = {
            'tight': 0.5,
            'standard': 1.0,
            'wide': 2.0,
            'very_wide': 3.0
        }

        multiplier = multipliers.get(tolerance_type, 1.0)
        return self.base_tolerance * vol_factor * multiplier

    def get_atr_tolerance(self, atr_multiplier: float = 0.5) -> float:
        """
        Get tolerance as a fraction of ATR.

        Args:
            atr_multiplier: Multiplier for ATR-based tolerance

        Returns:
            ATR-based tolerance value
        """
        atr = self.calculate_atr()
        if atr > 0 and len(self.df) > 0:
            close = self.df['Close'].iloc[-1]
            return (atr * atr_multiplier) / close if close > 0 else self.base_tolerance
        return self.base_tolerance
