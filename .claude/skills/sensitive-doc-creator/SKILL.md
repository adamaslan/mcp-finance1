---
name: sensitive-doc-creator
description: Guide safe creation of documentation that may contain sensitive data (API keys, credentials, PII, financial data). Use when generating reports, test results, backend analysis, documenting APIs, or when user mentions creating documentation, generating reports, documenting test results, or exporting data.
allowed-tools: ["Read", "Write", "Grep", "Glob", "Bash"]
trigger-keywords:
  - "create documentation"
  - "generate report"
  - "document test results"
  - "safe documentation"
  - "sensitive data"
  - "redact"
  - "anonymize"
---

# Sensitive Documentation Creator Skill

## Overview

This skill guides safe creation of documentation while protecting sensitive information. It provides a systematic approach to identify, redact, and securely manage documentation that may contain:

- **API Keys & Tokens** (Google, Stripe, OpenAI, etc.)
- **Database Credentials** (connection strings, passwords)
- **Personal Information** (email, phone, SSN)
- **Financial Data** (account numbers, transaction details)
- **GCP Project IDs & Service Accounts**
- **OAuth secrets & JWT signing keys**

## When to Use This Skill

### Automatic Triggers
Claude will automatically invoke this skill when you mention:
- "Create safe documentation"
- "Generate a report without exposing secrets"
- "Document test results safely"
- "Create anonymized backend analysis"
- "Export data safely"

### Manual Invocation
```bash
/sensitive-doc-creator [options]
```

### Use Cases

1. **Backend Test Reports**
   - Generating test result documentation from scripts/quick_start.sh
   - Safe API response summaries
   - Performance analysis reports

2. **API Documentation**
   - Documenting API endpoints
   - Creating setup guides
   - Configuration examples

3. **Architecture Documentation**
   - Backend architecture diagrams
   - Integration guides
   - Deployment documentation

4. **Analysis & Debugging**
   - Error analysis reports
   - Performance bottleneck documentation
   - Feature implementation guides

## Core Principles

### Four-Stage Safety Protocol

The skill follows a rigorous four-stage process:

```
Stage 1: PRE-FLIGHT SCANNING
├─ Identify sensitive data in source material
├─ Assess exposure risk
└─ Plan redaction strategy

Stage 2: SAFE ENVIRONMENT SETUP
├─ Create temporary working directory
├─ Update .gitignore with document path
└─ Verify file permissions

Stage 3: INTERACTIVE DOCUMENTATION CREATION
├─ Build documentation structure
├─ Apply appropriate redaction level
├─ Integrate anonymized examples
└─ Generate verification checklist

Stage 4: VERIFICATION & SAFE STORAGE
├─ Multi-stage content verification
├─ Final sensitive pattern scan
├─ Generate remediation script if needed
└─ Confirm safe-to-commit status
```

### Redaction Levels

The skill supports three redaction levels for different sensitivity contexts:

#### Level 1: Full Redaction (CRITICAL Data)
Used for: Passwords, API keys, database credentials, service account keys

```
BEFORE: STRIPE_KEY=sk_live_51234567890abcdef
AFTER:  STRIPE_KEY=[REDACTED]
```

#### Level 2: Partial Redaction (SENSITIVE Data)
Used for: Email addresses, transaction details, user IDs in analysis

```
BEFORE: user@example.com
AFTER:  u***@example.com

BEFORE: Stripe payment pi_1234567890abcdef
AFTER:  Stripe payment pi_***[REDACTED]
```

#### Level 3: Placeholder Redaction (INFORMATIONAL Data)
Used for: Configuration examples, connection strings, structure documentation

```
BEFORE: postgresql://admin:SecurePass123@prod-db.neon.tech:5432/mydb
AFTER:  postgresql://[USERNAME]:[PASSWORD]@[HOST]:[PORT]/[DATABASE]

BEFORE: firebase-config.json with API key AIzaSyCmicLheNasxh3RI_AtXlbtp4bOKdZBVYA
AFTER:  firebase-config.json with API key [REDACTED]
```

### False Positive Management

The skill filters out legitimate uses of patterns:
- Email addresses in .env.example or documentation headers
- Generic "password" text in guides
- Example credentials in comments (if clearly marked as examples)

## Step-by-Step Workflow

### Phase 1: Pre-Flight Analysis

**Objectives:**
- Scan source material for sensitive patterns
- Identify data types present
- Assess exposure risk
- Recommend redaction levels

**Process:**
1. Accept source material path or content
2. Use Grep tool to search for sensitive patterns
3. Analyze findings for context
4. Generate risk assessment report
5. Present redaction recommendations

**Input:** Source file, directory, or text content
**Output:** Risk assessment with specific findings

**Example:**
```
SOURCE: scripts/quick_start.sh output
SCAN RESULTS:
  🔴 CRITICAL (1 finding):
     - Google API key pattern (AIzaSy...) at line 1153
  🟡 WARNING (2 findings):
     - Email patterns at lines 45, 234
  🟢 INFO (0 findings)
RECOMMENDATION: Use Level 1 (Full) redaction for API keys
```

### Phase 2: Safe Environment Setup

**Objectives:**
- Create secure working directory
- Update .gitignore with document path
- Verify file permissions
- Initialize tracking metadata

**Process:**
1. Create temporary directory with restricted permissions
2. Add document path to .gitignore if sensitive data found
3. Generate metadata file tracking redaction decisions
4. Confirm environment readiness

**Outputs:**
- Secure working directory at `temp/.sensitive-doc-TIMESTAMP/`
- Updated .gitignore entry
- Metadata tracking file

**Safety Checks:**
- Verify .gitignore includes document path
- Confirm 600 permissions on working files
- Check git is tracking .gitignore changes

### Phase 3: Interactive Documentation Creation

**Objectives:**
- Build documentation structure
- Apply redaction transformations
- Integrate safe examples
- Create usage guides

**Process:**
1. Load document template (from templates/safe-report-template.md)
2. For each sensitive finding:
   - Apply selected redaction level
   - Generate placeholder if needed
   - Add explanation in appendix
3. Create safe example blocks with placeholders
4. Build final documentation
5. Generate verification checklist

**Features:**
- Three redaction templates for different data types
- Automatic placeholder generation
- Cross-references between main content and appendix
- Built-in examples for safe configurations

**Example Output Structure:**
```markdown
# Safe Backend Test Report

## Summary (SAFE)
Test run on 2025-01-22 completed in 45 seconds...

## Configuration (SAFE WITH PLACEHOLDERS)
```yaml
gemini:
  api_key: [REDACTED]  # See Appendix A for restore instructions
  model: gemini-2.0-flash
```

## Results (ANONYMIZED)
Successfully processed 100 test items...

## Appendix A: Configuration Details
[Full redaction of all credentials]
```

### Phase 4: Verification & Safe Storage

**Objectives:**
- Multi-stage content verification
- Final sensitive data scan
- Confirm safe-to-commit status
- Generate remediation if needed

**Verification Stages:**
1. Content verification: Check for unreplaced patterns
2. Pattern scan: Use sensitive-data-scan tool
3. File permission check: Ensure proper permissions
4. Git status check: Verify .gitignore applied

**Output:**
```
VERIFICATION REPORT:
✅ Content check: No unreplaced sensitive patterns found
✅ Pattern scan: 0 critical issues detected
✅ Permissions: File has correct 644 permissions
✅ Git tracking: Document is in .gitignore if needed
✅ SAFE TO COMMIT: Yes

Safe commit command:
  git add your-report.md
  git commit -m "docs: Add safe backend test report"
```

## Sensitive Data Pattern Database

### API Keys

**Google API Keys**
- Pattern: `AIzaSy[A-Za-z0-9_-]{35}`
- Example: `AIzaSyCmicLheNasxh3RI_AtXlbtp4bOKdZBVYA`
- Severity: 🔴 CRITICAL
- Redaction: Full - `[REDACTED]`
- Context: Often found in:
  - Gemini/VertexAI documentation
  - Firebase configuration
  - Google Cloud API calls

**Stripe Keys**
- Pattern: `(sk_live|sk_test)_[A-Za-z0-9_]{32,}`
- Example: `sk_live_51234567890abcdef`
- Severity: 🔴 CRITICAL
- Redaction: Full - `[REDACTED]`
- Context: Payment processing, webhook configuration

**OpenAI API Keys**
- Pattern: `sk-[A-Za-z0-9]{20,}`
- Example: `sk-proj-dXQdJ8xO0F9Q4mK2L3N5`
- Severity: 🔴 CRITICAL
- Redaction: Full - `[REDACTED]`

**Bearer Tokens**
- Pattern: `Bearer [A-Za-z0-9_.-]{40,}`
- Example: `Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...`
- Severity: 🔴 CRITICAL
- Redaction: Full - `[REDACTED]`

### Database Credentials

**PostgreSQL Connection Strings**
- Pattern: `postgresql://[^:]*:[^@]*@[^\s]*`
- Example: `postgresql://admin:Secure123@prod-db.neon.tech:5432/mydb`
- Severity: 🔴 CRITICAL
- Redaction: Placeholder - `postgresql://[USER]:[PASS]@[HOST]:[PORT]/[DB]`

**Database Passwords in Config**
- Pattern: `(password|passwd|pwd)\s*[=:]\s*['"]*([^'"\s]*)['"]*`
- Example: `password: npg_Hs0g5ypEPTzO`
- Severity: 🔴 CRITICAL
- Redaction: Full - `password: [REDACTED]`

**SSH Keys**
- Pattern: `-----BEGIN.*PRIVATE KEY-----[\s\S]*?-----END.*PRIVATE KEY-----`
- Severity: 🔴 CRITICAL
- Redaction: Full - `[SSH KEY REDACTED]`

**Service Account JSON**
- Pattern: `"type":\s*"service_account"[\s\S]*?"private_key":\s*"[^"]*"`
- Severity: 🔴 CRITICAL
- Redaction: Full - `[SERVICE ACCOUNT REDACTED]`

### Personal Information (PII)

**Email Addresses**
- Pattern: `[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}`
- Severity: 🟡 WARNING (context-dependent)
- Redaction: Partial - `u***@example.com`
- False Positives: `.env.example`, documentation headers

**Phone Numbers**
- Pattern: `(\d{3}[-.\s]?\d{3}[-.\s]?\d{4}|(\d{1,3}[-.\s]?)?(\d{1,3}[-.\s]?)?(\d{1,4}))`
- Severity: 🟡 WARNING (if customer data)
- Redaction: Partial - `***-***-1234`

**Social Security Numbers**
- Pattern: `\d{3}-\d{2}-\d{4}`
- Severity: 🔴 CRITICAL
- Redaction: Full - `[SSN REDACTED]`

### Financial Data

**Account Numbers**
- Pattern: `(account|acct)[\s:=]*([0-9]{10,})`
- Severity: 🔴 CRITICAL (if real account)
- Redaction: Full - `[ACCOUNT REDACTED]`

**Transaction IDs**
- Pattern: `(tx|transaction|payment)_[A-Za-z0-9]{20,}`
- Severity: 🟡 WARNING
- Redaction: Partial - `tx_***[REDACTED]`

**Credit Card Numbers**
- Pattern: `\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}`
- Severity: 🔴 CRITICAL
- Redaction: Full - `[CARD REDACTED]`

### GCP-Specific

**GCP Project IDs**
- Pattern: `[a-z][a-z0-9-]{5,28}[a-z0-9]` (in GCP context)
- Severity: 🟡 WARNING (in some contexts)
- Context: Use anonymized IDs like `example-project`

**GCP Service Accounts**
- Pattern: `\d+-compute@developer\.gserviceaccount\.com`
- Severity: 🟡 WARNING
- Redaction: Placeholder - `[SERVICE_ACCOUNT]@gserviceaccount.com`

## Redaction Templates

### Template 1: Safe Report Template

See: `templates/safe-report-template.md`

**Structure:**
- Executive Summary (SAFE)
- Configuration Section (with placeholders)
- Test Results (anonymized)
- Appendix (full redaction)

**Usage:**
Use this template when creating test result reports, analysis documents, or technical documentation.

### Template 2: Redaction Guide

See: `templates/redaction-guide.md`

**Sections:**
- API Key Redaction Examples
- Database Credential Handling
- PII Removal Strategies
- Financial Data Anonymization
- GCP-Specific Redaction

**Usage:**
Consult this guide when deciding which redaction level to apply to specific data types.

## Usage Examples

### Example 1: Generate Safe Test Report

```bash
/sensitive-doc-creator \
  --input=backend_test_results/latest/ \
  --output=backend_test_results/latest/SAFE_REPORT.md \
  --type=test-report
```

**Process:**
1. Scan `backend_test_results/latest/` for sensitive patterns
2. Apply Level 1 redaction to API keys
3. Apply Level 3 redaction to configuration
4. Create safe report using template
5. Generate verification checklist

**Output:**
- `backend_test_results/latest/SAFE_REPORT.md` - Main report
- `.gitignore` - Updated with document path
- Verification checklist in console

### Example 2: Create Safe API Documentation

```bash
/sensitive-doc-creator \
  --input=src/lib/api/docs.ts \
  --output=API_SETUP.md \
  --type=api-docs \
  --redaction-level=full
```

**Process:**
1. Parse API documentation source
2. Identify all credentials and examples
3. Replace real credentials with placeholders
4. Add security notes section
5. Generate safe documentation

**Output:**
```markdown
# API Setup Guide

## Authentication

Use an API key from Google Cloud Console:

```
GOOGLE_API_KEY=[REDACTED]  # See local .env.example for format
```

## Configuration

```yaml
gemini:
  api_key: [YOUR_API_KEY_HERE]  # Obtain from Google Cloud Console
  model: gemini-2.0-flash
```

## Security Notes

Never commit your API keys. See Security Guide for best practices.
```

### Example 3: Verify Existing Documentation

```bash
/sensitive-doc-creator \
  --verify=nu-docs/BACKEND_EXECUTION_REPORT.md
```

**Process:**
1. Scan document for exposed sensitive patterns
2. Report all findings with severity levels
3. Recommend redaction level
4. Suggest remediation command

**Output:**
```
VERIFICATION: nu-docs/BACKEND_EXECUTION_REPORT.md

🔴 CRITICAL FINDINGS (1):
  Line 1153: Google API key AIzaSyCmicLheNasxh3RI_AtXlbtp4bOKdZBVYA
             Type: Google API Key (Gemini)
             Action: ROTATE IMMEDIATELY - this key is exposed in git

🟡 WARNING FINDINGS (0):

REMEDIATION:
  1. Rotate the exposed Google API key:
     https://console.cloud.google.com/apis/credentials

  2. Remove file from git history:
     git rm --cached nu-docs/BACKEND_EXECUTION_REPORT.md
     git commit -m "Remove file with exposed API key"

  3. Update .gitignore:
     echo "nu-docs/*_EXECUTION_*.md" >> .gitignore
     git add .gitignore
     git commit -m "Protect backend execution reports"
```

## Built-in Verification Checklist

Before marking a document as safe, verify:

### Content Verification
- [ ] No unreplaced sensitive patterns (API keys, passwords, tokens)
- [ ] No PII in main content (emails, phone numbers with context)
- [ ] No financial account details (transaction IDs, account numbers)
- [ ] Configuration examples use placeholders `[EXAMPLE]`

### Format Verification
- [ ] Document follows safe-report-template.md structure
- [ ] Sensitive details moved to Appendix
- [ ] Redaction level is clearly marked
- [ ] Setup instructions reference .env.example

### Security Verification
- [ ] File is in .gitignore if it contains sensitive context
- [ ] No git history contains exposed versions
- [ ] Remediation instructions are provided (if needed)
- [ ] Safe-to-commit status is confirmed

### Git Verification
- [ ] .gitignore has been updated
- [ ] Document path is tracked in .gitignore
- [ ] File permissions are correct (644)
- [ ] git status shows only intended changes

## Integration with Existing Tools

### scripts/quick_start.sh Integration

The skill integrates with the test script:

```bash
# In scripts/quick_start.sh
echo "Generating safe backend report..."
/sensitive-doc-creator \
  --input="$LATEST_RUN" \
  --output="$LATEST_RUN/SAFE_REPORT.md" \
  --type=test-report \
  --auto-gitignore

echo "✅ Safe report generated: $LATEST_RUN/SAFE_REPORT.md"
```

### .gitignore Integration

The skill automatically updates .gitignore:

```gitignore
# ============================================================================
# Security: Sensitive Documentation
# ============================================================================
backend_test_results/*_EXECUTION_*.md
backend_test_results/*/raw_responses/
nu-docs/*_EXECUTION_*.md
```

### Makefile Integration

```makefile
.PHONY: safe-docs
safe-docs: ## Create safe documentation from test results
	@/sensitive-doc-creator --input=backend_test_results/latest/ \
                            --output=backend_test_results/latest/SAFE_REPORT.md

.PHONY: verify-docs
verify-docs: ## Verify documentation for sensitive data
	@/sensitive-doc-creator --verify=backend_test_results/latest/
```

## Command-Line Options

```bash
/sensitive-doc-creator [OPTIONS]

OPTIONS:
  --input PATH              Source file or directory to analyze
  --output PATH            Output file path for safe documentation
  --type TYPE              Document type (test-report, api-docs, analysis)
  --redaction-level LEVEL  Redaction level (full, partial, placeholder)
  --verify PATH            Verify existing document for sensitive data
  --auto-gitignore         Automatically update .gitignore (default: true)
  --interactive            Interactive mode with prompts (default: true)
  --non-interactive        Batch mode without prompts
  --template TEMPLATE      Use specific template (see templates/)
  --help                   Show this help message
```

## Security Best Practices

### Before Creating Documentation

1. **Identify the audience:**
   - Internal only → more relaxed redaction
   - External/public → strict redaction

2. **Determine required detail level:**
   - For troubleshooting → may need more detail (use Level 3)
   - For architecture → use Level 1 redaction

3. **Check for required credentials:**
   - Do you actually need to include the real credential?
   - Can you use a placeholder instead?

### When in Doubt

- Use **Level 1 (Full Redaction)** for anything sensitive
- Add explanatory note in Appendix
- Provide instructions for recreating information from .env.example

### After Creating Documentation

1. Run verification: `/sensitive-doc-creator --verify=your-file.md`
2. Check .gitignore: `git status | grep gitignore`
3. Verify before commit: `git diff HEAD` includes only your changes
4. Use provided commit command from verification report

## Troubleshooting

### Issue: "False positive detected for example@test.com"

**Solution:** The skill recognizes common false positive patterns:
- Emails in `.env.example` files
- Generic examples like `user@example.com`
- Documentation headers with contact info

If you have a legitimate false positive:
1. Review the context
2. Confirm it's safe (e.g., in documentation header)
3. Use `--context-check=false` if confident
4. Report the pattern for filter refinement

### Issue: "Redaction level too strict for my use case"

**Solution:** Choose appropriate redaction level:
- **Level 1**: API keys, passwords, secrets
- **Level 2**: Emails, transaction IDs (if context-dependent)
- **Level 3**: Configuration structure, connection string format

Example:
```bash
/sensitive-doc-creator \
  --input=src/lib/api/config.ts \
  --output=API_CONFIG.md \
  --redaction-level=placeholder
```

### Issue: "Cannot update .gitignore - not a git repo"

**Solution:** Ensure you're in the project root:
```bash
cd /Users/adamaslan/code/gcp\ app\ w\ mcp
/sensitive-doc-creator --auto-gitignore
```

## Frequently Asked Questions

**Q: Should I use Level 1 or Level 3 redaction for API keys in examples?**
A: Always use Level 1 (full redaction) for real API keys. Use Level 3 (placeholder) only for documentation showing the format, not real credentials.

**Q: Can I include real API keys with a warning?**
A: No. Always redact real credentials completely. If you need to show format, use placeholders or example keys from documentation.

**Q: What if I need to include real transaction data for debugging?**
A: Anonymize transaction IDs and amounts. Use fake dates and customer information. The goal is reproducible examples without exposing real data.

**Q: How do I rotate exposed credentials found in documentation?**
A: Follow the remediation guide in the verification report. Most importantly: rotate the credential immediately before committing any changes.

**Q: Can I use git commit --amend to remove exposed credentials from the last commit?**
A: Not recommended if already pushed. Use `git filter-branch` or BFG Repo-Cleaner. See remediation guide for detailed instructions.

## Summary

The Sensitive Documentation Creator skill provides a comprehensive, five-phase approach to creating safe documentation:

1. **Pre-Flight Analysis** - Identify and assess sensitive data
2. **Safe Environment Setup** - Create secure workspace
3. **Interactive Documentation** - Build safe documentation with redaction
4. **Verification** - Multi-stage safety checks
5. **Safe Storage** - .gitignore integration and commit guidance

By following this workflow, you can create detailed, useful documentation while protecting sensitive credentials and data.

## Related Skills

- **sensitive-data-scan** - Comprehensive repository security scanning
- **code-review** - General code quality and security review
- **docker-security** - Container security best practices

## Support

For questions about:
- **Redaction levels** - See "Redaction Templates" section
- **Specific data types** - See "Sensitive Data Pattern Database"
- **Integration** - See "Integration with Existing Tools"
- **Troubleshooting** - See "Troubleshooting" section

