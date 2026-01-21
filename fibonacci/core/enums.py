"""Enumerations for Fibonacci signal classification."""

from enum import Enum


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
