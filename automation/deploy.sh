#!/bin/bash
#
# Deploy Automated Stock Analysis Pipeline to GCP
# Usage: ./deploy.sh <project-id>
#
# API key is read from ../.env file (never pass as command line argument)
#
set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }
log_step() { echo -e "${BLUE}[STEP]${NC} $1"; }

# Configuration
PROJECT_ID="${1:-}"
REGION="us-central1"
FUNCTION_NAME="daily-stock-analysis"
TOPIC_NAME="daily-analysis-trigger"
SCHEDULER_JOB="daily-analysis-job"

# Read API key from .env file (secure - not from command line)
GEMINI_API_KEY=""
if [[ -f "../.env" ]]; then
    GEMINI_API_KEY=$(grep -E "^GEMINI_API_KEY=" ../.env | cut -d '=' -f2 | tr -d '"' | tr -d "'")
fi

# Validate inputs
if [[ -z "$PROJECT_ID" ]]; then
    log_error "Usage: ./deploy.sh <project-id>"
    log_error "  project-id: Your GCP project ID"
    log_error ""
    log_error "API key is read from ../.env file automatically"
    exit 1
fi

if [[ -z "$GEMINI_API_KEY" ]]; then
    log_error "Gemini API key not found in ../.env file"
    log_error "Add this line to your .env file:"
    log_error "  GEMINI_API_KEY=your-api-key-here"
    log_error ""
    log_error "Get your API key at: https://aistudio.google.com/app/apikey"
    exit 1
fi

echo ""
echo "============================================================"
echo "  GCP AUTOMATED STOCK ANALYSIS PIPELINE DEPLOYMENT"
echo "============================================================"
echo ""
echo "Project ID:  $PROJECT_ID"
echo "Region:      $REGION"
echo "Function:    $FUNCTION_NAME"
echo "API Key:     ${GEMINI_API_KEY:0:10}...${GEMINI_API_KEY: -4}"
echo ""

# Confirm
read -p "Continue with deployment? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    log_warn "Deployment cancelled"
    exit 0
fi

# Step 1: Set project
log_step "1/7 Setting GCP project..."
gcloud config set project "$PROJECT_ID" 2>/dev/null || {
    log_error "Failed to set project. Make sure project exists and you have access."
    exit 1
}
log_info "Project set to $PROJECT_ID"

# Step 2: Enable APIs
log_step "2/7 Enabling required APIs..."
apis=(
    "cloudfunctions.googleapis.com"
    "cloudscheduler.googleapis.com"
    "firestore.googleapis.com"
    "pubsub.googleapis.com"
    "cloudbuild.googleapis.com"
    "run.googleapis.com"
    "artifactregistry.googleapis.com"
)

for api in "${apis[@]}"; do
    echo "  Enabling $api..."
    gcloud services enable "$api" --quiet 2>/dev/null || true
done
log_info "APIs enabled"

# Step 3: Create Firestore database (if not exists)
log_step "3/7 Setting up Firestore..."
gcloud firestore databases create --location=nam5 --quiet 2>/dev/null || {
    log_info "Firestore already exists or using default"
}

# Step 4: Create Pub/Sub topic
log_step "4/7 Creating Pub/Sub topic..."
gcloud pubsub topics create "$TOPIC_NAME" --quiet 2>/dev/null || {
    log_info "Topic $TOPIC_NAME already exists"
}

# Step 5: Deploy Cloud Function
log_step "5/7 Deploying Cloud Function..."
cd functions/daily_analysis

gcloud functions deploy "$FUNCTION_NAME" \
    --gen2 \
    --runtime=python311 \
    --region="$REGION" \
    --source=. \
    --entry-point=daily_analysis_pubsub \
    --trigger-topic="$TOPIC_NAME" \
    --memory=512Mi \
    --timeout=540s \
    --set-env-vars="GEMINI_API_KEY=${GEMINI_API_KEY},GCP_PROJECT_ID=${PROJECT_ID}" \
    --max-instances=1 \
    --quiet

cd ../..
log_info "Cloud Function deployed"

# Step 6: Create Cloud Scheduler job
log_step "6/7 Creating Cloud Scheduler job..."

# Delete existing job if exists
gcloud scheduler jobs delete "$SCHEDULER_JOB" \
    --location="$REGION" \
    --quiet 2>/dev/null || true

# Create new job - Run Mon-Fri at 4:30 PM ET (market close + 30 min)
gcloud scheduler jobs create pubsub "$SCHEDULER_JOB" \
    --location="$REGION" \
    --schedule="30 16 * * 1-5" \
    --time-zone="America/New_York" \
    --topic="$TOPIC_NAME" \
    --message-body='{"trigger": "scheduled", "type": "daily"}' \
    --quiet

log_info "Scheduler job created (Mon-Fri 4:30 PM ET)"

# Step 7: Test the deployment
log_step "7/7 Testing deployment..."

echo ""
echo "============================================================"
echo "  DEPLOYMENT COMPLETE!"
echo "============================================================"
echo ""
echo "Resources created:"
echo "  ✓ Cloud Function: $FUNCTION_NAME"
echo "  ✓ Pub/Sub Topic:  $TOPIC_NAME"
echo "  ✓ Scheduler Job:  $SCHEDULER_JOB (Mon-Fri 4:30 PM ET)"
echo "  ✓ Firestore DB:   (default)"
echo ""
echo "Monthly Cost Estimate: \$0 (within free tier)"
echo ""
echo "Commands:"
echo "  # Trigger analysis manually"
echo "  gcloud scheduler jobs run $SCHEDULER_JOB --location=$REGION"
echo ""
echo "  # View function logs"
echo "  gcloud functions logs read $FUNCTION_NAME --region=$REGION --limit=100"
echo ""
echo "  # View results in Firestore"
echo "  open https://console.cloud.google.com/firestore/databases/-default-/data?project=$PROJECT_ID"
echo ""
echo "  # Check scheduler status"
echo "  gcloud scheduler jobs describe $SCHEDULER_JOB --location=$REGION"
echo ""

# Ask to run test
read -p "Run a test analysis now? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    log_info "Triggering test run..."
    gcloud scheduler jobs run "$SCHEDULER_JOB" --location="$REGION"
    echo ""
    log_info "Test triggered! View logs with:"
    echo "  gcloud functions logs read $FUNCTION_NAME --region=$REGION --limit=100"
fi
