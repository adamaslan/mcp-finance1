# Deployment Guide - MCP Finance Backend

## Overview

This guide covers deploying the updated Cloud Run backend with the 4 new endpoints:
- `/api/trade-plan`
- `/api/scan`
- `/api/portfolio-risk`
- `/api/morning-brief`

---

## Prerequisites

1. Google Cloud SDK installed (`gcloud`)
2. Docker installed (for local testing)
3. Authentication to GCP project (`gcloud auth login`)
4. Access to the project: `ttb-lang1`

---

## Local Testing (Recommended First Step)

### Option 1: Using Docker Compose

```bash
cd /Users/adamaslan/code/gcp\ app\ w\ mcp/mcp-finance1

# Build the image
docker build -f cloud-run/Dockerfile -t technical-analysis-api:latest .

# Run locally
docker run -p 8080:8080 \
  -e GCP_PROJECT_ID=ttb-lang1 \
  -e BUCKET_NAME=technical-analysis-data \
  technical-analysis-api:latest
```

### Option 2: Using Python venv

```bash
cd /Users/adamaslan/code/gcp\ app\ w\ mcp/mcp-finance1

# Create environment
mamba env create -f environment.yml -n mcp-test

# Activate
mamba activate mcp-test

# Install dependencies
pip install -r cloud-run/requirements.txt

# Run
cd cloud-run
python -m uvicorn main:app --host 0.0.0.0 --port 8080
```

### Run Integration Tests

```bash
# Test local instance
./test_endpoints.sh http://localhost:8080

# Test with verbose output
./test_endpoints.sh http://localhost:8080 true
```

**Expected Output:**
```
✅ Trade plan endpoint returns results
✅ Scan endpoint returns qualified trades
✅ Portfolio risk endpoint returns metrics
✅ Morning brief endpoint returns briefing
...
🎉 All tests passed!
```

---

## Deployment to Cloud Run

### Step 1: Set Project

```bash
gcloud config set project ttb-lang1
```

### Step 2: Verify Git Status

```bash
cd /Users/adamaslan/code/gcp\ app\ w\ mcp/mcp-finance1

# Check that code is committed
git status
git log --oneline -5
```

### Step 3: Deploy to Cloud Run

```bash
# Deploy from source (automatically builds and deploys)
gcloud run deploy technical-analysis-api \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars GCP_PROJECT_ID=ttb-lang1,BUCKET_NAME=technical-analysis-data \
  --timeout 3600 \
  --memory 2Gi \
  --cpu 2
```

**Note on flags:**
- `--source .` - Deploy from current directory
- `--allow-unauthenticated` - Allow public access (for testing)
- `--timeout 3600` - 1 hour timeout (for long-running analyses)
- `--memory 2Gi` - 2GB memory
- `--cpu 2` - 2 vCPU

### Step 4: Get the Deployed URL

```bash
# Get the service URL
gcloud run services list --filter="name:technical-analysis-api"

# Or get details
gcloud run services describe technical-analysis-api --region us-central1
```

The URL will be: `https://technical-analysis-api-XXXX.us-central1.run.app`

### Step 5: Test Deployed Instance

```bash
# Replace with your actual URL
export API_URL="https://technical-analysis-api-XXXX.us-central1.run.app"

# Run integration tests
./test_endpoints.sh $API_URL

# Test specific endpoint
curl -X POST $API_URL/api/trade-plan \
  -H "Content-Type: application/json" \
  -d '{"symbol":"AAPL"}'
```

---

## Rollback (If Something Goes Wrong)

### View Revisions

```bash
gcloud run revisions list --service=technical-analysis-api \
  --region=us-central1 \
  --limit=10
```

### Rollback to Previous Version

```bash
# Get the previous revision ID
PREV_REVISION=$(gcloud run revisions list \
  --service=technical-analysis-api \
  --region=us-central1 \
  --limit=2 \
  --format='value(name)' | tail -1)

# Route 100% traffic to previous version
gcloud run services update-traffic technical-analysis-api \
  --to-revisions $PREV_REVISION=100 \
  --region us-central1
```

### Delete Failed Revision

```bash
gcloud run revisions delete <REVISION_NAME> \
  --region us-central1
```

---

## Monitoring & Logs

### View Real-time Logs

```bash
# Stream logs
gcloud run services logs read technical-analysis-api \
  --region us-central1 \
  --follow

# Last 50 lines
gcloud run services logs read technical-analysis-api \
  --region us-central1 \
  --limit 50
```

### Check Service Status

```bash
gcloud run services describe technical-analysis-api \
  --region us-central1
```

### View Metrics in Cloud Console

1. Go to: https://console.cloud.google.com/run/detail/us-central1/technical-analysis-api
2. Click **Metrics** tab
3. View CPU, Memory, Request Rate, Latency

---

## Common Issues & Troubleshooting

### Issue: "MCP server functions not available"

**Symptom:** Endpoints return 503 error

**Solution:**
1. Check if `/workspace/src` path is correct
2. Ensure `technical_analysis_mcp` package is installed
3. Check logs: `gcloud run services logs read technical-analysis-api`

**Fix:**
```bash
# In Dockerfile, ensure these lines exist:
# WORKDIR /workspace
# COPY . .
# COPY src src
```

### Issue: "GCP_PROJECT_ID environment variable not set"

**Solution:**
```bash
gcloud run services update technical-analysis-api \
  --set-env-vars GCP_PROJECT_ID=ttb-lang1 \
  --region us-central1
```

### Issue: Timeout (request takes >60 seconds)

**Solution:** Increase timeout
```bash
gcloud run services update technical-analysis-api \
  --timeout 3600 \
  --region us-central1
```

### Issue: Out of Memory errors

**Solution:** Increase memory
```bash
gcloud run services update technical-analysis-api \
  --memory 4Gi \
  --region us-central1
```

---

## Performance Tuning

### Recommended Settings

```bash
gcloud run services update technical-analysis-api \
  --region us-central1 \
  --memory 2Gi \
  --cpu 2 \
  --concurrency 100 \
  --max-instances 10 \
  --timeout 3600
```

| Setting | Value | Reason |
|---------|-------|--------|
| Memory | 2-4 Gi | Data processing intensive |
| CPU | 2 | Multiple concurrent analyses |
| Concurrency | 100 | Handle multiple requests |
| Max Instances | 10 | Prevent runaway costs |
| Timeout | 3600s | Analysis can take 5+ min |

---

## Post-Deployment Verification

### Quick Checks

1. **Health Check**
   ```bash
   curl https://technical-analysis-api-XXXX.us-central1.run.app/
   ```
   Expected: `{"service":"Technical Analysis API","version":"2.0.0"}`

2. **Trade Plan Endpoint**
   ```bash
   curl -X POST https://technical-analysis-api-XXXX.us-central1.run.app/api/trade-plan \
     -H "Content-Type: application/json" \
     -d '{"symbol":"AAPL"}'
   ```
   Expected: Trade plan data with `symbol`, `timeframe`, `entry_price`, etc.

3. **Scan Endpoint**
   ```bash
   curl -X POST https://technical-analysis-api-XXXX.us-central1.run.app/api/scan \
     -H "Content-Type: application/json" \
     -d '{"universe":"sp500","max_results":3}'
   ```
   Expected: Array of qualified trades

4. **Run Full Test Suite**
   ```bash
   ./test_endpoints.sh https://technical-analysis-api-XXXX.us-central1.run.app true
   ```
   Expected: All tests pass

---

## Integration with Frontend

### Update Frontend Config (if needed)

The frontend should already have the correct URL in `.env`:

```env
# .env or .env.local in nextjs-mcp-finance/
MCP_CLOUD_RUN_URL=https://technical-analysis-api-1007181159506.us-central1.run.app
```

If deployed to a different URL, update:

```env
MCP_CLOUD_RUN_URL=https://technical-analysis-api-XXXX.us-central1.run.app
```

### Test Frontend Integration

1. Restart Next.js dev server:
   ```bash
   npm run dev
   ```

2. Navigate to `/analyze/AAPL` - should load trade plan data
3. Navigate to `/scanner` - should load scan results
4. Navigate to `/portfolio` - should calculate risk
5. Check dashboard - should show morning brief

---

## Cleanup (Removing Deployment)

### Delete Cloud Run Service

```bash
gcloud run services delete technical-analysis-api \
  --region us-central1
```

---

## Deployment Checklist

Before deploying to production:

- [ ] Code is committed to git
- [ ] Tested locally with `test_endpoints.sh`
- [ ] All 4 endpoints return 200 status
- [ ] Response structures match expected format
- [ ] Error handling works (invalid symbols return 500)
- [ ] Logs are being generated properly
- [ ] Environment variables are set correctly
- [ ] GCP project ID is correct
- [ ] Firestore/Storage permissions are configured
- [ ] API is set to allow-unauthenticated (for frontend access)
- [ ] Memory and CPU are sufficient
- [ ] Timeout is set high enough for analyses
- [ ] Frontend MCP_CLOUD_RUN_URL is updated (if URL changes)

---

## Useful gcloud Commands

```bash
# List all Cloud Run services
gcloud run services list

# Describe a service
gcloud run services describe technical-analysis-api --region us-central1

# View environment variables
gcloud run services describe technical-analysis-api --region us-central1 \
  --format='value(spec.template.spec.containers[0].env)'

# Update environment variable
gcloud run services update technical-analysis-api \
  --set-env-vars GCP_PROJECT_ID=ttb-lang1

# View traffic split
gcloud run services describe technical-analysis-api --region us-central1 \
  --format='value(status.traffic)'

# Update traffic split (canary deployment)
gcloud run services update-traffic technical-analysis-api \
  --to-revisions LATEST=90,PREVIOUS=10 \
  --region us-central1
```

---

## Support & Issues

For issues:
1. Check logs: `gcloud run services logs read technical-analysis-api --region us-central1`
2. Review MCP_INTEGRATION_ISSUES.md
3. Check IMPLEMENTATION_SUMMARY.md for endpoint details
4. Run local tests to isolate issues
