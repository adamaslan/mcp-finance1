# Beta1 Universe Scan Guide

**Universe**: Beta1
**Symbols**: MU, GLD, NVDA, RGTI, RR, PL, GEV, GOOG, IBIT, LICX, APLD
**Total**: 11 symbols

---

## Quick Start

Run the Beta1 scan and automatically save results to Firebase:

```bash
cd /Users/adamaslan/code/gcp\ app\ w\ mcp/mcp-finance1/cloud-run
python3 scripts/run_beta1_scan.py
```

---

## Prerequisites

### Option 1: Local Testing (Requires Environment)

**Setup environment**:
```bash
# Activate existing fin-ai1 environment
mamba activate fin-ai1
```

**Authenticate with GCP**:
```bash
# Login to GCP
gcloud auth application-default login

# Set project ID
export GCP_PROJECT_ID="ttb-lang1"
```

### Option 2: Cloud Run Job (Recommended for Production)

Deploy as a Cloud Run job that runs on schedule:
```bash
# Build and push image
docker build -t mcp-finance-backend-job .
docker tag mcp-finance-backend-job:latest \
  us-central1-docker.pkg.dev/ttb-lang1/mcp-finance/mcp-backend-job:latest
docker push us-central1-docker.pkg.dev/ttb-lang1/mcp-finance/mcp-backend-job:latest

# Create Cloud Run job
gcloud run jobs create beta1-scan \
  --image=us-central1-docker.pkg.dev/ttb-lang1/mcp-finance/mcp-backend-job:latest \
  --region=us-central1 \
  --set-env-vars="GCP_PROJECT_ID=ttb-lang1" \
  --command="python" \
  --args="scripts/run_beta1_scan.py"

# Run the job
gcloud run jobs execute beta1-scan --region=us-central1

# View logs
gcloud run jobs logs read beta1-scan --region=us-central1 --limit=100
```

---

## How It Works

### 1. Runs Technical Analysis

The script scans all symbols in the Beta1 universe using:
- **Data Source**: Yahoo Finance (yfinance)
- **Analysis**: Technical indicators, trend detection, signal generation
- **Concurrency**: 10 parallel requests (configurable)
- **Period**: 1 month of data

### 2. Identifies Qualified Trades

For each symbol, the analyzer identifies:
- Primary trading signal (BUY, SELL, HOLD)
- Signal strength/quality score (0-100)
- Support/resistance levels
- Entry/exit recommendations

### 3. Ranks Results

Results are ranked by quality score and returned in order:
- Highest quality trades first
- Qualified means signal strength > threshold
- Maximum results configurable

### 4. Saves to Firebase

Results are stored in three collections:

**scans/beta1_latest** (Latest Results)
```
{
  "universe": "beta1",
  "total_scanned": 11,
  "qualified_trades": [ ... ],
  "metadata": {
    "scan_timestamp": "2026-01-19T22:30:00...",
    "symbols": ["MU", "GLD", "NVDA", ...],
    "symbols_count": 11
  }
}
```

**scans/beta1_YYYYMMDD_HHMMSS** (Historical Records)
- Same structure as above
- Timestamped for audit trail and historical analysis

**beta1_trades/SYMBOL** (Individual Trades)
```
{
  "symbol": "MU",
  "quality_score": 85.5,
  "primary_signal": "BUY",
  "current_price": 125.30,
  "entry_price": 124.50,
  "stop_loss": 120.00,
  "target_price": 135.00,
  "last_updated": "2026-01-19T22:30:00..."
}
```

---

## Running Locally

### Step 1: Activate Environment

```bash
# Activate existing environment
mamba activate fin-ai1
```

### Step 2: Set Up GCP Credentials

```bash
# Option A: Interactive login
gcloud auth application-default login

# Option B: Service account
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account-key.json"
```

### Step 3: Set Project ID

```bash
export GCP_PROJECT_ID="ttb-lang1"
```

### Step 4: Run Scan

```bash
cd /Users/adamaslan/code/gcp\ app\ w\ mcp/mcp-finance1/cloud-run
python3 scripts/run_beta1_scan.py
```

### Expected Output

```
════════════════════════════════════════════════════════════════════════════════
                         🚀 BETA1 UNIVERSE SCAN
════════════════════════════════════════════════════════════════════════════════

Project ID: ttb-lang1

⏳ Loading dependencies...
✓ Dependencies loaded

⏳ Connecting to Firebase...
✓ Firebase connected and tested

────────────────────────────────────────────────────────────────────────────────
  BETA1 UNIVERSE
────────────────────────────────────────────────────────────────────────────────

✓ Loaded 11 symbols

Symbols: MU, GLD, NVDA, RGTI, RR, PL, GEV, GOOG, IBIT, LICX, APLD

────────────────────────────────────────────────────────────────────────────────
  SCANNING BETA1 UNIVERSE
────────────────────────────────────────────────────────────────────────────────

⏳ Scanning for qualified trade setups...
   (This may take 30-90 seconds depending on network conditions)

✓ Scan completed successfully!

────────────────────────────────────────────────────────────────────────────────
  SCAN RESULTS
────────────────────────────────────────────────────────────────────────────────

Total symbols scanned:        11
Qualified trades found:       7

🔝 Top Qualified Trades:

   1. NVDA     | Score:  92.50 | Signal:         BUY | Price: $125.30
   2. MU       | Score:  88.75 | Signal:         BUY | Price:  $98.20
   3. GOOG     | Score:  82.30 | Signal:         BUY | Price: $145.60
   4. GLD      | Score:  75.45 | Signal:        HOLD | Price: $198.50
   5. APLD     | Score:  71.20 | Signal:         BUY | Price:  $52.30
   6. RGTI     | Score:  68.90 | Signal:        SELL | Price:  $28.75
   7. PL       | Score:  65.50 | Signal:        HOLD | Price: $185.20

────────────────────────────────────────────────────────────────────────────────
  SAVING TO FIREBASE
────────────────────────────────────────────────────────────────────────────────

✓ Saved: scans/beta1_latest
✓ Saved: scans/beta1_20260119_223000
⏳ Saving individual trades...
✓ Saved 7 individual trades to beta1_trades/

════════════════════════════════════════════════════════════════════════════════

✓ Beta1 scan complete!
```

---

## Viewing Results in Firebase

### Via Firebase Console

1. Open: https://console.firebase.google.com/project/ttb-lang1/firestore
2. Navigate to `scans` collection
3. View `beta1_latest` document

### Via gcloud CLI

```bash
# Get latest Beta1 results
gcloud firestore documents get scans/beta1_latest

# List all Beta1 historical records
gcloud firestore documents list scans --collection-filter='startsWith(name,"beta1")'

# Get individual trade
gcloud firestore documents get beta1_trades/MU
```

### Via Python

```python
from google.cloud import firestore

db = firestore.Client(project="ttb-lang1")

# Get latest results
doc = db.collection("scans").document("beta1_latest").get()
result = doc.to_dict()

print(f"Qualified trades: {len(result['qualified_trades'])}")
for trade in result['qualified_trades']:
    print(f"  {trade['symbol']}: {trade['quality_score']:.1f}")

# Get specific trade
trade = db.collection("beta1_trades").document("MU").get()
print(trade.to_dict())

# Query qualified trades
trades = db.collection("beta1_trades").where("quality_score", ">", 80).get()
for trade in trades:
    print(f"  {trade.id}: {trade.get('quality_score')}")
```

---

## Scheduling Scans

### Option 1: Cloud Scheduler

Create a scheduled job to run the scan automatically:

```bash
# Create Cloud Scheduler job to run daily at 4 PM ET
gcloud scheduler jobs create pubsub beta1-scan-daily \
  --schedule="0 20 * * *" \
  --time-zone="America/New_York" \
  --topic="beta1-scan-trigger" \
  --message-body='{"trigger": "schedule"}'
```

### Option 2: GitHub Actions

Add to `.github/workflows/beta1-scan.yml`:

```yaml
name: Daily Beta1 Scan

on:
  schedule:
    - cron: "0 20 * * *"  # 4 PM ET daily

jobs:
  scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Authenticate to Google Cloud
        uses: google-github-actions/auth@v1
        with:
          credentials_json: ${{ secrets.GCP_SA_KEY }}

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Run Beta1 scan
        run: python mcp-finance1/cloud-run/scripts/run_beta1_scan.py
```

### Option 3: Manual Cron

Run daily via system cron:

```bash
# Edit crontab
crontab -e

# Add line (4 PM ET):
0 20 * * * cd /Users/adamaslan/code/gcp\ app\ w\ mcp/mcp-finance1/cloud-run && python3 scripts/run_beta1_scan.py >> /tmp/beta1-scan.log 2>&1
```

---

## Monitoring & Logging

### View Logs

```bash
# From script output
python3 scripts/run_beta1_scan.py 2>&1 | tee scan.log

# Cloud Logging (if deployed to Cloud Run)
gcloud run jobs logs read beta1-scan --region=us-central1 --limit=50

# System logs (if via cron)
tail -f /tmp/beta1-scan.log
```

### Set Up Alerts

Monitor Firebase for new results:

```python
from google.cloud import firestore

db = firestore.Client(project="ttb-lang1")

# Watch for changes
def on_snapshot(doc_snapshot, changes, read_time):
    for doc in doc_snapshot:
        data = doc.to_dict()
        print(f"Updated: {doc.id}")
        print(f"  Qualified: {len(data.get('qualified_trades', []))}")

# Start watching
query = db.collection("scans").document("beta1_latest")
query.on_snapshot(on_snapshot)
```

---

## Troubleshooting

### Error: "No module named 'pandas'"

**Solution**: Activate the environment
```bash
mamba activate fin-ai1
```

### Error: "Goofin-ai1 found"

**Solution**: Authenticate with GCP
```bash
gcloud auth application-default login
```

### Error: "Firebase connection failed"

**Solution**: Check project ID
```bash
export GCP_PROJECT_ID="ttb-lang1"
gcloud config set project ttb-lang1
```

### Error: "Firestore database not found"

**Solution**: Create Firestore database
```bash
gcloud firestore databases create --location=nam5
```

### Slow Performance (>2 minutes)

**Possible causes**:
- Network latency to data source
- Rate limiting from Yahoo Finance
- System resources

**Solutions**:
- Run during off-peak hours
- Reduce universe size
- Check network connectivity

---

## Performance Metrics

### Expected Scan Time

- **Network**: 30-90 seconds (depends on internet speed)
- **Analysis**: 5-15 seconds (depends on system)
- **Firebase Save**: 2-5 seconds
- **Total**: ~40-110 seconds

### Resource Usage

- **Memory**: ~200-500 MB
- **Disk**: ~50 MB temporary
- **CPU**: 1-2 cores
- **Bandwidth**: ~5-10 MB outbound

---

## API Endpoints (HTTP Alternative)

Instead of running the script, you can call the API endpoint once deployed:

```bash
# Start the API
python3 main.py

# Call scan endpoint
curl -X POST http://localhost:8080/api/scan \
  -H "Content-Type: application/json" \
  -d '{"universe": "beta1", "max_results": 11}'
```

Response:
```json
{
  "universe": "beta1",
  "total_scanned": 11,
  "qualified_trades": [
    {
      "symbol": "NVDA",
      "quality_score": 92.5,
      "primary_signal": "BUY",
      ...
    }
  ]
}
```

---

## Next Steps

1. **Deploy Backend**: Follow `DEPLOYMENT-QUICKSTART.md`
2. **Schedule Scans**: Use Cloud Scheduler or GitHub Actions
3. **Monitor Results**: Watch Firebase for new scans
4. **Build Dashboard**: Create visualizations from Firebase data
5. **Integrate Alerts**: Send notifications for qualified trades

---

## File Locations

- **Script**: `/mcp-finance1/cloud-run/scripts/run_beta1_scan.py`
- **Universe Config**: `/mcp-finance1/src/technical_analysis_mcp/universes.py`
- **MCP Server**: `/mcp-finance1/src/technical_analysis_mcp/server.py`
- **Main API**: `/mcp-finance1/cloud-run/main.py`

---

**Last Updated**: January 19, 2026
**Status**: ✅ Ready to Use
**Next**: Deploy backend and run first scan
