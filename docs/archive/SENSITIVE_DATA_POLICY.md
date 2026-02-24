# 🔐 Sensitive Data Policy - MCP Finance

**Status**: ENFORCED
**Last Updated**: 2026-02-11

---

## 📋 What Constitutes Sensitive Data

### ❌ NEVER COMMIT

**API Keys, Credentials & Secrets**
- Clerk API keys (publishable & secret)
- Stripe API keys (test & live)
- Gemini API keys
- Database passwords/connection strings
- OAuth tokens and secrets
- JWT signing keys
- AWS/GCP service account keys
- Any `.key`, `.pem`, `.crt` files
- Environment variable files (`.env`, `.env.local`, etc.)

**Personal & Financial Information**
- User email addresses (if tied to specific data)
- Phone numbers
- Credit card numbers (never stored anyway!)
- Bank account information
- Real transaction history with amounts/dates
- User IP addresses
- Personally identifiable information (PII)

**System Information**
- Real database IDs and URLs
- Real cloud project IDs
- Production server hostnames
- Internal API endpoint URLs
- Real customer/user data
- Real pricing or financial metrics

**Generated Files with Real Data**
- Database exports/dumps
- API response examples with real data
- Test result files with actual values
- Backend test reports showing real account data
- Screenshots of dashboards with sensitive info
- Audit logs with user activity
- Performance reports with real metrics

---

## ✅ SAFE TO COMMIT

### Code & Configuration

✅ Code structure and logic
✅ Example configurations (without real values)
✅ `.env.example` files (with placeholder values like `YOUR_API_KEY_HERE`)
✅ Architecture diagrams
✅ Documentation and guides

### Generated Files (Safe Versions)

✅ Test reports with **anonymized** or **synthetic** data
✅ Architecture/implementation documentation
✅ API endpoint specifications (without real examples)
✅ Database schema definitions (without sample data)
✅ User guides and feature documentation
✅ Performance analysis (without identifying customers)
✅ Error handling guides
✅ Deployment procedures

### Examples

**❌ DON'T COMMIT**:
```json
{
  "user_id": "user_123_actual_prod_id",
  "email": "john.doe@company.com",
  "api_response": {
    "stripe_customer_id": "cus_12345REAL",
    "subscription": "stripe_sub_67890REAL"
  }
}
```

**✅ COMMIT**:
```json
{
  "user_id": "user_example_placeholder",
  "email": "user@example.com",
  "api_response": {
    "stripe_customer_id": "cus_XXXXXXXXX",
    "subscription": "stripe_sub_XXXXXXXXX"
  }
}
```

---

## 🛡️ Prevention Measures

### 1. .gitignore Rules

**Current Protection**:
```gitignore
# Environment files
.env
.env.local
.env.*.local
*.env

# GCP Credentials
*.json (except package.json, tsconfig.json, *.schema.json)
service-account*.json
credentials*.json
*-key.json

# Generated data files
reports/*.json
backend_test_results/*/raw_data/
database_exports/
*.db
*.sqlite
*.sql
*.dump

# Screenshots with sensitive content
screenshots/*auth*
screenshots/*api*
screenshots/*key*
```

### 2. Pre-commit Checks

**Search Patterns** (before committing):
```bash
# Check for API keys
grep -r "api[_-]?key\|secret\|token\|password" .

# Check for GCP project IDs
grep -r "ttb-lang1\|ttb-fin1\|gen-lang-client" .

# Check for credentials
grep -r "service.account\|credentials\|private[_-]?key" .

# Check for PII patterns
grep -rE "[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}" .
```

### 3. Code Review Checklist

Before pushing code, verify:
- [ ] No hardcoded API keys
- [ ] No database credentials
- [ ] No user emails (unless documented as example)
- [ ] No real GCP project IDs
- [ ] No real customer/account data
- [ ] No screenshots with sensitive info
- [ ] All generated files use placeholder data
- [ ] `.env.example` doesn't contain real values
- [ ] Database exports not in repo
- [ ] Test files don't use production data

---

## 📁 .gitignore Protected Patterns

### By Category

**Environment Variables**
```
.env
.env.local
.env.development
.env.production
.env.staging
.env.*.local
```

**Credentials & Keys**
```
*.json (except project files)
service-account*.json
credentials*.json
*-key.json
*-credentials.json
*.pem
*.key
*.crt
```

**Data Exports**
```
reports/*.json
reports/*.csv
database_exports/
backups/
exports/
dumps/
*.db
*.sqlite
*.sql
*.dump
```

**Test/Analysis Files**
```
backend_test_results/*/raw_data/
backend_test_results/*_UNREVIEWED.md
test_results_with_data/
api_responses/
analysis_results_*_raw/
audit_logs_*_raw/
```

**Sensitive Screenshots**
```
screenshots/*auth*
screenshots/*api*
screenshots/*key*
screenshots/*token*
screenshots/*secret*
screenshots/*credential*
```

---

## 🔄 If You Accidentally Commit Sensitive Data

**IMMEDIATE ACTION REQUIRED**:

```bash
# 1. Stop pushing immediately
git reset HEAD~1

# 2. Remove from git history (use BFG or git-filter-repo)
# https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository

# 3. Regenerate compromised credentials
# - Rotate API keys
# - Reset passwords
# - Revoke tokens

# 4. Add to .gitignore
echo "sensitive_file.json" >> .gitignore

# 5. Commit the fix
git add .gitignore
git commit -m "Fix: add sensitive file to .gitignore"
git push

# 6. Report to team lead
```

---

## 📝 Examples for Documentation

### Safe Way to Document APIs

**❌ BAD: Uses real data**
```markdown
# API Response Example

```json
{
  "stripe_customer_id": "cus_L3Fjcnx9E9xBkJ",
  "subscription_id": "sub_1FNz7JL3bfgRQxy3x",
  "email": "customer@realcompany.com"
}
```
```

**✅ GOOD: Uses placeholder data**
```markdown
# API Response Example

```json
{
  "stripe_customer_id": "cus_XXXXXXXXXXXX",
  "subscription_id": "sub_XXXXXXXXXXXX",
  "email": "customer@example.com"
}
```
```

### Safe Test Result Files

**❌ BAD: Real test data with actual values**
```
TEST_RESULTS_2026-02-11.json
{
  "user_1": "john.doe@acme.com",
  "transaction_id": "stripe_ch_1234567890abcdef",
  "amount": 9999.99,
  "timestamp": "2026-02-11T15:30:00Z"
}
```

**✅ GOOD: Anonymized test data**
```
TEST_RESULTS_ANONYMIZED_2026-02-11.md
- Test 1: User creation ✅
- Test 2: Payment processing ✅
- Test 3: Subscription update ✅
- Total time: 45.2s
- Success rate: 100%
```

---

## 🚨 Common Mistakes to Avoid

**1. Committing .env files directly**
```bash
# ❌ Wrong
git add .env
git commit

# ✅ Right
# Create .env.example instead
cp .env .env.example
# Edit .env.example to remove real values
git add .env.example
```

**2. Adding real config files**
```bash
# ❌ Wrong
git add config/production.json  # Contains real API keys

# ✅ Right
echo "config/production.json" >> .gitignore
git add config/production.example.json  # Template only
```

**3. Logging sensitive data**
```python
# ❌ Wrong
logger.info(f"User {user_email} created: {stripe_id}")

# ✅ Right
logger.info(f"User created: {user_id[:8]}***")
```

**4. Using real data in examples**
```typescript
// ❌ Wrong
const testApiKey = "sk_live_51234567890abcdefghij";

// ✅ Right
const testApiKey = process.env.STRIPE_API_KEY;
// or
const exampleApiKey = "sk_test_XXXXXXXXXXXXXXXX";
```

---

## 📋 Before Every Commit

Run this checklist:

```bash
#!/bin/bash
# Pre-commit security check

echo "🔐 Security Pre-commit Check"
echo "=============================="

# Check for common sensitive patterns
patterns=(
    "api[_-]key"
    "secret"
    "password"
    "token"
    "credentials"
    "private[_-]key"
    "sk_live"  # Stripe live key
    "sk_test"  # Stripe test key
    "ttb-lang1"  # GCP project
    "ttb-fin1"   # GCP project
)

found=0
for pattern in "${patterns[@]}"; do
    if git diff --cached | grep -i "$pattern"; then
        echo "⚠️  Found: $pattern"
        found=$((found + 1))
    fi
done

if [ $found -gt 0 ]; then
    echo ""
    echo "❌ STOP! Found potentially sensitive data"
    echo "Please review and remove before committing"
    exit 1
else
    echo "✅ No obvious sensitive data detected"
    echo "Proceeding with commit..."
fi
```

---

## 📂 Quarantined Files (soosensitive/)

**Location**: `mcp-finance1/soosensitive/`

The following 16 files were moved here on 2026-02-11 because they contain **real GCP project IDs, email addresses, or service URLs**:

| File | Sensitive Data Found |
|------|---------------------|
| `FIRESTORE_CLI_REFERENCE.md` | GCP project ID `ttb-lang1` (13x), Firebase console URL |
| `FIRESTORE_DB_REPORT.md` | Project ID, email, console URL (12x) |
| `FIRESTORE_INDEX.md` | Project ID, console URL (5x) |
| `FIRESTORE_OPTIMIZATION_GUIDE.md` | Project ID in code examples |
| `FIRESTORE_QUICK_START.md` | Project ID, email address (9x) |
| `FIRESTORE_STATUS_DASHBOARD.md` | Project ID, email, console URL (5x) |
| `GCP_SERVICES_USAGE.md` | Project ID, email |
| `PIPELINE_OPTIMIZATION_SUMMARY.md` | Project ID (3x) |
| `gcloud_mcp_test.py` | Cloud Run URL with project number |
| `ENVIRONMENT_TEST_REPORT.md` | Project ID, console URL (4x) |
| `SCRIPT_EXECUTION_REPORT.md` | Project ID |
| `GUIDE-ENHANCED.md` | Project ID (3x) |
| `GUIDE.md` | Project ID (4x) |
| `EXECUTION_METHODS_SUMMARY.md` | Project ID |
| `BACKEND_IMPLEMENTATION_COMPLETE.md` | Project ID |
| `FILE_REORGANIZATION_PLAN.md` | Project ID (4x) |

**Total**: 16 files, ~70+ sensitive data instances

### Additional Files with Sensitive Data (in subdirectories, already gitignored)

- `nubackend1/FINNHUB_OPTIONS_PIPELINE.md`
- `nubackend1/run_pipeline.py`, `firestore_store.py`, `pipeline.py`, `config.py`
- `nu-docs/GCLOUD_MCP_STATUS.md`, `BACKEND_EXECUTION_RUNBOOK.md`, `BACKEND_EXECUTION_REPORT.md`

### To Sanitize for Public Sharing

Replace these patterns before committing any of these files:
- `ttb-lang1` -> `example-project`
- `chillcoders@gmail.com` -> `user@example.com`
- `1007181159506` -> `PROJECT_NUMBER`
- Firebase console URLs -> `https://console.firebase.google.com/project/example-project`

---

## 🔍 Audit Process

**Weekly Security Audit**:
```bash
# Find large files (might be data dumps)
find . -size +5M -type f

# Look for unusual extensions
find . -name "*.dump" -o -name "*.sql" -o -name "*.db"

# Check for unencrypted credentials
grep -r "password" . --include="*.py" --include="*.js" --include="*.ts"
```

---

## 👥 Team Responsibilities

### All Team Members
- ✅ Never commit API keys or credentials
- ✅ Use `.env` for local secrets
- ✅ Review `.env.example` before sharing
- ✅ Anonymize test data in examples
- ✅ Add sensitive file patterns to `.gitignore`

### Code Reviewers
- ✅ Check for hardcoded secrets
- ✅ Verify `.env` files not included
- ✅ Review generated documentation
- ✅ Look for real customer/user data

### DevOps/Infrastructure
- ✅ Rotate compromised credentials
- ✅ Audit commit history periodically
- ✅ Enforce branch protection rules
- ✅ Monitor for credential leaks

---

## 📞 Questions?

If unsure whether something is sensitive:
1. **Assume it is sensitive** (better safe than sorry)
2. **Use placeholder values** in examples
3. **Check with team** before committing
4. **Add to .gitignore** if in doubt

---

## 🔗 Resources

- [GitHub: Removing Sensitive Data](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository)
- [OWASP: Sensitive Data Exposure](https://owasp.org/www-project-top-ten/2017/A3_2017-Sensitive_Data_Exposure)
- [CWE: Use of Hard-coded Passwords](https://cwe.mitre.org/data/definitions/798.html)

---

**Policy Status**: ✅ ACTIVE
**Last Enforcement**: 2026-02-11
**Next Review**: 2026-03-11
