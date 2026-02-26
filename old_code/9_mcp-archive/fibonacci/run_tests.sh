#!/bin/bash

# Comprehensive Test Suite for Fibonacci Optimizations
# Runs all tests and generates a summary report

set -e

echo "=========================================="
echo "Fibonacci Analysis Test Suite"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test directories
TEST_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$TEST_DIR/../.." && pwd)"

echo "Test Directory: $TEST_DIR"
echo "Project Root: $PROJECT_ROOT"
echo ""

# Create results directory
RESULTS_DIR="$TEST_DIR/results"
mkdir -p "$RESULTS_DIR"
RESULTS_FILE="$RESULTS_DIR/test_results_$(date +%Y%m%d_%H%M%S).txt"

{
    echo "Fibonacci Analysis Test Results"
    echo "Generated: $(date)"
    echo "=========================================="
    echo ""

    # Test 1: Adaptive Tolerance Tests
    echo "1. ADAPTIVE TOLERANCE TESTS"
    echo "============================"
    cd "$PROJECT_ROOT"

    if python -m pytest "$TEST_DIR/tests/test_adaptive_tolerance.py" -v --tb=short; then
        echo -e "${GREEN}✓ Adaptive Tolerance Tests: PASSED${NC}"
        echo "  - Tolerance calculation verified"
        echo "  - Edge cases handled"
        echo "  - Bounds validation passed"
    else
        echo -e "${RED}✗ Adaptive Tolerance Tests: FAILED${NC}"
    fi
    echo ""

    # Test 2: Database Schema Tests
    echo "2. DATABASE SCHEMA TESTS"
    echo "========================="

    if python -m pytest "$TEST_DIR/tests/test_database_schema.py" -v --tb=short; then
        echo -e "${GREEN}✓ Database Schema Tests: PASSED${NC}"
        echo "  - Schema compilation verified"
        echo "  - Signal recording tested"
        echo "  - Performance calculations validated"
    else
        echo -e "${RED}✗ Database Schema Tests: FAILED${NC}"
    fi
    echo ""

    # Test 3: API Integration Tests
    echo "3. API INTEGRATION TESTS"
    echo "========================"

    if python -m pytest "$TEST_DIR/tests/test_api_integration.py" -v --tb=short; then
        echo -e "${GREEN}✓ API Integration Tests: PASSED${NC}"
        echo "  - Endpoint responses verified"
        echo "  - Tier gating validated"
        echo "  - Error handling tested"
    else
        echo -e "${RED}✗ API Integration Tests: FAILED${NC}"
    fi
    echo ""

    # Test 4: Dashboard UI Tests
    echo "4. DASHBOARD UI TESTS"
    echo "====================="

    if python -m pytest "$TEST_DIR/tests/test_dashboard_ui.py" -v --tb=short; then
        echo -e "${GREEN}✓ Dashboard UI Tests: PASSED${NC}"
        echo "  - Component rendering verified"
        echo "  - Layout responsiveness tested"
        echo "  - User interactions validated"
    else
        echo -e "${RED}✗ Dashboard UI Tests: FAILED${NC}"
    fi
    echo ""

    # Summary
    echo "=========================================="
    echo "TEST EXECUTION SUMMARY"
    echo "=========================================="
    echo "All test modules executed"
    echo "Review results above for any failures"
    echo ""
    echo "Test artifacts saved to: $RESULTS_DIR"

} | tee "$RESULTS_FILE"

echo ""
echo "Test results saved to: $RESULTS_FILE"
echo ""
echo "Next Steps:"
echo "1. Review any failed tests above"
echo "2. Check test logs for detailed errors"
echo "3. Fix issues and rerun tests"
echo "4. Ensure all components are working correctly"
