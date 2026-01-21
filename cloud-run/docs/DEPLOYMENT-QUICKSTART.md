# Cloud Run Deployment Quick Start
**Fast-track deployment guide for experienced teams**

---

## Prerequisites (One-time Setup)

```bash
# Install/verify tools
gcloud --version          # Should be 480.0.0 or later
docker --version          # Should be 24.0 or later
terraform --version       # Should be 1.0 or later

# Authenticate with GCP
gcloud auth login
gcloud config set project YOUR_PROJECT_ID

# Set environment
export PROJECT_ID="your-gcp-project-id"
export REGION="us-central1"
export REGISTRY="us-central1-docker.pkg.dev"
export REPO="mcp-finance"
export IMAGE="mcp-backend"
```

---

## 5-Minute Deployment

### 1. Build Docker Image (2 min)

```bash
cd mcp-finance1/cloud-run

# Build locally
docker build -t ${IMAGE}:latest .

# Verify it runs
docker run -d -p 8080:8080 ${IMAGE}:latest
sleep 2
curl http://localhost:8080/health
docker stop $(docker ps -q)
```

**Expected Output**:
```json
{"status": "healthy"}
```

### 2. Push to Artifact Registry (1 min)

```bash
# Configure Docker
gcloud auth configure-docker ${REGISTRY}

# Tag image
docker tag ${IMAGE}:latest \
  ${REGISTRY}/${PROJECT_ID}/${REPO}/${IMAGE}:latest

# Push
docker push ${REGISTRY}/${PROJECT_ID}/${REPO}/${IMAGE}:latest
```

### 3. Deploy to Cloud Run (2 min)

```bash
# Deploy with optimal settings
gcloud run deploy mcp-backend \
  --image=${REGISTRY}/${PROJECT_ID}/${REPO}/${IMAGE}:latest \
  --region=${REGION} \
  --platform=managed \
  --allow-unauthenticated \
  --memory=512Mi \
  --cpu=1 \
  --min-instances=0 \
  --max-instances=10 \
  --port=8080 \
  --env-file=.env \
  --no-gen2

# Get service URL
SERVICE_URL=$(gcloud run services describe mcp-backend \
  --region=${REGION} --format='value(status.url)')

echo "Deployment complete!"
echo "Service URL: $SERVICE_URL"
```

### 4. Verify Deployment (30 sec)

```bash
# Test endpoint
curl ${SERVICE_URL}/health

# View logs
gcloud run services logs read mcp-backend --region=${REGION} --limit=20
```

---

## Infrastructure as Code Deployment

### Option A: Terraform (Recommended for Production)

```bash
# Initialize Terraform
cd mcp-finance1/cloud-run
terraform init

# Plan deployment
terraform plan -var="project_id=${PROJECT_ID}" -out=tfplan

# Review plan output carefully, then apply
terraform apply tfplan

# Get outputs
terraform output -raw api_url
```

### Option B: Shell Script

```bash
# Quick automated deployment
cd mcp-finance1/automation
chmod +x deploy.sh
./deploy.sh ${PROJECT_ID}
```

---

## Health Check & Verification

```bash
# 1. Service health
gcloud run services describe mcp-backend --region=${REGION}

# 2. Endpoint test
curl -i ${SERVICE_URL}/health
curl -i ${SERVICE_URL}/api/docs

# 3. View metrics (wait 2-3 minutes for data)
gcloud monitoring time-series list \
  --filter='resource.type="cloud_run_revision" AND resource.labels.service_name="mcp-backend"' \
  --format=json | jq '.timeSeries[] | {metric: .metric.type, value: .points[0].value}'

# 4. Check error logs
gcloud run services logs read mcp-backend \
  --region=${REGION} \
  --filter='severity>=ERROR' \
  --limit=50
```

---

## Post-Deployment Monitoring

### Real-time Logs
```bash
# Stream logs live
gcloud run services logs read mcp-backend --follow --region=${REGION}

# Filter by severity
gcloud run services logs read mcp-backend --filter='severity>=WARNING' --region=${REGION}
```

### Metrics Dashboard
```bash
# Create simple metrics query
gcloud monitoring time-series list \
  --filter='resource.type="cloud_run_revision" AND resource.labels.service_name="mcp-backend"'
```

### Quick Troubleshooting
```bash
# Check if service is running
gcloud run services describe mcp-backend --region=${REGION} \
  --format='value(status.conditions[0].status)'

# Get service URL
gcloud run services describe mcp-backend --region=${REGION} \
  --format='value(status.url)'

# Check latest revision
gcloud run revisions list --service=mcp-backend --region=${REGION} \
  --limit=1 --format='value(metadata.name)'
```

---

## Rollback Procedure

### Quick Rollback (< 1 minute)

```bash
# Get previous revision SHA
PREVIOUS_REVISION=$(gcloud run revisions list \
  --service=mcp-backend \
  --region=${REGION} \
  --sort-by=~metadata.generation \
  --limit=2 \
  --format='value(metadata.name)' | tail -1)

# Route traffic back
gcloud run services update-traffic mcp-backend \
  --to-revisions=${PREVIOUS_REVISION}=100 \
  --region=${REGION}

# Verify
gcloud run services describe mcp-backend --region=${REGION} \
  --format='value(status.traffic[0].revisionName)'
```

---

## Environment Variables

### .env File Template
```bash
# Create and populate .env
cat > .env << 'EOF'
GCP_PROJECT_ID=your-project-id
BUCKET_NAME=your-bucket-name
LOG_LEVEL=INFO
PORT=8080
EOF

# Security note: Never commit .env file
echo ".env" >> .gitignore
```

### Update Running Service
```bash
# Update specific env var
gcloud run services update mcp-backend \
  --update-env-vars=GCP_PROJECT_ID=new-value \
  --region=${REGION}

# View current env vars
gcloud run services describe mcp-backend \
  --region=${REGION} \
  --format='value(template.spec.containers[0].env)'
```

---

## Cost Optimization

### Enable Min Scale 0 (Already Configured)
```bash
# Verify min instances is 0
gcloud run services describe mcp-backend --region=${REGION} \
  --format='value(template.metadata.annotations."autoscaling.knative.dev/minScale")'

# If not 0, update it
gcloud run services update mcp-backend \
  --min-instances=0 \
  --region=${REGION}
```

### View Estimated Costs
```bash
# Cloud Run always-free tier includes:
# - 2,000,000 requests per month
# - 360,000 GB-seconds per month
# - 1 GB Cloud Storage

# Current project costs
gcloud billing accounts list
# Then view: https://console.cloud.google.com/billing/

# Quick estimate: 100K requests/month = ~$0.20
```

---

## Common Operations

### Restart Service (Cold Start)
```bash
# Deploy same image (forces restart)
gcloud run deploy mcp-backend \
  --image=${REGISTRY}/${PROJECT_ID}/${REPO}/${IMAGE}:latest \
  --region=${REGION} \
  --no-traffic
```

### Update Configuration Only
```bash
# No redeployment needed
gcloud run services update mcp-backend \
  --memory=512Mi \
  --cpu=1 \
  --timeout=300 \
  --region=${REGION}
```

### Scale Configuration
```bash
# Adjust auto-scaling
gcloud run services update mcp-backend \
  --min-instances=1 \
  --max-instances=100 \
  --region=${REGION}
```

### View Detailed Status
```bash
gcloud run services describe mcp-backend --region=${REGION}

# Or just traffic split
gcloud run services describe mcp-backend --region=${REGION} \
  --format='table(status.traffic[].revisionName, status.traffic[].percent)'
```

---

## Debugging

### Check Container Runtime Issues
```bash
# Get latest revision name
LATEST=$(gcloud run revisions list --service=mcp-backend \
  --region=${REGION} --limit=1 --format='value(metadata.name)')

# View revision details
gcloud run revisions describe ${LATEST} --region=${REGION}

# Check if revision is serving
gcloud run revisions describe ${LATEST} --region=${REGION} \
  --format='value(status.conditions[0].status)'
```

### Test with Local Docker
```bash
# Pull and test production image
docker pull ${REGISTRY}/${PROJECT_ID}/${REPO}/${IMAGE}:latest

# Run with same env vars
docker run --env-file=.env \
  -p 8080:8080 \
  ${REGISTRY}/${PROJECT_ID}/${REPO}/${IMAGE}:latest

# Test in container
curl http://localhost:8080/health
```

### View Service Account Permissions
```bash
# Get service account email
SERVICE_ACCOUNT=$(gcloud run services describe mcp-backend \
  --region=${REGION} \
  --format='value(template.spec.serviceAccountName)')

# View its roles
gcloud projects get-iam-policy ${PROJECT_ID} \
  --flatten="bindings[].members" \
  --filter="bindings.members:${SERVICE_ACCOUNT}" \
  --format='table(bindings.role)'
```

---

## One-liner Commands

```bash
# Deploy in one command
docker build -t mcp-backend . && docker tag mcp-backend:latest ${REGISTRY}/${PROJECT_ID}/${REPO}/mcp-backend:latest && docker push ${REGISTRY}/${PROJECT_ID}/${REPO}/mcp-backend:latest && gcloud run deploy mcp-backend --image=${REGISTRY}/${PROJECT_ID}/${REPO}/mcp-backend:latest --region=${REGION} --allow-unauthenticated --env-file=.env

# Quick health check
curl $(gcloud run services describe mcp-backend --region=${REGION} --format='value(status.url)')/health

# Tail logs with grep
gcloud run services logs read mcp-backend --follow --region=${REGION} | grep -v "INFO"

# Get service URL and test
curl $(gcloud run services describe mcp-backend --region=${REGION} --format='value(status.url)')/api/docs
```

---

## Emergency Procedures

### Emergency Rollback
```bash
# 1. Stop traffic immediately
gcloud run services update-traffic mcp-backend --to-revisions=NONE --region=${REGION}

# 2. Check health of previous revision
gcloud run revisions list --service=mcp-backend --region=${REGION} --limit=2

# 3. Restore traffic
gcloud run services update-traffic mcp-backend --to-revisions=PREVIOUS_REVISION=100 --region=${REGION}
```

### Scale Down for Cost
```bash
# Immediate cost reduction
gcloud run services update mcp-backend \
  --min-instances=0 \
  --max-instances=1 \
  --region=${REGION}
```

### Delete Service
```bash
# Use with caution!
gcloud run services delete mcp-backend --region=${REGION}
```

---

## Quick Reference Links

- **Cloud Console**: https://console.cloud.google.com/run
- **Artifact Registry**: https://console.cloud.google.com/artifacts
- **Cloud Logging**: https://console.cloud.google.com/logs
- **Billing**: https://console.cloud.google.com/billing
- **gcloud CLI Reference**: https://cloud.google.com/sdk/gcloud/reference/run

---

## Next Steps

After successful deployment, see:
- `DEPLOYMENT-LOG-TEMPLATE.md` - Document your deployment
- `DEPLOYMENT-SETUP-REVIEW.md` - Full setup analysis
- `DOCKER-SECURITY-SETUP.md` - Security verification
- `ENVIRONMENT-SETUP.md` - Development environment

---

**Quick Start Version**: 1.0
**Last Updated**: January 19, 2026
**Estimated Time**: 5-10 minutes to first deployment
