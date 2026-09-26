"""Fibonacci anchors come from confirmed pivots, not the window's max/min."""
import numpy as np
import pandas as pd
import pytest

from fibonacci.analysis.context import FibonacciContext
from fibonacci.analysis.legs import PIVOT_WINDOW, find_pivots, recent_leg
from fibonacci.analysis.swing_detector import ANCHOR_EXTREMES, ANCHOR_PIVOTS, SwingPointDetector


def _frame(points: list[tuple[int, float]], atr: float | None = None) -> pd.DataFrame:
    """Close path linearly interpolated through (bar, price) points; High/Low = Close +/- 1."""
    bars = np.arange(points[-1][0] + 1)
    closes = np.interp(bars, [b for b, _ in points], [p for _, p in points])
    df = pd.DataFrame(
        {"Open": closes, "High": closes + 1, "Low": closes - 1, "Close": closes, "Volume": 1000.0},
        index=pd.date_range("2026-01-01", periods=len(bars), freq="D"),
    )
    if atr is not None:
        df["ATR"] = atr
    return df


# low 100 @20, high 150 @40, low 130 @50, then a run to 160 on the last bar (59)
ZIGZAG = [(0, 120), (20, 100), (40, 150), (50, 130), (59, 160)]


def test_unconfirmed_last_bar_high_is_not_an_anchor():
    df = _frame(ZIGZAG, atr=2.0)
    high, low, _, _ = SwingPointDetector(df).detect_swings(50)
    # Window extremes would be 161 (last bar, unconfirmed) and 99; the leg is 151 -> 129.
    assert (high, low) == (pytest.approx(151.0), pytest.approx(129.0))


def test_leg_direction_comes_from_pivot_order():
    detector = SwingPointDetector(_frame(ZIGZAG, atr=2.0))
    assert detector.get_trend_direction(50) == "DOWN"  # 151 then 129: a down-leg
    assert detector.anchor_source(50) == ANCHOR_PIVOTS


def test_pivot_needs_window_bars_after_it():
    df = _frame([(0, 100), (30, 150), (30 + PIVOT_WINDOW, 140)])
    assert all(p.bar_index < len(df) - PIVOT_WINDOW for p in find_pivots(df))
    assert not any(p.kind == "resistance" for p in find_pivots(df.iloc[: 30 + PIVOT_WINDOW]))


def test_small_recent_leg_is_skipped_for_the_earlier_qualifying_leg():
    leg = recent_leg(_frame(ZIGZAG, atr=10.0), 50)  # 22-point leg < 30; 52-point leg >= 30
    assert (leg.low, leg.high, leg.is_up) == (pytest.approx(99.0), pytest.approx(151.0), True)


def test_no_leg_of_three_atr_falls_back_to_window_extremes():
    df = _frame(ZIGZAG, atr=20.0)  # every leg < 60
    detector = SwingPointDetector(df)
    assert recent_leg(df, 50) is None
    assert detector.anchor_source(50) == ANCHOR_EXTREMES
    assert detector.detect_swings(50)[:2] == (df["High"].iloc[-50:].max(), df["Low"].iloc[-50:].min())


def test_leg_must_lie_inside_the_window():
    df = _frame(ZIGZAG, atr=2.0)
    assert recent_leg(df, 12) is None  # pivots at 40 and 50 don't both fit in the last 12 bars


def test_context_levels_use_the_pivot_leg():
    df = _frame(ZIGZAG, atr=2.0)
    ctx = FibonacciContext(df, "1d", df.iloc[-1], df.iloc[-2], float)
    levels = ctx.get_fib_levels(50)
    swing = ctx.get_swing_data(50)
    assert swing["anchor"] == ANCHOR_PIVOTS and swing["is_uptrend"] is False
    # down-leg 151 -> 129: the 0.618 retracement is measured up from the low
    assert levels["RETRACE_618"].price == pytest.approx(129 + 0.618 * 22)
