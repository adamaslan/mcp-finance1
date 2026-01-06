# Automating the Technical Analysis Pipeline with GCP & Vertex AI

A cost-optimized guide for running automated stock analysis for **$0-5/month**.

---

## Table of Contents

1. [Cost Comparison](#cost-comparison)
2. [Architecture Options](#architecture-options)
3. [Option A: $0/month - Gemini API Free Tier](#option-a-0month---gemini-api-free-tier)
4. [Option B: $2-5/month - Vertex AI](#option-b-2-5month---vertex-ai)
5. [Step-by-Step Setup](#step-by-step-setup)
6. [Automation Schedules](#automation-schedules)
7. [Cost Monitoring](#cost-monitoring)
8. [Troubleshooting](#troubleshooting)

---

## Cost Comparison

### AI Model Pricing

| Service | Free Tier | Paid Rate | Best For |
|---------|-----------|-----------|----------|
| **Gemini API (AI Studio)** | 60 RPM, 1,500 req/day | $0.075/1M input tokens | Development, low volume |
| **Vertex AI Gemini** | $300 credit (90 days) | $0.075/1M input tokens | Production, enterprise |
| **Vertex AI Gemini Flash** | $300 credit | $0.0375/1M tokens | High volume, cost-sensitive |

### GCP Services Free Tier

| Service | Monthly Free Allowance | Our Usage |
|---------|------------------------|-----------|
| Cloud Functions | 2M invocations, 400K GB-sec | ~1,000 invocations |
| Cloud Run | 2M requests, 360K vCPU-sec | ~500 requests |
| Cloud Scheduler | 3 jobs | 1-3 jobs |
| Firestore | 1 GB storage, 50K reads/day | ~100 reads/day |
| Cloud Storage | 5 GB | ~10 MB |
| Pub/Sub | 10 GB/month | ~1 MB |

**Bottom Line**: You can run daily analysis of 50+ stocks for **$0/month** using free tiers.

---

## Architecture Options

### Option A: Minimal ($0/month)
```
Cloud Scheduler → Cloud Function → Gemini API (free)
                       ↓
                  Firestore (results)
```

### Option B: Production ($2-5/month)
```
Cloud Scheduler → Pub/Sub → Cloud Run → Vertex AI Gemini
                                ↓
                           Firestore + Cloud Storage
                                ↓
                           Email/Slack Alerts
```

---

## Option A: $0/month - Gemini API Free Tier

This option uses the free Gemini API from Google AI Studio with Cloud Functions.

### Limits
- 60 requests per minute
- 1,500 requests per day
- 1 million tokens per minute

### What You Can Analyze
- **Daily**: 50 stocks with AI ranking = ~50 API calls
- **Weekly**: Full S&P 500 screening = ~500 API calls
- **Monthly**: ~45,000 API calls available

### Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│ Cloud Scheduler │────▶│ Cloud Function  │────▶│   Gemini API    │
│   (3 free)      │     │  (2M free/mo)   │     │  (1500/day free)│
└─────────────────┘     └────────┬────────┘     └─────────────────┘
                                 │
                                 ▼
                        ┌─────────────────┐
                        │    Firestore    │
                        │  (1GB free)     │
                        └─────────────────┘
```

### Setup Files

#### 1. Cloud Function Code

```python
# functions/daily_analysis/main.py
import functions_framework
from google.cloud import firestore
import google.generativeai as genai
import yfinance as yf
import pandas as pd
import json
import os
from datetime import datetime

# Configuration
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
PROJECT_ID = os.environ.get('GCP_PROJECT_ID')

# Initialize clients
db = firestore.Client(project=PROJECT_ID)
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.0-flash-exp')

# Watchlist - customize this
WATCHLIST = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'MU', 'AMD', 'TSLA', 'META', 'SPY']


def calculate_indicators(df: pd.DataFrame) -> dict:
    """Calculate key technical indicators."""
    close = df['Close']

    # RSI
    delta = close.diff()
    gain = delta.where(delta > 0, 0).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))

    # MACD
    ema12 = close.ewm(span=12).mean()
    ema26 = close.ewm(span=26).mean()
    macd = ema12 - ema26
    signal = macd.ewm(span=9).mean()

    # Moving Averages
    sma20 = close.rolling(20).mean()
    sma50 = close.rolling(50).mean()

    # ADX
    high, low = df['High'], df['Low']
    tr = pd.concat([high - low, abs(high - close.shift()), abs(low - close.shift())], axis=1).max(axis=1)
    atr = tr.rolling(14).mean()

    return {
        'price': float(close.iloc[-1]),
        'change_pct': float((close.iloc[-1] / close.iloc[-2] - 1) * 100),
        'rsi': float(rsi.iloc[-1]),
        'macd': float(macd.iloc[-1]),
        'macd_signal': float(signal.iloc[-1]),
        'sma20': float(sma20.iloc[-1]),
        'sma50': float(sma50.iloc[-1]),
        'volume': int(df['Volume'].iloc[-1]),
        'avg_volume': int(df['Volume'].rolling(20).mean().iloc[-1])
    }


def detect_signals(indicators: dict) -> list:
    """Detect trading signals from indicators."""
    signals = []

    # RSI signals
    if indicators['rsi'] < 30:
        signals.append({'signal': 'RSI Oversold', 'strength': 'BULLISH', 'value': indicators['rsi']})
    elif indicators['rsi'] > 70:
        signals.append({'signal': 'RSI Overbought', 'strength': 'BEARISH', 'value': indicators['rsi']})

    # MACD signals
    if indicators['macd'] > indicators['macd_signal']:
        signals.append({'signal': 'MACD Bullish', 'strength': 'BULLISH', 'value': indicators['macd']})
    else:
        signals.append({'signal': 'MACD Bearish', 'strength': 'BEARISH', 'value': indicators['macd']})

    # Moving average signals
    if indicators['price'] > indicators['sma20'] > indicators['sma50']:
        signals.append({'signal': 'Uptrend (Price > SMA20 > SMA50)', 'strength': 'BULLISH'})
    elif indicators['price'] < indicators['sma20'] < indicators['sma50']:
        signals.append({'signal': 'Downtrend (Price < SMA20 < SMA50)', 'strength': 'BEARISH'})

    # Volume signals
    if indicators['volume'] > indicators['avg_volume'] * 1.5:
        signals.append({'signal': 'High Volume', 'strength': 'SIGNIFICANT', 'value': indicators['volume']})

    return signals


def rank_with_gemini(symbol: str, indicators: dict, signals: list) -> dict:
    """Use Gemini to rank and analyze signals."""
    prompt = f"""Analyze {symbol} technical signals briefly.

INDICATORS:
- Price: ${indicators['price']:.2f} ({indicators['change_pct']:+.2f}%)
- RSI: {indicators['rsi']:.1f}
- MACD: {indicators['macd']:.4f}

SIGNALS:
{json.dumps(signals, indent=2)}

Return JSON only:
{{"score": 1-100, "outlook": "BULLISH/BEARISH/NEUTRAL", "summary": "1 sentence"}}"""

    try:
        response = model.generate_content(prompt)
        text = response.text.strip()

        # Parse JSON from response
        if '```' in text:
            text = text.split('```')[1].replace('json', '').strip()

        start = text.find('{')
        end = text.rfind('}') + 1
        if start >= 0 and end > start:
            return json.loads(text[start:end])
    except Exception as e:
        print(f"Gemini error for {symbol}: {e}")

    return {"score": 50, "outlook": "NEUTRAL", "summary": "AI analysis unavailable"}


def analyze_symbol(symbol: str) -> dict:
    """Complete analysis for a single symbol."""
    try:
        # Fetch data
        ticker = yf.Ticker(symbol)
        df = ticker.history(period='3mo')

        if len(df) < 50:
            return {"error": f"Insufficient data: {len(df)} days"}

        # Calculate indicators
        indicators = calculate_indicators(df)

        # Detect signals
        signals = detect_signals(indicators)

        # AI ranking
        ai_analysis = rank_with_gemini(symbol, indicators, signals)

        return {
            "symbol": symbol,
            "timestamp": datetime.utcnow().isoformat(),
            "indicators": indicators,
            "signals": signals,
            "ai_score": ai_analysis.get("score", 50),
            "ai_outlook": ai_analysis.get("outlook", "NEUTRAL"),
            "ai_summary": ai_analysis.get("summary", "")
        }
    except Exception as e:
        return {"symbol": symbol, "error": str(e)}


@functions_framework.http
def daily_analysis(request):
    """HTTP Cloud Function for daily analysis."""
    results = []

    for symbol in WATCHLIST:
        print(f"Analyzing {symbol}...")
        result = analyze_symbol(symbol)
        results.append(result)

        # Save to Firestore
        if "error" not in result:
            db.collection('analysis').document(symbol).set(result)

    # Save daily summary
    summary = {
        "date": datetime.utcnow().strftime("%Y-%m-%d"),
        "analyzed": len([r for r in results if "error" not in r]),
        "errors": len([r for r in results if "error" in r]),
        "top_bullish": sorted(
            [r for r in results if r.get("ai_outlook") == "BULLISH"],
            key=lambda x: x.get("ai_score", 0),
            reverse=True
        )[:5],
        "top_bearish": sorted(
            [r for r in results if r.get("ai_outlook") == "BEARISH"],
            key=lambda x: x.get("ai_score", 0),
            reverse=True
        )[:5]
    }

    db.collection('summaries').document(summary["date"]).set(summary)

    return json.dumps({"status": "success", "summary": summary}, indent=2)


@functions_framework.cloud_event
def scheduled_analysis(cloud_event):
    """Pub/Sub triggered function for scheduled runs."""
    return daily_analysis(None)
```

#### 2. Requirements

```txt
# functions/daily_analysis/requirements.txt
functions-framework==3.*
google-cloud-firestore==2.*
google-generativeai==0.3.*
yfinance==0.2.*
pandas==2.*
```

#### 3. Terraform Configuration

```hcl
# terraform/main.tf
terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "region" {
  default = "us-central1"
}

variable "gemini_api_key" {
  description = "Gemini API Key"
  type        = string
  sensitive   = true
}

# Enable APIs
resource "google_project_service" "apis" {
  for_each = toset([
    "cloudfunctions.googleapis.com",
    "cloudscheduler.googleapis.com",
    "firestore.googleapis.com",
    "pubsub.googleapis.com",
    "cloudbuild.googleapis.com"
  ])
  service            = each.key
  disable_on_destroy = false
}

# Pub/Sub topic for scheduled triggers
resource "google_pubsub_topic" "daily_trigger" {
  name       = "daily-analysis-trigger"
  depends_on = [google_project_service.apis]
}

# Cloud Function
resource "google_cloudfunctions2_function" "analysis" {
  name     = "daily-stock-analysis"
  location = var.region

  build_config {
    runtime     = "python311"
    entry_point = "scheduled_analysis"
    source {
      storage_source {
        bucket = google_storage_bucket.functions.name
        object = google_storage_bucket_object.function_zip.name
      }
    }
  }

  service_config {
    max_instance_count = 1
    available_memory   = "512Mi"
    timeout_seconds    = 300
    environment_variables = {
      GEMINI_API_KEY = var.gemini_api_key
      GCP_PROJECT_ID = var.project_id
    }
  }

  event_trigger {
    trigger_region = var.region
    event_type     = "google.cloud.pubsub.topic.v1.messagePublished"
    pubsub_topic   = google_pubsub_topic.daily_trigger.id
  }

  depends_on = [google_project_service.apis]
}

# Cloud Scheduler - Daily at 4:30 PM ET (market close + 30 min)
resource "google_cloud_scheduler_job" "daily" {
  name      = "daily-analysis-trigger"
  schedule  = "30 16 * * 1-5"  # Mon-Fri 4:30 PM
  time_zone = "America/New_York"

  pubsub_target {
    topic_name = google_pubsub_topic.daily_trigger.id
    data       = base64encode("{\"trigger\": \"daily\"}")
  }

  depends_on = [google_project_service.apis]
}

# Storage bucket for function code
resource "google_storage_bucket" "functions" {
  name     = "${var.project_id}-functions"
  location = var.region
}

# Function source code (zip)
resource "google_storage_bucket_object" "function_zip" {
  name   = "daily-analysis.zip"
  bucket = google_storage_bucket.functions.name
  source = "functions/daily_analysis.zip"
}

# Outputs
output "function_url" {
  value = google_cloudfunctions2_function.analysis.url
}
```

---

## Option B: $2-5/month - Vertex AI

For production workloads with better reliability and higher limits.

### When to Use Vertex AI
- Need more than 1,500 requests/day
- Want enterprise SLAs
- Need to process 100+ stocks daily
- Require audit logging

### Cost Breakdown

| Component | Usage | Monthly Cost |
|-----------|-------|--------------|
| Vertex AI (Gemini Flash) | 50 stocks × 30 days × ~500 tokens | ~$0.50 |
| Cloud Functions | 1,500 invocations | $0 (free tier) |
| Cloud Scheduler | 3 jobs | $0 (free tier) |
| Firestore | 1,500 writes, 3,000 reads | $0 (free tier) |
| Cloud Storage | 50 MB | $0 (free tier) |
| **Total** | | **~$0.50-2.00** |

### Vertex AI Function Code

```python
# functions/vertex_analysis/main.py
import functions_framework
from google.cloud import firestore
from google.cloud import aiplatform
from vertexai.generative_models import GenerativeModel
import yfinance as yf
import pandas as pd
import json
import os
from datetime import datetime

# Configuration
PROJECT_ID = os.environ.get('GCP_PROJECT_ID')
REGION = os.environ.get('GCP_REGION', 'us-central1')

# Initialize
aiplatform.init(project=PROJECT_ID, location=REGION)
db = firestore.Client(project=PROJECT_ID)
model = GenerativeModel('gemini-1.5-flash-001')  # Cheapest Vertex model

WATCHLIST = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'MU', 'AMD', 'TSLA', 'META', 'SPY',
             'QQQ', 'IWM', 'XLF', 'XLK', 'XLE', 'XLV', 'GLD', 'TLT', 'VIX', 'DIA']


def rank_with_vertex(symbol: str, indicators: dict, signals: list) -> dict:
    """Use Vertex AI Gemini for analysis."""
    prompt = f"""Analyze {symbol}. Return JSON only.

Price: ${indicators['price']:.2f} ({indicators['change_pct']:+.2f}%)
RSI: {indicators['rsi']:.1f} | MACD: {indicators['macd']:.4f}
Signals: {json.dumps([s['signal'] for s in signals])}

{{"score": 1-100, "outlook": "BULLISH/BEARISH/NEUTRAL", "action": "BUY/SELL/HOLD", "reason": "brief"}}"""

    try:
        response = model.generate_content(prompt)
        text = response.text.strip()

        # Extract JSON
        start = text.find('{')
        end = text.rfind('}') + 1
        if start >= 0 and end > start:
            return json.loads(text[start:end])
    except Exception as e:
        print(f"Vertex error for {symbol}: {e}")

    return {"score": 50, "outlook": "NEUTRAL", "action": "HOLD", "reason": "Analysis unavailable"}


# ... (rest of the analysis code same as Option A)
```

### Vertex AI Terraform Addition

```hcl
# Add to terraform/main.tf

# Enable Vertex AI API
resource "google_project_service" "vertex" {
  service            = "aiplatform.googleapis.com"
  disable_on_destroy = false
}

# Service account for Vertex AI
resource "google_service_account" "vertex_sa" {
  account_id   = "vertex-analysis"
  display_name = "Vertex AI Analysis"
}

# Grant Vertex AI user role
resource "google_project_iam_member" "vertex_user" {
  project = var.project_id
  role    = "roles/aiplatform.user"
  member  = "serviceAccount:${google_service_account.vertex_sa.email}"
}
```

---

## Step-by-Step Setup

### 1. Create GCP Project

```bash
# Install gcloud CLI if needed
# https://cloud.google.com/sdk/docs/install

# Login and create project
gcloud auth login
gcloud projects create stock-analysis-prod --name="Stock Analysis"
gcloud config set project stock-analysis-prod

# Enable billing (required for APIs)
# Visit: https://console.cloud.google.com/billing
```

### 2. Get Gemini API Key (Option A)

```bash
# Visit Google AI Studio
open https://aistudio.google.com/app/apikey

# Create API key and save it
export GEMINI_API_KEY="your-key-here"
```

### 3. Deploy with Terraform

```bash
# Navigate to terraform directory
cd terraform

# Initialize
terraform init

# Create terraform.tfvars
cat > terraform.tfvars << EOF
project_id     = "stock-analysis-prod"
region         = "us-central1"
gemini_api_key = "${GEMINI_API_KEY}"
EOF

# Plan and apply
terraform plan
terraform apply
```

### 4. Manual Deployment (Alternative)

```bash
# Enable APIs
gcloud services enable \
  cloudfunctions.googleapis.com \
  cloudscheduler.googleapis.com \
  firestore.googleapis.com \
  pubsub.googleapis.com

# Create Pub/Sub topic
gcloud pubsub topics create daily-analysis-trigger

# Deploy function
cd functions/daily_analysis
gcloud functions deploy daily-stock-analysis \
  --gen2 \
  --runtime=python311 \
  --trigger-topic=daily-analysis-trigger \
  --entry-point=scheduled_analysis \
  --memory=512Mi \
  --timeout=300s \
  --set-env-vars="GEMINI_API_KEY=${GEMINI_API_KEY},GCP_PROJECT_ID=${PROJECT_ID}" \
  --region=us-central1

# Create scheduler job (Mon-Fri 4:30 PM ET)
gcloud scheduler jobs create pubsub daily-analysis \
  --schedule="30 16 * * 1-5" \
  --time-zone="America/New_York" \
  --topic=daily-analysis-trigger \
  --message-body='{"trigger": "daily"}'
```

### 5. Verify Setup

```bash
# Test function manually
gcloud functions call daily-stock-analysis --data '{}'

# Check logs
gcloud functions logs read daily-stock-analysis --limit=50

# View results in Firestore
open https://console.cloud.google.com/firestore
```

---

## Automation Schedules

### Recommended Schedule (Free Tier Safe)

```bash
# Daily market close analysis (Mon-Fri 4:30 PM ET)
gcloud scheduler jobs create pubsub market-close \
  --schedule="30 16 * * 1-5" \
  --time-zone="America/New_York" \
  --topic=daily-analysis-trigger \
  --message-body='{"type": "daily", "watchlist": "default"}'

# Weekly full screening (Saturday 10 AM)
gcloud scheduler jobs create pubsub weekly-screen \
  --schedule="0 10 * * 6" \
  --time-zone="America/New_York" \
  --topic=daily-analysis-trigger \
  --message-body='{"type": "weekly", "universe": "sp500"}'

# Pre-market check (Mon-Fri 9:00 AM ET)
gcloud scheduler jobs create pubsub pre-market \
  --schedule="0 9 * * 1-5" \
  --time-zone="America/New_York" \
  --topic=daily-analysis-trigger \
  --message-body='{"type": "premarket", "watchlist": "movers"}'
```

### API Call Budget

| Schedule | Stocks | AI Calls/Day | Monthly Total |
|----------|--------|--------------|---------------|
| Daily close | 20 | 20 | 400 |
| Weekly screen | 100 | ~15 | 60 |
| Pre-market | 10 | 10 | 200 |
| **Total** | | | **~660** |

Free tier limit: **45,000/month** ✓

---

## Cost Monitoring

### Set Up Budget Alerts

```bash
# Create budget alert for $5
gcloud billing budgets create \
  --billing-account=YOUR_BILLING_ACCOUNT_ID \
  --display-name="Stock Analysis Budget" \
  --budget-amount=5USD \
  --threshold-rule=percent=50 \
  --threshold-rule=percent=90 \
  --threshold-rule=percent=100
```

### Monitoring Dashboard Query

```sql
-- BigQuery: Daily API usage
SELECT
  DATE(timestamp) as date,
  COUNT(*) as api_calls,
  SUM(CAST(JSON_EXTRACT_SCALAR(labels, '$.tokens') AS INT64)) as total_tokens
FROM `project.dataset.api_logs`
WHERE timestamp > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)
GROUP BY date
ORDER BY date DESC
```

### Cost Tracking Function

```python
# Add to your Cloud Function
def log_usage(symbol: str, tokens_used: int):
    """Log API usage for cost tracking."""
    db.collection('usage').add({
        'timestamp': datetime.utcnow(),
        'symbol': symbol,
        'tokens': tokens_used,
        'cost_estimate': tokens_used * 0.000000075  # $0.075/1M tokens
    })
```

---

## Troubleshooting

### Common Issues

#### 1. Function Timeout
```bash
# Increase timeout to 540s (max)
gcloud functions deploy daily-stock-analysis \
  --timeout=540s \
  --memory=1Gi
```

#### 2. Quota Exceeded
```python
# Add rate limiting
import time

for symbol in WATCHLIST:
    analyze_symbol(symbol)
    time.sleep(1)  # 1 second between calls = 60 RPM max
```

#### 3. Cold Start Latency
```bash
# Set minimum instances (costs ~$5/month)
gcloud functions deploy daily-stock-analysis \
  --min-instances=1
```

#### 4. API Key Issues
```bash
# Verify API key works
curl "https://generativelanguage.googleapis.com/v1/models/gemini-pro:generateContent?key=${GEMINI_API_KEY}" \
  -H 'Content-Type: application/json' \
  -d '{"contents":[{"parts":[{"text":"Hello"}]}]}'
```

---

## Quick Reference

### Cost Summary

| Tier | Monthly Cost | Stocks/Day | Features |
|------|--------------|------------|----------|
| Free | $0 | 50 | Daily analysis, Firestore storage |
| Basic | $2-5 | 200 | + Weekly screening, alerts |
| Pro | $10-20 | 500+ | + Historical tracking, dashboards |

### Commands Cheatsheet

```bash
# Deploy
terraform apply

# Test manually
gcloud functions call daily-stock-analysis

# View logs
gcloud functions logs read daily-stock-analysis

# Check scheduler
gcloud scheduler jobs list

# Trigger manually
gcloud scheduler jobs run daily-analysis

# View Firestore
open https://console.cloud.google.com/firestore

# Check billing
open https://console.cloud.google.com/billing
```

### File Structure

```
automation/
├── terraform/
│   ├── main.tf
│   ├── variables.tf
│   └── terraform.tfvars
├── functions/
│   └── daily_analysis/
│       ├── main.py
│       └── requirements.txt
└── scripts/
    ├── deploy.sh
    └── test.sh
```

---

## Summary

**Cheapest Setup ($0/month)**:
1. Use Gemini API free tier (1,500 calls/day)
2. Cloud Functions Gen2 (2M invocations free)
3. Cloud Scheduler (3 jobs free)
4. Firestore (1GB free)

**Commands to Get Started**:
```bash
# 1. Create project
gcloud projects create stock-analysis-prod

# 2. Get Gemini API key
open https://aistudio.google.com/app/apikey

# 3. Deploy
cd terraform && terraform apply

# 4. Test
gcloud functions call daily-stock-analysis
```

Your automated stock analysis pipeline will run every market day at 4:30 PM ET, analyzing your watchlist and storing AI-ranked signals in Firestore - all for **$0/month**.
