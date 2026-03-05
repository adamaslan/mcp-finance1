#!/usr/bin/env python3

"""
Test GCP Cache Workflow - Validates all 7 layers

Tests:
- L0: Secret Manager (if configured)
- L1: Memorystore/Redis
- L2a: Firestore
- L2b: Cloud Storage
- L3: BigQuery
- L4: Cloud Tasks
- L5: API providers (quota tracking)

Usage: python test_gcp_cache_workflow.py
"""

import asyncio
import json
import os
import sys
import time
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.technical_analysis_mcp.cache.gcp_cache_manager import GCPCacheManager, CacheLayer


class CacheWorkflowTest:
    """Test all cache layers."""

    def __init__(self):
        self.manager = GCPCacheManager()
        self.test_symbol = "AAPL"
        self.test_key = f"test:price:{self.test_symbol}"
        self.test_data = {
            "symbol": self.test_symbol,
            "price": 172.50,
            "timestamp": datetime.utcnow().isoformat()
        }
        self.passed = 0
        self.failed = 0

    def log_test(self, name: str, passed: bool, message: str = ""):
        """Log test result."""
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {name}")
        if message:
            print(f"     {message}")

        if passed:
            self.passed += 1
        else:
            self.failed += 1

    # ========================================================================
    # Layer 0: Secret Manager
    # ========================================================================

    def test_layer_0_secrets(self):
        """Test Secret Manager."""
        print("\n" + "=" * 70)
        print("Testing L0: Secret Manager")
        print("=" * 70)

        if not self.manager.layers_available.get(CacheLayer.SECRET_MANAGER):
            self.log_test("Secret Manager availability", False, "Not available (may be expected)")
            return

        # Try to get a test secret
        try:
            # This will fail if secret doesn't exist, which is OK
            secret = self.manager.get_secret("test-api-key")
            self.log_test("Get secret", secret is not None, f"Retrieved secret" if secret else "Secret not found")
        except Exception as e:
            self.log_test("Get secret", False, str(e))

    # ========================================================================
    # Layer 1: Redis
    # ========================================================================

    def test_layer_1_redis(self):
        """Test Memorystore/Redis."""
        print("\n" + "=" * 70)
        print("Testing L1: Memorystore/Redis")
        print("=" * 70)

        if not self.manager.layers_available.get(CacheLayer.REDIS):
            self.log_test("Redis availability", False, "Not available")
            return

        # Test SET
        set_result = self.manager.set_in_redis(self.test_key, self.test_data, ttl=60)
        self.log_test("SET in Redis", set_result)

        # Test GET
        time.sleep(0.5)  # Small delay
        get_result = self.manager.get_from_redis(self.test_key)
        self.log_test("GET from Redis", get_result is not None)

        if get_result:
            matches = get_result.get("symbol") == self.test_symbol
            self.log_test("Data integrity", matches, f"Symbol: {get_result.get('symbol')}")

    # ========================================================================
    # Layer 2a: Firestore
    # ========================================================================

    async def test_layer_2a_firestore(self):
        """Test Firestore."""
        print("\n" + "=" * 70)
        print("Testing L2a: Firestore")
        print("=" * 70)

        if not self.manager.layers_available.get(CacheLayer.FIRESTORE):
            self.log_test("Firestore availability", False, "Not available")
            return

        # Test SET
        try:
            set_result = await self.manager.set_in_firestore(
                "test_cache",
                self.test_key,
                self.test_data,
                ttl=60
            )
            self.log_test("SET in Firestore", set_result)

            # Small delay for async write
            await asyncio.sleep(1)

            # Test GET
            get_result = await self.manager.get_from_firestore("test_cache", self.test_key)
            self.log_test("GET from Firestore", get_result is not None)

            if get_result and "result" in get_result:
                matches = get_result["result"].get("symbol") == self.test_symbol
                self.log_test("Data integrity", matches)

        except Exception as e:
            self.log_test("Firestore operations", False, str(e))

    # ========================================================================
    # Layer 2b: Cloud Storage
    # ========================================================================

    def test_layer_2b_cloud_storage(self):
        """Test Cloud Storage."""
        print("\n" + "=" * 70)
        print("Testing L2b: Cloud Storage")
        print("=" * 70)

        if not self.manager.layers_available.get(CacheLayer.CLOUD_STORAGE):
            self.log_test("Cloud Storage availability", False, "Not available")
            return

        # Test SET
        try:
            set_result = self.manager.set_in_cloud_storage(
                self.test_symbol,
                self.test_data,
                period="test"
            )
            self.log_test("SET in Cloud Storage", set_result)

            # Small delay
            time.sleep(1)

            # Test GET
            get_result = self.manager.get_from_cloud_storage(self.test_symbol, period="test")
            self.log_test("GET from Cloud Storage", get_result is not None)

            if get_result:
                matches = get_result.get("symbol") == self.test_symbol
                self.log_test("Data integrity", matches)

        except Exception as e:
            self.log_test("Cloud Storage operations", False, str(e))

    # ========================================================================
    # Layer 3: BigQuery
    # ========================================================================

    def test_layer_3_bigquery(self):
        """Test BigQuery."""
        print("\n" + "=" * 70)
        print("Testing L3: BigQuery")
        print("=" * 70)

        if not self.manager.layers_available.get(CacheLayer.BIGQUERY):
            self.log_test("BigQuery availability", False, "Not available")
            return

        # Try to query a symbol (may not exist, which is OK)
        try:
            result = self.manager.get_from_bigquery(self.test_symbol)

            if result is None:
                self.log_test("Query BigQuery", True, "No data (materialized view may not exist yet)")
            else:
                self.log_test("Query BigQuery", True, f"Found {len(result)} fields")
                self.log_test("Data integrity", "symbol" in result or "trade_date" in result)

        except Exception as e:
            # This is expected if materialized views don't exist yet
            self.log_test("Query BigQuery", False, str(e))

    # ========================================================================
    # Layer 4: Cloud Tasks
    # ========================================================================

    def test_layer_4_cloud_tasks(self):
        """Test Cloud Tasks."""
        print("\n" + "=" * 70)
        print("Testing L4: Cloud Tasks")
        print("=" * 70)

        if not self.manager.layers_available.get(CacheLayer.CLOUD_TASKS):
            self.log_test("Cloud Tasks availability", False, "Not available")
            return

        # Test scheduling a refresh task
        try:
            result = self.manager.schedule_cache_refresh(
                symbol=self.test_symbol,
                tool_name="test_tool",
                delay_seconds=5
            )
            self.log_test("Schedule cache refresh", result)

        except Exception as e:
            self.log_test("Schedule cache refresh", False, str(e))

    # ========================================================================
    # API Quota Tracking
    # ========================================================================

    def test_api_quota_tracking(self):
        """Test quota tracking."""
        print("\n" + "=" * 70)
        print("Testing API Quota Tracking (Datastore)")
        print("=" * 70)

        try:
            # Check quota
            quota = self.manager.get_api_quota("alpha-vantage")
            self.log_test("Get API quota", True, f"Remaining: {quota}")

            # Decrement quota
            if quota > 0:
                result = self.manager.decrement_api_quota("alpha-vantage")
                self.log_test("Decrement quota", result)

                # Check again
                new_quota = self.manager.get_api_quota("alpha-vantage")
                self.log_test("Verify quota decremented", new_quota < quota, f"Old: {quota}, New: {new_quota}")

        except Exception as e:
            self.log_test("Quota tracking", False, str(e))

    # ========================================================================
    # Unified Get/Set (Full 7-Layer Workflow)
    # ========================================================================

    async def test_unified_workflow(self):
        """Test complete get/set workflow using all layers."""
        print("\n" + "=" * 70)
        print("Testing Unified Get/Set Workflow (All Layers)")
        print("=" * 70)

        try:
            # Write to all layers
            layers_written = await self.manager.set(
                self.test_key,
                self.test_data,
                symbol=self.test_symbol,
                ttl=60
            )
            self.log_test("Write to all layers", layers_written > 0, f"Wrote to {layers_written} layers")

            # Wait a bit
            await asyncio.sleep(1)

            # Read from cache (should hit L1 first)
            hit = await self.manager.get(
                self.test_key,
                symbol=self.test_symbol,
                tool_name="test_tool"
            )

            if hit:
                self.log_test("Read from cache", True, f"Hit layer: {hit.layer.name}")
                self.log_test("Data retrieved", hit.data is not None)
            else:
                self.log_test("Read from cache", False, "No data found")

        except Exception as e:
            self.log_test("Unified workflow", False, str(e))

    # ========================================================================
    # Health Check
    # ========================================================================

    def test_health_check(self):
        """Test health check status."""
        print("\n" + "=" * 70)
        print("Health Check")
        print("=" * 70)

        status = self.manager.health_check()
        available = sum(status.values())
        total = len(status)

        print(f"Layers available: {available}/{total}")
        for layer, is_available in status.items():
            symbol = "✓" if is_available else "✗"
            print(f"  {symbol} {layer.name} ({layer.value})")

        self.manager.log_status()

    # ========================================================================
    # Main Test Runner
    # ========================================================================

    async def run_all_tests(self):
        """Run all tests."""
        print("\n")
        print("╔" + "═" * 68 + "╗")
        print("║" + " " * 15 + "GCP Cache Workflow Test Suite" + " " * 24 + "║")
        print("╚" + "═" * 68 + "╝")

        # Health check first
        self.test_health_check()

        # Run all tests
        self.test_layer_0_secrets()
        self.test_layer_1_redis()
        await self.test_layer_2a_firestore()
        self.test_layer_2b_cloud_storage()
        self.test_layer_3_bigquery()
        self.test_layer_4_cloud_tasks()
        self.test_api_quota_tracking()
        await self.test_unified_workflow()

        # Summary
        print("\n" + "=" * 70)
        print("Test Summary")
        print("=" * 70)
        total = self.passed + self.failed
        percentage = (self.passed / total * 100) if total > 0 else 0
        print(f"Passed: {self.passed}/{total} ({percentage:.0f}%)")

        if self.failed > 0:
            print(f"Failed: {self.failed}")
            print("\n⚠️  Some tests failed. Check logs above for details.")
            return 1
        else:
            print("\n✓ All tests passed!")
            return 0


async def main():
    """Main entry point."""
    tester = CacheWorkflowTest()
    exit_code = await tester.run_all_tests()
    sys.exit(exit_code)


if __name__ == "__main__":
    asyncio.run(main())
