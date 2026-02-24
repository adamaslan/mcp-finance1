# Skills Implementation Plan: scan-trades, portfolio-risk, morning-brief

## Overview

Three new MCP skills extend the Risk-First Layer system:

1. **`/scan-trades`** - Automated universe scanning for qualified trade setups (LOW complexity)
2. **`/portfolio-risk`** - Aggregate risk analysis across positions (MEDIUM complexity)
3. **`/morning-brief`** - Daily market briefing with top signals and market analysis (MEDIUM complexity)

All skills are MCP tools that coexist with existing tools (`analyze_security`, `compare_securities`, `screen_securities`, `get_trade_plan`).

---

## Skill 1: `/scan-trades` - Smart Trade Scanner

### Architecture

```
Input: Universe name (sp500, nasdaq100, etf_large_cap, crypto)
  ↓
For each symbol (parallel processing, max 50):
  - Fetch data (cached)
  - Calculate indicators
  - Detect signals
  - Get risk-qualified trade plan
  ↓
Filter results: Only include qualified trades (has_trades=True)
  ↓
Rank by risk quality (HIGH > MEDIUM > LOW)
  ↓
Output: 1-10 actionable trade setups with details
```

### Data Models

```python
# ScanResult
symbol: str
entry_price: float
stop_price: float
target_price: float
risk_reward_ratio: float
risk_quality: RiskQuality  # HIGH | MEDIUM | LOW
timeframe: str  # swing | day | scalp
bias: str  # bullish | bearish | neutral
primary_signal: str
confidence: float  # 0.0 to 1.0 based on signal strength

# ScanOutput
universe: str
total_scanned: int
qualified_trades: list[ScanResult]  # 1-10 best setups
timestamp: str
duration_seconds: float
```

### Files to Create

1. **`src/technical_analysis_mcp/scanners/__init__.py`** - Package exports
2. **`src/technical_analysis_mcp/scanners/trade_scanner.py`** - TradeScanner class
   - `scan_universe()` - Main scanning logic
   - Parallel processing with asyncio.gather()
   - Caching for performance
   - Ranking by risk quality

### Files to Modify

1. **`src/technical_analysis_mcp/server.py`**
   - Add import: `from .scanners.trade_scanner import TradeScanner`
   - Add tool definition: `scan_trades`
   - Add handler in `call_tool()`
   - Implement `async def scan_trades()` function

2. **`src/technical_analysis_mcp/formatting.py`**
   - Add `format_scan_results()` - Display scan results with emoji ranking

### Tool Definition

```python
Tool(
    name="scan_trades",
    description="Scan universe for qualified trade setups (1-10 per universe)",
    inputSchema={
        "type": "object",
        "properties": {
            "universe": {
                "type": "string",
                "default": "sp500",
                "description": "Universe to scan (sp500, nasdaq100, etf_large_cap, crypto)",
            },
            "max_results": {
                "type": "integer",
                "default": 10,
                "description": "Maximum results (1-50)",
            },
        },
        "required": [],
    },
)
```

### Expected Output

```
🔍 Smart Trade Scan - S&P 500

Found 7 qualified setups (scanned 500 securities in 12.3 seconds)

🔥 HIGH QUALITY TRADES (3):
1. AAPL - $185.50 entry | $180.00 stop | $195.00 target
   R:R: 2.17:1 | Bias: BULLISH | Timeframe: SWING
   Signal: GOLDEN_CROSS | Confidence: 89%

2. MSFT - $425.25 entry | $410.00 stop | $445.00 target
   R:R: 1.87:1 | Bias: BULLISH | Timeframe: SWING
   Signal: RSI_OVERSOLD | Confidence: 76%

⚡ MEDIUM QUALITY TRADES (4):
...

Scan completed in 12.3 seconds
Cache: 2 hits, 498 fetches
```

---

## Skill 2: `/portfolio-risk` - Portfolio Risk Assessment

### Architecture

```
Input: List of positions [symbol, shares/contracts, entry_price]
  ↓
For each position:
  - Get current price and indicators
  - Calculate max loss per position
  - Calculate stop level from risk layer
  - Assess volatility and trend
  ↓
Aggregate across portfolio:
  - Total portfolio value
  - Total max loss (aggregate risk)
  - Risk as % of portfolio
  - Correlation matrix (if 5+ positions)
  - Sector concentration
  ↓
Output: Portfolio risk dashboard
```

### Data Models

```python
# PositionRisk
symbol: str
shares: float
entry_price: float
current_price: float
unrealized_pnl: float
unrealized_percent: float
stop_level: float
max_loss_dollar: float
max_loss_percent: float
risk_quality: RiskQuality
timeframe: str

# PortfolioRiskAssessment
total_value: float
total_max_loss: float
risk_percent_of_portfolio: float
positions: list[PositionRisk]
sector_concentration: dict[str, float]  # sector -> % of portfolio
correlation_matrix: dict[str, dict[str, float]] | None  # if 5+ positions
overall_risk_level: str  # LOW | MEDIUM | HIGH | CRITICAL
hedge_suggestions: list[str]  # e.g., "Add QQQ put for tech hedge"
timestamp: str
```

### Files to Create

1. **`src/technical_analysis_mcp/portfolio/__init__.py`** - Package exports
2. **`src/technical_analysis_mcp/portfolio/portfolio_risk.py`** - PortfolioRiskAssessor class
   - `assess_positions()` - Main assessment logic
   - Sector lookup (mapping symbol to sector)
   - Correlation calculation (numpy/scipy)
   - Risk aggregation and hedging suggestions

3. **`src/technical_analysis_mcp/portfolio/sector_mapping.py`** - SECTOR_MAPPING dict
   ```python
   SECTOR_MAPPING = {
       "AAPL": "Technology",
       "MSFT": "Technology",
       "JNJ": "Healthcare",
       ...  # 500+ mappings for S&P 500
   }
   ```

### Files to Modify

1. **`src/technical_analysis_mcp/server.py`**
   - Add import: `from .portfolio.portfolio_risk import PortfolioRiskAssessor`
   - Add tool definition: `portfolio_risk`
   - Add handler in `call_tool()`
   - Implement `async def portfolio_risk()` function

2. **`src/technical_analysis_mcp/formatting.py`**
   - Add `format_portfolio_risk()` - Display portfolio dashboard

### Tool Definition

```python
Tool(
    name="portfolio_risk",
    description="Assess aggregate risk across your positions",
    inputSchema={
        "type": "object",
        "properties": {
            "positions": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "symbol": {"type": "string"},
                        "shares": {"type": "number"},
                        "entry_price": {"type": "number"},
                    },
                    "required": ["symbol", "shares", "entry_price"],
                },
                "description": "List of open positions",
            },
        },
        "required": ["positions"],
    },
)
```

### Expected Output

```
📊 Portfolio Risk Assessment

Portfolio Value: $185,450
Maximum Loss: $18,200 (9.8% of portfolio)
Risk Level: 🟡 MEDIUM

POSITION BREAKDOWN:
1. AAPL (100 shares @ $185.50)
   Current: $18,550 | Max Loss: $500 | Risk: 2.7%
   Stop: $180.00 | Trend: STRONG UP | Quality: HIGH

2. MSFT (50 shares @ $425.25)
   Current: $21,262 | Max Loss: $750 | Risk: 3.5%
   Stop: $410.00 | Trend: MODERATE UP | Quality: MEDIUM

3. JNJ (75 shares @ $160.00)
   Current: $12,000 | Max Loss: $600 | Risk: 5.0%
   Stop: $152.00 | Trend: WEAK | Quality: LOW

SECTOR CONCENTRATION:
• Technology: 47.6% (⚠️ Concentrated)
• Healthcare: 23.4%
• Financials: 12.0%
• Energy: 8.2%
• Consumer: 8.8%

HEDGING SUGGESTIONS:
• Add QQQ put (3-month) to hedge tech exposure
• Consider selling AAPL call to reduce max loss
• JNJ stop is too tight - increase to $156 for better risk:reward

Correlation Risk: None detected (portfolio is well-diversified)
```

---

## Skill 3: `/morning-brief` - Daily Market Briefing

### Architecture

```
Input: (optional) Watchlist symbols, market region
  ↓
Market Status Check:
  - US/International market hours
  - Market close prices (previous)
  - Futures levels
  - Market sentiment (VIX, Put/Call ratio)
  ↓
For top 10 watchlist symbols:
  - Calculate top 5 signals
  - Current price and change
  - Risk assessment
  - Key levels (support/resistance)
  ↓
Economic Calendar:
  - Today's economic events
  - Expected releases
  - Previous and forecast values
  ↓
Sector Leaders/Losers:
  - Top 3 gainers
  - Top 3 losers
  - Sector rotation signals
  ↓
Output: Consolidated briefing (markdown)
```

### Data Models

```python
# MarketStatus
market_status: str  # OPEN | CLOSED | PRE_MARKET | AFTER_HOURS
current_time: str
market_hours_remaining: str
previous_close: float
futures_es: dict  # ES futures data
futures_nq: dict  # NQ futures data
vix: float
put_call_ratio: float
market_sentiment: str  # BULLISH | NEUTRAL | BEARISH

# EconomicEvent
timestamp: str
event_name: str
importance: str  # HIGH | MEDIUM | LOW
forecast: float | str
previous: float | str
actual: float | str | None

# WatchlistSignal
symbol: str
price: float
change_percent: float
top_signals: list[str]  # Top 3-5 signals
risk_assessment: str  # TRADE | HOLD | AVOID
key_support: float
key_resistance: float

# MorningBriefOutput
timestamp: str
market_status: MarketStatus
economic_events: list[EconomicEvent]
watchlist_signals: list[WatchlistSignal]
sector_leaders: list[dict]
sector_losers: list[dict]
key_themes: list[str]  # e.g., ["Tech weakness", "Financials rallying"]
```

### Files to Create

1. **`src/technical_analysis_mcp/briefing/__init__.py`** - Package exports
2. **`src/technical_analysis_mcp/briefing/morning_briefer.py`** - MorningBriefGenerator class
   - `generate_brief()` - Main generation logic
   - `_get_market_status()` - Market hours and futures
   - `_get_economic_events()` - Fetch from economic calendar API
   - `_analyze_watchlist()` - Signal analysis for symbols
   - `_get_sector_movers()` - Top gainers/losers
   - `_detect_market_themes()` - Key market narratives

3. **`src/technical_analysis_mcp/briefing/economic_calendar.py`** - EconomicCalendar class
   - Fetch from trading economics API or hardcoded data
   - Parse events for today
   - Store importance levels

4. **`src/technical_analysis_mcp/briefing/market_status.py`** - MarketStatusChecker class
   - Get current market hours (US/EU/Asia)
   - Fetch futures levels (ES, NQ, YM)
   - Get VIX and put/call ratio

### Files to Modify

1. **`src/technical_analysis_mcp/server.py`**
   - Add import: `from .briefing.morning_briefer import MorningBriefGenerator`
   - Add tool definition: `morning_brief`
   - Add handler in `call_tool()`
   - Implement `async def morning_brief()` function

2. **`src/technical_analysis_mcp/formatting.py`**
   - Add `format_morning_brief()` - Markdown formatted briefing

### Tool Definition

```python
Tool(
    name="morning_brief",
    description="Generate daily market briefing with signals and market conditions",
    inputSchema={
        "type": "object",
        "properties": {
            "watchlist": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Symbols to include (default: top 10 from S&P 500)",
            },
            "market_region": {
                "type": "string",
                "default": "US",
                "description": "Market region (US, EU, ASIA)",
            },
        },
        "required": [],
    },
)
```

### Expected Output

```
# 📈 Morning Market Brief - 2024-01-15

**Market Status**: 🟢 OPEN (6 hours 23 minutes remaining)
- Previous Close: SPY $485.50
- Futures: ES +0.35% | NQ +0.52% | VIX 14.2

---

## 📊 Economic Calendar

**HIGH IMPORTANCE (Today)**
• 08:30 ET - CPI Year-over-Year (Forecast: 3.2% | Previous: 3.1%)
• 10:00 ET - Consumer Sentiment Index (Forecast: 72.0 | Previous: 71.5)

**MEDIUM IMPORTANCE**
• 14:00 ET - Fed Speaker (Inflation Commentary)

---

## 🎯 Watchlist Signals (Top 10)

### 🔥 TRADE - AAPL ($185.50 +1.2%)
- Signals: GOLDEN_CROSS | MA_ALIGNMENT_BULLISH | RSI_OVERSOLD
- Risk Assessment: HIGH QUALITY (R:R 2.17:1)
- Support: $182.00 | Resistance: $190.00
- Action: **BUY on support bounce**

### ⚡ HOLD - MSFT ($425.25 +0.8%)
- Signals: RSI_NEUTRAL | MACD_POSITIVE
- Risk Assessment: MEDIUM QUALITY (R:R 1.87:1)
- Support: $420.00 | Resistance: $435.00
- Action: **Wait for pullback to support**

### ⚠️ AVOID - NVDA ($485.20 -2.1%)
- Signals: BEARISH_CROSS | RSI_OVERBOUGHT
- Risk Assessment: SUPPRESSED (volatility too high)
- Support: $475.00 | Resistance: $500.00
- Action: **Avoid until trend clarifies**

---

## 🏆 Sector Leaders/Losers

**Top Gainers**: Technology +2.1%, Financials +1.5%, Healthcare +0.8%
**Top Losers**: Energy -1.2%, Utilities -0.5%, Consumer -0.3%

---

## 🎪 Key Market Themes

1. **Tech Strength** - AI enthusiasm continues, semi strength
2. **Rate Sensitivity** - Bonds rallying on inflation hopes
3. **Earnings Season Prep** - Financial earnings start this week
4. **Dollar Weakness** - USD index down 0.7% supporting commodities

---

**Generated**: 2024-01-15 09:45 ET | Symbols Analyzed: 10
```

---

## Implementation Order

### Phase 1: scan-trades (1-2 hours)
1. Create `scanners/__init__.py`
2. Create `scanners/trade_scanner.py`
3. Modify `server.py` - Add tool definition and handler
4. Modify `formatting.py` - Add formatter
5. Test compilation and basic functionality

### Phase 2: portfolio-risk (2-3 hours)
6. Create `portfolio/__init__.py`
7. Create `portfolio/portfolio_risk.py`
8. Create `portfolio/sector_mapping.py`
9. Modify `server.py` - Add tool definition and handler
10. Modify `formatting.py` - Add formatter
11. Test compilation and basic functionality

### Phase 3: morning-brief (3-4 hours)
12. Create `briefing/__init__.py`
13. Create `briefing/morning_briefer.py`
14. Create `briefing/market_status.py`
15. Create `briefing/economic_calendar.py`
16. Modify `server.py` - Add tool definition and handler
17. Modify `formatting.py` - Add formatter
18. Test compilation and basic functionality

### Phase 4: Integration & Testing
19. Verify all tools load in MCP server
20. Create `SKILLS_IMPLEMENTATION_TEST.md` with results
21. Update `REPOSITORY_SUMMARY_v3.md` with new skills

---

## Backward Compatibility

- All 3 skills coexist with existing tools
- No modifications to existing tool behavior
- `analyze_security`, `compare_securities`, `screen_securities`, `get_trade_plan` all unchanged
- New tools are additive only
- Shared codebase leverages existing indicators, signals, and risk assessment

---

## Success Criteria

1. ✅ `/scan-trades` finds 1-10 qualified setups per universe, ranked by quality
2. ✅ `/portfolio-risk` calculates aggregate risk, sector concentration, hedge suggestions
3. ✅ `/morning-brief` generates daily market summary with watchlist signals
4. ✅ All 3 tools compile without errors
5. ✅ All tools integrate properly with MCP server
6. ✅ Formatters produce readable output for each tool
7. ✅ Existing tools remain fully functional (backward compatible)
8. ✅ Documentation complete with expected outputs
