# Phase 1 Implementation Complete

## Summary

Phase 1 of the MCP Finance risk profile and configuration system has been successfully implemented. All core infrastructure is in place for risk-profile-based analysis, with three predefined profiles (Risky, Neutral, Averse) and a comprehensive backend testing framework.

## What Was Implemented

### 1. **Configuration System** (`src/technical_analysis_mcp/profiles/`)

#### Files Created:
- **`__init__.py`** - Module exports
- **`base_config.py`** - Core configuration dataclasses
  - `RiskProfile` enum: RISKY, NEUTRAL, AVERSE
  - `IndicatorConfig` - RSI, MACD, Bollinger Bands, Stochastic, ADX/ATR settings
  - `RiskConfig` - Stop-loss, volatility, trend, position sizing, suppression thresholds
  - `MomentumConfig` - Momentum tracking parameters
  - `SignalConfig` - Output limits and signal weighting
  - `UserConfig` - Complete bundle of all configuration
- **`risk_profiles.py`** - Three predefined configurations
  - `RISKY_CONFIG` - Aggressive thresholds, lower R:R, more trades
  - `NEUTRAL_CONFIG` - Balanced defaults (baseline)
  - `AVERSE_CONFIG` - Conservative thresholds, higher R:R, fewer trades
- **`config_manager.py`** - Central management
  - `ConfigManager` class for getting, validating, and caching configurations
  - Support for user preferences, session overrides, and custom overrides
  - Validation methods for user-provided overrides

### 2. **Testing Framework** (`src/technical_analysis_mcp/testing/`)

#### Files Created:
- **`__init__.py`** - Module exports
- **`test_config.py`** - Core test infrastructure
  - `TestScenario` dataclass - Define test cases
  - `TestResult` dataclass - Store test results
  - `BackendTestRunner` class - Execute tests and generate reports
    - `run_scenario()` - Run single test scenario
    - `run_profile_comparison()` - Compare all three profiles
    - `run_config_sweep()` - Parameter optimization testing
    - `generate_report()` - Markdown test report
- **`scenarios.py`** - Predefined test scenarios
  - `SCENARIO_RISKY_GENERATES_MORE_TRADES` - Validate risky profile behavior
  - `SCENARIO_AVERSE_HIGHER_RR` - Validate averse profile R:R enforcement
  - `SCENARIO_NEUTRAL_BALANCED` - Validate neutral profile
  - `SCENARIO_MOMENTUM_INTEGRATION` - Verify momentum data in output
  - `SCENARIO_NO_MOCK_DATA` - Regression test against fake data
  - `SCENARIO_HIGH_VOLATILITY` - Edge case handling
  - `SCENARIO_LOW_VOLUME` - Edge case handling
  - `ALL_SCENARIOS` - List of all scenarios for batch execution

### 3. **CLI Test Runner** (`scripts/test_backend_config.py`)

Executable script for running tests from command line:

```bash
# Run all predefined scenarios
python scripts/test_backend_config.py --mode scenarios

# Compare all risk profiles on specific stocks
python scripts/test_backend_config.py --mode compare --symbols AAPL NVDA TSLA

# Sweep a single parameter to find optimal value
python scripts/test_backend_config.py --mode sweep \
    --symbols AAPL \
    --param rsi_oversold \
    --values 20 25 30 35 40

# Save results to custom file
python scripts/test_backend_config.py --mode scenarios --output my_report.md

# Verbose logging
python scripts/test_backend_config.py --mode scenarios --verbose
```

## Configuration Comparison

### Risk Thresholds by Profile

| Parameter | Risky | Neutral | Averse |
|-----------|-------|---------|--------|
| RSI Oversold | 35 | 30 | 25 |
| RSI Overbought | 65 | 70 | 75 |
| Min R:R Ratio | 1.2:1 | 1.5:1 | 2.0:1 |
| Stop ATR (Swing) | 1.5 | 2.0 | 2.5 |
| Volatility High | 4.0% | 3.0% | 2.5% |
| ADX Trending | 20 | 25 | 30 |
| Position Risk % | 3.0% | 2.0% | 1.0% |
| Portfolio Heat % | 10.0% | 6.0% | 4.0% |
| Signal Conflict % | 50% | 40% | 25% |
| Max Signals | 75 | 50 | 30 |
| Max Trade Plans | 5 | 3 | 2 |

## Next Steps: Integration with server.py

### Phase 1.5: Minimal Server.py Integration

To enable testing without full momentum integration, add these minimal changes to `server.py`:

```python
# In imports
from .profiles import (
    get_config_manager,
    get_profile,
    RiskProfile,
)

# In list_tools(), update tool schemas for analyze_security and get_trade_plan
# to include risk_profile parameter

# In analyze_security handler function:
async def analyze_security(
    symbol: str,
    period: str = DEFAULT_PERIOD,
    use_ai: bool = False,
    risk_profile: str = "neutral",  # NEW PARAMETER
) -> dict[str, Any]:
    """
    ... existing docstring ...

    Args:
        ... existing args ...
        risk_profile: User's risk tolerance ("risky", "neutral", "averse")
    """
    # Existing logic unchanged
    result = ... # existing analysis

    # NEW: Add profile info to output
    config = get_profile(risk_profile)
    result["risk_profile"] = risk_profile
    result["config_applied"] = config.to_dict()

    return result

# Same for get_trade_plan handler
```

### Phase 2: Full Implementation

Phase 2 will add:
- Momentum calculation and signal weighting
- Integration of momentum into all 9 servers
- Risk-adjusted output for all servers
- Complete parameter control for all MCP tools

## Testing the Configuration

### Quick Validation

```python
# Python REPL
from src.technical_analysis_mcp.profiles import (
    get_profile,
    get_config_manager,
    RiskProfile,
)

# Get a profile
risky = get_profile(RiskProfile.RISKY)
print(f"Risky R:R minimum: {risky.risk.min_rr_ratio}")  # 1.2

averse = get_profile("averse")
print(f"Averse R:R minimum: {averse.risk.min_rr_ratio}")  # 2.0

# Validate overrides
manager = get_config_manager()
is_valid, errors = manager.validate_overrides({"rsi_oversold": 28})
print(f"Valid: {is_valid}, Errors: {errors}")

# Get config with overrides
config = manager.get_config(
    risk_profile="neutral",
    session_overrides={"rsi_oversold": 28}
)
print(f"RSI Oversold: {config.indicators.rsi_oversold}")  # 28
```

### Running Backend Tests

```bash
cd /Users/adamaslan/code/gcp\ app\ w\ mcp/mcp-finance1

# Run all scenarios
python scripts/test_backend_config.py --mode scenarios

# Compare profiles on tech stocks
python scripts/test_backend_config.py --mode compare \
    --symbols AAPL MSFT GOOGL NVDA

# Find optimal RSI threshold
python scripts/test_backend_config.py --mode sweep \
    --symbols AAPL \
    --param rsi_oversold \
    --values 20 25 30 35 40 45
```

## Architecture Notes

### Design Patterns Used

1. **Immutable Data Structures** - All config dataclasses are frozen for thread-safety
2. **Dependency Injection** - ConfigManager provides configs to server functions
3. **Factory Pattern** - `get_profile()` and `get_config_manager()` singletons
4. **Strategy Pattern** - Different configurations apply different trading strategies
5. **Visitor Pattern** - Test runner validates results against expected behaviors

### Configuration Hierarchy

```
┌─────────────────────────────────┐
│   Session Overrides (temp)      │  <- Per-request customizations
└──────────────┬──────────────────┘
               ↓
┌─────────────────────────────────┐
│   User Saved Preferences (DB)   │  <- TODO: implement
└──────────────┬──────────────────┘
               ↓
┌─────────────────────────────────┐
│   Risk Profile Preset           │  <- Risky/Neutral/Averse
└──────────────┬──────────────────┘
               ↓
┌─────────────────────────────────┐
│   Default Config                │  <- Fallback values
└─────────────────────────────────┘
```

## File Structure

```
mcp-finance1/
├── src/technical_analysis_mcp/
│   ├── profiles/                          # NEW
│   │   ├── __init__.py
│   │   ├── base_config.py                 # Configuration dataclasses
│   │   ├── risk_profiles.py               # Three preset profiles
│   │   └── config_manager.py              # Central management
│   │
│   ├── testing/                           # NEW
│   │   ├── __init__.py
│   │   ├── test_config.py                 # Test runner
│   │   └── scenarios.py                   # Predefined scenarios
│   │
│   ├── server.py                          # WILL BE UPDATED
│   ├── config.py                          # (unchanged for now)
│   └── ... (other existing files)
│
└── scripts/
    └── test_backend_config.py             # NEW - CLI test runner
```

## Deliverables Checklist

- ✅ `profiles/` directory structure created
- ✅ `base_config.py` - All configuration dataclasses
- ✅ `risk_profiles.py` - Three preset profiles (RISKY, NEUTRAL, AVERSE)
- ✅ `config_manager.py` - Central configuration management
- ✅ `testing/test_config.py` - BackendTestRunner class
- ✅ `testing/scenarios.py` - 7 predefined test scenarios
- ✅ `scripts/test_backend_config.py` - CLI test tool
- ✅ This documentation file

## Phase 1 Status

**✅ COMPLETE**

All Phase 1 deliverables are implemented and ready for:
1. Server.py integration (minimal or full)
2. Backend testing to validate configuration logic
3. Phase 2 momentum integration

## Next Phase: Phase 2 - Momentum Integration

Phase 2 will implement:
- MomentumCalculator class for multi-period momentum analysis
- Integration into signal ranking system
- Divergence detection (bullish/bearish)
- Momentum-weighted signal scores
- Momentum output in all 9 MCP servers

See `nu-docs/mcp-input-control-risk-momentum-suggestions.md` for Phase 2 details.
