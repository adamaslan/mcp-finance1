"""Predefined test scenarios for backend validation."""

from .test_config import TestScenario
from ..profiles.risk_profiles import RISKY_CONFIG, NEUTRAL_CONFIG, AVERSE_CONFIG


# ============ PROFILE VALIDATION SCENARIOS ============

SCENARIO_RISKY_GENERATES_MORE_TRADES = TestScenario(
    name="risky_more_trades",
    description="Risky profile should generate more trade opportunities than neutral",
    config=RISKY_CONFIG,
    symbols=["AAPL", "MSFT", "GOOGL", "NVDA", "TSLA"],
    expected_behaviors={
        # Risky profile should generate at least 1 trade per major stock
        symbol: {
            "min_trades": 1,
            "max_trades": 5,
            "signal_count_range": (40, 100),
        }
        for symbol in ["AAPL", "MSFT", "GOOGL", "NVDA", "TSLA"]
    },
)

SCENARIO_AVERSE_HIGHER_RR = TestScenario(
    name="averse_higher_rr",
    description="Averse profile should only show trades with R:R >= 2.0",
    config=AVERSE_CONFIG,
    symbols=["AAPL", "MSFT", "SPY"],
    expected_behaviors={
        symbol: {
            "rr_range": (2.0, 6.0),
            "max_trades": 3,  # Averse shows fewer trades
            "signal_count_range": (0, 50),  # Fewer signals
        }
        for symbol in ["AAPL", "MSFT", "SPY"]
    },
)

SCENARIO_NEUTRAL_BALANCED = TestScenario(
    name="neutral_balanced_approach",
    description="Neutral profile should provide balanced trade opportunities",
    config=NEUTRAL_CONFIG,
    symbols=["AAPL", "MSFT", "QQQ"],
    expected_behaviors={
        symbol: {
            "rr_range": (1.0, 5.0),  # Accept wider range
            "max_trades": 4,
            "signal_count_range": (10, 80),
        }
        for symbol in ["AAPL", "MSFT", "QQQ"]
    },
)

SCENARIO_MOMENTUM_INTEGRATION = TestScenario(
    name="momentum_in_output",
    description="All analyses should include momentum data when enabled",
    config=NEUTRAL_CONFIG,
    symbols=["AAPL", "QQQ", "NVDA"],
    expected_behaviors={
        # Momentum fields should be present in response
        symbol: {
            "signal_count_range": (1, 150),  # Any number of signals is ok
        }
        for symbol in ["AAPL", "QQQ", "NVDA"]
    },
)


# ============ REGRESSION TEST SCENARIOS ============

SCENARIO_NO_MOCK_DATA = TestScenario(
    name="no_mock_data",
    description="All prices should be real (non-zero, non-placeholder values)",
    config=NEUTRAL_CONFIG,
    symbols=["AAPL", "MSFT", "INVALID_SYMBOL_XYZ"],
    expected_behaviors={
        "AAPL": {
            "min_trades": 0,  # Should have real data, may or may not have trades
            "signal_count_range": (0, 150),
        },
        "MSFT": {
            "min_trades": 0,
            "signal_count_range": (0, 150),
        },
        # INVALID_SYMBOL_XYZ should fail gracefully, not return mock data
    },
)


# ============ EDGE CASE SCENARIOS ============

SCENARIO_HIGH_VOLATILITY = TestScenario(
    name="high_volatility_handling",
    description="Test handling of high-volatility stocks",
    config=NEUTRAL_CONFIG,
    symbols=["GME", "AMC"],  # Known volatile stocks
    expected_behaviors={
        # Should either suppress or adjust stops appropriately
        symbol: {"signal_count_range": (0, 150)}
        for symbol in ["GME", "AMC"]
    },
)

SCENARIO_LOW_VOLUME = TestScenario(
    name="low_volume_handling",
    description="Test handling of low-liquidity symbols",
    config=NEUTRAL_CONFIG,
    symbols=["PLTR", "RIOT"],  # Lower volume stocks
    expected_behaviors={
        symbol: {"signal_count_range": (0, 150)}
        for symbol in ["PLTR", "RIOT"]
    },
)


# ============ PROFILE DIFFERENCE SCENARIOS ============

SCENARIO_COMPARE_ALL_PROFILES = TestScenario(
    name="compare_profiles_on_tech",
    description="Compare all profiles on tech stocks to show differences",
    config=NEUTRAL_CONFIG,  # Will be overridden in comparison test
    symbols=["NVDA", "META", "TSLA"],
    expected_behaviors={
        # Just verify we get results - comparison is in the analysis
        symbol: {"signal_count_range": (0, 150)}
        for symbol in ["NVDA", "META", "TSLA"]
    },
)


# All scenarios for batch running
ALL_SCENARIOS = [
    SCENARIO_RISKY_GENERATES_MORE_TRADES,
    SCENARIO_AVERSE_HIGHER_RR,
    SCENARIO_NEUTRAL_BALANCED,
    SCENARIO_MOMENTUM_INTEGRATION,
    SCENARIO_NO_MOCK_DATA,
    SCENARIO_HIGH_VOLATILITY,
    SCENARIO_LOW_VOLUME,
]
