"""Tests for /api/morning-brief endpoint.

This test suite validates daily market briefing generation.
"""

import logging

import requests
import pytest

logger = logging.getLogger(__name__)


class TestMorningBrief:
    """Morning brief endpoint tests."""

    @pytest.mark.integration
    def test_morning_brief_default(self, api_base_url, successful_flows):
        """Test morning brief with default parameters."""
        endpoint = "/api/morning-brief"
        request_data = {}  # Use defaults
        
        logger.info("Testing morning brief with defaults")
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
            response={"market_status": result.get("market_status", {}).get("market_status")},
            status=response.status_code
        )
        
        # Validate response
        assert "timestamp" in result
        assert "market_status" in result
        assert "watchlist_signals" in result
        
        logger.info(f"✅ Morning brief generated")

    @pytest.mark.integration
    def test_morning_brief_with_watchlist(self, api_base_url, successful_flows):
        """Test morning brief with custom watchlist."""
        endpoint = "/api/morning-brief"
        watchlist = ["AAPL", "NVDA", "TSLA", "MU", "AMD"]
        request_data = {
            "watchlist": watchlist,
            "market_region": "US"
        }
        
        logger.info(f"Testing morning brief with watchlist: {watchlist}")
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
            request={"watchlist_size": len(watchlist)},
            response={"signals_generated": len(result.get("watchlist_signals", []))},
            status=response.status_code
        )
        
        # Should have signals for watchlist
        assert "watchlist_signals" in result
        logger.info(f"✅ Generated {len(result.get('watchlist_signals', []))} watchlist signals")

    @pytest.mark.integration
    def test_morning_brief_response_structure(self, api_base_url):
        """Test morning brief response structure."""
        endpoint = "/api/morning-brief"
        response = requests.post(
            f"{api_base_url}{endpoint}",
            json={"watchlist": ["SPY", "QQQ"]},
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 200
        result = response.json()
        
        # Validate structure
        assert "timestamp" in result
        assert "market_status" in result
        assert "economic_events" in result
        assert "watchlist_signals" in result
        assert "key_themes" in result
        
        # Market status should have required fields
        market_status = result.get("market_status", {})
        assert "market_status" in market_status
        
        logger.info(f"✅ Morning brief response structure valid")

    @pytest.mark.integration
    def test_morning_brief_market_region(self, api_base_url, successful_flows):
        """Test morning brief with different market regions."""
        endpoint = "/api/morning-brief"
        
        for region in ["US", "EU", "ASIA"]:
            request_data = {"market_region": region}
            
            logger.info(f"Testing morning brief for {region} region")
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
                request={"region": region},
                response={"region": region},
                status=response.status_code
            )
            
            logger.info(f"✅ {region} brief generated")
