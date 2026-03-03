# Safe Report Template

Use this template when creating documentation that may contain sensitive data. The template enforces a clear separation between safe content (main body) and sensitive details (appendix).

## Template Structure

```markdown
# [Report Title]

**Report Generated:** [YYYY-MM-DD HH:MM UTC]
**Environment:** [development | staging | production]
**Status:** ✅ Safe to commit - no exposed credentials

---

## Executive Summary

[Non-sensitive summary of findings, performance, or results]

### Key Findings
- Finding 1 (non-sensitive metric or result)
- Finding 2 (non-sensitive metric or result)
- Finding 3 (performance or timing data)

### Test Results
- Total items processed: [NUMBER]
- Success rate: [PERCENTAGE]%
- Average response time: [TIME]ms
- Peak memory usage: [MEMORY]

---

## Configuration & Setup

### Prerequisites

Before running this test, ensure you have:
1. Required environment variables configured (see `.env.example`)
2. Access to required services (see Appendix A)
3. Network connectivity to external APIs

### Required Environment Variables

```bash
# ============================================================================
# Configuration
# ============================================================================

# Google Gemini API
GOOGLE_API_KEY=[REDACTED]  # See .env.example for format

# Database Connection
DATABASE_URL=postgresql://[USER]:[PASS]@[HOST]:[PORT]/[DB]

# Service Configuration
SERVICE_URL=https://[SERVICE_HOST]/api/v1
```

**To configure:**
1. Copy `.env.example` to `.env`
2. Add your actual credentials to `.env` (not version controlled)
3. Do NOT commit `.env` to git

---

## Test Results

### Performance Metrics

| Metric | Value | Unit |
|--------|-------|------|
| Total Duration | 45 | seconds |
| Requests Processed | 100 | items |
| Successful Requests | 100 | items (100%) |
| Failed Requests | 0 | items (0%) |
| Average Latency | 450 | ms |
| Median Latency | 425 | ms |
| P95 Latency | 500 | ms |
| P99 Latency | 550 | ms |

### Request/Response Summary

**Sample Request**
```
GET /api/v1/endpoint?parameter=example
Headers:
  Authorization: Bearer [TOKEN]
  Content-Type: application/json
```

**Sample Response**
```json
{
  "status": "success",
  "data": {
    "id": "item_[ID]",
    "timestamp": "2025-01-22T10:30:45Z",
    "result": "completed"
  }
}
```

### Error Handling

All error conditions were handled appropriately:
- Connection timeout: Retried with exponential backoff ✅
- Rate limiting: Respected 429 status code ✅
- Invalid input: Proper error messages returned ✅
- Service unavailable: Graceful degradation ✅

---

## Findings & Analysis

### Performance Analysis

The test results show [good/acceptable/concerning] performance:

- **Throughput**: X items/second is [better/worse] than expected
- **Latency**: Average response time of Xms is [within/above] SLA
- **Reliability**: 100% success rate indicates [stable/issues need investigation]
- **Resource Usage**: Memory consumption remained [constant/increased over time]

### Recommendations

1. **For Production Deployment**
   - [Specific recommendation 1]
   - [Specific recommendation 2]
   - [Specific recommendation 3]

2. **For Further Optimization**
   - [Performance improvement 1]
   - [Performance improvement 2]

3. **For Monitoring**
   - Set up alerts for [metric 1]
   - Monitor [metric 2] for degradation
   - Track [metric 3] over time

---

## How to Reproduce

To reproduce this test run:

```bash
cd /Users/adamaslan/code/gcp\ app\ w\ mcp

# 1. Activate mamba environment
mamba activate fin-ai1

# 2. Ensure .env is configured (copy from .env.example)
cp .env.example .env
# Then edit .env with your actual credentials

# 3. Run the test script
bash scripts/quick_start.sh

# 4. Find results in
ls backend_test_results/latest/

# 5. Generate safe report
/sensitive-doc-creator \
  --input=backend_test_results/latest/ \
  --output=backend_test_results/latest/SAFE_REPORT.md
```

---

## Security Notes

### Sensitive Data Handling

This document uses the following redaction strategy:

- **API Keys**: Fully redacted as `[REDACTED]`
- **Credentials**: Shown as placeholders: `[USER]:[PASS]@[HOST]`
- **Service URLs**: Placeholder format: `https://[SERVICE_HOST]/api`
- **Account Numbers**: Fully redacted
- **Transaction IDs**: Placeholder format: `[TX_ID]`

### To Configure Locally

Real credentials are stored in `.env` (not version controlled):
1. Copy `.env.example` to `.env`
2. Edit `.env` with your actual credentials
3. Load environment: `source .env`
4. Verify: The test script reads from your `.env`

### Never Include in Documentation

❌ Real API keys, tokens, or secrets
❌ Database passwords or connection strings
❌ Customer data or transaction IDs (if real)
❌ GCP service account JSON
❌ OAuth tokens or JWT secrets

✅ Configuration examples with placeholders
✅ Performance metrics and timing data
✅ Error handling patterns and responses
✅ Setup and reproduction instructions

---

## Verification Checklist

**Before committing this document, verify:**

- [ ] All API keys show `[REDACTED]` not actual keys
- [ ] All passwords show `[PASS]` or `[REDACTED]`
- [ ] Database URLs show `[HOST]` not actual hostname
- [ ] No service account JSON included
- [ ] No real customer/transaction data
- [ ] Configuration section references `.env.example`
- [ ] Instructions direct users to create their own `.env`

**After committing:**

- [ ] Run `/sensitive-doc-creator --verify=[this-file]`
- [ ] Verify git status shows only this file changed
- [ ] Confirm no `.env` or credentials in staging area
- [ ] Safe commit message (e.g., "docs: Add safe test report")

---

## Appendix A: Configuration Reference

### Environment Variables Reference

This section provides configuration reference without exposing actual values.

**Google Gemini API**
- Variable: `GOOGLE_API_KEY`
- Format: Alphanumeric starting with `AIzaSy`
- Length: ~39 characters
- Source: Google Cloud Console → APIs & Services → Credentials
- Usage: Used to authenticate requests to Gemini API
- Security: Keep in `.env`, never commit, rotate if exposed

**Database Connection**
- Variable: `DATABASE_URL`
- Format: `postgresql://username:password@host:port/database`
- Example: `postgresql://myuser:mypass@localhost:5432/mydb`
- Source: Neon console or self-hosted PostgreSQL
- Usage: Used for database operations
- Security: Keep in `.env`, use strong passwords, enable SSL

**Service Configuration**
- Variable: `SERVICE_URL`
- Format: `https://service-host/api/version`
- Example: `https://api.example.com/api/v1`
- Usage: Calls to external services
- Security: Use HTTPS, validate SSL certificates

### How to Obtain Credentials

**Google API Key**
1. Go to https://console.cloud.google.com/
2. Select your project
3. Enable Gemini API if not already enabled
4. Go to APIs & Services → Credentials
5. Create new API key (restrict to IP if possible)
6. Copy to `.env` as `GOOGLE_API_KEY=AIzaSy...`

**Database Credentials**
1. For Neon: https://console.neon.tech/
2. Select project and branch
3. Find connection string (contains password)
4. Copy to `.env` as `DATABASE_URL=postgresql://...`
5. Never use production credentials in development

**Service URLs**
- Check documentation for each service
- Use staging/test environments when possible
- Always verify HTTPS endpoints
- Validate SSL certificates

---

## Appendix B: Troubleshooting

### Common Issues

**Issue: "Connection to Gemini API failed"**
- Verify `GOOGLE_API_KEY` is set in `.env`
- Check key is valid and not expired
- Verify you have network access to api.generativeai.google.com
- Check if API key is restricted by IP (may need to adjust)

**Issue: "Database connection refused"**
- Verify `DATABASE_URL` is correct
- Check database is running and accessible
- Verify username/password are correct
- Check network connectivity to host
- For Neon: Verify database is not in suspend state

**Issue: "Rate limit exceeded"**
- Reduce concurrent requests
- Implement backoff strategy
- Consider upgrading API tier
- Contact service support for limit increase

---

## Document Status

**Created:** [YYYY-MM-DD HH:MM UTC]
**Last Updated:** [YYYY-MM-DD HH:MM UTC]
**Safe to Commit:** ✅ Yes
**Sensitive Data:** ❌ None (all redacted/placeholders)
**Git Status:** Ready to commit

---

## Related Documents

- `.env.example` - Configuration template
- `README.md` - Setup instructions
- `scripts/quick_start.sh` - Test execution script
- `backend_test_results/latest/` - Full test results
```

## Usage Notes

1. **Replace placeholders** in brackets `[LIKE_THIS]` with your actual values
2. **Keep "REDACTED" sections**: Don't replace with real values
3. **Include configuration examples** that show structure without real credentials
4. **Direct users to .env.example** for actual credential setup
5. **Use appendices** for detailed sensitive information that's fully redacted
6. **Always include the verification checklist** before committing

## When to Use

Use this template for:
- ✅ Backend test reports
- ✅ API integration documentation
- ✅ Performance analysis reports
- ✅ Architecture documentation
- ✅ Setup guides

Do NOT use for:
- ❌ Actual credential storage
- ❌ Production deployment guides (keep credentials separate)
- ❌ Customer-facing documentation without anonymization
- ❌ Internal wikis with unredacted credentials

