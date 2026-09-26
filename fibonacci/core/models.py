"""Data models for Fibonacci analysis."""

from dataclasses import dataclass, field
from typing import Dict, Any

from .enums import SignalStrength, FibonacciType

_DIRECTIONAL_TYPES = frozenset({FibonacciType.RETRACE, FibonacciType.EXTENSION})


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

    def calculate_price(self, low: float, high: float, is_uptrend: bool | None = None) -> float:
        """Calculate price level from swing range.

        Retracements are measured back from the leg's end: down from the high
        after an up-leg, up from the low after a down-leg. Extensions run on in
        the leg's direction. ``is_uptrend=None`` keeps the legacy behaviour of
        measuring every ratio up from the low. INVERSE levels carry negative
        ratios and are always measured from the low.
        """
        swing_range = high - low
        if is_uptrend is None or self.fib_type not in _DIRECTIONAL_TYPES:
            self.price = low + (self.ratio * swing_range)
        elif self.fib_type == FibonacciType.RETRACE:
            self.price = high - (self.ratio * swing_range) if is_uptrend else low + (self.ratio * swing_range)
        else:
            self.price = low + (self.ratio * swing_range) if is_uptrend else high - (self.ratio * swing_range)
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
