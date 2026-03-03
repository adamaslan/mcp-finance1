# Four-Layer Data Retrieval Workflow

**Status**: ✅ Active
**Scope**: All backend data fetching (MCP tools and API routes)
**Last Updated**: March 3, 2026

---

## The Architecture

All price/market data retrieval MUST follow this exact four-layer fallback pattern:

```
Layer 1: In-Memory Cache (L1)
    ↓ (if miss)
Layer 2: Persistent Firestore Cache (L2)
    ↓ (if miss)
Layer 3: User-Supplied Prices (L3)
    ↓ (if unavailable)
Layer 4: API Providers (L4)
```

---

## Layer-by-Layer Rules

### Layer 1: In-Memory Cache (300s TTL)

**Purpose**: Ultra-fast access per container instance

**Rules**:
- Always check first before any other layer
- Fast TTL = 300 seconds (5 minutes)
- Returns immediately on hit without I/O
- Per-container isolation (not shared)

**Code Pattern**:
```python
# In your tool function
result = self._in_memory_cache.get(cache_key)
if result:
    return result  # Instant return
# Continue to Layer 2...
```

**When to Use**:
- All real-time analysis (single request → multiple tool calls)
- Prevents duplicate API calls within same execution
- Always check this first, never skip

---

### Layer 2: Persistent Firestore Cache (300s TTL)

**Purpose**: Shared cache across all container instances

**Rules**:
- Hit: Return cached data to user immediately
- On hit: Spawn non-blocking background task to fetch fresh data
- Miss: Continue to Layer 3
- 300-second TTL (matches L1, aligns with frontend ISR)
- Write every tool result automatically (non-blocking)

**Code Pattern**:
```python
# Check Firestore
cached = await firestore_cache.get(cache_key)
if cached:
    # Return immediately to user
    return cached['result']

    # Optionally, background refresh (don't block)
    # asyncio.create_task(self._refresh_data(cache_key))

# Continue to Layer 3...
```

**Background Delta Update**:
- Only write to Firestore if data differs from cached version
- Never block tool execution for Firestore writes
- Log errors but don't fail the tool

---

### Layer 3: User-Supplied Prices (Optional Override)

**Purpose**: Allow portfolio owners to provide manual prices

**Rules**:
- Check if user supplied prices in portfolio positions
- If available: Use them, skip Layer 4 entirely
- This saves API quota and ensures consistency
- Applies to all securities in analysis

**Code Pattern**:
```python
# Check if user provided price in portfolio
if symbol in portfolio_prices:
    manual_price = portfolio_prices[symbol]
    logger.info(f"Using user-supplied price for {symbol}: {manual_price}")
    return manual_price  # Skip all APIs

# Continue to Layer 4...
```

**When Applicable**:
- analyze_security (single symbol)
- compare_securities (multiple symbols)
- portfolio_risk (all positions)
- Any tool working with portfolio holdings

---

### Layer 4: API Providers (External Data)

**Purpose**: Authoritative market data when no cached data available

**Rules**:
- Only reach here if Layers 1-3 miss/unavailable
- Implement provider-specific rate limiting
- Track quota usage and degrade gracefully
- Add intentional delays for generous providers
- Fail explicitly with error messages (never mock data)

#### Provider: yfinance

```python
# No API key required
# Generous limits but be respectful

# Rule: Add small delays between requests
import time
time.sleep(0.5)  # 500ms between API calls

# Fetch
price = yf.Ticker(symbol).info.get('currentPrice')
if not price:
    raise DataUnavailableError(f"yfinance unavailable for {symbol}")
return price
```

**Best Practices**:
- Use for supplementary data (PE, dividend, etc.)
- Batch requests when possible
- Don't hammer with rapid calls

#### Provider: Alpha Vantage

```python
# API Key required (limit: 25 calls/day)

# Rule: Track remaining quota
remaining = av_client.get_remaining_calls()
if remaining <= 5:
    logger.warning(f"Alpha Vantage quota low: {remaining} calls left")
    raise QuotaExhaustedError("Alpha Vantage daily limit approaching")

# Fetch with timeout
try:
    data = av_client.get_quote(symbol)
    return data['price']
except QuotaError:
    logger.error("Alpha Vantage quota exhausted for today")
    raise QuotaExhaustedError("Please try again tomorrow")
```

**Budget Rules**:
- Track remaining calls in state or logs
- Refuse calls when <= 5 remaining (preserve for critical needs)
- Log quota exhaustion clearly
- Return HTTP 503 (Service Unavailable) when quota exhausted
- Never mock data as fallback

#### Provider: Finnhub

```python
# Rate-limited based on tier

# Sandbox/Trial: ~60 calls/minute
# Premium: Higher limits, check documentation

# Rule: Respect rate limits
# Implement exponential backoff on 429 responses

try:
    price = finnhub_client.quote(symbol)['c']
except RateLimitError as e:
    logger.warning(f"Finnhub rate limited: {e}")
    await asyncio.sleep(2)  # Backoff
    raise ServiceUnavailableError("Finnhub rate limited, retry in 2s")
```

---

## Implementation Checklist

When implementing data fetching:

- [ ] Check Layer 1 (in-memory) first
- [ ] Check Layer 2 (Firestore) with background refresh
- [ ] Check Layer 3 (user prices) if available
- [ ] Only call Layer 4 APIs if all above miss
- [ ] Log each layer decision
- [ ] Handle Layer 4 errors gracefully (no mock data)
- [ ] Return proper HTTP status codes on failures
- [ ] Never block user response for cache writes

---

## Error Handling Rules

### When Each Layer Fails

| Layer | Failure | Action |
|-------|---------|--------|
| L1 | Cache miss | Continue to L2 |
| L2 | Firestore unavailable | Continue to L3 |
| L3 | No user prices | Continue to L4 |
| L4 | All APIs exhausted | Return HTTP 503 with error message |

### Error Response Format

```python
# NEVER mock data
if not data and no_fallback:
    return {
        "error": "Data unavailable",
        "reason": "Alpha Vantage quota exhausted",
        "status": "SERVICE_UNAVAILABLE",  # HTTP 503
        "retry_after": "24 hours",
        "details": "Please try again tomorrow"
    }
```

---

## Quota Tracking

### Alpha Vantage Budget

```python
# Track calls across session
AV_MAX_DAILY_CALLS = 25
av_calls_made = 0

def make_av_call(symbol):
    global av_calls_made
    if av_calls_made >= AV_MAX_DAILY_CALLS:
        raise QuotaExhaustedError(f"Used all {AV_MAX_DAILY_CALLS} calls")

    result = av_client.get_quote(symbol)
    av_calls_made += 1

    logger.info(f"AV: {av_calls_made}/{AV_MAX_DAILY_CALLS} calls used")
    return result
```

### Monitoring

Log these metrics:
- Total L1 hits (in-memory)
- Total L2 hits (Firestore)
- Total L3 hits (user prices)
- Total L4 calls per provider
- Quota remaining for each paid provider
- Cache refresh timing (background tasks)

---

## Cache Key Design

Consistent cache keys prevent duplication:

```python
# Format: {layer}:{provider}:{symbol_or_criteria}:{period}:{timestamp_bucket}

# Examples:
"firestore:yfinance:AAPL:daily:2026-03-03-09"  # Bucket by hour
"firestore:analyze_security:GOOG:1h:2026-03-03-09-15"  # Bucket by 15min
"firestore:portfolio_risk:AAPL,GOOG,TSLA:daily:2026-03-03"
```

---

## Common Mistakes (Don't Do These)

❌ **Mistake 1**: Skip L1 check
```python
# WRONG
result = firestore_cache.get(key)  # Should check L1 first

# RIGHT
result = in_memory_cache.get(key)
if result: return result
result = firestore_cache.get(key)
```

❌ **Mistake 2**: Block on Layer 2 writes
```python
# WRONG
await firestore_cache.set(key, data)  # Blocks user response
return data

# RIGHT
asyncio.create_task(firestore_cache.set(key, data))  # Fire-and-forget
return data
```

❌ **Mistake 3**: Mock data when API fails
```python
# WRONG
try:
    price = api.get_price(symbol)
except APIError:
    price = 100.0  # NEVER mock

# RIGHT
try:
    price = api.get_price(symbol)
except APIError as e:
    logger.error(f"Failed to fetch {symbol}: {e}")
    raise ServiceUnavailableError("Price data unavailable")
```

❌ **Mistake 4**: Ignore quota limits
```python
# WRONG
for symbol in symbols:
    price = av_client.get_quote(symbol)  # Will hit quota

# RIGHT
remaining = av_client.get_remaining_calls()
if len(symbols) > remaining:
    raise QuotaExhaustedError(f"Need {len(symbols)} calls, {remaining} left")
```

---

## Verification

### Code Review Checklist

When reviewing backend code, verify:

- [ ] All data fetching follows Layer 1→2→3→4 order
- [ ] No API calls skip cache layers
- [ ] Layer 2 writes are non-blocking (fire-and-forget)
- [ ] Proper HTTP 503 when quota exhausted
- [ ] No mock data in error paths
- [ ] All API errors logged with context
- [ ] User prices checked before external APIs
- [ ] Quota remaining tracked for paid providers
- [ ] Cache keys consistent across codebase

### Testing

```bash
# Test Layer 1: Call same symbol twice quickly
# Should use cache, skip L2-L4

# Test Layer 2: Restart container with Firestore data
# Should hit Firestore, background refresh L4

# Test Layer 3: Set portfolio price manually
# Should skip all APIs, use portfolio price

# Test Layer 4: Clear all caches, force API call
# Should use external API, track quota

# Test Quota: Make 25+ Alpha Vantage calls
# Should fail with HTTP 503 after quota
```

---

## Files Implementing This

**Backend Implementation**:
- `src/technical_analysis_mcp/cache/firestore_cache.py` - Layer 2
- `src/technical_analysis_mcp/cache/__init__.py` - Cache utilities
- `src/technical_analysis_mcp/server.py` - Integration with all tools
- Individual tool modules - Layer 1 + Layer 3 checks

**Frontend Integration**:
- `src/lib/firebase/landing-cache.ts` - Read Layer 2
- `src/app/api/dashboard/tool-cache/route.ts` - Public cache API
- `src/components/tools/ToolPage.tsx` - Display cached status

---

## Related Documentation

- `../../nu-logs2/DATA_FALLBACK_CACHING_GUIDE.md` - Full caching architecture
- `../../nu-logs2/FIRESTORE_CACHE_VERIFICATION.md` - Verification steps
- `./../CLAUDE.md` - Project guidelines (includes this rule)
- GCP Project: ttb-lang1, Firestore collection: mcp_tool_cache

---

**Enforcement**: This rule is mandatory for all data retrieval code in the backend. All PRs touching data fetching must comply.

**Questions**: Refer to the implementation examples in `src/technical_analysis_mcp/server.py` for working code.
