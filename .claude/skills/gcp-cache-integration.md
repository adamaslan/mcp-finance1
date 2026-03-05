# GCP Cache Integration Guide

**How to integrate the GCP-optimized 7-layer cache into MCP tools**

---

## Quick Start

### Import the Cache Manager

```python
from src.technical_analysis_mcp.cache import get_cache_manager

# Get the global cache manager (singleton)
cache_mgr = get_cache_manager()
```

### Use in Tool Functions

```python
async def analyze_security(
    symbol: str,
    period: str = "daily",
    portfolio_prices: dict = None
) -> dict:
    """Analyze security with cache integration."""

    cache_key = f"analyze_security:{symbol}:{period}"

    # Try cache first (all 7 layers)
    if cache_hit := await cache_mgr.get(
        cache_key,
        symbol=symbol,
        tool_name="analyze_security"
    ):
        logger.info(f"Cache hit from {cache_hit.layer.name}")
        return cache_hit.data

    # Cache miss - compute the result
    result = await compute_analysis(symbol, period, portfolio_prices)

    # Write to all cache layers (non-blocking)
    await cache_mgr.set(
        cache_key,
        result,
        symbol=symbol,
        ttl=300
    )

    return result
```

---

## Method Reference

### Read from Cache (All 7 Layers)

```python
# Get from cache with automatic layer fallthrough
cache_hit = await cache_mgr.get(
    key="analyze_security:AAPL:daily",
    symbol="AAPL",  # Optional, enables Cloud Storage/BigQuery
    tool_name="analyze_security"  # Optional, schedules background refresh
)

if cache_hit:
    print(f"Hit from {cache_hit.layer.name}")
    result = cache_hit.data
else:
    print("Cache miss - fetch from API")
    result = await fetch_from_api()
```

### Write to Cache (All Layers)

```python
# Write to all available layers (non-blocking)
layers_written = await cache_mgr.set(
    key="analyze_security:AAPL:daily",
    data=result_dict,
    symbol="AAPL",  # Optional, enables Cloud Storage
    ttl=300  # Time-to-live in seconds
)

print(f"Cached to {layers_written} layers")
```

### Individual Layer Access

```python
# L1: Redis
price = cache_mgr.get_from_redis("price:AAPL")
cache_mgr.set_in_redis("price:AAPL", 172.50)

# L2a: Firestore
doc = await cache_mgr.get_from_firestore("mcp_tool_cache", "key")
await cache_mgr.set_in_firestore("mcp_tool_cache", "key", data)

# L2b: Cloud Storage
historical = cache_mgr.get_from_cloud_storage("AAPL", period="daily")
cache_mgr.set_in_cloud_storage("AAPL", data, period="daily")

# L3: BigQuery
metrics = cache_mgr.get_from_bigquery("AAPL")

# L4: Cloud Tasks
cache_mgr.schedule_cache_refresh("AAPL", "analyze_security")

# L0: Secrets
api_key = cache_mgr.get_secret("finnhub-api-key")
```

### Quota Tracking

```python
# Check remaining quota
remaining = cache_mgr.get_api_quota("alpha-vantage")
if remaining <= 5:
    logger.warning(f"Low quota: {remaining} calls left")

# Atomically decrement quota
if not cache_mgr.decrement_api_quota("alpha-vantage"):
    raise HTTPException(status_code=503, detail="Quota exhausted")
```

---

## Complete Example

```python
from fastapi import HTTPException
from src.technical_analysis_mcp.cache import get_cache_manager
import asyncio

cache_mgr = get_cache_manager()

async def analyze_security_with_cache(
    symbol: str,
    period: str = "daily",
    portfolio_prices: dict = None
) -> dict:
    """Analyze security with full GCP cache integration."""

    cache_key = f"analyze_security:{symbol}:{period}"

    # Step 1: Check cache (L1→L2a→L2b→L3)
    logger.info(f"Checking cache for {symbol}")
    if cache_hit := await cache_mgr.get(cache_key, symbol=symbol, tool_name="analyze_security"):
        logger.info(f"✓ Cache hit from {cache_hit.layer.name}")
        # Background refresh via Cloud Tasks (fire-and-forget)
        cache_mgr.schedule_cache_refresh(symbol, "analyze_security")
        return cache_hit.data

    logger.info(f"Cache miss for {symbol}")

    # Step 2: Use user-supplied price if available (L3)
    price = None
    if symbol in (portfolio_prices or {}):
        price = portfolio_prices[symbol]
        logger.info(f"Using portfolio price for {symbol}: ${price}")

    # Step 3: Get API key from Secret Manager (L0)
    try:
        api_key = cache_mgr.get_secret("finnhub-api-key")
    except Exception as e:
        logger.error(f"Failed to get API key: {e}")
        raise HTTPException(status_code=503, detail="Configuration error")

    # Step 4: Check API quota and fetch from API (L5)
    logger.info(f"Fetching {symbol} from API")

    if not price:  # Only fetch if we don't have manual price
        # Check quota
        remaining = cache_mgr.get_api_quota("finnhub")
        if remaining <= 0:
            raise HTTPException(status_code=503, detail="API quota exhausted")

        # Get price from API
        try:
            import finnhub
            finnhub_client = finnhub.Client(api_key=api_key)
            quote = finnhub_client.quote(symbol)
            price = quote.get('c')

            # Decrement quota
            await asyncio.to_thread(
                cache_mgr.decrement_api_quota,
                "finnhub"
            )

        except Exception as e:
            logger.error(f"API fetch failed: {e}")
            raise HTTPException(status_code=503, detail="Price data unavailable")

    # Step 5: Compute analysis
    logger.info(f"Computing analysis for {symbol}")
    result = {
        "symbol": symbol,
        "price": price,
        "period": period,
        "signals": [...],  # Real analysis here
        "timestamp": datetime.utcnow().isoformat()
    }

    # Step 6: Write to all cache layers (non-blocking)
    logger.info(f"Caching result to all layers")
    await cache_mgr.set(
        key=cache_key,
        data=result,
        symbol=symbol,
        ttl=300  # 5 minutes
    )

    logger.info(f"✓ Analysis complete for {symbol}")
    return result
```

---

## Error Handling

### Graceful Degradation

```python
# Cache failures should never break tool execution
try:
    if cache_hit := await cache_mgr.get(cache_key, symbol=symbol):
        return cache_hit.data
except Exception as e:
    logger.warning(f"Cache read failed: {e}, continuing without cache")

# Compute result
result = await compute_analysis(symbol, period)

# Try to cache, but don't fail if it doesn't work
try:
    await cache_mgr.set(cache_key, result, symbol=symbol)
except Exception as e:
    logger.warning(f"Cache write failed: {e}, continuing")

return result
```

### Quota Exhaustion

```python
# Always check quota before API call
if not cache_mgr.decrement_api_quota("alpha-vantage"):
    logger.error("Alpha Vantage quota exhausted")
    raise HTTPException(
        status_code=503,
        detail="API quota exhausted. Please try again tomorrow."
    )

# Make API call
result = av_client.get_quote(symbol)
```

---

## Configuration

### Environment Variables

```bash
# .env.gcp or environment
GCP_PROJECT_ID=ttb-lang1
REDIS_HOST=10.0.0.3
REDIS_PORT=6379
BUCKET_NAME=mcp-cache-historical
CLOUD_TASKS_QUEUE=mcp-cache-refresh
CLOUD_TASKS_REGION=us-central1
CACHE_REFRESH_URL=https://mcp-backend.cloud.run/api/cache-refresh
```

### Disable Individual Layers (if needed)

```python
# For testing - disable specific layers
cache_mgr.layers_available[CacheLayer.REDIS] = False  # Skip Redis
cache_mgr.layers_available[CacheLayer.CLOUD_STORAGE] = False  # Skip Storage
```

---

## Performance Tips

### 1. Use Proper Cache Keys

```python
# Good: unique, deterministic
key = f"analyze_security:{symbol}:{period}"

# Bad: not unique, causes collisions
key = f"analysis"
```

### 2. Set Appropriate TTL

```python
# Real-time data: shorter TTL
await cache_mgr.set(key, data, ttl=60)  # 1 minute

# Stable data: longer TTL
await cache_mgr.set(key, data, ttl=3600)  # 1 hour
```

### 3. Schedule Background Refresh on Hits

```python
# Keeps cache fresh without blocking user
if cache_hit := await cache_mgr.get(key, symbol=symbol, tool_name="analyze_security"):
    # Background refresh already scheduled by get()
    return cache_hit.data
```

### 4. Use Symbol Parameter for Multi-Layer Access

```python
# Without symbol: only L1 (Redis) + L2a (Firestore)
await cache_mgr.get(key)

# With symbol: also tries L2b (Storage) + L3 (BigQuery)
await cache_mgr.get(key, symbol="AAPL")  # Much better!
```

---

## Testing

### Local Development

```bash
# Test with local Redis
export REDIS_HOST=localhost
export REDIS_PORT=6379
export SKIP_GCP_VALIDATION=true

# Run tests
python scripts/test_gcp_cache_workflow.py
```

### Production Verification

```bash
# After deployment to Cloud Run
python scripts/test_gcp_cache_workflow.py

# Should see:
# ✓ L0 Secret Manager: OK
# ✓ L1 Memorystore/Redis: OK
# ✓ L2a Firestore: OK
# ✓ L2b Cloud Storage: OK
# ✓ L3 BigQuery: OK (or "no data" if view not ready)
# ✓ L4 Cloud Tasks: OK
```

---

## Files

**Core Implementation**:
- `src/technical_analysis_mcp/cache/gcp_cache_manager.py` - Main cache class
- `src/technical_analysis_mcp/cache/__init__.py` - Exports

**Configuration**:
- `.env.gcp.template` - Environment template
- `.env.gcp` - Actual values (created by deployment script)

**Scripts**:
- `scripts/deploy_gcp_cache_infrastructure.sh` - Setup all GCP services
- `scripts/test_gcp_cache_workflow.py` - Test all 7 layers

**Documentation**:
- `.claude/rules/GCLOUD_OPTIMIZED_DATA_RETRIEVAL.md` - Full architecture
- `.claude/skills/gcp-cache-integration.md` - This file
- `.claude/skills/gcp-optimized-cache.md` - Quick reference

---

## Status

✅ Production Ready
**Updated**: March 3, 2026
**Version**: 1.0
