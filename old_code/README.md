# Old Code Archive

This directory contains legacy code, outdated implementations, and archived files that have been consolidated or superseded by the unified `src/technical_analysis_mcp/` library.

## Directory Structure

### `/cloud-run/`
Old FastAPI Cloud Run implementation with duplicate analysis logic.

**Status**: Superseded by Cloud Functions (`automation/functions/daily_analysis/main.py`)

**Why it's here**:
- Contains redundant indicator calculations
- Duplicated signal detection logic
- Not used in current pipeline

### `/mcp1/`
Earlier MCP server implementation.

**Status**: Superseded by `src/technical_analysis_mcp/server.py`

**Why it's here**:
- Preliminary server structure
- Features absorbed into main MCP implementation

### `/guides/`
Historical documentation and guides that have been updated.

**Status**: Archived for reference

**Contents**: Guides 1-6, Jupyter setup docs, old deployment guides

### `/scripts/`
Outdated utility scripts.

**Status**: Partially superseded

**Contents**:
- `cleanup.sh` - replaced by proper cloud cleanup
- `init-firestore.py` - manual setup (now automated)
- `test-api.sh` - old API testing

## Migration Path

If you're looking for functionality that was in old code:

### Analysis Logic
**Old**: `cloud-run/calculate_indicators.py`, `cloud-run/detect_signals.py`, etc.
**New**: `src/technical_analysis_mcp/indicators.py`, `src/technical_analysis_mcp/signals.py`
**Use**: Import from `technical_analysis_mcp` in any deployment context

### Signal Ranking
**Old**: `cloud-run/rank_signals_ai.py`
**New**: `src/technical_analysis_mcp/ranking.py` (with both RuleBasedRanking and GeminiRanking)
**Use**: StockAnalyzer handles this automatically

### Cloud Deployment
**Old**: FastAPI in `cloud-run/main.py`
**New**: Cloud Functions in `automation/functions/daily_analysis/main.py`
**Use**: Deploy via `automation/deploy.sh`

### Data Fetching
**Old**: Inline yfinance calls in multiple files
**New**: `src/technical_analysis_mcp/data.py` with CachedDataFetcher
**Use**: StockAnalyzer handles caching and retry logic

### Server Integration
**Old**: `mcp1/server.py`
**New**: `src/technical_analysis_mcp/server.py`
**Use**: Run via Claude Code or integrate with other tools

## When to Delete

It's safe to delete files in this directory when:
1. ✅ All functionality has been migrated to `src/technical_analysis_mcp/`
2. ✅ No deployment still references these files
3. ✅ Documentation has been updated with new references
4. ✅ Tests pass with unified library

## Keep for Reference

Consider keeping some files for architectural reference:
- Historical deployment approaches
- Example configurations
- Problem-solving approaches that worked

## Current Status

- **Unified Library**: ✅ Complete (`src/technical_analysis_mcp/`)
- **Cloud Function**: ✅ Migrated to use shared library
- **Local Analysis**: ✅ Uses shared library via `run_analysis.py`
- **MCP Server**: ✅ Uses shared library
- **Duplication**: ❌ Eliminated

---

**Last Updated**: 2026-01-06
