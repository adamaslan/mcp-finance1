"""Registry of all Fibonacci ratios with metadata."""

from typing import Dict

from .models import FibonacciLevel
from .enums import FibonacciType, SignalStrength


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
