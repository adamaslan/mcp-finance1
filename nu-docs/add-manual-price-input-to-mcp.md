# Adding Manual Price Input to MCP Tools

## Current Limitation

**PROBLEM**: All 9 MCP tools fetch prices exclusively from yfinance API with no way for users to:
- Input hypothetical prices for what-if analysis
- Override stale/incorrect API data
- Analyze options with custom strike prices
- Test scenarios when markets are closed
- Backtest with historical data they have

**IMPACT**:
- ❌ Cannot test "What if AAPL was at $150?"
- ❌ Cannot analyze custom option spreads
- ❌ Cannot use tools during market outages
- ❌ Cannot validate against known historical prices

---

## Price Data Flow (Current State)

```
User calls MCP tool (no price input allowed)
    ↓
Data Fetcher: yfinance API ONLY
    ↓
DataFrame with Close prices
    ↓
All 9 tools use these prices (no override)
    ↓
Results based solely on API data
```

**Key Bottleneck**: `YFinanceDataFetcher._fetch_data()` at [data.py:122-133](../src/technical_analysis_mcp/data.py#L122-L133)

---

## Solution: 3 Approaches to Add Manual Price Input

---

## Approach 1: Per-Tool Price Parameters (Simple)

**Best for**: Quick implementation, tool-specific needs

### Implementation

#### Step 1: Add Parameters to Tool Functions

```python
# src/technical_analysis_mcp/server.py

async def analyze_security(
    symbol: str,
    period: str = "3mo",
    use_ai: bool = False,
    # NEW PARAMETERS:
    price_override: float | None = None,
) -> dict[str, Any]:
    """Analyze security with optional manual price.

    Args:
        symbol: Ticker symbol.
        period: Time period for analysis.
        use_ai: Enable AI-powered ranking.
        price_override: Manual price override (optional).
            If provided, uses this instead of fetching from API.
            Useful for what-if scenarios and market-closed analysis.

    Example:
        # Normal API fetch
        analyze_security("AAPL", period="3mo")

        # Manual price override
        analyze_security("AAPL", period="3mo", price_override=150.50)
    """
    fetcher = get_data_fetcher()
    df = await fetcher.fetch(symbol, period)

    # Apply price override if provided
    if price_override is not None:
        df = df.copy()  # Don't modify cached data
        df.loc[df.index[-1], "Close"] = price_override
        df.loc[df.index[-1], "Open"] = price_override
        df.loc[df.index[-1], "High"] = max(price_override, df.iloc[-1]["High"])
        df.loc[df.index[-1], "Low"] = min(price_override, df.iloc[-1]["Low"])

    # ... rest of function unchanged
```

#### Step 2: Update Tool Registration

```python
# src/technical_analysis_mcp/server.py (tool list)

Tool(
    name="analyze_security",
    description="Run technical analysis with optional manual price",
    inputSchema={
        "type": "object",
        "properties": {
            "symbol": {
                "type": "string",
                "description": "Ticker symbol (e.g., AAPL, MSFT)",
            },
            "period": {
                "type": "string",
                "default": "3mo",
                "description": "Time period (1mo, 3mo, 6mo, 1y)",
            },
            "use_ai": {
                "type": "boolean",
                "default": False,
                "description": "Enable AI-powered ranking",
            },
            # NEW FIELD:
            "price_override": {
                "type": "number",
                "description": "Override current price (optional). Use for what-if scenarios.",
            },
        },
        "required": ["symbol"],
    },
),
```

#### Step 3: Add to All 9 Tools

Apply the same pattern to:
1. ✅ analyze_security
2. ✅ compare_securities (override per symbol via dict)
3. ✅ screen_securities
4. ✅ get_trade_plan
5. ✅ scan_trades
6. ✅ portfolio_risk (different - override entry_price)
7. ✅ morning_brief
8. ✅ analyze_fibonacci
9. ✅ options_risk_analysis (special handling for option chain)

### Pros & Cons

| Pros | Cons |
|------|------|
| Simple to implement | Repetitive code across tools |
| Tool-specific control | Price override per tool call (doesn't persist) |
| No architectural changes | No global override capability |

---

## Approach 2: Global Price Override Registry (Medium)

**Best for**: Session-wide overrides, testing, demonstrations

### Implementation

#### Step 1: Create Price Override Registry

```python
# src/technical_analysis_mcp/price_overrides.py

"""Price override registry for manual price injection."""

from typing import Dict, Optional
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class PriceOverride:
    """Single price override entry."""
    symbol: str
    price: float
    timestamp: datetime = field(default_factory=datetime.now)
    reason: str = ""


class PriceOverrideRegistry:
    """Global registry for manual price overrides."""

    def __init__(self):
        self._overrides: Dict[str, PriceOverride] = {}

    def set(self, symbol: str, price: float, reason: str = "") -> None:
        """Set price override for a symbol."""
        self._overrides[symbol.upper()] = PriceOverride(
            symbol=symbol.upper(),
            price=price,
            reason=reason,
        )

    def get(self, symbol: str) -> Optional[float]:
        """Get price override for a symbol."""
        override = self._overrides.get(symbol.upper())
        return override.price if override else None

    def remove(self, symbol: str) -> None:
        """Remove price override for a symbol."""
        self._overrides.pop(symbol.upper(), None)

    def clear(self) -> None:
        """Clear all price overrides."""
        self._overrides.clear()

    def list_all(self) -> Dict[str, PriceOverride]:
        """List all active overrides."""
        return self._overrides.copy()

    def has_override(self, symbol: str) -> bool:
        """Check if symbol has an override."""
        return symbol.upper() in self._overrides

    def set_multiple(self, overrides: Dict[str, float]) -> None:
        """Set multiple overrides at once."""
        for symbol, price in overrides.items():
            self.set(symbol, price)


# Global singleton
_registry = PriceOverrideRegistry()


def get_price_registry() -> PriceOverrideRegistry:
    """Get the global price override registry."""
    return _registry
```

#### Step 2: Integrate with Data Fetcher

```python
# src/technical_analysis_mcp/data.py

from .price_overrides import get_price_registry

class YFinanceDataFetcher:
    """Data fetcher with price override support."""

    def _fetch_data(self, symbol: str, period: str) -> pd.DataFrame:
        """Fetch data from yfinance with optional price override."""
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=period)

        if df.empty:
            raise DataFetchError(symbol, "No data returned from yfinance")

        # Check for price override
        registry = get_price_registry()
        override_price = registry.get(symbol)

        if override_price is not None:
            logger.info(
                f"Applying price override for {symbol}: ${override_price:.2f}"
            )
            # Override only the latest Close price
            df = df.copy()
            df.loc[df.index[-1], "Close"] = override_price
            df.loc[df.index[-1], "Open"] = override_price
            # Keep High/Low realistic
            df.loc[df.index[-1], "High"] = max(
                override_price, df.iloc[-1]["High"]
            )
            df.loc[df.index[-1], "Low"] = min(
                override_price, df.iloc[-1]["Low"]
            )

        return df
```

#### Step 3: Add Management Tools

```python
# Add new MCP tools for managing overrides

async def set_price_override(
    symbol: str,
    price: float,
    reason: str = "",
) -> dict[str, Any]:
    """Set manual price override for a symbol.

    Args:
        symbol: Ticker symbol.
        price: Override price.
        reason: Optional reason for override.

    Returns:
        Confirmation with active overrides.
    """
    registry = get_price_registry()
    registry.set(symbol, price, reason)

    return {
        "symbol": symbol,
        "price": price,
        "reason": reason,
        "active_overrides": len(registry.list_all()),
        "message": f"Price override set: {symbol} = ${price:.2f}",
    }


async def clear_price_overrides(
    symbol: str | None = None,
) -> dict[str, Any]:
    """Clear price overrides.

    Args:
        symbol: Specific symbol to clear (optional).
            If None, clears all overrides.

    Returns:
        Confirmation with cleared count.
    """
    registry = get_price_registry()

    if symbol:
        registry.remove(symbol)
        return {
            "cleared": symbol,
            "remaining_overrides": len(registry.list_all()),
        }
    else:
        count = len(registry.list_all())
        registry.clear()
        return {
            "cleared": "all",
            "count": count,
            "message": f"Cleared {count} price overrides",
        }


async def list_price_overrides() -> dict[str, Any]:
    """List all active price overrides.

    Returns:
        Dictionary of all active overrides.
    """
    registry = get_price_registry()
    overrides = registry.list_all()

    return {
        "count": len(overrides),
        "overrides": [
            {
                "symbol": o.symbol,
                "price": o.price,
                "timestamp": o.timestamp.isoformat(),
                "reason": o.reason,
            }
            for o in overrides.values()
        ],
    }
```

#### Step 4: Register New Tools

```python
# Add to app.list_tools()

Tool(
    name="set_price_override",
    description="Set manual price override for what-if analysis",
    inputSchema={
        "type": "object",
        "properties": {
            "symbol": {"type": "string", "description": "Ticker symbol"},
            "price": {"type": "number", "description": "Override price"},
            "reason": {"type": "string", "description": "Reason for override"},
        },
        "required": ["symbol", "price"],
    },
),
Tool(
    name="clear_price_overrides",
    description="Clear manual price overrides",
    inputSchema={
        "type": "object",
        "properties": {
            "symbol": {
                "type": "string",
                "description": "Symbol to clear (optional, clears all if omitted)",
            },
        },
    },
),
Tool(
    name="list_price_overrides",
    description="List all active price overrides",
    inputSchema={"type": "object", "properties": {}},
),
```

### Usage Example

```python
# Set price override
await set_price_override("AAPL", 150.50, reason="What-if scenario")

# Now all tools use $150.50 for AAPL
result1 = await analyze_security("AAPL")  # Uses $150.50
result2 = await get_trade_plan("AAPL")    # Uses $150.50
result3 = await compare_securities(["AAPL", "MSFT"])  # AAPL uses $150.50

# List active overrides
overrides = await list_price_overrides()
# {'count': 1, 'overrides': [{'symbol': 'AAPL', 'price': 150.5, ...}]}

# Clear override
await clear_price_overrides("AAPL")
```

### Pros & Cons

| Pros | Cons |
|------|------|
| Session-wide consistency | Global state (not thread-safe as-is) |
| No changes to existing tools | Override persists across calls |
| Easy testing/demos | Need to remember to clear |
| Management tools included | Cache invalidation needed |

---

## Approach 3: Enhanced Data Source with Fallbacks (Advanced)

**Best for**: Production apps, multiple data sources, reliability

### Implementation

#### Step 1: Create Data Source Abstraction

```python
# src/technical_analysis_mcp/data_sources.py

"""Flexible data source abstraction with manual overrides."""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
import pandas as pd
import yfinance as yf


class DataSource(ABC):
    """Abstract data source interface."""

    @abstractmethod
    async def fetch_ohlcv(
        self, symbol: str, period: str
    ) -> pd.DataFrame:
        """Fetch OHLCV data for symbol."""
        pass

    @abstractmethod
    async def fetch_current_price(self, symbol: str) -> float:
        """Fetch current price for symbol."""
        pass


class YFinanceDataSource(DataSource):
    """yfinance API data source."""

    async def fetch_ohlcv(
        self, symbol: str, period: str
    ) -> pd.DataFrame:
        ticker = yf.Ticker(symbol)
        return ticker.history(period=period)

    async def fetch_current_price(self, symbol: str) -> float:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period="1d")
        return float(hist["Close"].iloc[-1])


class ManualDataSource(DataSource):
    """Manual data source with user-provided prices."""

    def __init__(self, prices: Dict[str, float]):
        self._prices = prices

    async def fetch_ohlcv(
        self, symbol: str, period: str
    ) -> pd.DataFrame:
        """Not supported - manual source only provides current price."""
        raise NotImplementedError(
            "Manual data source doesn't provide historical OHLCV"
        )

    async def fetch_current_price(self, symbol: str) -> float:
        price = self._prices.get(symbol.upper())
        if price is None:
            raise ValueError(f"No manual price set for {symbol}")
        return price


class CSVDataSource(DataSource):
    """Load prices from CSV file."""

    def __init__(self, csv_path: str):
        self._data = pd.read_csv(csv_path, index_col="Date", parse_dates=True)

    async def fetch_ohlcv(
        self, symbol: str, period: str
    ) -> pd.DataFrame:
        # Filter by symbol column
        df = self._data[self._data["Symbol"] == symbol.upper()]
        # TODO: Apply period filter
        return df[["Open", "High", "Low", "Close", "Volume"]]

    async def fetch_current_price(self, symbol: str) -> float:
        df = self._data[self._data["Symbol"] == symbol.upper()]
        return float(df["Close"].iloc[-1])


class HybridDataSource(DataSource):
    """Hybrid source with fallback chain."""

    def __init__(
        self,
        sources: list[DataSource],
        price_overrides: Optional[Dict[str, float]] = None,
    ):
        self._sources = sources
        self._overrides = price_overrides or {}

    async def fetch_ohlcv(
        self, symbol: str, period: str
    ) -> pd.DataFrame:
        """Try sources in order until one succeeds."""
        for source in self._sources:
            try:
                df = await source.fetch_ohlcv(symbol, period)

                # Apply override to latest price if exists
                if symbol.upper() in self._overrides:
                    override = self._overrides[symbol.upper()]
                    df = df.copy()
                    df.loc[df.index[-1], "Close"] = override
                    df.loc[df.index[-1], "Open"] = override
                    df.loc[df.index[-1], "High"] = max(
                        override, df.iloc[-1]["High"]
                    )
                    df.loc[df.index[-1], "Low"] = min(
                        override, df.iloc[-1]["Low"]
                    )

                return df
            except Exception:
                continue

        raise DataFetchError(symbol, "All data sources failed")

    async def fetch_current_price(self, symbol: str) -> float:
        """Check override first, then try sources."""
        if symbol.upper() in self._overrides:
            return self._overrides[symbol.upper()]

        for source in self._sources:
            try:
                return await source.fetch_current_price(symbol)
            except Exception:
                continue

        raise DataFetchError(symbol, "All data sources failed")
```

#### Step 2: Configure Data Sources

```python
# src/technical_analysis_mcp/config.py

from .data_sources import (
    HybridDataSource,
    YFinanceDataSource,
    ManualDataSource,
    CSVDataSource,
)


def create_data_source(
    manual_prices: Optional[Dict[str, float]] = None,
    csv_path: Optional[str] = None,
) -> DataSource:
    """Create configured data source with fallbacks."""
    sources = []

    # Priority 1: Manual overrides (highest priority)
    if manual_prices:
        sources.append(ManualDataSource(manual_prices))

    # Priority 2: CSV file (for backtesting)
    if csv_path:
        sources.append(CSVDataSource(csv_path))

    # Priority 3: yfinance API (default)
    sources.append(YFinanceDataSource())

    return HybridDataSource(sources)
```

#### Step 3: Usage

```python
# Create hybrid source with overrides
data_source = create_data_source(
    manual_prices={"AAPL": 150.50, "TSLA": 245.75},
    csv_path="historical_data.csv",  # Optional
)

# Fetches in this order:
# 1. Check manual_prices for AAPL → $150.50 ✓
# 2. (skipped - found in #1)
# 3. (skipped - found in #1)

df = await data_source.fetch_ohlcv("AAPL", "3mo")
# Returns yfinance data with Close overridden to $150.50
```

### Pros & Cons

| Pros | Cons |
|------|------|
| Multiple data sources | Most complex to implement |
| Fallback reliability | Requires architectural refactor |
| CSV/file support | Steeper learning curve |
| Production-ready | Overkill for simple apps |

---

## Special Case: Options Price Override

Options require different handling because they have:
- **Underlying price** (stock)
- **Strike prices** (fixed)
- **Option premiums** (bid/ask/last)

### Option Price Override Structure

```python
@dataclass
class OptionPriceOverride:
    """Override for option chain data."""
    underlying_price: Optional[float] = None  # Override stock price
    option_prices: Dict[float, Dict[str, float]] = field(default_factory=dict)
    # option_prices format:
    # {
    #   185.0: {"call_bid": 2.50, "call_ask": 2.55, "put_bid": 1.20},
    #   190.0: {"call_bid": 1.25, "call_ask": 1.30, "put_bid": 2.10},
    # }


async def options_risk_analysis(
    symbol: str,
    expiration_date: str | None = None,
    option_type: str = "both",
    min_volume: int = 10,
    # NEW PARAMETERS:
    underlying_price_override: float | None = None,
    option_chain_override: Dict[float, Dict[str, float]] | None = None,
) -> dict[str, Any]:
    """Options analysis with manual price overrides.

    Args:
        symbol: Underlying ticker.
        expiration_date: Option expiration (YYYY-MM-DD).
        option_type: "calls", "puts", or "both".
        min_volume: Minimum option volume filter.
        underlying_price_override: Manual underlying stock price.
        option_chain_override: Manual option prices by strike.

    Example:
        # Override underlying to $150, custom option prices
        options_risk_analysis(
            "AAPL",
            underlying_price_override=150.0,
            option_chain_override={
                145.0: {"call_bid": 6.50, "call_ask": 6.60},
                150.0: {"call_bid": 3.25, "call_ask": 3.35},
                155.0: {"call_bid": 1.50, "call_ask": 1.55},
            }
        )
    """
    # ... implementation
```

---

## Comparison Summary

| Feature | Per-Tool Params | Global Registry | Hybrid Sources |
|---------|-----------------|-----------------|----------------|
| **Complexity** | Low | Medium | High |
| **Setup time** | 1 hour | 2 hours | 4+ hours |
| **Persistence** | Per call | Session | Configurable |
| **Multi-source** | No | No | Yes |
| **Thread-safe** | Yes | No (needs lock) | Yes |
| **CSV support** | No | No | Yes |
| **Best for** | Quick fixes | Demos/testing | Production |

---

## Recommended Implementation Order

### Phase 1: Quick Win (Week 1)
1. Add `price_override` parameter to `analyze_security`
2. Add `price_override` parameter to `get_trade_plan`
3. Test with sample use cases

### Phase 2: Registry (Week 2)
1. Implement `PriceOverrideRegistry`
2. Add management tools (set/clear/list)
3. Integrate with data fetcher
4. Add to remaining 7 tools

### Phase 3: Advanced (Week 3+)
1. Implement `DataSource` abstraction
2. Add CSV file support
3. Add option chain override support
4. Thread-safety improvements

---

## Testing Strategy

```python
# tests/test_price_overrides.py

import pytest
from src.technical_analysis_mcp.server import analyze_security
from src.technical_analysis_mcp.price_overrides import get_price_registry


@pytest.mark.asyncio
async def test_analyze_with_price_override():
    """Test analyze_security with manual price."""
    # Without override - uses API
    result1 = await analyze_security("AAPL", period="3mo")
    api_price = result1["price"]

    # With override
    result2 = await analyze_security("AAPL", period="3mo", price_override=999.99)
    assert result2["price"] == 999.99
    assert result2["price"] != api_price


@pytest.mark.asyncio
async def test_global_registry_override():
    """Test global price override registry."""
    registry = get_price_registry()
    registry.clear()

    # Set override
    registry.set("AAPL", 150.50)

    # All tools use override
    result = await analyze_security("AAPL")
    assert result["price"] == 150.50

    # Clear override
    registry.clear()
    result = await analyze_security("AAPL")
    assert result["price"] != 150.50  # Back to API
```

---

## Files to Create/Modify

| Approach | Files to Create | Files to Modify |
|----------|----------------|-----------------|
| **Per-Tool** | None | `server.py` (9 functions) |
| **Registry** | `price_overrides.py` | `server.py`, `data.py` |
| **Hybrid** | `data_sources.py` | `server.py`, `data.py`, `config.py` |

---

## Example Use Cases Enabled

### Use Case 1: What-If Analysis
```python
# "What if AAPL drops to $120?"
result = await analyze_security("AAPL", price_override=120.0)
# Shows signals/indicators at $120 price level
```

### Use Case 2: Options Strategy Testing
```python
# Test iron condor at specific prices
result = await options_risk_analysis(
    "SPY",
    underlying_price_override=450.0,
    option_chain_override={
        445.0: {"put_bid": 2.50, "put_ask": 2.55},
        455.0: {"call_bid": 2.45, "call_ask": 2.50},
    }
)
```

### Use Case 3: Market Closed Analysis
```python
# Set price from after-hours trading
registry = get_price_registry()
registry.set("TSLA", 245.75, reason="After-hours price at 8:00 PM")

# All tools use after-hours price
brief = await morning_brief(["TSLA", "AAPL"])
```

### Use Case 4: Backtesting
```python
# Load historical prices from CSV
data_source = create_data_source(csv_path="backtest_2023.csv")

# Run analysis with historical data
result = await get_trade_plan("AAPL")  # Uses CSV prices
```

---

## Recommendation

**Start with Approach 2 (Global Registry)** because it:
- ✅ Works across all 9 tools automatically
- ✅ Includes management tools (set/clear/list)
- ✅ Medium complexity (2-3 hour implementation)
- ✅ Easy to understand and use
- ✅ Enables demos and what-if scenarios
- ✅ Can be extended to Approach 3 later

**Skip Approach 1** - too repetitive, doesn't scale

**Plan for Approach 3** - Add CSV/multi-source later when needed
