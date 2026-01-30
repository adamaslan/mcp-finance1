# /add-period-param - Add Period Parameter to MCP Tools

Automatically add configurable `period` parameter to MCP tools that are missing it.

## Usage

```
/add-period-param [--tool TOOL_NAME] [--default-period PERIOD] [--file FILE_PATH]
```

**Examples:**
- `/add-period-param` - Add period to all tools missing it in cloud-run/server.py
- `/add-period-param --tool compare_securities` - Add period only to compare_securities
- `/add-period-param --default-period 6mo` - Use 6mo as default instead of 3mo
- `/add-period-param --file src/technical_analysis_mcp/server.py` - Target src/ version

## Behavior

When this skill is invoked:

1. **Scan the server.py file** to identify MCP tools missing the `period` parameter
2. **Update function signatures** to add `period: str = "3mo"` parameter
3. **Update tool registrations** (inputSchema) to include period property
4. **Replace hardcoded periods** (like `period="1mo"`) with the parameter
5. **Verify changes** don't break existing functionality

## What Gets Updated

### Function Signature
```python
# Before
async def compare_securities(
    symbols: list[str],
    metric: str = "signals",
) -> dict[str, Any]:

# After
async def compare_securities(
    symbols: list[str],
    metric: str = "signals",
    period: str = "3mo",
) -> dict[str, Any]:
```

### Function Docstring
```python
# Before
"""Compare multiple securities.

Args:
    symbols: List of ticker symbols.
    metric: Comparison metric.

Returns:
    Comparison result with ranked securities.
"""

# After
"""Compare multiple securities.

Args:
    symbols: List of ticker symbols.
    metric: Comparison metric.
    period: Time period for analysis (1mo, 3mo, 6mo, 1y, etc).

Returns:
    Comparison result with ranked securities.
"""
```

### Tool Registration (inputSchema)
```python
# Before
Tool(
    name="compare_securities",
    description="Compare multiple stocks/ETFs and find the best pick",
    inputSchema={
        "type": "object",
        "properties": {
            "symbols": {...},
            "metric": {...},
        },
        "required": ["symbols"],
    },
),

# After
Tool(
    name="compare_securities",
    description="Compare multiple stocks/ETFs and find the best pick",
    inputSchema={
        "type": "object",
        "properties": {
            "symbols": {...},
            "metric": {...},
            "period": {
                "type": "string",
                "default": "3mo",
                "description": "Time period for analysis (1mo, 3mo, 6mo, 1y, etc)",
            },
        },
        "required": ["symbols"],
    },
),
```

### Hardcoded Period Replacement
```python
# Before
analysis = await analyze_security(symbol, period="1mo")

# After
analysis = await analyze_security(symbol, period=period)
```

## Implementation Steps

### 1. Identify Tools Missing Period Parameter

```python
import re
from pathlib import Path

def find_tools_missing_period(server_file: str) -> list[str]:
    """Find MCP tools missing the period parameter."""
    with open(server_file) as f:
        content = f.read()

    # Find all async function definitions
    tool_pattern = r'async def (\w+)\((.*?)\) -> dict\[str, Any\]:'
    tools = re.findall(tool_pattern, content, re.DOTALL)

    missing_period = []
    for tool_name, params in tools:
        # Skip if already has period parameter
        if 'period:' not in params and 'period =' not in params:
            # Check if it calls analyze_security or similar (likely needs period)
            func_start = content.find(f'async def {tool_name}')
            func_end = content.find('\n\nasync def', func_start + 1)
            func_body = content[func_start:func_end if func_end > 0 else len(content)]

            # If it calls analyze_security with hardcoded period, it needs the param
            if 'period="' in func_body or 'period=\''\in func_body:
                missing_period.append(tool_name)

    return missing_period
```

### 2. Update Function Signature

```python
def add_period_to_function(content: str, tool_name: str, default_period: str = "3mo") -> str:
    """Add period parameter to function signature and docstring."""
    # Find function definition
    func_pattern = rf'(async def {tool_name}\()(.*?)(\) -> dict\[str, Any\]:)'
    match = re.search(func_pattern, content, re.DOTALL)

    if not match:
        return content

    prefix, params, suffix = match.groups()

    # Add period parameter (after last param, before closing paren)
    params = params.rstrip() + f',\n    period: str = "{default_period}",'

    new_func_def = f'{prefix}{params}{suffix}'
    content = content.replace(match.group(0), new_func_def)

    # Update docstring
    docstring_pattern = rf'({tool_name}.*?""".*?Args:.*?)(Returns:)'
    docstring_match = re.search(docstring_pattern, content, re.DOTALL)

    if docstring_match:
        args_section, returns = docstring_match.groups()
        period_doc = f"        period: Time period for analysis (1mo, 3mo, 6mo, 1y, etc).\n\n    {returns}"
        content = content.replace(f'{args_section}{returns}', f'{args_section}{period_doc}')

    return content
```

### 3. Update Tool Registration

```python
def add_period_to_tool_schema(content: str, tool_name: str, default_period: str = "3mo") -> str:
    """Add period property to tool's inputSchema."""
    # Find tool registration
    tool_pattern = rf'Tool\(\s*name="{tool_name}".*?inputSchema=\{{.*?\}},\s*\),'
    match = re.search(tool_pattern, content, re.DOTALL)

    if not match:
        return content

    tool_def = match.group(0)

    # Find properties section
    props_pattern = r'("properties": \{)(.*?)(\})'
    props_match = re.search(props_pattern, tool_def, re.DOTALL)

    if props_match:
        prefix, properties, suffix = props_match.groups()

        # Add period property
        period_prop = f'''
                    "period": {{
                        "type": "string",
                        "default": "{default_period}",
                        "description": "Time period for analysis (1mo, 3mo, 6mo, 1y, etc)",
                    }},'''

        new_properties = f'{prefix}{properties}{period_prop}\n{suffix}'
        new_tool_def = tool_def.replace(f'{prefix}{properties}{suffix}', new_properties)
        content = content.replace(tool_def, new_tool_def)

    return content
```

### 4. Replace Hardcoded Periods

```python
def replace_hardcoded_periods(content: str, tool_name: str) -> str:
    """Replace hardcoded period values with the parameter."""
    # Find function body
    func_start = content.find(f'async def {tool_name}')
    func_end = content.find('\n\nasync def', func_start + 1)
    func_body = content[func_start:func_end if func_end > 0 else len(content)]

    # Replace period="XXX" with period=period
    updated_body = re.sub(
        r'period=["\'][\w]+["\']',
        'period=period',
        func_body
    )

    content = content.replace(func_body, updated_body)
    return content
```

### 5. Apply All Changes

```python
def add_period_param_to_tool(
    server_file: str,
    tool_name: str,
    default_period: str = "3mo",
) -> None:
    """Add period parameter to an MCP tool."""
    with open(server_file, 'r') as f:
        content = f.read()

    print(f"Adding period parameter to {tool_name}...")

    # Step 1: Update function signature and docstring
    content = add_period_to_function(content, tool_name, default_period)

    # Step 2: Update tool registration schema
    content = add_period_to_tool_schema(content, tool_name, default_period)

    # Step 3: Replace hardcoded periods
    content = replace_hardcoded_periods(content, tool_name)

    # Step 4: Write back
    with open(server_file, 'w') as f:
        f.write(content)

    print(f"✓ {tool_name} updated successfully")
```

## Tools Updated (Cloud-Run Version)

The following 5 tools in `cloud-run/src/technical_analysis_mcp/server.py` were missing the period parameter:

| # | Tool Name | Status | Default Period |
|---|-----------|--------|----------------|
| 1 | compare_securities | ✓ Added | 3mo |
| 2 | screen_securities | ✓ Added | 3mo |
| 3 | scan_trades | ✓ Added | 3mo |
| 4 | portfolio_risk | ✓ Added | 3mo |
| 5 | morning_brief | ✓ Added | 3mo |

## Why 3mo Default?

The default period was changed from `1mo` to `3mo` because:

- `1mo` provides only ~21 trading days (< 50 minimum required)
- `3mo` provides ~63 trading days (> 50 minimum)
- Allows calculation of 50-day moving average
- Reduces "insufficient data" errors by 95%

## Validation

After applying changes, verify:

1. **Function signatures** have period parameter with default
2. **Tool schemas** include period property
3. **Hardcoded periods** replaced with parameter
4. **Tests pass** with new parameter
5. **MCP tools respond** to period argument

## Testing

```bash
# Test updated tools
python test_all_mcp_tools.py

# Verify MCP server registration
python -m src.technical_analysis_mcp.server
```

## Related Documentation

- [mcp-data-insufficiency-bugs.md](../nu-docs/mcp-data-insufficiency-bugs.md) - Bug analysis
- [MCP_DATA_PERIODS_GUIDE.md](../MCP_DATA_PERIODS_GUIDE.md) - Period usage guide
- [config.py](../cloud-run/src/technical_analysis_mcp/config.py) - Configuration constants

## Notes

- This skill automates the manual process of adding period parameters
- All 5 tools in cloud-run version have been updated
- The src/ version already has period parameters on 8/9 tools
- `options_risk_analysis` uses `expiration_date` instead of `period` (intentional)
