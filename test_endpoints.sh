#!/bin/bash

# Integration Test Script for Cloud Run Endpoints
# Tests the 4 newly added endpoints: trade-plan, scan, portfolio-risk, morning-brief

set -e

# Configuration
API_URL="${1:-https://technical-analysis-api-1007181159506.us-central1.run.app}"
VERBOSE="${2:-false}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test counter
TESTS_RUN=0
TESTS_PASSED=0
TESTS_FAILED=0

# Helper functions
print_header() {
    echo -e "\n${BLUE}=== $1 ===${NC}\n"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
    ((TESTS_PASSED++))
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
    ((TESTS_FAILED++))
}

print_info() {
    echo -e "${YELLOW}ℹ️  $1${NC}"
}

test_endpoint() {
    local method=$1
    local endpoint=$2
    local data=$3
    local expected_code=$4
    local test_name=$5

    ((TESTS_RUN++))
    print_info "Test $TESTS_RUN: $test_name"

    if [ "$method" = "GET" ]; then
        response=$(curl -s -w "\n%{http_code}" "$API_URL$endpoint")
    else
        response=$(curl -s -w "\n%{http_code}" -X "$method" \
            -H "Content-Type: application/json" \
            -d "$data" \
            "$API_URL$endpoint")
    fi

    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')

    if [ "$http_code" = "$expected_code" ]; then
        print_success "$test_name (HTTP $http_code)"
        if [ "$VERBOSE" = "true" ]; then
            echo "Response: $body" | head -c 200
            echo "..."
        fi
    else
        print_error "$test_name - Expected HTTP $expected_code, got $http_code"
        if [ "$VERBOSE" = "true" ]; then
            echo "Response: $body"
        fi
    fi
}

# ============================================================================
# TESTS START
# ============================================================================

print_header "MCP Finance Backend Integration Tests"
echo "API URL: $API_URL"
echo "Verbose: $VERBOSE"

# Health check
print_header "1. Health Check"
test_endpoint "GET" "/" "" "200" "API health check"

# ============================================================================
# EXISTING ENDPOINTS (Should still work)
# ============================================================================

print_header "2. Existing Endpoints (Validation)"

# Test analyze (async endpoint)
print_info "Testing /api/analyze (async job submission)"
test_endpoint "POST" "/api/analyze" \
    '{"symbol":"AAPL","period":"1mo"}' \
    "200" \
    "Analyze endpoint returns job status"

# Test compare (sync endpoint)
print_info "Testing /api/compare (requires previous analysis)"
test_endpoint "POST" "/api/compare" \
    '{"symbols":["AAPL","MSFT"]}' \
    "404" \
    "Compare endpoint works (404 expected - no prior analysis)"

# ============================================================================
# NEW ENDPOINTS (The 4 missing endpoints we added)
# ============================================================================

print_header "3. New Endpoints (Trade Plan, Scan, Portfolio Risk, Morning Brief)"

# Test trade-plan endpoint
print_info "Testing /api/trade-plan"
test_endpoint "POST" "/api/trade-plan" \
    '{"symbol":"AAPL","period":"1mo"}' \
    "200" \
    "Trade plan endpoint returns results"

# Test scan endpoint
print_info "Testing /api/scan"
test_endpoint "POST" "/api/scan" \
    '{"universe":"sp500","max_results":5}' \
    "200" \
    "Scan endpoint returns qualified trades"

# Test portfolio-risk endpoint
print_info "Testing /api/portfolio-risk"
test_endpoint "POST" "/api/portfolio-risk" \
    '{"positions":[{"symbol":"AAPL","shares":100,"entry_price":150}]}' \
    "200" \
    "Portfolio risk endpoint returns metrics"

# Test morning-brief endpoint
print_info "Testing /api/morning-brief"
test_endpoint "POST" "/api/morning-brief" \
    '{"watchlist":["AAPL","MSFT","GOOGL"],"market_region":"US"}' \
    "200" \
    "Morning brief endpoint returns briefing"

# ============================================================================
# ERROR HANDLING
# ============================================================================

print_header "4. Error Handling"

# Invalid symbol for trade-plan
print_info "Testing error handling with invalid symbol"
test_endpoint "POST" "/api/trade-plan" \
    '{"symbol":"INVALIDZZZ","period":"1mo"}' \
    "500" \
    "Invalid symbol returns error"

# Invalid universe for scan
print_info "Testing error handling with invalid universe"
test_endpoint "POST" "/api/scan" \
    '{"universe":"invalid_universe","max_results":5}' \
    "200" \
    "Invalid universe handled gracefully"

# ============================================================================
# VALIDATION CHECKS
# ============================================================================

print_header "5. Response Structure Validation"

# Check trade-plan response structure
print_info "Validating trade-plan response structure"
response=$(curl -s -X POST \
    -H "Content-Type: application/json" \
    -d '{"symbol":"AAPL"}' \
    "$API_URL/api/trade-plan")

if echo "$response" | grep -q '"symbol"'; then
    print_success "Trade plan response contains symbol field"
else
    print_error "Trade plan response missing symbol field"
fi

if echo "$response" | grep -q '"timeframe"'; then
    print_success "Trade plan response contains timeframe field"
else
    print_error "Trade plan response missing timeframe field"
fi

# Check scan response structure
print_info "Validating scan response structure"
response=$(curl -s -X POST \
    -H "Content-Type: application/json" \
    -d '{"universe":"sp500","max_results":3}' \
    "$API_URL/api/scan")

if echo "$response" | grep -q '"universe"'; then
    print_success "Scan response contains universe field"
else
    print_error "Scan response missing universe field"
fi

if echo "$response" | grep -q '"qualified_trades"'; then
    print_success "Scan response contains qualified_trades array"
else
    print_error "Scan response missing qualified_trades array"
fi

# Check portfolio-risk response structure
print_info "Validating portfolio-risk response structure"
response=$(curl -s -X POST \
    -H "Content-Type: application/json" \
    -d '{"positions":[{"symbol":"AAPL","shares":100,"entry_price":150}]}' \
    "$API_URL/api/portfolio-risk")

if echo "$response" | grep -q '"total_value"'; then
    print_success "Portfolio risk response contains total_value field"
else
    print_error "Portfolio risk response missing total_value field"
fi

if echo "$response" | grep -q '"positions"'; then
    print_success "Portfolio risk response contains positions array"
else
    print_error "Portfolio risk response missing positions array"
fi

# Check morning-brief response structure
print_info "Validating morning-brief response structure"
response=$(curl -s -X POST \
    -H "Content-Type: application/json" \
    -d '{"watchlist":["AAPL"],"market_region":"US"}' \
    "$API_URL/api/morning-brief")

if echo "$response" | grep -q '"market_status"'; then
    print_success "Morning brief response contains market_status"
else
    print_error "Morning brief response missing market_status"
fi

if echo "$response" | grep -q '"watchlist_signals"'; then
    print_success "Morning brief response contains watchlist_signals"
else
    print_error "Morning brief response missing watchlist_signals"
fi

# ============================================================================
# SUMMARY
# ============================================================================

print_header "Test Summary"
echo "Tests Run:    $TESTS_RUN"
echo -e "Tests Passed: ${GREEN}$TESTS_PASSED${NC}"
echo -e "Tests Failed: ${RED}$TESTS_FAILED${NC}"

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "\n${GREEN}🎉 All tests passed!${NC}\n"
    exit 0
else
    echo -e "\n${RED}⚠️  $TESTS_FAILED test(s) failed${NC}\n"
    exit 1
fi
