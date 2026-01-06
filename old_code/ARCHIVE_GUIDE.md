# Archive Guide: Old Code Directory

## Purpose

This directory archives code that has been consolidated into the unified `src/technical_analysis_mcp/` library. All functionality has been migrated to the single source of truth.

## Directory Contents

### ✅ To Be Archived (Copy Here When Ready)

```bash
# Copy when ready to completely clean up
cp -r cloud-run/ old_code/
cp -r mcp1/ old_code/
cp guide1.md guide2.md guide3-reqs.md guide4-jupyter.md guide5-cells-explained.md guide6-startup.md old_code/guides/
cp scripts/cleanup.sh scripts/init-firestore.py scripts/test-api.sh old_code/scripts/
```

### Files That Should Be Here

#### `/cloud-run/`
- `main.py` - Old FastAPI Cloud Run implementation
- `calculate_indicators.py` - Duplicate indicator logic
- `detect_signals.py` - Duplicate signal detection
- `rank_signals_ai.py` - Duplicate ranking logic
- `requirements.txt` - Old dependencies

**Why**: Superseded by Cloud Functions (`automation/functions/`)

#### `/mcp1/`
- `server.py` - Earlier MCP server implementation

**Why**: Superseded by `src/technical_analysis_mcp/server.py`

#### `/guides/`
- `guide1.md` through `guide6.md` - Historical setup guides
- `guide3-reqs.md` - Requirements documentation
- `guide4-jupyter.md` - Jupyter notebook guide
- `guide5-cells-explained.md` - Cell explanations
- `guide6-startup.md` - Startup guide

**Why**: Superseded by comprehensive guides in root:
- `AUTOMATED-PIPELINE-GUIDE.md`
- `GCP-MCP-OPTIMIZATION-GUIDE.md`
- `REFACTORING-AND-FREE-TIER-OPTIMIZATION.md`

#### `/scripts/`
- `cleanup.sh` - Old cleanup script
- `init-firestore.py` - Manual Firestore setup
- `test-api.sh` - Old API testing

**Why**: Superseded by automated deployment (`automation/deploy.sh`)

## What Stays in Root

✅ Current, active files:

```
automation/
├── deploy.sh                    ← Active deployment
└── functions/daily_analysis/
    ├── main.py                  ← Updated to use shared library
    └── requirements.txt

src/technical_analysis_mcp/     ← SINGLE SOURCE OF TRUTH
├── analysis.py                  ← New unified analyzer
├── indicators.py                ← Fixed RSI bug
├── signals.py
├── ranking.py
├── data.py
├── models.py
├── exceptions.py
├── config.py
└── server.py

run_analysis.py                  ← Uses shared library
view_firestore.py                ← Reference implementation

Documentation:
├── REFACTORING-SUMMARY.md
├── REFACTORING-AND-FREE-TIER-OPTIMIZATION.md
├── ARCHITECTURE-BEFORE-AFTER.md
├── AUTOMATED-PIPELINE-GUIDE.md
├── GCP-MCP-OPTIMIZATION-GUIDE.md
└── More...
```

## Migration Checklist

- [x] Unified code in `src/technical_analysis_mcp/`
- [x] Fixed RSI bug
- [x] Updated Cloud Function
- [x] Updated local scripts
- [ ] Copy old files to `old_code/`
- [ ] Verify all functionality works from shared library
- [ ] Delete old files from root (1-2 weeks after confirmation)

## Safe Deletion Timeline

### Immediate (Can delete now)
```bash
# These are not used
rm -f universes.py
rm -f server.py (move to old_code, then update references)
```

### After 1 week verification
```bash
# After confirming no references
rm -rf cloud-run/
rm -rf mcp1/
```

### After 2 weeks verification
```bash
# After confirming guides are updated
rm -f guide*.md
rm -rf scripts/
```

### Keep indefinitely
```bash
# Keep as reference for architecture decisions
old_code/README.md
old_code/ARCHIVE_GUIDE.md
```

## Reference: What Moved Where

### Analysis Logic

| Old Location | New Location | Component |
|---|---|---|
| `cloud-run/calculate_indicators.py` | `src/technical_analysis_mcp/indicators.py` | Indicators |
| `cloud-run/detect_signals.py` | `src/technical_analysis_mcp/signals.py` | Signals |
| `cloud-run/rank_signals_ai.py` | `src/technical_analysis_mcp/ranking.py` | Ranking |
| `automation/.../main.py` (inline) | `src/technical_analysis_mcp/analysis.py` | Orchestrator |

### Cloud Deployment

| Old | New |
|---|---|
| `cloud-run/main.py` (FastAPI) | `automation/functions/.../main.py` (Cloud Function) |
| Manual setup | `automation/deploy.sh` (automated) |

### Documentation

| Old | New |
|---|---|
| `guide1-6.md` | `AUTOMATED-PIPELINE-GUIDE.md`, etc. |
| Scattered notes | Comprehensive guides in root |

## Why This Structure?

```
✅ Keeps git history (safe to delete later)
✅ Preserves architectural decisions
✅ Reference for old deployment patterns
✅ Can restore if needed
✅ Doesn't clutter active codebase
```

## Questions?

See:
- `README.md` in this directory for overview
- `REFACTORING-AND-FREE-TIER-OPTIMIZATION.md` for detailed changes
- `ARCHITECTURE-BEFORE-AFTER.md` for visual comparison

---

**Status**: Archive ready for cleanup after 2-week verification period
**Last Updated**: 2026-01-06
