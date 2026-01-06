# /gcp-status - Infrastructure Health Check

Check GCP resources, execution logs, and pipeline health for the stock analysis system.

## Usage

```
/gcp-status [OPTIONS]
```

**Options:**
- `/gcp-status` - Full status report
- `/gcp-status --logs` - Show recent function execution logs
- `/gcp-status --logs 100` - Show last 100 log entries
- `/gcp-status --errors` - Show only errors from logs
- `/gcp-status --firestore` - Check Firestore data status
- `/gcp-status --scheduler` - Show scheduler job details
- `/gcp-status --quick` - Brief status summary only

**Examples:**
- `/gcp-status` - Complete infrastructure health check
- `/gcp-status --logs --errors` - Show only error logs
- `/gcp-status --firestore` - Verify Firestore has recent data

## Behavior

When this skill is invoked:

1. **Check Cloud Function** status and configuration
2. **Check Cloud Scheduler** job and next run time
3. **Review recent logs** for errors or issues
4. **Verify Firestore** has recent analysis data
5. **Calculate API usage** and quota status
6. **Generate health report** with actionable insights

## Implementation

### Check Cloud Function Status

```bash
# Get function details
gcloud functions describe daily-stock-analysis \
    --region=us-central1 \
    --format="yaml(name,state,updateTime,serviceConfig.uri)"

# Expected output parsing:
# - state: ACTIVE = healthy
# - updateTime: when last deployed
# - serviceConfig.uri: function URL
```

### Check Cloud Scheduler

```bash
# Get scheduler job details
gcloud scheduler jobs describe daily-analysis-job \
    --location=us-central1 \
    --format="yaml(name,state,schedule,timeZone,lastAttemptTime,scheduleTime)"

# Key fields:
# - state: ENABLED = active
# - schedule: "30 16 * * 1-5" (4:30 PM ET, Mon-Fri)
# - lastAttemptTime: when it last triggered
# - scheduleTime: next scheduled run
```

### Check Recent Logs

```bash
# Get recent execution logs
gcloud functions logs read daily-stock-analysis \
    --region=us-central1 \
    --limit=50

# For errors only
gcloud functions logs read daily-stock-analysis \
    --region=us-central1 \
    --limit=100 | grep -i "error\|exception\|failed\|429"
```

### Check Firestore Data

```bash
# Use Python to check Firestore
python3 << 'EOF'
from google.cloud import firestore
from datetime import datetime, timedelta

db = firestore.Client(project='ttb-lang1')

# Check analysis collection
analysis_docs = list(db.collection('analysis').stream())
print(f"Analysis documents: {len(analysis_docs)}")

# Check most recent
if analysis_docs:
    latest = max(analysis_docs, key=lambda d: d.to_dict().get('timestamp', ''))
    data = latest.to_dict()
    print(f"Latest: {data.get('symbol')} at {data.get('timestamp')}")

# Check summaries
summaries = list(db.collection('summaries').order_by('date', direction=firestore.Query.DESCENDING).limit(1).stream())
if summaries:
    summary = summaries[0].to_dict()
    print(f"Latest summary: {summary.get('date')}, {summary.get('successful')}/{summary.get('total_analyzed')} stocks")
EOF
```

## Output Format

### Full Status Report

```
══════════════════════════════════════════════════════════════
  GCP STATUS REPORT
  Project: ttb-lang1
  Generated: 2026-01-06 12:30:00 UTC
══════════════════════════════════════════════════════════════

  CLOUD FUNCTION
  ──────────────────────────────────────────────────────────
  Name:         daily-stock-analysis
  Status:       ✓ ACTIVE
  Revision:     daily-stock-analysis-00003
  Last Deploy:  2026-01-06 00:22:00 UTC
  Runtime:      python311
  Memory:       512Mi
  Timeout:      540s
  URL:          https://us-central1-ttb-lang1.cloudfunctions.net/daily-stock-analysis

  CLOUD SCHEDULER
  ──────────────────────────────────────────────────────────
  Job:          daily-analysis-job
  Status:       ✓ ENABLED
  Schedule:     30 16 * * 1-5 (Mon-Fri 4:30 PM ET)
  Timezone:     America/New_York
  Last Run:     2026-01-05 21:30:00 UTC
  Next Run:     2026-01-06 21:30:00 UTC
  Last Status:  ✓ SUCCESS

  RECENT EXECUTION
  ──────────────────────────────────────────────────────────
  Execution ID: A3Rsc9cFiZdi
  Time:         2026-01-06 00:22:12 UTC
  Duration:     110 seconds
  Status:       ✓ COMPLETE

  Results:
  ├─ Stocks Analyzed: 15/15
  ├─ Errors: 0
  ├─ Top Bullish: META (75), XLF (75), DIA (75)
  └─ Top Bearish: MSFT (35), TSLA (40)

  FIRESTORE
  ──────────────────────────────────────────────────────────
  Collection: analysis
  ├─ Documents: 15
  ├─ Latest Update: 2026-01-06 00:24:02 UTC
  └─ Status: ✓ FRESH (< 24 hours old)

  Collection: summaries
  ├─ Documents: 1
  └─ Latest: 2026-01-06 (15/15 stocks)

  API USAGE
  ──────────────────────────────────────────────────────────
  Gemini API:
  ├─ Last Run: 15 calls
  ├─ Rate: ~8.2 req/min (limit: 10/min)
  └─ Status: ✓ WITHIN QUOTA

  Cloud Functions:
  ├─ Invocations (month): ~250
  ├─ Free Tier: 2,000,000
  └─ Status: ✓ 0.01% of free tier

  Firestore:
  ├─ Reads (month): ~500
  ├─ Writes (month): ~500
  ├─ Free Tier: 50,000 each
  └─ Status: ✓ 1% of free tier

══════════════════════════════════════════════════════════════
  HEALTH SUMMARY
══════════════════════════════════════════════════════════════

  Overall Status: ✓ HEALTHY

  ✓ Cloud Function active and responding
  ✓ Scheduler job enabled and on schedule
  ✓ Last execution completed successfully
  ✓ Firestore data is fresh
  ✓ All API quotas within limits
  ✓ No errors in last 24 hours

══════════════════════════════════════════════════════════════
```

### Logs Output (--logs)

```
══════════════════════════════════════════════════════════════
  RECENT LOGS (last 50 entries)
══════════════════════════════════════════════════════════════

  [2026-01-06 00:24:02] SUMMARY
  ├─ Analyzed: 15/15
  ├─ Top Bullish: META (75), XLF (75), DIA (75)
  └─ Top Bearish: MSFT (35), TSLA (40)

  [2026-01-06 00:24:01] [15/15] Analyzing DIA...
  ├─ Price: $489.77 (+1.27%)
  ├─ Score: 75 | Outlook: BULLISH
  └─ Signals: 4

  [2026-01-06 00:23:54] [14/15] Analyzing XLK...
  ├─ Price: $144.62 (+0.22%)
  ├─ Score: 55 | Outlook: NEUTRAL
  └─ Signals: 3

  [... more entries ...]

  [2026-01-06 00:22:12] DAILY STOCK ANALYSIS
  └─ Time: 2026-01-06T00:22:12.570471

══════════════════════════════════════════════════════════════
```

### Errors Output (--errors)

```
══════════════════════════════════════════════════════════════
  ERROR LOG (last 24 hours)
══════════════════════════════════════════════════════════════

  ✓ No errors found in last 24 hours

  Previous Errors (resolved):
  ──────────────────────────────────────────────────────────
  [2026-01-05 21:30:49] Gemini error for DIA: 429 quota exceeded
  └─ Resolution: Rate limiting fix deployed (6.5s delays)

══════════════════════════════════════════════════════════════
```

### Quick Status (--quick)

```
GCP Status: ✓ HEALTHY
├─ Function: ACTIVE (revision 00003)
├─ Scheduler: ENABLED (next: 2026-01-06 21:30 UTC)
├─ Last Run: SUCCESS (15/15 stocks)
├─ Firestore: FRESH (updated 2h ago)
└─ Errors (24h): 0
```

## Error Detection

The skill checks for these issues:

| Issue | Detection | Severity |
|-------|-----------|----------|
| Function not ACTIVE | state != ACTIVE | CRITICAL |
| Scheduler disabled | state != ENABLED | HIGH |
| 429 quota errors | "429" in logs | MEDIUM |
| Execution failures | "error" in logs | HIGH |
| Stale Firestore data | > 48 hours old | MEDIUM |
| Missing API key | env var not set | CRITICAL |

## Recommendations

When issues are detected, the skill provides:

```
══════════════════════════════════════════════════════════════
  ISSUES DETECTED
══════════════════════════════════════════════════════════════

  ⚠️ WARNING: Gemini API rate limiting (429 errors)
  ├─ Cause: API calls exceeding 10/min quota
  ├─ Impact: Some stocks may not get AI analysis
  └─ Fix: Rate limiting already in place (6.5s delays)

  RECOMMENDED ACTIONS:
  ├─ 1. Monitor next execution for 429 errors
  ├─ 2. Consider reducing watchlist size if issue persists
  └─ 3. See RATE-LIMITING-SOLUTIONS.md for options

══════════════════════════════════════════════════════════════
```

## Dependencies

- gcloud CLI configured with project access
- Python with google-cloud-firestore (for Firestore checks)
- Access to Cloud Functions, Scheduler, and Firestore

## Notes

- Full status check takes 5-10 seconds
- Use --quick for faster 2-second check
- Logs are limited to last 24 hours by default
- Firestore checks require Python environment
- Use /deploy to fix deployment issues
