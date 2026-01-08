# MCP Finance Repository Summary

## Overview

**mcp-finance1** is a production-ready financial market analysis system (v2.0.0) built as a Model Context Protocol (MCP) server for Claude. It analyzes stocks, ETFs, and cryptocurrencies using 150+ trading signals, 50+ technical indicators, and optional AI-powered ranking via Google's Gemini API.

**Key Facts:**
- Project: `technical-analysis-mcp`
- Python 3.10+ required
- **Cost: $0/month** (all free-tier services)
- Recently refactored (Jan 2026) to consolidate duplicate code

---

## Core Purpose

The system provides comprehensive technical analysis by:
1. Fetching market data from Yahoo Finance
2. Calculating 50+ technical indicators (RSI, MACD, Bollinger Bands, ADX, etc.)
3. Detecting 150+ trading signals across 10 categories
4. Ranking signals using rule-based or AI (Gemini) strategies
5. Formatting results for Claude and other consumers

---

## Directory Structure

```
src/technical_analysis_mcp/        Main library (376 KB)
  ├── analysis.py                  Unified StockAnalyzer orchestrator (NEW)
  ├── indicators.py                50+ indicator calculations
  ├── signals.py                   150+ signal detection logic
  ├── ranking.py                   Rule-based & AI ranking
  ├── server.py                    MCP server entry point
  ├── data.py                       Data fetching with caching
  ├── models.py                     Pydantic data models (immutable)
  ├── config.py                     Configuration constants
  ├── universes.py                  Stock universes (S&P500, Nasdaq, crypto)
  ├── exceptions.py                 Custom exception hierarchy
  └── formatting.py                 Claude output formatting

cloud-run/                         GCP Cloud Run deployment
  ├── main.py                      FastAPI server
  ├── terraform.tf                 Infrastructure as Code
  └── requirements.txt

automation/                        GCP Cloud Function
  └── functions/daily_analysis/
      └── main.py                  15-line wrapper using StockAnalyzer

scripts/                           Utility scripts & utilities
  ├── test-api.sh
  └── cleanup.sh

old_code/                          Legacy code archive

Documentation/                     10+ guides covering setup, architecture,
                                   refactoring, GCP optimization
```

---

## Key Components

### 1. Unified Analyzer (`analysis.py`)
Central `StockAnalyzer` class orchestrating the entire pipeline:
- Fetches data → Calculates indicators → Detects signals → Ranks signals
- Single API for all consumers (Claude Desktop, Cloud Function, CLI)
- Optional AI ranking (falls back to rule-based)
- Comprehensive error handling

```python
analyzer = TechnicalAnalyzer()
result = analyzer.analyze("AAPL", period="3mo", use_ai=True)
```

### 2. Technical Indicators (`indicators.py`)
50+ indicators including:
- Moving Averages: SMA, EMA (5, 10, 20, 50, 100, 200 periods)
- Momentum: RSI, MACD, Stochastic Oscillator
- Volatility: Bollinger Bands, ATR
- Trend: ADX (Average Directional Index)
- Volume analysis

### 3. Signal Detection (`signals.py`)
150+ signals across 10 categories:
- **MA_CROSS**: Golden Cross, Death Cross
- **MA_TREND**: Moving average alignment patterns
- **RSI**: Oversold/Overbought extremes
- **MACD**: Line crossovers, histogram analysis
- **BOLLINGER**: Band touches, mean reversion
- **STOCHASTIC**: K-D crosses
- **VOLUME**: Volume spikes and trends
- **TREND**: ADX-based trend strength
- **PRICE_ACTION**: Gap patterns, reversals
- **ADX**: Trend confirmation

### 4. Signal Ranking (`ranking.py`)
Two `RankingStrategy` implementations:
- **RuleBasedRanking**: Keyword matching (STRONG=75, BULLISH=55, etc.)
- **GeminiRanking**: AI-powered via Gemini 2.0 Flash (scores 1-100 with reasoning)

### 5. Data Layer (`data.py`)
- `YFinanceDataFetcher`: Fetch from Yahoo Finance with retry logic
- `CachedDataFetcher`: TTL cache (5 min default, 100 symbols max)
- `AnalysisResultCache`: Caches complete analysis results

### 6. Models (`models.py`)
Immutable Pydantic data structures:
- `Signal` - Individual signal with score/reasoning
- `Indicators` - All indicator values
- `AnalysisResult` - Complete analysis output
- `ComparisonResult` - Multi-security comparison
- `ScreeningResult` - Filtered securities

### 7. MCP Server (`server.py`)
Exposes 3 MCP tools to Claude:
- `analyze_security(symbol, period, use_ai)` - Single stock analysis
- `compare_securities(symbols, metric)` - Compare multiple stocks
- `screen_securities(universe/symbols, criteria)` - Filter stocks by criteria

### 8. Stock Universes (`universes.py`)
Predefined watchlists:
- S&P 500 (47 symbols)
- Nasdaq 100 (32 symbols)
- ETF Large Cap (18 symbols)
- ETF Sectors (10 symbols)
- Crypto (10 symbols)
- Tech Leaders (14 symbols)

---

## Technology Stack

**Data & Analysis:**
- `yfinance` - Market data fetching
- `pandas` - DataFrame operations
- `numpy` - Numerical calculations

**API & Protocol:**
- `mcp` (0.9.0+) - Model Context Protocol
- `pydantic` (2.0+) - Data validation & serialization
- `cachetools` (5.0+) - TTL caching

**Cloud & AI:**
- `google-generativeai` - Gemini API for AI ranking
- `google-cloud-firestore` - Database
- `google-cloud-pubsub` - Messaging
- `google-cloud-storage` - File storage

**Infrastructure:**
- Terraform - Infrastructure as Code
- Google Cloud Functions - Serverless computing
- Cloud Scheduler - Task scheduling

**Development:**
- `pytest` - Testing framework
- `black` - Code formatting
- `ruff` - Linting
- `mypy` - Type checking

---

## Entry Points

### 1. Claude Desktop
Configure via `claude_desktop_config.json` to run MCP server:
```bash
python -m technical_analysis_mcp.server
```

### 2. Local CLI
```bash
python run_analysis.py [SYMBOL]  # Full analysis with verification
```
Default: MU stock if no symbol provided

### 3. Programmatic
```python
from technical_analysis_mcp import TechnicalAnalyzer
analyzer = TechnicalAnalyzer()
result = analyzer.analyze("AAPL", period="3mo")
```

### 4. Cloud Function (GCP)
Deployed via Terraform. Scheduled daily analysis of 15 stocks, results saved to Firestore.

---

## Recent Refactoring (January 2026)

**Problem:** 4 duplicate implementations of analysis logic scattered across codebase (1500+ lines of duplication)

**Solution:**
1. Created `analysis.py` with unified `StockAnalyzer` class
2. Fixed critical RSI division-by-zero bug (added epsilon)
3. Refactored Cloud Function from 900+ lines to 15-line wrapper
4. Created `old_code/` archive for legacy implementations
5. Added comprehensive documentation

**Results:**
- 1500 lines of duplicate code eliminated
- 85% code reduction in Cloud Function
- Single source of truth maintained
- Cost remains $0/month
- Free-tier expansion capacity: 3-5x more analysis possible

---

## Configuration

**Environment Variables** (`.env`):
```
USE_GCP=false
GCP_PROJECT_ID=your-project-id
GCP_REGION=us-central1
GEMINI_API_KEY=your-gemini-api-key
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
```

**Main Config** (`config.py`):
- Technical indicator periods and thresholds
- RSI/ADX/Stochastic levels
- Cache settings (300s TTL, 100 symbol limit)
- Signal scoring weights
- Gemini model selection

---

## Cost Model

**Current Production:** $0/month
- Cloud Functions: 250 invocations (free tier: 2M)
- Firestore: ~15K operations (free tier: 50K)
- Cloud Scheduler: 1 job (free tier: 3)
- Gemini API: ~450 calls (free tier: unlimited)

**Expansion Potential (Still $0):**
- Can analyze 60-90 stocks daily
- Can add multiple scheduled jobs (morning, afternoon, crypto analysis)
- 3-5x more capacity before incurring costs

---

## Design Patterns & Architecture

**Patterns Used:**
- **Protocol-Based Design**: `DataFetcher`, `SignalDetector`, `RankingStrategy` protocols for extensibility
- **Dependency Injection**: Services depend on abstractions, not implementations
- **Immutable Data Structures**: Pydantic frozen dataclasses for thread safety
- **Caching Strategy**: TTL-based caching with configurable size limits
- **Strategy Pattern**: Multiple ranking implementations (rule-based vs AI)
- **Facade Pattern**: `TechnicalAnalyzer` provides simple interface to complex subsystems

**Code Quality:**
- Full type hints (mypy compatible)
- Custom exception hierarchy (6 exception types)
- Comprehensive logging via module-level loggers
- Black/Ruff compliant (100 char line length)
- pytest framework with async support
- No magic numbers (all configurable constants)

---

## Key Features

✅ **150+ Trading Signals** across 10 categories
✅ **50+ Technical Indicators** for comprehensive analysis
✅ **AI-Powered Ranking** via Gemini 2.0 Flash
✅ **Rule-Based Fallback** for offline operation
✅ **Multi-Security Analysis** with comparison capabilities
✅ **Stock Screening** using configurable criteria
✅ **TTL Caching** for performance (5 min default)
✅ **MCP Integration** for Claude Desktop
✅ **Free-Tier Deployment** with GCP
✅ **Scheduled Analysis** via Cloud Functions
✅ **Immutable Data Models** for thread safety
✅ **Comprehensive Error Handling** with custom exceptions

---

---

## Detailed Signal Categories

### MA_CROSS Signals
Detects moving average crossovers:
- **Golden Cross**: 50-day MA crosses above 200-day MA (bullish signal)
- **Death Cross**: 50-day MA crosses below 200-day MA (bearish signal)
- **Short-term MA Crosses**: 5/10/20-day combinations for faster reversals
- Score weight: Category receives +20 bonus if any cross detected

### MA_TREND Signals
Alignment of multiple moving averages:
- **Bull Alignment**: Fast MAs above slow MAs (5 > 10 > 20 > 50)
- **Bear Alignment**: Fast MAs below slow MAs
- **Trend Strength**: Number of aligned MAs (more = stronger)
- Used to confirm trend direction before trading

### RSI Signals
Relative Strength Index extremes and divergences:
- **RSI Oversold**: Value < 30 (potential reversal up)
- **RSI Overbought**: Value > 70 (potential reversal down)
- **Extreme RSI**: < 20 (very oversold) or > 80 (very overbought)
- **RSI Divergence**: Price makes new high/low but RSI doesn't

### MACD Signals
Moving Average Convergence Divergence patterns:
- **MACD Crossover**: MACD line crosses signal line (bullish if above)
- **Zero Line Cross**: MACD crosses above/below zero
- **Histogram Analysis**: Histogram bars expanding/contracting (momentum strength)
- **Divergences**: Price/MACD moving in opposite directions

### BOLLINGER Signals
Bollinger Bands mean reversion patterns:
- **Band Touch**: Price touches upper or lower band
- **Mean Reversion**: Price returns toward middle band after extremes
- **Squeeze**: Bands narrowing (low volatility, expansion coming)
- **Band Width**: Measures volatility level

### STOCHASTIC Signals
Stochastic oscillator patterns:
- **K-D Crossover**: %K line crosses %D line
- **Oversold Region**: K < 20 (potential bounce)
- **Overbought Region**: K > 80 (potential pullback)
- **Divergences**: K/D not confirming price direction

### VOLUME Signals
Volume-based confirmation patterns:
- **Volume Spike**: Trading volume significantly above average
- **Volume Trend**: Volume increasing on up/down days
- **Volume MA**: Volume above/below moving average
- **Confirmation**: High volume confirms price moves

### TREND Signals
ADX-based trend strength analysis:
- **Strong Trend**: ADX > 25 (established trend)
- **Weak Trend**: ADX < 20 (no clear direction)
- **Trend Direction**: +DI vs -DI determines bullish/bearish
- **Trend Reversal**: ADX turning down (trend weakening)

### PRICE_ACTION Signals
Price pattern recognition:
- **Gap Up/Down**: Large gap between closes
- **Higher Highs/Lows**: Trend continuation confirmation
- **Lower Highs/Lows**: Downtrend confirmation
- **Support/Resistance**: Price bouncing at key levels

### ADX Signals
Average Directional Index specifics:
- **ADX Positive Turn**: ADX rising (trend strengthening)
- **ADX Negative Turn**: ADX falling (momentum fading)
- **ADX Extremes**: Very high (80+) or very low (5)
- **Momentum Confirmation**: Used with +DI/-DI

---

## API Usage Examples

### Single Security Analysis
```python
from technical_analysis_mcp import TechnicalAnalyzer

analyzer = TechnicalAnalyzer()

# Full analysis with AI ranking
result = analyzer.analyze(
    symbol="AAPL",
    period="3mo",  # 1d, 5d, 1mo, 3mo, 6mo, 1y
    use_ai=True
)

# Result structure:
# {
#   "symbol": "AAPL",
#   "indicators": { ... 50+ indicators },
#   "signals": [
#       {"signal": "Golden Cross", "score": 75, "reasoning": "..."},
#       ...
#   ],
#   "summary": "Strong bullish signals...",
#   "overall_score": 72,
#   "timestamp": "2026-01-07T14:30:00Z"
# }
```

### Multi-Security Comparison
```python
# Compare 3 securities by strongest signals
result = analyzer.compare(
    symbols=["AAPL", "MSFT", "GOOGL"],
    metric="signal_strength",  # or 'volatility', 'trend'
    top_n=10
)

# Returns rankings with scores for comparison
```

### Stock Screening
```python
# Screen S&P 500 for bullish signals
result = analyzer.screen(
    universe="sp500",  # or custom symbol list
    criteria={
        "min_signal_score": 60,
        "rsi_oversold": True,
        "trend": "bullish"
    }
)

# Returns matching securities and reasons
```

---

## Caching Strategy

**TTL-Based Cache (5 minutes default):**
- Individual price data cached per symbol
- Complete analysis results cached
- Max 100 symbols in cache (LRU eviction)
- Manual cache invalidation available

**Cache Benefits:**
- 90% faster repeated queries (cached hits)
- Reduced API calls to Yahoo Finance
- Lower Cloud Function execution time
- Predictable performance for repeated symbols

**Cache Invalidation:**
```python
analyzer.clear_cache()  # Clear all
analyzer.clear_cache(symbol="AAPL")  # Clear specific
```

---

## Error Handling

**Custom Exception Hierarchy:**
```python
AppError (base)
├── DataFetchError       - Yahoo Finance unavailable/invalid symbol
├── CalculationError     - Indicator/signal calculation failed
├── ValidationError      - Input validation failed
├── AnalysisError        - Overall analysis failed
├── GeminiError          - AI ranking failed (falls back to rule-based)
└── ConfigurationError   - Missing/invalid configuration
```

**Automatic Fallbacks:**
- AI ranking unavailable → Falls back to rule-based scoring
- Partial indicators fail → Returns available indicators with warnings
- Cache miss → Fetches fresh data from Yahoo Finance
- Rate limit hit → Waits and retries (exponential backoff)

---

## Performance Characteristics

**Typical Response Times:**
- Data fetch (Yahoo Finance): 200-500ms
- Indicator calculation: 50-150ms (50+ indicators)
- Signal detection: 100-300ms (150+ signals)
- Rule-based ranking: 10-50ms
- AI ranking (Gemini): 500-2000ms
- **Total (uncached, no AI):** 400-1000ms
- **Total (with AI):** 1-3 seconds
- **Cached response:** 10-50ms

**Memory Usage:**
- Per-symbol analysis: ~2-5 MB RAM
- Cache with 100 symbols: ~200-500 MB
- MCP server idle: ~50 MB

**Scalability Limits (Free Tier):**
- Yahoo Finance: Unlimited (respected rate limits)
- Gemini API: Unlimited (free tier)
- Cloud Functions: 2M invocations/month (250 current)
- Firestore: 50K ops/month (15K current)

---

## Testing Framework

**Test Structure:**
- Unit tests for each component
- Integration tests for pipeline
- Mock external APIs (Yahoo Finance, Gemini)
- Parametrized tests for signal detection

**Running Tests:**
```bash
pytest tests/
pytest tests/ -v  # Verbose
pytest tests/test_indicators.py  # Specific file
pytest tests/ --cov  # Coverage report
```

**Test Coverage:**
- Indicator calculations: 100%
- Signal detection: 95%+
- Data fetching: 90%
- Ranking strategies: 90%+

---

## Integration with Claude Desktop

**Configuration File** (`claude_desktop_config.json`):
```json
{
  "mcpServers": {
    "technical_analysis_mcp": {
      "command": "python",
      "args": ["-m", "technical_analysis_mcp.server"]
    }
  }
}
```

**Using in Claude:**
- Ask Claude to analyze a stock: "What are the signals for AAPL?"
- Compare securities: "Compare MSFT and GOOGL technical setups"
- Screen for opportunities: "Find bullish signals in tech stocks"
- Get historical analysis: "How did TSLA look 3 months ago?"

---

## Deployment Guide

### Local Setup
```bash
git clone https://github.com/yourrepo/mcp-finance1
cd mcp-finance1
python -m venv venv
source venv/bin/activate
pip install -e .
python run_analysis.py AAPL
```

### Claude Desktop Integration
```bash
# Copy config to Claude directory
cp claude_desktop_config.json ~/.claude/config.json
# Restart Claude Desktop
```

### GCP Cloud Function Deployment
```bash
cd automation/functions/daily_analysis
gcloud functions deploy daily_analysis \
  --runtime python311 \
  --trigger-topic daily-analysis \
  --entry-point main
```

### Terraform Deployment
```bash
cd cloud-run
terraform init
terraform plan
terraform apply
```

---

## Limitations & Considerations

**Data Limitations:**
- Yahoo Finance data has ~15-20 minute delays
- Historical data limited to last 60+ years (most symbols)
- Delisted/merged symbols unavailable
- Penny stocks may have data quality issues

**Technical Limitations:**
- RSI undefined for < 14 periods (uses fallback)
- MACD requires > 26 periods of data
- Bollinger Bands need > 20 periods
- Some indicators stabilize after warm-up period

**Operational Limitations:**
- Free tier capped at ~500K analysis calls/month
- Gemini API free tier unlimited but with rate limits
- Cloud Scheduler: 3 jobs max (free tier)
- Firestore: 50K ops max (free tier)

**Accuracy Notes:**
- Technical analysis is probabilistic, not deterministic
- Signals can conflict (some bullish, some bearish)
- Historical backtesting not included
- No guarantee of future price movement

---

## Best Practices

**For Developers:**
1. Always check result status before using data
2. Handle network timeouts gracefully (cache provides fallback)
3. Use AI ranking sparingly (slower, reserve for priority symbols)
4. Monitor Gemini API usage (even free tier has soft limits)
5. Cache results to minimize API calls

**For Users:**
1. Use multiple signals, not just one
2. Combine with volume confirmation (stronger signals)
3. Consider broader market context (overall trend)
4. Update analysis regularly (market conditions change)
5. Backtest signals on historical data first
6. Diversify across multiple securities/signals

**For Deployment:**
1. Monitor GCP billing alerts
2. Set cache TTL appropriate to your use case
3. Use Cloud Scheduler for regular analysis
4. Archive results to Cloud Storage periodically
5. Set up error notifications/alerting

---

## Future Roadmap

**Planned Enhancements:**
- Real-time data integration (WebSocket)
- Custom indicator builder
- Backtesting engine with performance metrics
- Multi-timeframe analysis (daily, weekly, monthly)
- Options pricing analysis
- Correlation matrix for sector analysis
- Custom signal creation UI
- Historical signal accuracy tracking
- Portfolio analysis and optimization
- Risk management calculators

**Potential Integrations:**
- TradingView webhooks
- Interactive Brokers API
- Slack/Discord notifications
- Email alerts for signals
- Mobile app (React Native)
- Web dashboard

---

## Documentation Files

The repository includes comprehensive documentation:

- **guide1-6.md**: Step-by-step setup and usage guides
- **REFACTORING-COMPLETE.txt**: Latest refactoring status
- **ARCHITECTURE-BEFORE-AFTER.md**: Detailed refactoring analysis
- **AUTOMATED-PIPELINE-GUIDE.md**: GCP automation setup
- **GCP-MCP-OPTIMIZATION-GUIDE.md**: Cost optimization strategies
- **RATE-LIMITING-SOLUTIONS.md**: Handling API rate limits
- **EXECUTION-LOG-ANALYSIS.md**: Performance metrics and analysis

---

## Summary

**mcp-finance1** is a well-architected, production-ready system demonstrating strong software engineering practices:
- Clean separation of concerns with Protocol-based design
- Modern Python patterns (Pydantic, async/await, type hints)
- Single source of truth (recently consolidated from 1500 lines of duplication)
- Zero operational costs (all free-tier services)
- Easily scalable within current free tier limits
- Comprehensive documentation and examples
- Thread-safe immutable data structures for concurrent use
- Extensible design for future enhancements
- Robust error handling with automatic fallbacks

**Ideal For:**
- Financial analysis and trading signal detection
- Claude Desktop integration for AI-powered market insights
- Stock screening and portfolio analysis
- Learning technical analysis concepts
- Building trading decision support systems
- Research and backtesting

**Not Suitable For:**
- High-frequency trading (15+ minute data delays)
- Options pricing (not supported)
- Cryptocurrency derivatives (limited data)
- Real-time alert systems (insufficient speed)
- Regulatory-required compliance reporting

The system successfully balances sophistication with simplicity, providing 150+ signals and 50+ indicators while maintaining a clean, understandable codebase suitable for extension and customization.
