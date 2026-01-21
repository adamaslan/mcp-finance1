# MCP Finance Cloud Run Deployment Guide
**Complete deployment documentation and procedures**

---

## 📋 Documentation Overview

This directory contains complete deployment documentation for the MCP Finance backend on Google Cloud Run. Each document serves a specific purpose in the deployment lifecycle.

### Core Documents

| Document | Purpose | Audience | When to Use |
|----------|---------|----------|------------|
| **DEPLOYMENT-QUICKSTART.md** | Fast 5-minute deployment guide | DevOps/Backend Engineers | Starting a new deployment |
| **DEPLOYMENT-SETUP-REVIEW.md** | Comprehensive setup analysis | Tech Leads/Architects | Understanding the infrastructure |
| **DEPLOYMENT-LOG-TEMPLATE.md** | Deployment record template | DevOps Engineers | After each deployment |
| **DEPLOYMENT-README.md** | This document - Master guide | Everyone | Getting started |

### Supporting Documents

| Document | Purpose |
|----------|---------|
| **ENVIRONMENT-SETUP.md** | Local development environment setup |
| **DOCKER-SECURITY-SETUP.md** | Security best practices and testing |
| **Dockerfile** | Container build configuration |
| **terraform.tf** | Infrastructure as Code |

---

## 🚀 Quick Start

### New to this project?

1. **Read This First**: `DEPLOYMENT-SETUP-REVIEW.md` (10 min)
   - Understand the architecture
   - Review security posture
   - Check pre-deployment requirements

2. **For Deployment**: `DEPLOYMENT-QUICKSTART.md` (5-10 min)
   - Follow step-by-step commands
   - Deploy in under 10 minutes

3. **After Deployment**: `DEPLOYMENT-LOG-TEMPLATE.md`
   - Document your deployment
   - Verify all systems working
   - Keep records for auditing

---

## 📊 Deployment Flow

```
┌─────────────────────────────────┐
│  1. Review Setup (OPTIONAL)     │  Read DEPLOYMENT-SETUP-REVIEW.md
│     DEPLOYMENT-SETUP-REVIEW.md  │  (First time only)
└────────────┬────────────────────┘
             │
             ▼
┌─────────────────────────────────┐
│  2. Prepare Environment         │  Set PROJECT_ID, REGION, etc.
│                                 │  Create .env file
└────────────┬────────────────────┘
             │
             ▼
┌─────────────────────────────────┐
│  3. Quick Deployment            │  Follow DEPLOYMENT-QUICKSTART.md
│     5-10 minutes                │  1. Build Docker image
│                                 │  2. Push to Artifact Registry
│                                 │  3. Deploy to Cloud Run
│                                 │  4. Verify
└────────────┬────────────────────┘
             │
             ▼
┌─────────────────────────────────┐
│  4. Document Deployment         │  Copy & fill DEPLOYMENT-LOG-TEMPLATE.md
│     Post-deployment             │  Rename with [DATE]_DEPLOYMENT-LOG.md
│                                 │  Save for audit trail
└────────────┬────────────────────┘
             │
             ▼
┌─────────────────────────────────┐
│  5. Monitor & Maintain          │  Watch logs
│     Next 24 hours               │  Track metrics
│                                 │  Alert on errors
└─────────────────────────────────┘
```

---

## 🎯 Deployment Checklist

### Pre-Deployment (1-2 hours before)

- [ ] **Code Ready**
  - [ ] All tests passing locally
  - [ ] No uncommitted changes
  - [ ] Merge to main branch complete
  - [ ] Git commit SHA noted: `_________________`

- [ ] **Docker Verification**
  - [ ] Run `docker build` locally - passes
  - [ ] Run container - starts successfully
  - [ ] Health endpoint `/health` responds
  - [ ] No security warnings in logs

- [ ] **GCP Setup**
  - [ ] Project ID verified
  - [ ] Billing enabled
  - [ ] `gcloud auth login` successful
  - [ ] APIs enabled (see DEPLOYMENT-SETUP-REVIEW.md)

- [ ] **Terraform (if using IaC)**
  - [ ] `terraform validate` passes
  - [ ] `terraform plan` output reviewed
  - [ ] No destructive changes in plan

- [ ] **Environment Variables**
  - [ ] `.env` file created
  - [ ] All required vars set (GCP_PROJECT_ID, BUCKET_NAME)
  - [ ] No secrets hardcoded
  - [ ] `.env` added to .gitignore

### During Deployment (10-15 minutes)

- [ ] **Build Phase**
  - [ ] Docker image builds successfully
  - [ ] Image size is reasonable (~600-800 MB)
  - [ ] No warnings or errors

- [ ] **Push Phase**
  - [ ] Image pushed to Artifact Registry
  - [ ] Push completes without errors
  - [ ] Image is readable: `gcloud artifacts docker images list`

- [ ] **Deploy Phase**
  - [ ] Cloud Run deployment started
  - [ ] Terraform apply or gcloud deploy completes
  - [ ] Service URL returned
  - [ ] No deployment errors

### Post-Deployment (30 minutes)

- [ ] **Health Checks**
  - [ ] Service is ACTIVE
  - [ ] `/health` endpoint responds with 200
  - [ ] API documentation `/api/docs` accessible
  - [ ] No startup errors in logs

- [ ] **Smoke Tests**
  - [ ] Basic API endpoints working
  - [ ] Database connections (if applicable)
  - [ ] External service integrations (if applicable)
  - [ ] Error handling working

- [ ] **Monitoring Setup**
  - [ ] Logs viewable in Cloud Logging
  - [ ] Metrics appearing in dashboard
  - [ ] Error alerts configured
  - [ ] Team notified

- [ ] **Documentation**
  - [ ] Deployment log completed
  - [ ] Performance baseline recorded
  - [ ] Any issues documented
  - [ ] Team wiki updated

---

## 🛠️ Common Scenarios

### Scenario 1: First Time Deployment

**Time Required**: 30 minutes

```bash
# 1. Read documentation (10 min)
open DEPLOYMENT-SETUP-REVIEW.md

# 2. Run deployment (10 min)
# Follow steps in DEPLOYMENT-QUICKSTART.md

# 3. Document (10 min)
# Fill out DEPLOYMENT-LOG-TEMPLATE.md
```

### Scenario 2: Standard Maintenance Deployment

**Time Required**: 10 minutes

```bash
# 1. Build & push (5 min)
docker build -t mcp-backend:latest .
docker tag mcp-backend:latest ${REGISTRY}/${PROJECT_ID}/${REPO}/mcp-backend:latest
docker push ${REGISTRY}/${PROJECT_ID}/${REPO}/mcp-backend:latest

# 2. Deploy (2 min)
gcloud run deploy mcp-backend \
  --image=${REGISTRY}/${PROJECT_ID}/${REPO}/mcp-backend:latest \
  --region=us-central1 \
  --allow-unauthenticated \
  --env-file=.env

# 3. Verify (3 min)
curl https://mcp-backend-XXXXX.run.app/health
gcloud run services logs read mcp-backend --limit=20
```

### Scenario 3: Emergency Rollback

**Time Required**: 2 minutes

```bash
# Get previous revision
PREVIOUS=$(gcloud run revisions list --service=mcp-backend \
  --region=us-central1 --sort-by=~metadata.generation --limit=2 \
  --format='value(metadata.name)' | tail -1)

# Rollback
gcloud run services update-traffic mcp-backend \
  --to-revisions=${PREVIOUS}=100 --region=us-central1

# Verify
curl https://mcp-backend-XXXXX.run.app/health
```

---

## 📝 Post-Deployment Documentation

After each deployment, complete a deployment log:

```bash
# 1. Copy the template
cp DEPLOYMENT-LOG-TEMPLATE.md DEPLOYMENT-LOG-[DATE].md

# 2. Fill in details
# - Deployment date and time
# - Version deployed
# - Pre-deployment verification
# - Deployment metrics
# - Post-deployment verification
# - Any issues encountered
# - Performance baseline

# 3. Commit to git (optional but recommended)
git add DEPLOYMENT-LOG-[DATE].md
git commit -m "docs: deployment log for [version] on [date]"
```

**Example filename**: `DEPLOYMENT-LOG-2026-01-19.md`

---

## 🔍 Monitoring After Deployment

### First Hour (Critical)

```bash
# Watch for errors
watch -n 5 'gcloud run services logs read mcp-backend --limit=20 --filter="severity>=ERROR"'

# Monitor requests
gcloud monitoring read \
  --filter='resource.type="cloud_run_revision" AND resource.labels.service_name="mcp-backend"'

# Track latency
watch -n 10 'gcloud run services logs read mcp-backend --limit=100 | grep "latency"'
```

### Daily (Routine)

```bash
# Check service health
gcloud run services describe mcp-backend --region=us-central1

# Review error logs
gcloud run services logs read mcp-backend \
  --filter='severity>=ERROR' \
  --limit=50

# Monitor costs
gcloud billing accounts list
```

### Weekly (Maintenance)

```bash
# Review performance trends
# Open Cloud Console > Cloud Run > Metrics

# Update dependencies (if needed)
# Review terraform state for drift
terraform plan

# Review security posture
docker scout cves ${REGISTRY}/${PROJECT_ID}/${REPO}/mcp-backend:latest
```

---

## 🔐 Security Verification

After deployment, verify security posture:

```bash
# 1. Verify non-root execution
gcloud run services describe mcp-backend --region=us-central1 \
  --format='value(template.spec.containers[0].runAsUser)'

# 2. Check environment variables (for secrets)
gcloud run services describe mcp-backend --region=us-central1 \
  --format='value(template.spec.containers[0].env[].name)'

# 3. Verify authentication requirement
curl -i https://mcp-backend-XXXXX.run.app/health
# Should not require authentication for /health

# 4. Scan for vulnerabilities
trivy image ${REGISTRY}/${PROJECT_ID}/${REPO}/mcp-backend:latest
```

See `DOCKER-SECURITY-SETUP.md` for detailed security procedures.

---

## 📈 Performance Baseline

After stable deployment, establish baseline metrics:

```bash
# After 1 hour of normal traffic:

# 1. Average Response Time
gcloud monitoring read \
  --filter='resource.type="cloud_run_revision"' \
  --format=json | jq '.[] | .points[0].value.distribution_value.bucket_counts'

# 2. Error Rate
gcloud run services logs read mcp-backend --filter='severity=ERROR' | wc -l

# 3. CPU Usage
gcloud monitoring read \
  --filter='metric.type="run.googleapis.com/request_count"'

# 4. Memory Usage
gcloud monitoring read \
  --filter='resource.type="cloud_run_revision" AND resource.labels.service_name="mcp-backend"'
```

Document these in your deployment log for comparison with future deployments.

---

## 🐛 Troubleshooting

### Service Won't Start

```bash
# Check logs
gcloud run services logs read mcp-backend --region=us-central1 --limit=100

# Verify container works locally
docker run -p 8080:8080 --env-file=.env mcp-finance-backend:latest

# Check required env vars are set
gcloud run services describe mcp-backend --region=us-central1 \
  --format='value(template.spec.containers[0].env)'
```

### Health Check Failing

```bash
# Test endpoint directly
curl -v https://mcp-backend-XXXXX.run.app/health

# Check health check configuration
gcloud run services describe mcp-backend --region=us-central1 \
  --format='value(template.spec.containers[0].livenessProbe)'

# View container logs for health check errors
gcloud run services logs read mcp-backend --filter='health'
```

### High Latency/Errors

```bash
# Check resource allocation
gcloud run services describe mcp-backend --region=us-central1 \
  --format='value(template.spec.containers[0].resources.limits)'

# Check current traffic
gcloud run services describe mcp-backend --region=us-central1 \
  --format='value(status.traffic)'

# View slow request logs
gcloud run services logs read mcp-backend --filter='latency>1000'
```

See full troubleshooting in `DOCKER-SECURITY-SETUP.md`.

---

## 🔄 Update/Rollback Procedures

### Rolling Update

```bash
# Build new image
docker build -t mcp-backend:v2 .

# Tag and push
docker tag mcp-backend:v2 ${REGISTRY}/${PROJECT_ID}/${REPO}/mcp-backend:v2
docker push ${REGISTRY}/${PROJECT_ID}/${REPO}/mcp-backend:v2

# Deploy with traffic split (gradual rollout)
gcloud run deploy mcp-backend \
  --image=${REGISTRY}/${PROJECT_ID}/${REPO}/mcp-backend:v2 \
  --region=us-central1 \
  --no-traffic

# Split traffic (90/10 to test)
gcloud run services update-traffic mcp-backend \
  --to-revisions=LATEST=10,STABLE=90 \
  --region=us-central1

# Monitor for errors (5-10 minutes)
watch 'gcloud run services logs read mcp-backend --filter="severity>=ERROR"'

# Either increase traffic or rollback
# Increase traffic:
gcloud run services update-traffic mcp-backend \
  --to-revisions=LATEST=100 \
  --region=us-central1

# Or rollback:
gcloud run services update-traffic mcp-backend \
  --to-revisions=PREVIOUS=100 \
  --region=us-central1
```

### Quick Rollback

```bash
# Get previous revision
PREVIOUS=$(gcloud run revisions list --service=mcp-backend \
  --region=us-central1 --limit=2 --sort-by=~metadata.generation \
  --format='value(metadata.name)' | tail -1)

# Immediate rollback
gcloud run services update-traffic mcp-backend \
  --to-revisions=${PREVIOUS}=100 --region=us-central1

# Verify
curl https://mcp-backend-XXXXX.run.app/health
```

---

## 💰 Cost Management

### Understanding Cloud Run Pricing

- **Compute**: $0.00002400 per vCPU-second
- **Memory**: $0.0000025 per GB-second
- **Requests**: $0.40 per 1M requests
- **Free Tier**: 2M requests + 360k GB-seconds per month

### For mcp-backend (512Mi, 1 CPU, 0 min instances):

```
Scenario 1: 100K requests/month
  - Compute: 100K * 300ms * 1 CPU * $0.00002400 = ~$0.72
  - Memory: 100K * 300ms * 0.5GB * $0.0000025 = ~$0.04
  - Requests: Within free tier
  Total: ~$0.76/month (within free tier most months)

Scenario 2: 1M requests/month
  - Compute: 1M * 300ms * 1 CPU * $0.00002400 = ~$7.20
  - Memory: 1M * 300ms * 0.5GB * $0.0000025 = ~$0.38
  - Requests: (1M - 2M free) = $0
  Total: ~$7.58/month
```

### Cost Optimization

```bash
# 1. Set min instances to 0 (already configured)
gcloud run services update mcp-backend \
  --min-instances=0 --region=us-central1

# 2. Use smallest memory that works
gcloud run services update mcp-backend \
  --memory=512Mi --region=us-central1

# 3. Scale down max instances during low-traffic periods
gcloud run services update mcp-backend \
  --max-instances=5 --region=us-central1

# 4. Monitor actual costs
gcloud billing accounts list
# Then open: https://console.cloud.google.com/billing/
```

---

## 📚 Additional Resources

### Official Documentation
- [Cloud Run Documentation](https://cloud.google.com/run/docs)
- [Terraform Google Provider](https://registry.terraform.io/providers/hashicorp/google/latest/docs)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)

### Our Documentation
- Security Details: See `DOCKER-SECURITY-SETUP.md`
- Development Setup: See `ENVIRONMENT-SETUP.md`
- Infrastructure: See `terraform.tf`

### Tools & CLIs
- [gcloud CLI Reference](https://cloud.google.com/sdk/gcloud)
- [docker Documentation](https://docs.docker.com/)
- [Terraform Documentation](https://www.terraform.io/docs)

---

## 🤝 Getting Help

### For Deployment Issues

1. Check `DEPLOYMENT-SETUP-REVIEW.md` → Common Issues section
2. Check `DOCKER-SECURITY-SETUP.md` → Troubleshooting section
3. Review deployment logs: `gcloud run services logs read mcp-backend`

### For Development Questions

- See `ENVIRONMENT-SETUP.md` for local dev setup
- Check `main.py` source code for API details

### For Infrastructure Questions

- See `terraform.tf` for infrastructure code
- Review `DEPLOYMENT-SETUP-REVIEW.md` → Infrastructure section

---

## ✅ Deployment Sign-off Template

After successful deployment, confirm:

```
Deployment Date: [DATE]
Deployed Version: [VERSION/SHA]
Deployed By: [NAME]

Verification Complete: [ ] Yes / [ ] No
Issues Found: [ ] None / [ ] See log

Health Check: [ ] ✅ Passing
Logs Monitored: [ ] ✅ 24h
Performance Normal: [ ] ✅ Yes

Ready for Production: [ ] ✅ Approved / [ ] ⚠️ Issues / [ ] ❌ Rollback

Team Notified: [ ] Yes
Runbook Updated: [ ] Yes
Documentation Filed: [ ] Yes
```

---

## 📞 Support Contacts

- **Cloud Run Issues**: [GCP Support Portal](https://cloud.google.com/support)
- **Team Lead**: [Contact Info]
- **On-Call Engineer**: [Contact Info]
- **DevOps Team**: [Contact Info]

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-19 | Initial comprehensive deployment guide |

---

**Last Updated**: January 19, 2026
**Status**: ✅ Ready for Production Deployment
**Maintainer**: Infrastructure Team

---

## Next Steps

1. **First Time?** Start with `DEPLOYMENT-QUICKSTART.md`
2. **New to Project?** Read `DEPLOYMENT-SETUP-REVIEW.md`
3. **After Deployment?** Complete `DEPLOYMENT-LOG-[DATE].md`
4. **Need Details?** See specific document in table above

**Ready to deploy?** → Follow `DEPLOYMENT-QUICKSTART.md`
