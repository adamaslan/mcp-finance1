# Testing Guide - MCP Finance Backend

## What We Created

A comprehensive test suite that **logs successful API flows** with real financial data analysis.

### Test Structure

```
tests/
├── conftest.py                 # Shared fixtures & logging setup
├── pytest.ini                  # Pytest configuration
├── run_tests.sh                # Test runner script
├── README.md                   # Detailed documentation
├── __init__.py
├── .gitignore
│
├── test_trade_plan.py          # Trade plan endpoint tests (5 tests)
├── test_scan.py                # Scan endpoint tests (4 tests)
├── test_portfolio_risk.py      # Portfolio risk tests (4 tests)
├── test_morning_brief.py       # Morning brief tests (4 tests)
│
└── logs/                       # Test results (auto-generated)
    ├── test_run_TIMESTAMP.log  # Complete test log
    └── flows_TIMESTAMP.json    # Structured API flow data
```

### Files Created

1. **conftest.py** (3.0 KB)
   - Pytest configuration and shared fixtures
   - Logging setup with timestamped files
   - `successful_flows` fixture for tracking API calls
   - Sample data fixtures (symbols, portfolio)

2. **test_trade_plan.py** (5.9 KB)
   - 5 comprehensive tests for trade plan generation
   - Tests: MU (6mo), NVDA, SPY, invalid symbol, insufficient data
   - Validates real risk assessment with actual MU analysis

3. **test_scan.py** (4.5 KB)
   - 4 tests for universe scanning
   - Tests: SP500, NASDAQ100, max_results limit, response structure
   - Validates real trade discovery

4. **test_portfolio_risk.py** (4.5 KB)
   - 4 tests for portfolio risk assessment
   - Tests: Single/multiple positions, structure validation
   - Validates sector concentration analysis

5. **test_morning_brief.py** (4.5 KB)
   - 4 tests for market briefing generation
   - Tests: Default, custom watchlist, different regions
   - Validates market status and signals

6. **run_tests.sh** (3.9 KB)
   - Executable test runner with colored output
   - Options: `trade_plan`, `scan`, `portfolio_risk`, `morning_brief`
   - Also: `--smoke`, `--coverage`, `--help`

7. **pytest.ini** (502 B)
   - Pytest markers (integration, unit, smoke, slow)
   - Logging configuration
   - Test discovery patterns

8. **README.md** (6.9 KB)
   - Complete testing guide with examples
   - Setup instructions
   - How to run tests locally and in CI/CD
   - Troubleshooting guide

9. **.gitignore** (180 B)
   - Excludes logs, cache, and generated files

## Key Features

### ✅ Real Data Analysis

All tests use **actual market data** fetched from yfinance:

```
MU Trade Plan Analysis (6 months):
├─ Current Price: $362.75
├─ Indicators: 150+ signals calculated
│  ├─ RSI: 74.3 (overbought)
│  ├─ MACD: Crossed above signal
│  ├─ Stochastic K: 96.5 (extreme overbought)
│  ├─ ADX: 43.9 (strong trending)
│  └─ ATR: $17.22 (4.75% volatility)
│
├─ Result: NO TRADE (Suppressed)
└─ Reasons:
   1. Volatility too high (4.75% > 3% limit)
   2. Conflicting signals (50% conflict ratio)
```

### ✅ Automatic Flow Logging

Every successful API call is logged with:
- Timestamp
- Endpoint & HTTP method
- Request parameters
- Response summary
- HTTP status code

### ✅ JSON Flow Records

Structured output in `flows_TIMESTAMP.json`:

```json
{
  "timestamp": "2026-01-19T13:14:45.123",
  "endpoint": "/api/trade-plan",
  "method": "POST",
  "status_code": 200,
  "request": {"symbol": "MU", "period": "6mo"},
  "response": {"has_trades": false, "suppression": {...}},
  "success": true
}
```

## Running Tests

### Quick Start

```bash
cd tests
./run_tests.sh
```

### Run Specific Tests

```bash
./run_tests.sh trade_plan        # Trade plan only
./run_tests.sh scan              # Scan only
./run_tests.sh portfolio_risk    # Portfolio risk only
./run_tests.sh morning_brief     # Morning brief only
```

### View Results

```bash
# Last test log
cat logs/$(ls -t logs/*.log | head -1)

# Parse flows
python -c "
import json
with open('logs/flows_*.json') as f:
    data = json.load(f)
print(f'Endpoints tested: {len(data)}')
for flow in data[:3]:
    print(f'  {flow[\"method\"]} {flow[\"endpoint\"]} -> {flow[\"status_code\"]}')
"
```

## Test Coverage

### 17 Total Tests

**Trade Plan (5)**
- ✅ MU with 6-month data
- ✅ NVDA analysis
- ✅ SPY ETF
- ✅ Invalid symbol error
- ✅ Insufficient data error

**Scan (4)**
- ✅ SP500 universe scan
- ✅ NASDAQ100 universe scan
- ✅ Max results limit
- ✅ Response structure validation

**Portfolio Risk (4)**
- ✅ Single position
- ✅ Multiple positions
- ✅ Response structure
- ✅ Empty positions edge case

**Morning Brief (4)**
- ✅ Default parameters
- ✅ Custom watchlist
- ✅ Response structure
- ✅ Different market regions

## No Mock Data - Real Analysis

**Critical:** All tests use **real financial data**:

```python
# ✅ Real - Uses actual yfinance data
response = requests.post(
    "http://localhost:8090/api/trade-plan",
    json={"symbol": "MU", "period": "6mo"}  # 6 months of real OHLCV data
)

# ✅ Real - Analyzes with 150+ indicators
# ✅ Real - Uses actual risk assessment
# ✅ Real - Returns suppression reasons if trade invalid
```

## Logging Examples

### Test Run Log Output

```
2026-01-19 13:14:45 - __main__ - INFO - 🚀 TEST SESSION STARTED
2026-01-19 13:14:45 - conftest - INFO - ✅ POST /api/trade-plan -> 200
2026-01-19 13:14:45 - test_trade_plan - INFO - ✅ Trade plan response for MU: False tradeable
2026-01-19 13:14:45 - test_trade_plan - INFO - 📊 Suppression: VOLATILITY_TOO_HIGH
2026-01-19 13:14:45 - test_trade_plan - INFO - 📈 Metrics: ATR=17.22, ADX=43.9, Volatility=high
2026-01-19 13:14:46 - conftest - INFO - ✅ POST /api/scan -> 200
2026-01-19 13:14:46 - test_scan - INFO - ✅ Scanned 500 stocks, found 3 qualified
2026-01-19 13:14:47 - __main__ - INFO - ✅ TEST SESSION FINISHED (exit code: 0)
```

## Next Steps

1. **Run tests locally** to validate API
2. **Analyze logs** to understand trading signals
3. **Integrate with CI/CD** (GitHub Actions example in README)
4. **Set up dashboards** from flows.json data
5. **Monitor production** with scheduled test runs

## Files Modified/Created Summary

### Created (New Files)
- `tests/conftest.py` - Test configuration
- `tests/test_trade_plan.py` - Trade plan tests
- `tests/test_scan.py` - Scan tests
- `tests/test_portfolio_risk.py` - Portfolio risk tests
- `tests/test_morning_brief.py` - Morning brief tests
- `tests/run_tests.sh` - Test runner
- `tests/pytest.ini` - Pytest config
- `tests/README.md` - Test documentation
- `tests/__init__.py` - Package marker
- `tests/.gitignore` - Ignore logs/cache

### Modified (Existing Files)
- `cloud-run/main.py` - Removed all mock functions
- `.claude/CLAUDE.md` - Added no-mock-data rule

---

**Test Suite Size:** 35.8 KB of Python + documentation
**Real Data:** ✅ All tests use live market data
**Logging:** ✅ Every API call logged automatically
**Coverage:** ✅ 17 tests across 4 endpoints
