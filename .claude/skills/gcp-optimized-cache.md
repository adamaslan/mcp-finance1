# GCP-Optimized Cache Implementation

**Quick reference for using GCP services instead of generic caching**

---

## The GCP Stack (Replace Generic Code)

```
Layer 0: Secret Manager (API Keys)
Layer 1: Memorystore/Redis (Distributed Cache)
Layer 2a: Firestore (Real-time Results)
Layer 2b: Cloud Storage (Historical Data)
Layer 3: BigQuery (Pre-computed Metrics)
Layer 4: API Providers
```

---

## Layer 0: API Keys from Secret Manager

❌ **WRONG** - Keys in .env
```python
FINNHUB_KEY = os.getenv("FINNHUB_API_KEY")  # From .env file
```

✅ **RIGHT** - Keys from GCP Secret Manager
```python
from google.cloud import secretmanager

def get_api_key(key_name: str) -> str:
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/ttb-lang1/secrets/{key_name}/versions/latest"
    return client.access_secret_version(request={"name": name}).payload.data.decode("UTF-8")

FINNHUB_KEY = get_api_key("finnhub-api-key")
```

**Setup (one-time)**:
```bash
gcloud secrets create finnhub-api-key --replication-policy=automatic --data-file=-
gcloud secrets add-iam-policy-binding finnhub-api-key \
  --member=serviceAccount:1007181159506-compute@developer.gserviceaccount.com \
  --role=roles/secretmanager.secretAccessor
```

---

## Layer 1: Redis Instead of In-Memory Dict

❌ **WRONG** - In-memory (lost on restart, not shared)
```python
cache = {}  # or TTLCache()
cached = cache.get(key)
```

✅ **RIGHT** - Memorystore/Redis (persistent, shared)
```python
import redis
import json

redis_cache = redis.Redis(host=REDIS_HOST, port=6379, decode_responses=True)

def get_cached(key: str):
    value = redis_cache.get(key)
    return json.loads(value) if value else None

def set_cached(key: str, value: dict, ttl: int = 300):
    redis_cache.setex(key, ttl, json.dumps(value))
```

**Setup (one-time)**:
```bash
gcloud redis instances create mcp-cache-prod --size=1 --region=us-central1
gcloud redis instances describe mcp-cache-prod --region=us-central1 --format="value(host,port)"
```

---

## Layer 2a: Firestore for Real-Time Results

✅ **Always Use** for tool execution results
```python
from google.cloud import firestore

db = firestore.AsyncClient()

async def cache_tool_result(tool_name: str, params: dict, result: dict):
    """Non-blocking write to Firestore."""
    key = f"{tool_name}:{json.dumps(params, sort_keys=True)}"
    await db.collection("mcp_tool_cache").document(key).set({
        "result": result,
        "timestamp": firestore.SERVER_TIMESTAMP,
    }, merge=True)

# Read
doc = await db.collection("mcp_tool_cache").document(key).get()
if doc.exists:
    return doc.get("result")
```

**Cost**: ~$0.06 per 100k reads (very cheap)

---

## Layer 2b: Cloud Storage for Historical Data

✅ **Use for** candlesticks, correlation matrices, large datasets
```python
from google.cloud import storage
import json

bucket = storage.Client().bucket("mcp-cache-historical")

def get_historical(symbol: str, period: str) -> dict:
    blob = bucket.blob(f"historical/{symbol}/{period}/data.json")
    if blob.exists():
        return json.loads(blob.download_as_string())
    return None

def set_historical(symbol: str, period: str, data: dict):
    blob = bucket.blob(f"historical/{symbol}/{period}/data.json")
    blob.upload_from_string(json.dumps(data))
```

**Cost**: ~$0.02 per GB (much cheaper than Firestore for large data)

---

## Layer 3: BigQuery for Pre-Computed Metrics

✅ **Use for** indicators, aggregations, lookbacks
```python
from google.cloud import bigquery

bq = bigquery.Client(project="ttb-lang1")

def get_daily_metrics(symbol: str) -> dict:
    """Get pre-computed volatility, MA, etc."""
    query = f"""
    SELECT * FROM `ttb-lang1.mcp_cache.daily_analysis`
    WHERE symbol = '{symbol}'
    ORDER BY trade_date DESC LIMIT 1
    """
    results = bq.query_and_wait(query)
    if results.total_rows > 0:
        return dict(results.to_dataframe().iloc[0])
    return None
```

**Cost**: ~$0.025 per GB scanned (best for aggregated data)

---

## Layer 4: Cloud Tasks for Background Refresh

❌ **WRONG** - Fire-and-forget (lost if container crashes)
```python
asyncio.create_task(refresh_cache(key))  # Can be lost!
```

✅ **RIGHT** - Cloud Tasks (guaranteed execution)
```python
from google.cloud import tasks_v2
import json

def schedule_refresh(symbol: str, tool: str):
    client = tasks_v2.CloudTasksClient()
    parent = client.queue_path("ttb-lang1", "us-central1", "mcp-cache-refresh")

    task = {
        "http_request": {
            "http_method": tasks_v2.HttpMethod.POST,
            "url": "https://mcp-backend.cloud.run/api/cache-refresh",
            "body": json.dumps({"symbol": symbol, "tool": tool}).encode(),
        }
    }
    client.create_task(request={"parent": parent, "task": task})

# Usage: On cache hit, schedule background refresh
if cached := redis_cache.get(key):
    schedule_refresh(symbol, tool_name)  # Guaranteed to run
    return cached
```

---

## Quota Tracking with Datastore

❌ **WRONG** - In-memory counter (reset on restart)
```python
av_calls = 0
av_calls += 1
if av_calls >= 25:
    raise QuotaError()
```

✅ **RIGHT** - Datastore (persistent, atomic)
```python
from google.cloud import datastore

ds = datastore.Client(project="ttb-lang1")

def check_and_decrement_quota(provider: str) -> bool:
    key = ds.key("APIQuota", provider)

    with ds.transaction():
        quota = ds.get(key)
        if quota is None:
            quota = datastore.Entity(key=key)
            quota["remaining"] = 25

        if quota["remaining"] <= 0:
            return False

        quota["remaining"] -= 1
        ds.put(quota)
        return True

# Usage
if not check_and_decrement_quota("alpha-vantage"):
    raise HTTPException(status_code=503, detail="Quota exhausted")
```

---

## Complete Implementation

```python
async def get_market_data(symbol: str, portfolio_prices: dict = None) -> dict:
    """All four layers with GCP optimization."""

    key = f"price:{symbol}"

    # L1: Redis
    if cached := redis_cache.get(key):
        schedule_refresh(symbol, "price")  # Cloud Tasks
        return cached

    # L2a: Firestore
    doc = await db.collection("mcp_tool_cache").document(key).get()
    if doc.exists:
        schedule_refresh(symbol, "price")
        return doc.get("result")

    # L2b: Cloud Storage
    if historical := get_historical(symbol, "daily"):
        return historical

    # L3: BigQuery
    if metrics := get_daily_metrics(symbol):
        return metrics

    # L4: API
    if not check_and_decrement_quota("finnhub"):
        raise HTTPException(status_code=503, detail="Quota exhausted")

    try:
        result = finnhub_client.quote(symbol)

        # Non-blocking writes to all caches
        redis_cache.setex(key, 300, json.dumps(result))
        await db.collection("mcp_tool_cache").document(key).set({"result": result})
        set_historical(symbol, "daily", result)

        return result
    except Exception as e:
        logger.error(f"API failed: {e}")
        raise HTTPException(status_code=503, detail="Data unavailable")
```

---

## Setup Commands (Copy & Paste)

```bash
# 1. Create Redis
gcloud redis instances create mcp-cache-prod \
  --size=1 --region=us-central1 --project=ttb-lang1

# 2. Create Cloud Storage bucket
gsutil mb gs://mcp-cache-historical

# 3. Create BigQuery dataset
bq mk --dataset --project_id=ttb-lang1 mcp_cache

# 4. Create Cloud Tasks queue
gcloud tasks queues create mcp-cache-refresh \
  --location=us-central1 --project=ttb-lang1

# 5. Grant service account permissions
SA="1007181159506-compute@developer.gserviceaccount.com"

gcloud projects add-iam-policy-binding ttb-lang1 \
  --member=serviceAccount:$SA \
  --role=roles/redis.client

gcloud projects add-iam-policy-binding ttb-lang1 \
  --member=serviceAccount:$SA \
  --role=roles/storage.objectAdmin

gcloud projects add-iam-policy-binding ttb-lang1 \
  --member=serviceAccount:$SA \
  --role=roles/bigquery.dataEditor

gcloud projects add-iam-policy-binding ttb-lang1 \
  --member=serviceAccount:$SA \
  --role=roles/cloudtasks.taskRunner
```

---

## Cost Breakdown

| Service | Usage | Est. Cost |
|---------|-------|-----------|
| Memorystore (1GB) | 1 instance | $0.25/month |
| Firestore | 1M reads | $0.06 |
| Cloud Storage | 100GB | $2/month |
| BigQuery | 1GB queries | $0.025 |
| Cloud Tasks | 10k tasks | $0.40 |
| Secret Manager | 10k accesses | $0.06 |
| **Total** | | **~$3/month** |

Compared to API calls alone: **$100+/month** → **Much cheaper with caching**

---

## When to Use Each Layer

- **L1 (Redis)**: Always first - shared, instant access
- **L2a (Firestore)**: Tool results - fast, flexible queries
- **L2b (Storage)**: Large data - cheap, historical
- **L3 (BigQuery)**: Pre-computed - saves computation
- **L4 (APIs)**: Only if nothing cached

---

## References

- Full guide: `.claude/rules/GCLOUD_OPTIMIZED_DATA_RETRIEVAL.md`
- GCP Memorystore: `gcloud redis instances list`
- Cloud Tasks: `gcloud tasks queues list`
- Firestore: `gcloud firestore indexes list`

---

**Status**: Active | **Updated**: March 3, 2026
