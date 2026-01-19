"""Tests for /api/scan endpoint.

This test suite validates universe scanning for qualified trade setups.
"""

import logging

import requests
import pytest

logger = logging.getLogger(__name__)


class TestScan:
    """Scan endpoint tests."""

    @pytest.mark.integration
    def test_scan_sp500_default(self, api_base_url, successful_flows):
        """Test scanning SP500 universe with default parameters."""
        endpoint = "/api/scan"
        request_data = {"universe": "sp500", "max_results": 10}
        
        logger.info("Testing scan for SP500")
        response = requests.post(
            f"{api_base_url}{endpoint}",
            json=request_data,
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 200
        result = response.json()
        
        successful_flows["log_flow"](
            endpoint=endpoint,
            method="POST",
            request=request_data,
            response={"universe": result.get("universe"), "found": len(result.get("qualified_trades", []))},
            status=response.status_code
        )
        
        # Validate response
        assert "universe" in result
        assert result["universe"] == "sp500"
        assert "qualified_trades" in result
        assert "total_scanned" in result
        
        logger.info(f"✅ Scanned {result.get('total_scanned')} stocks, found {len(result.get('qualified_trades', []))} qualified")

    @pytest.mark.integration
    def test_scan_nasdaq100(self, api_base_url, successful_flows):
        """Test scanning NASDAQ100 universe."""
        endpoint = "/api/scan"
        request_data = {"universe": "nasdaq100", "max_results": 5}
        
        logger.info("Testing scan for NASDAQ100")
        response = requests.post(
            f"{api_base_url}{endpoint}",
            json=request_data,
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 200
        result = response.json()
        
        successful_flows["log_flow"](
            endpoint=endpoint,
            method="POST",
            request=request_data,
            response={"universe": "nasdaq100", "trades_found": len(result.get("qualified_trades", []))},
            status=response.status_code
        )
        
        assert result["universe"] == "nasdaq100"
        logger.info(f"✅ NASDAQ100 scan: {len(result.get('qualified_trades', []))} qualified trades")

    @pytest.mark.integration
    def test_scan_with_max_results(self, api_base_url, successful_flows):
        """Test scan respects max_results limit."""
        endpoint = "/api/scan"
        max_results = 3
        request_data = {"universe": "sp500", "max_results": max_results}
        
        logger.info(f"Testing scan with max_results={max_results}")
        response = requests.post(
            f"{api_base_url}{endpoint}",
            json=request_data,
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 200
        result = response.json()
        
        successful_flows["log_flow"](
            endpoint=endpoint,
            method="POST",
            request=request_data,
            response={"requested": max_results, "received": len(result.get("qualified_trades", []))},
            status=response.status_code
        )
        
        # Should return at most max_results
        assert len(result.get("qualified_trades", [])) <= max_results
        logger.info(f"✅ Scan respects max_results limit")

    @pytest.mark.integration
    def test_scan_response_structure(self, api_base_url):
        """Test scan response structure."""
        endpoint = "/api/scan"
        response = requests.post(
            f"{api_base_url}{endpoint}",
            json={"universe": "sp500", "max_results": 1},
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 200
        result = response.json()
        
        # Validate structure
        assert "universe" in result
        assert "total_scanned" in result
        assert "qualified_trades" in result
        assert "timestamp" in result
        assert "duration_seconds" in result
        
        # Each trade should have required fields
        for trade in result.get("qualified_trades", []):
            assert "symbol" in trade
            assert "entry_price" in trade or "price" in trade
        
        logger.info(f"✅ Scan response structure valid")
