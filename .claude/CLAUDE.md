# MCP Finance - Project Guidelines

## 📝 PROJECT LOGS & DOCUMENTATION

**Preferred location for project update logs & change documentation:**
- Store all update logs, change summaries, and feature documentation in `nu-logs2/` folder
- Create files with clear naming: `FEATURE_UPDATE_vX.X.md`, `BUG_FIX_SUMMARY.md`, etc.
- This keeps project history organized and separate from code
- All major updates should have corresponding documentation files

### Recent Updates
- `INTRADAY_PERIODS_UPDATE_v1.1.md` - Added 15m, 1h, 4h period support to all 9 MCP tools

---

## Development Workflow

### When Making Changes
1. ✅ Make code changes in src/ and supporting files
2. ✅ Create corresponding documentation in nu-logs2/ with update log
3. ✅ Include version number and date in filename
4. ✅ Link from main docs (MCP_DATA_PERIODS_GUIDE.md, etc.) when relevant

### Important Files
- `MCP_DATA_PERIODS_GUIDE.md` - Complete guide to data periods for all 9 tools
- `FINAL_MCP_TEST_REPORT.md` - Latest test results and bug tracking
- `nu-logs2/` - All update logs and change documentation

---

## Current Version

**MCP Finance v1.1** - Intraday Periods Support
- All 9 MCP tools now support configurable periods
- Added 15m, 1h, 4h intraday periods
- All changes backward compatible

---

## Key Technical Guidelines

### From Global CLAUDE.md
This project follows Python Development Guidelines 2 from `~/.claude/CLAUDE.md`

Key principles:
- Single Responsibility Principle
- Early returns and guard clauses
- Proper error handling
- Type hints throughout
- Comprehensive documentation

### Project-Specific Rules

1. **No Mock Data** - Never use fake/hardcoded data
2. **Period Flexibility** - All analysis tools must accept configurable periods
3. **Error Handling** - Return HTTP 503 if dependencies unavailable
4. **Testing** - Always test period changes with `test_all_mcp_tools_fixed.py`
5. **Documentation** - Update logs go in `nu-logs2/` folder
6. **Four-Layer Data Retrieval** - All data fetching must follow the four-layer cache hierarchy
   - Base Pattern: `.claude/rules/FOUR_LAYER_DATA_RETRIEVAL.md`
   - GCP-Optimized (RECOMMENDED): `.claude/rules/GCLOUD_OPTIMIZED_DATA_RETRIEVAL.md`
   - Quick References: `.claude/skills/four-layer-cache.md` and `.claude/skills/gcp-optimized-cache.md`

   **GCP Stack (Preferred for Production)**:
   - Layer 0: Secret Manager (API keys)
   - Layer 1: Memorystore/Redis (distributed cache)
   - Layer 2a: Firestore (real-time results)
   - Layer 2b: Cloud Storage (historical data)
   - Layer 3: BigQuery (pre-computed metrics)
   - Layer 4: API providers (yfinance, Alpha Vantage, Finnhub)

---

## 🔐 Secret Scanning for Commits & PRs

### CRITICAL RULE: Automatic Secret Prevention

**All commits are automatically scanned for secrets before allowing them to be created.** This is enforced via git pre-commit hooks and MUST NOT be bypassed.

### What Gets Blocked

The pre-commit hook will **BLOCK** commits if it detects:

- ❌ **GCP API Keys** - `AIzaSy*` pattern
- ❌ **GCP OAuth Secrets** - `GOCSPX-*` pattern
- ❌ **GCP Access Tokens** - `ya29.*` pattern
- ❌ **GCP Refresh Tokens** - `1//*` pattern
- ❌ **Service Account JSON files** - files containing service_account type with private_key fields
- ❌ **Stripe API Keys** - `sk_live_*`, `rk_live_*`, `pk_live_*`
- ❌ **Database connection strings** - `postgresql://`, `mysql://` with credentials
- ❌ **AWS Credentials** - AWS_SECRET_ACCESS_KEY, AWS_ACCESS_KEY_ID
- ❌ **Password assignments** - `password=`, `secret=`, `api_key=`

### Before Creating PRs

1. **Never commit actual secrets** - Use .env files (gitignored) instead
2. **Use placeholder values** - Example: `API_KEY=your-api-key-here`
3. **Check .gitignore** - Ensure sensitive files are properly ignored
4. **Scan manually if needed** - See "If hook needs to be bypassed" below

### If Pre-commit Hook Blocks Your Commit

**This is expected behavior!** Do NOT use `--no-verify` without investigation:

```bash
# 1. Check what triggered the block
git diff --cached

# 2. Remove the secret from the file
# Edit the file to use a placeholder value

# 3. Stage the fix
git add <file>

# 4. Try committing again
git commit -m "your message"
```

### If You MUST Override (Emergency Only)

```bash
# Only use if you've verified no real secrets are in the commit
git commit --no-verify -m "your message"

# Then IMMEDIATELY:
git log --oneline | head -1  # Get commit hash
git reset --soft HEAD~1      # Undo commit
# Fix the issue
git commit -m "corrected message"
```

### For PR Reviewers

When reviewing PRs, verify:
- ✅ No .env files are included
- ✅ No real API keys in code examples
- ✅ Database passwords are redacted
- ✅ GCP credentials paths use relative references (e.g., `~/.gcloud-credentials/`)
- ✅ All examples use placeholder values

### Sensitive Data Patterns in .gitignore

The following are automatically ignored (even if accidentally staged):
```
.env*              # All environment files
*.key              # Key files
*.pem              # PEM certificates
*secret*           # Secret files
*credentials*      # Credential files
*password*         # Password files
```

### Security Checklist Before Committing

- [ ] Reviewed all `git diff --cached` output
- [ ] No real API keys in staged files
- [ ] No database passwords visible
- [ ] No GCP/AWS credentials
- [ ] All placeholders use example values
- [ ] .env files are in .gitignore
- [ ] Documentation uses generic examples

---

## MCP Tools Reference

All 9 MCP tools now support configurable periods:

1. **analyze_security** - Single security analysis with 150+ signals
2. **compare_securities** - Compare multiple securities (newly configurable)
3. **screen_securities** - Screen universe against criteria (newly configurable)
4. **get_trade_plan** - Risk-qualified trade plans with stops/targets
5. **scan_trades** - Scan universe for qualified setups (newly configurable)
6. **portfolio_risk** - Assess portfolio risk across positions (newly configurable)
7. **morning_brief** - Daily market briefing with signals (newly configurable)
8. **analyze_fibonacci** - Fibonacci levels and signals
9. **options_risk_analysis** - Options chain analysis (no period needed)

---

**Last Updated**: March 3, 2026
**Version**: 1.1
**Status**: Production Ready

## Recent Changes (March 3, 2026)

- Added `Four-Layer Data Retrieval` rule - Enforces unified caching architecture across all data fetching
- Created `.claude/rules/FOUR_LAYER_DATA_RETRIEVAL.md` - Complete guide with implementation patterns
- Rule applies to all 9 MCP tools and any new data fetching code
