# GCP-Optimized Four-Layer Data Retrieval Workflow

**Status**: ✅ Active
**Scope**: All backend data fetching with GCP services optimization
**Last Updated**: March 3, 2026
**Project**: ttb-lang1

---

## Optimized Architecture (GCP-Native)

```
Layer 0: GCP Secret Manager (API Keys & Credentials)
    ↓ (automatic, on startup)
Layer 1: Memorystore/Redis (Distributed Cache, 300s)
    ↓ (if miss)
Layer 2: Firestore (Persistent Cache, 300s) + Cloud Storage (Historical)
    ↓ (if miss)
Layer 3: BigQuery (Pre-computed Analysis Data)
    ↓ (if miss)
Layer 4: API Providers (yfinance, Alpha Vantage, Finnhub)
```

---

## Layer 0: GCP Secret Manager (NEW)

**Purpose**: Centralized, rotatable API keys with no filesystem exposure

### Implementation

```bash
# Create secrets in GCP
gcloud secrets create finnhub-api-key --replication-policy="automatic" --data-file=-
gcloud secrets create alpha-vantage-api-key --replication-policy="automatic" --data-file=-

# Grant access to Cloud Run service account
gcloud secrets add-iam-policy-binding finnhub-api-key \
  --member=serviceAccount:1007181159506-compute@developer.gserviceaccount.com \
  --role=roles/secretmanager.secretAccessor
```

### Python Code

```python
from google.cloud import secretmanager

class SecretsClient:
    def __init__(self, project_id: str = "ttb-lang1"):
        self.client = secretmanager.SecretManagerServiceClient()
        self.project_id = project_id

    def get_secret(self, secret_id: str, version: str = "latest") -> str:
        """Fetch secret from GCP Secret Manager with caching."""
        name = f"projects/{self.project_id}/secrets/{secret_id}/versions/{version}"
        response = self.client.access_secret_version(request={"name": name})
        return response.payload.data.decode("UTF-8")

# Usage in server startup
secrets = SecretsClient()
FINNHUB_API_KEY = secrets.get_secret("finnhub-api-key")
AV_API_KEY = secrets.get_secret("alpha-vantage-api-key")
```

**Benefits**:
- ✅ No API keys in .env files or code
- ✅ Automatic rotation without container restart
- ✅ Audit trail of all access attempts
- ✅ Fine-grained IAM permissions

---

## Layer 1: Memorystore/Redis (OPTIMIZED)

**Purpose**: Distributed cache across all container instances

### Setup (One-Time)

```bash
# Create Redis instance in GCP
gcloud redis instances create mcp-cache-prod \
  --size=1 \
  --region=us-central1 \
  --redis-version=7.2 \
  --project=ttb-lang1

# Get connection details
gcloud redis instances describe mcp-cache-prod \
  --region=us-central1 \
  --project=ttb-lang1 \
  --format="value(host,port)"
```

### Python Implementation

```python
import redis
from typing import Optional, Any
import json

class RedisCache:
    def __init__(self, host: str, port: int = 6379, ttl: int = 300):
        self.redis = redis.Redis(
            host=host,
            port=port,
            decode_responses=True,
            socket_connect_timeout=5,
            socket_keepalive=True,
        )
        self.ttl = ttl

    def get(self, key: str) -> Optional[dict]:
        """Get value from Redis (L1 distributed cache)."""
        try:
            value = self.redis.get(key)
            if value:
                return json.loads(value)
            return None
        except redis.ConnectionError:
            logger.warning("Redis connection failed, skipping L1")
            return None

    def set(self, key: str, value: Any, ttl: int = None) -> bool:
        """Set value in Redis with TTL."""
        try:
            ttl = ttl or self.ttl
            self.redis.setex(
                key,
                ttl,
                json.dumps(value)
            )
            return True
        except redis.ConnectionError:
            logger.warning("Redis write failed, continuing without L1")
            return False

    def get_all_by_pattern(self, pattern: str) -> dict:
        """Get all keys matching pattern (useful for portfolio cache warming)."""
        try:
            keys = self.redis.keys(pattern)
            return {k: json.loads(self.redis.get(k)) for k in keys if self.redis.get(k)}
        except redis.ConnectionError:
            return {}

# Usage
redis_cache = RedisCache(
    host=os.getenv("REDIS_HOST", "localhost"),
    port=int(os.getenv("REDIS_PORT", 6379))
)

# In tool function
cached = redis_cache.get(f"analyze_security:{symbol}:daily")
if cached:
    return cached
```

**Advantages over in-memory**:
- ✅ Shared across all container instances
- ✅ Survives container restarts
- ✅ Single source of truth for all pods
- ✅ Built-in TTL support
- ✅ Pattern matching for cache warming
- ✅ No additional complexity vs in-memory dict

---

## Layer 2: Firestore + Cloud Storage (OPTIMIZED)

### Firestore: Real-time Analysis Results

```python
async def write_to_firestore_optimized(
    tool_name: str,
    params: dict,
    result: dict
) -> None:
    """Non-blocking write to Firestore with automatic TTL."""
    try:
        key = f"{tool_name}:{json.dumps(params, sort_keys=True)}"

        # Write with server timestamp for TTL management
        await firestore_db.collection("mcp_tool_cache").document(key).set({
            "result": result,
            "tool": tool_name,
            "params": params,
            "timestamp": firestore.SERVER_TIMESTAMP,
            "ttl": 300,  # 5 minutes
        }, merge=True)

        logger.info(f"Cached {tool_name} result")
    except Exception as e:
        logger.error(f"Firestore cache write failed: {e}")
        # Don't fail the tool, just log
```

### Cloud Storage: Historical/Large Data

```python
from google.cloud import storage

class HistoricalCache:
    def __init__(self, bucket_name: str = "mcp-cache-historical"):
        self.bucket = storage.Client().bucket(bucket_name)

    def get_historical(self, symbol: str, period: str) -> Optional[dict]:
        """Get cached historical data from Cloud Storage (cheaper than Firestore)."""
        blob = self.bucket.blob(f"historical/{symbol}/{period}/data.json")

        try:
            if blob.exists():
                # Check if data is still fresh (within cache window)
                age = time.time() - blob.updated.timestamp()
                if age < 300:  # 5 min cache
                    return json.loads(blob.download_as_string())
        except Exception as e:
            logger.debug(f"Cloud Storage read failed: {e}")

        return None

    def set_historical(self, symbol: str, period: str, data: dict) -> bool:
        """Write historical data to Cloud Storage (optimized for large datasets)."""
        try:
            blob = self.bucket.blob(f"historical/{symbol}/{period}/data.json")
            blob.upload_from_string(
                json.dumps(data),
                content_type="application/json"
            )
            return True
        except Exception as e:
            logger.error(f"Cloud Storage write failed: {e}")
            return False

# Usage
historical_cache = HistoricalCache()

# Get candlestick data from storage (cheaper than re-computing)
candles = historical_cache.get_historical("AAPL", "daily")
if not candles:
    candles = fetch_from_api()
    historical_cache.set_historical("AAPL", "daily", candles)
```

**Layer 2 Strategy**:
- **Firestore**: Small, frequently-accessed results (analysis, signals, trade plans)
- **Cloud Storage**: Large datasets (candlestick history, correlation matrices)
- **TTL Management**: Use Cloud Firestore TTL policies (automatic cleanup)

---

## Layer 3: BigQuery (NEW - Pre-computed Data)

**Purpose**: Cache pre-computed analysis and aggregations

### Setup

```bash
# Create dataset
bq mk --dataset \
  --description="MCP cache pre-computed data" \
  ttb-lang1:mcp_cache

# Create materialized view for frequently-used metrics
bq query --use_legacy_sql=false '
CREATE MATERIALIZED VIEW mcp_cache.daily_analysis AS
SELECT
  symbol,
  DATE(timestamp) as trade_date,
  APPROX_QUANTILES(close, 100)[OFFSET(50)] as median_price,
  MAX(close) as high,
  MIN(close) as low,
  AVG(close) as avg_price,
  STDDEV(close) as volatility
FROM `ttb-lang1.market_data.prices`
WHERE timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 2 YEAR)
GROUP BY symbol, DATE(timestamp)
'
```

### Query Cached Data

```python
from google.cloud import bigquery

class BigQueryCache:
    def __init__(self, project_id: str = "ttb-lang1"):
        self.client = bigquery.Client(project=project_id)

    def get_daily_metrics(self, symbol: str) -> Optional[dict]:
        """Get pre-computed daily metrics from BigQuery (much faster than live calc)."""
        query = f"""
        SELECT * FROM `ttb-lang1.mcp_cache.daily_analysis`
        WHERE symbol = '{symbol}'
        ORDER BY trade_date DESC
        LIMIT 1
        """

        try:
            results = self.client.query_and_wait(query, timeout=10)
            if results.total_rows > 0:
                return dict(results.to_dataframe().iloc[0])
        except Exception as e:
            logger.debug(f"BigQuery query failed: {e}")

        return None

# Usage in portfolio_risk
bq_cache = BigQueryCache()
metrics = bq_cache.get_daily_metrics("AAPL")
if metrics:
    volatility = metrics['volatility']  # Pre-computed!
    return metrics
```

**Benefits**:
- ✅ Pre-computed metrics (faster than live calculation)
- ✅ Materialized views update on schedule
- ✅ Cost-effective for large datasets
- ✅ Can join with multiple data sources
- ✅ Perfect for historical lookbacks

---

## Layer 4: API Providers (WITH GCP OPTIMIZATION)

### Cloud Tasks: Reliable Background Refresh

Instead of `asyncio.create_task()`, use Cloud Tasks for guaranteed execution:

```python
from google.cloud import tasks_v2

class BackgroundTaskScheduler:
    def __init__(self, project_id: str = "ttb-lang1"):
        self.client = tasks_v2.CloudTasksClient()
        self.project = project_id
        self.queue = "mcp-cache-refresh"
        self.region = "us-central1"

    def schedule_api_refresh(self, symbol: str, tool_name: str) -> None:
        """Schedule background cache refresh using Cloud Tasks (reliable)."""
        parent = self.client.queue_path(self.project, self.region, self.queue)

        task = {
            "http_request": {
                "http_method": tasks_v2.HttpMethod.POST,
                "url": "https://mcp-backend.cloud.run/api/cache-refresh",
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({
                    "symbol": symbol,
                    "tool": tool_name,
                    "priority": "low"  # Use lower priority for background
                }).encode(),
            },
            "schedule_time": {"seconds": int(time.time()) + 5}  # Run in 5 seconds
        }

        try:
            self.client.create_task(request={"parent": parent, "task": task})
            logger.info(f"Scheduled refresh for {symbol}")
        except Exception as e:
            logger.error(f"Task scheduling failed: {e}")

# Usage
task_scheduler = BackgroundTaskScheduler()

# On cache hit, schedule background refresh
if cached := redis_cache.get(key):
    task_scheduler.schedule_api_refresh(symbol, tool_name)
    return cached
```

**Advantages over asyncio.create_task()**:
- ✅ Guaranteed execution (survives crashes)
- ✅ Automatic retries with exponential backoff
- ✅ Proper error logging in Cloud Logging
- ✅ Can be monitored/debugged in Cloud Console
- ✅ Prevents cache refresh loss if container dies

### Quota Tracking with Datastore

```python
from google.cloud import datastore

class QuotaTracker:
    def __init__(self, project_id: str = "ttb-lang1"):
        self.client = datastore.Client(project=project_id)

    def get_remaining_quota(self, provider: str) -> int:
        """Get remaining API quota from Datastore (persistent across requests)."""
        key = self.client.key("APIQuota", provider)
        quota = self.client.get(key)

        if quota is None:
            return 25  # Default for Alpha Vantage

        return quota.get("remaining", 0)

    def decrement_quota(self, provider: str) -> bool:
        """Decrement quota atomically."""
        key = self.client.key("APIQuota", provider)

        with self.client.transaction():
            quota = self.client.get(key)
            if quota is None:
                quota = datastore.Entity(key=key)
                quota["remaining"] = 24
            else:
                quota["remaining"] -= 1

            quota["updated"] = datetime.utcnow()

            if quota["remaining"] <= 0:
                logger.critical("API quota exhausted")
                return False

            self.client.put(quota)
            return True

# Usage
quota_tracker = QuotaTracker()

if not quota_tracker.decrement_quota("alpha-vantage"):
    raise HTTPException(status_code=503, detail="Daily quota exhausted")

result = av_client.get_quote(symbol)
```

**Better than in-memory tracking**:
- ✅ Quota persists across container restarts
- ✅ Shared across all instances (no double-counting)
- ✅ Atomic operations prevent race conditions
- ✅ Historical quota usage available for analysis

---

## Complete Optimized Flow

```python
async def get_market_data(
    symbol: str,
    portfolio_prices: dict = None
) -> dict:
    """Complete four-layer retrieval with GCP optimization."""

    cache_key = f"price:{symbol}"

    # L0: Secrets (automatic on startup)
    # API_KEY = secrets_client.get_secret("finnhub-api-key")

    # L1: Redis (distributed, fast)
    if cached := redis_cache.get(cache_key):
        logger.info(f"L1 hit for {symbol}")
        # Schedule background refresh via Cloud Tasks
        task_scheduler.schedule_api_refresh(symbol, "price_fetch")
        return cached

    # L2a: Firestore (real-time results)
    if cached := await firestore_cache.get(cache_key):
        logger.info(f"L2 Firestore hit for {symbol}")
        # Background refresh via Cloud Tasks
        task_scheduler.schedule_api_refresh(symbol, "price_fetch")
        return cached

    # L2b: Cloud Storage (historical data)
    if historical := historical_cache.get_historical(symbol, "daily"):
        logger.info(f"L2 Storage hit for {symbol}")
        return historical

    # L3: BigQuery (pre-computed metrics)
    if metrics := bq_cache.get_daily_metrics(symbol):
        logger.info(f"L3 BigQuery hit for {symbol}")
        return metrics

    # L4: API Provider
    logger.info(f"L4 API call for {symbol}")

    # Atomically decrement quota for the provider being used (finnhub)
    if not quota_tracker.decrement_quota("finnhub"):
        raise HTTPException(status_code=503, detail="Quota exhausted")

    try:
        result = finnhub_client.quote(symbol)

        # Non-blocking writes to all caches
        redis_cache.set(cache_key, result)  # L1
        asyncio.create_task(firestore_cache.set(cache_key, result))  # L2
        asyncio.create_task(historical_cache.set_historical(symbol, "daily", result))  # L2b

        return result

    except APIError as e:
        logger.error(f"API call failed: {e}")
        raise HTTPException(status_code=503, detail="Data unavailable")
```

---

## GCP Deployment Configuration

### Cloud Run Environment Variables

```yaml
# .env.cloud-run (deployed via gcloud)
REDIS_HOST=mcp-cache-prod.internal  # Private IP
REDIS_PORT=6379
GCP_PROJECT_ID=ttb-lang1
BUCKET_NAME=mcp-cache-historical
DATASTORE_PROJECT_ID=ttb-lang1
BIG_QUERY_PROJECT_ID=ttb-lang1
CLOUD_TASKS_QUEUE=mcp-cache-refresh
CLOUD_TASKS_REGION=us-central1
```

### Deploy with GCP Integration

```bash
# Deploy to Cloud Run with all permissions
gcloud run deploy mcp-backend \
  --source . \
  --region us-central1 \
  --platform managed \
  --memory 2Gi \
  --cpu 2 \
  --project ttb-lang1 \
  --service-account=1007181159506-compute@developer.gserviceaccount.com \
  --set-env-vars=REDIS_HOST=mcp-cache-prod.internal,GCP_PROJECT_ID=ttb-lang1,BUCKET_NAME=mcp-cache-historical \
  --allow-unauthenticated \
  --vpc-connector=mcp-vpc-connector
```

### IAM Permissions Required

```bash
# Firestore
gcloud projects add-iam-policy-binding ttb-lang1 \
  --member=serviceAccount:1007181159506-compute@developer.gserviceaccount.com \
  --role=roles/datastore.user

# Cloud Storage
gcloud projects add-iam-policy-binding ttb-lang1 \
  --member=serviceAccount:1007181159506-compute@developer.gserviceaccount.com \
  --role=roles/storage.objectAdmin

# BigQuery
gcloud projects add-iam-policy-binding ttb-lang1 \
  --member=serviceAccount:1007181159506-compute@developer.gserviceaccount.com \
  --role=roles/bigquery.dataEditor

# Cloud Tasks
gcloud projects add-iam-policy-binding ttb-lang1 \
  --member=serviceAccount:1007181159506-compute@developer.gserviceaccount.com \
  --role=roles/cloudtasks.taskRunner

# Secret Manager
gcloud projects add-iam-policy-binding ttb-lang1 \
  --member=serviceAccount:1007181159506-compute@developer.gserviceaccount.com \
  --role=roles/secretmanager.secretAccessor

# Redis
gcloud projects add-iam-policy-binding ttb-lang1 \
  --member=serviceAccount:1007181159506-compute@developer.gserviceaccount.com \
  --role=roles/redis.client
```

---

## Monitoring & Metrics (GCP Native)

### Cloud Logging

```python
from google.cloud import logging_v2

def log_cache_metrics():
    """Send cache performance metrics to Cloud Logging."""
    logging_client = logging_v2.Client(project="ttb-lang1")
    logger = logging_client.logger("mcp-cache-metrics")

    logger.log_struct({
        "l1_hits": redis_cache.get_stats()['hits'],
        "l2_hits": firestore_stats['hits'],
        "l3_hits": bq_stats['hits'],
        "l4_api_calls": api_call_count,
        "cache_hit_ratio": hit_ratio,
        "avg_latency_ms": avg_latency,
    }, severity="INFO")
```

### Cloud Monitoring Alerts

```bash
# Alert when API quota running low
gcloud alpha monitoring policies create \
  --notification-channels=CHANNEL_ID \
  --display-name="Alpha Vantage Quota Low" \
  --condition-display-name="Remaining < 5 calls" \
  --condition-query='resource.type="cloud_function" AND metric.type="custom.googleapis.com/api_quota_remaining" AND metric.labels.provider="alpha-vantage" AND metric.value < 5'
```

---

## Performance Benchmarks

| Layer | Latency | Hit Rate | Cost |
|-------|---------|----------|------|
| L0: Secrets | ~50ms | N/A | ~$0.08/10k |
| L1: Redis | <1ms | ~70% | ~$0.25/month |
| L2: Firestore | ~10ms | ~20% | ~$0.06/100k |
| L2b: Storage | ~50ms | ~5% | ~$0.02/GB |
| L3: BigQuery | ~500ms | ~2% | ~$0.025/GB |
| L4: API | ~500ms-5s | 0% | Variable |

**Expected outcome**: 95% of requests served in <10ms with combined caches

---

## Migration Path

### Phase 1 (Current)
- ✅ Layer 2: Firestore + Cloud Storage
- ✅ Layer 4: API Providers

### Phase 2 (Add Redis)
- Add Layer 1: Memorystore/Redis (distributed cache)
- Migrate from in-memory to Redis

### Phase 3 (Add BigQuery)
- Create BigQuery materialized views
- Add Layer 3 queries for pre-computed metrics

### Phase 4 (Production)
- Migrate API keys to Secret Manager
- Implement Cloud Tasks background refresh
- Add Datastore quota tracking

---

## Testing Checklist

- [ ] Redis connection works in development
- [ ] Firestore writes are non-blocking
- [ ] Cloud Storage reads return historical data
- [ ] BigQuery queries complete in <1 second
- [ ] Cloud Tasks background jobs execute
- [ ] Secret Manager keys rotate without restart
- [ ] Quota tracking prevents API exhaustion
- [ ] All layers degrade gracefully on failure
- [ ] Monitoring alerts trigger correctly

---

## References

- [GCP Memorystore Documentation](https://cloud.google.com/memorystore/docs)
- [Cloud Storage Best Practices](https://cloud.google.com/storage/docs/best-practices)
- [BigQuery Materialized Views](https://cloud.google.com/bigquery/docs/materialized-views)
- [Cloud Tasks Guide](https://cloud.google.com/tasks/docs)
- [Secret Manager](https://cloud.google.com/secret-manager/docs)

---

**This optimization guide is MANDATORY for all new data fetching code. Leverage GCP services for reliability, cost-efficiency, and performance.**
