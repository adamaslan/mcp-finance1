# /deploy - GCP Deployment Automation

Deploy the Cloud Function to GCP with validation, testing, and rollback support.

## Usage

```
/deploy [OPTIONS]
```

**Options:**
- `/deploy` - Deploy to default project (from .env or gcloud config)
- `/deploy --project PROJECT_ID` - Deploy to specific project
- `/deploy --test` - Deploy and trigger a test run
- `/deploy --dry-run` - Show what would happen without deploying
- `/deploy --logs` - Show deployment logs after completion

**Examples:**
- `/deploy` - Standard deployment
- `/deploy --test` - Deploy and verify with test execution
- `/deploy --dry-run --project ttb-lang1` - Preview deployment

## Behavior

When this skill is invoked:

1. **Pre-flight checks**:
   - Verify .env file exists and has GEMINI_API_KEY
   - Check gcloud CLI is authenticated
   - Validate project access
   - Ensure required APIs are enabled

2. **Deploy**:
   - Run `automation/deploy.sh` or direct gcloud commands
   - Monitor deployment progress
   - Capture deployment output

3. **Post-deployment**:
   - Verify function is ACTIVE
   - Optionally trigger test execution
   - Show function URL and logs command

## Implementation Steps

### Step 1: Pre-flight Validation

```bash
# Check .env exists
if [[ ! -f ".env" ]]; then
    echo "ERROR: .env file not found"
    echo "Create .env with GEMINI_API_KEY=your-key"
    exit 1
fi

# Check GEMINI_API_KEY is set
GEMINI_API_KEY=$(grep -E "^GEMINI_API_KEY=" .env | cut -d '=' -f2 | tr -d '"' | tr -d "'")
if [[ -z "$GEMINI_API_KEY" ]]; then
    echo "ERROR: GEMINI_API_KEY not found in .env"
    exit 1
fi
echo "✓ API key validated: ${GEMINI_API_KEY:0:10}...${GEMINI_API_KEY: -4}"

# Check gcloud auth
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | head -1 > /dev/null 2>&1; then
    echo "ERROR: Not authenticated with gcloud"
    echo "Run: gcloud auth login"
    exit 1
fi
echo "✓ gcloud authenticated"

# Get project ID
PROJECT_ID=$(gcloud config get-value project 2>/dev/null)
if [[ -z "$PROJECT_ID" ]]; then
    echo "ERROR: No GCP project configured"
    echo "Run: gcloud config set project YOUR_PROJECT_ID"
    exit 1
fi
echo "✓ Project: $PROJECT_ID"
```

### Step 2: Deploy Cloud Function

```bash
cd automation/functions/daily_analysis

gcloud functions deploy daily-stock-analysis \
    --gen2 \
    --runtime=python311 \
    --region=us-central1 \
    --source=. \
    --entry-point=daily_analysis_pubsub \
    --trigger-topic=daily-analysis-trigger \
    --memory=512Mi \
    --timeout=540s \
    --set-env-vars="GEMINI_API_KEY=${GEMINI_API_KEY},GCP_PROJECT_ID=${PROJECT_ID}" \
    --max-instances=1 \
    --quiet

cd ../../..
```

### Step 3: Verify Deployment

```bash
# Check function status
STATUS=$(gcloud functions describe daily-stock-analysis \
    --region=us-central1 \
    --format="value(state)" 2>/dev/null)

if [[ "$STATUS" == "ACTIVE" ]]; then
    echo "✓ Function deployed and ACTIVE"
else
    echo "ERROR: Function state is $STATUS"
    exit 1
fi
```

### Step 4: Optional Test Run

```bash
if [[ "$RUN_TEST" == "true" ]]; then
    echo "Triggering test run..."
    gcloud scheduler jobs run daily-analysis-job --location=us-central1
    echo "✓ Test triggered"
    echo "View logs: gcloud functions logs read daily-stock-analysis --region=us-central1 --limit=50"
fi
```

## Output Format

### Successful Deployment

```
══════════════════════════════════════════════════════════════
  DEPLOYING TO GCP
══════════════════════════════════════════════════════════════

  Pre-flight Checks:
  ├─ ✓ API key validated: AIzaSyArpa...02UU
  ├─ ✓ gcloud authenticated
  └─ ✓ Project: ttb-lang1

  Deployment:
  ├─ ✓ Building container...
  ├─ ✓ Deploying function...
  └─ ✓ Updating traffic...

  Result:
  ├─ Status: ACTIVE
  ├─ Revision: daily-stock-analysis-00003
  ├─ URL: https://us-central1-ttb-lang1.cloudfunctions.net/daily-stock-analysis
  └─ Trigger: daily-analysis-trigger (Pub/Sub)

  Commands:
  ├─ View logs: gcloud functions logs read daily-stock-analysis --region=us-central1
  ├─ Trigger now: gcloud scheduler jobs run daily-analysis-job --location=us-central1
  └─ Describe: gcloud functions describe daily-stock-analysis --region=us-central1

══════════════════════════════════════════════════════════════
  DEPLOYMENT COMPLETE
══════════════════════════════════════════════════════════════
```

### Dry Run Output

```
══════════════════════════════════════════════════════════════
  DRY RUN - No changes will be made
══════════════════════════════════════════════════════════════

  Would deploy:
  ├─ Function: daily-stock-analysis
  ├─ Runtime: python311
  ├─ Region: us-central1
  ├─ Memory: 512Mi
  ├─ Timeout: 540s
  └─ Entry point: daily_analysis_pubsub

  Environment variables:
  ├─ GEMINI_API_KEY: AIzaSyArpa...02UU
  └─ GCP_PROJECT_ID: ttb-lang1

  To deploy for real, run: /deploy
══════════════════════════════════════════════════════════════
```

### Error Output

```
══════════════════════════════════════════════════════════════
  DEPLOYMENT FAILED
══════════════════════════════════════════════════════════════

  Error: Cloud Function deployment failed

  Details:
  └─ Build failed: ImportError: No module named 'technical_analysis_mcp'

  Troubleshooting:
  ├─ Ensure src/technical_analysis_mcp is copied to function directory
  ├─ Check requirements.txt includes all dependencies
  └─ Review: gcloud functions logs read daily-stock-analysis --region=us-central1

  Rollback:
  └─ Previous revision is still active

══════════════════════════════════════════════════════════════
```

## Error Handling

1. **Missing .env**: Prompt to create with template
2. **Auth failure**: Provide `gcloud auth login` command
3. **Project not set**: Provide `gcloud config set project` command
4. **API not enabled**: Auto-enable required APIs
5. **Build failure**: Show logs and troubleshooting steps
6. **Deployment timeout**: Suggest checking Cloud Build logs

## Dependencies

- gcloud CLI installed and configured
- .env file with GEMINI_API_KEY
- automation/functions/daily_analysis/ directory
- Pub/Sub topic: daily-analysis-trigger
- Cloud Scheduler job: daily-analysis-job

## Notes

- Deployment takes 2-5 minutes
- Function uses Gen2 (Cloud Run based)
- Max instances set to 1 to prevent concurrent runs
- Timeout is 540s (9 minutes) for full watchlist analysis
