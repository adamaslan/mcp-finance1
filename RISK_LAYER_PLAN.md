# Risk-First Layer Implementation Plan

## Overview

Add a Risk-First Layer that transforms 150+ signals into 1-3 actionable Trade Plans. The layer acts as a gate: if risk assessment fails, signals are suppressed with machine-readable reasons.

**New Pipeline:**
```
data → indicators → signals → ranking → RISK QUALIFICATION → trade plan OR suppression
```

---

## New Module Structure

```
src/technical_analysis_mcp/risk/
├── __init__.py           # Package exports
├── models.py             # TradePlan, RiskAssessment, SuppressionReason
├── protocols.py          # RiskQualifier, TimeframeSelector, VehicleSelector
├── risk_assessor.py      # Core orchestrator
├── volatility_regime.py  # LOW/MEDIUM/HIGH classification
├── timeframe_rules.py    # Swing/Day/Scalp selection (1 active)
├── stop_distance.py      # ATR-based stop validation
├── invalidation.py       # Structure-based invalidation detection
├── rr_calculator.py      # Risk-to-reward calculation
├── suppression.py        # Suppression logic with codes
└── option_rules.py       # Stock-first, options as expression
```

---

## Key Models

### TradePlan (Primary Output)
```python
TradePlan {
    symbol: str
    timeframe: "swing" | "day" | "scalp"
    bias: "bullish" | "bearish" | "neutral"
    risk_quality: "high" | "medium" | "low"
    entry_price: float
    stop_price: float
    target_price: float
    invalidation_price: float
    risk_reward_ratio: float
    expected_move_percent: float
    max_loss_percent: float
    vehicle: "stock" | "option_call" | "option_put" | "option_spread"
    vehicle_notes: str | None
    # Full option suggestions (when vehicle is option)
    option_dte_range: tuple[int, int] | None      # e.g., (30, 45)
    option_delta_range: tuple[float, float] | None # e.g., (0.40, 0.60)
    option_spread_width: float | None              # e.g., $5.00
    primary_signal: str
    supporting_signals: tuple[str, ...]
    is_suppressed: bool
    suppression_reasons: tuple[SuppressionReason, ...]
}
```

### SuppressionCode (Machine-Readable)
```python
SuppressionCode:
    STOP_TOO_WIDE          # Stop > 3 ATR
    STOP_TOO_TIGHT         # Stop < 0.5 ATR
    RR_UNFAVORABLE         # R:R < 1.5:1
    NO_CLEAR_INVALIDATION  # No structure for stop
    VOLATILITY_TOO_HIGH    # ATR > 3% of price
    NO_TREND               # ADX < 20
    CONFLICTING_SIGNALS    # >40% signals conflict
```

---

## Configuration Constants (add to config.py)

```python
# Volatility Regime Thresholds
VOLATILITY_LOW_THRESHOLD = 1.5      # ATR < 1.5% = LOW
VOLATILITY_HIGH_THRESHOLD = 3.0     # ATR > 3.0% = HIGH

# Stop Distance (ATR multiples)
STOP_MIN_ATR_MULTIPLE = 0.5
STOP_MAX_ATR_MULTIPLE = 3.0
STOP_ATR_SWING = 2.0
STOP_ATR_DAY = 1.5
STOP_ATR_SCALP = 1.0

# Risk-to-Reward
MIN_RR_RATIO = 1.5
PREFERRED_RR_RATIO = 2.0

# Trend Thresholds
ADX_TRENDING_THRESHOLD = 25.0
ADX_NO_TREND_THRESHOLD = 20.0

# Output Limits
MAX_TRADE_PLANS = 3

# Options (Full Suggestions)
OPTION_MIN_EXPECTED_MOVE = 3.0      # Min 3% move for options
OPTION_SWING_MIN_DTE = 30
OPTION_SWING_MAX_DTE = 45
OPTION_CALL_DELTA_MIN = 0.40        # Min delta for calls
OPTION_CALL_DELTA_MAX = 0.60        # Max delta for calls
OPTION_PUT_DELTA_MIN = -0.60        # Min delta for puts
OPTION_PUT_DELTA_MAX = -0.40        # Max delta for puts
OPTION_SPREAD_WIDTH_ATR = 1.0       # Spread width as ATR multiple
```

---

## Integration Points

### 1. analysis.py Modification
Insert risk layer between ranking and scoring (lines 115-117):

```python
class StockAnalyzer:
    def __init__(
        self,
        use_cache: bool = True,
        use_ai: bool = True,
        enable_risk_layer: bool = True,  # NEW
    ):
        self._risk_assessor = RiskAssessor() if enable_risk_layer else None

    def analyze(
        self,
        symbol: str,
        period: str = "1mo",
        output_mode: str = "risk",  # NEW: "risk" | "legacy"
    ) -> dict[str, Any]:
        # ... existing pipeline ...
        ranked_signals = self._rank_signals(...)

        # NEW: Risk qualification
        if self._risk_assessor and output_mode == "risk":
            return self._risk_assessor.assess(df, ranked_signals, symbol)

        # Legacy path unchanged
        return self._legacy_output(...)
```

### 2. server.py - New MCP Tool (Coexist with existing)
Add `get_trade_plan` tool alongside existing `analyze_security` (both tools available):

```python
Tool(
    name="get_trade_plan",
    description="Get risk-qualified trade plan (1-3 max) or suppression reasons",
    inputSchema={
        "properties": {
            "symbol": {"type": "string"},
            "period": {"type": "string", "default": "1mo"},
        },
        "required": ["symbol"],
    },
)
```

**Reuse Strategy**: The new tool will reuse existing:
- `YFinanceDataFetcher` / `CachedDataFetcher` for data
- `calculate_all_indicators()` for indicators
- `detect_all_signals()` for signal detection
- `rank_signals()` for ranking
- Only add new risk qualification layer on top

### 3. formatting.py - New Formatters
```python
def format_trade_plan(plan: TradePlan) -> str
def format_risk_analysis(result: RiskAnalysisResult) -> str
def format_suppression(reasons: tuple[SuppressionReason, ...]) -> str
```

---

## Implementation Order

### Phase 1: Core Models & Protocols
1. Create `risk/__init__.py`
2. Create `risk/models.py` - All Pydantic models
3. Create `risk/protocols.py` - Protocol definitions
4. Add config constants to `config.py`

### Phase 2: Component Implementations
5. Create `risk/volatility_regime.py` - ATRVolatilityClassifier
6. Create `risk/timeframe_rules.py` - DefaultTimeframeSelector
7. Create `risk/stop_distance.py` - ATRStopCalculator
8. Create `risk/invalidation.py` - StructureInvalidationDetector
9. Create `risk/rr_calculator.py` - DefaultRRCalculator
10. Create `risk/suppression.py` - DefaultSuppressionEvaluator
11. Create `risk/option_rules.py` - DefaultVehicleSelector

### Phase 3: Orchestration
12. Create `risk/risk_assessor.py` - RiskAssessor orchestrator

### Phase 4: Integration
13. Modify `analysis.py` - Add risk layer integration
14. Modify `formatting.py` - Add risk formatters
15. Modify `server.py` - Add `get_trade_plan` tool

### Phase 5: Testing
16. Create `tests/risk/` test directory
17. Unit tests for each component
18. Integration tests for full pipeline

---

## Files to Modify

| File | Changes |
|------|---------|
| `src/technical_analysis_mcp/config.py` | Add risk constants |
| `src/technical_analysis_mcp/analysis.py` | Add risk_assessor integration |
| `src/technical_analysis_mcp/formatting.py` | Add trade plan formatters |
| `src/technical_analysis_mcp/server.py` | Add `get_trade_plan` tool |
| `src/technical_analysis_mcp/__init__.py` | Export risk module |

## New Files to Create

| File | Purpose |
|------|---------|
| `risk/__init__.py` | Package exports |
| `risk/models.py` | Pydantic models (TradePlan, etc.) |
| `risk/protocols.py` | Protocol definitions |
| `risk/risk_assessor.py` | Main orchestrator |
| `risk/volatility_regime.py` | Volatility classification |
| `risk/timeframe_rules.py` | Timeframe selection |
| `risk/stop_distance.py` | Stop validation |
| `risk/invalidation.py` | Invalidation detection |
| `risk/rr_calculator.py` | R:R calculation |
| `risk/suppression.py` | Suppression logic |
| `risk/option_rules.py` | Vehicle selection with full option suggestions (DTE, delta, spread width) |

---

## Backward Compatibility

- **Both tools coexist**: `analyze_security` and `get_trade_plan` available simultaneously
- Existing `analyze_security` tool completely unchanged
- New `get_trade_plan` reuses existing data/indicator/signal pipeline
- No deprecation planned - users choose which tool fits their needs
- Shared codebase minimizes maintenance burden

---

## Success Criteria

1. Users see 1-3 trade plans instead of 150 signals
2. Suppression feels intentional ("No trades - here's why")
3. Each plan has clear entry/stop/target/invalidation
4. R:R is always >= 1.5:1 for qualified trades
5. Options include full suggestions: DTE range (30-45), delta range (0.40-0.60), spread width
6. 40% conflicting signals triggers suppression
7. Both `analyze_security` and `get_trade_plan` tools work independently
8. All existing tests pass (backward compatible)
