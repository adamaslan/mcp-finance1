# MCP Finance - Data Periods Configuration Guide

**Last Updated**: January 28, 2026
**Version**: 1.1 - **Added: 15m, 1h, 4h intraday periods**

---

## Table of Contents

1. [Overview](#overview)
2. [Quick Reference Table](#quick-reference-table)
3. [Tool-by-Tool Configuration](#tool-by-tool-configuration)
4. [Global Configuration](#global-configuration)
5. [How to Change Periods](#how-to-change-periods)
6. [Troubleshooting](#troubleshooting)

---

## Overview

The MCP Finance backend uses **9 different tools** for technical analysis, risk assessment, and options analysis. Each tool has different data period requirements based on the technical indicators it calculates.

### What is a "Period"?

A **period** (or **timeframe**) defines how much historical price data is fetched from yfinance for analysis:

**Intraday Periods** (New - for day traders):
- `15m` = 15 minutes of data (60 candles = 4 hours of trading)
- `1h` = 1 hour of data (1 trading day ~8 hours)
- `4h` = 4 hours of data (5 trading days = 1 week)

**Daily & Longer Periods**:
- `1d` = 1 day of data (1 trading day)
- `5d` = 5 days of data (1 trading week)
- `1mo` = 1 month (~21 trading days)
- `3mo` = 3 months (~63 trading days)
- `6mo` = 6 months (~126 trading days)
- `1y` = 1 year (~252 trading days)
- `2y`, `5y`, `10y` = Multi-year periods

### Why Periods Matter

**Technical indicators need minimum data points to calculate accurately:**

- **RSI (14-period)**: Needs 14+ data points (minimum `1mo`)
- **MACD (12/26/9)**: Needs 26+ data points (minimum `1mo`)
- **50-day SMA**: Needs 50+ data points (minimum `3mo`)
- **200-day SMA**: Needs 200+ data points (minimum `1y`)

**Using too short a period results in**:
- Missing indicators (e.g., 50-day SMA not calculated)
- Fewer signals detected
- Less accurate technical analysis
- Portfolio risk calculations failing

### NEW: Intraday Trading Support (15m, 1h, 4h)

✨ **NEW in v1.1**: Intraday periods now available for day traders and scalpers!

**When to use intraday periods:**
- `15m` = **Scalping** (rapid trades, 15 min - 1 hour holding periods)
- `1h` = **Day Trading** (hold within a trading day, 1-4 hour trades)
- `4h` = **Swing Trading** (1-5 day trades, intermediate timeframe)

**Intraday period advantages:**
- ✅ Real-time signals for active traders
- ✅ Faster trend identification
- ✅ More entry/exit opportunities
- ✅ Better for momentum strategies
- ✅ Reduced overnight gap risk

**Intraday period limitations:**
- ⚠️ Higher noise in signals (false breakouts more common)
- ⚠️ Moving averages less reliable (need more candles for stability)
- ⚠️ Risk: Whipsaws and quick reversals
- ⚠️ Requires active monitoring (not for swing traders)

---

## Quick Reference Table

| # | Tool Name | Current Default | Recommended | Configurable? | Supports Intraday? |
|---|-----------|----------------|-------------|---------------|--------------------|
| 1 | analyze_security | `1mo` | `3mo` - `6mo` | ✅ Yes (parameter) | ✅ 15m, 1h, 4h |
| 2 | compare_securities | `1mo` | `3mo` - `6mo` | ✅ Yes (parameter)* | ✅ 15m, 1h, 4h |
| 3 | screen_securities | `1mo` | `3mo` - `6mo` | ✅ Yes (parameter)* | ✅ 15m, 1h, 4h |
| 4 | get_trade_plan | `1mo` | `3mo` - `6mo` | ✅ Yes (parameter) | ✅ 15m, 1h, 4h |
| 5 | scan_trades | `1mo` | `3mo` - `6mo` | ✅ Yes (parameter)* | ✅ 15m, 1h, 4h |
| 6 | portfolio_risk | `1mo` | `6mo` - `1y` | ✅ Yes (parameter)* | ✅ 15m, 1h, 4h |
| 7 | morning_brief | `1mo` | `3mo` - `6mo` | ✅ Yes (parameter)* | ✅ 15m, 1h, 4h |
| 8 | analyze_fibonacci | `1mo` | `3mo` - `6mo` | ✅ Yes (parameter) | ✅ 15m, 1h, 4h |
| 9 | options_risk_analysis | N/A | Any (current) | N/A | N/A |

**Legend:**
- `*` = Newly added parameter support (v1.1)
- ✅ All tools now support 15m, 1h, 4h intraday periods!

---

## Tool-by-Tool Configuration

### 1. analyze_security

**Purpose**: Analyze a single security with technical indicators and signals.

**Current Default**: `1mo` (21 trading days)
**Recommended**: `3mo` to `6mo` (63-126 trading days)
**Configurable**: ✅ Yes - via function parameter

#### Current Configuration

**File**: `src/technical_analysis_mcp/server.py`
**Line**: 386

```python
async def analyze_security(
    symbol: str,
    period: str = DEFAULT_PERIOD,  # DEFAULT_PERIOD = "1mo"
    use_ai: bool = False,
) -> dict[str, Any]:
```

#### How to Change

**Option 1: Change when calling the function** (Recommended)

```python
# In your client code or test script
result = await analyze_security(
    symbol="AAPL",
    period="3mo",  # Change to 3mo, 6mo, or 1y
    use_ai=False,
)
```

**Option 2: Change global default**

Edit `src/technical_analysis_mcp/config.py` line 16:

```python
# Before
DEFAULT_PERIOD: Final[str] = "1mo"

# After
DEFAULT_PERIOD: Final[str] = "3mo"
```

#### Technical Requirements

- **Minimum**: `1mo` (21 days) for basic indicators
- **Recommended**: `3mo` (63 days) for 50-day SMA
- **Optimal**: `6mo` (126 days) for more stable signals
- **Advanced**: `1y` (252 days) for 200-day SMA

---

### 2. compare_securities

**Purpose**: Compare multiple securities and rank them by a metric (signals, strength).

**Current Default**: `1mo` (hardcoded in function)
**Recommended**: `3mo` to `6mo`
**Configurable**: ⚠️ Requires code modification

#### Current Configuration

**File**: `src/technical_analysis_mcp/server.py`
**Line**: 487

```python
for symbol in symbols:
    try:
        analysis = await analyze_security(symbol, period="1mo")  # HARDCODED
```

#### How to Change

**Step 1**: Edit `server.py` line 487

```python
# Before
analysis = await analyze_security(symbol, period="1mo")

# After - Option A: Use global default
analysis = await analyze_security(symbol, period=DEFAULT_PERIOD)

# After - Option B: Hardcode new value
analysis = await analyze_security(symbol, period="3mo")
```

**Step 2**: Add period parameter to function signature (Optional - for flexibility)

```python
async def compare_securities(
    symbols: list[str],
    metric: str = "signals",
    period: str = DEFAULT_PERIOD,  # ADD THIS
) -> dict[str, Any]:
    """Compare securities."""
    # ...
    for symbol in symbols:
        try:
            analysis = await analyze_security(symbol, period=period)  # USE IT
```

**Step 3**: Update MCP tool registration (if you added parameter)

Find the tool registration around line 180-200 and add period to schema:

```python
{
    "name": "compare_securities",
    "description": "Compare multiple securities...",
    "inputSchema": {
        "type": "object",
        "properties": {
            "symbols": {...},
            "metric": {...},
            "period": {  # ADD THIS
                "type": "string",
                "default": "3mo",
                "description": "Time period (1mo, 3mo, 6mo, 1y)",
            },
        },
    },
}
```

#### Known Issues

⚠️ **BUG**: This tool crashes with `'NoneType' object has no attribute 'get'` when all symbols fail to analyze.

**Fix Required**: Add null check before accessing winner attributes (see [FINAL_MCP_TEST_REPORT.md](FINAL_MCP_TEST_REPORT.md) line 263-288).

---

### 3. screen_securities

**Purpose**: Screen a universe of stocks for specific technical criteria.

**Current Default**: `1mo` (hardcoded in function)
**Recommended**: `3mo` to `6mo`
**Configurable**: ⚠️ Requires code modification

#### Current Configuration

**File**: `src/technical_analysis_mcp/server.py`
**Line**: 543

```python
for symbol in symbols:
    try:
        analysis = await analyze_security(symbol, period="1mo")  # HARDCODED
```

#### How to Change

**Step 1**: Edit `server.py` line 543

```python
# Before
analysis = await analyze_security(symbol, period="1mo")

# After - Option A: Use global default
analysis = await analyze_security(symbol, period=DEFAULT_PERIOD)

# After - Option B: Hardcode new value
analysis = await analyze_security(symbol, period="3mo")
```

**Step 2**: Add period parameter to function signature (Optional)

```python
async def screen_securities(
    universe: str,
    criteria: dict[str, Any],
    limit: int = 20,
    period: str = DEFAULT_PERIOD,  # ADD THIS
) -> dict[str, Any]:
    """Screen securities."""
    # ...
    for symbol in symbols:
        try:
            analysis = await analyze_security(symbol, period=period)  # USE IT
```

**Step 3**: Update MCP tool registration (if you added parameter)

Add period to the tool schema (around line 220-250).

#### Performance Notes

- Screening scans **hundreds of symbols** (e.g., S&P 500 has 500 stocks)
- Using `6mo` or `1y` periods significantly increases execution time
- Consider using `3mo` as a balance between accuracy and performance

---

### 4. get_trade_plan

**Purpose**: Generate risk-qualified trade plans with stop-loss, targets, and R:R ratios.

**Current Default**: `1mo`
**Recommended**: `3mo` to `6mo`
**Configurable**: ✅ Yes - via function parameter

#### Current Configuration

**File**: `src/technical_analysis_mcp/server.py`
**Line**: 606

```python
async def get_trade_plan(
    symbol: str,
    period: str = DEFAULT_PERIOD,  # DEFAULT_PERIOD = "1mo"
) -> dict[str, Any]:
```

#### How to Change

**Option 1: Change when calling the function** (Recommended)

```python
result = await get_trade_plan(
    symbol="AAPL",
    period="3mo",  # Change to 3mo, 6mo, or 1y
)
```

**Option 2: Change global default**

Edit `src/technical_analysis_mcp/config.py` line 16 (same as analyze_security).

#### Why Longer Periods Help

The trade plan tool:
- Calculates ATR (Average True Range) for stop-loss placement
- Needs stable trend indicators (ADX, moving averages)
- Assesses volatility regimes

**With 1mo**: May miss longer-term trends, ATR less stable
**With 3mo+**: More reliable stop-loss levels, better trend context

---

### 5. scan_trades

**Purpose**: Scan an entire universe (NASDAQ-100, Russell 2000) for qualified trades.

**Current Default**: `1mo` (hardcoded in function)
**Recommended**: `3mo` to `6mo`
**Configurable**: ⚠️ Requires code modification

#### Current Configuration

**File**: `src/technical_analysis_mcp/server.py`
**Line**: 681

```python
scanner = TradeScanner(max_concurrent=10)
result = await scanner.scan_universe(universe, max_results, period="1mo")  # HARDCODED
```

#### How to Change

**Step 1**: Edit `server.py` line 681

```python
# Before
result = await scanner.scan_universe(universe, max_results, period="1mo")

# After
result = await scanner.scan_universe(universe, max_results, period="3mo")
```

**Step 2**: Add period parameter to function signature (Optional)

```python
async def scan_trades(
    universe: str,
    max_results: int = 10,
    period: str = DEFAULT_PERIOD,  # ADD THIS
) -> dict[str, Any]:
    """Scan universe for trades."""
    # ...
    result = await scanner.scan_universe(universe, max_results, period=period)
```

**Step 3**: Update MCP tool registration (if you added parameter)

Add period to the tool schema.

#### Performance Considerations

- Scans **100+ symbols** concurrently
- Using longer periods increases memory usage
- `3mo` is a good balance for production use

---

### 6. portfolio_risk

**Purpose**: Assess aggregate risk across portfolio positions.

**Current Default**: N/A (calls analyze_security internally with default period)
**Recommended**: `6mo` to `1y` (needs longer periods for accurate risk assessment)
**Configurable**: ⚠️ Requires code modification

#### Current Configuration

**File**: `src/technical_analysis_mcp/server.py`
**Line**: 693

```python
async def portfolio_risk(
    positions: list[dict[str, Any]],
) -> dict[str, Any]:
    """Assess portfolio risk."""
    assessor = PortfolioRiskAssessor()
    result = await assessor.assess(positions)  # Uses nested calls with default period
    return result
```

#### How This Tool Works

The `portfolio_risk` tool:
1. Calls `PortfolioRiskAssessor.assess()` in `src/technical_analysis_mcp/portfolio.py`
2. Which internally calls `analyze_security()` for each position
3. Those calls use `DEFAULT_PERIOD` (currently `1mo`)

#### How to Change

**Option 1: Pass period through the chain** (Recommended)

**Step 1**: Add period parameter to `portfolio_risk` function:

```python
async def portfolio_risk(
    positions: list[dict[str, Any]],
    period: str = "6mo",  # ADD THIS with higher default
) -> dict[str, Any]:
    """Assess portfolio risk."""
    assessor = PortfolioRiskAssessor()
    result = await assessor.assess(positions, period=period)  # PASS IT
    return result
```

**Step 2**: Update `PortfolioRiskAssessor.assess()` in `portfolio.py`:

```python
# In src/technical_analysis_mcp/portfolio.py
async def assess(
    self,
    positions: list[dict[str, Any]],
    period: str = "6mo",  # ADD THIS
) -> dict[str, Any]:
    """Assess portfolio risk."""
    # ...
    for position in positions:
        analysis = await analyze_security(position["symbol"], period=period)  # USE IT
```

**Step 3**: Update MCP tool registration to include period parameter.

**Option 2: Change global default** (Simple but affects all tools)

Edit `config.py` line 16 to change `DEFAULT_PERIOD` from `"1mo"` to `"6mo"`.

⚠️ **Warning**: This affects ALL tools that use `DEFAULT_PERIOD`.

#### Why Portfolio Risk Needs Longer Periods

- Portfolio risk assessment needs stable volatility measures (ATR)
- Risk correlations require longer price history
- Stop-loss calculations are more reliable with 6mo+ data

**Test Results** (from FINAL_MCP_TEST_REPORT.md):
- With `1mo`: Limited assessment, many positions couldn't be fully evaluated
- Recommended: `6mo` to `1y` for comprehensive portfolio analysis

---

### 7. morning_brief

**Purpose**: Generate daily market briefing with signals and market conditions.

**Current Default**: N/A (calls analyze_security internally with default period)
**Recommended**: `3mo` to `6mo`
**Configurable**: ⚠️ Requires code modification

#### Current Configuration

**File**: `src/technical_analysis_mcp/server.py`
**Line**: 723

```python
async def morning_brief(
    watchlist: list[str] | None = None,
    market_region: str = "US",
) -> dict[str, Any]:
    """Generate morning briefing."""
    generator = MorningBriefGenerator()
    result = await generator.generate(watchlist, market_region)
    return result
```

#### How This Tool Works

The `morning_brief` tool:
1. Calls `MorningBriefGenerator.generate()` in `src/technical_analysis_mcp/briefing.py`
2. Which internally calls `analyze_security()` for each watchlist symbol
3. Those calls use `DEFAULT_PERIOD` (currently `1mo`)

#### How to Change

**Option 1: Pass period through the chain**

**Step 1**: Add period parameter to `morning_brief` function:

```python
async def morning_brief(
    watchlist: list[str] | None = None,
    market_region: str = "US",
    period: str = "3mo",  # ADD THIS
) -> dict[str, Any]:
    """Generate morning briefing."""
    generator = MorningBriefGenerator()
    result = await generator.generate(watchlist, market_region, period=period)  # PASS IT
    return result
```

**Step 2**: Update `MorningBriefGenerator.generate()` in `briefing.py` to accept and use period parameter.

**Step 3**: Update MCP tool registration.

**Option 2: Change global default**

Edit `config.py` to change `DEFAULT_PERIOD` (affects all tools).

#### Why Morning Brief Needs Longer Periods

- Needs reliable signals for daily trading decisions
- Market condition assessment requires trend context
- Theme detection (bullish/bearish sectors) needs stable indicators

---

### 8. analyze_fibonacci

**Purpose**: Analyze Fibonacci retracement/extension levels and detect signals.

**Current Default**: `1mo`
**Recommended**: `3mo` to `6mo`
**Configurable**: ✅ Yes - via function parameter

#### Current Configuration

**File**: `src/technical_analysis_mcp/server.py`
**Line**: 755

```python
async def analyze_fibonacci(
    symbol: str,
    period: str = "1mo",  # EXPLICIT DEFAULT
    window: int = 50,
) -> dict[str, Any]:
```

#### How to Change

**Option 1: Change when calling the function** (Recommended)

```python
result = await analyze_fibonacci(
    symbol="AAPL",
    period="3mo",  # Change to 3mo, 6mo, or 1y
    window=50,
)
```

**Option 2: Change function default**

Edit `server.py` line 755:

```python
# Before
async def analyze_fibonacci(
    symbol: str,
    period: str = "1mo",
    window: int = 50,
) -> dict[str, Any]:

# After
async def analyze_fibonacci(
    symbol: str,
    period: str = "3mo",  # CHANGE THIS
    window: int = 50,
) -> dict[str, Any]:
```

#### Known Issues

⚠️ **BUG**: Array broadcasting error in multi-timeframe analysis (see FINAL_MCP_TEST_REPORT.md line 290).

**Status**: Needs debugging in weekly resampling logic (lines 900-920 in server.py).

#### Window Parameter

The `window` parameter controls how many bars to look back for swing high/low detection:

- `window=50`: Looks back 50 bars for swing points
- Requires `period` to have at least `window + 20` bars
- **Minimum period for window=50**: `3mo` (63 trading days)

**Relationship**:
- `period="1mo"` (21 days) + `window=50` = ❌ **Not enough data**
- `period="3mo"` (63 days) + `window=50` = ✅ **Works**
- `period="6mo"` (126 days) + `window=50` = ✅ **Optimal**

---

### 9. options_risk_analysis

**Purpose**: Analyze options chain risk metrics (IV, put/call ratio, volume, open interest).

**Current Default**: N/A (uses current options chain data only)
**Recommended**: Any (doesn't use historical price period)
**Configurable**: N/A (no period parameter)

#### Current Configuration

**File**: `src/technical_analysis_mcp/server.py`
**Line**: 1226

```python
async def options_risk_analysis(
    symbol: str,
    expiration_date: str | None = None,
    option_type: str = "both",
    min_volume: int = 10,
) -> dict[str, Any]:
    """Analyze options chain."""
    # Fetches CURRENT options chain data from yfinance
    # No historical period needed
```

#### Why This Tool is Different

**Options data is CURRENT SNAPSHOT data**, not historical:

- Fetches today's options chain (strikes, IV, volume, OI)
- Uses `ticker.option_chain(expiration_date)` from yfinance
- No period parameter needed
- **Fastest tool** - no historical data fetching

#### Parameters You Can Configure

Instead of `period`, this tool has:

1. **expiration_date** (`str | None`):
   - Specific expiration date (e.g., "2026-02-21")
   - `None` = uses nearest expiration

2. **option_type** (`str`):
   - `"both"`: Analyze calls and puts (default)
   - `"call"`: Calls only
   - `"put"`: Puts only

3. **min_volume** (`int`):
   - Minimum volume to consider an option "liquid"
   - Default: 10 contracts
   - Higher = fewer but more liquid options

#### Example Usage

```python
# Analyze AAPL options expiring Feb 21, 2026
result = await options_risk_analysis(
    symbol="AAPL",
    expiration_date="2026-02-21",
    option_type="both",
    min_volume=50,  # Only highly liquid options
)
```

#### Performance Notes

From test results (FINAL_MCP_TEST_REPORT.md line 116):

✅ **BEST PERFORMING TOOL**
- 10.7 KB of detailed options data in seconds
- Put/Call Ratio analysis
- IV analysis (implied volatility)
- Volume and Open Interest breakdown
- **Ready for production immediately**

---

## Global Configuration

All period defaults are centralized in `src/technical_analysis_mcp/config.py`:

### config.py - Line 16

```python
# Data Fetching
DEFAULT_PERIOD: Final[str] = "1mo"
VALID_PERIODS: Final[tuple[str, ...]] = (
    "1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max"
)
```

### How to Change Global Default

**Step 1**: Edit `config.py`

```python
# Before
DEFAULT_PERIOD: Final[str] = "1mo"

# After - Recommended
DEFAULT_PERIOD: Final[str] = "3mo"
```

**Step 2**: Restart MCP server

```bash
# Deactivate and reactivate environment
mamba deactivate
mamba activate fin-ai1

# Restart server (if running as service)
# Or simply re-run your test script
```

### Impact of Changing Global Default

✅ **Affected tools** (use `DEFAULT_PERIOD`):
1. `analyze_security` (if period not specified)
2. `get_trade_plan` (if period not specified)
3. `analyze_fibonacci` (if period not specified)

⚠️ **NOT affected** (use hardcoded values):
1. `compare_securities` (hardcoded `"1mo"`)
2. `screen_securities` (hardcoded `"1mo"`)
3. `scan_trades` (hardcoded `"1mo"`)
4. `portfolio_risk` (uses nested calls)
5. `morning_brief` (uses nested calls)

❌ **Not applicable**:
1. `options_risk_analysis` (no period concept)

---

## How to Change Periods

### Method 1: Change When Calling (Recommended)

**For tools with period parameter** (`analyze_security`, `get_trade_plan`, `analyze_fibonacci`):

```python
# Python client code
from src.technical_analysis_mcp.server import analyze_security

result = await analyze_security(
    symbol="AAPL",
    period="3mo",  # SPECIFY HERE
    use_ai=False,
)
```

**Advantages**:
- ✅ No code modification needed
- ✅ Flexible - different periods for different calls
- ✅ Safe - doesn't affect other tools

**Disadvantages**:
- ❌ Must remember to specify every time
- ❌ Doesn't work for tools without period parameter

---

### Method 2: Change Global Default

**Edit** `src/technical_analysis_mcp/config.py` line 16:

```python
DEFAULT_PERIOD: Final[str] = "3mo"  # Changed from "1mo"
```

**Advantages**:
- ✅ Simple - one line change
- ✅ Affects all tools using `DEFAULT_PERIOD`
- ✅ Good for consistent baseline

**Disadvantages**:
- ❌ Doesn't affect tools with hardcoded periods
- ❌ All tools get same period (less flexibility)

---

### Method 3: Modify Individual Tool (Advanced)

**For tools with hardcoded periods** (`compare_securities`, `screen_securities`, `scan_trades`):

**Step 1**: Find the hardcoded period in `server.py`

Example - `compare_securities` line 487:

```python
analysis = await analyze_security(symbol, period="1mo")  # HARDCODED
```

**Step 2**: Change the hardcoded value

```python
analysis = await analyze_security(symbol, period="3mo")  # CHANGED
```

**Step 3** (Optional): Add period parameter for flexibility

```python
async def compare_securities(
    symbols: list[str],
    metric: str = "signals",
    period: str = "3mo",  # ADD THIS
) -> dict[str, Any]:
    # ...
    analysis = await analyze_security(symbol, period=period)  # USE IT
```

**Step 4**: Update MCP tool schema registration

Add period to the tool's JSON schema (find tool registration in `server.py`).

**Advantages**:
- ✅ Most flexible - per-tool control
- ✅ Can add parameter for runtime configuration

**Disadvantages**:
- ❌ Requires code modification
- ❌ Need to update MCP schema
- ❌ More testing required

---

### Method 4: Environment Variable (Future Enhancement)

**Currently NOT implemented**, but recommended for production:

```bash
# .env file
MCP_DEFAULT_PERIOD=3mo
MCP_PORTFOLIO_PERIOD=6mo
MCP_FIBONACCI_PERIOD=6mo
```

```python
# config.py (proposed change)
import os
DEFAULT_PERIOD: Final[str] = os.getenv("MCP_DEFAULT_PERIOD", "1mo")
```

**Advantages**:
- ✅ No code changes needed
- ✅ Easy to change per environment (dev/staging/prod)
- ✅ Follows 12-factor app principles

**Disadvantages**:
- ❌ Not currently implemented
- ❌ Requires code refactoring

---

## Troubleshooting

### Issue 1: "Insufficient data points" Error

**Symptom**:
```
InsufficientDataError: Symbol AAPL has only 21 data points, need at least 50
```

**Cause**: Period too short for the indicators being calculated.

**Solution**: Increase the period parameter:

```python
# Before (fails)
result = await analyze_security("AAPL", period="1mo")  # Only 21 days

# After (works)
result = await analyze_security("AAPL", period="3mo")  # 63 days
```

---

### Issue 2: No Signals Detected

**Symptom**:
```json
{
  "summary": {
    "total_signals": 0,
    "avg_score": 0
  }
}
```

**Cause**: Insufficient data for technical indicators (e.g., 50-day SMA missing).

**Solution**: Use longer period:

```python
# For 50-day SMA signals
result = await analyze_security("AAPL", period="3mo")

# For 200-day SMA signals
result = await analyze_security("AAPL", period="1y")
```

---

### Issue 3: Screen/Scan Returns Zero Results

**Symptom**:
```json
{
  "matches": [],
  "scanned": 250,
  "matched": 0
}
```

**Possible Causes**:
1. Criteria too strict
2. Period too short (missing indicators)
3. Current market conditions don't match criteria

**Solutions**:

**A. Increase period** (if using hardcoded `1mo`):

Edit `screen_securities` in `server.py` line 543:

```python
# Change from
analysis = await analyze_security(symbol, period="1mo")

# To
analysis = await analyze_security(symbol, period="3mo")
```

**B. Relax screening criteria**:

```python
result = await screen_securities(
    universe="sp500",
    criteria={
        "rsi": {"min": 20, "max": 80},  # Wider range
        "min_score": 40,  # Lower threshold
        "min_bullish": 5,  # Fewer signals required
    },
)
```

---

### Issue 4: Portfolio Risk Shows "0% Risk"

**Symptom**:
```json
{
  "total_value": 0.00,
  "risk_level": "LOW",
  "risk_percent": 0
}
```

**Cause**: Individual positions couldn't be assessed due to insufficient data period.

**Solution**: Increase period for portfolio risk (requires code change):

See [Method 3](#method-3-modify-individual-tool-advanced) for `portfolio_risk`.

**Recommended**: Use `6mo` to `1y` for portfolio risk assessment.

---

### Issue 5: Fibonacci Analysis Fails

**Symptom**:
```
operands could not be broadcast together with shapes (28,) (29,)
```

**Cause**: Known bug in weekly resampling logic (see FINAL_MCP_TEST_REPORT.md).

**Status**: Bug fix required in `server.py` lines 900-920.

**Workaround**: Use `period="3mo"` or longer (doesn't fix bug but may reduce frequency).

---

### Issue 6: Compare Securities Crashes

**Symptom**:
```
'NoneType' object has no attribute 'get'
```

**Cause**: All symbols failed to analyze (e.g., invalid symbols or data period issues).

**Solution**:

**A. Fix the bug** (see FINAL_MCP_TEST_REPORT.md line 263-288):

```python
# In compare_securities function
winner = results[0] if results else None
return {
    "comparison": results,
    "metric": metric,
    "winner": {
        "symbol": winner.get("symbol") if winner else None,
        "score": winner.get("score") if winner else 0,
    } if winner else None,
}
```

**B. Ensure valid symbols and sufficient period**:

```python
result = await compare_securities(
    symbols=["AAPL", "MSFT", "GOOGL"],  # Use valid symbols
    metric="signals",
)
```

---

### Issue 7: Slow Performance with Long Periods

**Symptom**: Tools take minutes to complete with `6mo` or `1y` periods.

**Cause**: More data to fetch and process.

**Solutions**:

**A. Use appropriate period for the task**:
- Quick analysis: `1mo` to `3mo`
- Comprehensive analysis: `6mo`
- Long-term trends: `1y`

**B. Enable caching** (already enabled by default):

Cache configuration in `config.py`:

```python
CACHE_TTL_SECONDS: Final[int] = 300  # 5 minutes
CACHE_MAX_SIZE: Final[int] = 100  # Maximum symbols to cache
```

**C. For screening/scanning, use `3mo` as maximum**:

Screening 500 symbols with `1y` period is very slow. Use `3mo` for good balance.

---

### Issue 8: "Invalid period" Warning

**Symptom**:
```
WARNING: Invalid period '2mo', using default '1mo'
```

**Cause**: Period not in `VALID_PERIODS` list.

**Valid periods** (from `config.py` line 17):
- **Intraday**: `15m`, `1h`, `4h` (NEW in v1.1)
- **Daily & Longer**: `1d`, `5d`, `1mo`, `3mo`, `6mo`, `1y`, `2y`, `5y`, `10y`, `ytd`, `max`

**Solution**: Use a valid period:

```python
# Invalid
result = await analyze_security("AAPL", period="2mo")  # ❌ Not valid

# Valid - Daily period
result = await analyze_security("AAPL", period="3mo")  # ✅ Valid

# Valid - Intraday period (NEW)
result = await analyze_security("AAPL", period="1h")  # ✅ Valid (day trading)
result = await analyze_security("AAPL", period="15m")  # ✅ Valid (scalping)
```

---

## Best Practices

### 1. Match Period to Use Case

| Use Case | Recommended Period | Reasoning |
|----------|-------------------|-----------|
| Scalping | `15m` | Fastest signals, high-frequency trades |
| Day trading | `1h` to `4h` | Intraday momentum, quick reversals |
| Swing trading | `1d` to `3mo` | Balance of recent + trend context |
| Position trading | `6mo` to `1y` | Long-term trends and 200-day SMA |
| Portfolio risk | `6mo` to `1y` | Stable volatility and correlation measures |
| Quick screening | `1mo` to `3mo` | Performance vs. accuracy tradeoff |
| Comprehensive analysis | `6mo` | Best balance for most use cases |
| **NEW: Intraday momentum** | **`4h`** | **Best for intraday trend analysis** |
| **NEW: Intraday volatility** | **`1h` - `4h`** | **Optimal for stop-loss placement** |

---

### 2. Understand Indicator Requirements

| Indicator | Minimum Data Points | Minimum Period |
|-----------|---------------------|----------------|
| RSI (14) | 14 | `1mo` (21 days) |
| MACD (12/26/9) | 26 | `3mo` (63 days) |
| 5-day SMA | 5 | `1d` (5 days) |
| 10-day SMA | 10 | `5d` (10 days) |
| 20-day SMA | 20 | `1mo` (21 days) |
| 50-day SMA | 50 | `3mo` (63 days) |
| 100-day SMA | 100 | `6mo` (126 days) |
| 200-day SMA | 200 | `1y` (252 days) |
| Bollinger Bands (20) | 20 | `1mo` (21 days) |
| ADX (14) | 14 | `1mo` (21 days) |
| ATR (14) | 14 | `1mo` (21 days) |

---

### 3. Test Changes Before Deploying

**Always test period changes**:

```bash
# Activate environment
mamba activate fin-ai1

# Run test suite
python test_all_mcp_tools_fixed.py

# Check results
cat mcp_test_results_fixed/*/SUMMARY.json
```

---

### 4. Monitor Cache Performance

Longer periods benefit more from caching:

```python
# config.py - Increase cache for production
CACHE_TTL_SECONDS: Final[int] = 600  # 10 minutes (up from 5)
CACHE_MAX_SIZE: Final[int] = 200  # 200 symbols (up from 100)
```

---

### 5. Use Environment-Specific Periods

**Development**: Shorter periods for faster iteration
```python
DEFAULT_PERIOD = "1mo"  # Fast for testing
```

**Staging**: Match production
```python
DEFAULT_PERIOD = "3mo"  # Same as production
```

**Production**: Optimal for accuracy
```python
DEFAULT_PERIOD = "3mo"  # or "6mo" for comprehensive analysis
```

---

### 6. Intraday Trading Best Practices (NEW in v1.1)

**Using the new 15m, 1h, 4h periods:**

```python
# Scalping strategy (15-minute bars)
result = await analyze_security(
    symbol="AAPL",
    period="15m"  # Ultra-high frequency signals
)

# Day trading strategy (1-hour bars)
result = await get_trade_plan(
    symbol="AAPL",
    period="1h"  # Hourly trend + volatility
)

# Swing trading within a week (4-hour bars)
result = await scan_trades(
    universe="nasdaq100",
    period="4h"  # Best intraday swing analysis
)
```

**Intraday-specific considerations:**

1. **Signal Quality**: Intraday signals have more noise - use stricter filters
2. **Risk Management**: Set tighter stops due to volatility (0.5-1 ATR vs 1.5-2 ATR)
3. **Entry/Exit Timing**: Use intraday resistance/support levels, not daily levels
4. **Monitor ATR**: Intraday ATR will be much smaller - adjust position sizing
5. **Market Hours**: Only use intraday periods during trading hours (9:30-16:00 ET)

---

## Summary

### ✅ ALL TOOLS NOW SUPPORT PERIOD PARAMETERS (v1.1)

**All 9 MCP tools now accept period as a configurable parameter:**

1. ✅ `analyze_security` - Pass `period="3mo"` or `period="1h"`
2. ✅ `compare_securities` - Pass `period="3mo"` or `period="15m"`
3. ✅ `screen_securities` - Pass `period="3mo"` or `period="4h"`
4. ✅ `get_trade_plan` - Pass `period="3mo"` or `period="1h"`
5. ✅ `scan_trades` - Pass `period="3mo"` or `period="4h"`
6. ✅ `portfolio_risk` - Pass `period="6mo"` or any valid period
7. ✅ `morning_brief` - Pass `period="3mo"` or any valid period
8. ✅ `analyze_fibonacci` - Pass `period="3mo"` or any valid period
9. ❌ `options_risk_analysis` - Uses current data (no period needed)

**Global default**:
- Edit `config.py` line 16: `DEFAULT_PERIOD = "3mo"` or `"1h"` for intraday

**Supported Periods** (new & existing):
```
Intraday:  15m, 1h, 4h       (NEW - for day/swing traders)
Daily:     1d, 5d, 1mo       (existing)
Long-term: 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max (existing)
```

---

## References

- **Configuration File**: [src/technical_analysis_mcp/config.py](src/technical_analysis_mcp/config.py)
- **Server Implementation**: [src/technical_analysis_mcp/server.py](src/technical_analysis_mcp/server.py)
- **Test Results**: [FINAL_MCP_TEST_REPORT.md](FINAL_MCP_TEST_REPORT.md)
- **Test Script**: [test_all_mcp_tools_fixed.py](test_all_mcp_tools_fixed.py)

---

---

## 🎉 What's New in v1.1

✨ **Major Update**: Full intraday period support!

- **Added**: 15-minute, 1-hour, and 4-hour periods for all analysis tools
- **Updated**: All 9 MCP tools now accept period as a configurable parameter (8 with changes)
- **Enhanced**: Period parameter added to 5 tools that previously had hardcoded periods
- **Documentation**: Complete intraday trading guide with best practices

**Breaking Changes**: None - all changes are backward compatible

**Migration**: No action required for existing code. Optionally add periods to your calls:
```python
# Old (still works - uses default 1mo)
result = await analyze_security("AAPL")

# New (explicit period control)
result = await analyze_security("AAPL", period="1h")
```

---

**Document Version**: 1.1 - Intraday Support
**Last Updated**: January 28, 2026
**Maintainer**: MCP Finance Team
