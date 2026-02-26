# Industry Tracker Setup Guide

Complete setup for local development and GCloud deployment with all features.

## Quick Start

### Local Development (Fastest, No Auth Needed)

```bash
# 1. Activate environment
mamba activate fin-ai1

# 2. Install dependencies
mamba install -c conda-forge yfinance pandas

# 3. Run test
python test_industry_brief.py
```

No Firebase, GCP, or API keys needed. Uses free yfinance data.

---

## Installation

### Dependencies for Local Mode

```bash
mamba activate fin-ai1
mamba install -c conda-forge yfinance pandas httpx
```

### Dependencies for Cloud Mode (Full Features)

```bash
mamba activate fin-ai1
mamba install -c conda-forge \
  yfinance \
  pandas \
  httpx \
  firebase-admin \
  google-cloud-firestore
```

### Optional: API Keys for Premium Data Sources

Add to `.env.local` (NOT committed to git):

```bash
# Alpha Vantage (for historical data fallback)
ALPHA_VANTAGE_KEY=your_api_key_here

# Finnhub (preferred data source, minimal quota)
FINNHUB_API_KEY=your_api_key_here

# GCP (for cloud deployment)
GCP_PROJECT_ID=your-project-id
```

---

## Local Development Mode

Perfect for development, testing, and demos. Works with zero dependencies beyond yfinance.

### Example: Fetch Performance Data Locally

```python
from industry_tracker import IndustryService

# Initialize service (no GCP credentials needed)
service = IndustryService(
    alpha_vantage_key="",      # Optional
    gcp_project_id=None,        # Disabled
    finnhub_key="",             # Optional
)

# Get top performers (uses yfinance automatically)
import asyncio

async def demo():
    result = await service.get_industry_performance("Software")
    print(f"Software ETF (IGV) returns:")
    print(f"  1w: {result['returns']['1w']}%")
    print(f"  2w: {result['returns']['2w']}%")
    print(f"  1m: {result['returns']['1m']}%")

asyncio.run(demo())
```

### Data Source Priority (Local Mode)

1. ✅ yfinance (free, no auth, always available)

---

## Cloud Deployment Mode

Full features: Firebase caching, persistent storage, API fallbacks.

### Prerequisites

1. **GCP Project**
   ```bash
   # Create project or use existing
   gcloud config set project your-project-id
   ```

2. **Enable Firebase** in GCP Console:
   - Firestore Database
   - Storage

3. **GCP Credentials**
   ```bash
   # Set local credentials for development
   export GOOGLE_APPLICATION_CREDENTIALS=~/.gcloud-credentials/gcloud-key-latest.json
   export GCP_PROJECT_ID=your-project-id
   ```

4. **API Keys** (optional, but recommended)
   ```bash
   # Get from:
   # - Finnhub: https://finnhub.io (free tier: 60 req/min)
   # - Alpha Vantage: https://www.alphavantage.co (free tier: 5 req/min)
   ```

### Example: Use With Firebase

```python
import os
from industry_tracker import IndustryService

# Initialize service with cloud features
service = IndustryService(
    alpha_vantage_key=os.getenv("ALPHA_VANTAGE_KEY", ""),
    gcp_project_id=os.getenv("GCP_PROJECT_ID"),  # Enables Firebase
    finnhub_key=os.getenv("FINNHUB_API_KEY", ""),
)

# All data is now cached in Firebase!
import asyncio

async def demo():
    # Refresh all 50 industries (caches to Firebase)
    result = await service.refresh_all_industries()
    print(f"Updated: {result['success_count']}, Failed: {result['failure_count']}")

    # Get cached morning summary
    summary = await service.get_morning_summary(horizon="1w")
    print(summary["narrative"])

asyncio.run(demo())
```

### Data Source Priority (Cloud Mode)

1. ✅ Persistent Store (Firestore) - Zero-cost reads, full history
2. ✅ Finnhub API - Real-time data, minimal quota
3. ✅ Alpha Vantage API - Fallback for historical data
4. ✅ yfinance - Free fallback, no auth needed

---

## Configuration

### Environment Variables

**Local Development:**
```bash
# Optional (uses free yfinance by default)
FINNHUB_API_KEY=optional
ALPHA_VANTAGE_KEY=optional
```

**Cloud Deployment:**
```bash
# Required for Firebase
GCP_PROJECT_ID=your-project-id
GOOGLE_APPLICATION_CREDENTIALS=~/.gcloud-credentials/gcloud-key-latest.json

# Recommended for data quality
FINNHUB_API_KEY=your_key
ALPHA_VANTAGE_KEY=your_key
```

### Programmatic Configuration

```python
from industry_tracker import IndustryService

# Local mode (no Firebase)
local_service = IndustryService(
    alpha_vantage_key="",
    gcp_project_id=None,
    finnhub_key="",
)

# Cloud mode (with Firebase + APIs)
cloud_service = IndustryService(
    alpha_vantage_key="your_key",
    gcp_project_id="your-project",
    finnhub_key="your_key",
)
```

---

## Usage Examples

### Example 1: Get Top Performers (Any Mode)

```python
from industry_tracker import IndustryService
import asyncio

async def get_top_performers():
    service = IndustryService()  # Auto-detects mode

    # Fetch performance for all 50 industries
    result = await service.get_industry_performance("Software")
    print(result)

asyncio.run(get_top_performers())
```

### Example 2: Refresh & Cache (Cloud Only)

```python
from industry_tracker import IndustryService
import asyncio
import os

async def refresh_cache():
    service = IndustryService(
        gcp_project_id=os.getenv("GCP_PROJECT_ID"),
    )

    # Refresh all industries and cache to Firebase
    result = await service.refresh_all_industries()
    print(f"✓ Updated {result['success_count']} industries")
    print(f"✗ Failed: {result['failure_count']}")

asyncio.run(refresh_cache())
```

### Example 3: Generate Morning Summary (Cloud Only)

```python
from industry_tracker import IndustryService
import asyncio
import os

async def morning_brief():
    service = IndustryService(
        gcp_project_id=os.getenv("GCP_PROJECT_ID"),
    )

    # Get cached summary for last week
    summary = await service.get_morning_summary(horizon="1w")

    # Print top performers
    print("Top Performers (Last Week):")
    for i, perf in enumerate(summary['top_performers'], 1):
        ret = perf['returns']['1w']
        print(f"  {i}. {perf['industry']}: {ret:+.2f}%")

    # Print narrative
    print("\nMarket Narrative:")
    print(summary['narrative'])

asyncio.run(morning_brief())
```

### Example 4: Use Without APIs (Local yfinance)

```python
from industry_tracker import IndustryBrief

# This works WITHOUT any API keys or Firebase
brief = IndustryBrief()

# Generates local analysis using only yfinance
analysis = brief.generate_brief(horizon="2w", top_n=10)

for perf in analysis['top_performers']:
    print(f"{perf['industry']}: {perf['returns']['2w']:+.2f}%")
```

---

## Supported Time Horizons

All modes support 11 time horizons:

- `1w` - Last week (5 trading days) ✨ **NEW**
- `2w` - Last 2 weeks (10 trading days) ✨ **NEW**
- `1m` - Last month (21 trading days)
- `2m` - Last 2 months
- `3m` - Last quarter
- `6m` - Last 6 months
- `52w` - Last year
- `2y` - Last 2 years
- `3y` - Last 3 years
- `5y` - Last 5 years
- `10y` - Last 10 years

---

## 50 Industries Tracked

All organized by sector:

**Technology** (8): Software, Semiconductors, Cloud Computing, Cybersecurity, AI, Internet, Hardware, Telecom

**Healthcare** (6): Biotech, Pharma, Providers, Medical Devices, Managed Care, Healthcare REIT

**Financials** (7): Banks, Insurance, Asset Management, Fintech, REITs, Payments, Regional Banks

**Consumer** (8): Retail, E-Commerce, Staples, Discretionary, Restaurants, Apparel, Automotive, Luxury

**Energy & Materials** (5): Oil & Gas, Renewable, Mining, Steel, Chemicals

**Industrials** (5): Aerospace, Transportation, Construction, Logistics, Industrials

**Real Estate** (4): Real Estate, Infrastructure, Homebuilders, Commercial Real Estate

**Communications** (3): Media, Entertainment, Social Media

**Other** (4): Utilities, Agriculture, Cannabis, ESG

---

## Testing

### Test Local Mode

```bash
cd /Users/adamaslan/code/gcp\ app\ w\ mcp/mcp-finance1/9_mcp/morning_brief
python test_industry_brief.py
```

Shows best performers for last week and 2 weeks.

### Test Cloud Mode

```bash
# Requires GCP_PROJECT_ID and Firebase setup
export GCP_PROJECT_ID=your-project-id
export GOOGLE_APPLICATION_CREDENTIALS=~/.gcloud-credentials/gcloud-key-latest.json

python -c "
from industry_tracker import IndustryService
import asyncio
import os

async def test():
    service = IndustryService(gcp_project_id=os.getenv('GCP_PROJECT_ID'))
    result = await service.get_cache_status()
    print(result)

asyncio.run(test())
"
```

---

## Troubleshooting

### "No module named yfinance"
```bash
mamba install -c conda-forge yfinance
```

### "Firebase not installed"
```bash
mamba install -c conda-forge firebase-admin google-cloud-firestore
```

### "GCP_PROJECT_ID not set"
```bash
export GCP_PROJECT_ID=your-project-id
export GOOGLE_APPLICATION_CREDENTIALS=~/.gcloud-credentials/gcloud-key-latest.json
```

### "All data sources failed"
- Check internet connection
- Verify yfinance works: `python -c "import yfinance; print(yfinance.Ticker('IGV').history())"`
- Check API keys if set
- Try local mode without APIs

---

## Architecture

### Data Flow

**Local Mode:**
```
Client Code
    ↓
IndustryService
    ↓
ETFDataFetcher (yfinance)
    ↓
PerformanceCalculator
```

**Cloud Mode:**
```
Client Code
    ↓
IndustryService
    ↓
FirebaseCache (L1)
    ↓
PersistentStore (L2)
    ↓
ETFDataFetcher (Finnhub/Alpha Vantage/yfinance)
    ↓
PerformanceCalculator
    ↓
Back to FirebaseCache (write)
```

### Fallback Chain

1. **Persistent Store** (Firestore) - Zero-cost, full history
2. **Finnhub API** - Real-time, low quota
3. **Alpha Vantage** - Historical, limited quota
4. **yfinance** - Free, always available

---

## Performance

- **Local mode**: ~1-2 seconds per industry (yfinance)
- **Cloud mode (cached)**: ~10ms per industry (Firestore read)
- **Cloud mode (fresh)**: ~2-5 seconds per industry (API call + Firestore write)

All 50 industries: ~2 minutes for full refresh

---

## Security

### API Keys
- Never commit `.env` files
- Use `.env.local` for local development
- Set env vars for cloud deployments
- Rotate keys every 7 days (GCP service account keys)

### Firebase
- Uses Application Default Credentials (works in Cloud Run)
- Respects IAM permissions
- Data encrypted at rest and in transit

### Firestore Structure
```
industry_cache/{industry_name}
  → performance data with returns

etf_history/{symbol}
  → full price history (chunked for large datasets)
```

---

## Next Steps

1. **Local testing**: Run `python test_industry_brief.py`
2. **Deploy locally**: Integrate into your MCP tools
3. **Add to Cloud**: Set `GCP_PROJECT_ID` for Firebase features
4. **Schedule daily updates**: Set up Cloud Scheduler job

---

For API details, see `industry_tracker/README.md`
