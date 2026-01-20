# Run Beta1 Scan Locally

**Quick setup and execution guide for running Beta1 scans on your machine.**

---

## Prerequisites

Make sure you have:
- ✅ Mamba or conda installed
- ✅ GCP credentials configured
- ✅ `gcloud` CLI installed

---

## Step-by-Step Setup

### Step 1: Navigate to the Project Directory

```bash
cd "/Users/adamaslan/code/gcp app w mcp/mcp-finance1/cloud-run"
```

### Step 2: Create/Activate the Mamba Environment

**First time only** - Create the environment:
```bash
mamba env create -f environment.yml -n mcp-finance-backend
```

**Every time** - Activate the environment:
```bash
mamba activate mcp-finance-backend
```

You should see `(mcp-finance-backend)` in your terminal prompt.

### Step 3: Set GCP Project ID

```bash
export GCP_PROJECT_ID="ttb-lang1"
```

### Step 4: Authenticate with Google Cloud

```bash
gcloud auth application-default login
```

This will open a browser window to sign in. Complete the authentication.

### Step 5: Run the Beta1 Scan

```bash
python3 scripts/run_beta1_scan.py
```

---

## What You'll See

The script will output:

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

## Viewing Results

### In Firebase Console

1. Open: https://console.firebase.google.com/project/ttb-lang1/firestore
2. Look for these collections:
   - **scans** → **beta1_latest** (most recent results)
   - **scans** → **beta1_YYYYMMDD_HHMMSS** (historical records)
   - **beta1_trades** → Individual trades per symbol

### Via Command Line

```bash
# View latest results
gcloud firestore documents get scans/beta1_latest

# List all Beta1 records
gcloud firestore documents list scans --collection-filter='startsWith(name,"beta1")'

# Get specific trade
gcloud firestore documents get beta1_trades/NVDA
```

### Via Python Script

```python
from google.cloud import firestore

db = firestore.Client(project="ttb-lang1")

# Get latest scan results
doc = db.collection("scans").document("beta1_latest").get()
result = doc.to_dict()

print(f"Scan found {len(result['qualified_trades'])} qualified trades:")
for trade in result['qualified_trades']:
    print(f"  {trade['symbol']}: {trade['quality_score']:.1f}")
```

---

## Troubleshooting

### Error: "No module named 'pandas'"

**Problem**: Environment not activated

**Solution**:
```bash
mamba activate mcp-finance-backend
```

### Error: "The gcloud config project is not set"

**Problem**: GCP project not set

**Solution**:
```bash
export GCP_PROJECT_ID="ttb-lang1"
gcloud config set project ttb-lang1
```

### Error: "The caller does not have permission"

**Problem**: GCP credentials not authenticated

**Solution**:
```bash
gcloud auth application-default login
```

### Error: "Firestore database not found"

**Problem**: Firebase not initialized for this project

**Solution**:
```bash
gcloud firestore databases create --location=nam5
```

### Scan takes too long (>2 minutes)

**Possible causes**:
- Slow internet connection
- Rate limiting from Yahoo Finance
- System under heavy load

**Solutions**:
- Try again during off-peak hours
- Check internet speed: `speedtest-cli`
- Monitor system resources: `top` or `Activity Monitor`

---

## Quick Reference

### Full Command (One-Liner After Setup)

```bash
mamba activate mcp-finance-backend && \
export GCP_PROJECT_ID="ttb-lang1" && \
cd "/Users/adamaslan/code/gcp app w mcp/mcp-finance1/cloud-run" && \
python3 scripts/run_beta1_scan.py
```

### Save Command to Shell Alias (Optional)

Add to `~/.zshrc` or `~/.bash_profile`:
```bash
alias beta1-scan='cd "/Users/adamaslan/code/gcp app w mcp/mcp-finance1/cloud-run" && \
mamba activate mcp-finance-backend && \
export GCP_PROJECT_ID="ttb-lang1" && \
python3 scripts/run_beta1_scan.py'
```

Then run anytime with: `beta1-scan`

---

## Next Steps

After running the scan:

1. **View Results**
   - Check Firebase console
   - Query with Python or gcloud

2. **Run Regularly**
   - Schedule with `crontab` (local)
   - Schedule with Cloud Scheduler (production)
   - Schedule with GitHub Actions

3. **Build Dashboard**
   - Use Firebase data
   - Create visualizations
   - Set up alerts

---

## Expected Behavior

| Step | Expected | Duration |
|------|----------|----------|
| Load environment | ✓ Shows prompts | <10 sec |
| Connect Firebase | ✓ "Connected" message | <5 sec |
| Scan symbols | ✓ Shows progress | 30-90 sec |
| Save results | ✓ 3 save confirmations | 2-5 sec |
| **Total** | **✓ Complete** | **~50-110 sec** |

---

## File Locations

- **Script**: `/Users/adamaslan/code/gcp app w mcp/mcp-finance1/cloud-run/scripts/run_beta1_scan.py`
- **Environment**: `/Users/adamaslan/code/gcp app w mcp/mcp-finance1/cloud-run/environment.yml`
- **Universe Config**: `/Users/adamaslan/code/gcp app w mcp/mcp-finance1/src/technical_analysis_mcp/universes.py`

---

## Support

For detailed information, see:
- `BETA1-SCAN-GUIDE.md` - Comprehensive guide
- `DEPLOYMENT-QUICKSTART.md` - Deployment guide
- `ENVIRONMENT-SETUP.md` - Environment setup

---

**Status**: ✅ Ready to Run
**Last Updated**: January 19, 2026
