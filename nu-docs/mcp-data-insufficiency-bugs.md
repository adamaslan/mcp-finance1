# MCP Tool Data Insufficiency Bugs - Analysis & Fixes

## Executive Summary

Four MCP tools are failing with data insufficiency errors when analyzing securities. The root cause is a mismatch between the default period (`1mo` = ~21 trading days) and the minimum data requirement (`MIN_DATA_POINTS = 50`).

---

## Bugs Identified

### Bug 1: Period/Minimum Data Mismatch

**Affected Tools**: `analyze_security`, `compare_securities`, `get_trade_plan`, `analyze_fibonacci`

**Location**: [config.py:16](cloud-run/src/technical_analysis_mcp/config.py#L16) and [config.py:39](cloud-run/src/technical_analysis_mcp/config.py#L39)

```python
DEFAULT_PERIOD: Final[str] = "1mo"      # ~21 trading days
MIN_DATA_POINTS: Final[int] = 50        # Requires 50 candles
```

**Problem**: The default period returns ~21 data points, but validation requires 50. This causes immediate failure for any tool using defaults.

**Error Message**:
```
Insufficient data for AAPL (need 50 periods, have 21 with 1mo period)
```

---

### Bug 2: NoneType Error in `compare_securities`

**Location**: [server.py:382](cloud-run/src/technical_analysis_mcp/server.py#L382)

```python
return {
    "comparison": results,
    "metric": metric,
    "winner": results[0] if results else None,  # Safe
}
```

**Problem**: While the `winner` key handles empty results, downstream code accessing `analysis["summary"]["avg_score"]` at line 366 fails with `NoneType` when `analyze_security` returns partial data or the summary is missing.

**Root Cause**: When all symbols fail due to insufficient data, the error is logged but then the function tries to access attributes on `None` objects.

---

### Bug 3: No Graceful Degradation for Indicators

**Location**: [config.py:24](cloud-run/src/technical_analysis_mcp/config.py#L24)

```python
MA_PERIODS: Final[tuple[int, ...]] = (5, 10, 20, 50, 100, 200)
```

**Problem**: When calculating 50-SMA or 200-SMA with insufficient data:
- 50-SMA needs 50 data points minimum
- 200-SMA needs 200 data points minimum

With `1mo` period (~21 days), these indicators either fail silently (returning `NaN`) or cause cascading errors in signal detection.

---

### Bug 4: No Period Auto-Escalation

**Location**: [data.py](cloud-run/src/technical_analysis_mcp/data.py) (fetch logic)

**Problem**: When the requested period doesn't provide enough data, the system throws an error instead of automatically trying a longer period.

**Current Behavior**:
```
Request: analyze_security("AAPL", period="1mo")
Result: InsufficientDataError (21 < 50)
```

**Expected Behavior**:
```
Request: analyze_security("AAPL", period="1mo")
Auto-escalate to "3mo" -> Success (63 data points)
```

---

### Bug 5: Hardcoded Period in `compare_securities`

**Location**: [server.py:363](cloud-run/src/technical_analysis_mcp/server.py#L363)

```python
analysis = await analyze_security(symbol, period="1mo")  # Hardcoded!
```

**Problem**: The period is hardcoded to `1mo` instead of being configurable or using a smart default. Users cannot pass a different period to `compare_securities`.

---

## 5 Ways to Make MCP Tools More Robust

### 1. Implement Adaptive Period Selection

**Description**: Automatically escalate to longer periods when data is insufficient.

**Implementation**:
```python
PERIOD_ESCALATION_ORDER = ["1mo", "3mo", "6mo", "1y"]

async def fetch_with_adaptive_period(
    symbol: str,
    requested_period: str,
    min_points: int = MIN_DATA_POINTS
) -> tuple[pd.DataFrame, str]:
    """Fetch data, auto-escalating period if needed."""
    periods_to_try = PERIOD_ESCALATION_ORDER[
        PERIOD_ESCALATION_ORDER.index(requested_period):
    ]

    for period in periods_to_try:
        df = await fetch_data(symbol, period)
        if len(df) >= min_points:
            return df, period

    raise InsufficientDataError(
        symbol,
        required_periods=min_points,
        available_periods=len(df),
        tried_periods=periods_to_try
    )
```

**Benefits**:
- Transparent to users
- Always returns valid data when possible
- Logs which period was actually used

---

### 2. Implement Graceful Indicator Degradation

**Description**: Calculate only the indicators that are possible with available data.

**Implementation**:
```python
def calculate_indicators_adaptive(df: pd.DataFrame) -> dict[str, Any]:
    """Calculate indicators based on available data points."""
    n = len(df)
    indicators = {}

    # Always calculate these (need minimal data)
    if n >= RSI_PERIOD:
        indicators["rsi"] = calculate_rsi(df)

    if n >= MACD_SLOW:
        indicators["macd"] = calculate_macd(df)

    # Only calculate MAs we have data for
    available_mas = [p for p in MA_PERIODS if p <= n]
    for period in available_mas:
        indicators[f"sma_{period}"] = df["Close"].rolling(period).mean()

    # Flag what's missing
    indicators["_missing"] = [p for p in MA_PERIODS if p > n]
    indicators["_data_points"] = n

    return indicators
```

**Benefits**:
- Partial analysis is better than no analysis
- Users know what's missing
- No silent `NaN` values

---

### 3. Add Configurable Period to `compare_securities`

**Description**: Allow users to specify the analysis period.

**Implementation**:
```python
async def compare_securities(
    symbols: list[str],
    metric: str = "signals",
    period: str = "3mo",  # New parameter with better default
) -> dict[str, Any]:
    """Compare multiple securities.

    Args:
        symbols: List of ticker symbols.
        metric: Comparison metric.
        period: Analysis period (default: 3mo for reliable data).
    """
    # Validate period
    if period not in VALID_PERIODS:
        period = "3mo"

    for symbol in symbols:
        try:
            analysis = await analyze_security(symbol, period=period)
            # ...
```

**Benefits**:
- User control over data depth
- Better default (`3mo` provides ~63 data points)
- Consistent behavior across tools

---

### 4. Implement Comprehensive Error Handling with Fallbacks

**Description**: Handle errors gracefully and provide useful feedback.

**Implementation**:
```python
async def analyze_security_robust(
    symbol: str,
    period: str = "3mo",
    allow_partial: bool = True,
) -> dict[str, Any]:
    """Analyze security with robust error handling.

    Args:
        symbol: Stock ticker.
        period: Data period.
        allow_partial: If True, return partial analysis on insufficient data.
    """
    try:
        df = await fetch_data(symbol, period)
        data_points = len(df)

        if data_points < MIN_DATA_POINTS:
            if allow_partial:
                return {
                    "symbol": symbol,
                    "status": "partial",
                    "data_points": data_points,
                    "required_points": MIN_DATA_POINTS,
                    "indicators": calculate_indicators_adaptive(df),
                    "signals": [],  # Skip signal detection
                    "warning": f"Partial analysis: {data_points}/{MIN_DATA_POINTS} data points",
                    "suggestion": f"Use period='3mo' or longer for full analysis",
                }
            else:
                raise InsufficientDataError(symbol, MIN_DATA_POINTS, data_points)

        # Full analysis
        return await _full_analysis(df, symbol)

    except InvalidSymbolError:
        return {
            "symbol": symbol,
            "status": "error",
            "error": "Invalid symbol",
            "suggestion": "Check ticker symbol format",
        }
    except DataFetchError as e:
        return {
            "symbol": symbol,
            "status": "error",
            "error": str(e),
            "suggestion": "Market may be closed or API unavailable",
        }
```

**Benefits**:
- Never crashes on bad input
- Provides actionable suggestions
- Supports partial results for quick feedback

---

### 5. Add Data Sufficiency Pre-Check Endpoint

**Description**: Create a validation endpoint to check data availability before analysis.

**Implementation**:
```python
async def check_data_sufficiency(
    symbols: list[str],
    period: str = "1mo",
    required_indicators: list[str] | None = None,
) -> dict[str, Any]:
    """Pre-check data sufficiency for analysis.

    Returns which symbols have sufficient data and recommended periods.
    """
    required_indicators = required_indicators or ["rsi", "macd", "sma_50"]

    # Calculate minimum points needed
    indicator_requirements = {
        "rsi": RSI_PERIOD,
        "macd": MACD_SLOW,
        "sma_20": 20,
        "sma_50": 50,
        "sma_200": 200,
    }
    min_needed = max(
        indicator_requirements.get(ind, 50)
        for ind in required_indicators
    )

    results = []
    for symbol in symbols:
        try:
            df = await fetch_data(symbol, period)
            available = len(df)
            sufficient = available >= min_needed

            results.append({
                "symbol": symbol,
                "sufficient": sufficient,
                "available_points": available,
                "required_points": min_needed,
                "recommended_period": _recommend_period(available, min_needed),
            })
        except Exception as e:
            results.append({
                "symbol": symbol,
                "sufficient": False,
                "error": str(e),
            })

    return {
        "checked": len(symbols),
        "sufficient_count": sum(1 for r in results if r.get("sufficient")),
        "results": results,
    }

def _recommend_period(available: int, needed: int) -> str:
    """Recommend period based on data gap."""
    if available >= needed:
        return "1mo"  # Current is fine

    # Estimate needed period
    ratio = needed / max(available, 1)
    if ratio <= 1.5:
        return "3mo"
    elif ratio <= 3:
        return "6mo"
    else:
        return "1y"
```

**Benefits**:
- Users can validate before expensive operations
- Batch check multiple symbols
- Smart period recommendations

---

## Quick Fix: Change Default Period

The simplest immediate fix is to change the default period in [config.py](cloud-run/src/technical_analysis_mcp/config.py):

```python
# Before
DEFAULT_PERIOD: Final[str] = "1mo"

# After
DEFAULT_PERIOD: Final[str] = "3mo"  # ~63 trading days > 50 minimum
```

This single change would resolve most failures without requiring code changes to any tools.

---

## Data Requirements Summary

| Indicator | Min Data Points | Period Needed |
|-----------|-----------------|---------------|
| RSI | 14 | 1mo |
| MACD | 26 | 1mo |
| SMA-20 | 20 | 1mo |
| SMA-50 | 50 | 3mo |
| SMA-100 | 100 | 6mo |
| SMA-200 | 200 | 1y |
| Full Analysis | 50 | 3mo |

---

## Recommended Priority

1. **Immediate**: Change `DEFAULT_PERIOD` to `"3mo"` (5 minutes)
2. **Short-term**: Add `period` parameter to `compare_securities` (30 minutes)
3. **Medium-term**: Implement adaptive period selection (2 hours)
4. **Long-term**: Implement graceful degradation and pre-check endpoint (4 hours)

---

## Files to Modify

| File | Change |
|------|--------|
| [config.py](cloud-run/src/technical_analysis_mcp/config.py) | Change `DEFAULT_PERIOD` to `"3mo"` |
| [server.py](cloud-run/src/technical_analysis_mcp/server.py) | Add period parameter to `compare_securities` |
| [data.py](cloud-run/src/technical_analysis_mcp/data.py) | Implement adaptive period escalation |
| [indicators.py](cloud-run/src/technical_analysis_mcp/indicators.py) | Add graceful degradation logic |
