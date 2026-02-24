# Industry Performance Tracker API

Standalone backend module for tracking performance of 50 US economy industries mapped to representative ETFs with multi-horizon analysis and Firebase caching.

## Overview

The Industry Tracker provides:
- **50-industry framework** covering the full US economy
- **Multi-horizon performance** (2 weeks → 10 years)
- **Firebase Firestore cache** for fast retrieval
- **Morning market summaries** with narrative insights
- **RESTful API** integrated with existing Options MCP Backend

---

## Architecture

### Module Structure

```
nubackend1/src/industry_tracker/
├── __init__.py                 # Module exports
├── industry_mapper.py          # 50-industry → ETF mapping
├── etf_data_fetcher.py         # Alpha Vantage data retrieval
├── performance_calculator.py   # Multi-horizon returns calculation
├── firebase_cache.py           # Firestore caching layer
├── summary_generator.py        # Morning summary generation
└── api_service.py              # Business logic orchestration
```

### Data Flow

```
┌─────────────────┐
│  API Request    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐     ┌──────────────────┐
│ IndustryService │────▶│ FirebaseCache    │
└────────┬────────┘     │ (Check cache)    │
         │              └──────────────────┘
         │ (Cache miss)
         ▼
┌─────────────────┐     ┌──────────────────┐
│ ETFDataFetcher  │────▶│ Alpha Vantage API│
└────────┬────────┘     │ (Fetch history)  │
         │              └──────────────────┘
         ▼
┌─────────────────┐
│ Performance     │
│ Calculator      │
│ (Pandas)        │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ FirebaseCache   │
│ (Update cache)  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ JSON Response   │
└─────────────────┘
```

---

## 50-Industry Framework

### Technology (8)
- Software → IGV
- Semiconductors → SOXX
- Cloud Computing → CLOU
- Cybersecurity → HACK
- Artificial Intelligence → BOTZ
- Internet → FDN
- Hardware → XLK
- Telecommunications → VOX

### Healthcare (6)
- Biotechnology → IBB
- Pharmaceuticals → XPH
- Healthcare Providers → IHF
- Medical Devices → IHI
- Managed Care → XLV
- Healthcare REIT → VHT

### Financials (7)
- Banks → KBE
- Insurance → KIE
- Asset Management → PFM
- Fintech → FINX
- REITs → VNQ
- Payments → IPAY
- Regional Banks → KRE

### Consumer (8)
- Retail → XRT
- E-Commerce → IBUY
- Consumer Staples → XLP
- Consumer Discretionary → XLY
- Restaurants → BITE
- Apparel → PEJ
- Automotive → CARZ
- Luxury Goods → LUXE

### Energy & Materials (5)
- Oil & Gas → XLE
- Renewable Energy → ICLN
- Mining → XME
- Steel → SLX
- Chemicals → XLB

### Industrials (5)
- Aerospace & Defense → ITA
- Transportation → XTN
- Construction → ITB
- Logistics → FTXR
- Industrials → XLI

### Real Estate & Infrastructure (4)
- Real Estate → IYR
- Infrastructure → PAVE
- Homebuilders → XHB
- Commercial Real Estate → INDS

### Communications & Media (3)
- Media → PBS
- Entertainment → PEJ
- Social Media → SOCL

### Other (4)
- Utilities → XLU
- Agriculture → DBA
- Cannabis → MSOS
- ESG → ESGU

---

## Performance Horizons

All returns are calculated across **10 time horizons** (in trading days):

| Horizon | Trading Days | Label       |
|---------|--------------|-------------|
| `2w`    | 10           | 2 weeks     |
| `1m`    | 21           | 1 month     |
| `2m`    | 42           | 2 months    |
| `3m`    | 63           | 3 months    |
| `6m`    | 126          | 6 months    |
| `52w`   | 252          | 52 weeks    |
| `2y`    | 504          | 2 years     |
| `3y`    | 756          | 3 years     |
| `5y`    | 1260         | 5 years     |
| `10y`   | 2520         | 10 years    |

**Note**: Returns are `null` if insufficient historical data exists for a horizon.

---

## API Endpoints

### 1. GET `/api/industries`

List all 50 industries and their ETF mappings.

**Response**:
```json
{
  "success": true,
  "data": [
    {"industry": "Software", "etf": "IGV"},
    {"industry": "Biotechnology", "etf": "IBB"},
    ...
  ]
}
```

---

### 2. GET `/api/industry/{industry_name}`

Get cached performance for a single industry.

**Parameters**:
- `industry_name` (path): Industry name (e.g., "Software", "Biotechnology")

**Response**:
```json
{
  "success": true,
  "data": {
    "industry": "Software",
    "etf": "IGV",
    "updated": "2026-02-21T10:30:00.000Z",
    "returns": {
      "2w": 3.5,
      "1m": 7.2,
      "2m": 12.1,
      "3m": 15.8,
      "6m": 24.3,
      "52w": 45.6,
      "2y": 78.2,
      "3y": 102.4,
      "5y": 156.7,
      "10y": null
    }
  }
}
```

**Errors**:
- `404`: Industry not found
- `503`: Alpha Vantage or Firebase unavailable

---

### 3. GET `/api/industry/{industry_name}/refresh`

Recompute and update cache for a single industry (fetches fresh data from Alpha Vantage).

**Parameters**:
- `industry_name` (path): Industry name

**Response**: Same as GET `/api/industry/{industry_name}` but with fresh data.

**Note**: Respects Alpha Vantage rate limits (5 calls/minute).

---

### 4. POST `/api/refresh-all`

Refresh performance data for all 50 industries.

**Request Body** (optional):
```json
{
  "batch_size": 10,
  "force": false
}
```

**Response**:
```json
{
  "success": true,
  "data": {
    "success_count": 48,
    "failure_count": 2,
    "performances": [
      {
        "industry": "Software",
        "etf": "IGV",
        "updated": "2026-02-21T10:35:00.000Z",
        "returns": { ... }
      },
      ...
    ],
    "failures": [
      {"industry": "Cannabis", "error": "Alpha Vantage rate limit hit"}
    ]
  }
}
```

**Warning**: This endpoint can take **5-10 minutes** due to API rate limits.

**Best Practice**: Run this **once daily** in a scheduled job (e.g., every morning at 6 AM EST).

---

### 5. GET `/api/summary/morning`

Generate morning market summary with top/bottom performers and narrative.

**Query Parameters**:
- `horizon` (optional, default: `1m`): Time horizon for analysis
- `force_refresh` (optional, default: `false`): Refresh all data before generating summary

**Response**:
```json
{
  "success": true,
  "data": {
    "timestamp": "2026-02-21T10:00:00.000Z",
    "horizon": "1m",
    "top_performers": [
      {
        "industry": "Artificial Intelligence",
        "etf": "BOTZ",
        "updated": "2026-02-21T06:00:00.000Z",
        "returns": {
          "1m": 12.5,
          ...
        }
      },
      ...
    ],
    "worst_performers": [
      {
        "industry": "Utilities",
        "etf": "XLU",
        "returns": {
          "1m": -2.3,
          ...
        }
      },
      ...
    ],
    "extremes": {
      "highs": [
        {
          "industry": "Semiconductors",
          "etf": "SOXX",
          "returns": { "52w": 48.2, ... }
        }
      ],
      "lows": []
    },
    "narrative": "The US economy is showing strong bullish momentum over the past month, with an average industry return of +5.2%. Broad-based strength is evident with 42 of 50 industries positive, indicating healthy market breadth. Leadership is concentrated in Artificial Intelligence, Semiconductors, Software, with the top performer up +12.5%. Underperformers include Utilities, Energy, Real Estate, with the weakest sector down -2.3%. Notable momentum: Semiconductors, Cloud Computing reaching 52-week highs, signaling sustained uptrends.",
    "metrics": {
      "average_return": 5.2,
      "positive_count": 42,
      "negative_count": 6,
      "neutral_count": 2,
      "total_industries": 50,
      "industries_with_data": 50
    }
  }
}
```

---

## Setup & Configuration

### 1. Environment Variables

Add to `.env` or `.env.cloud-run`:

```bash
# Required for Industry Tracker
ALPHA_VANTAGE_KEY=your-alpha-vantage-api-key
GCP_PROJECT_ID=your-gcp-project-id

# Firebase uses Application Default Credentials
# For local dev: gcloud auth application-default login
# For Cloud Run: Automatic via service account
```

### 2. Install Dependencies

```bash
# Activate environment
mamba activate fin-ai1

# Update environment with new dependencies
mamba env update -f environment.yml

# Or install manually
mamba install -c conda-forge pandas numpy firebase-admin google-cloud-firestore
pip install alpha-vantage
```

### 3. Firebase Setup

#### Option A: Cloud Run (Production)
Firebase automatically uses the Cloud Run service account. No additional setup needed.

#### Option B: Local Development
```bash
# Authenticate with gcloud
gcloud auth application-default login

# Set project
gcloud config set project YOUR_PROJECT_ID
```

### 4. Alpha Vantage API Key

Get a free API key: https://www.alphavantage.co/support/#api-key

**Free Tier Limits**:
- 5 API calls per minute
- 500 API calls per day

**Rate Limiting**: The module automatically enforces 12-second delays between calls to respect the 5/min limit.

---

## Usage Examples

### Example 1: Morning Brief Integration

```python
# In your morning_brief API endpoint
from industry_tracker.api_service import IndustryService

service = IndustryService(
    alpha_vantage_key=os.getenv("ALPHA_VANTAGE_KEY"),
    gcp_project_id=os.getenv("GCP_PROJECT_ID"),
)

# Get morning summary (uses cached data)
summary = await service.get_morning_summary(horizon="1m")

# Returns:
# {
#   "top_performers": [...],
#   "worst_performers": [...],
#   "narrative": "The US economy is showing...",
#   ...
# }
```

### Example 2: Scheduled Daily Refresh

```bash
# Run daily at 6 AM EST via cron or Cloud Scheduler
curl -X POST https://your-backend.run.app/api/refresh-all \
  -H "Content-Type: application/json" \
  -d '{"batch_size": 10}'
```

### Example 3: Check Specific Industry

```bash
# Get cached performance for Software industry
curl https://your-backend.run.app/api/industry/Software

# Refresh and get latest data
curl https://your-backend.run.app/api/industry/Software/refresh
```

---

## Firebase Cache Schema

### Collection: `industry_cache`

Each document is keyed by industry name:

```
industry_cache/
├── Software
├── Biotechnology
├── Banks
└── ...
```

### Document Structure

```typescript
{
  industry: string,        // "Software"
  etf: string,             // "IGV"
  updated: string,         // ISO timestamp
  returns: {
    "2w": number | null,
    "1m": number | null,
    "2m": number | null,
    "3m": number | null,
    "6m": number | null,
    "52w": number | null,
    "2y": number | null,
    "3y": number | null,
    "5y": number | null,
    "10y": number | null,
  }
}
```

---

## Performance Considerations

### Alpha Vantage Rate Limits

**Problem**: Free tier allows 5 calls/minute, 500/day.

**Solution**:
- Module enforces 12-second delays between calls
- Refreshing all 50 industries takes ~10 minutes
- Use Firebase cache to minimize API calls

### Cache Strategy

**Best Practice**:
1. Run `POST /api/refresh-all` **once daily** at market close or before open
2. All other endpoints use cached data from Firebase (sub-100ms response time)
3. Manual refresh only for specific industries as needed

### Firestore Read/Write Costs

**Reads**: ~50 reads/day (one per industry in morning summary)
**Writes**: ~50 writes/day (one per industry in daily refresh)

**Cost**: Free tier covers 50k reads + 20k writes/day → well within limits.

---

## Error Handling

### Common Errors

#### 1. `503: ALPHA_VANTAGE_KEY not configured`
**Fix**: Set `ALPHA_VANTAGE_KEY` in environment variables.

#### 2. `503: GCP_PROJECT_ID not configured`
**Fix**: Set `GCP_PROJECT_ID` in environment variables.

#### 3. `404: Industry not found: InvalidIndustry`
**Fix**: Check industry name against the 50-industry list. Names are case-sensitive.

#### 4. `503: No cached data available. Run POST /refresh-all first.`
**Fix**: Run `POST /api/refresh-all` to populate the cache initially.

#### 5. `Alpha Vantage rate limit hit`
**Fix**: Wait 1 minute, then retry. Free tier is limited to 5 calls/minute.

### Graceful Degradation

- If Alpha Vantage is down, cached data is still served
- If Firebase is down, API returns 503 with clear error message
- Individual industry fetch failures don't block bulk operations

---

## Testing

### Manual Testing

```bash
# 1. Check service health
curl http://localhost:8080/

# 2. List all industries
curl http://localhost:8080/api/industries

# 3. Get cached performance
curl http://localhost:8080/api/industry/Software

# 4. Refresh one industry (slow ~12s)
curl http://localhost:8080/api/industry/Software/refresh

# 5. Generate morning summary
curl "http://localhost:8080/api/summary/morning?horizon=1m"

# 6. Refresh all (slow ~10 minutes)
curl -X POST http://localhost:8080/api/refresh-all \
  -H "Content-Type: application/json" \
  -d '{"batch_size": 10}'
```

### Automated Testing

Create `test_industry_tracker.py`:

```python
import pytest
from industry_tracker.industry_mapper import IndustryMapper
from industry_tracker.performance_calculator import PerformanceCalculator

def test_industry_count():
    assert IndustryMapper.get_count() == 50

def test_etf_mapping():
    assert IndustryMapper.get_etf("Software") == "IGV"
    assert IndustryMapper.get_industry("IGV") == "Software"

def test_horizon_days():
    calc = PerformanceCalculator()
    assert calc.get_horizon_days("1m") == 21
    assert calc.get_horizon_days("52w") == 252
```

Run tests:
```bash
pytest test_industry_tracker.py -v
```

---

## Production Deployment

### Cloud Run Configuration

```yaml
# cloud-run.yaml
env:
  - name: ALPHA_VANTAGE_KEY
    valueFrom:
      secretKeyRef:
        name: alpha-vantage-key
        key: latest

  - name: GCP_PROJECT_ID
    value: "your-project-id"
```

### Scheduled Daily Refresh

Use Cloud Scheduler to trigger daily refresh:

```bash
gcloud scheduler jobs create http industry-daily-refresh \
  --schedule="0 6 * * *" \
  --uri="https://your-backend.run.app/api/refresh-all" \
  --http-method=POST \
  --headers="Content-Type=application/json" \
  --message-body='{"batch_size": 10}' \
  --time-zone="America/New_York"
```

---

## Troubleshooting

### Cache is Stale

**Symptom**: Morning summary shows old timestamps.

**Fix**:
```bash
curl -X POST https://your-backend.run.app/api/refresh-all
```

### Missing Data for Some Industries

**Symptom**: Some industries return `null` for certain horizons.

**Cause**: ETF doesn't have enough historical data (e.g., new ETF).

**Fix**: This is expected. The module returns `null` for insufficient data.

### Slow API Responses

**Symptom**: API calls take >5 seconds.

**Cause**: Cache miss triggering Alpha Vantage fetch.

**Fix**: Ensure daily refresh job is running to keep cache fresh.

---

## Roadmap

### Future Enhancements

1. **Sector-level aggregation** (Technology average, Healthcare average, etc.)
2. **Correlation analysis** (which industries move together)
3. **Momentum scoring** (detect rotation patterns)
4. **Webhook notifications** (alert on 52-week highs/lows)
5. **Multi-region support** (EU, Asia industry frameworks)

---

## Support

For issues or questions:
- Check [INDUSTRY_TRACKER_GUIDE.md](./INDUSTRY_TRACKER_GUIDE.md)
- Review logs: `gcloud run logs read --service=your-service`
- Test locally: `uvicorn main:app --reload --port 8080`

---

**Built with**: Python 3.11, FastAPI, Pandas, Firebase, Alpha Vantage

**License**: MIT

**Author**: MCP Finance Engineering Team
