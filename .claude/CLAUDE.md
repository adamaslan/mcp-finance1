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

**Last Updated**: January 28, 2026
**Version**: 1.1
**Status**: Production Ready
