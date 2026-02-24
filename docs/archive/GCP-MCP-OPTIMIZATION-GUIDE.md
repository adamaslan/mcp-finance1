# GCP & MCP Optimization Guide

A comprehensive guide for optimizing this technical analysis repository for Google Cloud Platform and integrating with other MCP (Model Context Protocol) servers.

---

## Table of Contents

1. [GCP Optimization](#gcp-optimization)
   - [Cost Optimization](#cost-optimization)
   - [Performance Optimization](#performance-optimization)
   - [Scaling Strategies](#scaling-strategies)
   - [Security Hardening](#security-hardening)
2. [MCP Integration](#mcp-integration)
   - [Connecting to Other MCP Servers](#connecting-to-other-mcp-servers)
   - [Building Composite MCP Workflows](#building-composite-mcp-workflows)
   - [MCP Best Practices](#mcp-best-practices)
3. [Advanced Configurations](#advanced-configurations)
4. [Monitoring & Observability](#monitoring--observability)
5. [Deployment](#deployment)
   - [Docker Configuration](#docker-configuration)
   - [CI/CD Pipeline](#cicd-pipeline)
   - [Testing Setup](#testing-setup)
   - [Deployment Scripts](#deployment-scripts)
6. [Additional MCP Server Examples](#additional-mcp-server-examples)
7. [Troubleshooting Guide](#troubleshooting-guide)

---

## GCP Optimization

### Cost Optimization

#### 1. Stay Within Free Tier Limits

| Service | Free Tier Limit | Current Usage | Optimization |
|---------|-----------------|---------------|--------------|
| Cloud Run | 2M requests/month | Variable | Scale to zero when idle |
| Firestore | 1GB storage, 50K reads/day | Low | Use TTL for cache cleanup |
| Cloud Storage | 5GB | Low | Enable lifecycle policies |
| Pub/Sub | 10GB/month | Low | Batch messages |
| Cloud Functions | 2M invocations/month | Variable | Optimize cold starts |

#### 2. Implement Aggressive Caching

```python
# config.py - Optimize cache settings
CACHE_TTL_SECONDS: Final[int] = 600  # Increase to 10 minutes (was 5)
CACHE_MAX_SIZE: Final[int] = 200  # Double cache size (was 100)

# Multi-tier caching strategy
CACHE_TIERS = {
    "hot": 300,      # 5 min - frequently accessed symbols
    "warm": 1800,    # 30 min - popular ETFs
    "cold": 3600,    # 1 hour - less frequently accessed
}
```

#### 3. Firestore Document Structure

Optimize Firestore for fewer reads:

```python
# Before: Multiple documents per symbol
signals/{symbol}           # 1 read
analysis/{symbol}/history  # N reads

# After: Denormalized structure
analysis/{symbol}  # Single read contains:
  - current_signals
  - indicators
  - last_7_days_history (embedded)
  - metadata
```

#### 4. Cloud Run Configuration

```yaml
# Optimal Cloud Run settings for cost
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: technical-analysis-api
spec:
  template:
    metadata:
      annotations:
        autoscaling.knative.dev/minScale: "0"      # Scale to zero
        autoscaling.knative.dev/maxScale: "3"      # Limit max instances
        run.googleapis.com/cpu-throttling: "true"  # Reduce CPU when idle
        run.googleapis.com/startup-cpu-boost: "true"  # Fast cold starts
    spec:
      containerConcurrency: 80  # Handle more requests per instance
      timeoutSeconds: 300
      containers:
        - image: gcr.io/$PROJECT_ID/technical-analysis-api
          resources:
            limits:
              cpu: "1"
              memory: "512Mi"  # Minimum needed for pandas
```

#### 5. Use Cloud Scheduler Efficiently

```terraform
# Consolidate scheduled jobs
resource "google_cloud_scheduler_job" "market_analysis" {
  name     = "market-analysis-batch"
  schedule = "0 17 * * 1-5"  # Once at market close

  # Batch multiple analyses into one job
  pubsub_target {
    data = base64encode(jsonencode({
      type = "batch_analysis"
      batches = [
        { type = "major_indices", symbols = ["SPY", "QQQ", "DIA", "IWM"] },
        { type = "sector_etfs", symbols = ["XLF", "XLK", "XLE", "XLV"] },
        { type = "watchlist", symbols = ["AAPL", "MSFT", "GOOGL"] }
      ]
    }))
  }
}
```

---

### Performance Optimization

#### 1. Parallel Data Fetching

```python
# data.py - Add parallel fetching
import asyncio
from concurrent.futures import ThreadPoolExecutor

class ParallelDataFetcher(DataFetcher):
    def __init__(self, max_workers: int = 5):
        self._executor = ThreadPoolExecutor(max_workers=max_workers)

    async def fetch_multiple(
        self,
        symbols: list[str],
        period: str = "1mo"
    ) -> dict[str, pd.DataFrame]:
        """Fetch multiple symbols in parallel."""
        loop = asyncio.get_event_loop()

        tasks = [
            loop.run_in_executor(
                self._executor,
                self._fetch_single,
                symbol,
                period
            )
            for symbol in symbols
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        return {
            symbol: result
            for symbol, result in zip(symbols, results)
            if not isinstance(result, Exception)
        }
```

#### 2. Optimize Indicator Calculations

```python
# indicators.py - Vectorized calculations
import numba
from numba import jit

@jit(nopython=True, cache=True)
def calculate_rsi_fast(prices: np.ndarray, period: int = 14) -> np.ndarray:
    """Numba-optimized RSI calculation."""
    deltas = np.diff(prices)
    gains = np.where(deltas > 0, deltas, 0.0)
    losses = np.where(deltas < 0, -deltas, 0.0)

    avg_gain = np.zeros(len(prices))
    avg_loss = np.zeros(len(prices))

    # Initial averages
    avg_gain[period] = np.mean(gains[:period])
    avg_loss[period] = np.mean(losses[:period])

    # Smoothed averages
    for i in range(period + 1, len(prices)):
        avg_gain[i] = (avg_gain[i-1] * (period-1) + gains[i-1]) / period
        avg_loss[i] = (avg_loss[i-1] * (period-1) + losses[i-1]) / period

    rs = avg_gain / (avg_loss + 1e-10)
    return 100 - (100 / (1 + rs))
```

#### 3. Lazy Loading for Signals

```python
# signals.py - Only calculate needed signals
class LazySignalDetector:
    """Lazy evaluation - only compute requested signal categories."""

    def __init__(self, df: pd.DataFrame):
        self._df = df
        self._cache: dict[str, list[Signal]] = {}

    def get_signals(
        self,
        categories: list[SignalCategory] | None = None
    ) -> list[Signal]:
        """Get signals for specific categories only."""
        if categories is None:
            categories = list(SignalCategory)

        signals = []
        for category in categories:
            if category not in self._cache:
                self._cache[category] = self._detect_category(category)
            signals.extend(self._cache[category])

        return signals

    def _detect_category(self, category: SignalCategory) -> list[Signal]:
        """Detect signals for a single category."""
        detectors = {
            SignalCategory.RSI: self._detect_rsi_signals,
            SignalCategory.MACD: self._detect_macd_signals,
            SignalCategory.MA_CROSS: self._detect_ma_cross_signals,
            # ... other detectors
        }
        return detectors.get(category, lambda: [])()
```

#### 4. Connection Pooling

```python
# cloud-run/main.py - Add connection pooling
from google.cloud import firestore
from google.cloud.firestore_v1 import AsyncClient

# Use async client with connection pooling
class FirestorePool:
    _instance: AsyncClient | None = None

    @classmethod
    def get_client(cls) -> AsyncClient:
        if cls._instance is None:
            cls._instance = AsyncClient(
                project=PROJECT_ID,
                # Connection pool settings
                client_options={
                    "api_endpoint": "firestore.googleapis.com",
                }
            )
        return cls._instance
```

---

### Scaling Strategies

#### 1. Horizontal Scaling with Cloud Functions

```python
# functions/parallel_screener.py
import functions_framework
from google.cloud import pubsub_v1
import json

@functions_framework.cloud_event
def parallel_screen(cloud_event):
    """Process screening in parallel batches."""
    data = json.loads(cloud_event.data["message"]["data"])
    symbols = data["symbols"]

    # Split into batches of 10
    batch_size = 10
    batches = [symbols[i:i+batch_size] for i in range(0, len(symbols), batch_size)]

    publisher = pubsub_v1.PublisherClient()
    topic = publisher.topic_path(PROJECT_ID, "screen-batch")

    for batch in batches:
        publisher.publish(topic, json.dumps({"symbols": batch}).encode())

    return f"Dispatched {len(batches)} batches"
```

#### 2. Regional Deployment

```terraform
# Deploy to multiple regions for lower latency
variable "regions" {
  default = ["us-central1", "us-east1", "europe-west1"]
}

resource "google_cloud_run_service" "api" {
  for_each = toset(var.regions)

  name     = "technical-analysis-api"
  location = each.value

  # ... rest of configuration
}

# Global load balancer
resource "google_compute_global_address" "default" {
  name = "technical-analysis-lb"
}
```

---

### Security Hardening

#### 1. API Authentication

```python
# cloud-run/auth.py
from fastapi import Depends, HTTPException, Security
from fastapi.security import APIKeyHeader
import hashlib
import os

API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)
VALID_API_KEYS = set(os.getenv("API_KEYS", "").split(","))

async def verify_api_key(api_key: str = Security(API_KEY_HEADER)):
    """Verify API key for protected endpoints."""
    if not api_key:
        raise HTTPException(status_code=401, detail="API key required")

    # Hash comparison to prevent timing attacks
    key_hash = hashlib.sha256(api_key.encode()).hexdigest()
    valid_hashes = {hashlib.sha256(k.encode()).hexdigest() for k in VALID_API_KEYS}

    if key_hash not in valid_hashes:
        raise HTTPException(status_code=403, detail="Invalid API key")

    return api_key

# Usage in endpoints
@app.post("/api/admin/clear-cache")
async def clear_cache(
    collection: str = Query("signals"),
    api_key: str = Depends(verify_api_key)
):
    # Protected endpoint
    ...
```

#### 2. Rate Limiting

```python
# cloud-run/ratelimit.py
from fastapi import Request
from collections import defaultdict
from datetime import datetime, timedelta
import asyncio

class RateLimiter:
    def __init__(self, requests_per_minute: int = 60):
        self.rpm = requests_per_minute
        self.requests: dict[str, list[datetime]] = defaultdict(list)
        self._lock = asyncio.Lock()

    async def check(self, client_ip: str) -> bool:
        """Check if request is allowed."""
        async with self._lock:
            now = datetime.now()
            cutoff = now - timedelta(minutes=1)

            # Clean old requests
            self.requests[client_ip] = [
                t for t in self.requests[client_ip] if t > cutoff
            ]

            if len(self.requests[client_ip]) >= self.rpm:
                return False

            self.requests[client_ip].append(now)
            return True

rate_limiter = RateLimiter(requests_per_minute=100)

@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    client_ip = request.client.host

    if not await rate_limiter.check(client_ip):
        return JSONResponse(
            status_code=429,
            content={"error": "Rate limit exceeded"}
        )

    return await call_next(request)
```

#### 3. Secret Management

```python
# Use Secret Manager instead of environment variables
from google.cloud import secretmanager

def get_secret(secret_id: str, version: str = "latest") -> str:
    """Fetch secret from GCP Secret Manager."""
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{PROJECT_ID}/secrets/{secret_id}/versions/{version}"
    response = client.access_secret_version(request={"name": name})
    return response.payload.data.decode("UTF-8")

# Usage
GEMINI_API_KEY = get_secret("gemini-api-key")
```

---

## MCP Integration

### Connecting to Other MCP Servers

#### 1. MCP Server Discovery Configuration

Create a unified Claude Desktop configuration that combines multiple MCP servers:

```json
{
  "mcpServers": {
    "technical-analysis": {
      "command": "python",
      "args": ["-m", "technical_analysis_mcp.server"],
      "env": {
        "GEMINI_API_KEY": "${GEMINI_API_KEY}"
      }
    },
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/Users/you/data"]
    },
    "postgres": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-postgres"],
      "env": {
        "POSTGRES_CONNECTION_STRING": "${POSTGRES_URL}"
      }
    },
    "brave-search": {
      "command": "npx",
      "args": ["-y", "@anthropic/mcp-server-brave-search"],
      "env": {
        "BRAVE_API_KEY": "${BRAVE_API_KEY}"
      }
    },
    "slack": {
      "command": "npx",
      "args": ["-y", "@anthropic/mcp-server-slack"],
      "env": {
        "SLACK_BOT_TOKEN": "${SLACK_BOT_TOKEN}"
      }
    }
  }
}
```

#### 2. Common MCP Servers to Integrate

| MCP Server | Use Case | Integration Benefit |
|------------|----------|---------------------|
| `@modelcontextprotocol/server-filesystem` | Read/write analysis reports | Save results to files |
| `@modelcontextprotocol/server-postgres` | Store historical data | Persistent analysis storage |
| `@anthropic/mcp-server-brave-search` | Market news search | Combine with technical signals |
| `@anthropic/mcp-server-slack` | Send alerts | Notify on signal triggers |
| `@modelcontextprotocol/server-github` | Version control | Track analysis changes |
| `@modelcontextprotocol/server-sqlite` | Local database | Lightweight storage |

#### 3. Building a Composite MCP Workflow

Example: Technical Analysis + News + Slack Alerts

```python
# composite_workflow.py
"""
Example workflow combining multiple MCP servers.
Run this as a standalone script that orchestrates MCP tools.
"""

from dataclasses import dataclass
from typing import Any

@dataclass
class WorkflowStep:
    server: str
    tool: str
    args: dict[str, Any]

class CompositeWorkflow:
    """Orchestrate multiple MCP server calls."""

    async def morning_analysis(self, symbols: list[str]) -> dict:
        """Complete morning analysis workflow."""
        results = {}

        # Step 1: Technical Analysis
        for symbol in symbols:
            analysis = await self.call_mcp(
                server="technical-analysis",
                tool="analyze_security",
                args={"symbol": symbol, "use_ai": True}
            )
            results[symbol] = analysis

        # Step 2: Search for recent news
        news = await self.call_mcp(
            server="brave-search",
            tool="brave_web_search",
            args={"query": f"{' OR '.join(symbols)} stock market news today"}
        )
        results["news"] = news

        # Step 3: Save report to filesystem
        await self.call_mcp(
            server="filesystem",
            tool="write_file",
            args={
                "path": f"/reports/morning_{datetime.now().strftime('%Y%m%d')}.json",
                "content": json.dumps(results, indent=2)
            }
        )

        # Step 4: Send Slack alert for strong signals
        strong_signals = self._extract_strong_signals(results)
        if strong_signals:
            await self.call_mcp(
                server="slack",
                tool="send_message",
                args={
                    "channel": "#trading-alerts",
                    "text": self._format_alert(strong_signals)
                }
            )

        return results

    async def call_mcp(self, server: str, tool: str, args: dict) -> Any:
        """Call an MCP server tool (stub - actual implementation varies)."""
        # In practice, this would use MCP client SDK
        pass
```

---

### Building Composite MCP Workflows

#### 1. Database Integration Pattern

```python
# Add PostgreSQL storage for historical analysis
from typing import Protocol

class AnalysisStorage(Protocol):
    """Protocol for analysis storage backends."""

    async def save_analysis(self, symbol: str, analysis: dict) -> None: ...
    async def get_history(self, symbol: str, days: int) -> list[dict]: ...

class PostgresStorage:
    """PostgreSQL storage via MCP server."""

    async def save_analysis(self, symbol: str, analysis: dict) -> None:
        """Save analysis to PostgreSQL via MCP."""
        # This would call the postgres MCP server
        await mcp_call(
            server="postgres",
            tool="query",
            args={
                "sql": """
                    INSERT INTO analyses (symbol, timestamp, data)
                    VALUES ($1, $2, $3)
                    ON CONFLICT (symbol, timestamp)
                    DO UPDATE SET data = $3
                """,
                "params": [symbol, analysis["timestamp"], json.dumps(analysis)]
            }
        )

    async def get_history(self, symbol: str, days: int) -> list[dict]:
        """Get historical analyses from PostgreSQL."""
        result = await mcp_call(
            server="postgres",
            tool="query",
            args={
                "sql": """
                    SELECT data FROM analyses
                    WHERE symbol = $1
                    AND timestamp > NOW() - INTERVAL '$2 days'
                    ORDER BY timestamp DESC
                """,
                "params": [symbol, days]
            }
        )
        return [json.loads(row["data"]) for row in result]
```

#### 2. Filesystem Export Pattern

```python
# Add filesystem export capabilities
class ReportExporter:
    """Export reports via filesystem MCP server."""

    async def export_analysis(
        self,
        analysis: dict,
        format: str = "json"
    ) -> str:
        """Export analysis to file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        symbol = analysis["symbol"]

        if format == "json":
            content = json.dumps(analysis, indent=2)
            filename = f"analysis_{symbol}_{timestamp}.json"
        elif format == "csv":
            content = self._to_csv(analysis)
            filename = f"analysis_{symbol}_{timestamp}.csv"
        elif format == "markdown":
            content = self._to_markdown(analysis)
            filename = f"analysis_{symbol}_{timestamp}.md"

        path = f"/reports/{filename}"

        await mcp_call(
            server="filesystem",
            tool="write_file",
            args={"path": path, "content": content}
        )

        return path

    def _to_markdown(self, analysis: dict) -> str:
        """Convert analysis to markdown report."""
        return f"""# Technical Analysis: {analysis['symbol']}

**Generated:** {analysis['timestamp']}
**Price:** ${analysis['price']:.2f} ({analysis['change']:+.2f}%)

## Summary
- Total Signals: {analysis['summary']['total_signals']}
- Bullish: {analysis['summary']['bullish']}
- Bearish: {analysis['summary']['bearish']}
- Average Score: {analysis['summary']['avg_score']:.1f}

## Top Signals
{self._format_signals_md(analysis['signals'][:10])}

## Key Indicators
| Indicator | Value |
|-----------|-------|
| RSI | {analysis['indicators']['rsi']:.1f} |
| MACD | {analysis['indicators']['macd']:.4f} |
| ADX | {analysis['indicators']['adx']:.1f} |
"""
```

#### 3. Alert Integration Pattern

```python
# Slack/Discord alert integration
class AlertManager:
    """Send alerts via messaging MCP servers."""

    SIGNAL_THRESHOLDS = {
        "urgent": 90,    # Immediate alert
        "important": 75,  # Daily digest
        "notable": 60,    # Weekly summary
    }

    async def check_and_alert(self, analysis: dict) -> None:
        """Check analysis for alertable conditions."""
        alerts = []

        # Check for high-scoring signals
        for signal in analysis["signals"]:
            score = signal.get("ai_score", 0)

            if score >= self.SIGNAL_THRESHOLDS["urgent"]:
                alerts.append({
                    "priority": "urgent",
                    "symbol": analysis["symbol"],
                    "signal": signal["signal"],
                    "score": score
                })

        # Check for extreme RSI
        rsi = analysis["indicators"]["rsi"]
        if rsi < 20 or rsi > 80:
            alerts.append({
                "priority": "urgent",
                "symbol": analysis["symbol"],
                "signal": f"Extreme RSI: {rsi:.1f}",
                "score": 85
            })

        # Send alerts
        for alert in alerts:
            await self._send_alert(alert)

    async def _send_alert(self, alert: dict) -> None:
        """Send alert to configured channels."""
        message = self._format_alert(alert)

        # Slack alert
        await mcp_call(
            server="slack",
            tool="send_message",
            args={
                "channel": "#trading-alerts",
                "text": message
            }
        )
```

---

### MCP Best Practices

#### 1. Tool Design Principles

```python
# Good: Specific, focused tools
Tool(
    name="analyze_security",
    description="Analyze any stock/ETF with 150+ technical signals",
    inputSchema={
        "type": "object",
        "properties": {
            "symbol": {"type": "string", "description": "Ticker symbol"},
            "period": {"type": "string", "default": "1mo"},
            "use_ai": {"type": "boolean", "default": False}
        },
        "required": ["symbol"]
    }
)

# Bad: Overly generic tool
Tool(
    name="do_analysis",
    description="Do stuff with stocks",  # Too vague
    inputSchema={"type": "object"}  # No structure
)
```

#### 2. Error Handling Standards

```python
# Consistent error responses for MCP tools
class MCPError(Exception):
    """Base class for MCP tool errors."""
    def __init__(self, message: str, code: str, details: dict | None = None):
        self.message = message
        self.code = code
        self.details = details or {}

class SymbolNotFoundError(MCPError):
    def __init__(self, symbol: str):
        super().__init__(
            message=f"Symbol '{symbol}' not found or has no data",
            code="SYMBOL_NOT_FOUND",
            details={"symbol": symbol}
        )

# In tool handler
@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    try:
        result = await handle_tool(name, arguments)
        return [TextContent(type="text", text=format_result(result))]
    except MCPError as e:
        return [TextContent(
            type="text",
            text=f"Error [{e.code}]: {e.message}"
        )]
    except Exception as e:
        logger.exception("Unexpected error")
        return [TextContent(
            type="text",
            text=f"Unexpected error: {str(e)}"
        )]
```

#### 3. Response Formatting

```python
# Structured, parseable responses
def format_analysis(result: dict) -> str:
    """Format analysis for Claude consumption."""
    output = []

    # Header with key metrics
    output.append(f"## {result['symbol']} Technical Analysis")
    output.append(f"**Price:** ${result['price']:.2f} ({result['change']:+.2f}%)")
    output.append(f"**Timestamp:** {result['timestamp']}")
    output.append("")

    # Signal summary - easy to parse
    summary = result["summary"]
    output.append("### Signal Summary")
    output.append(f"- Total: {summary['total_signals']}")
    output.append(f"- Bullish: {summary['bullish']}")
    output.append(f"- Bearish: {summary['bearish']}")
    output.append(f"- Avg Score: {summary['avg_score']:.1f}/100")
    output.append("")

    # Top signals with consistent formatting
    output.append("### Top Signals")
    for i, signal in enumerate(result["signals"][:10], 1):
        score = signal.get("ai_score", "-")
        output.append(
            f"{i}. **{signal['signal']}** [{signal['strength']}] "
            f"Score: {score}"
        )

    return "\n".join(output)
```

#### 4. Caching Strategy

```python
# MCP-aware caching
class MCPResultCache:
    """Cache MCP tool results with invalidation."""

    def __init__(self, ttl_seconds: int = 300):
        self._cache: dict[str, tuple[Any, datetime]] = {}
        self._ttl = timedelta(seconds=ttl_seconds)

    def cache_key(self, tool: str, args: dict) -> str:
        """Generate cache key from tool call."""
        args_hash = hashlib.md5(
            json.dumps(args, sort_keys=True).encode()
        ).hexdigest()
        return f"{tool}:{args_hash}"

    def get(self, tool: str, args: dict) -> Any | None:
        """Get cached result if valid."""
        key = self.cache_key(tool, args)
        if key not in self._cache:
            return None

        result, timestamp = self._cache[key]
        if datetime.now() - timestamp > self._ttl:
            del self._cache[key]
            return None

        return result

    def set(self, tool: str, args: dict, result: Any) -> None:
        """Cache a tool result."""
        key = self.cache_key(tool, args)
        self._cache[key] = (result, datetime.now())
```

---

## Advanced Configurations

### 1. Environment-Based Configuration

```python
# config.py - Environment-aware configuration
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    """Application settings with environment variable support."""

    # Core settings
    environment: str = "development"
    log_level: str = "INFO"

    # Cache settings
    cache_ttl_seconds: int = 300
    cache_max_size: int = 100

    # GCP settings (optional)
    use_gcp: bool = False
    gcp_project_id: str = ""
    cloud_run_url: str = ""
    bucket_name: str = "technical-analysis-data"

    # AI settings
    gemini_api_key: str = ""
    use_ai_ranking: bool = False

    # Rate limiting
    rate_limit_rpm: int = 60

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

@lru_cache
def get_settings() -> Settings:
    return Settings()

# Usage
settings = get_settings()
if settings.use_gcp:
    # Initialize GCP clients
    pass
```

### 2. Feature Flags

```python
# features.py - Feature flag system
from enum import Enum

class Feature(str, Enum):
    AI_RANKING = "ai_ranking"
    PARALLEL_SCREENING = "parallel_screening"
    HISTORICAL_TRACKING = "historical_tracking"
    SLACK_ALERTS = "slack_alerts"
    ADVANCED_INDICATORS = "advanced_indicators"

class FeatureFlags:
    """Simple feature flag implementation."""

    _flags: dict[Feature, bool] = {
        Feature.AI_RANKING: False,
        Feature.PARALLEL_SCREENING: True,
        Feature.HISTORICAL_TRACKING: False,
        Feature.SLACK_ALERTS: False,
        Feature.ADVANCED_INDICATORS: True,
    }

    @classmethod
    def is_enabled(cls, feature: Feature) -> bool:
        return cls._flags.get(feature, False)

    @classmethod
    def enable(cls, feature: Feature) -> None:
        cls._flags[feature] = True

    @classmethod
    def disable(cls, feature: Feature) -> None:
        cls._flags[feature] = False

# Usage
if FeatureFlags.is_enabled(Feature.AI_RANKING):
    ranked_signals = await ai_rank_signals(signals)
else:
    ranked_signals = rule_rank_signals(signals)
```

### 3. Plugin Architecture

```python
# plugins.py - Extensible plugin system
from abc import ABC, abstractmethod
from typing import Protocol

class IndicatorPlugin(Protocol):
    """Protocol for custom indicator plugins."""

    name: str

    def calculate(self, df: pd.DataFrame) -> pd.Series: ...
    def get_signals(self, df: pd.DataFrame) -> list[Signal]: ...

class SignalPlugin(Protocol):
    """Protocol for custom signal plugins."""

    name: str
    category: SignalCategory

    def detect(self, df: pd.DataFrame) -> list[Signal]: ...

class PluginRegistry:
    """Registry for custom plugins."""

    _indicators: dict[str, IndicatorPlugin] = {}
    _signals: dict[str, SignalPlugin] = {}

    @classmethod
    def register_indicator(cls, plugin: IndicatorPlugin) -> None:
        cls._indicators[plugin.name] = plugin

    @classmethod
    def register_signal(cls, plugin: SignalPlugin) -> None:
        cls._signals[plugin.name] = plugin

    @classmethod
    def get_all_indicators(cls) -> list[IndicatorPlugin]:
        return list(cls._indicators.values())

# Example custom plugin
class VWAPPlugin:
    """Volume Weighted Average Price plugin."""

    name = "vwap"

    def calculate(self, df: pd.DataFrame) -> pd.Series:
        typical_price = (df["High"] + df["Low"] + df["Close"]) / 3
        return (typical_price * df["Volume"]).cumsum() / df["Volume"].cumsum()

    def get_signals(self, df: pd.DataFrame) -> list[Signal]:
        vwap = self.calculate(df)
        signals = []

        if df["Close"].iloc[-1] > vwap.iloc[-1] * 1.02:
            signals.append(Signal(
                signal="Price Above VWAP",
                description="Price trading 2%+ above VWAP",
                strength=SignalStrength.BULLISH,
                category=SignalCategory.VOLUME
            ))

        return signals

# Register plugin
PluginRegistry.register_indicator(VWAPPlugin())
```

---

## Monitoring & Observability

### 1. Structured Logging

```python
# logging_config.py
import logging
import json
from datetime import datetime

class JSONFormatter(logging.Formatter):
    """JSON log formatter for GCP Cloud Logging."""

    def format(self, record: logging.LogRecord) -> str:
        log_obj = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "severity": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
            "source": {
                "file": record.pathname,
                "line": record.lineno,
                "function": record.funcName
            }
        }

        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)

        if hasattr(record, "extra"):
            log_obj.update(record.extra)

        return json.dumps(log_obj)

def configure_logging(level: str = "INFO") -> None:
    """Configure structured logging."""
    handler = logging.StreamHandler()
    handler.setFormatter(JSONFormatter())

    logging.basicConfig(
        level=getattr(logging, level),
        handlers=[handler]
    )
```

### 2. Metrics Collection

```python
# metrics.py
from dataclasses import dataclass, field
from datetime import datetime
from collections import defaultdict

@dataclass
class Metrics:
    """Application metrics collector."""

    request_count: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    errors: int = 0
    latencies: list[float] = field(default_factory=list)
    symbols_analyzed: set[str] = field(default_factory=set)

    def record_request(self, symbol: str, latency_ms: float, cached: bool) -> None:
        self.request_count += 1
        self.latencies.append(latency_ms)
        self.symbols_analyzed.add(symbol)

        if cached:
            self.cache_hits += 1
        else:
            self.cache_misses += 1

    def record_error(self) -> None:
        self.errors += 1

    def get_summary(self) -> dict:
        return {
            "total_requests": self.request_count,
            "cache_hit_rate": self.cache_hits / max(self.request_count, 1),
            "avg_latency_ms": sum(self.latencies) / max(len(self.latencies), 1),
            "p95_latency_ms": sorted(self.latencies)[int(len(self.latencies) * 0.95)] if self.latencies else 0,
            "error_rate": self.errors / max(self.request_count, 1),
            "unique_symbols": len(self.symbols_analyzed)
        }

# Global metrics instance
metrics = Metrics()

# Usage in endpoints
@app.post("/api/analyze")
async def analyze(request: AnalyzeRequest):
    start = time.time()
    try:
        result = await do_analysis(request)
        metrics.record_request(
            symbol=request.symbol,
            latency_ms=(time.time() - start) * 1000,
            cached=result.get("cached", False)
        )
        return result
    except Exception as e:
        metrics.record_error()
        raise
```

### 3. Health Checks

```python
# health.py
from dataclasses import dataclass
from enum import Enum

class HealthStatus(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"

@dataclass
class HealthCheck:
    name: str
    status: HealthStatus
    message: str = ""
    latency_ms: float = 0

async def check_yfinance() -> HealthCheck:
    """Check yfinance connectivity."""
    import yfinance as yf
    start = time.time()

    try:
        ticker = yf.Ticker("SPY")
        data = ticker.history(period="1d")

        if data.empty:
            return HealthCheck(
                name="yfinance",
                status=HealthStatus.DEGRADED,
                message="No data returned"
            )

        return HealthCheck(
            name="yfinance",
            status=HealthStatus.HEALTHY,
            latency_ms=(time.time() - start) * 1000
        )
    except Exception as e:
        return HealthCheck(
            name="yfinance",
            status=HealthStatus.UNHEALTHY,
            message=str(e)
        )

async def check_firestore() -> HealthCheck:
    """Check Firestore connectivity."""
    if not settings.use_gcp:
        return HealthCheck(
            name="firestore",
            status=HealthStatus.HEALTHY,
            message="GCP disabled"
        )

    start = time.time()
    try:
        db.collection("_health").document("check").set({"ts": datetime.now()})
        return HealthCheck(
            name="firestore",
            status=HealthStatus.HEALTHY,
            latency_ms=(time.time() - start) * 1000
        )
    except Exception as e:
        return HealthCheck(
            name="firestore",
            status=HealthStatus.UNHEALTHY,
            message=str(e)
        )

@app.get("/health/detailed")
async def detailed_health():
    """Detailed health check endpoint."""
    checks = await asyncio.gather(
        check_yfinance(),
        check_firestore()
    )

    overall = HealthStatus.HEALTHY
    for check in checks:
        if check.status == HealthStatus.UNHEALTHY:
            overall = HealthStatus.UNHEALTHY
            break
        elif check.status == HealthStatus.DEGRADED:
            overall = HealthStatus.DEGRADED

    return {
        "status": overall,
        "checks": [
            {
                "name": c.name,
                "status": c.status,
                "message": c.message,
                "latency_ms": c.latency_ms
            }
            for c in checks
        ],
        "metrics": metrics.get_summary()
    }
```

---

## Quick Start Checklist

### For GCP Deployment:

- [ ] Enable required GCP APIs (Cloud Run, Firestore, Pub/Sub, etc.)
- [ ] Create service account with minimal permissions
- [ ] Configure Terraform variables
- [ ] Set up Cloud Storage lifecycle policies
- [ ] Deploy with `terraform apply`
- [ ] Configure Cloud Scheduler for automated analysis
- [ ] Set up monitoring and alerts in Cloud Console

### For MCP Integration:

- [ ] Update Claude Desktop configuration with all MCP servers
- [ ] Test each MCP server individually
- [ ] Create composite workflows for common use cases
- [ ] Set up alerting channels (Slack, Discord)
- [ ] Configure filesystem paths for report exports
- [ ] Test end-to-end workflows

### For Production:

- [ ] Enable API authentication
- [ ] Configure rate limiting
- [ ] Set up structured logging
- [ ] Configure health check endpoints
- [ ] Set up monitoring dashboards
- [ ] Create runbooks for common issues
- [ ] Document API for team members

---

## Summary

This guide covers the key optimizations for running the technical analysis MCP server on GCP and integrating with other MCP servers:

1. **GCP Cost Optimization**: Stay within free tier with aggressive caching, scale-to-zero, and efficient resource usage
2. **Performance**: Parallel processing, vectorized calculations, connection pooling
3. **Security**: API keys, rate limiting, Secret Manager
4. **MCP Integration**: Combine with filesystem, database, search, and messaging MCP servers
5. **Observability**: Structured logging, metrics, health checks

The modular architecture allows you to start simple (local, free) and progressively add GCP and MCP integrations as needed.

---

## Deployment

### Docker Configuration

#### Optimized Dockerfile

```dockerfile
# Dockerfile for Cloud Run deployment
FROM python:3.11-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Production stage
FROM python:3.11-slim as production

WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy application code
COPY src/ ./src/
COPY cloud-run/ ./cloud-run/

# Security: Run as non-root user
RUN useradd --create-home --shell /bin/bash appuser
USER appuser

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PORT=8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

EXPOSE 8080

CMD ["uvicorn", "cloud-run.main:app", "--host", "0.0.0.0", "--port", "8080"]
```

#### Docker Compose for Local Development

```yaml
# docker-compose.yml
version: '3.8'

services:
  api:
    build:
      context: .
      dockerfile: Dockerfile
      target: production
    ports:
      - "8080:8080"
    environment:
      - ENVIRONMENT=development
      - LOG_LEVEL=DEBUG
      - CACHE_TTL_SECONDS=60
      - GEMINI_API_KEY=${GEMINI_API_KEY}
    volumes:
      - ./src:/app/src:ro
      - ./reports:/app/reports
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Local Firestore emulator
  firestore:
    image: gcr.io/google.com/cloudsdktool/cloud-sdk:latest
    command: gcloud emulators firestore start --host-port=0.0.0.0:8085
    ports:
      - "8085:8085"

  # Redis for distributed caching (optional)
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

volumes:
  redis_data:
```

---

### CI/CD Pipeline

#### GitHub Actions Workflow

```yaml
# .github/workflows/deploy.yml
name: Deploy to GCP

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

env:
  PROJECT_ID: ${{ secrets.GCP_PROJECT_ID }}
  REGION: us-central1
  SERVICE_NAME: technical-analysis-api

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          cache: 'pip'

      - name: Install dependencies
        run: |
          pip install -e ".[dev]"

      - name: Run linting
        run: |
          ruff check src/
          mypy src/ --ignore-missing-imports

      - name: Run tests
        run: |
          pytest tests/ -v --cov=src --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: coverage.xml

  build:
    needs: test
    runs-on: ubuntu-latest
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'

    steps:
      - uses: actions/checkout@v4

      - name: Authenticate to GCP
        uses: google-github-actions/auth@v2
        with:
          credentials_json: ${{ secrets.GCP_SA_KEY }}

      - name: Set up Cloud SDK
        uses: google-github-actions/setup-gcloud@v2

      - name: Configure Docker
        run: |
          gcloud auth configure-docker

      - name: Build and push image
        run: |
          docker build -t gcr.io/$PROJECT_ID/$SERVICE_NAME:${{ github.sha }} .
          docker push gcr.io/$PROJECT_ID/$SERVICE_NAME:${{ github.sha }}

  deploy:
    needs: build
    runs-on: ubuntu-latest

    steps:
      - name: Authenticate to GCP
        uses: google-github-actions/auth@v2
        with:
          credentials_json: ${{ secrets.GCP_SA_KEY }}

      - name: Deploy to Cloud Run
        uses: google-github-actions/deploy-cloudrun@v2
        with:
          service: ${{ env.SERVICE_NAME }}
          region: ${{ env.REGION }}
          image: gcr.io/${{ env.PROJECT_ID }}/${{ env.SERVICE_NAME }}:${{ github.sha }}
          flags: |
            --allow-unauthenticated
            --min-instances=0
            --max-instances=3
            --memory=512Mi
            --cpu=1
            --timeout=300
            --set-env-vars=ENVIRONMENT=production

      - name: Smoke test
        run: |
          URL=$(gcloud run services describe $SERVICE_NAME --region=$REGION --format='value(status.url)')
          curl -f "$URL/health" || exit 1
```

#### Terraform CI/CD

```yaml
# .github/workflows/terraform.yml
name: Terraform

on:
  push:
    branches: [main]
    paths:
      - 'cloud-run/terraform/**'
  pull_request:
    paths:
      - 'cloud-run/terraform/**'

jobs:
  terraform:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: cloud-run/terraform

    steps:
      - uses: actions/checkout@v4

      - name: Setup Terraform
        uses: hashicorp/setup-terraform@v3
        with:
          terraform_version: 1.6.0

      - name: Authenticate to GCP
        uses: google-github-actions/auth@v2
        with:
          credentials_json: ${{ secrets.GCP_SA_KEY }}

      - name: Terraform Init
        run: terraform init

      - name: Terraform Format
        run: terraform fmt -check

      - name: Terraform Validate
        run: terraform validate

      - name: Terraform Plan
        if: github.event_name == 'pull_request'
        run: terraform plan -no-color
        continue-on-error: true

      - name: Terraform Apply
        if: github.ref == 'refs/heads/main' && github.event_name == 'push'
        run: terraform apply -auto-approve
```

---

### Testing Setup

#### Test Configuration

```python
# tests/conftest.py
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock

from src.technical_analysis_mcp.models import Signal
from src.technical_analysis_mcp.config import SignalStrength, SignalCategory


@pytest.fixture
def sample_price_data() -> pd.DataFrame:
    """Generate sample OHLCV data for testing."""
    dates = pd.date_range(end=datetime.now(), periods=100, freq='D')
    np.random.seed(42)

    # Generate realistic price movements
    base_price = 100
    returns = np.random.normal(0.001, 0.02, len(dates))
    prices = base_price * np.cumprod(1 + returns)

    df = pd.DataFrame({
        'Open': prices * (1 + np.random.uniform(-0.01, 0.01, len(dates))),
        'High': prices * (1 + np.random.uniform(0, 0.02, len(dates))),
        'Low': prices * (1 - np.random.uniform(0, 0.02, len(dates))),
        'Close': prices,
        'Volume': np.random.randint(1000000, 10000000, len(dates))
    }, index=dates)

    return df


@pytest.fixture
def sample_signals() -> list[Signal]:
    """Generate sample signals for testing."""
    return [
        Signal(
            signal="Golden Cross",
            description="50-day MA crossed above 200-day MA",
            strength=SignalStrength.STRONG_BULLISH,
            category=SignalCategory.MA_CROSS,
            ai_score=85
        ),
        Signal(
            signal="RSI Oversold",
            description="RSI below 30",
            strength=SignalStrength.BULLISH,
            category=SignalCategory.RSI,
            ai_score=70
        ),
    ]


@pytest.fixture
def mock_data_fetcher():
    """Mock data fetcher for testing."""
    fetcher = Mock()
    fetcher.fetch = Mock(return_value=sample_price_data())
    return fetcher


@pytest.fixture
def mock_gemini_client():
    """Mock Gemini API client."""
    client = AsyncMock()
    client.generate_content = AsyncMock(return_value=Mock(
        text='{"score": 85, "reasoning": "Strong signal"}'
    ))
    return client
```

#### Unit Tests

```python
# tests/test_indicators.py
import pytest
import pandas as pd
import numpy as np
from src.technical_analysis_mcp.indicators import (
    calculate_rsi,
    calculate_macd,
    calculate_bollinger_bands,
    calculate_all_indicators
)


class TestRSI:
    def test_rsi_calculation_basic(self, sample_price_data):
        """Test basic RSI calculation."""
        rsi = calculate_rsi(sample_price_data['Close'])

        assert len(rsi) == len(sample_price_data)
        assert rsi.iloc[-1] >= 0 and rsi.iloc[-1] <= 100

    def test_rsi_extreme_up_trend(self):
        """Test RSI in strong uptrend."""
        # Create strong uptrend data
        prices = pd.Series([100 + i * 2 for i in range(50)])
        rsi = calculate_rsi(prices)

        assert rsi.iloc[-1] > 70  # Should be overbought

    def test_rsi_extreme_down_trend(self):
        """Test RSI in strong downtrend."""
        prices = pd.Series([100 - i * 2 for i in range(50)])
        rsi = calculate_rsi(prices)

        assert rsi.iloc[-1] < 30  # Should be oversold


class TestMACD:
    def test_macd_calculation(self, sample_price_data):
        """Test MACD calculation."""
        macd, signal, histogram = calculate_macd(sample_price_data['Close'])

        assert len(macd) == len(sample_price_data)
        assert len(signal) == len(sample_price_data)
        assert len(histogram) == len(sample_price_data)

    def test_macd_crossover_detection(self, sample_price_data):
        """Test MACD crossover logic."""
        macd, signal, _ = calculate_macd(sample_price_data['Close'])

        # Check that crossovers can be detected
        crossovers = (macd > signal) != (macd.shift(1) > signal.shift(1))
        assert crossovers.any()


class TestBollingerBands:
    def test_bollinger_bands_structure(self, sample_price_data):
        """Test Bollinger Bands calculation."""
        upper, middle, lower = calculate_bollinger_bands(sample_price_data['Close'])

        # Upper should always be above middle, middle above lower
        assert (upper >= middle).all()
        assert (middle >= lower).all()

    def test_bollinger_bands_width(self, sample_price_data):
        """Test Bollinger Bands width."""
        upper, middle, lower = calculate_bollinger_bands(sample_price_data['Close'])
        width = upper - lower

        # Width should be positive
        assert (width > 0).all()
```

#### Integration Tests

```python
# tests/test_server.py
import pytest
from unittest.mock import patch, Mock
from src.technical_analysis_mcp.server import (
    analyze_security,
    compare_securities,
    screen_securities
)


class TestAnalyzeSecurity:
    @pytest.mark.asyncio
    async def test_analyze_returns_valid_structure(self, sample_price_data):
        """Test that analyze_security returns correct structure."""
        with patch('src.technical_analysis_mcp.server.get_data_fetcher') as mock:
            mock.return_value.fetch.return_value = sample_price_data

            result = await analyze_security("AAPL", period="1mo")

            assert "symbol" in result
            assert "signals" in result
            assert "summary" in result
            assert "indicators" in result
            assert result["symbol"] == "AAPL"

    @pytest.mark.asyncio
    async def test_analyze_caches_results(self, sample_price_data):
        """Test that results are cached."""
        with patch('src.technical_analysis_mcp.server.get_data_fetcher') as mock:
            mock.return_value.fetch.return_value = sample_price_data

            # First call
            result1 = await analyze_security("AAPL")
            # Second call (should use cache)
            result2 = await analyze_security("AAPL")

            # fetch should only be called once
            assert mock.return_value.fetch.call_count == 1


class TestCompareSecurities:
    @pytest.mark.asyncio
    async def test_compare_ranks_by_score(self, sample_price_data):
        """Test that comparison ranks securities correctly."""
        with patch('src.technical_analysis_mcp.server.analyze_security') as mock:
            mock.side_effect = [
                {"symbol": "AAPL", "summary": {"avg_score": 80}, "price": 150, "change": 2},
                {"symbol": "MSFT", "summary": {"avg_score": 90}, "price": 350, "change": 1},
            ]

            result = await compare_securities(["AAPL", "MSFT"])

            assert result["winner"]["symbol"] == "MSFT"
            assert result["comparison"][0]["symbol"] == "MSFT"
```

#### Load Tests

```python
# tests/test_performance.py
import pytest
import asyncio
import time
from statistics import mean, stdev


class TestPerformance:
    @pytest.mark.asyncio
    async def test_analysis_latency(self, sample_price_data):
        """Test analysis completes within acceptable time."""
        latencies = []

        for _ in range(10):
            start = time.time()
            # Run analysis
            await analyze_security("TEST")
            latencies.append((time.time() - start) * 1000)

        avg_latency = mean(latencies)
        p95_latency = sorted(latencies)[int(len(latencies) * 0.95)]

        assert avg_latency < 500  # Average under 500ms
        assert p95_latency < 1000  # P95 under 1 second

    @pytest.mark.asyncio
    async def test_concurrent_requests(self, sample_price_data):
        """Test handling concurrent requests."""
        symbols = ["AAPL", "MSFT", "GOOGL", "AMZN", "META"]

        start = time.time()
        results = await asyncio.gather(*[
            analyze_security(s) for s in symbols
        ])
        elapsed = time.time() - start

        assert len(results) == 5
        # Should complete all 5 in under 5 seconds with parallelism
        assert elapsed < 5.0
```

---

### Deployment Scripts

#### Deploy Script

```bash
#!/bin/bash
# scripts/deploy.sh

set -euo pipefail

# Configuration
PROJECT_ID="${GCP_PROJECT_ID:-}"
REGION="${GCP_REGION:-us-central1}"
SERVICE_NAME="technical-analysis-api"
IMAGE_TAG="${1:-latest}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Validate environment
if [[ -z "$PROJECT_ID" ]]; then
    log_error "GCP_PROJECT_ID is not set"
    exit 1
fi

log_info "Deploying to project: $PROJECT_ID"
log_info "Region: $REGION"
log_info "Service: $SERVICE_NAME"
log_info "Image tag: $IMAGE_TAG"

# Authenticate
log_info "Configuring Docker authentication..."
gcloud auth configure-docker --quiet

# Build image
log_info "Building Docker image..."
docker build \
    --platform linux/amd64 \
    -t "gcr.io/${PROJECT_ID}/${SERVICE_NAME}:${IMAGE_TAG}" \
    -t "gcr.io/${PROJECT_ID}/${SERVICE_NAME}:latest" \
    .

# Push image
log_info "Pushing image to GCR..."
docker push "gcr.io/${PROJECT_ID}/${SERVICE_NAME}:${IMAGE_TAG}"
docker push "gcr.io/${PROJECT_ID}/${SERVICE_NAME}:latest"

# Deploy to Cloud Run
log_info "Deploying to Cloud Run..."
gcloud run deploy "$SERVICE_NAME" \
    --project="$PROJECT_ID" \
    --region="$REGION" \
    --image="gcr.io/${PROJECT_ID}/${SERVICE_NAME}:${IMAGE_TAG}" \
    --platform=managed \
    --allow-unauthenticated \
    --min-instances=0 \
    --max-instances=3 \
    --memory=512Mi \
    --cpu=1 \
    --timeout=300 \
    --set-env-vars="ENVIRONMENT=production,GCP_PROJECT_ID=${PROJECT_ID}" \
    --quiet

# Get service URL
SERVICE_URL=$(gcloud run services describe "$SERVICE_NAME" \
    --project="$PROJECT_ID" \
    --region="$REGION" \
    --format='value(status.url)')

log_info "Deployment complete!"
log_info "Service URL: $SERVICE_URL"

# Smoke test
log_info "Running smoke test..."
if curl -sf "${SERVICE_URL}/health" > /dev/null; then
    log_info "Health check passed!"
else
    log_error "Health check failed!"
    exit 1
fi

log_info "Deployment successful!"
```

#### Terraform Deploy Script

```bash
#!/bin/bash
# scripts/terraform-deploy.sh

set -euo pipefail

TERRAFORM_DIR="cloud-run/terraform"
ACTION="${1:-plan}"

cd "$TERRAFORM_DIR"

# Initialize if needed
if [[ ! -d ".terraform" ]]; then
    echo "Initializing Terraform..."
    terraform init
fi

case "$ACTION" in
    plan)
        terraform plan -out=tfplan
        ;;
    apply)
        terraform apply tfplan
        ;;
    destroy)
        read -p "Are you sure you want to destroy? (yes/no) " confirm
        if [[ "$confirm" == "yes" ]]; then
            terraform destroy
        fi
        ;;
    *)
        echo "Usage: $0 {plan|apply|destroy}"
        exit 1
        ;;
esac
```

#### Cost Monitor Script

```bash
#!/bin/bash
# scripts/monitor-costs.sh

PROJECT_ID="${GCP_PROJECT_ID:-}"

echo "=== GCP Free Tier Usage Report ==="
echo "Project: $PROJECT_ID"
echo ""

# Cloud Run requests
echo "Cloud Run (2M requests/month free):"
gcloud monitoring metrics list \
    --filter="metric.type=run.googleapis.com/request_count" \
    --project="$PROJECT_ID" 2>/dev/null || echo "  Unable to fetch metrics"

# Firestore reads
echo ""
echo "Firestore (50K reads/day free):"
gcloud firestore operations list \
    --project="$PROJECT_ID" \
    --limit=5 2>/dev/null || echo "  Unable to fetch operations"

# Storage usage
echo ""
echo "Cloud Storage (5GB free):"
gsutil du -s "gs://technical-analysis-data" 2>/dev/null || echo "  Bucket not found"

# Billing estimate
echo ""
echo "Current billing period estimate:"
gcloud billing accounts list --format="table(displayName,open)" 2>/dev/null || echo "  Unable to fetch billing info"
```

---

## Additional MCP Server Examples

### Google Sheets Integration

```json
{
  "mcpServers": {
    "google-sheets": {
      "command": "npx",
      "args": ["-y", "@anthropic/mcp-server-google-sheets"],
      "env": {
        "GOOGLE_CREDENTIALS_PATH": "${HOME}/.config/gcloud/application_default_credentials.json"
      }
    }
  }
}
```

**Use Case**: Export analysis results to a Google Sheet for tracking:

```python
# Export to Google Sheets via MCP
async def export_to_sheets(analysis: dict, spreadsheet_id: str):
    await mcp_call(
        server="google-sheets",
        tool="append_rows",
        args={
            "spreadsheet_id": spreadsheet_id,
            "range": "Analysis!A:Z",
            "values": [[
                analysis["timestamp"],
                analysis["symbol"],
                analysis["price"],
                analysis["change"],
                analysis["summary"]["bullish"],
                analysis["summary"]["bearish"],
                analysis["summary"]["avg_score"]
            ]]
        }
    )
```

### Memory/Knowledge Base Integration

```json
{
  "mcpServers": {
    "memory": {
      "command": "npx",
      "args": ["-y", "@anthropic/mcp-server-memory"]
    }
  }
}
```

**Use Case**: Store and retrieve analysis patterns:

```python
# Store successful trade patterns
async def remember_pattern(signal: str, outcome: str, notes: str):
    await mcp_call(
        server="memory",
        tool="create_memory",
        args={
            "content": f"Signal: {signal}\nOutcome: {outcome}\nNotes: {notes}",
            "tags": ["trading", "pattern", outcome]
        }
    )

# Retrieve similar patterns
async def recall_patterns(signal: str):
    return await mcp_call(
        server="memory",
        tool="search_memories",
        args={"query": f"trading pattern {signal}"}
    )
```

### Puppeteer/Browser Integration

```json
{
  "mcpServers": {
    "puppeteer": {
      "command": "npx",
      "args": ["-y", "@anthropic/mcp-server-puppeteer"]
    }
  }
}
```

**Use Case**: Capture chart screenshots for reports:

```python
# Capture TradingView chart
async def capture_chart(symbol: str) -> str:
    await mcp_call(
        server="puppeteer",
        tool="navigate",
        args={"url": f"https://www.tradingview.com/chart/?symbol={symbol}"}
    )

    await mcp_call(
        server="puppeteer",
        tool="wait",
        args={"selector": ".chart-container", "timeout": 5000}
    )

    screenshot = await mcp_call(
        server="puppeteer",
        tool="screenshot",
        args={"fullPage": False}
    )

    return screenshot["path"]
```

---

## Troubleshooting Guide

### Common Issues

#### 1. yfinance Rate Limiting

**Symptom**: `DataFetchError: No data returned for symbol`

**Solution**:
```python
# Add retry logic with backoff
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10)
)
def fetch_with_retry(symbol: str, period: str) -> pd.DataFrame:
    ticker = yf.Ticker(symbol)
    data = ticker.history(period=period)
    if data.empty:
        raise ValueError(f"No data for {symbol}")
    return data
```

#### 2. Cloud Run Cold Starts

**Symptom**: First request takes 5-10 seconds

**Solution**:
```yaml
# Set minimum instances
annotations:
  autoscaling.knative.dev/minScale: "1"  # Keep 1 instance warm
  run.googleapis.com/startup-cpu-boost: "true"
```

#### 3. Firestore Quota Exceeded

**Symptom**: `ResourceExhausted: Quota exceeded`

**Solution**:
- Enable caching to reduce reads
- Batch writes where possible
- Use subcollections for high-volume data

```python
# Batch writes
batch = db.batch()
for symbol, data in analyses.items():
    ref = db.collection("signals").document(symbol)
    batch.set(ref, data)
batch.commit()  # Single write operation
```

#### 4. MCP Server Connection Refused

**Symptom**: `Connection refused` when calling MCP tools

**Solution**:
1. Check server is running: `ps aux | grep mcp`
2. Verify Claude Desktop config path
3. Check logs: `~/Library/Logs/Claude/mcp*.log`
4. Restart Claude Desktop

#### 5. Gemini API Rate Limits

**Symptom**: `429 Too Many Requests`

**Solution**:
```python
# Implement rate limiting
from asyncio import Semaphore

gemini_semaphore = Semaphore(10)  # Max 10 concurrent requests

async def rank_with_ai(signals: list[Signal]) -> list[Signal]:
    async with gemini_semaphore:
        # Rate limit to 60 RPM
        await asyncio.sleep(1.0)  # 1 second between requests
        return await call_gemini(signals)
```

### Debug Mode

Enable debug logging:

```bash
# Environment variable
export LOG_LEVEL=DEBUG

# Or in code
import logging
logging.getLogger("technical_analysis_mcp").setLevel(logging.DEBUG)
```

### Performance Profiling

```python
# Add profiling middleware
import cProfile
import pstats
from io import StringIO

@app.middleware("http")
async def profile_middleware(request: Request, call_next):
    if request.headers.get("X-Profile") == "true":
        profiler = cProfile.Profile()
        profiler.enable()

        response = await call_next(request)

        profiler.disable()
        stream = StringIO()
        stats = pstats.Stats(profiler, stream=stream)
        stats.sort_stats("cumulative")
        stats.print_stats(20)

        # Log profile results
        logger.info("Profile:\n%s", stream.getvalue())

        return response

    return await call_next(request)
```

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2024-01 | Initial guide |
| 1.1.0 | 2024-01 | Added Docker, CI/CD, testing sections |
| 1.2.0 | 2024-01 | Added MCP server examples, troubleshooting |
