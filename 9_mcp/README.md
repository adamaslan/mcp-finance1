# MCP Finance - 9 Tools

All 9 stock analysis tools organized in individual folders with consistent structure.

## Tools Directory

```
9_mcp/
├── analyze_fibonacci/          # Fibonacci retracement analysis
├── analyze_security/           # Security analysis with AI insights
├── compare_securities/         # Compare multiple securities
├── get_trade_plan/            # Generate trading strategies
├── morning_brief/             # Daily market summary
├── options_risk_analysis/     # Options portfolio risk analysis
├── portfolio_risk/            # Portfolio risk metrics
├── scan_trades/               # Scan for trading opportunities
└── screen_securities/         # Security screening with parallel processing
```

## Tool Structure

Each tool follows the same pattern:

```
tool_name/
├── __init__.py           # Tool export and entry point
├── core/                 # Core logic and models
│   └── __init__.py
└── handlers/             # Request handlers
    └── __init__.py
```

### Example: security_analyzer

```
security_analyzer/
├── __init__.py
├── core/
│   ├── __init__.py
│   ├── models.py         # (Optional) Data models
│   └── utils.py          # (Optional) Utilities
└── handlers/
    ├── __init__.py
    └── analyze.py        # (Optional) Analysis logic
```

## Usage

Import any tool:

```python
from mcp_finance.tools import analyze_security, get_trade_plan

result = await analyze_security("AAPL", period="1mo")
plan = await get_trade_plan("TSLA", risk_profile="neutral")
```

Or import from 9_mcp:

```python
from mcp_finance_1._mcp import analyze_security, morning_brief

result = await analyze_security("SPY")
brief = await morning_brief()
```

## Adding New Modules

To add new functionality to a tool:

1. Create module in `tool_name/handlers/`:
   ```
   tool_name/handlers/
   ├── __init__.py
   └── new_module.py
   ```

2. Import in `handlers/__init__.py`:
   ```python
   from .new_module import some_function
   ```

3. Use in tool's main `__init__.py`

## Modifying Existing Tools

Each tool is independent - modify without affecting others:

- Update `tool_name/core/` for business logic
- Update `tool_name/handlers/` for API handlers
- Keep `tool_name/__init__.py` for exports

## Common Structure (fibonacci)

The fibonacci tool already has this structure:
- `core/` - Core models (enums, registry)
- `analysis/` - Analysis logic
- `signals/` - Signal generation

This is a good reference for expanding other tools.

---

**Created**: Feb 24, 2026
**Status**: ✅ Complete - All 9 tools organized
