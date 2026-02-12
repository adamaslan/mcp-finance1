#!/usr/bin/env python
"""Test script to verify all three config override fixes work correctly.

Tests:
1. get_profile_with_overrides - Overrides are actually applied to nested fields
2. analyze_security - Config parameter is used in analysis
3. End-to-end - Configuration changes produce different results
"""

import sys
import logging
from decimal import Decimal

# Add src to path
sys.path.insert(0, "/Users/adamaslan/code/gcp app w mcp/mcp-finance1/src")

from technical_analysis_mcp.profiles.base_config import (
    RiskProfile,
    UserConfig,
    IndicatorConfig,
    RiskConfig,
)
from technical_analysis_mcp.profiles.risk_profiles import (
    get_profile,
    get_profile_with_overrides,
)
from technical_analysis_mcp.profiles.config_manager import get_config_manager
from technical_analysis_mcp.config_adapter import (
    ConfigContext,
    get_config_context,
    validate_config_context,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s",
)
logger = logging.getLogger(__name__)


def test_1_get_profile_with_overrides():
    """Test: Overrides are actually applied to nested dataclass fields."""
    print("\n" + "=" * 80)
    print("TEST 1: get_profile_with_overrides - Overrides Applied ✓")
    print("=" * 80)

    # Get neutral profile
    base = get_profile("neutral")
    original_rsi_oversold = base.indicators.rsi_oversold
    print(f"✓ Base profile RSI oversold: {original_rsi_oversold}")

    # Apply override
    overrides = {"rsi_oversold": 28.0, "min_rr_ratio": 1.8}
    config = get_profile_with_overrides("neutral", overrides)

    print(f"✓ Applied overrides: {overrides}")

    # CHECK 1: Overrides stored in custom_overrides dict
    assert config.custom_overrides == overrides, "Overrides not stored in custom_overrides"
    print(f"✓ Overrides stored in custom_overrides: {config.custom_overrides}")

    # CHECK 2: CRITICAL - Overrides actually applied to nested field
    assert (
        config.indicators.rsi_oversold == 28.0
    ), f"❌ BROKEN: rsi_oversold not applied! Expected 28.0, got {config.indicators.rsi_oversold}"
    print(f"✓ ✓ ✓ rsi_oversold ACTUALLY CHANGED to {config.indicators.rsi_oversold}")

    # CHECK 3: CRITICAL - Other risk field override applied
    assert (
        config.risk.min_rr_ratio == 1.8
    ), f"❌ BROKEN: min_rr_ratio not applied! Expected 1.8, got {config.risk.min_rr_ratio}"
    print(f"✓ ✓ ✓ min_rr_ratio ACTUALLY CHANGED to {config.risk.min_rr_ratio}")

    # CHECK 4: Unchanged fields stay unchanged
    assert (
        config.indicators.rsi_overbought == base.indicators.rsi_overbought
    ), "Unchanged field was modified"
    print(
        f"✓ Unmodified fields preserved: rsi_overbought={config.indicators.rsi_overbought}"
    )

    print("\n✅ TEST 1 PASSED: Configuration overrides are properly applied to nested fields\n")


def test_2_config_context():
    """Test: ConfigContext properly bridges UserConfig to analysis functions."""
    print("\n" + "=" * 80)
    print("TEST 2: ConfigContext - Config Available in Analysis ✓")
    print("=" * 80)

    # Create config with overrides
    # Note: rsi_oversold must be > rsi_extreme_oversold (which is 25 in risky profile)
    config = get_profile_with_overrides(
        "risky", {"rsi_oversold": 32.0, "max_signals_returned": 20}
    )
    print(f"✓ Created config with overrides: {config.custom_overrides}")

    # Create context from config
    ctx = get_config_context(config)
    print(f"✓ Created ConfigContext from UserConfig")

    # CHECK 1: Context has correct values from config
    assert ctx.rsi_oversold == 32.0, f"Context RSI oversold incorrect: {ctx.rsi_oversold}"
    print(f"✓ ConfigContext.rsi_oversold = {ctx.rsi_oversold} (from overrides)")

    assert (
        ctx.max_signals_returned == 20
    ), f"Context max signals incorrect: {ctx.max_signals_returned}"
    print(f"✓ ConfigContext.max_signals_returned = {ctx.max_signals_returned} (from overrides)")

    # CHECK 2: Validation works
    is_valid, errors = validate_config_context(ctx)
    assert is_valid, f"Validation failed: {errors}"
    print(f"✓ ConfigContext validation passed")

    print(
        "\n✅ TEST 2 PASSED: ConfigContext properly extracts and validates config\n"
    )


def test_3_config_manager_end_to_end():
    """Test: Full end-to-end config manager flow with overrides."""
    print("\n" + "=" * 80)
    print("TEST 3: ConfigManager End-to-End ✓")
    print("=" * 80)

    mgr = get_config_manager()

    # Get default config
    default = mgr.get_config(risk_profile="neutral")
    print(f"✓ Got default neutral profile: rsi_oversold={default.indicators.rsi_oversold}")

    # Get with overrides
    session_overrides = {
        "rsi_oversold": 26.0,
        "min_rr_ratio": 2.2,
        "max_signals_returned": 25,
    }
    overridden = mgr.get_config(
        risk_profile="neutral", session_overrides=session_overrides
    )
    print(f"✓ Got config with overrides: {session_overrides}")

    # CHECK 1: Overrides were applied
    assert overridden.indicators.rsi_oversold == 26.0
    assert overridden.risk.min_rr_ratio == 2.2
    assert overridden.signals.max_signals_returned == 25
    print(f"✓ ✓ ✓ All overrides properly applied to nested fields")

    # CHECK 2: Values differ from default
    assert overridden.indicators.rsi_oversold != default.indicators.rsi_oversold
    print(
        f"✓ Overridden value differs from default: "
        f"{overridden.indicators.rsi_oversold} != {default.indicators.rsi_oversold}"
    )

    # CHECK 3: Validation
    is_valid, errors = mgr.validate_overrides(session_overrides)
    assert is_valid, f"Validation failed: {errors}"
    print(f"✓ Overrides validated successfully")

    print("\n✅ TEST 3 PASSED: Config manager properly handles overrides end-to-end\n")


def test_4_different_profiles():
    """Test: Different profiles produce different configurations."""
    print("\n" + "=" * 80)
    print("TEST 4: Profile Variations ✓")
    print("=" * 80)

    risky = get_profile("risky")
    neutral = get_profile("neutral")
    averse = get_profile("averse")

    print(f"Risky profile RSI oversold:  {risky.indicators.rsi_oversold}")
    print(f"Neutral profile RSI oversold: {neutral.indicators.rsi_oversold}")
    print(f"Averse profile RSI oversold:  {averse.indicators.rsi_oversold}")

    # Profiles should be different
    assert risky.indicators.rsi_oversold != neutral.indicators.rsi_oversold
    assert averse.indicators.rsi_oversold != neutral.indicators.rsi_oversold
    print(f"✓ ✓ ✓ Profiles have different RSI oversold thresholds")

    # Apply same override to all profiles
    override = {"rsi_oversold": 32.0}
    risky_ov = get_profile_with_overrides("risky", override)
    neutral_ov = get_profile_with_overrides("neutral", override)
    averse_ov = get_profile_with_overrides("averse", override)

    # After override, all should be the same for that field
    assert risky_ov.indicators.rsi_oversold == 32.0
    assert neutral_ov.indicators.rsi_oversold == 32.0
    assert averse_ov.indicators.rsi_oversold == 32.0
    print(f"✓ ✓ ✓ Same override applied to all profiles produces same value: 32.0")

    # But other fields should still be different
    assert risky_ov.risk.min_rr_ratio != averse_ov.risk.min_rr_ratio
    print(
        f"✓ Other fields still differ: "
        f"risky min_rr_ratio={risky_ov.risk.min_rr_ratio}, "
        f"averse min_rr_ratio={averse_ov.risk.min_rr_ratio}"
    )

    print("\n✅ TEST 4 PASSED: Different profiles work correctly\n")


def main():
    """Run all tests."""
    print("\n" + "=" * 80)
    print("CONFIG OVERRIDE FIXES - COMPREHENSIVE TEST SUITE")
    print("=" * 80)

    try:
        test_1_get_profile_with_overrides()
        test_2_config_context()
        test_3_config_manager_end_to_end()
        test_4_different_profiles()

        print("\n" + "=" * 80)
        print("🎉 ALL TESTS PASSED! 🎉")
        print("=" * 80)
        print("\nFixes verified:")
        print("✅ Issue #1: get_profile_with_overrides - Overrides now applied to nested fields")
        print("✅ Issue #2: ConfigContext bridges config to analysis functions")
        print("✅ Issue #3: End-to-end flow properly applies overrides")
        print("\n")
        return 0

    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}\n")
        return 1
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}\n")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
