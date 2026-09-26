"""Fibonacci level prices must respect the leg's direction."""
import pytest

from fibonacci.core.enums import FibonacciType, SignalStrength
from fibonacci.core.models import FibonacciLevel


def _level(ratio: float, fib_type: FibonacciType) -> FibonacciLevel:
    return FibonacciLevel("k", ratio, "n", fib_type, SignalStrength.MODERATE)


LOW, HIGH = 100.0, 200.0


def test_uptrend_retracement_measured_down_from_high():
    assert _level(0.618, FibonacciType.RETRACE).calculate_price(LOW, HIGH, True) == pytest.approx(138.2)


def test_downtrend_retracement_measured_up_from_low():
    assert _level(0.618, FibonacciType.RETRACE).calculate_price(LOW, HIGH, False) == pytest.approx(161.8)


def test_extension_runs_on_in_the_leg_direction():
    ext = _level(1.618, FibonacciType.EXTENSION)
    assert ext.calculate_price(LOW, HIGH, True) == pytest.approx(261.8)
    assert ext.calculate_price(LOW, HIGH, False) == pytest.approx(38.2)


def test_direction_unknown_keeps_legacy_low_based_price():
    assert _level(0.618, FibonacciType.RETRACE).calculate_price(LOW, HIGH) == pytest.approx(161.8)


def test_inverse_levels_stay_low_based():
    inv = _level(-0.382, FibonacciType.INVERSE)
    assert inv.calculate_price(LOW, HIGH, True) == inv.calculate_price(LOW, HIGH, False) == pytest.approx(61.8)


def test_context_uses_trend_direction():
    import pandas as pd
    from fibonacci.analysis.context import FibonacciContext

    closes = [100 + i for i in range(60)]  # low first, high last: up-leg
    df = pd.DataFrame({"Open": closes, "High": [c + 1 for c in closes], "Low": [c - 1 for c in closes],
                       "Close": closes, "Volume": 1000.0, "ATR": 2.0})
    ctx = FibonacciContext(df, "1d", df.iloc[-1], df.iloc[-2], lambda v: float(v))
    levels = ctx.get_fib_levels(50)
    high, low = df["High"].iloc[-50:].max(), df["Low"].iloc[-50:].min()
    assert levels["RETRACE_618"].price == pytest.approx(high - 0.618 * (high - low))


def test_direction_uses_bar_position_not_index_labels():
    import pandas as pd
    from fibonacci.analysis.swing_detector import SwingPointDetector

    closes = [100 + i for i in range(60)]  # up-leg in bar order
    df = pd.DataFrame({"High": [c + 1 for c in closes], "Low": [c - 1 for c in closes]},
                      index=list(range(59, -1, -1)))  # labels descend while time ascends
    assert SwingPointDetector(df).get_trend_direction(50) == "UP"
