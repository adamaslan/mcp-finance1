"""
Swing Legs From Confirmed Pivots
================================
Ported from signals-app ``indicators/pivots.py`` and ``indicators/fibonacci.py``
(the canonical Fibonacci definition across the finance apps). Keep the two in step.

A pivot at bar ``j`` only exists once bars ``j+1 .. j+PIVOT_WINDOW`` exist, so a
leg built from pivots never uses a bar that has not been confirmed. Legs
smaller than ``MIN_LEG_ATR`` x ATR are skipped: tiny legs put many levels a few
cents apart and price touches all of them.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

import numpy as np
import pandas as pd

PIVOT_WINDOW: Final[int] = 3
MIN_LEG_ATR: Final[float] = 3.0
ATR_PERIOD: Final[int] = 14
_SUPPORT: Final[str] = "support"
_RESISTANCE: Final[str] = "resistance"


@dataclass(frozen=True)
class Pivot:
    """A confirmed swing high (resistance) or swing low (support)."""

    price: float
    bar_index: int  # position in the frame, not an index label
    kind: str


@dataclass(frozen=True)
class SwingLeg:
    """A swing leg between two alternating confirmed pivots."""

    low: float
    high: float
    low_index: int
    high_index: int
    is_up: bool  # True: the low pivot precedes the high pivot

    @property
    def range(self) -> float:
        return self.high - self.low

    @property
    def end_index(self) -> int:
        return max(self.low_index, self.high_index)


def find_pivots(df: pd.DataFrame, window: int = PIVOT_WINDOW) -> list[Pivot]:
    """Pivots in bar order. Bar ``i`` is a pivot high when its High is the max of
    ``[i-window, i+window]`` (and that span isn't flat); likewise for lows."""
    if len(df) < window * 2 + 1:
        return []
    highs = df["High"].to_numpy(dtype=float)
    lows = df["Low"].to_numpy(dtype=float)
    pivots: list[Pivot] = []
    for i in range(window, len(df) - window):
        span_high = highs[i - window : i + window + 1]
        span_low = lows[i - window : i + window + 1]
        if highs[i] == np.max(span_high) and highs[i] > np.min(span_high):
            pivots.append(Pivot(float(highs[i]), i, _RESISTANCE))
        if lows[i] == np.min(span_low) and lows[i] < np.max(span_low):
            pivots.append(Pivot(float(lows[i]), i, _SUPPORT))
    return pivots


def _alternating(pivots: list[Pivot]) -> list[Pivot]:
    """Collapse runs of same-kind pivots, keeping the most extreme of each run."""
    merged: list[Pivot] = []
    for pivot in pivots:
        if merged and merged[-1].kind == pivot.kind:
            prev = merged[-1]
            more_extreme = pivot.price > prev.price if pivot.kind == _RESISTANCE else pivot.price < prev.price
            if more_extreme:
                merged[-1] = pivot
            continue
        merged.append(pivot)
    return merged


def average_true_range(df: pd.DataFrame, period: int = ATR_PERIOD) -> float:
    """Latest ATR: the frame's ``ATR`` column when present, else a simple mean true range."""
    if "ATR" in df.columns:
        latest = pd.to_numeric(df["ATR"], errors="coerce").dropna()
        if len(latest) and latest.iloc[-1] > 0:
            return float(latest.iloc[-1])
    prev_close = df["Close"].shift(1) if "Close" in df.columns else df["Low"]
    true_range = pd.concat(
        [df["High"] - df["Low"], (df["High"] - prev_close).abs(), (df["Low"] - prev_close).abs()], axis=1
    ).max(axis=1)
    atr = true_range.tail(period).mean()
    return float(atr) if pd.notna(atr) else 0.0


def recent_leg(df: pd.DataFrame, window: int, atr: float | None = None) -> SwingLeg | None:
    """Most recent qualifying leg whose pivots both fall in the last ``window`` bars.

    Pivots are found on the whole frame so a pivot near the window's start still
    gets its left-hand confirmation bars. Returns None when no leg qualifies.
    """
    atr = average_true_range(df) if atr is None else atr
    if atr <= 0:
        return None
    first_bar = len(df) - min(window, len(df))
    pivots = _alternating(find_pivots(df))
    for earlier, later in zip(reversed(pivots[:-1]), reversed(pivots[1:])):
        if earlier.bar_index < first_bar:
            return None
        # A wide outside bar can be both a pivot high and a pivot low; a "leg"
        # between them has no elapsed swing.
        if earlier.bar_index == later.bar_index:
            continue
        is_up = later.kind == _RESISTANCE
        low, high = (earlier, later) if is_up else (later, earlier)
        if high.price - low.price < MIN_LEG_ATR * atr:
            continue
        return SwingLeg(low.price, high.price, low.bar_index, high.bar_index, is_up)
    return None
