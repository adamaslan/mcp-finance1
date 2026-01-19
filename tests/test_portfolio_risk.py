"""Tests for /api/portfolio-risk endpoint.

This test suite validates portfolio risk assessment.
"""

import logging

import requests
import pytest

logger = logging.getLogger(__name__)


class TestPortfolioRisk:
    """Portfolio risk endpoint tests."""

    @pytest.mark.integration
    def test_portfolio_risk_single_position(self, api_base_url, successful_flows):
        """Test portfolio risk for single position."""
        endpoint = "/api/portfolio-risk"
        request_data = {
            "positions": [
                {"symbol": "MU", "shares": 100, "entry_price": 362.75}
            ]
        }
        
        logger.info("Testing portfolio risk with single position")
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
            request={"positions": 1},
            response={"total_value": result.get("total_value"), "risk_level": result.get("overall_risk_level")},
            status=response.status_code
        )
        
        # Validate response
        assert "total_value" in result
        assert "total_max_loss" in result
        assert "overall_risk_level" in result
        assert "positions" in result
        
        logger.info(f"✅ Portfolio value: ${result.get('total_value'):,.2f}, Max loss: ${result.get('total_max_loss'):,.2f}")

    @pytest.mark.integration
    def test_portfolio_risk_multiple_positions(self, api_base_url, successful_flows, sample_portfolio):
        """Test portfolio risk with multiple positions."""
        endpoint = "/api/portfolio-risk"
        request_data = {"positions": sample_portfolio}
        
        logger.info(f"Testing portfolio risk with {len(sample_portfolio)} positions")
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
            request={"positions": len(sample_portfolio)},
            response={
                "total_value": result.get("total_value"),
                "positions": len(result.get("positions", [])),
                "risk_level": result.get("overall_risk_level")
            },
            status=response.status_code
        )
        
        assert len(result.get("positions", [])) == len(sample_portfolio)
        assert "sector_concentration" in result
        
        logger.info(f"✅ Multi-position portfolio: ${result.get('total_value'):,.2f}")
        logger.info(f"📊 Sectors: {result.get('sector_concentration', {})}")

    @pytest.mark.integration
    def test_portfolio_risk_response_structure(self, api_base_url):
        """Test portfolio risk response structure."""
        endpoint = "/api/portfolio-risk"
        response = requests.post(
            f"{api_base_url}{endpoint}",
            json={
                "positions": [
                    {"symbol": "AAPL", "shares": 50, "entry_price": 195.30}
                ]
            },
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 200
        result = response.json()
        
        # Validate required fields
        assert "total_value" in result
        assert "total_max_loss" in result
        assert "risk_percent_of_portfolio" in result
        assert "overall_risk_level" in result
        assert result["overall_risk_level"] in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
        
        logger.info(f"✅ Portfolio risk response structure valid")

    @pytest.mark.integration
    def test_portfolio_risk_empty_positions(self, api_base_url):
        """Test portfolio risk with empty positions."""
        endpoint = "/api/portfolio-risk"
        response = requests.post(
            f"{api_base_url}{endpoint}",
            json={"positions": []},
            headers={"Content-Type": "application/json"}
        )
        
        # Should handle empty gracefully
        assert response.status_code in [200, 400]
        logger.info(f"✅ Empty positions handled with {response.status_code}")
