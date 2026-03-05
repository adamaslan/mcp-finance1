# Four-Layer Data Retrieval Cache Pattern

**Quick reference for implementing data fetching in MCP tools**

---

## The Pattern (In Order)

Always follow this exact sequence for ANY data retrieval:

1. **Check In-Memory Cache** (L1)
   ```python
   result = cache.get(key)
   if result: return result
   ```

2. **Check Firestore** (L2)
   ```python
   cached = await firestore_cache.get(key)
   if cached:
       # Background refresh (async, non-blocking)
       asyncio.create_task(refresh_data(key))
       return cached['result']
   ```

3. **Check User Prices** (L3)
   ```python
   if symbol in portfolio_prices:
       return portfolio_prices[symbol]
   ```

4. **Call API** (L4)
   ```python
   price = api.get_price(symbol)  # yfinance, Finnhub, Alpha Vantage
   ```

---

## Critical Rules

❌ **NEVER**:
- Skip cache layers
- Block on Firestore writes
- Mock data when API fails
- Ignore quota limits

✅ **ALWAYS**:
- Check L1 first
- Write L2 results non-blocking
- Handle errors with proper HTTP status codes
- Return 503 when all sources fail

---

## Code Template

```python
async def get_price(symbol: str, portfolio_prices: dict = None) -> float:
    """Get price following four-layer cache pattern."""

    # L1: In-memory
    key = f"price:{symbol}"
    if price := self._cache.get(key):
        return price

    # L2: Firestore
    if cached := await firestore_cache.get(key):
        # Background refresh
        asyncio.create_task(firestore_cache.refresh(key))
        return cached['price']

    # L3: User prices
    if portfolio_prices and symbol in portfolio_prices:
        return portfolio_prices[symbol]

    # L4: API (with error handling)
    try:
        price = yf.Ticker(symbol).info.get('currentPrice')
        if not price:
            raise DataError(f"No price for {symbol}")

        # Non-blocking cache write
        asyncio.create_task(firestore_cache.set(key, {'price': price}))
        return price

    except QuotaError:
        raise HTTPException(status_code=503,
                          detail="Quota exhausted, try again tomorrow")
    except Exception as e:
        logger.error(f"Price fetch failed for {symbol}: {e}")
        raise HTTPException(status_code=503,
                          detail=f"Price unavailable: {e}")
```

---

## Per-Provider Rules

### yfinance
- No API key
- Add 0.5s delay between calls
- Use for supplementary data

### Alpha Vantage
- 25 calls/day limit
- Track remaining quota
- Fail when `remaining <= 5`
- Return 503 on quota exhaustion

### Finnhub
- Rate-limited per tier
- Implement exponential backoff on 429
- Handle gracefully

---

## When in Doubt

Check the full documentation:
- `.claude/rules/FOUR_LAYER_DATA_RETRIEVAL.md` - Complete guide
- `src/technical_analysis_mcp/server.py` - Working implementation
- `nu-logs2/DATA_FALLBACK_CACHING_GUIDE.md` - Architecture details

---

## Files Using This Pattern

- `src/technical_analysis_mcp/server.py` - All tool integrations
- `src/technical_analysis_mcp/cache/firestore_cache.py` - L2 implementation
- Individual tool modules - L1 + L3 checks

---

**Status**: Active
**Updated**: March 3, 2026
