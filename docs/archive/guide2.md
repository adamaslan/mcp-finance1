# Technical Analysis: Two Architecture Options

## 🎯 Architecture Comparison

| Feature | **Option 1: 100% Free** | **Option 2: GCP Free Tier Maximized** |
|---------|-------------------------|---------------------------------------|
| **Monthly Cost** | $0 | $0-2 |
| **Storage** | In-memory only | Firestore (1GB free) + Cloud Storage (5GB free) |
| **Compute** | Local only | Cloud Run (2M req/mo free) + Cloud Functions |
| **AI Ranking** | Rule-based | Vertex AI Gemini (free tier) |
| **Caching** | 5-min in-memory | Persistent cache in Firestore |
| **Historical Data** | None | 30 days in Cloud Storage |
| **Screening** | Sequential | Parallel Cloud Functions |
| **Pub/Sub** | None | Yes (10GB/mo free) |
| **Monitoring** | None | Cloud Logging (50GB/mo free) |

---

# 🟢 OPTION 1: 100% FREE (Pure Local)

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   CLAUDE DESKTOP                            │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  │ MCP Protocol
                  │
┌─────────────────▼───────────────────────────────────────────┐
│              MCP SERVER (Local Python)                      │
│                                                             │
│  Components:                                                │
│  • yfinance data fetching                                   │
│  • pandas/numpy calculations                                │
│  • In-memory LRU cache (5 min TTL)                          │
│  • Rule-based signal ranking                                │
│  • All processing local                                     │
│                                                             │
│  No external dependencies                                   │
│  No network calls (except yfinance)                         │
│  No storage costs                                           │
└─────────────────────────────────────────────────────────────┘

Cost: $0 forever
```

## Features

✅ **Instant Analysis**: 2-3 seconds per stock
✅ **No Setup**: Just install and run
✅ **Unlimited Usage**: No quotas or limits
✅ **Works Offline**: Cache for recent requests
✅ **Privacy**: All data stays local

## Limitations

❌ **No Persistence**: Cache clears on restart
❌ **No Historical Tracking**: Can't compare to yesterday
❌ **Sequential Screening**: Slower for 100+ symbols
❌ **Basic Ranking**: Rule-based only (no AI)
❌ **No Monitoring**: Can't track usage patterns

## When to Use

- Personal use only
- Don't need historical data
- Prefer simplicity over features
- Privacy is critical
- Want zero costs forever

---

# 🔵 OPTION 2: GCP FREE TIER MAXIMIZED

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   CLAUDE DESKTOP                            │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  │ MCP Protocol
                  │
┌─────────────────▼───────────────────────────────────────────┐
│              MCP SERVER (Local Bridge)                      │
│  • Handles MCP protocol                                     │
│  • Routes to GCP or local                                   │
│  • Smart caching strategy                                   │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  │ HTTPS
                  │
┌─────────────────▼───────────────────────────────────────────┐
│                     GCP BACKEND                             │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │   Cloud Run API (2M req/mo FREE)                     │  │
│  │   • FastAPI endpoints                                │  │
│  │   • Smart routing                                    │  │
│  │   • Request deduplication                            │  │
│  └────────────┬─────────────────────────────────────────┘  │
│               │                                             │
│  ┌────────────▼─────────────────────────────────────────┐  │
│  │   Firestore (1GB FREE)                               │  │
│  │   • signals/{symbol}/latest (5min cache)             │  │
│  │   • analysis/{symbol}/history (30 days)              │  │
│  │   • universes/sp500 (static lists)                   │  │
│  │   • screener_cache/{criteria_hash} (15min)           │  │
│  └────────────┬─────────────────────────────────────────┘  │
│               │                                             │
│  ┌────────────▼─────────────────────────────────────────┐  │
│  │   Cloud Storage (5GB FREE)                           │  │
│  │   • daily/{date}/{symbol}-data.csv                   │  │
│  │   • signals/{date}/{symbol}-signals.json             │  │
│  │   • reports/weekly/ (summaries)                      │  │
│  └────────────┬─────────────────────────────────────────┘  │
│               │                                             │
│  ┌────────────▼─────────────────────────────────────────┐  │
│  │   Pub/Sub (10GB/mo FREE)                             │  │
│  │   • analyze-request → Cloud Function                 │  │
│  │   • batch-screen → Parallel processing               │  │
│  │   • rank-signals → AI ranking                        │  │
│  └────────────┬─────────────────────────────────────────┘  │
│               │                                             │
│  ┌────────────▼─────────────────────────────────────────┐  │
│  │   Cloud Functions (2M invoc/mo FREE)                 │  │
│  │   • calculate_indicators()                           │  │
│  │   • detect_signals()                                 │  │
│  │   • parallel_screener() (10 concurrent)              │  │
│  └────────────┬─────────────────────────────────────────┘  │
│               │                                             │
│  ┌────────────▼─────────────────────────────────────────┐  │
│  │   Vertex AI / Gemini (FREE TIER)                     │  │
│  │   • Signal ranking                                   │  │
│  │   • Pattern recognition                              │  │
│  │   • Market insights                                  │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │   Cloud Logging (50GB/mo FREE)                       │  │
│  │   • Request tracking                                 │  │
│  │   • Performance monitoring                           │  │
│  │   • Error alerting                                   │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │   Cloud Scheduler (3 jobs FREE)                      │  │
│  │   • Daily market summary                             │  │
│  │   • Weekly top picks                                 │  │
│  │   • Cache warming                                    │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘

Cost: $0-2/month (within free tiers)
```

## Features

✅ **AI-Powered Ranking**: Gemini ranks all signals
✅ **Persistent Cache**: Analysis stored for 30 days
✅ **Historical Tracking**: Compare today vs yesterday
✅ **Parallel Screening**: 10x faster for large universes
✅ **Automated Reports**: Daily summaries via Scheduler
✅ **Monitoring**: Track usage and performance
✅ **Scalable**: Handles burst traffic
✅ **Smart Routing**: Local for simple, GCP for complex

## Free Tier Allocations

### Cloud Run (Always Free)
- **2M requests/month** = 66k/day = 2,750/hour
- **360k vCPU-seconds** = 100 hours compute/month
- **1GB network egress**

### Firestore (Always Free)
- **1GB storage**
- **50k document reads/day** = 1.5M/month
- **20k document writes/day** = 600k/month
- **20k document deletes/day**

### Cloud Storage (Always Free)
- **5GB storage**
- **5GB egress/month**
- **5k Class A operations/month** (writes)
- **50k Class B operations/month** (reads)

### Cloud Functions (Always Free)
- **2M invocations/month**
- **400k GB-seconds compute**
- **200k GHz-seconds compute**
- **5GB egress/month**

### Pub/Sub (Always Free)
- **10GB messages/month**

### Vertex AI Gemini (Free Tier)
- **Varies by region**
- **Rate limits apply**
- **Generous free quota**

### Cloud Logging (Always Free)
- **50GB logs/month**

### Cloud Scheduler (Always Free)
- **3 jobs**

## Staying Within Free Tier

### Request Distribution Strategy

```
Total requests/month target: 50k (well below 2M limit)
├── Simple queries (80%): 40k → Local cache hit
├── Medium queries (15%): 7.5k → Firestore cache hit  
└── Complex queries (5%): 2.5k → Full GCP pipeline
```

### Storage Strategy

```
Firestore (1GB limit):
├── Hot cache (5min): ~100 symbols × 50KB = 5MB
├── Daily cache (24h): ~500 symbols × 50KB = 25MB
├── Historical (30d): ~500 symbols × 50KB × 30 = 750MB
└── Metadata: ~50MB
Total: ~830MB (83% of limit)
```

### Compute Budget

```
Cloud Run (360k vCPU-sec/mo):
├── 50k requests × 0.5 sec avg = 25k vCPU-sec
└── Safety margin: 93% remaining
```

## Advanced Features

### 1. Historical Comparison

```python
# Store daily snapshots
@app.get("/api/compare-history/{symbol}")
async def compare_history(symbol: str, days: int = 7):
    """Compare today's signals vs past week"""
    
    today = await get_analysis(symbol)
    history = []
    
    for i in range(1, days + 1):
        date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
        doc = db.collection("analysis").document(symbol).collection("history").document(date).get()
        if doc.exists:
            history.append(doc.to_dict())
    
    return {
        "symbol": symbol,
        "current": today,
        "history": history,
        "trend": calculate_trend(today, history)
    }
```

### 2. Parallel Screening

```python
# Cloud Function: parallel_screener
from concurrent.futures import ThreadPoolExecutor

def parallel_screener(event, context):
    """Screen 100+ symbols in parallel"""
    data = json.loads(base64.b64decode(event['data']))
    symbols = data['symbols']  # e.g., all S&P 500
    criteria = data['criteria']
    
    def analyze_one(symbol):
        # Trigger analysis via Pub/Sub
        publisher.publish(
            topic_path,
            data=json.dumps({"symbol": symbol}).encode()
        )
    
    # Process 10 at a time
    with ThreadPoolExecutor(max_workers=10) as executor:
        executor.map(analyze_one, symbols)
```

### 3. Scheduled Reports

```python
# Cloud Function: daily_summary (triggered by Cloud Scheduler)
def daily_summary(request):
    """Generate daily market summary"""
    
    # Get top movers
    symbols = ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA"]
    analyses = []
    
    for symbol in symbols:
        doc = db.collection("signals").document(symbol).get()
        if doc.exists:
            analyses.append(doc.to_dict())
    
    # Generate summary
    summary = {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "top_bullish": sorted(analyses, key=lambda x: x['summary']['bullish'], reverse=True)[:3],
        "top_bearish": sorted(analyses, key=lambda x: x['summary']['bearish'], reverse=True)[:3],
        "market_sentiment": calculate_sentiment(analyses)
    }
    
    # Save to Cloud Storage
    bucket = storage_client.bucket(BUCKET_NAME)
    blob = bucket.blob(f"reports/daily/{summary['date']}-summary.json")
    blob.upload_from_string(json.dumps(summary, indent=2))
    
    return summary
```

### 4. AI Signal Ranking

```python
# Cloud Function: rank_signals_ai
from google.cloud import aiplatform
from vertexai.preview.generative_models import GenerativeModel

def rank_signals_ai(event, context):
    """Use Gemini to rank signals"""
    data = json.loads(base64.b64decode(event['data']))
    symbol = data['symbol']
    signals = data['signals']
    
    # Initialize Gemini
    model = GenerativeModel("gemini-2.0-flash-exp")
    
    prompt = f"""
    Expert technical analyst scoring signals for {symbol}.
    
    Score each 1-100 based on:
    - Actionability (can trade on this?)
    - Reliability (historical accuracy)
    - Timing (relevant now?)
    - Risk/reward
    
    Signals:
    {json.dumps(signals, indent=2)}
    
    Return ONLY JSON:
    {{"scores": [{{"signal_number": 1, "score": 85, "reasoning": "..."}}]}}
    """
    
    response = model.generate_content(prompt)
    scores = json.loads(response.text)
    
    # Update Firestore
    for score_item in scores['scores']:
        sig_idx = score_item['signal_number'] - 1
        signals[sig_idx]['ai_score'] = score_item['score']
        signals[sig_idx]['ai_reasoning'] = score_item['reasoning']
    
    # Save ranked signals
    db.collection("signals").document(symbol).set({
        "signals": signals,
        "timestamp": datetime.now(),
        "ranked_by": "gemini-2.0"
    })
```

### 5. Smart Caching Strategy

```python
# MCP Server: Intelligent routing
async def analyze_security(symbol: str, period: str = "1mo"):
    """Smart routing: local cache → Firestore → GCP → yfinance"""
    
    # Level 1: Local in-memory cache (instant)
    cache_key = f"{symbol}:{period}"
    if cache_key in LOCAL_CACHE:
        logger.info(f"✅ L1 cache hit: {symbol}")
        return LOCAL_CACHE[cache_key]
    
    # Level 2: Firestore cache (fast, persistent)
    doc = db.collection("signals").document(symbol).get()
    if doc.exists and is_cache_valid(doc.to_dict(), ttl=300):
        logger.info(f"✅ L2 cache hit: {symbol}")
        data = doc.to_dict()
        LOCAL_CACHE[cache_key] = data
        return data
    
    # Level 3: GCP full pipeline (AI ranking)
    logger.info(f"🔄 L3 cache miss: {symbol} - triggering GCP")
    
    # Trigger async analysis
    response = await call_cloud_run_api(
        endpoint="/api/analyze",
        data={"symbol": symbol, "period": period, "use_ai": True}
    )
    
    return response
```

## Implementation Files

### File Structure

```
technical-analysis-mcp/
├── option1-free/                    # 100% Free version
│   ├── src/
│   │   └── technical_analysis_mcp/
│   │       └── server.py            # Pure local MCP server
│   └── pyproject.toml
│
├── option2-gcp/                     # GCP Free Tier version
│   ├── mcp-server/                  # Local MCP bridge
│   │   ├── src/
│   │   │   └── technical_analysis_mcp/
│   │   │       ├── server.py        # MCP server with GCP client
│   │   │       └── gcp_client.py    # GCP API client
│   │   └── pyproject.toml
│   │
│   ├── cloud-run/                   # Cloud Run API
│   │   ├── main.py                  # FastAPI application
│   │   ├── requirements.txt
│   │   └── Dockerfile
│   │
│   ├── cloud-functions/             # Cloud Functions
│   │   ├── calculate_indicators/
│   │   │   ├── main.py
│   │   │   └── requirements.txt
│   │   ├── detect_signals/
│   │   │   ├── main.py
│   │   │   └── requirements.txt
│   │   ├── rank_signals_ai/
│   │   │   ├── main.py
│   │   │   └── requirements.txt
│   │   ├── parallel_screener/
│   │   │   ├── main.py
│   │   │   └── requirements.txt
│   │   └── daily_summary/
│   │       ├── main.py
│   │       └── requirements.txt
│   │
│   ├── terraform/                   # Infrastructure as Code
│   │   ├── main.tf
│   │   ├── firestore.tf
│   │   ├── cloud-run.tf
│   │   ├── cloud-functions.tf
│   │   ├── pubsub.tf
│   │   └── scheduler.tf
│   │
│   └── scripts/
│       ├── deploy.sh                # One-click deployment
│       ├── init-firestore.py        # Initialize Firestore
│       └── setup-scheduler.sh       # Setup Cloud Scheduler
│
└── README.md                        # Choose your adventure
```

## Cost Monitoring

### Daily Quotas (GCP Free Tier)

```python
# scripts/check_quotas.py

from google.cloud import monitoring_v3
from datetime import datetime, timedelta

def check_free_tier_usage():
    """Check usage against free tier limits"""
    
    client = monitoring_v3.MetricServiceClient()
    project_name = f"projects/{PROJECT_ID}"
    
    # Check Cloud Run requests
    interval = monitoring_v3.TimeInterval({
        "end_time": {"seconds": int(time.time())},
        "start_time": {"seconds": int((datetime.now() - timedelta(days=1)).timestamp())}
    })
    
    results = client.list_time_series(
        request={
            "name": project_name,
            "filter": 'metric.type="run.googleapis.com/request_count"',
            "interval": interval,
        }
    )
    
    daily_requests = sum(point.value.int64_value for result in results for point in result.points)
    
    print(f"""
    📊 Free Tier Usage (Last 24h):
    
    Cloud Run:
    • Requests: {daily_requests:,} / 66,666 daily ({daily_requests/666.66:.1f}%)
    • Status: {'✅ Safe' if daily_requests < 50000 else '⚠️  High'}
    
    Firestore:
    • Reads: {get_firestore_reads():,} / 50,000 daily
    • Writes: {get_firestore_writes():,} / 20,000 daily
    
    Cloud Storage:
    • Usage: {get_storage_usage():.2f} GB / 5 GB
    
    Recommendations:
    {get_recommendations(daily_requests)}
    """)

def get_recommendations(requests):
    if requests > 50000:
        return "⚠️  Consider adding more local caching"
    elif requests > 30000:
        return "💡 Usage is moderate, monitor trends"
    else:
        return "✅ Well within free tier limits"
```

## Deployment

### Option 1: 100% Free (5 minutes)

```bash
# Clone and install
git clone <repo>
cd technical-analysis-mcp/option1-free
pip install -e .

# Configure Claude Desktop
cat >> ~/Library/Application\ Support/Claude/claude_desktop_config.json <<EOF
{
  "mcpServers": {
    "technical-analysis": {
      "command": "python",
      "args": ["-m", "technical_analysis_mcp.server"]
    }
  }
}
EOF

# Restart Claude Desktop
# Done! ✅
```

### Option 2: GCP Free Tier (30 minutes)

```bash
# Clone
git clone <repo>
cd technical-analysis-mcp/option2-gcp

# Setup GCP project
gcloud projects create technical-analysis-prod
gcloud config set project technical-analysis-prod

# Enable APIs
gcloud services enable \
  run.googleapis.com \
  cloudfunctions.googleapis.com \
  firestore.googleapis.com \
  storage.googleapis.com \
  pubsub.googleapis.com \
  aiplatform.googleapis.com \
  cloudscheduler.googleapis.com

# Deploy using Terraform
cd terraform
terraform init
terraform apply -auto-approve

# Initialize Firestore
python ../scripts/init-firestore.py

# Setup Cloud Scheduler
bash ../scripts/setup-scheduler.sh

# Install MCP server
cd ../mcp-server
pip install -e .

# Configure with GCP endpoint
export CLOUD_RUN_URL=$(gcloud run services describe technical-analysis-api --format='value(status.url)')

cat >> ~/Library/Application\ Support/Claude/claude_desktop_config.json <<EOF
{
  "mcpServers": {
    "technical-analysis": {
      "command": "python",
      "args": ["-m", "technical_analysis_mcp.server"],
      "env": {
        "CLOUD_RUN_URL": "$CLOUD_RUN_URL",
        "USE_GCP": "true"
      }
    }
  }
}
EOF

# Restart Claude Desktop
# Done! ✅
```

## Feature Comparison

| Feature | Option 1 (Free) | Option 2 (GCP) |
|---------|-----------------|----------------|
| **Setup Time** | 5 min | 30 min |
| **Monthly Cost** | $0 | $0-2 |
| **Analysis Speed** | 2-3 sec | 1-2 sec (cached) |
| **Cache Duration** | 5 min | 30 days |
| **Historical Data** | ❌ | ✅ 30 days |
| **AI Ranking** | ❌ | ✅ Gemini |
| **Parallel Screening** | ❌ | ✅ 10x faster |
| **Daily Reports** | ❌ | ✅ Automated |
| **Monitoring** | ❌ | ✅ Full logs |
| **Scalability** | Local limits | 2M req/mo |
| **Offline Mode** | ✅ (cached) | ❌ (needs GCP) |
| **Privacy** | ✅ 100% local | ⚠️  Data in GCP |

## Which Should You Choose?

### Choose Option 1 (100% Free) if:
- ✅ You want **zero costs forever**
- ✅ You value **simplicity** over features
- ✅ You don't need **historical tracking**
- ✅ **Privacy** is critical
- ✅ You're okay with **rule-based** ranking
- ✅ You analyze **<50 symbols/day**

### Choose Option 2 (GCP Free Tier) if:
- ✅ You want **AI-powered** insights
- ✅ You need **historical comparisons**
- ✅ You screen **100+ symbols** frequently
- ✅ You want **automated daily reports**
- ✅ You like **monitoring** and **optimization**
- ✅ You might **scale up** later
- ✅ You're comfortable with **GCP** (still free!)

## Next Steps

I can now create:

1. **Complete Option 1** (100% Free)
   - Full server.py with 150+ signals
   - Installation script
   - Testing suite

2. **Complete Option 2** (GCP Free Tier)
   - MCP server with GCP client
   - Cloud Run API
   - All Cloud Functions
   - Terraform deployment
   - Monitoring dashboard

Which would you like me to build first?