"""Backend testing configuration for validating config changes."""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

from ..profiles.base_config import UserConfig, RiskProfile
from ..profiles.risk_profiles import get_profile

logger = logging.getLogger(__name__)


@dataclass
class TestScenario:
    """Definition of a test scenario.

    Attributes:
        name: Unique scenario identifier
        description: Human-readable scenario description
        config: UserConfig to test with
        symbols: List of symbols to analyze
        expected_behaviors: Dict mapping symbols to expected behavior assertions
            Example:
            {
                "AAPL": {
                    "min_trades": 1,
                    "max_trades": 5,
                    "rr_range": (1.2, 3.0),
                    "momentum_state": ["strong_up", "up"]
                }
            }
    """

    name: str
    description: str
    config: UserConfig
    symbols: List[str]
    expected_behaviors: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TestResult:
    """Result of a test scenario run.

    Attributes:
        scenario_name: Name of the scenario that was run
        timestamp: When the test was executed
        passed: Whether all assertions passed
        duration_ms: Execution time in milliseconds
        results_by_symbol: Raw analysis results for each symbol
        violations: List of assertion violations (if any)
        config_used: Configuration that was applied
    """

    scenario_name: str
    timestamp: datetime
    passed: bool
    duration_ms: float
    results_by_symbol: Dict[str, Dict[str, Any]]
    violations: List[str]
    config_used: Dict[str, Any]


class BackendTestRunner:
    """Run tests against different configurations.

    This class manages test execution, result collection, and reporting
    for validating that configuration changes produce expected results.
    """

    def __init__(self):
        """Initialize test runner."""
        self._results: List[TestResult] = []

    async def run_scenario(
        self,
        scenario: TestScenario,
    ) -> TestResult:
        """Run a single test scenario.

        Args:
            scenario: TestScenario definition to execute

        Returns:
            TestResult with pass/fail status and details
        """
        start = datetime.now()
        violations = []
        results_by_symbol = {}

        logger.info(f"Running scenario: {scenario.name}")

        for symbol in scenario.symbols:
            try:
                # Run analysis with scenario config
                result = await self._analyze_with_config(symbol, scenario.config)
                results_by_symbol[symbol] = result

                # Check expected behaviors
                if symbol in scenario.expected_behaviors:
                    symbol_violations = self._check_expectations(
                        result, scenario.expected_behaviors[symbol]
                    )
                    violations.extend(symbol_violations)
                    if symbol_violations:
                        logger.warning(
                            f"  {symbol}: {len(symbol_violations)} violations"
                        )
                    else:
                        logger.info(f"  {symbol}: ✓ Passed")

            except Exception as e:
                error_msg = f"{symbol}: Error - {str(e)}"
                violations.append(error_msg)
                results_by_symbol[symbol] = {"error": str(e)}
                logger.error(f"  {symbol}: ✗ {str(e)}")

        duration = (datetime.now() - start).total_seconds() * 1000

        test_result = TestResult(
            scenario_name=scenario.name,
            timestamp=start,
            passed=len(violations) == 0,
            duration_ms=duration,
            results_by_symbol=results_by_symbol,
            violations=violations,
            config_used=scenario.config.to_dict(),
        )

        self._results.append(test_result)
        return test_result

    async def run_profile_comparison(
        self,
        symbols: List[str],
    ) -> Dict[str, TestResult]:
        """Run all three risk profiles against symbols and compare.

        Useful for A/B testing profile configurations to ensure they
        produce meaningfully different results.

        Args:
            symbols: List of symbols to analyze with each profile

        Returns:
            Dictionary mapping profile names to TestResults
        """
        logger.info(f"Running profile comparison on {len(symbols)} symbols")
        comparison = {}

        for profile in RiskProfile:
            scenario = TestScenario(
                name=f"profile_{profile.value}",
                description=f"Profile comparison: {profile.value}",
                config=get_profile(profile),
                symbols=symbols,
            )
            result = await self.run_scenario(scenario)
            comparison[profile.value] = result

        return comparison

    async def run_config_sweep(
        self,
        symbol: str,
        param_name: str,
        param_values: List[Any],
        base_profile: RiskProfile = RiskProfile.NEUTRAL,
    ) -> List[Dict[str, Any]]:
        """Sweep a single parameter across values.

        Useful for finding optimal threshold values by observing how
        changes to a single parameter affect analysis output.

        Args:
            symbol: Symbol to analyze
            param_name: Name of parameter to sweep
            param_values: List of values to test
            base_profile: Base profile to start from

        Returns:
            List of results showing parameter value and its effects

        Example:
            results = await runner.run_config_sweep(
                "AAPL",
                "rsi_oversold",
                [20, 25, 30, 35, 40],
            )
        """
        logger.info(
            f"Running config sweep: {param_name} = {param_values} for {symbol}"
        )
        results = []
        base_config = get_profile(base_profile)

        for value in param_values:
            # Create config with override
            test_config = self._override_param(base_config, param_name, value)

            # Run analysis
            analysis = await self._analyze_with_config(symbol, test_config)

            trades_found = len(analysis.get("trade_plans", []))
            avg_rr = self._calc_avg_rr(analysis)
            signal_count = len(analysis.get("signals", []))

            result_item = {
                "param_value": value,
                "trades_found": trades_found,
                "avg_rr": avg_rr,
                "signal_count": signal_count,
            }
            results.append(result_item)

            logger.debug(
                f"  {param_name}={value}: {trades_found} trades, "
                f"avg_rr={avg_rr:.2f}, {signal_count} signals"
            )

        return results

    def generate_report(self) -> str:
        """Generate test report from all results.

        Returns:
            Markdown-formatted test report
        """
        report = ["# Backend Configuration Test Report", ""]
        report.append(f"Generated: {datetime.now().isoformat()}")
        report.append(f"Total scenarios run: {len(self._results)}")
        report.append("")

        passed = sum(1 for r in self._results if r.passed)
        failed = len(self._results) - passed

        status = "✅ ALL PASSED" if failed == 0 else f"⚠️  {failed} FAILED"
        report.append(f"## Test Summary: {status}")
        report.append(f"- Passed: {passed}/{len(self._results)}")
        report.append(f"- Failed: {failed}/{len(self._results)}")
        report.append("")

        for result in self._results:
            status = "✅" if result.passed else "❌"
            report.append(f"### {status} {result.scenario_name}")
            report.append(f"Duration: {result.duration_ms:.1f}ms")
            report.append(f"Symbols tested: {len(result.results_by_symbol)}")

            if result.violations:
                report.append("#### Violations:")
                for v in result.violations:
                    report.append(f"- {v}")

            report.append("")

        return "\n".join(report)

    async def _analyze_with_config(
        self,
        symbol: str,
        config: UserConfig,
    ) -> Dict[str, Any]:
        """Run analyze_security with specific config.

        Args:
            symbol: Stock symbol
            config: Configuration to use

        Returns:
            Analysis result dictionary
        """
        # Import here to avoid circular imports
        from ..server import analyze_security

        try:
            # Call the actual server function with risk_profile parameter
            # For now, we'll return a placeholder that shows config was applied
            result = await analyze_security(
                symbol,
                period="1mo",
                # risk_profile would be added here once server.py supports it
            )
            return result
        except Exception as e:
            logger.error(f"Error analyzing {symbol}: {e}")
            raise

    def _check_expectations(
        self,
        result: Dict[str, Any],
        expectations: Dict[str, Any],
    ) -> List[str]:
        """Check if result meets expectations.

        Args:
            result: Analysis result to check
            expectations: Dictionary of expected conditions

        Returns:
            List of violation messages (empty if all pass)
        """
        violations = []

        trades = result.get("trade_plans", [])

        if "min_trades" in expectations:
            if len(trades) < expectations["min_trades"]:
                violations.append(
                    f"Expected min {expectations['min_trades']} trades, "
                    f"got {len(trades)}"
                )

        if "max_trades" in expectations:
            if len(trades) > expectations["max_trades"]:
                violations.append(
                    f"Expected max {expectations['max_trades']} trades, "
                    f"got {len(trades)}"
                )

        if "rr_range" in expectations and trades:
            min_rr, max_rr = expectations["rr_range"]
            for i, trade in enumerate(trades):
                rr = trade.get("risk_reward", 0)
                if not (min_rr <= rr <= max_rr):
                    violations.append(
                        f"Trade {i+1} R:R {rr:.2f} outside expected "
                        f"range ({min_rr}, {max_rr})"
                    )

        if "signal_count_range" in expectations:
            min_signals, max_signals = expectations["signal_count_range"]
            signal_count = len(result.get("signals", []))
            if not (min_signals <= signal_count <= max_signals):
                violations.append(
                    f"Signal count {signal_count} outside expected "
                    f"range ({min_signals}, {max_signals})"
                )

        return violations

    def _override_param(
        self,
        config: UserConfig,
        param_name: str,
        value: Any,
    ) -> UserConfig:
        """Create new config with single param override.

        Args:
            config: Base configuration
            param_name: Parameter name to override
            value: New value

        Returns:
            New UserConfig with override applied
        """
        return UserConfig(
            risk_profile=config.risk_profile,
            indicators=config.indicators,
            risk=config.risk,
            momentum=config.momentum,
            signals=config.signals,
            custom_overrides={param_name: value},
        )

    def _calc_avg_rr(self, analysis: Dict[str, Any]) -> float:
        """Calculate average R:R from analysis.

        Args:
            analysis: Analysis result

        Returns:
            Average risk:reward ratio or 0.0 if no trades
        """
        trades = analysis.get("trade_plans", [])
        if not trades:
            return 0.0
        rrs = [t.get("risk_reward", 0) for t in trades]
        return sum(rrs) / len(rrs)

    def clear_results(self) -> None:
        """Clear all stored test results."""
        self._results = []
        logger.info("Test results cleared")
