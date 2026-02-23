#!/usr/bin/env python3
"""
GCP Cloud Run MCP Test - Tests all 9 MCP tools via Cloud Run API.

This script calls the deployed Cloud Run service instead of using yfinance directly,
avoiding rate limits and testing the production deployment.
"""

import asyncio
import json
import logging
import httpx
from datetime import datetime
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Cloud Run service URL (newly deployed with all 9 tools)
BASE_URL = "https://technical-analysis-mcp-1007181159506.us-central1.run.app"


async def test_all_cloud_run_tools():
    """Test all 9 MCP tools via Cloud Run HTTP API."""
    results = {}
    test_symbol = "AAPL"

    print("\n" + "=" * 60)
    print("CLOUD RUN MCP TOOLS TEST - ALL 9 TOOLS")
    print("=" * 60)
    print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Base URL: {BASE_URL}")
    print(f"Test symbol: {test_symbol}")
    print("=" * 60 + "\n")

    async with httpx.AsyncClient(timeout=60.0) as client:

        # Test 1: analyze_security
        print("[1/9] Testing /api/analyze (analyze_security)...")
        try:
            response = await client.post(
                f"{BASE_URL}/api/analyze",
                json={
                    "symbol": test_symbol,
                    "period": "3mo",
                    "include_ai": False,
                    "security_type": "auto"
                }
            )
            response.raise_for_status()
            result = response.json()

            # If async processing, wait for result
            if result.get("status") == "processing":
                print(f"   ⏳ Analysis started, waiting 10s...")
                await asyncio.sleep(10)
                # Get cached result
                response = await client.get(f"{BASE_URL}/api/signals/{test_symbol}")
                response.raise_for_status()
                result = response.json()

            results["analyze_security"] = {
                "status": "success",
                "total_signals": result.get("total_signals", 0),
            }
            print(f"   ✓ SUCCESS - {results['analyze_security']['total_signals']} signals")
        except Exception as e:
            results["analyze_security"] = {"status": "error", "error": str(e)}
            print(f"   ✗ ERROR: {e}")

        # Test 2: compare_securities
        print("[2/9] Testing /api/compare (compare_securities)...")
        try:
            response = await client.post(
                f"{BASE_URL}/api/compare",
                json={
                    "symbols": ["AAPL", "MSFT", "GOOGL"],
                    "period": "3mo"
                }
            )
            response.raise_for_status()
            result = response.json()
            winner = result.get("winner", {})
            results["compare_securities"] = {
                "status": "success",
                "winner": winner.get("symbol"),
                "total_compared": result.get("total_compared", 0),
            }
            print(f"   ✓ SUCCESS - Winner: {results['compare_securities']['winner']}")
        except Exception as e:
            results["compare_securities"] = {"status": "error", "error": str(e)}
            print(f"   ✗ ERROR: {e}")

        # Test 3: screen_securities
        print("[3/9] Testing /api/screen (screen_securities)...")
        try:
            # Note: screening requires pre-analyzed symbols
            response = await client.post(
                f"{BASE_URL}/api/screen",
                json={
                    "symbols": ["AAPL", "MSFT", "GOOGL", "TSLA", "NVDA"],
                    "criteria": {"rsi": {"min": 10, "max": 90}},
                    "limit": 5
                }
            )
            response.raise_for_status()
            result = response.json()
            results["screen_securities"] = {
                "status": "success",
                "cache_status": result.get("status", "unknown"),
            }
            print(f"   ✓ SUCCESS - Status: {results['screen_securities']['cache_status']}")
        except Exception as e:
            results["screen_securities"] = {"status": "error", "error": str(e)}
            print(f"   ✗ ERROR: {e}")

        # Test 4: get_trade_plan
        print("[4/9] Testing /api/trade-plan (get_trade_plan)...")
        try:
            response = await client.post(
                f"{BASE_URL}/api/trade-plan",
                json={
                    "symbol": test_symbol,
                    "period": "3mo"
                }
            )
            response.raise_for_status()
            result = response.json()
            results["get_trade_plan"] = {
                "status": "success",
                "has_trades": result.get("has_trades", False),
            }
            print(f"   ✓ SUCCESS - has_trades={results['get_trade_plan']['has_trades']}")
        except Exception as e:
            results["get_trade_plan"] = {"status": "error", "error": str(e)}
            print(f"   ✗ ERROR: {e}")

        # Test 5: scan_trades
        print("[5/9] Testing /api/scan (scan_trades)...")
        try:
            response = await client.post(
                f"{BASE_URL}/api/scan",
                json={
                    "universe": "etf_large_cap",
                    "max_results": 3
                }
            )
            response.raise_for_status()
            result = response.json()
            results["scan_trades"] = {
                "status": "success",
                "qualified_trades": len(result.get("qualified_trades", [])),
            }
            print(f"   ✓ SUCCESS - {results['scan_trades']['qualified_trades']} qualified trades")
        except Exception as e:
            results["scan_trades"] = {"status": "error", "error": str(e)}
            print(f"   ✗ ERROR: {e}")

        # Test 6: portfolio_risk
        print("[6/9] Testing /api/portfolio-risk (portfolio_risk)...")
        try:
            response = await client.post(
                f"{BASE_URL}/api/portfolio-risk",
                json={
                    "positions": [
                        {"symbol": "AAPL", "shares": 100, "entry_price": 150},
                        {"symbol": "MSFT", "shares": 50, "entry_price": 380},
                    ]
                }
            )
            response.raise_for_status()
            result = response.json()
            results["portfolio_risk"] = {
                "status": "success",
                "total_value": result.get("total_value", 0),
                "risk_level": result.get("overall_risk_level", "UNKNOWN"),
            }
            print(f"   ✓ SUCCESS - total_value=${results['portfolio_risk']['total_value']:,.2f}, risk={results['portfolio_risk']['risk_level']}")
        except Exception as e:
            results["portfolio_risk"] = {"status": "error", "error": str(e)}
            print(f"   ✗ ERROR: {e}")

        # Test 7: morning_brief
        print("[7/9] Testing /api/morning-brief (morning_brief)...")
        try:
            response = await client.post(
                f"{BASE_URL}/api/morning-brief",
                json={
                    "watchlist": ["AAPL", "MSFT", "NVDA"],
                    "market_region": "US"
                }
            )
            response.raise_for_status()
            result = response.json()
            results["morning_brief"] = {
                "status": "success",
                "signals_count": len(result.get("watchlist_signals", [])),
            }
            print(f"   ✓ SUCCESS - {results['morning_brief']['signals_count']} signals")
        except Exception as e:
            results["morning_brief"] = {"status": "error", "error": str(e)}
            print(f"   ✗ ERROR: {e}")

        # Test 8: analyze_fibonacci
        print("[8/9] Testing /api/fibonacci (analyze_fibonacci)...")
        try:
            response = await client.post(
                f"{BASE_URL}/api/fibonacci",
                json={
                    "symbol": test_symbol,
                    "period": "3mo",
                    "window": 150
                }
            )
            response.raise_for_status()
            result = response.json()
            results["analyze_fibonacci"] = {
                "status": "success",
                "levels": len(result.get("levels", [])),
                "signals": len(result.get("signals", [])),
            }
            print(f"   ✓ SUCCESS - {results['analyze_fibonacci']['levels']} levels, {results['analyze_fibonacci']['signals']} signals")
        except Exception as e:
            results["analyze_fibonacci"] = {"status": "error", "error": str(e)}
            print(f"   ✗ ERROR: {e}")

        # Test 9: options_risk_analysis
        print("[9/9] Testing /api/options-risk (options_risk_analysis)...")
        try:
            response = await client.post(
                f"{BASE_URL}/api/options-risk",
                json={
                    "symbol": test_symbol,
                    "option_type": "both",
                    "min_volume": 75
                }
            )
            response.raise_for_status()
            result = response.json()
            results["options_risk_analysis"] = {
                "status": "success",
                "dte": result.get("days_to_expiration", 0),
            }
            print(f"   ✓ SUCCESS - DTE={results['options_risk_analysis']['dte']}")
        except Exception as e:
            results["options_risk_analysis"] = {"status": "error", "error": str(e)}
            print(f"   ✗ ERROR: {e}")

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    success_count = sum(1 for r in results.values() if r.get("status") == "success")
    error_count = sum(1 for r in results.values() if r.get("status") == "error")
    total = len(results)

    print(f"Total tests: {total}")
    print(f"Successful: {success_count}")
    print(f"Errors: {error_count}")
    print(f"Success rate: {success_count / total * 100:.0f}%")
    print()

    for tool, result in results.items():
        status = "✓" if result.get("status") == "success" else "✗"
        print(f"  {status} {tool}")

    print("=" * 60)

    # Save results
    output_file = Path(__file__).parent / "nu-logs" / f"gcloud_mcp_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\nResults saved to: {output_file}")

    return results


if __name__ == "__main__":
    asyncio.run(test_all_cloud_run_tools())
