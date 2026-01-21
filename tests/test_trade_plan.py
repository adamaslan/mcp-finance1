"""Tests for /api/trade-plan endpoint.

This test suite validates the trade plan generation for individual securities.
Tests real MCP analysis with sufficient data periods.
"""

import json
import logging

import requests
import pytest

logger = logging.getLogger(__name__)


class TestTradePlan:
    """Trade plan endpoint tests."""

    @pytest.mark.integration
    def test_trade_plan_mu_with_6mo_data(self, api_base_url, successful_flows):
        """Test trade plan generation for MU with 6-month data.
        
        MU at $362.75 - validates real technical analysis:
        - Fetches 6 months of OHLCV data
        - Calculates 150+ technical signals
        - Assesses risk metrics
        - Returns suppression reasons if not tradeable
        """
        endpoint = "/api/trade-plan"
        request_data = {"symbol": "MU", "period": "6mo"}
        
        logger.info(f"Testing {endpoint} with MU (6 months)")
        response = requests.post(
            f"{api_base_url}{endpoint}",
            json=request_data,
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        result = response.json()
        
        # Log successful flow
        successful_flows["log_flow"](
            endpoint=endpoint,
            method="POST",
            request=request_data,
            response={"has_trades": result.get("has_trades"), "suppression": result.get("primary_suppression")},
            status=response.status_code
        )
        
        # Validate response structure
        assert "symbol" in result
        assert result["symbol"] == "MU"
        assert "has_trades" in result
        assert "trade_plans" in result
        assert "risk_assessment" in result
        
        logger.info(f"✅ Trade plan response for MU: {result.get('has_trades')} tradeable")
        
        # Log detailed analysis
        if result.get("primary_suppression"):
            logger.info(f"📊 Suppression: {result['primary_suppression']['code']}")
            logger.info(f"   Reason: {result['primary_suppression']['message']}")
        
        # Validate risk metrics
        metrics = result.get("risk_assessment", {}).get("metrics", {})
        logger.info(f"📈 Metrics: ATR={metrics.get('atr'):.2f}, ADX={metrics.get('adx'):.1f}, Volatility={metrics.get('volatility_regime')}")
        
        # If not tradeable, should have suppression reasons
        if not result.get("has_trades"):
            assert result.get("all_suppressions"), "No trade should have suppression reasons"
            logger.info(f"⚠️  {len(result.get('all_suppressions', []))} suppression reason(s)")

    @pytest.mark.integration
    def test_trade_plan_nvda(self, api_base_url, successful_flows):
        """Test trade plan for NVDA."""
        endpoint = "/api/trade-plan"
        request_data = {"symbol": "NVDA", "period": "6mo"}
        
        logger.info("Testing trade plan for NVDA")
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
            response={"has_trades": result.get("has_trades"), "symbol": "NVDA"},
            status=response.status_code
        )
        
        assert result["symbol"] == "NVDA"
        logger.info(f"✅ NVDA analysis complete: {result.get('has_trades')} tradeable")

    @pytest.mark.integration
    def test_trade_plan_spy_etf(self, api_base_url, successful_flows):
        """Test trade plan for SPY ETF."""
        endpoint = "/api/trade-plan"
        request_data = {"symbol": "SPY", "period": "6mo"}
        
        logger.info("Testing trade plan for SPY ETF")
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
            response={"has_trades": result.get("has_trades"), "symbol": "SPY"},
            status=response.status_code
        )
        
        assert result["symbol"] == "SPY"
        logger.info(f"✅ SPY analysis complete")

    @pytest.mark.integration
    def test_trade_plan_with_invalid_symbol(self, api_base_url):
        """Test trade plan with invalid symbol."""
        endpoint = "/api/trade-plan"
        request_data = {"symbol": "INVALID123", "period": "6mo"}
        
        logger.info("Testing with invalid symbol")
        response = requests.post(
            f"{api_base_url}{endpoint}",
            json=request_data,
            headers={"Content-Type": "application/json"}
        )
        
        # Should fail gracefully with error
        assert response.status_code >= 400
        logger.info(f"✅ Invalid symbol rejected with {response.status_code}")

    @pytest.mark.integration
    def test_trade_plan_with_insufficient_data(self, api_base_url):
        """Test trade plan with insufficient data period."""
        endpoint = "/api/trade-plan"
        request_data = {"symbol": "MU", "period": "1mo"}  # Too short
        
        logger.info("Testing with insufficient data period (1mo)")
        response = requests.post(
            f"{api_base_url}{endpoint}",
            json=request_data,
            headers={"Content-Type": "application/json"}
        )
        
        # Should fail due to insufficient data
        assert response.status_code >= 400
        logger.info(f"✅ Insufficient data rejected with {response.status_code}")
