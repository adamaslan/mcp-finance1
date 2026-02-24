# MCP Finance Repository - Complete Summary (v2.0)

## Overview

**mcp-finance1** is a professional-grade financial market analysis system (v2.0.0) that provides both comprehensive technical signal detection AND risk-qualified trade planning. Built as a Model Context Protocol (MCP) server for Claude, it analyzes stocks, ETFs, and cryptocurrencies using 150+ trading signals, 50+ technical indicators, with optional AI ranking and a new Risk-First Layer.

**Key Facts:**
- Project: `technical-analysis-mcp` v2.0.0
- Python 3.10+ required
- **Cost: $0/month** (all free-tier services)
- Recently enhanced (Jan 2026) with Risk-First Layer for trade planning
- Dual-mode operation: signals analysis + risk-qualified trade plans

---

## What's New: Risk-First Layer (v2.0)

A new professional risk management layer sits between signal detection and output, transforming 150+ signals into **1-3 actionable trade plans** or suppressed setups with machine-readable reasons.

**New Pipeline:**
```
data → indicators → signals → ranking → RISK QUALIFICATION → trade plan OR suppression
```

**Two Operating Modes:**

### Mode 1: Signal Analysis (Legacy - Unchanged)
- `analyze_security` tool
- Returns 150+ ranked signals
- Supports AI ranking via Gemini
- Best for: Comprehensive market insight

### Mode 2: Risk-Qualified Trading (NEW)
- `get_trade_plan` tool
- Returns 1-3 actionable trade plans
- Includes full suppression logic with machine-readable codes
- Best for: Actionable trade decisions

Both tools coexist and reuse the same data/indicator/signal pipeline.

---

## Core Purpose

The system provides two complementary analysis modes:

### Signal Analysis (Traditional)
1. Fetch market data from Yahoo Finance
2. Calculate 50+ technical indicators (RSI, MACD, Bollinger, ADX, ATR, etc.)
3. Detect 150+ trading signals across 10 categories
4. Rank signals using rule-based or AI (Gemini) strategies
5. Format results for Claude display

### Trade Planning (NEW - Risk-First)
1. Execute signal analysis pipeline (above)
2. Classify volatility regime (LOW/MEDIUM/HIGH by ATR)
3. Select trading timeframe (ONE active: swing/day/scalp)
4. Calculate ATR-based stop levels with validation
5. Detect structure-based invalidation levels
6. Compute risk-to-reward ratio (minimum 1.5:1)
7. Evaluate 7+ suppression conditions
8. Generate 1-3 trade plans OR explain why suppressed
9. Suggest trade vehicle (stock vs options with full specs)

---

## Directory Structure

```
src/technical_analysis_mcp/
├── __init__.py                  # Package exports
├── server.py                    # MCP server (4 tools)
├── analysis.py                  # Unified StockAnalyzer
├── indicators.py                # 50+ indicators
├── signals.py                   # 150+ signal detection
├── ranking.py                   # Rule-based & AI ranking
├── data.py                       # Data fetching & caching
├── models.py                     # Pydantic models (signals)
├── config.py                     # Config constants (50+)
├── universes.py                  # Stock universes
├── exceptions.py                 # Exception hierarchy
├── formatting.py                 # Output formatting
│
└── risk/                         # NEW: Risk-First Layer
    ├── __init__.py
    ├── models.py                 # 15 Pydantic models
    ├── protocols.py              # 6 Protocol definitions
    ├── risk_assessor.py          # Main orchestrator
    ├── volatility_regime.py      # Volatility classification
    ├── timeframe_rules.py        # Timeframe selector
    ├── stop_distance.py          # Stop validation
    ├── invalidation.py           # Invalidation detection
    ├── rr_calculator.py          # R:R calculation
    ├── suppression.py            # Suppression logic (7+ codes)
    └── option_rules.py           # Vehicle selection

cloud-run/                        # GCP Cloud Run deployment
├── main.py                       # FastAPI server
├── terraform.tf                  # Infrastructure as Code
└── requirements.txt

automation/                       # GCP Cloud Function
└── functions/daily_analysis/
    └── main.py

Documentation/
├── RISK_LAYER_PLAN.md           # Implementation plan
├── REPOSITORY_SUMMARY.md        # Original summary
├── IMPLEMENTATION_TEST.md       # Test results
└── 10+ setup and optimization guides
```

---

## MCP Tools (4 Total)

### 1. `analyze_security` (Signal Analysis)
Comprehensive technical signal detection and ranking.

**Parameters:**
- `symbol` (required): Ticker symbol
- `period` (optional, default "1mo"): 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max
- `use_ai` (optional, default false): Enable Gemini AI ranking

**Returns:**
- 150+ detected signals (top 50 returned)
- Summary: total signals, bullish/bearish counts, average score
- Key indicators: RSI, MACD, ADX, Volume
- Cached indicator: whether result was cached

**Output Example:**
```
📊 AAPL Technical Analysis
🟢 Price: $182.50 (+1.25%)

📈 Summary:
• Total Signals: 147
• Bullish: 89 | Bearish: 58
• Avg Score: 68.5/100

🎯 Top 10 Signals:
1. 🔥 [85] GOLDEN CROSS
2. ⚡ [72] MA ALIGNMENT BULLISH
3. ⚡ [65] RSI OVERSOLD
...
```

---

### 2. `get_trade_plan` (Risk-Qualified Trading - NEW)
Professional trade planning with risk assessment and suppression logic.

**Parameters:**
- `symbol` (required): Ticker symbol
- `period` (optional, default "1mo"): Time period

**Returns:**
- 1-3 actionable trade plans with full details, OR
- Suppression reasons with machine-readable codes

**Output Example (Qualified):**
```
🔥 AAPL Trade Plan (SWING)
🟢 Bias: BULLISH

📍 Levels:
• Entry: $182.50
• Stop: $178.20 (2.4% risk)
• Target: $191.45 (5.0% move)
• Invalidation: $177.50

📊 Risk Profile:
• R:R Ratio: 2.08:1
• Quality: HIGH

🎯 Vehicle: OPTION_CALL
   • DTE Range: 30-45 days
   • Delta Range: 0.40 to 0.60

📈 Signal Basis:
• Primary: GOLDEN CROSS
• Supporting: MA ALIGNMENT BULLISH
```

**Output Example (Suppressed):**
```
❌ AAPL: No Trades

Suppression Reasons:
• [NO_TREND] ADX 18.5 below trending threshold 25.0
• [RR_UNFAVORABLE] R:R ratio 1.23:1 below minimum 1.5:1
• [VOLATILITY_TOO_HIGH] Volatility regime HIGH (5.2% ATR)
```

---

### 3. `compare_securities` (Multi-Security Analysis)
Compare multiple stocks and identify best setup.

**Parameters:**
- `symbols` (required): List of ticker symbols (max 10)
- `metric` (optional, default "signals"): Comparison metric

**Returns:**
- Ranked securities with scores
- Winner highlighted with trophy emoji

---

### 4. `screen_securities` (Technical Screening)
Filter securities matching criteria from predefined universes.

**Parameters:**
- `universe` (optional, default "sp500"): sp500, nasdaq100, etf_large_cap
- `criteria` (optional): RSI min/max, min_score, min_bullish
- `limit` (optional, default 20): Max results

**Returns:**
- Screened securities matching criteria
- Score, signals, price, RSI for each match

---

## Technical Indicators (50+)

**Moving Averages (12 total):**
- SMA & EMA: 5, 10, 20, 50, 100, 200 periods

**Momentum:**
- RSI (14-period)
- MACD (12/26/9)
- Stochastic (14-period K, 3-period D)

**Volatility:**
- Bollinger Bands (20-period, 2σ)
- ATR (14-period) - used for risk calculations
- Bollinger Band Width

**Trend:**
- ADX (14-period)
- Directional Indicators (+DI, -DI)

**Volume:**
- Volume MA (20, 50 periods)
- OBV (On-Balance Volume)
- Volume ratio

**Price Action:**
- Price change (%, 5-day)
- Distance from MAs

---

## Trading Signals (150+)

### 10 Signal Categories

1. **MA_CROSS**: Golden Cross, Death Cross, short-term MA crosses
2. **MA_TREND**: Moving average alignment patterns
3. **RSI**: Oversold, overbought, divergences
4. **MACD**: Line crossovers, zero crosses, histogram analysis
5. **BOLLINGER**: Band touches, mean reversion
6. **STOCHASTIC**: K-D crosses, oversold/overbought
7. **VOLUME**: Spikes (2x, 3x), volume trends
8. **TREND**: ADX-based trend strength
9. **PRICE_ACTION**: Gap patterns, reversals
10. **ADX**: Trend confirmation, divergences

### Signal Strength Levels
- STRONG_BULLISH (score: 75)
- BULLISH (score: 55)
- NEUTRAL
- BEARISH (score: 55)
- STRONG_BEARISH (score: 75)
- SIGNIFICANT, VERY_SIGNIFICANT, TRENDING

---

## Risk-First Layer Components

### 1. Volatility Regime Classification
Classifies market volatility based on ATR as % of price:
- **LOW**: ATR < 1.5% (quiet markets)
- **MEDIUM**: ATR 1.5-3.0% (normal)
- **HIGH**: ATR > 3.0% (volatile)

### 2. Timeframe Selection
Selects ONE active timeframe:
- **SWING**: 2-10 days (low-med volatility + trend)
- **DAY**: Intraday (medium volatility)
- **SCALP**: Minutes-hours (high volatility)

### 3. Stop-Loss Calculation
ATR-based stops with validation:
- **Swing**: 2.0 ATR
- **Day**: 1.5 ATR
- **Scalp**: 1.0 ATR
- Minimum: 0.5 ATR, Maximum: 3.0 ATR

### 4. Invalidation Detection
Structure-based invalidation levels:
- Support/resistance breaks
- Moving average crosses
- Swing high/low breaks

### 5. Risk-to-Reward Calculation
- Minimum: 1.5:1 ratio
- Preferred: 2.0:1 ratio
- Favorable: >= 1.5:1

### 6. Suppression Logic
7 machine-readable suppression codes:

| Code | Condition |
|------|-----------|
| STOP_TOO_WIDE | Stop > 3 ATR |
| STOP_TOO_TIGHT | Stop < 0.5 ATR |
| RR_UNFAVORABLE | R:R < 1.5:1 |
| NO_CLEAR_INVALIDATION | No structure found |
| VOLATILITY_TOO_HIGH | ATR > 3% of price |
| NO_TREND | ADX < 20 |
| CONFLICTING_SIGNALS | >40% signals conflict |

### 7. Trade Vehicle Selection
Stock-first approach with options suggestions:
- **Stock**: Default for all non-swing
- **Option Call**: Swing trades, bullish, sufficient move
- **Option Put**: Swing trades, bearish, sufficient move
- **Option Spread**: High volatility, defined risk

**Full Option Suggestions Include:**
- DTE range (30-45 days for swing)
- Delta range (0.40-0.60 for calls, -0.60 to -0.40 for puts)
- Spread width specifications

---

## Models

### Signal Analysis Models
- `Signal` (immutable)
- `Indicators` (key indicators only)
- `AnalysisResult` (complete analysis)
- `ComparisonResult`, `ScreeningResult`

### Risk Layer Models (NEW)
**Enums:**
- `Timeframe` (swing, day, scalp)
- `Bias` (bullish, bearish, neutral)
- `RiskQuality` (high, medium, low)
- `VolatilityRegime` (low, medium, high)
- `Vehicle` (stock, option_call, option_put, option_spread)
- `SuppressionCode` (7 codes)

**Data Models (all frozen=True):**
- `RiskMetrics` - ATR, ADX, volatility, trend
- `StopLevel` - Price, distance, validation
- `TargetLevel` - Price, distance
- `RiskReward` - Ratio, favorability
- `InvalidationLevel` - Price, type, description
- `SuppressionReason` - Code, message, thresholds
- `RiskAssessment` - Complete risk evaluation
- `TradePlan` - Actionable trade with full details
- `RiskAnalysisResult` - Final output

---

## Configuration Constants

### Signal Analysis (Existing)
- Indicator periods (MA, RSI, MACD, Bollinger, etc.)
- Thresholds (RSI oversold/overbought, etc.)
- Volume spike levels (2x, 3x)
- ADX trending threshold (25.0)

### Risk Layer (NEW - 20+ Constants)
```
# Volatility
VOLATILITY_LOW_THRESHOLD = 1.5
VOLATILITY_HIGH_THRESHOLD = 3.0

# Stops (ATR multiples)
STOP_MIN_ATR_MULTIPLE = 0.5
STOP_MAX_ATR_MULTIPLE = 3.0
STOP_ATR_SWING = 2.0
STOP_ATR_DAY = 1.5
STOP_ATR_SCALP = 1.0

# Risk-to-Reward
MIN_RR_RATIO = 1.5
PREFERRED_RR_RATIO = 2.0

# Trend
ADX_TRENDING_THRESHOLD = 25.0
ADX_STRONG_TREND_THRESHOLD = 40.0
ADX_NO_TREND_THRESHOLD = 20.0

# Options (Full Suggestions)
OPTION_MIN_EXPECTED_MOVE = 3.0
OPTION_SWING_MIN_DTE = 30
OPTION_SWING_MAX_DTE = 45
OPTION_CALL_DELTA_MIN = 0.40
OPTION_CALL_DELTA_MAX = 0.60
OPTION_PUT_DELTA_MIN = -0.60
OPTION_PUT_DELTA_MAX = -0.40
OPTION_SPREAD_WIDTH_ATR = 1.0

# Suppression
MAX_CONFLICTING_SIGNALS_RATIO = 0.4
```

---

## Technology Stack

**Data & Analysis:**
- `yfinance` - Market data
- `pandas` - DataFrames
- `numpy` - Numerical ops

**API & Protocol:**
- `mcp` (0.9.0+) - Model Context Protocol
- `pydantic` (2.0+) - Data validation
- `cachetools` (5.0+) - TTL caching

**Cloud & AI:**
- `google-generativeai` - Gemini API
- `google-cloud-firestore` - Database
- `google-cloud-pubsub` - Messaging
- `google-cloud-storage` - Storage

**Infrastructure:**
- Terraform - IaC
- Google Cloud Functions - Serverless

**Development:**
- `pytest` - Testing
- `black` - Formatting
- `ruff` - Linting
- `mypy` - Type checking

---

## Entry Points

### 1. Claude Desktop
Configure via `claude_desktop_config.json`:
```bash
python -m technical_analysis_mcp.server
```

### 2. Local CLI
```bash
python run_analysis.py [SYMBOL]
```

### 3. Programmatic
```python
from technical_analysis_mcp.server import analyze_security, get_trade_plan
import asyncio

async def example():
    # Signal analysis
    signals = await analyze_security("AAPL", period="3mo")

    # Trade planning
    trade_plan = await get_trade_plan("AAPL", period="3mo")

asyncio.run(example())
```

### 4. Cloud Function (GCP)
Automated daily analysis via Terraform deployment.

---

## Cost Model

**Current Production:** $0/month
- Cloud Functions: 250 invocations (free tier: 2M)
- Firestore: ~15K ops (free tier: 50K)
- Cloud Scheduler: 1 job (free tier: 3)
- Gemini API: ~450 calls (free tier: unlimited)

**Expansion Potential:** 3-5x capacity, still $0/month

---

## Design Patterns

**Architecture:**
- Protocol-Based Design (6 Protocols)
- Dependency Injection
- Facade Pattern (StockAnalyzer, RiskAssessor)
- Strategy Pattern (Ranking, Risk Qualification)
- Immutable Data (Pydantic frozen dataclasses)

**Code Quality:**
- Full type hints (mypy compatible)
- Custom exception hierarchy
- Comprehensive logging
- Black/Ruff formatted
- pytest framework

---

## Implementation Status

### Phase 1: Core (Complete ✅)
- Models, Protocols, Constants

### Phase 2: Components (Complete ✅)
- Volatility, Timeframe, Stops, Invalidation, R:R, Suppression, Options

### Phase 3: Orchestration (Complete ✅)
- RiskAssessor coordinating all components

### Phase 4: Integration (Complete ✅)
- Server tool, Formatters, Config

### Phase 5: Testing (Ready ✅)
- All code compiles, test framework ready

---

## Key Features

✅ **150+ Trading Signals** with 10 categories
✅ **50+ Technical Indicators** for comprehensive analysis
✅ **Signal Ranking** via rule-based or AI (Gemini 2.0 Flash)
✅ **NEW: Risk-First Layer** - 1-3 trade plans maximum
✅ **Trade Plan Details** - Entry/Stop/Target/Invalidation
✅ **Risk Management** - ATR-based stops, R:R validation
✅ **Machine-Readable Suppression** - 7+ reason codes
✅ **Options Integration** - DTE, delta, spread suggestions
✅ **Single Timeframe** - ONE active (swing/day/scalp)
✅ **Stock Universe Support** - S&P 500, Nasdaq 100, ETFs, Crypto
✅ **TTL Caching** - 5-min default, 100-symbol limit
✅ **MCP Integration** - Claude Desktop support
✅ **Free-Tier Deployment** - $0/month with GCP
✅ **Dual Operating Modes** - Signals OR trade plans

---

## Ideal Use Cases

✅ **Professional Trading Analysis**
- Risk-qualified trade planning with full specifications
- Machine-readable suppression explains unqualified setups

✅ **Signal-Based Strategy Research**
- 150+ signals across 10 categories
- AI ranking via Gemini for priority evaluation
- Historical multi-timeframe analysis

✅ **Portfolio Screening**
- Technical criteria filtering
- Multi-security comparison
- Predefined universes (S&P 500, Nasdaq, crypto)

✅ **Claude Integration**
- Ask Claude for trade ideas using MCP tools
- Combine with other MCP servers for complete analysis
- AI-powered decision support

✅ **Educational**
- Learn technical analysis signals and indicators
- Understand risk management principles
- Explore volatility and trend dynamics

---

## Not Suitable For

❌ High-frequency trading (15+ min delays)
❌ Options pricing (greeks, IV rank not included)
❌ Real-time alerts (insufficient speed)
❌ Regulatory compliance reporting (no audit trail)
❌ Cryptocurrency derivatives (limited data)

---

## Recent Changes (v2.0)

**Major Addition: Risk-First Layer**
- New `risk/` module with 11 files, ~1,700 lines
- 6 Protocol definitions for extensibility
- 15 new Pydantic models for risk data
- New `get_trade_plan` MCP tool
- Machine-readable suppression codes
- Full options vehicle integration

**Integration:**
- Updated `server.py` with new tool
- Enhanced `formatting.py` with 3 new formatters
- Added 20+ config constants
- All backward compatible

**No Breaking Changes:**
- Existing `analyze_security` tool unchanged
- Legacy signal analysis still available
- All existing integrations work as before

---

## Documentation

Comprehensive guides included:
- **RISK_LAYER_PLAN.md** - Implementation architecture
- **IMPLEMENTATION_TEST.md** - Code verification results
- **REPOSITORY_SUMMARY.md** - Original feature summary
- **10+ setup guides** - Installation and deployment
- **GCP optimization guide** - Free-tier strategy

---

## Summary

**mcp-finance1** is a dual-mode financial analysis system that provides both comprehensive technical signal detection (150+) and risk-qualified trade planning (1-3 plans).

**Unique Advantages:**
- Professional risk management layer integrated into signal pipeline
- Machine-readable suppression explains all rejections
- Full options integration with specific DTE/delta suggestions
- Single-timeframe focus (one active mode at a time)
- Zero operational cost on free-tier services
- Clean, maintainable architecture with Protocol-based design
- AI-powered ranking optional (fallback to rule-based)
- Easily extensible for future enhancements

**Two Operating Modes:**
1. **Signal Analysis** - Traditional: 150+ ranked signals
2. **Trade Planning** - Professional: 1-3 actionable plans with risk details

Users can choose the mode that best fits their workflow:
- Signal traders get comprehensive detection and ranking
- Risk managers get actionable plans with full suppression logic
- Both share the same underlying data/indicator/signal pipeline

Suitable for Claude integration, professional trading, research, education, and portfolio analysis.
