#!/usr/bin/env python
"""CLI tool for testing backend configurations.

Usage:
    python scripts/test_backend_config.py --mode scenarios
    python scripts/test_backend_config.py --mode compare --symbols AAPL NVDA TSLA
    python scripts/test_backend_config.py --mode sweep --symbols AAPL --param rsi_oversold --values 20 25 30 35 40
"""

import asyncio
import argparse
import json
import sys
import logging
from datetime import datetime
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from technical_analysis_mcp.testing import (
    BackendTestRunner,
    ALL_SCENARIOS,
)
from technical_analysis_mcp.profiles.base_config import RiskProfile
from technical_analysis_mcp.profiles.risk_profiles import get_profile

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Test backend configurations and risk profiles"
    )
    parser.add_argument(
        "--mode",
        choices=["scenarios", "compare", "sweep"],
        default="scenarios",
        help="Test mode to run",
    )
    parser.add_argument(
        "--symbols",
        nargs="+",
        default=["AAPL", "MSFT", "NVDA"],
        help="Symbols to test",
    )
    parser.add_argument(
        "--param",
        help="Parameter to sweep (for sweep mode)",
    )
    parser.add_argument(
        "--values",
        nargs="+",
        type=float,
        help="Values to sweep (for sweep mode)",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Output file for report (default: test_results_TIMESTAMP.md)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Verbose output",
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Set default output filename if not provided
    if not args.output:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        args.output = f"test_results_{timestamp}.md"

    runner = BackendTestRunner()

    print("=" * 70)
    print(f"Backend Configuration Test Runner")
    print(f"Mode: {args.mode}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("=" * 70)
    print()

    if args.mode == "scenarios":
        await run_scenarios(runner, args.output)

    elif args.mode == "compare":
        await run_compare(runner, args.symbols, args.output)

    elif args.mode == "sweep":
        if not args.param or not args.values:
            print("ERROR: --param and --values required for sweep mode")
            sys.exit(1)
        await run_sweep(runner, args.symbols[0], args.param, args.values, args.output)

    print()
    print("=" * 70)
    print(f"Report saved to: {args.output}")
    print("=" * 70)


async def run_scenarios(runner: BackendTestRunner, output_path: str) -> None:
    """Run all predefined scenarios.

    Args:
        runner: Test runner instance
        output_path: Path to save report
    """
    print(f"Running {len(ALL_SCENARIOS)} test scenarios...")
    print()

    for i, scenario in enumerate(ALL_SCENARIOS, 1):
        print(f"[{i}/{len(ALL_SCENARIOS)}] {scenario.name}")
        print(f"  Description: {scenario.description}")
        print(f"  Symbols: {', '.join(scenario.symbols)}")
        print(f"  Config: {scenario.config.risk_profile.value}")

        try:
            result = await runner.run_scenario(scenario)
            status = "✅ PASS" if result.passed else "❌ FAIL"
            print(f"  Result: {status} ({result.duration_ms:.1f}ms)")

            if result.violations:
                print(f"  Violations ({len(result.violations)}):")
                for violation in result.violations[:3]:  # Show first 3
                    print(f"    - {violation}")
                if len(result.violations) > 3:
                    print(f"    ... and {len(result.violations) - 3} more")
        except Exception as e:
            print(f"  Result: ❌ ERROR - {str(e)}")

        print()

    # Generate and save report
    report = runner.generate_report()
    with open(output_path, "w") as f:
        f.write(report)

    print(report)


async def run_compare(
    runner: BackendTestRunner, symbols: list[str], output_path: str
) -> None:
    """Run profile comparison.

    Args:
        runner: Test runner instance
        symbols: List of symbols to analyze
        output_path: Path to save report
    """
    print(f"Comparing risk profiles for {len(symbols)} symbols...")
    print(f"Symbols: {', '.join(symbols)}")
    print()

    comparison = await runner.run_profile_comparison(symbols)

    print("Profile Comparison Results:")
    print("-" * 70)

    profile_stats = {}
    for profile_name, result in comparison.items():
        total_trades = 0
        total_signals = 0
        error_count = 0

        for symbol_result in result.results_by_symbol.values():
            if "error" in symbol_result:
                error_count += 1
            else:
                total_trades += len(symbol_result.get("trade_plans", []))
                total_signals += len(symbol_result.get("signals", []))

        profile_stats[profile_name] = {
            "total_trades": total_trades,
            "total_signals": total_signals,
            "errors": error_count,
        }

        print(f"\n{profile_name.upper()}:")
        print(f"  Total trades: {total_trades}")
        print(f"  Total signals: {total_signals}")
        print(f"  Errors: {error_count}")
        print(f"  Duration: {result.duration_ms:.1f}ms")

    # Generate and save report
    report = runner.generate_report()
    report += "\n## Profile Comparison Summary\n\n"
    report += "| Profile | Trades | Signals | Errors |\n"
    report += "|---------|--------|---------|--------|\n"
    for profile, stats in profile_stats.items():
        report += (
            f"| {profile} | {stats['total_trades']} | "
            f"{stats['total_signals']} | {stats['errors']} |\n"
        )

    with open(output_path, "w") as f:
        f.write(report)

    print("\n" + "-" * 70)
    print(report)


async def run_sweep(
    runner: BackendTestRunner,
    symbol: str,
    param: str,
    values: list[float],
    output_path: str,
) -> None:
    """Run parameter sweep.

    Args:
        runner: Test runner instance
        symbol: Symbol to analyze
        param: Parameter name to sweep
        values: List of values to test
        output_path: Path to save report
    """
    print(f"Sweeping {param} = {values} for {symbol}...")
    print()

    results = await runner.run_config_sweep(symbol, param, values)

    print("Parameter Sweep Results:")
    print("-" * 70)
    print(f"{'Value':>10} | {'Trades':>6} | {'Avg R:R':>8} | {'Signals':>8}")
    print("-" * 45)

    for r in results:
        print(
            f"{r['param_value']:>10.2f} | "
            f"{r['trades_found']:>6} | "
            f"{r['avg_rr']:>8.2f} | "
            f"{r['signal_count']:>8}"
        )

    # Generate and save report
    report = runner.generate_report()
    report += f"\n## Parameter Sweep: {param}\n\n"
    report += "| Value | Trades | Avg R:R | Signals |\n"
    report += "|-------|--------|---------|----------|\n"
    for r in results:
        report += (
            f"| {r['param_value']:.2f} | {r['trades_found']} | "
            f"{r['avg_rr']:.2f} | {r['signal_count']} |\n"
        )

    with open(output_path, "w") as f:
        f.write(report)

    print("\n" + "-" * 70)
    print(report)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nTest run interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nFATAL ERROR: {str(e)}")
        logger.exception("Uncaught exception")
        sys.exit(1)
