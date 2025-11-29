#!/bin/bash
# Test API endpoints

API_URL="${CLOUD_RUN_URL:-http://localhost:8080}"

echo "🧪 Testing Technical Analysis API"
echo "API URL: $API_URL"
echo ""

# Test health endpoint
echo "1. Testing health endpoint..."
curl -s ${API_URL}/health | jq '.'
echo ""s

# Test analyze endpoint (async)
echo "2. Testing analyze endpoint..."
curl -s -X POST ${API_URL}/api/analyze \
  -H "Content-Type: application/json" \
  -d '{"symbol": "AAPL", "period": "1mo", "include_ai": true}' \
  | jq '.'
echo ""

# Wait a bit for processing
echo "3. Waiting 10 seconds for analysis to complete..."
sleep 10

# Get signals
echo "4. Getting signals..."
curl -s ${API_URL}/api/signals/AAPL | jq '.'
echo ""

# Test compare endpoint
echo "5. Testing compare endpoint..."
curl -s -X POST ${API_URL}/api/compare \
  -H "Content-Type: application/json" \
  -d '{"symbols": ["AAPL", "MSFT", "GOOGL"]}' \
  | jq '.'
echo ""

echo "✅ API tests complete!"
```

---

### 12. Cleanup Script
**File**: `option2-gcp/scripts/cleanup.sh`

```bash
#!/bin/bash
# Cleanup GCP resources (use with caution!)

PROJECT_ID="${GCP_PROJECT_ID:-technical-analysis-prod}"
REGION="${GCP_REGION:-us-central1}"

echo "⚠️  WARNING: This will delete all GCP resources!"
read -p "Are you sure? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "Cleanup cancelled."
    exit 0
fi

echo "🗑️  Cleaning up GCP resources..."

# Delete Cloud Run service
gcloud run services delete technical-analysis-api --region=${REGION} --quiet

# Delete Cloud Functions
gcloud functions delete calculate-indicators --region=${REGION} --gen2 --quiet
gcloud functions delete detect-signals --region=${REGION} --gen2 --quiet
gcloud functions delete rank-signals-ai --region=${REGION} --gen2 --quiet

# Delete Pub/Sub topics
gcloud pubsub topics delete analyze-request --quiet
gcloud pubsub topics delete indicators-complete --quiet
gcloud pubsub topics delete signals-detected --quiet
gcloud pubsub topics delete analysis-complete --quiet
gcloud pubsub topics delete screen-request --quiet

# Delete Cloud Scheduler job
gcloud scheduler jobs delete daily-market-summary --location=${REGION} --quiet

# Delete Cloud Storage bucket (WARNING: deletes all data!)
# gsutil -m rm -r gs://technical-analysis-data

echo "✅ Cleanup complete!"
echo "Note: Firestore database not deleted (do manually if needed)"
