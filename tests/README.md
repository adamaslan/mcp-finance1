# MCP Finance Backend - Test Suite

Comprehensive test suite with automatic logging of successful API flows.

## Overview

This test suite validates all 4 backend endpoints with **real financial data** and logs successful flows to JSON files for analysis.

### Endpoints Tested

1. **Trade Plan** (`POST /api/trade-plan`)
   - Generates risk-qualified trade plans for individual securities
   - Uses 150+ technical indicators and signals
   - Tests: MU, NVDA, SPY, error handling

2. **Scan** (`POST /api/scan`)
   - Scans universes for qualified trade setups
   - Tests: SP500, NASDAQ100, max results validation

3. **Portfolio Risk** (`POST /api/portfolio-risk`)
   - Assesses aggregate portfolio risk
   - Tests: Single/multiple positions, sector concentration

4. **Morning Brief** (`POST /api/morning-brief`)
   - Generates daily market briefing
   - Tests: Default, custom watchlist, different regions

## Setup

### Prerequisites

- Python 3.11+
- pytest
- requests
- Docker container running on port 8090

### Install Test Dependencies

```bash
cd mcp-finance1/tests
pip install pytest requests
```

### Start Backend Container

```bash
docker run -d -p 8090:8080 \
  -e GCP_PROJECT_ID=ttb-lang1 \
  -e BUCKET_NAME=technical-analysis-data \
  technical-analysis-api:latest
```

## Running Tests

### Run All Tests

```bash
cd tests
./run_tests.sh
```

### Run Specific Endpoint Tests

```bash
./run_tests.sh trade_plan       # Trade plan tests
./run_tests.sh scan             # Scan tests
./run_tests.sh portfolio_risk   # Portfolio risk tests
./run_tests.sh morning_brief    # Morning brief tests
```

### Run with Different API URL

```bash
API_BASE_URL=http://localhost:8080 ./run_tests.sh
```

### Using pytest Directly

```bash
# All integration tests
pytest -v -m integration

# Specific test file
pytest -v test_trade_plan.py

# Specific test class
pytest -v test_trade_plan.py::TestTradePlan

# Specific test method
pytest -v test_trade_plan.py::TestTradePlan::test_trade_plan_mu_with_6mo_data
```

## Test Results & Logging

### Test Run Log

Each test run creates a timestamped log file in `logs/`:

```
logs/
├── test_run_20260119_131445.log      # Complete test run log
├── flows_20260119_131445.json        # Successful API flows (JSON)
└── ...
```

### Log File Example

**test_run_TIMESTAMP.log:**
```
2026-01-19 13:14:45 - __main__ - INFO - ════════════════════════════════════════════════════════════
2026-01-19 13:14:45 - __main__ - INFO - 🚀 TEST SESSION STARTED
2026-01-19 13:14:45 - __main__ - INFO - 📝 Log file: /app/tests/logs/test_run_20260119_131445.log
2026-01-19 13:14:45 - conftest - INFO - ✅ POST /api/trade-plan -> 200
2026-01-19 13:14:45 - test_trade_plan - INFO - ✅ Trade plan response for MU: False tradeable
2026-01-19 13:14:45 - test_trade_plan - INFO - 📊 Suppression: VOLATILITY_TOO_HIGH
2026-01-19 13:14:45 - test_trade_plan - INFO - 📈 Metrics: ATR=17.22, ADX=43.9, Volatility=high
```

### Flows JSON

**flows_TIMESTAMP.json** - Structured record of all successful API calls:

```json
[
  {
    "timestamp": "2026-01-19T13:14:45.123456",
    "endpoint": "/api/trade-plan",
    "method": "POST",
    "status_code": 200,
    "request": {
      "symbol": "MU",
      "period": "6mo"
    },
    "response": {
      "has_trades": false,
      "suppression": {
        "code": "VOLATILITY_TOO_HIGH",
        "message": "Volatility regime HIGH (4.75% ATR) exceeds threshold (3.0%)"
      }
    },
    "success": true
  },
  ...
]
```

## Test Features

### Real Data Analysis

- ✅ Uses actual yfinance market data
- ✅ 150+ technical indicators calculated
- ✅ Real risk assessment and suppression logic
- ✅ No mock data or fake responses

### Automatic Logging

- ✅ Every successful API call logged
- ✅ Request/response captured
- ✅ Timestamped for reproducibility
- ✅ JSON format for analysis

### Comprehensive Coverage

- ✅ Happy path (valid requests)
- ✅ Error handling (invalid symbols, insufficient data)
- ✅ Edge cases (empty positions, extreme markets)
- ✅ Response validation (structure, fields)

## Understanding Test Output

### Successful Trade Plan

```
✅ Trade plan response for MU: False tradeable
📊 Suppression: VOLATILITY_TOO_HIGH
   Reason: Volatility regime HIGH (4.75% ATR) exceeds threshold (3.0%)
📈 Metrics: ATR=17.22, ADX=43.9, Volatility=high
⚠️  2 suppression reason(s)
```

This shows that MU was **correctly rejected** because:
1. Volatility too high (4.75% vs 3% limit)
2. Conflicting signals (2 bullish, 2 bearish)

### Successful Scan

```
✅ Scanned 500 stocks, found 3 qualified
✅ NASDAQ100 scan: 5 qualified trades
✅ Scan respects max_results limit
```

### Successful Portfolio Risk

```
✅ Portfolio value: $124,537.50, Max loss: $6,226.88
✅ Multi-position portfolio: $203,842.10
📊 Sectors: {'Technology': 60, 'Semiconductors': 40}
```

## Analyzing Test Results

### View Recent Test Log

```bash
cat logs/$(ls -t logs | head -1)
```

### Parse Flows JSON

```python
import json

with open('logs/flows_*.json') as f:
    flows = json.load(f)

# Count by endpoint
from collections import Counter
endpoints = Counter(f['endpoint'] for f in flows)
print(endpoints)

# Find failed flows
failures = [f for f in flows if not f['success']]
print(f"Failed flows: {len(failures)}")
```

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Backend Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Start backend
        run: |
          docker run -d -p 8090:8080 \
            -e GCP_PROJECT_ID=ttb-lang1 \
            technical-analysis-api:latest
          sleep 10
      
      - name: Run tests
        run: |
          cd tests
          python -m pip install pytest requests
          ./run_tests.sh
      
      - name: Upload logs
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: test-logs
          path: tests/logs/
```

## Troubleshooting

### Container Not Running

```bash
# Check if container is running
docker ps | grep technical-analysis-api

# Start container
docker run -d -p 8090:8080 technical-analysis-api:latest

# Check logs
docker logs <container_id>
```

### Tests Timeout

- Increase timeout in `conftest.py`
- Check if API is responding: `curl http://localhost:8090/`
- Check container logs for errors

### Import Errors

```bash
# Install missing dependencies
pip install pytest requests pytest-cov

# Verify pytest configuration
pytest --version
```

## Next Steps

- Integrate with GitHub Actions CI/CD
- Parse flows.json for analytics dashboards
- Add performance benchmarking tests
- Set up scheduled test runs

---

**Created:** 2026-01-19  
**Backend:** Python FastAPI with MCP Server  
**Test Framework:** pytest
