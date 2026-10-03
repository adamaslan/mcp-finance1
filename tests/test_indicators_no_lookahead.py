"""Causality guard: no indicator column may use rows after the row it is reported on."""

import numpy as np
import pandas as pd
import pytest

from technical_analysis_mcp.indicators import calculate_all_indicators

FULL_BARS = 320
TRUNCATED_BARS = 220


def _ohlcv(bars: int) -> pd.DataFrame:
    rng = np.random.default_rng(7)
    close = 100 + rng.normal(0, 1, FULL_BARS).cumsum()
    frame = pd.DataFrame(
        {
            "Open": close,
            "High": close + 1,
            "Low": close - 1,
            "Close": close,
            "Volume": rng.integers(900_000, 1_100_000, FULL_BARS),
        },
        index=pd.date_range("2024-01-01", periods=FULL_BARS, freq="B"),
    )
    return frame.iloc[:bars]


def test_indicator_columns_do_not_change_when_future_bars_are_removed():
    full = calculate_all_indicators(_ohlcv(FULL_BARS))
    truncated = calculate_all_indicators(_ohlcv(TRUNCATED_BARS))

    leaking = [
        column
        for column in truncated.columns
        if not np.allclose(
            truncated[column].to_numpy(dtype=float),
            full[column].iloc[:TRUNCATED_BARS].to_numpy(dtype=float),
            equal_nan=True,
        )
    ]

    assert not leaking, f"columns depend on future rows: {leaking}"


def test_detector_catches_a_negative_shift():
    leaky = _ohlcv(FULL_BARS).assign(Chikou=lambda f: f["Close"].shift(-26))
    full = leaky["Chikou"]
    truncated = _ohlcv(TRUNCATED_BARS).assign(Chikou=lambda f: f["Close"].shift(-26))["Chikou"]

    assert not np.allclose(
        truncated.to_numpy(dtype=float),
        full.iloc[:TRUNCATED_BARS].to_numpy(dtype=float),
        equal_nan=True,
    )
