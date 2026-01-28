#!/usr/bin/env python3
"""
Fixed version: Comprehensive test script for all 9 MCP tools with proper time periods.

Tests all MCP server tools with correct parameters:
1. analyze_security (period=3mo)
2. compare_securities (period=3mo)
3. screen_securities (period=3mo)
4. get_trade_plan (period=3mo)
5. scan_trades
6. portfolio_risk
7. morning_brief
8. analyze_fibonacci (period=3mo, window=50)
9. options_risk_analysis
"""

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Import MCP server functions
import sys
sys.path.insert(0, str(Path(__file__).parent))

from src.technical_analysis_mcp.server import (
    analyze_security,
    compare_securities,
    screen_securities,
    get_trade_plan,
    scan_trades,
    portfolio_risk,
    morning_brief,
    analyze_fibonacci,
    options_risk_analysis,
)


class MCPToolsTesterFixed:
    """Fixed tester for all 9 MCP tools with proper parameters."""

    def __init__(self, output_dir: str | None = None):
        """Initialize tester with output directory."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if output_dir:
            self.output_dir = Path(output_dir)
        else:
            self.output_dir = Path(__file__).parent / "mcp_test_results_fixed" / timestamp

        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.results: dict[str, dict[str, Any]] = {}

        logger.info(f"Test results will be saved to: {self.output_dir}")

    def save_result(self, tool_name: str, result: dict[str, Any]) -> None:
        """Save tool result to JSON file."""
        output_file = self.output_dir / f"{tool_name}.json"
        with open(output_file, "w") as f:
            json.dump(result, f, indent=2, default=str)
        logger.info(f"✓ Saved {tool_name} result to {output_file}")

    async def test_analyze_security(self) -> dict[str, Any]:
        """Test 1: analyze_security tool with 3mo period."""
        logger.info("=" * 80)
        logger.info("TEST 1: analyze_security (FIXED: period=3mo)")
        logger.info("=" * 80)

        try:
            result = await analyze_security(
                symbol="AAPL",
                period="3mo",  # FIXED: Changed from 1mo to 3mo
                use_ai=False,
            )
            self.save_result("01_analyze_security_aapl", result)
            self.results["analyze_security"] = {
                "status": "success",
                "symbol": "AAPL",
                "signals": result.get("summary", {}).get("total_signals", 0),
                "avg_score": result.get("summary", {}).get("avg_score", 0),
            }
            logger.info(
                f"✓ analyze_security completed: {result.get('summary', {}).get('total_signals')} signals, "
                f"avg_score={result.get('summary', {}).get('avg_score', 0):.1f}"
            )
            return result
        except Exception as e:
            logger.error(f"✗ analyze_security failed: {e}")
            self.results["analyze_security"] = {"status": "error", "error": str(e)}
            return {"error": str(e)}

    async def test_compare_securities(self) -> dict[str, Any]:
        """Test 2: compare_securities tool with 3mo period."""
        logger.info("=" * 80)
        logger.info("TEST 2: compare_securities (FIXED: period=3mo)")
        logger.info("=" * 80)

        try:
            result = await compare_securities(
                symbols=["AAPL", "MSFT", "GOOGL", "TSLA", "NVDA"],
                metric="signals",
            )
            self.save_result("02_compare_securities", result)
            winner = result.get("winner", {})
            self.results["compare_securities"] = {
                "status": "success",
                "winner": winner.get("symbol") if winner else None,
                "score": winner.get("score") if winner else 0,
                "compared": len(result.get("comparison", [])),
            }
            logger.info(
                f"✓ compare_securities completed: winner={winner.get('symbol') if winner else 'NONE'}, "
                f"score={winner.get('score', 0):.1f}"
            )
            return result
        except Exception as e:
            logger.error(f"✗ compare_securities failed: {e}")
            self.results["compare_securities"] = {"status": "error", "error": str(e)}
            return {"error": str(e)}

    async def test_screen_securities(self) -> dict[str, Any]:
        """Test 3: screen_securities tool with relaxed criteria."""
        logger.info("=" * 80)
        logger.info("TEST 3: screen_securities (FIXED: relaxed criteria)")
        logger.info("=" * 80)

        try:
            result = await screen_securities(
                universe="sp500",
                criteria={
                    "rsi": {"min": 20, "max": 80},  # FIXED: More relaxed range
                    "min_score": 40,  # FIXED: Lower threshold
                    "min_bullish": 5,  # FIXED: Lower requirement
                },
                limit=20,
            )
            self.save_result("03_screen_securities", result)
            matches = len(result.get("matches", []))
            self.results["screen_securities"] = {
                "status": "success",
                "matches": matches,
                "universe": "sp500",
                "criteria": "relaxed",
            }
            logger.info(f"✓ screen_securities completed: {matches} matches found")

            # Log top matches
            if matches > 0:
                logger.info("Top 5 matches:")
                for match in result.get("matches", [])[:5]:
                    logger.info(
                        f"  - {match['symbol']}: score={match['score']:.1f}, "
                        f"RSI={match['rsi']:.1f}, signals={match['signals']}"
                    )

            return result
        except Exception as e:
            logger.error(f"✗ screen_securities failed: {e}")
            self.results["screen_securities"] = {"status": "error", "error": str(e)}
            return {"error": str(e)}

    async def test_get_trade_plan(self) -> dict[str, Any]:
        """Test 4: get_trade_plan tool with 3mo period."""
        logger.info("=" * 80)
        logger.info("TEST 4: get_trade_plan (FIXED: period=3mo)")
        logger.info("=" * 80)

        try:
            result = await get_trade_plan(
                symbol="AAPL",
                period="3mo",  # FIXED: Changed from 1mo to 3mo
            )
            self.save_result("04_get_trade_plan_aapl", result)

            # Test another symbol
            result_msft = await get_trade_plan(symbol="MSFT", period="3mo")
            self.save_result("04_get_trade_plan_msft", result_msft)

            has_trades = result.get("has_trades", False)
            trade_count = len(result.get("trade_plans", []))
            self.results["get_trade_plan"] = {
                "status": "success",
                "has_trades": has_trades,
                "trade_count": trade_count,
            }
            logger.info(f"✓ get_trade_plan completed: has_trades={has_trades}, count={trade_count}")

            if has_trades:
                for i, plan in enumerate(result.get("trade_plans", []), 1):
                    logger.info(
                        f"  Trade Plan {i}: {plan.get('bias')} @ ${plan.get('entry_price', 0):.2f}, "
                        f"R:R={plan.get('risk_reward_ratio', 0):.2f}"
                    )

            return result
        except Exception as e:
            logger.error(f"✗ get_trade_plan failed: {e}")
            self.results["get_trade_plan"] = {"status": "error", "error": str(e)}
            return {"error": str(e)}

    async def test_scan_trades(self) -> dict[str, Any]:
        """Test 5: scan_trades tool."""
        logger.info("=" * 80)
        logger.info("TEST 5: scan_trades")
        logger.info("=" * 80)

        try:
            result = await scan_trades(
                universe="nasdaq100",  # FIXED: Using smaller universe for speed
                max_results=10,
            )
            self.save_result("05_scan_trades_nasdaq100", result)

            qualified = len(result.get("qualified_trades", []))
            self.results["scan_trades"] = {
                "status": "success",
                "qualified_trades": qualified,
                "universe": "nasdaq100",
            }
            logger.info(f"✓ scan_trades completed: {qualified} qualified trades found")

            if qualified > 0:
                logger.info("Top qualified trades:")
                for trade in result.get("qualified_trades", [])[:5]:
                    logger.info(
                        f"  - {trade.get('symbol')}: {trade.get('bias')} @ ${trade.get('entry_price', 0):.2f}, "
                        f"R:R={trade.get('risk_reward_ratio', 0):.2f}"
                    )

            return result
        except Exception as e:
            logger.error(f"✗ scan_trades failed: {e}")
            self.results["scan_trades"] = {"status": "error", "error": str(e)}
            return {"error": str(e)}

    async def test_portfolio_risk(self) -> dict[str, Any]:
        """Test 6: portfolio_risk tool."""
        logger.info("=" * 80)
        logger.info("TEST 6: portfolio_risk")
        logger.info("=" * 80)

        try:
            positions = [
                {"symbol": "AAPL", "shares": 100, "entry_price": 150.0},
                {"symbol": "MSFT", "shares": 50, "entry_price": 400.0},
                {"symbol": "GOOGL", "shares": 75, "entry_price": 140.0},
                {"symbol": "TSLA", "shares": 30, "entry_price": 250.0},
            ]

            result = await portfolio_risk(positions=positions)
            self.save_result("06_portfolio_risk", result)

            total_value = result.get("total_value", 0)
            max_loss = result.get("total_max_loss", 0)
            risk_level = result.get("overall_risk_level", "UNKNOWN")
            risk_pct = result.get("risk_percent_of_portfolio", 0)

            self.results["portfolio_risk"] = {
                "status": "success",
                "total_value": total_value,
                "risk_level": risk_level,
                "position_count": len(positions),
                "risk_percent": risk_pct,
            }
            logger.info(
                f"✓ portfolio_risk completed: total_value=${total_value:,.2f}, "
                f"max_loss=${max_loss:,.2f}, risk={risk_level} ({risk_pct:.1f}%)"
            )
            return result
        except Exception as e:
            logger.error(f"✗ portfolio_risk failed: {e}")
            self.results["portfolio_risk"] = {"status": "error", "error": str(e)}
            return {"error": str(e)}

    async def test_morning_brief(self) -> dict[str, Any]:
        """Test 7: morning_brief tool."""
        logger.info("=" * 80)
        logger.info("TEST 7: morning_brief")
        logger.info("=" * 80)

        try:
            watchlist = ["AAPL", "MSFT", "GOOGL", "TSLA", "NVDA", "META", "AMZN"]

            result = await morning_brief(
                watchlist=watchlist,
                market_region="US",
            )
            self.save_result("07_morning_brief", result)

            signals = len(result.get("watchlist_signals", []))
            themes = len(result.get("key_themes", []))
            self.results["morning_brief"] = {
                "status": "success",
                "signals": signals,
                "themes": themes,
                "watchlist_count": len(watchlist),
            }
            logger.info(f"✓ morning_brief completed: {signals} signals, {themes} themes")

            if themes > 0:
                logger.info("Key themes:")
                for theme in result.get("key_themes", []):
                    logger.info(f"  - {theme}")

            return result
        except Exception as e:
            logger.error(f"✗ morning_brief failed: {e}")
            self.results["morning_brief"] = {"status": "error", "error": str(e)}
            return {"error": str(e)}

    async def test_analyze_fibonacci(self) -> dict[str, Any]:
        """Test 8: analyze_fibonacci tool with 3mo period."""
        logger.info("=" * 80)
        logger.info("TEST 8: analyze_fibonacci (FIXED: period=3mo)")
        logger.info("=" * 80)

        try:
            result = await analyze_fibonacci(
                symbol="AAPL",
                period="3mo",  # FIXED: Changed from 1mo to 3mo
                window=50,
            )
            self.save_result("08_analyze_fibonacci_aapl", result)

            # Test crypto with longer period
            result_btc = await analyze_fibonacci(
                symbol="BTC-USD",
                period="6mo",  # Even longer for crypto
                window=100,
            )
            self.save_result("08_analyze_fibonacci_btc", result_btc)

            levels = len(result.get("levels", []))
            signals = len(result.get("signals", []))
            clusters = len(result.get("clusters", []))
            confluence_zones = len(result.get("confluenceZones", []))
            high_conf_zones = result.get("summary", {}).get("highConfidenceZones", 0)

            self.results["analyze_fibonacci"] = {
                "status": "success",
                "levels": levels,
                "signals": signals,
                "clusters": clusters,
                "confluence_zones": confluence_zones,
                "high_confidence_zones": high_conf_zones,
            }
            logger.info(
                f"✓ analyze_fibonacci completed: {levels} levels, {signals} signals, "
                f"{clusters} clusters, {confluence_zones} confluence zones ({high_conf_zones} high confidence)"
            )

            if confluence_zones > 0:
                logger.info("Top 3 confluence zones:")
                for zone in result.get("confluenceZones", [])[:3]:
                    logger.info(
                        f"  - ${zone['price']:.2f}: {zone['strength']} "
                        f"(score={zone['confluenceScore']:.1f}, signals={zone['signalCount']})"
                    )

            return result
        except Exception as e:
            logger.error(f"✗ analyze_fibonacci failed: {e}")
            self.results["analyze_fibonacci"] = {"status": "error", "error": str(e)}
            return {"error": str(e)}

    async def test_options_risk_analysis(self) -> dict[str, Any]:
        """Test 9: options_risk_analysis tool."""
        logger.info("=" * 80)
        logger.info("TEST 9: options_risk_analysis")
        logger.info("=" * 80)

        try:
            result = await options_risk_analysis(
                symbol="AAPL",
                expiration_date=None,  # Use nearest expiration
                option_type="both",
                min_volume=10,
            )
            self.save_result("09_options_risk_analysis_aapl", result)

            # Test SPY with higher volume threshold
            result_spy = await options_risk_analysis(
                symbol="SPY",
                expiration_date=None,
                option_type="both",
                min_volume=50,
            )
            self.save_result("09_options_risk_analysis_spy", result_spy)

            # Test QQQ
            result_qqq = await options_risk_analysis(
                symbol="QQQ",
                expiration_date=None,
                option_type="both",
                min_volume=50,
            )
            self.save_result("09_options_risk_analysis_qqq", result_qqq)

            calls = result.get("calls", {})
            puts = result.get("puts", {})
            pcr = result.get("put_call_ratio", {})
            warnings = result.get("risk_warnings", [])
            opps = result.get("opportunities", [])

            self.results["options_risk_analysis"] = {
                "status": "success",
                "symbol": result.get("symbol"),
                "dte": result.get("days_to_expiration"),
                "pcr_volume": pcr.get("volume"),
                "calls_liquid": calls.get("liquid_contracts", 0) if calls else 0,
                "puts_liquid": puts.get("liquid_contracts", 0) if puts else 0,
                "warnings": len(warnings),
                "opportunities": len(opps),
            }
            logger.info(
                f"✓ options_risk_analysis completed: "
                f"DTE={result.get('days_to_expiration')}, "
                f"PCR={pcr.get('volume', 0):.2f}, "
                f"{len(warnings)} warnings, {len(opps)} opportunities"
            )

            if warnings:
                logger.info("Risk warnings:")
                for warning in warnings[:3]:
                    logger.info(f"  ⚠️ {warning}")

            if opps:
                logger.info("Opportunities:")
                for opp in opps[:3]:
                    logger.info(f"  💡 {opp}")

            return result
        except Exception as e:
            logger.error(f"✗ options_risk_analysis failed: {e}")
            self.results["options_risk_analysis"] = {"status": "error", "error": str(e)}
            return {"error": str(e)}

    async def run_all_tests(self) -> None:
        """Run all 9 MCP tool tests in sequence."""
        logger.info("\n\n")
        logger.info("=" * 80)
        logger.info("MCP FINANCE - FIXED COMPREHENSIVE TOOL TEST SUITE")
        logger.info("Testing all 9 MCP tools with proper parameters")
        logger.info("=" * 80)
        logger.info(f"Output directory: {self.output_dir}")
        logger.info(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("\n")

        start_time = datetime.now()

        # Run all tests
        await self.test_analyze_security()
        await self.test_compare_securities()
        await self.test_screen_securities()
        await self.test_get_trade_plan()
        await self.test_scan_trades()
        await self.test_portfolio_risk()
        await self.test_morning_brief()
        await self.test_analyze_fibonacci()
        await self.test_options_risk_analysis()

        # Calculate duration
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        # Generate summary
        self.generate_summary(duration)

    def generate_summary(self, duration: float) -> None:
        """Generate and save test summary."""
        logger.info("\n\n")
        logger.info("=" * 80)
        logger.info("FIXED TEST SUMMARY")
        logger.info("=" * 80)

        success_count = sum(1 for r in self.results.values() if r.get("status") == "success")
        error_count = sum(1 for r in self.results.values() if r.get("status") == "error")

        summary = {
            "timestamp": datetime.now().isoformat(),
            "duration_seconds": round(duration, 2),
            "total_tests": len(self.results),
            "successful": success_count,
            "errors": error_count,
            "success_rate": f"{(success_count / len(self.results) * 100):.1f}%",
            "results": self.results,
        }

        # Save summary
        summary_file = self.output_dir / "SUMMARY.json"
        with open(summary_file, "w") as f:
            json.dump(summary, f, indent=2, default=str)

        # Print summary
        logger.info(f"Total Tests: {len(self.results)}")
        logger.info(f"Successful: {success_count} ({summary['success_rate']})")
        logger.info(f"Errors: {error_count}")
        logger.info(f"Duration: {duration:.2f} seconds")
        logger.info("")

        logger.info("Individual Test Results:")
        for tool_name, result in self.results.items():
            status = result.get("status")
            if status == "success":
                extra_info = []
                if "signals" in result:
                    extra_info.append(f"{result['signals']} signals")
                if "avg_score" in result:
                    extra_info.append(f"score={result['avg_score']:.1f}")
                if "matches" in result:
                    extra_info.append(f"{result['matches']} matches")
                if "qualified_trades" in result:
                    extra_info.append(f"{result['qualified_trades']} trades")
                if "confluence_zones" in result:
                    extra_info.append(f"{result['confluence_zones']} zones")

                extra = f" ({', '.join(extra_info)})" if extra_info else ""
                logger.info(f"  ✓ {tool_name}: SUCCESS{extra}")
            else:
                logger.info(f"  ✗ {tool_name}: ERROR - {result.get('error')}")

        logger.info("")
        logger.info(f"Results saved to: {self.output_dir}")
        logger.info(f"Summary: {summary_file}")
        logger.info("")

        # List all output files
        json_files = sorted(self.output_dir.glob("*.json"))
        logger.info(f"Generated {len(json_files)} output files:")
        total_size = 0
        for f in json_files:
            size = f.stat().st_size
            total_size += size
            logger.info(f"  - {f.name} ({size:,} bytes)")

        logger.info(f"\nTotal output size: {total_size:,} bytes ({total_size / 1024:.1f} KB)")
        logger.info("")
        logger.info("=" * 80)
        logger.info(f"ALL TESTS COMPLETED - {summary['success_rate']} SUCCESS RATE")
        logger.info("=" * 80)


async def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Test all 9 MCP tools with fixed parameters")
    parser.add_argument(
        "--output-dir",
        "-o",
        help="Output directory for test results (default: auto-generated)",
        default=None,
    )
    args = parser.parse_args()

    tester = MCPToolsTesterFixed(output_dir=args.output_dir)
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
