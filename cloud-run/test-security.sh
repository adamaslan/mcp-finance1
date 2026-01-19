#!/bin/bash

# MCP Finance Backend - Docker Security Test Script
# This script verifies that the container runs securely as a non-root user

set -e

IMAGE_NAME="${1:-mcp-finance-backend:latest}"

echo "========================================"
echo "Docker Security Test Suite"
echo "========================================"
echo "Testing image: $IMAGE_NAME"
echo ""

# Color codes for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Test counter
PASS=0
FAIL=0

# Function to run a test
run_test() {
    local test_name="$1"
    local command="$2"
    local expected="$3"

    echo -n "Testing: $test_name... "

    result=$(eval "$command" 2>&1)

    if echo "$result" | grep -q "$expected"; then
        echo -e "${GREEN}✅ PASS${NC}"
        ((PASS++))
        return 0
    else
        echo -e "${RED}❌ FAIL${NC}"
        echo "  Expected: $expected"
        echo "  Got: $result"
        ((FAIL++))
        return 1
    fi
}

# Test 1: User is not root
run_test "Container runs as non-root user" \
    "docker run --rm $IMAGE_NAME whoami" \
    "mambauser"

# Test 2: UID is 1000 (not 0)
run_test "User ID is 1000 (not root)" \
    "docker run --rm $IMAGE_NAME id -u" \
    "1000"

# Test 3: GID is 1000
run_test "Group ID is 1000" \
    "docker run --rm $IMAGE_NAME id -g" \
    "1000"

# Test 4: Files are owned by mambauser
run_test "Application files owned by mambauser" \
    "docker run --rm $IMAGE_NAME ls -l /app/main.py | awk '{print \$3}'" \
    "mambauser"

# Test 5: Cannot write to root filesystem (with read-only flag)
echo -n "Testing: Read-only filesystem protection... "
if docker run --rm --read-only $IMAGE_NAME touch /test 2>&1 | grep -q "Read-only file system"; then
    echo -e "${GREEN}✅ PASS${NC}"
    ((PASS++))
else
    echo -e "${RED}❌ FAIL${NC}"
    ((FAIL++))
fi

# Test 6: Python is installed and working
run_test "Python is installed" \
    "docker run --rm $IMAGE_NAME python --version" \
    "Python 3.11"

# Test 7: FastAPI is installed
run_test "FastAPI is installed" \
    "docker run --rm $IMAGE_NAME python -c 'import fastapi; print(fastapi.__version__)'" \
    "[0-9]"

# Test 8: Required GCP packages are installed
run_test "GCP Firestore package installed" \
    "docker run --rm $IMAGE_NAME python -c 'import google.cloud.firestore; print(\"ok\")'" \
    "ok"

# Test 9: Health check is configured
run_test "Health check is configured" \
    "docker inspect --format='{{.Config.Healthcheck.Test}}' $IMAGE_NAME" \
    "CMD"

# Test 10: Port 8080 is exposed
run_test "Port 8080 is exposed" \
    "docker inspect --format='{{.Config.ExposedPorts}}' $IMAGE_NAME" \
    "8080"

echo ""
echo "========================================"
echo "Test Results"
echo "========================================"
echo -e "Passed: ${GREEN}$PASS${NC}"
echo -e "Failed: ${RED}$FAIL${NC}"
echo ""

if [ $FAIL -eq 0 ]; then
    echo -e "${GREEN}✅ All security tests passed!${NC}"
    echo "The container is secure and ready for production."
    exit 0
else
    echo -e "${RED}❌ Some tests failed.${NC}"
    echo "Please review the failures above and fix them before deploying."
    exit 1
fi
