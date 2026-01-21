"""Data models for Fibonacci analysis."""

from dataclasses import dataclass, field
from typing import Dict, Any

from .enums import SignalStrength, FibonacciType


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
