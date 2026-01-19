"""Shared test configuration and fixtures."""

import json
import logging
import os
from datetime import datetime
from pathlib import Path

import pytest


# Setup logging for tests
LOG_DIR = Path(__file__).parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
LOG_FILE = LOG_DIR / f"test_run_{TIMESTAMP}.log"

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


@pytest.fixture
def api_base_url():
    """Get API base URL from environment or use default."""
    return os.environ.get("API_BASE_URL", "http://localhost:8090")


@pytest.fixture
def test_results_logger():
    """Logger for capturing successful test flows."""
    logger = logging.getLogger("test_results")
    return logger


@pytest.fixture
def successful_flows():
    """Track successful API flows."""
    flows = []
    
    def log_flow(endpoint: str, method: str, request: dict, response: dict, status: int):
        flow = {
            "timestamp": datetime.now().isoformat(),
            "endpoint": endpoint,
            "method": method,
            "status_code": status,
            "request": request,
            "response": response,
            "success": 200 <= status < 300
        }
        flows.append(flow)
        logger.info(f"✅ {method} {endpoint} -> {status}")
        return flow
    
    def save_flows(filename: str = None):
        if not filename:
            filename = f"flows_{TIMESTAMP}.json"
        filepath = LOG_DIR / filename
        with open(filepath, 'w') as f:
            json.dump(flows, f, indent=2)
        logger.info(f"📊 Saved {len(flows)} successful flows to {filepath}")
        return filepath
    
    yield {
        "log_flow": log_flow,
        "save_flows": save_flows,
        "flows": flows
    }


@pytest.fixture
def sample_symbols():
    """Sample symbols for testing."""
    return {
        "single": "MU",
        "tech": ["NVDA", "AMD", "TSLA"],
        "mixed": ["MU", "SPY", "QQQ"],
        "crypto": ["BTC-USD", "ETH-USD"]
    }


@pytest.fixture
def sample_portfolio():
    """Sample portfolio positions for risk testing."""
    return [
        {"symbol": "MU", "shares": 100, "entry_price": 362.75},
        {"symbol": "NVDA", "shares": 50, "entry_price": 875.50},
        {"symbol": "AMD", "shares": 75, "entry_price": 185.25}
    ]


def pytest_sessionstart(session):
    """Log test session start."""
    logger.info("=" * 80)
    logger.info("🚀 TEST SESSION STARTED")
    logger.info(f"📝 Log file: {LOG_FILE}")
    logger.info("=" * 80)


def pytest_sessionfinish(session, exitstatus):
    """Log test session end."""
    logger.info("=" * 80)
    logger.info(f"✅ TEST SESSION FINISHED (exit code: {exitstatus})")
    logger.info(f"📁 All logs saved to: {LOG_DIR}")
    logger.info("=" * 80)
