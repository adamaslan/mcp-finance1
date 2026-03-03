#!/bin/bash

#
# GCP Cache Infrastructure Deployment Script
# Deploys all 7 cache layers to GCP
#
# Usage: ./deploy_gcp_cache_infrastructure.sh [PROJECT_ID] [REGION]
#

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ID="${1:-ttb-lang1}"
REGION="${2:-us-central1}"
SERVICE_ACCOUNT="1007181159506-compute@developer.gserviceaccount.com"

echo -e "${YELLOW}========================================${NC}"
echo -e "${YELLOW}GCP Cache Infrastructure Deployment${NC}"
echo -e "${YELLOW}Project: $PROJECT_ID${NC}"
echo -e "${YELLOW}Region: $REGION${NC}"
echo -e "${YELLOW}========================================${NC}"
echo ""

# ============================================================================
# Helper Functions
# ============================================================================

log_info() {
    echo -e "${GREEN}✓${NC} $1"
}

log_error() {
    echo -e "${RED}✗${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}⚠${NC} $1"
}

section() {
    echo ""
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${YELLOW}$1${NC}"
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

# ============================================================================
# Layer 0: Secret Manager (API Keys)
# ============================================================================

deploy_secret_manager() {
    section "Deploying Layer 0: Secret Manager"

    # Create Finnhub API key secret
    if gcloud secrets describe finnhub-api-key --project=$PROJECT_ID &>/dev/null; then
        log_info "Finnhub API key secret already exists"
    else
        log_warn "Finnhub API key secret not found. Create manually:"
        echo "  gcloud secrets create finnhub-api-key --project=$PROJECT_ID --replication-policy=automatic --data-file=-"
        echo "  # Paste your key, then Ctrl+D"
    fi

    # Create Alpha Vantage API key secret
    if gcloud secrets describe alpha-vantage-api-key --project=$PROJECT_ID &>/dev/null; then
        log_info "Alpha Vantage API key secret already exists"
    else
        log_warn "Alpha Vantage API key secret not found. Create manually:"
        echo "  gcloud secrets create alpha-vantage-api-key --project=$PROJECT_ID --replication-policy=automatic --data-file=-"
        echo "  # Paste your key, then Ctrl+D"
    fi

    # Grant service account access to secrets
    for secret in finnhub-api-key alpha-vantage-api-key; do
        if gcloud secrets describe $secret --project=$PROJECT_ID &>/dev/null; then
            gcloud secrets add-iam-policy-binding $secret \
                --project=$PROJECT_ID \
                --member=serviceAccount:$SERVICE_ACCOUNT \
                --role=roles/secretmanager.secretAccessor \
                --quiet 2>/dev/null || log_warn "Could not grant access to $secret"
            log_info "Granted secret access: $secret"
        fi
    done
}

# ============================================================================
# Layer 1: Memorystore/Redis
# ============================================================================

deploy_redis() {
    section "Deploying Layer 1: Memorystore/Redis"

    INSTANCE_NAME="mcp-cache-prod"

    if gcloud redis instances describe $INSTANCE_NAME --region=$REGION --project=$PROJECT_ID &>/dev/null; then
        log_info "Redis instance already exists: $INSTANCE_NAME"
    else
        log_info "Creating Redis instance: $INSTANCE_NAME"
        gcloud redis instances create $INSTANCE_NAME \
            --size=1 \
            --region=$REGION \
            --redis-version=7.2 \
            --project=$PROJECT_ID \
            --quiet

        log_info "Redis instance created"
    fi

    # Get connection details
    HOST=$(gcloud redis instances describe $INSTANCE_NAME \
        --region=$REGION \
        --project=$PROJECT_ID \
        --format="value(host)")
    PORT=$(gcloud redis instances describe $INSTANCE_NAME \
        --region=$REGION \
        --project=$PROJECT_ID \
        --format="value(port)")

    log_info "Redis connection: $HOST:$PORT"
    echo "  Add to .env.gcp:"
    echo "    REDIS_HOST=$HOST"
    echo "    REDIS_PORT=$PORT"
}

# ============================================================================
# Layer 2a: Firestore
# ============================================================================

deploy_firestore() {
    section "Deploying Layer 2a: Firestore"

    # Check if Firestore is enabled
    if gcloud firestore databases list --project=$PROJECT_ID &>/dev/null; then
        log_info "Firestore is already enabled"
    else
        log_info "Enabling Firestore"
        gcloud firestore databases create \
            --region=$REGION \
            --project=$PROJECT_ID \
            --quiet
        log_info "Firestore created in region: $REGION"
    fi

    # Create TTL policy for auto-cleanup
    log_info "Firestore configured (TTL policies managed at collection level)"
}

# ============================================================================
# Layer 2b: Cloud Storage
# ============================================================================

deploy_cloud_storage() {
    section "Deploying Layer 2b: Cloud Storage"

    BUCKET_NAME="mcp-cache-historical"

    if gsutil ls -b "gs://$BUCKET_NAME" &>/dev/null; then
        log_info "Cloud Storage bucket already exists: gs://$BUCKET_NAME"
    else
        log_info "Creating Cloud Storage bucket: gs://$BUCKET_NAME"
        gsutil mb -p $PROJECT_ID -l $REGION "gs://$BUCKET_NAME"
        log_info "Bucket created"
    fi

    # Set lifecycle policy (delete old data after 30 days)
    cat > /tmp/bucket_lifecycle.json <<EOF
{
  "lifecycle": {
    "rule": [
      {
        "action": {"type": "Delete"},
        "condition": {"age": 30}
      }
    ]
  }
}
EOF

    gsutil lifecycle set /tmp/bucket_lifecycle.json "gs://$BUCKET_NAME" || log_warn "Could not set lifecycle policy"
    log_info "Lifecycle policy configured (30-day auto-delete)"

    # Grant service account access
    gsutil iam ch "serviceAccount:$SERVICE_ACCOUNT:objectAdmin" "gs://$BUCKET_NAME" 2>/dev/null || log_warn "Could not grant bucket access"
    log_info "Bucket access configured"

    echo "  Add to .env.gcp:"
    echo "    BUCKET_NAME=$BUCKET_NAME"
}

# ============================================================================
# Layer 3: BigQuery
# ============================================================================

deploy_bigquery() {
    section "Deploying Layer 3: BigQuery"

    DATASET_ID="mcp_cache"

    # Create dataset if not exists
    if bq ls -d --project_id=$PROJECT_ID | grep -q $DATASET_ID; then
        log_info "BigQuery dataset already exists: $DATASET_ID"
    else
        log_info "Creating BigQuery dataset: $DATASET_ID"
        bq mk --dataset \
            --project_id=$PROJECT_ID \
            --location=$REGION \
            --description="MCP cache pre-computed data" \
            $DATASET_ID
        log_info "Dataset created"
    fi

    # Note about materialized views
    log_info "Create materialized views manually when market data tables are available"
    echo "  Example materialized view (run in BigQuery console):"
    echo "    CREATE OR REPLACE MATERIALIZED VIEW \`$PROJECT_ID.$DATASET_ID.daily_analysis\` AS"
    echo "    SELECT"
    echo "      symbol,"
    echo "      DATE(timestamp) as trade_date,"
    echo "      APPROX_QUANTILES(close, 100)[OFFSET(50)] as median_price,"
    echo "      MAX(close) as high,"
    echo "      MIN(close) as low,"
    echo "      AVG(close) as avg_price,"
    echo "      STDDEV(close) as volatility"
    echo "    FROM \`$PROJECT_ID.market_data.prices\`"
    echo "    WHERE timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 2 YEAR)"
    echo "    GROUP BY symbol, DATE(timestamp)"
}

# ============================================================================
# Layer 4: Cloud Tasks
# ============================================================================

deploy_cloud_tasks() {
    section "Deploying Layer 4: Cloud Tasks"

    QUEUE_NAME="mcp-cache-refresh"

    # Check if queue exists
    if gcloud tasks queues describe $QUEUE_NAME \
        --location=$REGION \
        --project=$PROJECT_ID &>/dev/null; then
        log_info "Cloud Tasks queue already exists: $QUEUE_NAME"
    else
        log_info "Creating Cloud Tasks queue: $QUEUE_NAME"
        gcloud tasks queues create $QUEUE_NAME \
            --location=$REGION \
            --project=$PROJECT_ID

        log_info "Queue created"
    fi

    # Configure retry policy
    gcloud tasks queues update $QUEUE_NAME \
        --location=$REGION \
        --project=$PROJECT_ID \
        --max-attempts=5 \
        --max-retry-delay=600s \
        --min-retry-delay=5s \
        --max-doublings=4 \
        --quiet || log_warn "Could not update queue retry policy"

    log_info "Queue configured with retry policy"

    echo "  Add to .env.gcp:"
    echo "    CLOUD_TASKS_QUEUE=$QUEUE_NAME"
    echo "    CLOUD_TASKS_REGION=$REGION"
}

# ============================================================================
# IAM Permissions
# ============================================================================

grant_iam_permissions() {
    section "Granting IAM Permissions to Service Account"

    ROLES=(
        "roles/redis.client"
        "roles/datastore.user"
        "roles/storage.objectAdmin"
        "roles/bigquery.dataEditor"
        "roles/cloudtasks.taskRunner"
        "roles/secretmanager.secretAccessor"
    )

    for role in "${ROLES[@]}"; do
        log_info "Granting $role to service account"
        gcloud projects add-iam-policy-binding $PROJECT_ID \
            --member=serviceAccount:$SERVICE_ACCOUNT \
            --role=$role \
            --quiet 2>/dev/null || log_warn "Could not grant $role"
    done

    log_info "IAM permissions configured"
}

# ============================================================================
# Environment Configuration
# ============================================================================

generate_env_file() {
    section "Generating .env.gcp Configuration"

    # Get Redis details
    REDIS_HOST=$(gcloud redis instances describe mcp-cache-prod \
        --region=$REGION \
        --project=$PROJECT_ID \
        --format="value(host)" 2>/dev/null || echo "localhost")
    REDIS_PORT=$(gcloud redis instances describe mcp-cache-prod \
        --region=$REGION \
        --project=$PROJECT_ID \
        --format="value(port)" 2>/dev/null || echo "6379")

    cat > .env.gcp <<EOF
# GCP Cache Configuration
# Generated: $(date)

# Project
GCP_PROJECT_ID=$PROJECT_ID
REGION=$REGION

# Layer 0: Secret Manager
# (API keys stored in Secret Manager, no .env needed)

# Layer 1: Memorystore/Redis
REDIS_HOST=$REDIS_HOST
REDIS_PORT=$REDIS_PORT

# Layer 2b: Cloud Storage
BUCKET_NAME=mcp-cache-historical

# Layer 3: BigQuery
# (Automatically uses GCP_PROJECT_ID)

# Layer 4: Cloud Tasks
CLOUD_TASKS_QUEUE=mcp-cache-refresh
CLOUD_TASKS_REGION=$REGION
CACHE_REFRESH_URL=https://mcp-backend.cloud.run/api/cache-refresh

# Cloud Run Deployment
SERVICE_NAME=mcp-backend
MEMORY=2Gi
CPU=2
TIMEOUT=3600
EOF

    log_info "Configuration generated: .env.gcp"
    cat .env.gcp
}

# ============================================================================
# Verification
# ============================================================================

verify_deployment() {
    section "Verifying Deployment"

    echo "Testing each layer:"

    # L0: Secret Manager
    if gcloud secrets describe finnhub-api-key --project=$PROJECT_ID &>/dev/null; then
        log_info "L0 Secret Manager: OK"
    else
        log_warn "L0 Secret Manager: Secrets not created"
    fi

    # L1: Redis
    if gcloud redis instances describe mcp-cache-prod --region=$REGION --project=$PROJECT_ID &>/dev/null; then
        log_info "L1 Memorystore/Redis: OK"
    else
        log_error "L1 Memorystore/Redis: FAILED"
    fi

    # L2a: Firestore
    if gcloud firestore databases list --project=$PROJECT_ID &>/dev/null; then
        log_info "L2a Firestore: OK"
    else
        log_error "L2a Firestore: FAILED"
    fi

    # L2b: Cloud Storage
    if gsutil ls -b "gs://mcp-cache-historical" &>/dev/null; then
        log_info "L2b Cloud Storage: OK"
    else
        log_error "L2b Cloud Storage: FAILED"
    fi

    # L3: BigQuery
    if bq ls -d --project_id=$PROJECT_ID | grep -q mcp_cache; then
        log_info "L3 BigQuery: OK"
    else
        log_error "L3 BigQuery: FAILED"
    fi

    # L4: Cloud Tasks
    if gcloud tasks queues describe mcp-cache-refresh --location=$REGION --project=$PROJECT_ID &>/dev/null; then
        log_info "L4 Cloud Tasks: OK"
    else
        log_error "L4 Cloud Tasks: FAILED"
    fi

    echo ""
    log_info "Deployment verification complete"
}

# ============================================================================
# Main Execution
# ============================================================================

main() {
    # Verify gcloud is installed
    if ! command -v gcloud &>/dev/null; then
        log_error "gcloud CLI is not installed"
        exit 1
    fi

    # Set current project
    gcloud config set project $PROJECT_ID

    # Run deployment steps
    deploy_secret_manager
    deploy_redis
    deploy_firestore
    deploy_cloud_storage
    deploy_bigquery
    deploy_cloud_tasks
    grant_iam_permissions
    generate_env_file
    verify_deployment

    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}Deployment Complete!${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. Review .env.gcp and ensure all values are correct"
    echo "  2. Copy .env.gcp values to Cloud Run environment"
    echo "  3. Deploy backend: gcloud run deploy mcp-backend --source . --env-vars-file=.env.gcp"
    echo "  4. Run health check: python src/technical_analysis_mcp/cache/health_check.py"
    echo ""
}

main "$@"
