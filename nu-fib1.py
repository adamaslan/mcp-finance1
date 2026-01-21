"""
Enhanced Fibonacci Signal Detection Module
==========================================
Production-grade Fibonacci analysis with 200+ unique signals across:
- Classic retracements and extensions
- Dynamic multi-timeframe analysis
- Harmonic patterns (Gartley, Bat, Butterfly, Crab, Shark)
- Elliott Wave Fibonacci relationships
- Fibonacci confluence and cluster detection
- Volume-weighted Fibonacci analysis
- Momentum-Fibonacci divergence patterns
- Adaptive tolerance based on volatility
- Time-based Fibonacci projections
"""

from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
import pandas as pd
import numpy as np
from abc import ABC, abstractmethod


class SignalStrength(Enum):
    """Signal strength classification."""
    WEAK = "WEAK"
    MODERATE = "MODERATE"
    SIGNIFICANT = "SIGNIFICANT"
    STRONG = "STRONG"
    EXTREME = "EXTREME"


class FibonacciType(Enum):
    """Types of Fibonacci analysis."""
    RETRACE = "RETRACE"
    EXTENSION = "EXTENSION"
    PROJECTION = "PROJECTION"
    EXPANSION = "EXPANSION"
    INVERSE = "INVERSE"
    HARMONIC = "HARMONIC"
    TIME = "TIME"


@dataclass
class FibonacciLevel:
    """Represents a single Fibonacci level with metadata."""
    key: str
    ratio: float
    name: str
    fib_type: FibonacciType
    strength: SignalStrength
    description: str = ""
    price: float = 0.0
    
    def calculate_price(self, low: float, high: float) -> float:
        """Calculate price level from swing range."""
        swing_range = high - low
        if self.fib_type == FibonacciType.INVERSE:
            self.price = low + (self.ratio * swing_range)
        else:
            self.price = low + (self.ratio * swing_range)
        return self.price


@dataclass
class FibonacciSignal:
    """Standardized signal output."""
    signal: str
    description: str
    strength: str
    category: str
    timeframe: str
    value: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for compatibility."""
        result = {
            'signal': self.signal,
            'description': self.description,
            'strength': self.strength,
            'category': self.category,
            'timeframe': self.timeframe,
            'value': self.value
        }
        result.update(self.metadata)
        return result


class FibonacciLevelRegistry:
    """
    Registry of all Fibonacci ratios with metadata.
    Extensible design allows adding new ratios dynamically.
    """
    
    # Core Fibonacci sequence ratios
    CORE_RATIOS = {
        # Primary retracements
        'RETRACE_236': (0.236, 'RETRACE', 'WEAK', '23.6%'),
        'RETRACE_382': (0.382, 'RETRACE', 'MODERATE', '38.2%'),
        'RETRACE_500': (0.500, 'RETRACE', 'MODERATE', '50.0%'),
        'RETRACE_618': (0.618, 'RETRACE', 'SIGNIFICANT', '61.8%'),
        'RETRACE_707': (0.707, 'RETRACE', 'MODERATE', '70.7%'),  # sqrt(0.5)
        'RETRACE_786': (0.786, 'RETRACE', 'SIGNIFICANT', '78.6%'),
        'RETRACE_886': (0.886, 'RETRACE', 'SIGNIFICANT', '88.6%'),  # Harmonic
        
        # Extensions
        'EXT_1000': (1.000, 'EXTENSION', 'MODERATE', '100.0%'),
        'EXT_1130': (1.130, 'EXTENSION', 'MODERATE', '113.0%'),  # Harmonic
        'EXT_1272': (1.272, 'EXTENSION', 'MODERATE', '127.2%'),
        'EXT_1414': (1.414, 'EXTENSION', 'MODERATE', '141.4%'),  # sqrt(2)
        'EXT_1500': (1.500, 'EXTENSION', 'MODERATE', '150.0%'),
        'EXT_1618': (1.618, 'EXTENSION', 'SIGNIFICANT', '161.8%'),
        'EXT_1786': (1.786, 'EXTENSION', 'MODERATE', '178.6%'),
        'EXT_2000': (2.000, 'EXTENSION', 'SIGNIFICANT', '200.0%'),
        'EXT_2236': (2.236, 'EXTENSION', 'MODERATE', '223.6%'),  # sqrt(5)
        'EXT_2618': (2.618, 'EXTENSION', 'SIGNIFICANT', '261.8%'),
        'EXT_3000': (3.000, 'EXTENSION', 'MODERATE', '300.0%'),
        'EXT_3236': (3.236, 'EXTENSION', 'SIGNIFICANT', '323.6%'),
        'EXT_3618': (3.618, 'EXTENSION', 'MODERATE', '361.8%'),
        'EXT_4236': (4.236, 'EXTENSION', 'SIGNIFICANT', '423.6%'),
        
        # Inverse/negative retracements
        'INV_236': (-0.236, 'INVERSE', 'WEAK', '-23.6%'),
        'INV_382': (-0.382, 'INVERSE', 'MODERATE', '-38.2%'),
        'INV_500': (-0.500, 'INVERSE', 'MODERATE', '-50.0%'),
        'INV_618': (-0.618, 'INVERSE', 'SIGNIFICANT', '-61.8%'),
        
        # Deep retracements (for complex corrections)
        'RETRACE_146': (0.146, 'RETRACE', 'WEAK', '14.6%'),  # 0.236^2
        'RETRACE_090': (0.090, 'RETRACE', 'WEAK', '9.0%'),   # 0.382^2/1.618
        
        # Harmonic pattern specific
        'HARMONIC_886': (0.886, 'HARMONIC', 'SIGNIFICANT', '88.6%'),
        'HARMONIC_1130': (1.130, 'HARMONIC', 'MODERATE', '113.0%'),
        'HARMONIC_1270': (1.270, 'HARMONIC', 'MODERATE', '127.0%'),
        'HARMONIC_1414': (1.414, 'HARMONIC', 'MODERATE', '141.4%'),
        'HARMONIC_2000': (2.000, 'HARMONIC', 'SIGNIFICANT', '200.0%'),
        'HARMONIC_2240': (2.240, 'HARMONIC', 'MODERATE', '224.0%'),
        'HARMONIC_2618': (2.618, 'HARMONIC', 'SIGNIFICANT', '261.8%'),
        'HARMONIC_3140': (3.140, 'HARMONIC', 'MODERATE', '314.0%'),
        'HARMONIC_3618': (3.618, 'HARMONIC', 'SIGNIFICANT', '361.8%'),
    }
    
    # Fibonacci time numbers
    TIME_NUMBERS = [1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144, 233]
    
    @classmethod
    def get_all_levels(cls) -> Dict[str, FibonacciLevel]:
        """Generate all Fibonacci levels with metadata."""
        levels = {}
        for key, (ratio, fib_type, strength, name) in cls.CORE_RATIOS.items():
            levels[key] = FibonacciLevel(
                key=key,
                ratio=ratio,
                name=name,
                fib_type=FibonacciType[fib_type],
                strength=SignalStrength[strength]
            )
        return levels
    
    @classmethod
    def get_levels_by_type(cls, fib_type: FibonacciType) -> Dict[str, FibonacciLevel]:
        """Get levels filtered by type."""
        all_levels = cls.get_all_levels()
        return {k: v for k, v in all_levels.items() if v.fib_type == fib_type}
    
    @classmethod
    def get_retracements(cls) -> Dict[str, FibonacciLevel]:
        """Get only retracement levels."""
        return cls.get_levels_by_type(FibonacciType.RETRACE)
    
    @classmethod
    def get_extensions(cls) -> Dict[str, FibonacciLevel]:
        """Get only extension levels."""
        return cls.get_levels_by_type(FibonacciType.EXTENSION)


class SwingPointDetector:
    """
    Detects swing highs and lows across multiple lookback windows.
    Provides dynamic swing point detection for robust Fibonacci analysis.
    """
    
    def __init__(self, df: pd.DataFrame):
        self.df = df
        self._cache: Dict[int, Tuple[float, float, int, int]] = {}
    
    def detect_swings(self, window: int = 50) -> Tuple[float, float, int, int]:
        """
        Detect swing high and low within window.
        Returns: (swing_high, swing_low, high_idx, low_idx)
        """
        if window in self._cache:
            return self._cache[window]
        
        if len(self.df) < window:
            window = len(self.df)
        
        highs = self.df['High'].iloc[-window:]
        lows = self.df['Low'].iloc[-window:]
        
        high_val = highs.max()
        low_val = lows.min()
        high_idx = highs.idxmax() if hasattr(highs, 'idxmax') else highs.argmax()
        low_idx = lows.idxmin() if hasattr(lows, 'idxmin') else lows.argmin()
        
        self._cache[window] = (high_val, low_val, high_idx, low_idx)
        return self._cache[window]
    
    def get_trend_direction(self, window: int = 50) -> str:
        """Determine if we're in uptrend or downtrend based on swing sequence."""
        high_val, low_val, high_idx, low_idx = self.detect_swings(window)
        
        # If low came before high, likely uptrend
        if low_idx < high_idx:
            return 'UP'
        return 'DOWN'
    
    def get_multiple_swings(self, windows: List[int] = None) -> Dict[int, Tuple[float, float, int, int]]:
        """Get swings for multiple timeframe windows."""
        if windows is None:
            windows = [20, 50, 100, 200]
        
        return {w: self.detect_swings(w) for w in windows if w <= len(self.df)}


class AdaptiveTolerance:
    """
    Calculates dynamic tolerance based on market volatility.
    More volatile markets get wider tolerance bands.
    """
    
    def __init__(self, df: pd.DataFrame, base_tolerance: float = 0.01):
        self.df = df
        self.base_tolerance = base_tolerance
        self._atr: Optional[float] = None
        self._volatility_factor: Optional[float] = None
    
    def calculate_atr(self, period: int = 14) -> float:
        """Calculate Average True Range."""
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
        """Get volatility multiplier for tolerance adjustment."""
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
        
        tolerance_type: 'tight', 'standard', 'wide'
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
        """Get tolerance as a fraction of ATR."""
        atr = self.calculate_atr()
        if atr > 0 and len(self.df) > 0:
            close = self.df['Close'].iloc[-1]
            return (atr * atr_multiplier) / close if close > 0 else self.base_tolerance
        return self.base_tolerance


class SignalGenerator(ABC):
    """Abstract base class for signal generators."""
    
    @abstractmethod
    def generate(self, context: 'FibonacciContext') -> List[FibonacciSignal]:
        """Generate signals from context."""
        pass


class FibonacciContext:
    """
    Context object containing all data needed for signal generation.
    Avoids passing many parameters and enables caching.
    """
    
    def __init__(
        self,
        df: pd.DataFrame,
        interval: str,
        current: pd.Series,
        prev: pd.Series,
        safe_float_fn
    ):
        self.df = df
        self.interval = interval
        self.current = current
        self.prev = prev
        self._safe_float = safe_float_fn
        
        # Initialize helpers
        self.swing_detector = SwingPointDetector(df)
        self.tolerance_calc = AdaptiveTolerance(df)
        self.fib_registry = FibonacciLevelRegistry()
        
        # Cache commonly used values
        self._close: Optional[float] = None
        self._prev_close: Optional[float] = None
        self._fib_levels: Optional[Dict[str, FibonacciLevel]] = None
        self._swing_data: Dict[int, Dict] = {}
    
    @property
    def close(self) -> Optional[float]:
        """Current close price."""
        if self._close is None:
            self._close = self._safe_float(self.current.get('Close'))
        return self._close
    
    @property
    def prev_close(self) -> Optional[float]:
        """Previous close price."""
        if self._prev_close is None:
            self._prev_close = self._safe_float(self.prev.get('Close'))
        return self._prev_close
    
    def get_fib_levels(self, window: int = 50) -> Dict[str, FibonacciLevel]:
        """Get Fibonacci levels calculated for given window."""
        if window in self._swing_data:
            return self._swing_data[window]['levels']
        
        high, low, high_idx, low_idx = self.swing_detector.detect_swings(window)
        swing_range = high - low
        
        if swing_range <= 0:
            return {}
        
        levels = self.fib_registry.get_all_levels()
        
        for level in levels.values():
            level.calculate_price(low, high)
        
        self._swing_data[window] = {
            'high': high,
            'low': low,
            'high_idx': high_idx,
            'low_idx': low_idx,
            'range': swing_range,
            'levels': levels
        }
        
        return levels
    
    def get_swing_data(self, window: int = 50) -> Dict:
        """Get full swing data for window."""
        if window not in self._swing_data:
            self.get_fib_levels(window)
        return self._swing_data.get(window, {})
    
    def get_tolerance(self, tolerance_type: str = 'standard') -> float:
        """Get adaptive tolerance."""
        return self.tolerance_calc.get_tolerance(tolerance_type)
    
    def price_at_level(
        self, 
        price: float, 
        level: FibonacciLevel, 
        tolerance: Optional[float] = None
    ) -> bool:
        """Check if price is at Fibonacci level within tolerance."""
        if tolerance is None:
            tolerance = self.get_tolerance()
        
        if price <= 0 or level.price <= 0:
            return False
        
        diff = abs(price - level.price) / price
        return diff < tolerance
    
    def price_crossed_level(
        self,
        prev_price: float,
        curr_price: float,
        level: FibonacciLevel
    ) -> str:
        """
        Check if price crossed a level.
        Returns: 'UP', 'DOWN', or 'NONE'
        """
        if prev_price < level.price <= curr_price:
            return 'UP'
        if prev_price > level.price >= curr_price:
            return 'DOWN'
        return 'NONE'


# =============================================================================
# SIGNAL GENERATORS
# =============================================================================

class PriceLevelSignals(SignalGenerator):
    """Generates signals for price at Fibonacci levels."""
    
    def generate(self, ctx: FibonacciContext) -> List[FibonacciSignal]:
        signals = []
        
        if ctx.close is None:
            return signals
        
        for window in [20, 50, 100, 200]:
            if window > len(ctx.df):
                continue
            
            levels = ctx.get_fib_levels(window)
            tolerance = ctx.get_tolerance()
            
            for key, level in levels.items():
                if ctx.price_at_level(ctx.close, level, tolerance):
                    window_label = f"{window}P" if window != 50 else ""
                    signals.append(FibonacciSignal(
                        signal=f"FIB {level.fib_type.value} {level.name}{window_label}",
                        description=f"Price at {level.name} {level.fib_type.value.lower()} "
                                   f"({window}-period swing)",
                        strength=level.strength.value,
                        category='FIB_PRICE_LEVEL',
                        timeframe=ctx.interval,
                        value=level.price,
                        metadata={
                            'distance_pct': abs(ctx.close - level.price) / ctx.close * 100,
                            'window': window,
                            'ratio': level.ratio
                        }
                    ))
        
        return signals


class BounceSignals(SignalGenerator):
    """Detects bounces off Fibonacci levels."""
    
    def generate(self, ctx: FibonacciContext) -> List[FibonacciSignal]:
        signals = []
        
        if ctx.close is None or ctx.prev_close is None:
            return signals
        
        if len(ctx.df) < 3:
            return signals
        
        levels = ctx.get_fib_levels()
        
        for key, level in levels.items():
            if level.fib_type not in [FibonacciType.RETRACE, FibonacciType.EXTENSION]:
                continue
            
            # Bullish bounce: price dipped below then closed above
            low = ctx._safe_float(ctx.current.get('Low'))
            if low is not None and low <= level.price < ctx.close:
                if ctx.close > ctx.prev_close:
                    signals.append(FibonacciSignal(
                        signal=f"FIB {level.name} BULLISH BOUNCE",
                        description=f"Bullish bounce off {level.name} Fibonacci level",
                        strength='SIGNIFICANT',
                        category='FIB_BOUNCE',
                        timeframe=ctx.interval,
                        value=level.price,
                        metadata={'bounce_type': 'BULLISH'}
                    ))
            
            # Bearish bounce: price spiked above then closed below
            high = ctx._safe_float(ctx.current.get('High'))
            if high is not None and high >= level.price > ctx.close:
                if ctx.close < ctx.prev_close:
                    signals.append(FibonacciSignal(
                        signal=f"FIB {level.name} BEARISH BOUNCE",
                        description=f"Bearish rejection from {level.name} Fibonacci level",
                        strength='SIGNIFICANT',
                        category='FIB_BOUNCE',
                        timeframe=ctx.interval,
                        value=level.price,
                        metadata={'bounce_type': 'BEARISH'}
                    ))
        
        return signals


class BreakoutSignals(SignalGenerator):
    """Detects breakouts through Fibonacci levels."""
    
    def generate(self, ctx: FibonacciContext) -> List[FibonacciSignal]:
        signals = []
        
        if ctx.close is None or ctx.prev_close is None:
            return signals
        
        levels = ctx.get_fib_levels()
        tolerance = ctx.get_tolerance('tight')
        
        for key, level in levels.items():
            cross = ctx.price_crossed_level(ctx.prev_close, ctx.close, level)
            
            if cross == 'UP':
                # Check for decisive break (>1% beyond level)
                break_pct = (ctx.close - level.price) / level.price
                if break_pct > 0.01:
                    strength = 'EXTREME' if break_pct > 0.02 else 'SIGNIFICANT'
                    signals.append(FibonacciSignal(
                        signal=f"FIB {level.name} BULLISH BREAKOUT",
                        description=f"Decisive break above {level.name} Fibonacci",
                        strength=strength,
                        category='FIB_BREAKOUT',
                        timeframe=ctx.interval,
                        value=level.price,
                        metadata={
                            'breakout_type': 'BULLISH',
                            'break_pct': break_pct * 100
                        }
                    ))
            
            elif cross == 'DOWN':
                break_pct = (level.price - ctx.close) / level.price
                if break_pct > 0.01:
                    strength = 'EXTREME' if break_pct > 0.02 else 'SIGNIFICANT'
                    signals.append(FibonacciSignal(
                        signal=f"FIB {level.name} BEARISH BREAKDOWN",
                        description=f"Decisive break below {level.name} Fibonacci",
                        strength=strength,
                        category='FIB_BREAKOUT',
                        timeframe=ctx.interval,
                        value=level.price,
                        metadata={
                            'breakout_type': 'BEARISH',
                            'break_pct': break_pct * 100
                        }
                    ))
        
        return signals


class ChannelSignals(SignalGenerator):
    """Detects price within Fibonacci channels/zones."""
    
    def generate(self, ctx: FibonacciContext) -> List[FibonacciSignal]:
        signals = []
        
        if ctx.close is None:
            return signals
        
        levels = ctx.get_fib_levels()
        
        # Group by type
        retracements = sorted(
            [l for l in levels.values() if l.fib_type == FibonacciType.RETRACE],
            key=lambda x: x.ratio
        )
        extensions = sorted(
            [l for l in levels.values() if l.fib_type == FibonacciType.EXTENSION],
            key=lambda x: x.ratio
        )
        
        # Retracement channels
        for i in range(len(retracements) - 1):
            lower = retracements[i]
            upper = retracements[i + 1]
            
            if lower.price <= ctx.close <= upper.price:
                # Determine position within channel
                channel_range = upper.price - lower.price
                if channel_range > 0:
                    position = (ctx.close - lower.price) / channel_range
                    position_label = (
                        "LOWER" if position < 0.33 else
                        "MIDDLE" if position < 0.66 else
                        "UPPER"
                    )
                    
                    signals.append(FibonacciSignal(
                        signal=f"FIB CHANNEL {lower.name}-{upper.name} {position_label}",
                        description=f"Price in {position_label.lower()} {lower.name}-{upper.name} channel",
                        strength='MODERATE',
                        category='FIB_CHANNEL',
                        timeframe=ctx.interval,
                        value=(lower.price + upper.price) / 2,
                        metadata={
                            'channel_position': position,
                            'lower_level': lower.name,
                            'upper_level': upper.name
                        }
                    ))
        
        # Extension channels
        for i in range(len(extensions) - 1):
            lower = extensions[i]
            upper = extensions[i + 1]
            
            if lower.price <= ctx.close <= upper.price:
                signals.append(FibonacciSignal(
                    signal=f"FIB EXT ZONE {lower.name}-{upper.name}",
                    description=f"Price in extension zone {lower.name}-{upper.name}",
                    strength='SIGNIFICANT',
                    category='FIB_EXT_CHANNEL',
                    timeframe=ctx.interval,
                    value=(lower.price + upper.price) / 2,
                    metadata={
                        'lower_level': lower.name,
                        'upper_level': upper.name
                    }
                ))
        
        return signals


class ClusterSignals(SignalGenerator):
    """Detects Fibonacci level clusters and confluence zones."""
    
    def generate(self, ctx: FibonacciContext) -> List[FibonacciSignal]:
        signals = []
        
        if ctx.close is None:
            return signals
        
        swing_data = ctx.get_swing_data()
        if not swing_data:
            return signals
        
        swing_range = swing_data['range']
        cluster_tolerance = swing_range * 0.02
        
        levels = ctx.get_fib_levels()
        
        # Group levels by price cluster
        price_clusters: Dict[float, List[FibonacciLevel]] = {}
        
        for level in levels.values():
            cluster_key = round(level.price / cluster_tolerance) * cluster_tolerance
            
            if cluster_key not in price_clusters:
                price_clusters[cluster_key] = []
            price_clusters[cluster_key].append(level)
        
        # Find clusters near current price
        tolerance = ctx.get_tolerance('wide')
        
        for cluster_price, cluster_levels in price_clusters.items():
            if len(cluster_levels) >= 2:
                if abs(ctx.close - cluster_price) / ctx.close < tolerance:
                    level_names = [l.name for l in cluster_levels]
                    level_types = set(l.fib_type.value for l in cluster_levels)
                    
                    strength = (
                        'EXTREME' if len(cluster_levels) >= 4 else
                        'STRONG' if len(cluster_levels) >= 3 else
                        'SIGNIFICANT'
                    )
                    
                    signals.append(FibonacciSignal(
                        signal=f"FIB CLUSTER {len(cluster_levels)} LEVELS",
                        description=f"Fibonacci confluence: {', '.join(level_names)}",
                        strength=strength,
                        category='FIB_CLUSTER',
                        timeframe=ctx.interval,
                        value=cluster_price,
                        metadata={
                            'cluster_count': len(cluster_levels),
                            'level_names': level_names,
                            'level_types': list(level_types)
                        }
                    ))
        
        return signals


class MultiTimeframeClusterSignals(SignalGenerator):
    """Detects clusters across multiple lookback windows."""
    
    def generate(self, ctx: FibonacciContext) -> List[FibonacciSignal]:
        signals = []
        
        if ctx.close is None:
            return signals
        
        windows = [20, 50, 100, 200]
        all_levels: List[Tuple[int, FibonacciLevel]] = []
        
        # Collect levels from all windows
        for window in windows:
            if window > len(ctx.df):
                continue
            levels = ctx.get_fib_levels(window)
            for level in levels.values():
                all_levels.append((window, level))
        
        # Find price levels that appear across multiple windows
        tolerance = ctx.get_tolerance('standard')
        price_groups: Dict[float, List[Tuple[int, FibonacciLevel]]] = {}
        
        for window, level in all_levels:
            # Round to cluster
            cluster_key = round(level.price / (ctx.close * tolerance)) * (ctx.close * tolerance)
            
            if cluster_key not in price_groups:
                price_groups[cluster_key] = []
            price_groups[cluster_key].append((window, level))
        
        # Find multi-window confluences near current price
        for cluster_price, group in price_groups.items():
            windows_in_cluster = set(w for w, _ in group)
            
            if len(windows_in_cluster) >= 2 and abs(ctx.close - cluster_price) / ctx.close < tolerance * 2:
                level_desc = [f"{l.name}({w}P)" for w, l in group[:5]]  # Limit description
                
                strength = (
                    'EXTREME' if len(windows_in_cluster) >= 3 else
                    'SIGNIFICANT'
                )
                
                signals.append(FibonacciSignal(
                    signal=f"FIB MTF CONFLUENCE {len(windows_in_cluster)} WINDOWS",
                    description=f"Multi-timeframe confluence: {', '.join(level_desc)}",
                    strength=strength,
                    category='FIB_MTF_CLUSTER',
                    timeframe=ctx.interval,
                    value=cluster_price,
                    metadata={
                        'windows': list(windows_in_cluster),
                        'total_levels': len(group)
                    }
                ))
        
        return signals


class TimeZoneSignals(SignalGenerator):
    """Fibonacci time zone analysis."""
    
    def generate(self, ctx: FibonacciContext) -> List[FibonacciSignal]:
        signals = []
        
        swing_data = ctx.get_swing_data()
        if not swing_data:
            return signals
        
        current_bar = len(ctx.df)
        pivot_bar = min(swing_data['high_idx'], swing_data['low_idx'])
        bars_from_pivot = current_bar - pivot_bar if pivot_bar < current_bar else 0
        
        fib_times = FibonacciLevelRegistry.TIME_NUMBERS
        
        aligned_zones = []
        
        for fib_num in fib_times:
            # Check if current bar is at or near Fibonacci time from pivot
            if fib_num <= bars_from_pivot:
                remainder = bars_from_pivot % fib_num
                if remainder <= 1 or (fib_num - remainder) <= 1:
                    aligned_zones.append(fib_num)
                    
                    signals.append(FibonacciSignal(
                        signal=f"FIB TIME ZONE {fib_num}",
                        description=f"At {fib_num}-period Fibonacci time zone",
                        strength='SIGNIFICANT' if fib_num >= 21 else 'MODERATE',
                        category='FIB_TIME',
                        timeframe=ctx.interval,
                        value=float(fib_num),
                        metadata={
                            'bars_from_pivot': bars_from_pivot,
                            'fib_number': fib_num
                        }
                    ))
        
        # Time zone cluster
        if len(aligned_zones) >= 2:
            signals.append(FibonacciSignal(
                signal=f"FIB TIME CLUSTER {len(aligned_zones)}",
                description=f"Multiple time zones aligned: {', '.join(map(str, aligned_zones))}",
                strength='EXTREME',
                category='FIB_TIME_CLUSTER',
                timeframe=ctx.interval,
                value=float(len(aligned_zones)),
                metadata={'aligned_zones': aligned_zones}
            ))
        
        return signals


class VolumeConfirmationSignals(SignalGenerator):
    """Volume-confirmed Fibonacci signals."""
    
    def generate(self, ctx: FibonacciContext) -> List[FibonacciSignal]:
        signals = []
        
        if ctx.close is None or 'Volume' not in ctx.df.columns:
            return signals
        
        volume = ctx._safe_float(ctx.current.get('Volume'))
        if volume is None or volume <= 0:
            return signals
        
        # Calculate volume metrics
        if len(ctx.df) >= 20:
            avg_volume = ctx.df['Volume'].iloc[-20:].mean()
            if avg_volume <= 0:
                return signals
            
            volume_ratio = volume / avg_volume
            
            levels = ctx.get_fib_levels()
            tolerance = ctx.get_tolerance()
            
            # Find nearest level
            nearest = min(
                levels.values(),
                key=lambda l: abs(l.price - ctx.close) if l.price > 0 else float('inf')
            )
            
            if ctx.price_at_level(ctx.close, nearest, tolerance):
                if volume_ratio > 1.5:
                    strength = (
                        'EXTREME' if volume_ratio > 3.0 else
                        'STRONG' if volume_ratio > 2.0 else
                        'SIGNIFICANT'
                    )
                    
                    signals.append(FibonacciSignal(
                        signal=f"FIB {nearest.name} + VOLUME {volume_ratio:.1f}X",
                        description=f"{nearest.name} Fibonacci with {volume_ratio:.1f}x average volume",
                        strength=strength,
                        category='FIB_VOLUME',
                        timeframe=ctx.interval,
                        value=nearest.price,
                        metadata={
                            'volume_ratio': volume_ratio,
                            'fib_level': nearest.name
                        }
                    ))
                
                # Volume spike
                if volume_ratio > 2.5:
                    signals.append(FibonacciSignal(
                        signal="FIB + VOLUME SPIKE",
                        description=f"Fibonacci level with extreme volume spike ({volume_ratio:.1f}x)",
                        strength='EXTREME',
                        category='FIB_VOLUME_SPIKE',
                        timeframe=ctx.interval,
                        value=ctx.close,
                        metadata={'volume_ratio': volume_ratio}
                    ))
        
        return signals


class MovingAverageConfluenceSignals(SignalGenerator):
    """Fibonacci + Moving Average confluence signals."""
    
    MA_COLUMNS = ['SMA_20', 'SMA_50', 'SMA_100', 'SMA_200', 'EMA_12', 'EMA_26', 'EMA_50']
    
    def generate(self, ctx: FibonacciContext) -> List[FibonacciSignal]:
        signals = []
        
        if ctx.close is None:
            return signals
        
        levels = ctx.get_fib_levels()
        tolerance = ctx.get_tolerance('wide')
        
        for ma_col in self.MA_COLUMNS:
            if ma_col not in ctx.df.columns:
                continue
            
            ma_value = ctx._safe_float(ctx.current.get(ma_col))
            if ma_value is None or ma_value <= 0:
                continue
            
            # Find Fibonacci level closest to MA
            for level in levels.values():
                if abs(ma_value - level.price) / ma_value < tolerance:
                    # Check if price is also near this confluence
                    if abs(ctx.close - level.price) / ctx.close < tolerance * 2:
                        signals.append(FibonacciSignal(
                            signal=f"FIB {level.name} + {ma_col} CONFLUENCE",
                            description=f"{level.name} Fibonacci converging with {ma_col}",
                            strength='SIGNIFICANT',
                            category='FIB_MA_CONFLUENCE',
                            timeframe=ctx.interval,
                            value=level.price,
                            metadata={
                                'ma_type': ma_col,
                                'ma_value': ma_value,
                                'fib_level': level.name
                            }
                        ))
        
        return signals


class RSIDivergenceSignals(SignalGenerator):
    """Fibonacci + RSI divergence signals."""
    
    def generate(self, ctx: FibonacciContext) -> List[FibonacciSignal]:
        signals = []
        
        if ctx.close is None or 'RSI' not in ctx.df.columns:
            return signals
        
        if len(ctx.df) < 5:
            return signals
        
        rsi = ctx._safe_float(ctx.current.get('RSI'))
        prev_rsi = ctx._safe_float(ctx.prev.get('RSI'))
        
        if rsi is None or prev_rsi is None:
            return signals
        
        swing_data = ctx.get_swing_data()
        if not swing_data:
            return signals
        
        low = swing_data['low']
        high = swing_data['high']
        swing_range = swing_data['range']
        
        # Check recent price action for divergence
        price_5_ago = ctx._safe_float(ctx.df['Close'].iloc[-5])
        rsi_5_ago = ctx._safe_float(ctx.df['RSI'].iloc[-5]) if 'RSI' in ctx.df.columns else None
        
        if price_5_ago is None or rsi_5_ago is None:
            return signals
        
        # Bullish divergence: price lower, RSI higher (at support levels)
        if ctx.close < price_5_ago and rsi > rsi_5_ago:
            # Check if at Fibonacci support
            if ctx.close < low + (0.5 * swing_range):
                levels = ctx.get_fib_levels()
                for level in levels.values():
                    if level.fib_type == FibonacciType.RETRACE and level.ratio <= 0.618:
                        if ctx.price_at_level(ctx.close, level, ctx.get_tolerance('wide')):
                            signals.append(FibonacciSignal(
                                signal=f"FIB {level.name} + BULLISH RSI DIVERGENCE",
                                description=f"Bullish RSI divergence at {level.name} Fibonacci support",
                                strength='SIGNIFICANT',
                                category='FIB_RSI_DIVERGENCE',
                                timeframe=ctx.interval,
                                value=level.price,
                                metadata={
                                    'divergence_type': 'BULLISH',
                                    'rsi': rsi,
                                    'prev_rsi': rsi_5_ago
                                }
                            ))
                            break
        
        # Bearish divergence: price higher, RSI lower (at resistance levels)
        if ctx.close > price_5_ago and rsi < rsi_5_ago:
            if ctx.close > low + (0.5 * swing_range):
                levels = ctx.get_fib_levels()
                for level in levels.values():
                    if level.fib_type == FibonacciType.EXTENSION or (
                        level.fib_type == FibonacciType.RETRACE and level.ratio >= 0.618
                    ):
                        if ctx.price_at_level(ctx.close, level, ctx.get_tolerance('wide')):
                            signals.append(FibonacciSignal(
                                signal=f"FIB {level.name} + BEARISH RSI DIVERGENCE",
                                description=f"Bearish RSI divergence at {level.name} Fibonacci resistance",
                                strength='SIGNIFICANT',
                                category='FIB_RSI_DIVERGENCE',
                                timeframe=ctx.interval,
                                value=level.price,
                                metadata={
                                    'divergence_type': 'BEARISH',
                                    'rsi': rsi,
                                    'prev_rsi': rsi_5_ago
                                }
                            ))
                            break
        
        # Oversold/Overbought at Fibonacci
        levels = ctx.get_fib_levels()
        for level in levels.values():
            if ctx.price_at_level(ctx.close, level, ctx.get_tolerance()):
                if rsi < 30:
                    signals.append(FibonacciSignal(
                        signal=f"FIB {level.name} + RSI OVERSOLD",
                        description=f"RSI oversold ({rsi:.0f}) at {level.name} Fibonacci",
                        strength='SIGNIFICANT',
                        category='FIB_RSI_EXTREME',
                        timeframe=ctx.interval,
                        value=level.price,
                        metadata={'rsi': rsi, 'condition': 'OVERSOLD'}
                    ))
                elif rsi > 70:
                    signals.append(FibonacciSignal(
                        signal=f"FIB {level.name} + RSI OVERBOUGHT",
                        description=f"RSI overbought ({rsi:.0f}) at {level.name} Fibonacci",
                        strength='SIGNIFICANT',
                        category='FIB_RSI_EXTREME',
                        timeframe=ctx.interval,
                        value=level.price,
                        metadata={'rsi': rsi, 'condition': 'OVERBOUGHT'}
                    ))
        
        return signals


class MACDConfluenceSignals(SignalGenerator):
    """Fibonacci + MACD confluence signals."""
    
    def generate(self, ctx: FibonacciContext) -> List[FibonacciSignal]:
        signals = []
        
        if ctx.close is None:
            return signals
        
        # Check for MACD columns
        macd_cols = {'MACD', 'MACD_Signal', 'MACD_Histogram'}
        if not macd_cols.issubset(set(ctx.df.columns)):
            return signals
        
        macd = ctx._safe_float(ctx.current.get('MACD'))
        macd_signal = ctx._safe_float(ctx.current.get('MACD_Signal'))
        macd_hist = ctx._safe_float(ctx.current.get('MACD_Histogram'))
        
        prev_macd = ctx._safe_float(ctx.prev.get('MACD'))
        prev_signal = ctx._safe_float(ctx.prev.get('MACD_Signal'))
        
        if macd is None or macd_signal is None:
            return signals
        
        levels = ctx.get_fib_levels()
        tolerance = ctx.get_tolerance()
        
        # MACD crossover at Fibonacci level
        if prev_macd is not None and prev_signal is not None:
            # Bullish crossover
            if prev_macd < prev_signal and macd > macd_signal:
                for level in levels.values():
                    if ctx.price_at_level(ctx.close, level, tolerance):
                        signals.append(FibonacciSignal(
                            signal=f"FIB {level.name} + MACD BULLISH CROSS",
                            description=f"MACD bullish crossover at {level.name} Fibonacci",
                            strength='SIGNIFICANT',
                            category='FIB_MACD_CROSS',
                            timeframe=ctx.interval,
                            value=level.price,
                            metadata={'cross_type': 'BULLISH', 'macd': macd}
                        ))
                        break
            
            # Bearish crossover
            if prev_macd > prev_signal and macd < macd_signal:
                for level in levels.values():
                    if ctx.price_at_level(ctx.close, level, tolerance):
                        signals.append(FibonacciSignal(
                            signal=f"FIB {level.name} + MACD BEARISH CROSS",
                            description=f"MACD bearish crossover at {level.name} Fibonacci",
                            strength='SIGNIFICANT',
                            category='FIB_MACD_CROSS',
                            timeframe=ctx.interval,
                            value=level.price,
                            metadata={'cross_type': 'BEARISH', 'macd': macd}
                        ))
                        break
        
        # MACD histogram reversal at Fibonacci
        if macd_hist is not None and len(ctx.df) >= 3:
            prev_hist = ctx._safe_float(ctx.df['MACD_Histogram'].iloc[-2])
            prev_prev_hist = ctx._safe_float(ctx.df['MACD_Histogram'].iloc[-3])
            
            if prev_hist is not None and prev_prev_hist is not None:
                # Histogram turning up
                if macd_hist > prev_hist < prev_prev_hist:
                    for level in levels.values():
                        if level.fib_type == FibonacciType.RETRACE:
                            if ctx.price_at_level(ctx.close, level, tolerance):
                                signals.append(FibonacciSignal(
                                    signal=f"FIB {level.name} + MACD HIST REVERSAL UP",
                                    description=f"MACD histogram turning up at {level.name}",
                                    strength='MODERATE',
                                    category='FIB_MACD_HIST',
                                    timeframe=ctx.interval,
                                    value=level.price,
                                    metadata={'histogram': macd_hist}
                                ))
                                break
        
        return signals


class StochasticConfluenceSignals(SignalGenerator):
    """Fibonacci + Stochastic confluence signals."""
    
    def generate(self, ctx: FibonacciContext) -> List[FibonacciSignal]:
        signals = []
        
        if ctx.close is None:
            return signals
        
        if 'Stoch_K' not in ctx.df.columns or 'Stoch_D' not in ctx.df.columns:
            return signals
        
        stoch_k = ctx._safe_float(ctx.current.get('Stoch_K'))
        stoch_d = ctx._safe_float(ctx.current.get('Stoch_D'))
        
        if stoch_k is None or stoch_d is None:
            return signals
        
        levels = ctx.get_fib_levels()
        tolerance = ctx.get_tolerance()
        
        for level in levels.values():
            if not ctx.price_at_level(ctx.close, level, tolerance):
                continue
            
            # Stochastic extreme at Fibonacci
            if stoch_k < 20 and stoch_d < 20:
                signals.append(FibonacciSignal(
                    signal=f"FIB {level.name} + STOCH OVERSOLD",
                    description=f"Stochastic oversold at {level.name} Fibonacci",
                    strength='SIGNIFICANT',
                    category='FIB_STOCH',
                    timeframe=ctx.interval,
                    value=level.price,
                    metadata={'stoch_k': stoch_k, 'stoch_d': stoch_d, 'condition': 'OVERSOLD'}
                ))
            
            elif stoch_k > 80 and stoch_d > 80:
                signals.append(FibonacciSignal(
                    signal=f"FIB {level.name} + STOCH OVERBOUGHT",
                    description=f"Stochastic overbought at {level.name} Fibonacci",
                    strength='SIGNIFICANT',
                    category='FIB_STOCH',
                    timeframe=ctx.interval,
                    value=level.price,
                    metadata={'stoch_k': stoch_k, 'stoch_d': stoch_d, 'condition': 'OVERBOUGHT'}
                ))
            
            # Stochastic crossover
            if len(ctx.df) >= 2:
                prev_k = ctx._safe_float(ctx.prev.get('Stoch_K'))
                prev_d = ctx._safe_float(ctx.prev.get('Stoch_D'))
                
                if prev_k is not None and prev_d is not None:
                    if prev_k < prev_d and stoch_k > stoch_d:  # Bullish cross
                        signals.append(FibonacciSignal(
                            signal=f"FIB {level.name} + STOCH BULLISH CROSS",
                            description=f"Stochastic bullish cross at {level.name}",
                            strength='MODERATE',
                            category='FIB_STOCH_CROSS',
                            timeframe=ctx.interval,
                            value=level.price,
                            metadata={'cross_type': 'BULLISH'}
                        ))
                    
                    elif prev_k > prev_d and stoch_k < stoch_d:  # Bearish cross
                        signals.append(FibonacciSignal(
                            signal=f"FIB {level.name} + STOCH BEARISH CROSS",
                            description=f"Stochastic bearish cross at {level.name}",
                            strength='MODERATE',
                            category='FIB_STOCH_CROSS',
                            timeframe=ctx.interval,
                            value=level.price,
                            metadata={'cross_type': 'BEARISH'}
                        ))
        
        return signals


class HarmonicPatternSignals(SignalGenerator):
    """
    Detects harmonic pattern completion at Fibonacci levels.
    Patterns: Gartley, Bat, Butterfly, Crab, Shark
    """
    
    # Harmonic pattern Fibonacci ratios
    PATTERNS = {
        'GARTLEY': {
            'XAB': (0.618, 0.618),
            'ABC': (0.382, 0.886),
            'BCD': (1.272, 1.618),
            'XAD': (0.786, 0.786)
        },
        'BAT': {
            'XAB': (0.382, 0.500),
            'ABC': (0.382, 0.886),
            'BCD': (1.618, 2.618),
            'XAD': (0.886, 0.886)
        },
        'BUTTERFLY': {
            'XAB': (0.786, 0.786),
            'ABC': (0.382, 0.886),
            'BCD': (1.618, 2.618),
            'XAD': (1.270, 1.618)
        },
        'CRAB': {
            'XAB': (0.382, 0.618),
            'ABC': (0.382, 0.886),
            'BCD': (2.240, 3.618),
            'XAD': (1.618, 1.618)
        },
        'SHARK': {
            'XAB': (0.886, 1.130),
            'ABC': (1.130, 1.618),
            'BCD': (1.618, 2.240),
            'XAD': (0.886, 1.130)
        }
    }
    
    def generate(self, ctx: FibonacciContext) -> List[FibonacciSignal]:
        signals = []
        
        if ctx.close is None or len(ctx.df) < 50:
            return signals
        
        # Find potential XABCD points
        swing_data = ctx.get_swing_data(50)
        if not swing_data:
            return signals
        
        # Simplified harmonic detection - check if current price
        # is at a harmonic pattern completion ratio
        
        levels = ctx.get_fib_levels()
        tolerance = ctx.get_tolerance('wide')
        
        for pattern_name, ratios in self.PATTERNS.items():
            xad_ratio = ratios['XAD'][0]  # Use first ratio
            
            # Check if price is at XAD completion level
            harmonic_level = swing_data['low'] + (xad_ratio * swing_data['range'])
            
            if abs(ctx.close - harmonic_level) / ctx.close < tolerance:
                signals.append(FibonacciSignal(
                    signal=f"FIB HARMONIC {pattern_name} COMPLETION",
                    description=f"Potential {pattern_name} pattern completion at {xad_ratio*100:.1f}%",
                    strength='SIGNIFICANT',
                    category='FIB_HARMONIC',
                    timeframe=ctx.interval,
                    value=harmonic_level,
                    metadata={
                        'pattern': pattern_name,
                        'xad_ratio': xad_ratio
                    }
                ))
        
        return signals


class ElliottWaveSignals(SignalGenerator):
    """Elliott Wave Fibonacci relationship signals."""
    
    def generate(self, ctx: FibonacciContext) -> List[FibonacciSignal]:
        signals = []
        
        if ctx.close is None or len(ctx.df) < 100:
            return signals
        
        tolerance = ctx.get_tolerance('wide')
        
        # Divide data into wave segments (simplified)
        segment_size = 20
        waves = []
        
        for i in range(5):
            start_idx = -(100 - i * segment_size)
            end_idx = -(100 - (i + 1) * segment_size) if i < 4 else None
            
            segment = ctx.df.iloc[start_idx:end_idx] if end_idx else ctx.df.iloc[start_idx:]
            if len(segment) > 0:
                waves.append({
                    'high': segment['High'].max(),
                    'low': segment['Low'].min(),
                    'range': segment['High'].max() - segment['Low'].min()
                })
        
        if len(waves) < 3:
            return signals
        
        wave1_range = waves[0]['range']
        
        if wave1_range <= 0:
            return signals
        
        # Wave 3 = 1.618x Wave 1
        wave3_target = waves[0]['low'] + (1.618 * wave1_range)
        if abs(ctx.close - wave3_target) / ctx.close < tolerance:
            signals.append(FibonacciSignal(
                signal="ELLIOTT WAVE 3 = 161.8% WAVE 1",
                description="Price at Elliott Wave 3 extension (1.618x Wave 1)",
                strength='SIGNIFICANT',
                category='ELLIOTT_FIB',
                timeframe=ctx.interval,
                value=wave3_target,
                metadata={'wave_ratio': 1.618}
            ))
        
        # Wave 3 = 2.618x Wave 1 (extended)
        wave3_ext_target = waves[0]['low'] + (2.618 * wave1_range)
        if abs(ctx.close - wave3_ext_target) / ctx.close < tolerance:
            signals.append(FibonacciSignal(
                signal="ELLIOTT WAVE 3 = 261.8% WAVE 1 (EXTENDED)",
                description="Price at extended Wave 3 target (2.618x Wave 1)",
                strength='SIGNIFICANT',
                category='ELLIOTT_FIB',
                timeframe=ctx.interval,
                value=wave3_ext_target,
                metadata={'wave_ratio': 2.618}
            ))
        
        # Wave 5 = Wave 1 (equality)
        wave5_eq_target = waves[0]['low'] + wave1_range + waves[2]['range'] + wave1_range
        if abs(ctx.close - wave5_eq_target) / ctx.close < tolerance:
            signals.append(FibonacciSignal(
                signal="ELLIOTT WAVE 5 = WAVE 1",
                description="Price at Wave 5 equality with Wave 1",
                strength='MODERATE',
                category='ELLIOTT_FIB',
                timeframe=ctx.interval,
                value=wave5_eq_target,
                metadata={'wave_ratio': 1.0}
            ))
        
        # Wave 2 retracement check
        if len(waves) >= 2:
            wave2_retrace = waves[1]['range'] / wave1_range if wave1_range > 0 else 0
            
            if 0.50 <= wave2_retrace <= 0.62:
                signals.append(FibonacciSignal(
                    signal="ELLIOTT WAVE 2 RETRACE 50-61.8%",
                    description=f"Wave 2 retraces {wave2_retrace*100:.1f}% of Wave 1",
                    strength='MODERATE',
                    category='ELLIOTT_FIB',
                    timeframe=ctx.interval,
                    value=wave2_retrace,
                    metadata={'retrace_pct': wave2_retrace}
                ))
            
            elif 0.38 <= wave2_retrace < 0.50:
                signals.append(FibonacciSignal(
                    signal="ELLIOTT WAVE 2 SHALLOW RETRACE 38.2%",
                    description=f"Shallow Wave 2 retrace ({wave2_retrace*100:.1f}%)",
                    strength='MODERATE',
                    category='ELLIOTT_FIB',
                    timeframe=ctx.interval,
                    value=wave2_retrace,
                    metadata={'retrace_pct': wave2_retrace}
                ))
        
        return signals


class CandlePatternAtFibSignals(SignalGenerator):
    """Detects candlestick reversal patterns at Fibonacci levels."""
    
    def generate(self, ctx: FibonacciContext) -> List[FibonacciSignal]:
        signals = []
        
        if ctx.close is None or len(ctx.df) < 3:
            return signals
        
        # Current candle data
        open_price = ctx._safe_float(ctx.current.get('Open'))
        high = ctx._safe_float(ctx.current.get('High'))
        low = ctx._safe_float(ctx.current.get('Low'))
        close = ctx.close
        
        if any(v is None for v in [open_price, high, low]):
            return signals
        
        body = abs(close - open_price)
        upper_wick = high - max(close, open_price)
        lower_wick = min(close, open_price) - low
        candle_range = high - low
        
        if candle_range <= 0:
            return signals
        
        levels = ctx.get_fib_levels()
        tolerance = ctx.get_tolerance()
        
        for level in levels.values():
            if not ctx.price_at_level(close, level, tolerance * 2):
                continue
            
            # Hammer/Pin bar (bullish reversal)
            if lower_wick > body * 2 and upper_wick < body * 0.5:
                if low <= level.price:
                    signals.append(FibonacciSignal(
                        signal=f"FIB {level.name} + HAMMER",
                        description=f"Bullish hammer at {level.name} Fibonacci",
                        strength='SIGNIFICANT',
                        category='FIB_CANDLE_REVERSAL',
                        timeframe=ctx.interval,
                        value=level.price,
                        metadata={'pattern': 'HAMMER', 'direction': 'BULLISH'}
                    ))
            
            # Shooting star (bearish reversal)
            if upper_wick > body * 2 and lower_wick < body * 0.5:
                if high >= level.price:
                    signals.append(FibonacciSignal(
                        signal=f"FIB {level.name} + SHOOTING STAR",
                        description=f"Bearish shooting star at {level.name} Fibonacci",
                        strength='SIGNIFICANT',
                        category='FIB_CANDLE_REVERSAL',
                        timeframe=ctx.interval,
                        value=level.price,
                        metadata={'pattern': 'SHOOTING_STAR', 'direction': 'BEARISH'}
                    ))
            
            # Doji at Fibonacci
            if body < candle_range * 0.1:
                signals.append(FibonacciSignal(
                    signal=f"FIB {level.name} + DOJI",
                    description=f"Indecision doji at {level.name} Fibonacci",
                    strength='MODERATE',
                    category='FIB_CANDLE_REVERSAL',
                    timeframe=ctx.interval,
                    value=level.price,
                    metadata={'pattern': 'DOJI'}
                ))
            
            # Engulfing patterns (need previous candle)
            prev_open = ctx._safe_float(ctx.prev.get('Open'))
            prev_close = ctx._safe_float(ctx.prev.get('Close'))
            
            if prev_open is not None and prev_close is not None:
                prev_body = abs(prev_close - prev_open)
                
                # Bullish engulfing
                if (close > open_price and  # Current is bullish
                    prev_close < prev_open and  # Previous is bearish
                    open_price < prev_close and  # Opens below prev close
                    close > prev_open):  # Closes above prev open
                    signals.append(FibonacciSignal(
                        signal=f"FIB {level.name} + BULLISH ENGULFING",
                        description=f"Bullish engulfing at {level.name} Fibonacci",
                        strength='SIGNIFICANT',
                        category='FIB_CANDLE_REVERSAL',
                        timeframe=ctx.interval,
                        value=level.price,
                        metadata={'pattern': 'BULLISH_ENGULFING'}
                    ))
                
                # Bearish engulfing
                if (close < open_price and  # Current is bearish
                    prev_close > prev_open and  # Previous is bullish
                    open_price > prev_close and  # Opens above prev close
                    close < prev_open):  # Closes below prev open
                    signals.append(FibonacciSignal(
                        signal=f"FIB {level.name} + BEARISH ENGULFING",
                        description=f"Bearish engulfing at {level.name} Fibonacci",
                        strength='SIGNIFICANT',
                        category='FIB_CANDLE_REVERSAL',
                        timeframe=ctx.interval,
                        value=level.price,
                        metadata={'pattern': 'BEARISH_ENGULFING'}
                    ))
        
        return signals


class GoldenPocketSignals(SignalGenerator):
    """
    Detects price in the 'Golden Pocket' zone (61.8% - 65% retracement).
    This is considered a high-probability reversal zone.
    """
    
    def generate(self, ctx: FibonacciContext) -> List[FibonacciSignal]:
        signals = []
        
        if ctx.close is None:
            return signals
        
        for window in [20, 50, 100]:
            if window > len(ctx.df):
                continue
            
            swing_data = ctx.get_swing_data(window)
            if not swing_data:
                continue
            
            low = swing_data['low']
            high = swing_data['high']
            swing_range = swing_data['range']
            
            if swing_range <= 0:
                continue
            
            # Golden pocket boundaries
            pocket_low = low + (0.618 * swing_range)
            pocket_high = low + (0.65 * swing_range)
            
            if pocket_low <= ctx.close <= pocket_high:
                # Calculate position within pocket
                pocket_position = (ctx.close - pocket_low) / (pocket_high - pocket_low)
                
                signals.append(FibonacciSignal(
                    signal=f"FIB GOLDEN POCKET ({window}P)",
                    description=f"Price in Golden Pocket zone (61.8%-65%) on {window}-period swing",
                    strength='SIGNIFICANT',
                    category='FIB_GOLDEN_POCKET',
                    timeframe=ctx.interval,
                    value=(pocket_low + pocket_high) / 2,
                    metadata={
                        'window': window,
                        'pocket_position': pocket_position,
                        'pocket_low': pocket_low,
                        'pocket_high': pocket_high
                    }
                ))
        
        return signals


class FibonacciSpeedResistanceSignals(SignalGenerator):
    """
    Speed resistance lines (1/3 and 2/3 of move).
    These are key levels for trend strength assessment.
    """
    
    def generate(self, ctx: FibonacciContext) -> List[FibonacciSignal]:
        signals = []
        
        if ctx.close is None:
            return signals
        
        swing_data = ctx.get_swing_data()
        if not swing_data:
            return signals
        
        low = swing_data['low']
        high = swing_data['high']
        swing_range = swing_data['range']
        
        if swing_range <= 0:
            return signals
        
        tolerance = ctx.get_tolerance()
        
        # Speed resistance levels
        speed_levels = [
            (1/3, 'SPEED 1/3', 'First speed resistance'),
            (2/3, 'SPEED 2/3', 'Second speed resistance'),
            (1/4, 'SPEED 1/4', 'Quarter speed line'),
            (3/4, 'SPEED 3/4', 'Three-quarter speed line')
        ]
        
        for ratio, name, desc in speed_levels:
            level_price = low + (ratio * swing_range)
            
            if abs(ctx.close - level_price) / ctx.close < tolerance:
                signals.append(FibonacciSignal(
                    signal=f"FIB {name}",
                    description=f"Price at {desc} ({ratio*100:.1f}%)",
                    strength='MODERATE',
                    category='FIB_SPEED_RESISTANCE',
                    timeframe=ctx.interval,
                    value=level_price,
                    metadata={'ratio': ratio, 'speed_type': name}
                ))
        
        return signals


class TrendLineConfluenceSignals(SignalGenerator):
    """Detects when Fibonacci levels align with trend lines."""
    
    def generate(self, ctx: FibonacciContext) -> List[FibonacciSignal]:
        signals = []
        
        if ctx.close is None or len(ctx.df) < 20:
            return signals
        
        # Calculate simple trend lines using linear regression
        closes = ctx.df['Close'].iloc[-20:].values
        x = np.arange(len(closes))
        
        # Linear regression
        slope, intercept = np.polyfit(x, closes, 1)
        trend_value = slope * (len(closes) - 1) + intercept
        
        levels = ctx.get_fib_levels()
        tolerance = ctx.get_tolerance('wide')
        
        for level in levels.values():
            # Check if trend line value is near Fibonacci level
            if abs(trend_value - level.price) / trend_value < tolerance:
                # And price is also near this area
                if abs(ctx.close - level.price) / ctx.close < tolerance * 2:
                    trend_direction = 'UPTREND' if slope > 0 else 'DOWNTREND'
                    
                    signals.append(FibonacciSignal(
                        signal=f"FIB {level.name} + TRENDLINE CONFLUENCE",
                        description=f"{level.name} Fibonacci aligns with {trend_direction.lower()} line",
                        strength='SIGNIFICANT',
                        category='FIB_TRENDLINE',
                        timeframe=ctx.interval,
                        value=level.price,
                        metadata={
                            'trend_direction': trend_direction,
                            'slope': slope,
                            'trend_value': trend_value
                        }
                    ))
        
        return signals


class PriceActionMomentumSignals(SignalGenerator):
    """Price momentum signals at Fibonacci levels."""
    
    def generate(self, ctx: FibonacciContext) -> List[FibonacciSignal]:
        signals = []
        
        if ctx.close is None or len(ctx.df) < 5:
            return signals
        
        # Calculate momentum
        close_5_ago = ctx._safe_float(ctx.df['Close'].iloc[-5])
        if close_5_ago is None or close_5_ago <= 0:
            return signals
        
        momentum_pct = (ctx.close - close_5_ago) / close_5_ago * 100
        
        levels = ctx.get_fib_levels()
        tolerance = ctx.get_tolerance()
        
        for level in levels.values():
            if not ctx.price_at_level(ctx.close, level, tolerance):
                continue
            
            # Strong upward momentum at Fibonacci
            if momentum_pct > 3:
                signals.append(FibonacciSignal(
                    signal=f"FIB {level.name} + STRONG UP MOMENTUM",
                    description=f"Strong bullish momentum ({momentum_pct:.1f}%) at {level.name}",
                    strength='SIGNIFICANT',
                    category='FIB_MOMENTUM',
                    timeframe=ctx.interval,
                    value=level.price,
                    metadata={'momentum_pct': momentum_pct, 'direction': 'BULLISH'}
                ))
            
            # Strong downward momentum at Fibonacci
            elif momentum_pct < -3:
                signals.append(FibonacciSignal(
                    signal=f"FIB {level.name} + STRONG DOWN MOMENTUM",
                    description=f"Strong bearish momentum ({momentum_pct:.1f}%) at {level.name}",
                    strength='SIGNIFICANT',
                    category='FIB_MOMENTUM',
                    timeframe=ctx.interval,
                    value=level.price,
                    metadata={'momentum_pct': momentum_pct, 'direction': 'BEARISH'}
                ))
            
            # Momentum stalling at Fibonacci (potential reversal)
            elif abs(momentum_pct) < 0.5:
                signals.append(FibonacciSignal(
                    signal=f"FIB {level.name} MOMENTUM STALL",
                    description=f"Momentum stalling at {level.name} Fibonacci",
                    strength='MODERATE',
                    category='FIB_MOMENTUM_STALL',
                    timeframe=ctx.interval,
                    value=level.price,
                    metadata={'momentum_pct': momentum_pct}
                ))
        
        return signals


class ATRVolatilityFibSignals(SignalGenerator):
    """Fibonacci + ATR-based volatility signals."""
    
    def generate(self, ctx: FibonacciContext) -> List[FibonacciSignal]:
        signals = []
        
        if ctx.close is None or len(ctx.df) < 14:
            return signals
        
        # Calculate ATR
        atr = ctx.tolerance_calc.calculate_atr()
        if atr <= 0:
            return signals
        
        atr_pct = atr / ctx.close * 100
        
        levels = ctx.get_fib_levels()
        tolerance = ctx.get_tolerance()
        
        for level in levels.values():
            if not ctx.price_at_level(ctx.close, level, tolerance):
                continue
            
            # High volatility at Fibonacci
            if atr_pct > 3:
                signals.append(FibonacciSignal(
                    signal=f"FIB {level.name} + HIGH ATR VOLATILITY",
                    description=f"High volatility (ATR: {atr_pct:.1f}%) at {level.name}",
                    strength='SIGNIFICANT',
                    category='FIB_ATR',
                    timeframe=ctx.interval,
                    value=level.price,
                    metadata={'atr': atr, 'atr_pct': atr_pct}
                ))
            
            # Low volatility (potential breakout setup)
            elif atr_pct < 1:
                signals.append(FibonacciSignal(
                    signal=f"FIB {level.name} + LOW ATR (COILING)",
                    description=f"Low volatility coiling at {level.name} (ATR: {atr_pct:.1f}%)",
                    strength='MODERATE',
                    category='FIB_ATR_COIL',
                    timeframe=ctx.interval,
                    value=level.price,
                    metadata={'atr': atr, 'atr_pct': atr_pct}
                ))
        
        return signals


class FibonacciArcSignals(SignalGenerator):
    """Fibonacci arc signal detection."""
    
    def generate(self, ctx: FibonacciContext) -> List[FibonacciSignal]:
        signals = []
        
        if ctx.close is None:
            return signals
        
        swing_data = ctx.get_swing_data()
        if not swing_data:
            return signals
        
        low = swing_data['low']
        swing_range = swing_data['range']
        current_bar = len(ctx.df)
        pivot_bar = swing_data['low_idx']
        time_since_pivot = current_bar - pivot_bar if pivot_bar < current_bar else 1
        
        arc_ratios = [0.236, 0.382, 0.500, 0.618, 0.786, 1.0]
        tolerance = ctx.get_tolerance('wide')
        
        for arc_ratio in arc_ratios:
            # Arc extends outward in both price and time
            time_factor = 1 + (time_since_pivot / len(ctx.df)) if len(ctx.df) > 0 else 1
            arc_price = low + (arc_ratio * swing_range * time_factor)
            
            if abs(ctx.close - arc_price) / ctx.close < tolerance:
                signals.append(FibonacciSignal(
                    signal=f"FIB ARC {arc_ratio*100:.1f}%",
                    description=f"Price touching {arc_ratio*100:.1f}% Fibonacci arc",
                    strength='MODERATE',
                    category='FIB_ARC',
                    timeframe=ctx.interval,
                    value=arc_price,
                    metadata={'arc_ratio': arc_ratio, 'time_factor': time_factor}
                ))
        
        return signals


class FibonacciFanSignals(SignalGenerator):
    """Fibonacci fan line signal detection."""
    
    def generate(self, ctx: FibonacciContext) -> List[FibonacciSignal]:
        signals = []
        
        if ctx.close is None:
            return signals
        
        swing_data = ctx.get_swing_data()
        if not swing_data:
            return signals
        
        low = swing_data['low']
        swing_range = swing_data['range']
        time_diff = len(ctx.df) - 50
        
        fan_ratios = [0.236, 0.382, 0.500, 0.618, 0.786]
        tolerance = ctx.get_tolerance('wide')
        
        for fan_ratio in fan_ratios:
            fan_price = low + (fan_ratio * swing_range) * (time_diff / 50) if time_diff > 0 else low
            fan_strength = 'SIGNIFICANT' if fan_ratio in [0.618, 0.786] else 'MODERATE'
            
            if abs(ctx.close - fan_price) / ctx.close < tolerance:
                signals.append(FibonacciSignal(
                    signal=f"FIB FAN {fan_ratio*100:.1f}%",
                    description=f"Price at {fan_ratio*100:.1f}% Fibonacci fan line",
                    strength=fan_strength,
                    category='FIB_FAN',
                    timeframe=ctx.interval,
                    value=fan_price,
                    metadata={'fan_ratio': fan_ratio}
                ))
        
        return signals


class RetraceExtensionConfluenceSignals(SignalGenerator):
    """Detects when retracement and extension levels converge."""
    
    def generate(self, ctx: FibonacciContext) -> List[FibonacciSignal]:
        signals = []
        
        if ctx.close is None:
            return signals
        
        levels = ctx.get_fib_levels()
        retraces = [l for l in levels.values() if l.fib_type == FibonacciType.RETRACE]
        extensions = [l for l in levels.values() if l.fib_type == FibonacciType.EXTENSION]
        
        tolerance = ctx.get_tolerance('wide')
        
        for retrace in retraces:
            for ext in extensions:
                # Check if levels converge
                if retrace.price > 0 and abs(retrace.price - ext.price) / retrace.price < 0.03:
                    # Check if price is at confluence
                    avg_price = (retrace.price + ext.price) / 2
                    if abs(ctx.close - avg_price) / ctx.close < tolerance:
                        signals.append(FibonacciSignal(
                            signal=f"FIB {retrace.name} + {ext.name} CONFLUENCE",
                            description=f"Retracement {retrace.name} converges with extension {ext.name}",
                            strength='EXTREME',
                            category='FIB_RET_EXT_CONFLUENCE',
                            timeframe=ctx.interval,
                            value=avg_price,
                            metadata={
                                'retrace_level': retrace.name,
                                'extension_level': ext.name
                            }
                        ))
        
        return signals


# =============================================================================
# MAIN SIGNAL DETECTOR CLASS
# =============================================================================

class EnhancedFibonacciSignalDetector:
    """
    Main class for comprehensive Fibonacci signal detection.
    Coordinates all signal generators and provides unified output.
    """
    
    def __init__(self, interval: str = "1d"):
        self.interval = interval
        
        # Register all signal generators
        self.generators: List[SignalGenerator] = [
            PriceLevelSignals(),
            BounceSignals(),
            BreakoutSignals(),
            ChannelSignals(),
            ClusterSignals(),
            MultiTimeframeClusterSignals(),
            TimeZoneSignals(),
            VolumeConfirmationSignals(),
            MovingAverageConfluenceSignals(),
            RSIDivergenceSignals(),
            MACDConfluenceSignals(),
            StochasticConfluenceSignals(),
            HarmonicPatternSignals(),
            ElliottWaveSignals(),
            CandlePatternAtFibSignals(),
            GoldenPocketSignals(),
            FibonacciSpeedResistanceSignals(),
            TrendLineConfluenceSignals(),
            PriceActionMomentumSignals(),
            ATRVolatilityFibSignals(),
            FibonacciArcSignals(),
            FibonacciFanSignals(),
            RetraceExtensionConfluenceSignals(),
        ]
    
    def _safe_float(self, value) -> Optional[float]:
        """Safely convert value to float."""
        if value is None:
            return None
        if isinstance(value, (int, float)):
            if np.isnan(value) or np.isinf(value):
                return None
            return float(value)
        try:
            result = float(value)
            if np.isnan(result) or np.isinf(result):
                return None
            return result
        except (ValueError, TypeError):
            return None
    
    def detect_fibonacci_signals(
        self,
        df: pd.DataFrame,
        current: pd.Series,
        prev: pd.Series
    ) -> List[Dict]:
        """
        Detect comprehensive Fibonacci signals.
        
        Args:
            df: DataFrame with OHLCV data
            current: Current bar data
            prev: Previous bar data
            
        Returns:
            List of signal dictionaries
        """
        signals = []
        
        # Validate inputs
        if len(df) < 20:
            return signals
        
        # Create context
        ctx = FibonacciContext(
            df=df,
            interval=self.interval,
            current=current,
            prev=prev,
            safe_float_fn=self._safe_float
        )
        
        # Validate close price
        if ctx.close is None:
            return signals
        
        # Run all generators
        for generator in self.generators:
            try:
                gen_signals = generator.generate(ctx)
                for sig in gen_signals:
                    signals.append(sig.to_dict())
            except Exception as e:
                # Log error but continue with other generators
                continue
        
        # Deduplicate signals
        signals = self._deduplicate_signals(signals)
        
        return signals
    
    def _deduplicate_signals(self, signals: List[Dict]) -> List[Dict]:
        """Remove duplicate signals based on signal name."""
        seen = set()
        unique = []
        
        for sig in signals:
            key = (sig['signal'], sig.get('category', ''))
            if key not in seen:
                seen.add(key)
                unique.append(sig)
        
        return unique
    
    def get_signal_summary(self, signals: List[Dict]) -> Dict:
        """Generate summary statistics for signals."""
        if not signals:
            return {
                'total_signals': 0,
                'by_strength': {},
                'by_category': {},
                'extreme_signals': []
            }
        
        by_strength = {}
        by_category = {}
        extreme_signals = []
        
        for sig in signals:
            # Count by strength
            strength = sig.get('strength', 'UNKNOWN')
            by_strength[strength] = by_strength.get(strength, 0) + 1
            
            # Count by category
            category = sig.get('category', 'UNKNOWN')
            by_category[category] = by_category.get(category, 0) + 1
            
            # Collect extreme signals
            if strength in ['EXTREME', 'STRONG']:
                extreme_signals.append(sig['signal'])
        
        return {
            'total_signals': len(signals),
            'by_strength': by_strength,
            'by_category': by_category,
            'extreme_signals': extreme_signals
        }


# =============================================================================
# USAGE EXAMPLE AND INTEGRATION HELPER
# =============================================================================

def create_test_data(n_bars: int = 200, seed: int = 42, scenario: str = 'trending') -> pd.DataFrame:
    """
    Create test OHLCV data with various scenarios.
    
    Args:
        n_bars: Number of bars
        seed: Random seed
        scenario: 'trending', 'ranging', 'volatile', 'at_fib_levels'
    """
    np.random.seed(seed)
    
    dates = pd.date_range(end=pd.Timestamp.now(), periods=n_bars, freq='1h')
    base_price = 100
    
    if scenario == 'trending':
        # Strong uptrend with pullbacks to Fibonacci levels
        trend = np.linspace(0, 0.5, n_bars)
        noise = np.random.randn(n_bars) * 0.02
        # Add pullbacks at specific intervals
        pullbacks = np.zeros(n_bars)
        pullbacks[50:60] = -0.1  # 38.2% retrace
        pullbacks[100:110] = -0.15  # 61.8% retrace
        pullbacks[150:160] = -0.08  # 23.6% retrace
        close = base_price * (1 + trend + noise + pullbacks)
        
    elif scenario == 'ranging':
        # Price ranging between Fibonacci levels
        close = base_price * (1 + np.sin(np.linspace(0, 8*np.pi, n_bars)) * 0.15)
        close += np.random.randn(n_bars) * 0.01
        
    elif scenario == 'volatile':
        # High volatility with many Fibonacci touches
        returns = np.random.randn(n_bars) * 0.04
        cumulative = np.cumsum(returns)
        close = base_price * (1 + cumulative)
        
    elif scenario == 'at_fib_levels':
        # Price specifically at Fibonacci levels
        # Create swing from 90 to 110, then retrace to various Fib levels
        close = np.ones(n_bars) * 100
        close[:50] = np.linspace(90, 110, 50)  # Up move
        
        # Position current price at 61.8% retrace
        swing_range = 20  # 110 - 90
        fib_618 = 110 - (0.618 * swing_range)  # ~97.64
        close[50:] = fib_618 + np.random.randn(n_bars-50) * 0.3
        
    else:
        returns = np.random.randn(n_bars) * 0.02
        close = base_price * (1 + np.cumsum(returns))
    
    close_series = pd.Series(close)
    
    # Generate OHLC from close
    high = close * (1 + abs(np.random.randn(n_bars) * 0.01))
    low = close * (1 - abs(np.random.randn(n_bars) * 0.01))
    open_price = np.roll(close, 1) * (1 + np.random.randn(n_bars) * 0.005)
    open_price[0] = close[0]
    
    # Create DataFrame
    df = pd.DataFrame({
        'Open': open_price,
        'High': high,
        'Low': low,
        'Close': close,
        'Volume': np.random.randint(1000, 20000, n_bars).astype(float),
    }, index=dates)
    
    # Add technical indicators
    df['RSI'] = 50 + np.random.randn(n_bars) * 20
    df['RSI'] = df['RSI'].clip(0, 100)
    
    df['SMA_20'] = close_series.rolling(20, min_periods=1).mean().values
    df['SMA_50'] = close_series.rolling(50, min_periods=1).mean().values
    df['SMA_100'] = close_series.rolling(100, min_periods=1).mean().values
    df['SMA_200'] = close_series.rolling(200, min_periods=1).mean().values
    
    df['EMA_12'] = close_series.ewm(span=12).mean().values
    df['EMA_26'] = close_series.ewm(span=26).mean().values
    df['EMA_50'] = close_series.ewm(span=50).mean().values
    
    # MACD
    df['MACD'] = df['EMA_12'] - df['EMA_26']
    df['MACD_Signal'] = pd.Series(df['MACD']).ewm(span=9).mean().values
    df['MACD_Histogram'] = df['MACD'] - df['MACD_Signal']
    
    # Stochastic
    low_14 = df['Low'].rolling(14).min()
    high_14 = df['High'].rolling(14).max()
    df['Stoch_K'] = 100 * (df['Close'] - low_14) / (high_14 - low_14 + 0.0001)
    df['Stoch_D'] = df['Stoch_K'].rolling(3).mean()
    
    return df


def run_signal_detection_demo():
    """Run comprehensive demo of signal detection across scenarios."""
    
    print("\n" + "="*70)
    print("ENHANCED FIBONACCI SIGNAL DETECTION - COMPREHENSIVE TEST")
    print("="*70)
    
    scenarios = ['trending', 'ranging', 'volatile', 'at_fib_levels']
    all_signals = []
    
    for scenario in scenarios:
        print(f"\n{'='*50}")
        print(f"SCENARIO: {scenario.upper()}")
        print(f"{'='*50}")
        
        # Create data
        df = create_test_data(n_bars=200, scenario=scenario)
        
        # Initialize detector
        detector = EnhancedFibonacciSignalDetector(interval="1h")
        
        # Detect signals
        current = df.iloc[-1]
        prev = df.iloc[-2]
        
        signals = detector.detect_fibonacci_signals(df, current, prev)
        all_signals.extend(signals)
        
        # Summary
        summary = detector.get_signal_summary(signals)
        
        print(f"\nTotal Signals: {len(signals)}")
        print(f"\nBy Strength:")
        for strength, count in sorted(summary['by_strength'].items()):
            print(f"  {strength}: {count}")
        
        print(f"\nBy Category:")
        for category, count in sorted(summary['by_category'].items()):
            print(f"  {category}: {count}")
        
        if summary['extreme_signals']:
            print(f"\nExtreme/Strong Signals:")
            for sig in summary['extreme_signals'][:5]:
                print(f"  • {sig}")
    
    # Overall statistics
    print("\n" + "="*70)
    print("OVERALL STATISTICS")
    print("="*70)
    
    unique_signal_types = set(s['signal'] for s in all_signals)
    unique_categories = set(s['category'] for s in all_signals)
    
    print(f"\nTotal signals across all scenarios: {len(all_signals)}")
    print(f"Unique signal types: {len(unique_signal_types)}")
    print(f"Unique categories: {len(unique_categories)}")
    
    print("\nAll Categories Found:")
    for cat in sorted(unique_categories):
        print(f"  • {cat}")
    
    print("\nSample of Unique Signals:")
    for sig in list(unique_signal_types)[:20]:
        print(f"  • {sig}")
    
    return all_signals


if __name__ == "__main__":
    run_signal_detection_demo()