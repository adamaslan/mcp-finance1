"""Backend testing framework for validating configurations."""

from .test_config import BackendTestRunner, TestScenario, TestResult
from .scenarios import (
    ALL_SCENARIOS,
    SCENARIO_RISKY_GENERATES_MORE_TRADES,
    SCENARIO_AVERSE_HIGHER_RR,
    SCENARIO_MOMENTUM_INTEGRATION,
    SCENARIO_NO_MOCK_DATA,
)

__all__ = [
    "BackendTestRunner",
    "TestScenario",
    "TestResult",
    "ALL_SCENARIOS",
    "SCENARIO_RISKY_GENERATES_MORE_TRADES",
    "SCENARIO_AVERSE_HIGHER_RR",
    "SCENARIO_MOMENTUM_INTEGRATION",
    "SCENARIO_NO_MOCK_DATA",
]
