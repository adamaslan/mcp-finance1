#!/bin/bash
"""Test runner for MCP Finance Backend.

Usage:
    ./run_tests.sh                    # Run all integration tests
    ./run_tests.sh trade_plan         # Run only trade plan tests
    ./run_tests.sh --smoke            # Quick smoke tests
    ./run_tests.sh --coverage         # Generate coverage report
"""

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Default API URL
API_URL="${API_BASE_URL:-http://localhost:8090}"

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║        MCP Finance Backend - Test Suite                   ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${YELLOW}🔗 API URL: ${API_URL}${NC}"
echo ""

# Check if API is running
if ! curl -s "${API_URL}/" > /dev/null; then
    echo -e "${YELLOW}⚠️  Warning: API not responding at ${API_URL}${NC}"
    echo -e "${YELLOW}   Make sure Docker container is running:${NC}"
    echo -e "${YELLOW}   docker run -d -p 8090:8080 technical-analysis-api:latest${NC}"
    echo ""
fi

# Parse arguments
TEST_FILTER=""
PYTEST_ARGS="-v --tb=short -m integration"

case "${1:-}" in
    trade_plan)
        TEST_FILTER="test_trade_plan"
        echo -e "${GREEN}🧪 Running trade plan tests...${NC}"
        ;;
    scan)
        TEST_FILTER="test_scan"
        echo -e "${GREEN}🧪 Running scan tests...${NC}"
        ;;
    portfolio_risk)
        TEST_FILTER="test_portfolio_risk"
        echo -e "${GREEN}🧪 Running portfolio risk tests...${NC}"
        ;;
    morning_brief)
        TEST_FILTER="test_morning_brief"
        echo -e "${GREEN}🧪 Running morning brief tests...${NC}"
        ;;
    --smoke)
        echo -e "${GREEN}🚬 Running smoke tests...${NC}"
        PYTEST_ARGS="-v --tb=short -m smoke"
        ;;
    --coverage)
        echo -e "${GREEN}📊 Running tests with coverage...${NC}"
        PYTEST_ARGS="--cov=. --cov-report=html -v"
        ;;
    --help)
        echo "Usage: ./run_tests.sh [option]"
        echo ""
        echo "Options:"
        echo "  trade_plan        Run trade plan tests"
        echo "  scan              Run scan tests"
        echo "  portfolio_risk    Run portfolio risk tests"
        echo "  morning_brief     Run morning brief tests"
        echo "  --smoke           Run quick smoke tests"
        echo "  --coverage        Generate coverage report"
        echo "  --help            Show this help message"
        exit 0
        ;;
    *)
        echo -e "${GREEN}🧪 Running all integration tests...${NC}"
        ;;
esac

echo ""

# Run tests
export API_BASE_URL="${API_URL}"

if [ -z "$TEST_FILTER" ]; then
    python -m pytest ${PYTEST_ARGS} .
else
    python -m pytest ${PYTEST_ARGS} -k "${TEST_FILTER}" .
fi

EXIT_CODE=$?

echo ""
echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
if [ $EXIT_CODE -eq 0 ]; then
    echo -e "${BLUE}║          ✅ All tests passed!                             ║${NC}"
else
    echo -e "${BLUE}║          ❌ Some tests failed                             ║${NC}"
fi
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${YELLOW}📁 Test logs and flows saved to: $(pwd)/logs/$(ls -t logs | head -1)${NC}"
echo ""

exit $EXIT_CODE
