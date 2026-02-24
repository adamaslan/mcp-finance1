# File Reorganization Plan: Beta1 Scan Script & Documentation

**Created**: 2026-01-20
**Goal**: Move `run_beta1_scan.py` and related files into proper source structure for git tracking

---

## Executive Summary

**Problem**: `run_beta1_scan.py` and related documentation files are currently in `/cloud-run/` root and are NOT tracked by git. They need to be moved to `/cloud-run/src/technical_analysis_mcp/` where they can be properly tracked and organized.

**Impact**: Minimal - The file already uses proper imports from `technical_analysis_mcp.*`, so most imports won't need changes.

**Risk Level**: Low - The script is self-contained and references are limited to documentation files and one shell script.

---

## Current State Analysis

### Files Not Tracked by Git (in /cloud-run/)

```
?? cloud-run/BETA1-SCAN-GUIDE.md
?? cloud-run/DEPLOYMENT-LOG-TEMPLATE.md
?? cloud-run/DEPLOYMENT-QUICKSTART.md
?? cloud-run/DEPLOYMENT-README.md
?? cloud-run/DEPLOYMENT-REVIEW-SUMMARY.md
?? cloud-run/DEPLOYMENT-SETUP-REVIEW.md
?? cloud-run/RUN_BETA1_LOCALLY.md
?? cloud-run/call_beta1_via_api.sh
?? cloud-run/run_beta1_scan.py
```

### Current Import Structure in run_beta1_scan.py

```python
# Lines 22-24: Path setup for local testing
src_path = os.path.join(os.path.dirname(__file__), '..', 'src')
if os.path.exists(src_path):
    sys.path.insert(0, src_path)

# Lines 62-63: Imports
from technical_analysis_mcp.server import scan_trades
from technical_analysis_mcp.universes import get_universe, list_universes
```

### Files That Reference run_beta1_scan.py

1. **call_beta1_via_api.sh** (line 122)
   ```bash
   echo "  3. Save to Firebase: python3 run_beta1_scan.py"
   ```

2. **BETA1-SCAN-GUIDE.md** (multiple references)
   - Line 14: `python3 run_beta1_scan.py`
   - Line 158: `python3 run_beta1_scan.py`
   - Line 481: `/mcp-finance1/cloud-run/run_beta1_scan.py`

3. **RUN_BETA1_LOCALLY.md** (multiple references)
   - Line 55: `python3 run_beta1_scan.py`
   - Line 229: `python3 run_beta1_scan.py`
   - Line 239: `python3 run_beta1_scan.py`
   - Line 280: Full path reference

---

## Proposed Target Structure

```
/cloud-run/
├── main.py                          # Keep (already tracked)
├── Dockerfile                       # Keep (already tracked)
├── environment.yml                  # Keep (already tracked)
├── src/
│   └── technical_analysis_mcp/
│       ├── __init__.py             # Existing (tracked)
│       ├── server.py               # Existing (tracked)
│       ├── universes.py            # Existing (tracked)
│       ├── scanners/               # Existing directory
│       │   ├── __init__.py
│       │   └── beta1_scanner.py   # NEW: Move run_beta1_scan.py here (rename)
│       └── ... (other existing files)
├── scripts/                         # NEW: For convenience scripts
│   ├── call_beta1_via_api.sh       # Move here
│   └── activate_and_run.sh         # If it exists, move here
└── docs/                            # NEW: For documentation
    ├── BETA1-SCAN-GUIDE.md         # Move here
    ├── RUN_BETA1_LOCALLY.md        # Move here
    ├── DEPLOYMENT-QUICKSTART.md    # Move here
    ├── DEPLOYMENT-README.md        # Move here
    ├── DEPLOYMENT-SETUP-REVIEW.md  # Move here
    ├── DEPLOYMENT-REVIEW-SUMMARY.md # Move here
    └── DEPLOYMENT-LOG-TEMPLATE.md  # Move here
```

---

## Detailed Move Plan

### Phase 1: Create Directory Structure

```bash
# From /cloud-run/ directory
mkdir -p scripts
mkdir -p docs
```

### Phase 2: Move Documentation Files

Use `git mv` to preserve history (even though not currently tracked, this prepares for tracking):

```bash
cd /Users/adamaslan/code/gcp\ app\ w\ mcp/mcp-finance1/cloud-run

# Move all documentation
mv BETA1-SCAN-GUIDE.md docs/
mv RUN_BETA1_LOCALLY.md docs/
mv DEPLOYMENT-QUICKSTART.md docs/
mv DEPLOYMENT-README.md docs/
mv DEPLOYMENT-SETUP-REVIEW.md docs/
mv DEPLOYMENT-REVIEW-SUMMARY.md docs/
mv DEPLOYMENT-LOG-TEMPLATE.md docs/
```

### Phase 3: Move Shell Scripts

```bash
# Move convenience script
mv call_beta1_via_api.sh scripts/

# If activate_and_run.sh exists:
# mv activate_and_run.sh scripts/
```

### Phase 4: Move and Refactor run_beta1_scan.py

**Option A: Keep as Standalone Script** (Recommended for now)
```bash
# Move to scripts directory as executable
mv run_beta1_scan.py scripts/
chmod +x scripts/run_beta1_scan.py
```

**Option B: Integrate into Package** (Future enhancement)
```bash
# Move into scanners module (requires more refactoring)
mv run_beta1_scan.py src/technical_analysis_mcp/scanners/beta1_scanner.py
```

**Recommendation**: Use **Option A** initially for minimal disruption.

---

## Import Changes Required

### For run_beta1_scan.py (if moved to scripts/)

**Current (lines 22-24)**:
```python
src_path = os.path.join(os.path.dirname(__file__), '..', 'src')
if os.path.exists(src_path):
    sys.path.insert(0, src_path)
```

**New (if in scripts/)**:
```python
src_path = os.path.join(os.path.dirname(__file__), '..', 'src')
if os.path.exists(src_path):
    sys.path.insert(0, src_path)
```

**No change needed!** The relative path `../src` still works from `scripts/` directory.

### For main.py (NO CHANGES NEEDED)

main.py already has robust path handling (lines 25-31):
```python
for path in ['/app/src', '/workspace/src', '../src', './src']:
    if os.path.isdir(path):
        sys.path.insert(0, path)
        break
```

---

## Path Reference Updates

### File: scripts/call_beta1_via_api.sh

**Line 122**:
```bash
# OLD
echo "  3. Save to Firebase: python3 run_beta1_scan.py"

# NEW
echo "  3. Save to Firebase: python3 scripts/run_beta1_scan.py"
```

### File: docs/BETA1-SCAN-GUIDE.md

**Line 14**:
```bash
# OLD
python3 run_beta1_scan.py

# NEW
python3 scripts/run_beta1_scan.py
```

**Line 158**:
```bash
# OLD
python3 run_beta1_scan.py

# NEW
python3 scripts/run_beta1_scan.py
```

**Line 481**:
```bash
# OLD
- **Script**: `/mcp-finance1/cloud-run/run_beta1_scan.py`

# NEW
- **Script**: `/mcp-finance1/cloud-run/scripts/run_beta1_scan.py`
```

### File: docs/RUN_BETA1_LOCALLY.md

**Line 55**:
```bash
# OLD
python3 run_beta1_scan.py

# NEW
python3 scripts/run_beta1_scan.py
```

**Line 229**:
```bash
# OLD
python3 run_beta1_scan.py

# NEW
python3 scripts/run_beta1_scan.py
```

**Line 239**:
```bash
# OLD
python3 run_beta1_scan.py

# NEW
python3 scripts/run_beta1_scan.py
```

**Line 280**:
```bash
# OLD
- **Script**: `/Users/adamaslan/code/gcp app w mcp/mcp-finance1/cloud-run/run_beta1_scan.py`

# NEW
- **Script**: `/Users/adamaslan/code/gcp app w mcp/mcp-finance1/cloud-run/scripts/run_beta1_scan.py`
```

---

## Execution Path Updates

### Direct Python Execution

**OLD**:
```bash
cd /Users/adamaslan/code/gcp\ app\ w\ mcp/mcp-finance1/cloud-run
python3 run_beta1_scan.py
```

**NEW**:
```bash
cd /Users/adamaslan/code/gcp\ app\ w\ mcp/mcp-finance1/cloud-run
python3 scripts/run_beta1_scan.py
```

### Docker/Cloud Run (NO CHANGES NEEDED)

The Dockerfile likely doesn't reference run_beta1_scan.py directly - it's an on-demand script. If it does, update the COPY/CMD instructions:

```dockerfile
# If Dockerfile references it:
# OLD
COPY run_beta1_scan.py .

# NEW
COPY scripts/run_beta1_scan.py scripts/
```

---

## Git Tracking Strategy

### Add Files to Git

After moving, add all files to git:

```bash
cd /Users/adamaslan/code/gcp\ app\ w\ mcp/mcp-finance1

# Stage new directories
git add cloud-run/scripts/
git add cloud-run/docs/

# Verify what will be added
git status

# Commit with descriptive message
git commit -m "Reorganize: Move Beta1 scanner to scripts/ and docs to docs/

- Move run_beta1_scan.py to scripts/ for better organization
- Move all deployment and Beta1 docs to docs/ directory
- Move shell scripts to scripts/ directory
- Update all path references in documentation
- Update call_beta1_via_api.sh script paths

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

### Update .gitignore (if needed)

Check if any patterns accidentally exclude the new locations:

```bash
# Test what would be ignored
git check-ignore -v scripts/run_beta1_scan.py
git check-ignore -v docs/*.md
git check-ignore -v scripts/*.sh
```

**Current .gitignore doesn't exclude these** - no changes needed!

---

## Testing Strategy

### Pre-Move Testing

1. **Verify Current Script Works**:
   ```bash
   cd /Users/adamaslan/code/gcp\ app\ w\ mcp/mcp-finance1/cloud-run
   mamba activate fin-ai1
   export GCP_PROJECT_ID="ttb-lang1"
   python3 run_beta1_scan.py --help  # Or just run it
   ```

2. **Document Current Behavior**:
   - Note execution time
   - Verify Firebase saves
   - Check console output format

### Post-Move Testing

1. **Test Script from New Location**:
   ```bash
   cd /Users/adamaslan/code/gcp\ app\ w\ mcp/mcp-finance1/cloud-run
   mamba activate fin-ai1
   export GCP_PROJECT_ID="ttb-lang1"
   python3 scripts/run_beta1_scan.py
   ```

2. **Verify All Functionality**:
   - ✅ Script executes without import errors
   - ✅ Connects to Firebase successfully
   - ✅ Scans Beta1 universe (11 symbols)
   - ✅ Saves results to Firebase (3 collections)
   - ✅ Console output matches previous format
   - ✅ Execution time similar to before

3. **Test API Script**:
   ```bash
   cd /Users/adamaslan/code/gcp\ app\ w\ mcp/mcp-finance1/cloud-run
   chmod +x scripts/call_beta1_via_api.sh
   ./scripts/call_beta1_via_api.sh
   ```

4. **Verify Documentation**:
   - Open each doc file and verify path references
   - Test copy-paste commands from docs
   - Ensure all examples work

5. **Test Import from Other Modules** (if applicable):
   ```python
   # From Python REPL in cloud-run directory
   import sys
   sys.path.insert(0, 'src')
   from technical_analysis_mcp.server import scan_trades
   # Should work without errors
   ```

### Testing Checklist

- [ ] Pre-move: Current script runs successfully
- [ ] Pre-move: Firebase saves work
- [ ] Pre-move: Document baseline behavior
- [ ] Move: Execute all mv commands
- [ ] Move: Verify files in new locations
- [ ] Post-move: Script runs from scripts/ directory
- [ ] Post-move: All imports resolve correctly
- [ ] Post-move: Firebase connectivity works
- [ ] Post-move: Console output unchanged
- [ ] Post-move: API shell script works
- [ ] Post-move: All docs have correct paths
- [ ] Git: All files staged correctly
- [ ] Git: Commit message descriptive
- [ ] Git: No unintended .gitignore exclusions

---

## Rollback Plan

If anything breaks during or after the move:

### Immediate Rollback (Before Git Commit)

```bash
cd /Users/adamaslan/code/gcp\ app\ w\ mcp/mcp-finance1/cloud-run

# Undo all moves
mv scripts/run_beta1_scan.py .
mv scripts/call_beta1_via_api.sh .
mv docs/*.md .

# Remove empty directories
rmdir scripts docs

# Test original state
python3 run_beta1_scan.py
```

### Rollback After Git Commit

```bash
# Revert the commit
git revert HEAD

# Or reset to previous commit (if no one else has pulled)
git reset --hard HEAD~1

# Verify files are back
ls -la /Users/adamaslan/code/gcp\ app\ w\ mcp/mcp-finance1/cloud-run/
```

### Partial Rollback

If only specific files have issues:

```bash
# Restore specific file from git
git checkout HEAD -- cloud-run/scripts/run_beta1_scan.py

# Or copy from backup
cp /path/to/backup/run_beta1_scan.py scripts/
```

---

## Risk Assessment

### Low Risk Items (Safe to Move)

✅ **Documentation files** - No code dependencies, pure markdown
- BETA1-SCAN-GUIDE.md
- RUN_BETA1_LOCALLY.md
- DEPLOYMENT-*.md

✅ **Shell scripts** - Self-contained, easy to update
- call_beta1_via_api.sh

### Medium Risk Items (Requires Testing)

⚠️ **run_beta1_scan.py** - Core functionality, but good import structure
- Already uses relative imports
- Path setup is flexible
- No hardcoded absolute paths
- Imports from technical_analysis_mcp.* already

### No Risk Items

✅ **Existing source files** - Not moving
- src/technical_analysis_mcp/* (all stay in place)

---

## Dependencies and Blockers

### Prerequisites

1. ✅ Git repository initialized (confirmed)
2. ✅ Source structure exists (src/technical_analysis_mcp/)
3. ✅ Current script is functional (ready to test)
4. ✅ No conflicting files in target locations

### No Blockers Identified

All prerequisites are met. Safe to proceed.

---

## Alternative Approach: Minimal Move

If you want even lower risk, consider this minimal approach:

### Minimal Plan: Only Move Documentation

```bash
# Move only docs, leave scripts in root
cd /Users/adamaslan/code/gcp\ app\ w\ mcp/mcp-finance1/cloud-run
mkdir -p docs
mv BETA1-SCAN-GUIDE.md docs/
mv RUN_BETA1_LOCALLY.md docs/
mv DEPLOYMENT-*.md docs/
```

**Pros**:
- Zero code changes required
- Documentation is organized
- Scripts still work as-is
- Extremely low risk

**Cons**:
- run_beta1_scan.py still not tracked
- Scripts still in root directory
- Doesn't fully solve the git tracking issue

**Verdict**: Not recommended. The full move (scripts/ + docs/) is still low-risk and achieves the goal.

---

## Step-by-Step Execution Guide

### Step 1: Backup Current State

```bash
cd /Users/adamaslan/code/gcp\ app\ w\ mcp/mcp-finance1
cp -r cloud-run /tmp/cloud-run-backup-$(date +%Y%m%d_%H%M%S)
echo "Backup created at: /tmp/cloud-run-backup-$(date +%Y%m%d_%H%M%S)"
```

### Step 2: Pre-Move Test

```bash
cd /Users/adamaslan/code/gcp\ app\ w\ mcp/mcp-finance1/cloud-run
mamba activate fin-ai1
export GCP_PROJECT_ID="ttb-lang1"
python3 run_beta1_scan.py
# Wait for completion, verify success
```

### Step 3: Create Directory Structure

```bash
cd /Users/adamaslan/code/gcp\ app\ w\ mcp/mcp-finance1/cloud-run
mkdir -p scripts docs
```

### Step 4: Move Files

```bash
# Move script
mv run_beta1_scan.py scripts/

# Move API caller
mv call_beta1_via_api.sh scripts/

# Move documentation (one command)
mv BETA1-SCAN-GUIDE.md RUN_BETA1_LOCALLY.md \
   DEPLOYMENT-QUICKSTART.md DEPLOYMENT-README.md \
   DEPLOYMENT-SETUP-REVIEW.md DEPLOYMENT-REVIEW-SUMMARY.md \
   DEPLOYMENT-LOG-TEMPLATE.md docs/

# Make scripts executable
chmod +x scripts/*.sh scripts/*.py
```

### Step 5: Update Path References

Update the files listed in "Path Reference Updates" section above:
- scripts/call_beta1_via_api.sh (line 122)
- docs/BETA1-SCAN-GUIDE.md (lines 14, 158, 481)
- docs/RUN_BETA1_LOCALLY.md (lines 55, 229, 239, 280)

Use the Edit tool to make these changes.

### Step 6: Post-Move Test

```bash
cd /Users/adamaslan/code/gcp\ app\ w\ mcp/mcp-finance1/cloud-run
mamba activate fin-ai1
export GCP_PROJECT_ID="ttb-lang1"
python3 scripts/run_beta1_scan.py
# Verify same behavior as pre-move test
```

### Step 7: Test API Script

```bash
cd /Users/adamaslan/code/gcp\ app\ w\ mcp/mcp-finance1/cloud-run
./scripts/call_beta1_via_api.sh http://localhost:8080
```

### Step 8: Git Add and Commit

```bash
cd /Users/adamaslan/code/gcp\ app\ w\ mcp/mcp-finance1

# Stage changes
git add cloud-run/scripts/
git add cloud-run/docs/

# Review what will be committed
git status
git diff --cached

# Commit
git commit -m "Reorganize: Move Beta1 scanner to scripts/ and docs to docs/

- Move run_beta1_scan.py to scripts/ for better organization
- Move all deployment and Beta1 docs to docs/ directory
- Move shell scripts to scripts/ directory
- Update all path references in documentation
- Update call_beta1_via_api.sh script paths

Files now properly tracked in git for version control.

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

### Step 9: Final Verification

```bash
# Verify git tracking
git ls-files cloud-run/scripts/
git ls-files cloud-run/docs/

# Test one more time
cd cloud-run
python3 scripts/run_beta1_scan.py
```

---

## Post-Implementation Tasks

### Update README Files

If there's a root README or cloud-run/README.md, update it to reflect new structure:

```markdown
## Directory Structure

- `scripts/` - Executable scripts for Beta1 scanning and API calls
  - `run_beta1_scan.py` - Main Beta1 universe scanner
  - `call_beta1_via_api.sh` - API client for scan endpoint
- `docs/` - Documentation for deployment and usage
  - `BETA1-SCAN-GUIDE.md` - Comprehensive Beta1 scanning guide
  - `RUN_BETA1_LOCALLY.md` - Local execution instructions
  - `DEPLOYMENT-*.md` - Deployment guides and templates
- `src/technical_analysis_mcp/` - Core analysis package
```

### Update Shell Aliases (if any exist)

Check user's shell config (~/.zshrc, ~/.bash_profile):

```bash
# OLD alias (line 236 in RUN_BETA1_LOCALLY.md)
alias beta1-scan='cd "/Users/adamaslan/code/gcp app w mcp/mcp-finance1/cloud-run" && \
mamba activate fin-ai1 && \
export GCP_PROJECT_ID="ttb-lang1" && \
python3 run_beta1_scan.py'

# NEW alias
alias beta1-scan='cd "/Users/adamaslan/code/gcp app w mcp/mcp-finance1/cloud-run" && \
mamba activate fin-ai1 && \
export GCP_PROJECT_ID="ttb-lang1" && \
python3 scripts/run_beta1_scan.py'
```

### Update Cloud Run Job Definition (if exists)

If there's a Cloud Run job config for run_beta1_scan.py:

```bash
# Check if Cloud Run job exists
gcloud run jobs list --region=us-central1 | grep beta1

# If exists, update the command:
gcloud run jobs update beta1-scan \
  --region=us-central1 \
  --command="python3" \
  --args="scripts/run_beta1_scan.py"
```

---

## Success Criteria

The reorganization is successful when:

✅ All files are in their new locations
✅ `run_beta1_scan.py` is tracked by git
✅ Script executes successfully from new location
✅ All documentation has correct paths
✅ API shell script works
✅ No import errors
✅ Firebase connectivity maintained
✅ Console output unchanged
✅ Git history is clean
✅ README files updated
✅ No performance degradation

---

## Timeline Estimate

- **Planning & Review**: 10 minutes (this document)
- **Backup**: 2 minutes
- **Pre-move testing**: 2-3 minutes
- **File moves**: 2 minutes
- **Update references**: 5-10 minutes
- **Post-move testing**: 5 minutes
- **Git commit**: 2 minutes
- **Final verification**: 2 minutes

**Total**: 30-40 minutes

---

## Notes and Considerations

### Why scripts/ Instead of src/technical_analysis_mcp/scanners/?

1. **Separation of Concerns**:
   - `run_beta1_scan.py` is an **executable script**, not a library module
   - It's meant to be run directly, not imported
   - It's a convenience wrapper around the library

2. **Deployment Flexibility**:
   - Scripts can be updated independently
   - No need to rebuild/reinstall package
   - Can be scheduled directly (cron, Cloud Scheduler)

3. **Convention**:
   - Most Python projects have a `scripts/` or `bin/` directory
   - Source code lives in `src/`, executables in `scripts/`

4. **Future Option**:
   - Can still create a proper CLI entry point later
   - Could use setuptools `console_scripts` in the future
   - This approach doesn't prevent that

### Future Enhancement: Make it a Proper CLI

Once settled, consider creating a proper CLI entry point:

```python
# In setup.py or pyproject.toml
[project.scripts]
beta1-scan = "technical_analysis_mcp.cli:run_beta1_scan"
```

But for now, the scripts/ approach is simpler and safer.

---

## Appendix: File Contents Summary

### run_beta1_scan.py
- **Purpose**: Scans Beta1 universe, saves to Firebase
- **Dependencies**: technical_analysis_mcp.server, technical_analysis_mcp.universes, firestore
- **Entry point**: `if __name__ == "__main__"` block (line 226)
- **No command-line arguments** - all config via env vars and hardcoded defaults
- **Async**: Uses asyncio.run() (line 214)

### call_beta1_via_api.sh
- **Purpose**: HTTP client for /api/scan endpoint
- **Dependencies**: curl, jq
- **Configurable**: URL and max_results via args
- **Reference to run_beta1_scan.py**: Line 122 (documentation only)

---

## Approval & Sign-off

**Plan Created By**: File Reorganization Planning Agent
**Date**: 2026-01-20
**Review Status**: ⏳ Awaiting review

**Next Steps**:
1. Review this plan
2. Approve for execution (or suggest modifications)
3. Execute according to Step-by-Step Execution Guide
4. Verify success against Success Criteria

---

**Ready to proceed?** If approved, we can execute this plan step-by-step with careful testing at each stage.
