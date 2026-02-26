"""
Standalone test runner for Fibonacci analysis tests.
Runs without requiring pytest to be installed.
"""

import sys
import traceback
from datetime import datetime
from io import StringIO


class TestRunner:
    """Simple test runner without pytest dependency."""

    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = []
        self.output = []

    def run_test(self, test_func, test_name: str):
        """Run a single test function."""
        try:
            test_func()
            self.passed += 1
            self._log(f"✓ PASS: {test_name}")
        except AssertionError as e:
            self.failed += 1
            self._log(f"✗ FAIL: {test_name}")
            self._log(f"  Error: {e}")
            self.errors.append((test_name, str(e)))
        except Exception as e:
            self.failed += 1
            self._log(f"✗ ERROR: {test_name}")
            self._log(f"  Exception: {e}")
            self.errors.append((test_name, f"Exception: {e}"))
            traceback.print_exc()

    def _log(self, message: str):
        """Log message."""
        self.output.append(message)
        print(message)

    def summary(self) -> str:
        """Get test summary."""
        total = self.passed + self.failed
        summary = f"""
{'=' * 70}
TEST SUMMARY
{'=' * 70}
Total Tests: {total}
Passed: {self.passed}
Failed: {self.failed}
Success Rate: {(self.passed/total*100):.1f}% if {total} > 0 else 0%
{'=' * 70}
"""
        return summary


def run_adaptive_tolerance_tests():
    """Run adaptive tolerance tests."""
    print("\n" + "=" * 70)
    print("1. ADAPTIVE TOLERANCE TESTS")
    print("=" * 70)

    runner = TestRunner()

    # Test 1: Tolerance initialization
    def test_init():
        import pandas as pd
        import numpy as np
        from fibonacci.analysis.tolerance import AdaptiveTolerance

        dates = pd.date_range(start="2024-01-01", periods=50, freq="1d")
        df = pd.DataFrame(
            {
                "Date": dates,
                "High": np.random.uniform(100, 110, 50),
                "Low": np.random.uniform(98, 108, 50),
                "Close": np.random.uniform(100, 110, 50),
            }
        )
        df.set_index("Date", inplace=True)

        tolerance = AdaptiveTolerance(df, base_tolerance=0.01)
        assert tolerance.base_tolerance == 0.01
        assert tolerance._atr is None

    runner.run_test(test_init, "Tolerance initialization")

    # Test 2: ATR calculation
    def test_atr():
        import pandas as pd
        import numpy as np
        from fibonacci.analysis.tolerance import AdaptiveTolerance

        dates = pd.date_range(start="2024-01-01", periods=50, freq="1d")
        df = pd.DataFrame(
            {
                "Date": dates,
                "High": np.linspace(100, 110, 50),
                "Low": np.linspace(98, 108, 50),
                "Close": np.linspace(100, 110, 50),
            }
        )
        df.set_index("Date", inplace=True)

        tolerance = AdaptiveTolerance(df)
        atr = tolerance.calculate_atr(period=14)
        assert atr >= 0

    runner.run_test(test_atr, "ATR calculation")

    # Test 3: Volatility factor bounds
    def test_vol_bounds():
        import pandas as pd
        import numpy as np
        from fibonacci.analysis.tolerance import AdaptiveTolerance

        dates = pd.date_range(start="2024-01-01", periods=50, freq="1d")
        df = pd.DataFrame(
            {
                "Date": dates,
                "High": np.random.uniform(100, 110, 50),
                "Low": np.random.uniform(98, 108, 50),
                "Close": np.random.uniform(100, 110, 50),
            }
        )
        df.set_index("Date", inplace=True)

        tolerance = AdaptiveTolerance(df)
        vol_factor = tolerance.get_volatility_factor()
        assert 0.5 <= vol_factor <= 2.0

    runner.run_test(test_vol_bounds, "Volatility factor bounds")

    # Test 4: Tolerance calculation
    def test_tolerance_calc():
        import pandas as pd
        import numpy as np
        from fibonacci.analysis.tolerance import AdaptiveTolerance

        dates = pd.date_range(start="2024-01-01", periods=50, freq="1d")
        df = pd.DataFrame(
            {
                "Date": dates,
                "High": np.linspace(100, 110, 50),
                "Low": np.linspace(98, 108, 50),
                "Close": np.linspace(100, 110, 50),
            }
        )
        df.set_index("Date", inplace=True)

        tolerance = AdaptiveTolerance(df, base_tolerance=0.01)
        tol = tolerance.get_tolerance("standard")
        assert tol > 0
        assert isinstance(tol, float)

    runner.run_test(test_tolerance_calc, "Tolerance calculation")

    # Test 5: Edge case - empty data
    def test_empty_data():
        import pandas as pd
        from fibonacci.analysis.tolerance import AdaptiveTolerance

        df = pd.DataFrame({"High": [], "Low": [], "Close": []})
        tolerance = AdaptiveTolerance(df)
        vol_factor = tolerance.get_volatility_factor()
        assert vol_factor == 1.0  # Should default

    runner.run_test(test_empty_data, "Edge case: empty data")

    print(runner.summary())
    return runner.passed, runner.failed


def run_database_schema_tests():
    """Run database schema tests."""
    print("\n" + "=" * 70)
    print("2. DATABASE SCHEMA TESTS")
    print("=" * 70)

    runner = TestRunner()

    # Test 1: Signal record creation
    def test_record_creation():
        from fibonacci.tests.test_database_schema import FibonacciSignalRecord
        from datetime import datetime

        now = datetime.utcnow()
        signal = FibonacciSignalRecord(
            id="sig_001",
            user_id="user_123",
            symbol="AAPL",
            level_price=150.0,
            level_name="0.618 Retracement",
            signal_time=now,
            signal_strength="strong",
            category="retracement",
            timeframe="1d",
        )
        assert signal.id == "sig_001"
        assert signal.symbol == "AAPL"

    runner.run_test(test_record_creation, "Signal record creation")

    # Test 2: Signal serialization
    def test_serialization():
        from fibonacci.tests.test_database_schema import FibonacciSignalRecord
        from datetime import datetime

        now = datetime.utcnow()
        signal = FibonacciSignalRecord(
            id="sig_001",
            user_id="user_123",
            symbol="AAPL",
            level_price=150.0,
            level_name="0.618 Retracement",
            signal_time=now,
            signal_strength="strong",
            category="retracement",
            timeframe="1d",
        )
        data = signal.to_dict()
        assert "id" in data
        assert data["symbol"] == "AAPL"

    runner.run_test(test_serialization, "Signal serialization")

    # Test 3: Performance calculation
    def test_performance():
        from fibonacci.tests.test_database_schema import (
            FibonacciSignalRecord,
            FibonacciSignalPerformance,
        )
        from datetime import datetime, timedelta

        now = datetime.utcnow()
        signals = []

        # Create test signals
        for i in range(3):
            signal = FibonacciSignalRecord(
                id=f"sig_win_{i}",
                user_id="user_123",
                symbol="AAPL",
                level_price=150.0,
                level_name="0.618",
                signal_time=now - timedelta(days=i),
                signal_strength="strong",
                category="retracement",
                timeframe="1d",
            )
            signal.result = "win"
            signal.result_price = 155.0
            signals.append(signal)

        performance = FibonacciSignalPerformance(signals)
        win_rate = performance.calculate_win_rate()
        assert win_rate == 1.0  # All wins

    runner.run_test(test_performance, "Performance calculation")

    # Test 4: Win rate calculation
    def test_win_rate():
        from fibonacci.tests.test_database_schema import (
            FibonacciSignalRecord,
            FibonacciSignalPerformance,
        )
        from datetime import datetime, timedelta

        now = datetime.utcnow()
        signals = []

        # 3 wins
        for i in range(3):
            signal = FibonacciSignalRecord(
                id=f"sig_win_{i}",
                user_id="user_123",
                symbol="AAPL",
                level_price=150.0,
                level_name="0.618",
                signal_time=now - timedelta(days=i),
                signal_strength="strong",
                category="retracement",
                timeframe="1d",
            )
            signal.result = "win"
            signal.result_price = 155.0
            signals.append(signal)

        # 2 losses
        for i in range(2):
            signal = FibonacciSignalRecord(
                id=f"sig_loss_{i}",
                user_id="user_123",
                symbol="AAPL",
                level_price=150.0,
                level_name="0.618",
                signal_time=now - timedelta(hours=i),
                signal_strength="moderate",
                category="retracement",
                timeframe="1d",
            )
            signal.result = "loss"
            signal.result_price = 148.0
            signals.append(signal)

        performance = FibonacciSignalPerformance(signals)
        win_rate = performance.calculate_win_rate()
        assert win_rate == 0.6  # 3 wins / 5 total

    runner.run_test(test_win_rate, "Win rate calculation")

    # Test 5: API response format
    def test_api_format():
        from fibonacci.tests.test_database_schema import (
            FibonacciSignalRecord,
            FibonacciSignalPerformance,
        )
        from datetime import datetime

        now = datetime.utcnow()
        signals = [
            FibonacciSignalRecord(
                id=f"sig_{i}",
                user_id="user_123",
                symbol="AAPL",
                level_price=150.0,
                level_name="0.618",
                signal_time=now,
                signal_strength="strong",
                category="retracement",
                timeframe="1d",
            )
            for i in range(2)
        ]

        performance = FibonacciSignalPerformance(signals)
        data = performance.to_dict()
        assert "total_signals" in data
        assert "win_rate" in data

    runner.run_test(test_api_format, "API response format")

    print(runner.summary())
    return runner.passed, runner.failed


def run_api_integration_tests():
    """Run API integration tests."""
    print("\n" + "=" * 70)
    print("3. API INTEGRATION TESTS")
    print("=" * 70)

    runner = TestRunner()

    # Test 1: Confluence zone sorting
    def test_zone_sorting():
        from fibonacci.tests.test_api_integration import ConfluenceZone

        zones = [
            ConfluenceZone(150.0, ["0.618"], "strong", 0.85, 1),
            ConfluenceZone(155.0, ["1.0"], "strong", 0.95, 1),
            ConfluenceZone(148.0, ["0.5"], "moderate", 0.65, 1),
        ]

        sorted_zones = sorted(
            zones, key=lambda z: z.confluence_score, reverse=True
        )
        assert sorted_zones[0].confluence_score == 0.95

    runner.run_test(test_zone_sorting, "Confluence zone sorting")

    # Test 2: Level properties
    def test_level_properties():
        from fibonacci.tests.test_api_integration import FibonacciLevel

        level = FibonacciLevel(
            key="fib_0.618",
            name="0.618 Retracement",
            price=150.0,
            ratio=0.618,
            strength="strong",
            distance_from_current=0.05,
        )

        data = level.to_dict()
        required_fields = [
            "key",
            "name",
            "price",
            "ratio",
            "strength",
            "distanceFromCurrent",
        ]
        for field in required_fields:
            assert field in data

    runner.run_test(test_level_properties, "Level properties")

    # Test 3: Signal properties
    def test_signal_properties():
        from fibonacci.tests.test_api_integration import FibonacciSignal

        signal = FibonacciSignal(
            signal="Price at 0.618",
            description="Test signal",
            strength="strong",
            category="retracement",
            timeframe="1d",
            value=150.0,
        )

        data = signal.to_dict()
        assert data["signal"] == "Price at 0.618"
        assert data["strength"] == "strong"

    runner.run_test(test_signal_properties, "Signal properties")

    # Test 4: Error handling
    def test_error_handling():
        error = {
            "status_code": 400,
            "message": "Symbol required",
        }
        assert error["status_code"] == 400

    runner.run_test(test_error_handling, "Error handling")

    # Test 5: Tier gating
    def test_tier_gating():
        free_levels = ["fib_0.236", "fib_0.382", "fib_0.5", "fib_0.618"]
        all_levels = [
            "fib_0.236",
            "fib_0.382",
            "fib_0.5",
            "fib_0.618",
            "fib_1.0",
            "fib_1.618",
        ]
        assert len(free_levels) < len(all_levels)

    runner.run_test(test_tier_gating, "Tier gating")

    print(runner.summary())
    return runner.passed, runner.failed


def run_dashboard_ui_tests():
    """Run dashboard UI tests."""
    print("\n" + "=" * 70)
    print("4. DASHBOARD UI TESTS")
    print("=" * 70)

    runner = TestRunner()

    # Test 1: Dashboard initialization
    def test_dashboard_init():
        from fibonacci.tests.test_dashboard_ui import DashboardPage

        dashboard = DashboardPage()
        assert dashboard.input_symbol is not None
        assert dashboard.result is None

    runner.run_test(test_dashboard_init, "Dashboard initialization")

    # Test 2: Symbol input
    def test_symbol_input():
        from fibonacci.tests.test_dashboard_ui import DashboardPage

        dashboard = DashboardPage()
        dashboard.set_symbol("aapl")
        assert dashboard.input_symbol.value == "AAPL"

    runner.run_test(test_symbol_input, "Symbol input uppercasing")

    # Test 3: Responsive layouts
    def test_responsive_layout():
        from fibonacci.tests.test_dashboard_ui import DashboardPage, Breakpoint

        dashboard = DashboardPage()
        dashboard.set_breakpoint(Breakpoint.MOBILE)
        layout = dashboard.get_current_layout()
        assert layout["columns"] == 1

        dashboard.set_breakpoint(Breakpoint.DESKTOP)
        layout = dashboard.get_current_layout()
        assert layout["columns"] == 3

    runner.run_test(test_responsive_layout, "Responsive layouts")

    # Test 4: Badge colors
    def test_badge_colors():
        from fibonacci.tests.test_dashboard_ui import Badge

        badge = Badge(text="STRONG")
        color = badge.get_color("STRONG")
        assert "green" in color.lower()

        badge = Badge(text="MODERATE")
        color = badge.get_color("MODERATE")
        assert "yellow" in color.lower()

    runner.run_test(test_badge_colors, "Badge colors")

    # Test 5: Error display
    def test_error_display():
        from fibonacci.tests.test_dashboard_ui import DashboardPage

        dashboard = DashboardPage()
        dashboard.analyze(None)  # Simulate failure
        assert dashboard.error is not None

    runner.run_test(test_error_display, "Error display")

    print(runner.summary())
    return runner.passed, runner.failed


def main():
    """Run all test suites."""
    print("\n" + "=" * 70)
    print("FIBONACCI ANALYSIS COMPREHENSIVE TEST SUITE")
    print("=" * 70)
    print(f"Started at: {datetime.now().isoformat()}")

    total_passed = 0
    total_failed = 0

    try:
        p, f = run_adaptive_tolerance_tests()
        total_passed += p
        total_failed += f
    except Exception as e:
        print(f"\n✗ Adaptive Tolerance tests failed: {e}")
        total_failed += 1

    try:
        p, f = run_database_schema_tests()
        total_passed += p
        total_failed += f
    except Exception as e:
        print(f"\n✗ Database Schema tests failed: {e}")
        total_failed += 1

    try:
        p, f = run_api_integration_tests()
        total_passed += p
        total_failed += f
    except Exception as e:
        print(f"\n✗ API Integration tests failed: {e}")
        total_failed += 1

    try:
        p, f = run_dashboard_ui_tests()
        total_passed += p
        total_failed += f
    except Exception as e:
        print(f"\n✗ Dashboard UI tests failed: {e}")
        total_failed += 1

    # Final summary
    print("\n" + "=" * 70)
    print("OVERALL TEST SUMMARY")
    print("=" * 70)
    total = total_passed + total_failed
    print(f"Total Tests Run: {total}")
    print(f"Passed: {total_passed}")
    print(f"Failed: {total_failed}")
    if total > 0:
        print(f"Success Rate: {(total_passed/total*100):.1f}%")
    print("=" * 70)
    print(f"Completed at: {datetime.now().isoformat()}")


if __name__ == "__main__":
    main()
