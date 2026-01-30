# MCP Centralized Configuration Guide

Three approaches to configure all 9 MCP tools from a single file.

---

## Overview

Currently, MCP tool configuration is spread across:
- `config.py` - Global constants
- `server.py` - Tool registrations with hardcoded defaults
- Individual tool functions - Default parameters

This guide presents **3 approaches** to centralize all configuration into a single source of truth.

---

## The 9 MCP Tools

| # | Tool Name | Configurable Parameters |
|---|-----------|------------------------|
| 1 | analyze_security | period, use_ai |
| 2 | compare_securities | period, metric, max_symbols |
| 3 | screen_securities | period, universe, limit |
| 4 | get_trade_plan | period |
| 5 | scan_trades | period, universe, max_results |
| 6 | portfolio_risk | period |
| 7 | morning_brief | period, market_region, watchlist |
| 8 | analyze_fibonacci | period, window |
| 9 | options_risk_analysis | expiration_date, option_type, min_volume |

---

## Approach 1: YAML Configuration File

**Best for**: Human-readable config, non-developers, quick edits

### Create `mcp_config.yaml`

```yaml
# mcp_config.yaml - Centralized MCP Tool Configuration
# =====================================================

# Global defaults applied to all tools
global:
  default_period: "3mo"
  cache_ttl_seconds: 300
  max_retry_attempts: 3
  use_ai: false

# Per-tool configuration
tools:
  analyze_security:
    enabled: true
    period: "3mo"
    use_ai: false
    description: "Run technical analysis on a single security"

  compare_securities:
    enabled: true
    period: "3mo"
    metric: "signals"
    max_symbols: 10
    description: "Compare multiple securities side-by-side"

  screen_securities:
    enabled: true
    period: "3mo"
    default_universe: "sp500"
    limit: 20
    description: "Screen securities matching criteria"

  get_trade_plan:
    enabled: true
    period: "3mo"
    max_plans: 3
    min_rr_ratio: 1.5
    description: "Generate risk-qualified trade plans"

  scan_trades:
    enabled: true
    period: "3mo"
    default_universe: "sp500"
    max_results: 10
    description: "Scan universe for trade setups"

  portfolio_risk:
    enabled: true
    period: "3mo"
    description: "Assess portfolio-level risk"

  morning_brief:
    enabled: true
    period: "3mo"
    market_region: "US"
    default_watchlist:
      - "AAPL"
      - "MSFT"
      - "GOOGL"
      - "TSLA"
      - "NVDA"
    description: "Generate daily market briefing"

  analyze_fibonacci:
    enabled: true
    period: "3mo"
    window: 50
    description: "Fibonacci retracement analysis"

  options_risk_analysis:
    enabled: true
    option_type: "both"
    min_volume: 10
    min_dte: 7
    max_dte: 45
    description: "Options chain risk analysis"

# Indicator settings
indicators:
  rsi:
    period: 14
    oversold: 30
    overbought: 70
  macd:
    fast: 12
    slow: 26
    signal: 9
  bollinger:
    period: 20
    std_dev: 2.0
  moving_averages:
    - 5
    - 10
    - 20
    - 50
    - 100
    - 200

# Risk thresholds
risk:
  min_rr_ratio: 1.5
  preferred_rr_ratio: 2.0
  max_conflicting_signals: 0.4
  min_volume_ratio: 0.5

# Universe definitions
universes:
  sp500:
    name: "S&P 500"
    source: "wikipedia"
  nasdaq100:
    name: "NASDAQ 100"
    source: "nasdaq"
  crypto:
    symbols:
      - "BTC-USD"
      - "ETH-USD"
      - "SOL-USD"
```

### Config Loader (`yaml_config.py`)

```python
"""YAML-based configuration loader for MCP tools."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass
class ToolConfig:
    """Configuration for a single MCP tool."""
    enabled: bool = True
    period: str = "3mo"
    description: str = ""
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class MCPConfig:
    """Centralized MCP configuration."""
    global_settings: dict[str, Any]
    tools: dict[str, ToolConfig]
    indicators: dict[str, Any]
    risk: dict[str, Any]
    universes: dict[str, Any]

    @classmethod
    def load(cls, config_path: str | Path = "mcp_config.yaml") -> "MCPConfig":
        """Load configuration from YAML file."""
        path = Path(config_path)
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {path}")

        with open(path) as f:
            data = yaml.safe_load(f)

        # Parse tool configs
        tools = {}
        for name, tool_data in data.get("tools", {}).items():
            tools[name] = ToolConfig(
                enabled=tool_data.get("enabled", True),
                period=tool_data.get("period", data["global"]["default_period"]),
                description=tool_data.get("description", ""),
                extra=tool_data,
            )

        return cls(
            global_settings=data.get("global", {}),
            tools=tools,
            indicators=data.get("indicators", {}),
            risk=data.get("risk", {}),
            universes=data.get("universes", {}),
        )

    def get_tool_config(self, tool_name: str) -> ToolConfig:
        """Get configuration for a specific tool."""
        return self.tools.get(tool_name, ToolConfig())

    def get_period(self, tool_name: str) -> str:
        """Get period for a tool, falling back to global default."""
        tool = self.tools.get(tool_name)
        if tool and tool.period:
            return tool.period
        return self.global_settings.get("default_period", "3mo")


# Global config instance (singleton)
_config: MCPConfig | None = None


def get_config() -> MCPConfig:
    """Get the global configuration instance."""
    global _config
    if _config is None:
        _config = MCPConfig.load()
    return _config


def reload_config(config_path: str | Path = "mcp_config.yaml") -> MCPConfig:
    """Reload configuration from file."""
    global _config
    _config = MCPConfig.load(config_path)
    return _config
```

### Usage in Server

```python
# server.py
from yaml_config import get_config

config = get_config()

async def analyze_security(
    symbol: str,
    period: str | None = None,
    use_ai: bool | None = None,
) -> dict[str, Any]:
    """Analyze security with YAML-configured defaults."""
    tool_config = config.get_tool_config("analyze_security")

    # Use provided values or fall back to config
    period = period or tool_config.period
    use_ai = use_ai if use_ai is not None else tool_config.extra.get("use_ai", False)

    # ... rest of implementation
```

### Pros & Cons

| Pros | Cons |
|------|------|
| Human-readable | No type validation |
| Easy to edit without code changes | Requires yaml package |
| Supports comments | No IDE autocomplete |
| Can be version controlled separately | Runtime errors on typos |

---

## Approach 2: Pydantic Settings

**Best for**: Type safety, validation, environment variable support

### Create `settings.py`

```python
"""Pydantic Settings for MCP Tools - Type-safe configuration."""

from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class ToolSettings(BaseSettings):
    """Base settings for all tools."""
    enabled: bool = True
    period: str = "3mo"

    @field_validator("period")
    @classmethod
    def validate_period(cls, v: str) -> str:
        valid = ("1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max")
        if v not in valid:
            raise ValueError(f"Invalid period: {v}. Must be one of {valid}")
        return v


class AnalyzeSecuritySettings(ToolSettings):
    """Settings for analyze_security tool."""
    model_config = SettingsConfigDict(env_prefix="MCP_ANALYZE_")

    use_ai: bool = False
    max_signals: int = Field(default=50, ge=1, le=200)


class CompareSecuritiesSettings(ToolSettings):
    """Settings for compare_securities tool."""
    model_config = SettingsConfigDict(env_prefix="MCP_COMPARE_")

    metric: Literal["signals", "score", "momentum"] = "signals"
    max_symbols: int = Field(default=10, ge=2, le=20)


class ScreenSecuritiesSettings(ToolSettings):
    """Settings for screen_securities tool."""
    model_config = SettingsConfigDict(env_prefix="MCP_SCREEN_")

    default_universe: str = "sp500"
    limit: int = Field(default=20, ge=1, le=100)


class GetTradePlanSettings(ToolSettings):
    """Settings for get_trade_plan tool."""
    model_config = SettingsConfigDict(env_prefix="MCP_TRADE_PLAN_")

    max_plans: int = Field(default=3, ge=1, le=5)
    min_rr_ratio: float = Field(default=1.5, ge=1.0)


class ScanTradesSettings(ToolSettings):
    """Settings for scan_trades tool."""
    model_config = SettingsConfigDict(env_prefix="MCP_SCAN_")

    default_universe: str = "sp500"
    max_results: int = Field(default=10, ge=1, le=50)


class PortfolioRiskSettings(ToolSettings):
    """Settings for portfolio_risk tool."""
    model_config = SettingsConfigDict(env_prefix="MCP_PORTFOLIO_")


class MorningBriefSettings(ToolSettings):
    """Settings for morning_brief tool."""
    model_config = SettingsConfigDict(env_prefix="MCP_BRIEF_")

    market_region: Literal["US", "EU", "ASIA"] = "US"
    default_watchlist: list[str] = Field(
        default=["AAPL", "MSFT", "GOOGL", "TSLA", "NVDA"]
    )


class AnalyzeFibonacciSettings(ToolSettings):
    """Settings for analyze_fibonacci tool."""
    model_config = SettingsConfigDict(env_prefix="MCP_FIBONACCI_")

    window: int = Field(default=50, ge=10, le=200)


class OptionsRiskSettings(BaseSettings):
    """Settings for options_risk_analysis tool."""
    model_config = SettingsConfigDict(env_prefix="MCP_OPTIONS_")

    enabled: bool = True
    option_type: Literal["calls", "puts", "both"] = "both"
    min_volume: int = Field(default=10, ge=1)
    min_dte: int = Field(default=7, ge=0)
    max_dte: int = Field(default=45, ge=1)


class IndicatorSettings(BaseSettings):
    """Settings for technical indicators."""
    model_config = SettingsConfigDict(env_prefix="MCP_INDICATOR_")

    rsi_period: int = 14
    rsi_oversold: float = 30.0
    rsi_overbought: float = 70.0
    macd_fast: int = 12
    macd_slow: int = 26
    macd_signal: int = 9
    bollinger_period: int = 20
    bollinger_std: float = 2.0
    ma_periods: tuple[int, ...] = (5, 10, 20, 50, 100, 200)


class RiskSettings(BaseSettings):
    """Settings for risk assessment."""
    model_config = SettingsConfigDict(env_prefix="MCP_RISK_")

    min_rr_ratio: float = 1.5
    preferred_rr_ratio: float = 2.0
    max_conflicting_signals: float = 0.4
    min_volume_ratio: float = 0.5
    volatility_low: float = 1.5
    volatility_high: float = 3.0


class MCPSettings(BaseSettings):
    """Master settings combining all tool configurations."""
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="MCP_",
        extra="ignore",
    )

    # Global settings
    default_period: str = "3mo"
    cache_ttl: int = 300
    max_retries: int = 3
    gemini_api_key: str | None = None

    # Tool-specific settings (nested)
    analyze_security: AnalyzeSecuritySettings = Field(default_factory=AnalyzeSecuritySettings)
    compare_securities: CompareSecuritiesSettings = Field(default_factory=CompareSecuritiesSettings)
    screen_securities: ScreenSecuritiesSettings = Field(default_factory=ScreenSecuritiesSettings)
    get_trade_plan: GetTradePlanSettings = Field(default_factory=GetTradePlanSettings)
    scan_trades: ScanTradesSettings = Field(default_factory=ScanTradesSettings)
    portfolio_risk: PortfolioRiskSettings = Field(default_factory=PortfolioRiskSettings)
    morning_brief: MorningBriefSettings = Field(default_factory=MorningBriefSettings)
    analyze_fibonacci: AnalyzeFibonacciSettings = Field(default_factory=AnalyzeFibonacciSettings)
    options_risk: OptionsRiskSettings = Field(default_factory=OptionsRiskSettings)

    # Shared settings
    indicators: IndicatorSettings = Field(default_factory=IndicatorSettings)
    risk: RiskSettings = Field(default_factory=RiskSettings)


@lru_cache
def get_settings() -> MCPSettings:
    """Get cached settings instance."""
    return MCPSettings()


def reload_settings() -> MCPSettings:
    """Clear cache and reload settings."""
    get_settings.cache_clear()
    return get_settings()
```

### Environment File (`.env`)

```bash
# .env - MCP Tool Configuration via Environment Variables
# ========================================================

# Global Settings
MCP_DEFAULT_PERIOD=3mo
MCP_CACHE_TTL=300
MCP_MAX_RETRIES=3
MCP_GEMINI_API_KEY=your-api-key-here

# analyze_security
MCP_ANALYZE_PERIOD=3mo
MCP_ANALYZE_USE_AI=false
MCP_ANALYZE_MAX_SIGNALS=50

# compare_securities
MCP_COMPARE_PERIOD=3mo
MCP_COMPARE_METRIC=signals
MCP_COMPARE_MAX_SYMBOLS=10

# screen_securities
MCP_SCREEN_PERIOD=3mo
MCP_SCREEN_DEFAULT_UNIVERSE=sp500
MCP_SCREEN_LIMIT=20

# get_trade_plan
MCP_TRADE_PLAN_PERIOD=3mo
MCP_TRADE_PLAN_MAX_PLANS=3
MCP_TRADE_PLAN_MIN_RR_RATIO=1.5

# scan_trades
MCP_SCAN_PERIOD=3mo
MCP_SCAN_DEFAULT_UNIVERSE=sp500
MCP_SCAN_MAX_RESULTS=10

# portfolio_risk
MCP_PORTFOLIO_PERIOD=6mo

# morning_brief
MCP_BRIEF_PERIOD=3mo
MCP_BRIEF_MARKET_REGION=US

# analyze_fibonacci
MCP_FIBONACCI_PERIOD=3mo
MCP_FIBONACCI_WINDOW=50

# options_risk_analysis
MCP_OPTIONS_OPTION_TYPE=both
MCP_OPTIONS_MIN_VOLUME=10
MCP_OPTIONS_MIN_DTE=7
MCP_OPTIONS_MAX_DTE=45

# Indicator Settings
MCP_INDICATOR_RSI_PERIOD=14
MCP_INDICATOR_RSI_OVERSOLD=30
MCP_INDICATOR_RSI_OVERBOUGHT=70

# Risk Settings
MCP_RISK_MIN_RR_RATIO=1.5
MCP_RISK_MIN_VOLUME_RATIO=0.5
```

### Usage in Server

```python
# server.py
from settings import get_settings

settings = get_settings()

async def analyze_security(
    symbol: str,
    period: str | None = None,
    use_ai: bool | None = None,
) -> dict[str, Any]:
    """Analyze security with Pydantic-validated settings."""
    tool_settings = settings.analyze_security

    # Use provided values or fall back to settings
    period = period or tool_settings.period
    use_ai = use_ai if use_ai is not None else tool_settings.use_ai

    # Validation already done by Pydantic!
    # ... rest of implementation
```

### Pros & Cons

| Pros | Cons |
|------|------|
| Full type safety | More complex setup |
| Validation at startup | Requires pydantic-settings |
| IDE autocomplete | Nested env vars can be verbose |
| Environment variable support | Learning curve |
| Fails fast on invalid config | |

---

## Approach 3: Tool Registry Pattern

**Best for**: Programmatic control, dependency injection, testing

### Create `tool_registry.py`

```python
"""Tool Registry Pattern for MCP Configuration."""

from dataclasses import dataclass, field
from typing import Any, Callable, Awaitable
from enum import Enum


class ToolStatus(Enum):
    """Tool availability status."""
    ENABLED = "enabled"
    DISABLED = "disabled"
    MAINTENANCE = "maintenance"


@dataclass
class ToolDefinition:
    """Complete definition of an MCP tool."""
    name: str
    handler: Callable[..., Awaitable[dict[str, Any]]]
    description: str
    status: ToolStatus = ToolStatus.ENABLED

    # Default parameters
    defaults: dict[str, Any] = field(default_factory=dict)

    # Parameter constraints
    constraints: dict[str, dict[str, Any]] = field(default_factory=dict)

    # Input schema for MCP registration
    input_schema: dict[str, Any] = field(default_factory=dict)

    def get_default(self, param: str, fallback: Any = None) -> Any:
        """Get default value for a parameter."""
        return self.defaults.get(param, fallback)

    def validate_param(self, param: str, value: Any) -> bool:
        """Validate a parameter against constraints."""
        if param not in self.constraints:
            return True

        constraint = self.constraints[param]

        if "choices" in constraint and value not in constraint["choices"]:
            return False
        if "min" in constraint and value < constraint["min"]:
            return False
        if "max" in constraint and value > constraint["max"]:
            return False

        return True


class ToolRegistry:
    """Central registry for all MCP tools."""

    def __init__(self):
        self._tools: dict[str, ToolDefinition] = {}
        self._global_defaults: dict[str, Any] = {
            "period": "3mo",
            "use_ai": False,
        }

    def register(self, tool: ToolDefinition) -> None:
        """Register a tool with the registry."""
        self._tools[tool.name] = tool

    def get(self, name: str) -> ToolDefinition | None:
        """Get a tool by name."""
        return self._tools.get(name)

    def all_tools(self) -> list[ToolDefinition]:
        """Get all registered tools."""
        return list(self._tools.values())

    def enabled_tools(self) -> list[ToolDefinition]:
        """Get only enabled tools."""
        return [t for t in self._tools.values() if t.status == ToolStatus.ENABLED]

    def set_global_default(self, param: str, value: Any) -> None:
        """Set a global default that applies to all tools."""
        self._global_defaults[param] = value

    def get_effective_default(self, tool_name: str, param: str) -> Any:
        """Get effective default (tool-specific or global)."""
        tool = self._tools.get(tool_name)
        if tool and param in tool.defaults:
            return tool.defaults[param]
        return self._global_defaults.get(param)

    def configure_tool(self, name: str, **kwargs) -> None:
        """Configure a tool's defaults."""
        tool = self._tools.get(name)
        if tool:
            tool.defaults.update(kwargs)

    def configure_all(self, **kwargs) -> None:
        """Configure all tools with the same settings."""
        for tool in self._tools.values():
            tool.defaults.update(kwargs)

    def disable_tool(self, name: str) -> None:
        """Disable a tool."""
        tool = self._tools.get(name)
        if tool:
            tool.status = ToolStatus.DISABLED

    def enable_tool(self, name: str) -> None:
        """Enable a tool."""
        tool = self._tools.get(name)
        if tool:
            tool.status = ToolStatus.ENABLED

    def to_mcp_tools(self) -> list[dict[str, Any]]:
        """Convert registry to MCP tool list format."""
        from mcp.types import Tool

        return [
            Tool(
                name=t.name,
                description=t.description,
                inputSchema=t.input_schema,
            )
            for t in self.enabled_tools()
        ]

    def load_from_dict(self, config: dict[str, Any]) -> None:
        """Load configuration from a dictionary."""
        # Global defaults
        if "global" in config:
            self._global_defaults.update(config["global"])

        # Per-tool configuration
        if "tools" in config:
            for name, tool_config in config["tools"].items():
                if name in self._tools:
                    self._tools[name].defaults.update(tool_config)
                    if "enabled" in tool_config:
                        self._tools[name].status = (
                            ToolStatus.ENABLED if tool_config["enabled"]
                            else ToolStatus.DISABLED
                        )

    def load_from_yaml(self, path: str) -> None:
        """Load configuration from YAML file."""
        import yaml
        with open(path) as f:
            config = yaml.safe_load(f)
        self.load_from_dict(config)

    def load_from_env(self) -> None:
        """Load configuration from environment variables."""
        import os

        # Global defaults
        if period := os.getenv("MCP_DEFAULT_PERIOD"):
            self._global_defaults["period"] = period

        # Per-tool from env (MCP_TOOLNAME_PARAM format)
        for tool in self._tools.values():
            prefix = f"MCP_{tool.name.upper()}_"
            for key, value in os.environ.items():
                if key.startswith(prefix):
                    param = key[len(prefix):].lower()
                    tool.defaults[param] = value


# Global registry instance
registry = ToolRegistry()


def create_registry() -> ToolRegistry:
    """Create and populate the tool registry."""
    from server import (
        analyze_security,
        compare_securities,
        screen_securities,
        get_trade_plan,
        scan_trades,
        portfolio_risk,
        morning_brief,
        analyze_fibonacci,
        options_risk_analysis,
    )

    r = ToolRegistry()

    # Register all 9 tools
    r.register(ToolDefinition(
        name="analyze_security",
        handler=analyze_security,
        description="Run technical analysis on a single security",
        defaults={"period": "3mo", "use_ai": False},
        constraints={
            "period": {"choices": ["1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y"]},
        },
        input_schema={
            "type": "object",
            "properties": {
                "symbol": {"type": "string", "description": "Ticker symbol"},
                "period": {"type": "string", "default": "3mo"},
                "use_ai": {"type": "boolean", "default": False},
            },
            "required": ["symbol"],
        },
    ))

    r.register(ToolDefinition(
        name="compare_securities",
        handler=compare_securities,
        description="Compare multiple securities",
        defaults={"period": "3mo", "metric": "signals", "max_symbols": 10},
        input_schema={
            "type": "object",
            "properties": {
                "symbols": {"type": "array", "items": {"type": "string"}},
                "period": {"type": "string", "default": "3mo"},
                "metric": {"type": "string", "default": "signals"},
            },
            "required": ["symbols"],
        },
    ))

    # ... register remaining 7 tools similarly

    return r
```

### Configuration File (`mcp_tools.py`)

```python
"""MCP Tools Configuration - Single file to configure all 9 tools."""

from tool_registry import registry, ToolStatus

# ============================================================================
# GLOBAL CONFIGURATION
# ============================================================================

registry.set_global_default("period", "3mo")
registry.set_global_default("use_ai", False)

# ============================================================================
# TOOL-SPECIFIC CONFIGURATION
# ============================================================================

# 1. analyze_security
registry.configure_tool("analyze_security",
    period="3mo",
    use_ai=False,
    max_signals=50,
)

# 2. compare_securities
registry.configure_tool("compare_securities",
    period="3mo",
    metric="signals",
    max_symbols=10,
)

# 3. screen_securities
registry.configure_tool("screen_securities",
    period="3mo",
    default_universe="sp500",
    limit=20,
)

# 4. get_trade_plan
registry.configure_tool("get_trade_plan",
    period="3mo",
    max_plans=3,
    min_rr_ratio=1.5,
)

# 5. scan_trades
registry.configure_tool("scan_trades",
    period="3mo",
    default_universe="sp500",
    max_results=10,
)

# 6. portfolio_risk
registry.configure_tool("portfolio_risk",
    period="6mo",  # Longer period for portfolio analysis
)

# 7. morning_brief
registry.configure_tool("morning_brief",
    period="3mo",
    market_region="US",
    default_watchlist=["AAPL", "MSFT", "GOOGL", "TSLA", "NVDA"],
)

# 8. analyze_fibonacci
registry.configure_tool("analyze_fibonacci",
    period="3mo",
    window=50,
)

# 9. options_risk_analysis
registry.configure_tool("options_risk_analysis",
    option_type="both",
    min_volume=10,
    min_dte=7,
    max_dte=45,
)

# ============================================================================
# DISABLE TOOLS (if needed)
# ============================================================================

# registry.disable_tool("options_risk_analysis")  # Uncomment to disable

# ============================================================================
# LOAD OVERRIDES FROM ENVIRONMENT
# ============================================================================

registry.load_from_env()
```

### Usage in Server

```python
# server.py
from tool_registry import registry

@app.list_tools()
async def list_tools() -> list[Tool]:
    """List all enabled tools from registry."""
    return registry.to_mcp_tools()

@app.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """Route tool calls through registry."""
    tool = registry.get(name)

    if not tool:
        raise ValueError(f"Unknown tool: {name}")

    if tool.status != ToolStatus.ENABLED:
        raise ValueError(f"Tool {name} is currently {tool.status.value}")

    # Apply defaults for missing arguments
    for param, default in tool.defaults.items():
        if param not in arguments:
            arguments[param] = default

    # Validate parameters
    for param, value in arguments.items():
        if not tool.validate_param(param, value):
            raise ValueError(f"Invalid value for {param}: {value}")

    # Call the handler
    result = await tool.handler(**arguments)
    return [TextContent(type="text", text=format_result(result))]
```

### Pros & Cons

| Pros | Cons |
|------|------|
| Full programmatic control | More code to write |
| Easy testing (mock registry) | Steeper learning curve |
| Dependency injection ready | Requires architectural changes |
| Runtime tool management | May be overkill for simple apps |
| Enable/disable tools dynamically | |

---

## Comparison Summary

| Feature | YAML | Pydantic | Registry |
|---------|------|----------|----------|
| **Ease of setup** | Easy | Medium | Complex |
| **Type safety** | None | Full | Partial |
| **Validation** | Manual | Automatic | Custom |
| **IDE support** | None | Full | Partial |
| **Env var support** | Manual | Built-in | Custom |
| **Hot reload** | Yes | Yes | Yes |
| **Testing** | Easy | Easy | Best |
| **Dynamic changes** | Limited | Limited | Full |
| **Best for** | Non-devs | Production | Enterprise |

---

## Recommendation

| Scenario | Recommended Approach |
|----------|---------------------|
| Quick setup, simple needs | **YAML** |
| Production with validation | **Pydantic Settings** |
| Complex enterprise app | **Tool Registry** |
| Team with mixed skill levels | **YAML + Pydantic hybrid** |

### Hybrid Approach

For the best of all worlds, combine approaches:

```python
"""Hybrid configuration: YAML + Pydantic validation."""

from pathlib import Path
import yaml
from pydantic import BaseModel, ValidationError


class ToolConfig(BaseModel):
    """Validated tool configuration."""
    enabled: bool = True
    period: str = "3mo"

    class Config:
        extra = "allow"


def load_validated_config(path: str = "mcp_config.yaml") -> dict[str, ToolConfig]:
    """Load YAML and validate with Pydantic."""
    with open(path) as f:
        raw = yaml.safe_load(f)

    validated = {}
    for name, data in raw.get("tools", {}).items():
        try:
            validated[name] = ToolConfig(**data)
        except ValidationError as e:
            raise ValueError(f"Invalid config for {name}: {e}")

    return validated
```

---

## Files to Create

| Approach | Files |
|----------|-------|
| **YAML** | `mcp_config.yaml`, `yaml_config.py` |
| **Pydantic** | `settings.py`, `.env` |
| **Registry** | `tool_registry.py`, `mcp_tools.py` |

Choose one approach based on your team's needs and implement accordingly!
