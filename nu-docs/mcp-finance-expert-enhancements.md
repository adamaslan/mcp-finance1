# MCP Finance: Expert Enhancements for All 9 Servers

**Document Version**: 1.0
**Date**: 2026-01-29
**Author**: Finance Expert Analysis
**Purpose**: Professional enhancements to make MCP Finance a institutional-grade trading platform

---

## Executive Summary

This document provides **2 expert-level enhancements for each of the 9 MCP servers**, designed from the perspective of a seasoned quantitative trader and risk manager. Each enhancement addresses real-world trading needs, institutional best practices, and edge cases that separate amateur tools from professional-grade platforms.

**Key Themes Across All Enhancements:**
- **Regime Awareness**: Markets behave differently in bull/bear/sideways regimes
- **Multi-Timeframe Confirmation**: Professional traders never trust a single timeframe
- **Risk-First Thinking**: Capital preservation is paramount
- **Liquidity Awareness**: Best signals mean nothing in illiquid markets
- **Institutional Patterns**: Smart money leaves footprints

---

## 1. `analyze_security` - Technical Analysis Engine

### Enhancement 1.1: Market Regime Detection & Regime-Adaptive Indicators

**Problem:**
Technical indicators optimized for trending markets perform poorly in choppy/sideways markets, and vice versa. RSI oversold signals work great in uptrends but can be death traps in downtrends.

**Solution:**
Implement automatic market regime classification that adjusts indicator interpretation:

```python
class MarketRegime(str, Enum):
    STRONG_UPTREND = "strong_uptrend"      # ADX > 30, price > 200 SMA, rising
    UPTREND = "uptrend"                     # ADX 20-30, price > 200 SMA
    SIDEWAYS = "sideways"                   # ADX < 20
    DOWNTREND = "downtrend"                 # ADX 20-30, price < 200 SMA
    STRONG_DOWNTREND = "strong_downtrend"   # ADX > 30, price < 200 SMA, falling
    DISTRIBUTION = "distribution"            # High volume, narrowing range, topping pattern
    ACCUMULATION = "accumulation"            # High volume, narrowing range, basing pattern

@dataclass
class RegimeAdaptiveSignal:
    """Signal with regime-specific interpretation."""

    signal_name: str
    raw_value: float
    regime: MarketRegime
    regime_quality: str  # "EXCELLENT", "GOOD", "POOR", "AVOID"
    regime_notes: str

    # Example: RSI 30 in STRONG_UPTREND = "EXCELLENT" (buy dip)
    #          RSI 30 in STRONG_DOWNTREND = "AVOID" (falling knife)

def detect_regime(df: pd.DataFrame) -> MarketRegime:
    """Detect current market regime using multi-factor analysis.

    Factors:
    - Trend: 50/200 SMA relationship
    - Strength: ADX level
    - Momentum: Rate of change
    - Volume: Distribution vs accumulation
    - Volatility: ATR expansion/contraction
    """
    # Implementation...
    pass

def interpret_signal_by_regime(
    signal: Signal,
    regime: MarketRegime,
) -> RegimeAdaptiveSignal:
    """Adjust signal quality based on regime."""
    # RSI oversold in uptrend = high quality
    # RSI oversold in downtrend = low quality (knife catch)
    # MACD cross in sideways = low quality (whipsaw)
    # MACD cross in strong trend = high quality
    pass
```

**Finance Expert Rationale:**
- **Real-world traders check regime first**: "Is this a trending or mean-reverting market?"
- **Prevents catastrophic errors**: Buying RSI oversold in a waterfall decline
- **Improves win rate**: Signals are only actionable in appropriate regimes
- **Institutional standard**: All quant funds have regime filters

**Implementation Impact:**
- Add `regime` field to analysis output
- Add `regime_quality` to each signal
- Suppress signals with "POOR" or "AVOID" quality unless user overrides
- Show regime transition warnings (e.g., "Entering distribution phase")

---

### Enhancement 1.2: Smart Money Flow Analysis (Order Flow Proxy)

**Problem:**
Retail traders see price and volume. Institutional traders see **who** is buying/selling and **at what conviction level**. Current system lacks order flow intelligence.

**Solution:**
Implement "footprint analysis" using volume-weighted price action to detect smart money accumulation/distribution:

```python
@dataclass
class SmartMoneyAnalysis:
    """Order flow intelligence from price/volume patterns."""

    # Accumulation/Distribution
    accumulation_score: float  # 0-100
    distribution_score: float  # 0-100
    smart_money_bias: str  # "ACCUMULATING", "DISTRIBUTING", "NEUTRAL"

    # Volume Profile Insights
    high_volume_nodes: list[float]  # Price levels with high volume (support/resistance)
    low_volume_nodes: list[float]   # Price levels with gaps (price likely to pass through)
    point_of_control: float         # Price with highest volume (magnet)

    # Order Flow Signals
    absorption_detected: bool       # Large volume, small price move (institutions absorbing)
    exhaustion_detected: bool       # Climactic volume at extreme (reversal warning)
    hidden_orders: list[str]        # "Iceberg detected at $185" (large hidden liquidity)

    # Dark Pool / Block Trade Indicators
    unusual_block_trades: int       # Count of suspiciously large single candles
    block_trade_direction: str      # "BUY_SIDE", "SELL_SIDE", "NEUTRAL"

    # Smart Money Behavior
    smart_money_notes: list[str]
    # "Large buyers stepped in at $180 - institutional support"
    # "Distribution detected: selling into strength at $195"
    # "Absorption zone $182-$184 - strong hands accumulating"

def analyze_smart_money(df: pd.DataFrame) -> SmartMoneyAnalysis:
    """Detect institutional activity patterns.

    Techniques:
    1. Volume Profile Analysis:
       - High volume at lows = accumulation
       - High volume at highs = distribution

    2. Price-Volume Divergence:
       - Rising price, falling volume = weak hands buying (distribution)
       - Falling price, falling volume = capitulation ending (accumulation)

    3. Order Flow Imbalances:
       - Large volume, small range = absorption (institutions stepping in)
       - Small volume, large range = no interest (avoid)

    4. Hidden Orders (Iceberg Detection):
       - Repeated tests of price level with high volume but no breakout
       - Suggests large hidden sell wall (resistance) or bid (support)

    5. Block Trade Detection:
       - Single candles with volume > 3x average = institutional block
       - Direction matters: blocks at lows = accumulation, at highs = distribution
    """
    pass

def detect_absorption_zones(df: pd.DataFrame) -> list[tuple[float, float]]:
    """Find price ranges where institutions are absorbing supply/demand.

    Absorption characteristics:
    - Multiple tests of price level
    - High volume
    - Small price movement (price keeps bouncing back)
    - Indicates strong institutional interest

    Returns:
        List of (low, high) price ranges where absorption detected
    """
    pass
```

**Finance Expert Rationale:**
- **Follow the smart money**: Retail traders lose when fighting institutions
- **Volume tells the truth**: Price can be manipulated, volume cannot (as easily)
- **Absorption zones = high probability**: When institutions step in, price tends to respect those levels
- **Dark pool activity matters**: 40%+ of US equity volume trades off-exchange
- **Prevents bad entries**: Avoid buying into distribution or selling into accumulation

**Implementation Impact:**
- Add `smart_money` section to analysis output
- Highlight absorption zones as high-confidence support/resistance
- Warn if trying to buy into distribution or sell into accumulation
- Show unusual block trade activity (may indicate insider knowledge)

---

## 2. `compare_securities` - Multi-Asset Comparison

### Enhancement 2.1: Relative Strength Comparison (Sector & Market Relative)

**Problem:**
Absolute performance means little without context. A stock up 5% in a market up 10% is actually underperforming (relative weakness).

**Solution:**
Implement dual-layer relative strength analysis:

```python
@dataclass
class RelativeStrengthAnalysis:
    """Relative performance vs sector and market."""

    # Absolute Performance
    symbol: str
    absolute_return_1w: float
    absolute_return_1m: float
    absolute_return_3m: float

    # Relative to Sector
    sector: str  # "Technology", "Financials", etc.
    sector_etf: str  # "XLK", "XLF", etc.
    relative_strength_sector: float  # > 1.0 = outperforming sector
    sector_rank_percentile: float  # 0-100, where this stock ranks in sector

    # Relative to Market
    market_benchmark: str  # "SPY", "QQQ", etc.
    relative_strength_market: float  # > 1.0 = outperforming market
    market_beta: float  # Stock volatility relative to market

    # Relative Momentum
    rs_trend: str  # "ACCELERATING", "DECELERATING", "REVERSING"
    rs_quality: str  # "LEADER", "LAGGARD", "RECOVERING", "DETERIORATING"

    # Comparative Signals
    best_for_trade: str  # Which comparison symbol is best trade right now
    rotation_signal: Optional[str]  # "ROTATE_INTO" or "ROTATE_OUT_OF"

    # Professional Notes
    notes: list[str]
    # "AAPL showing relative strength vs XLK - sector leader"
    # "AAPL underperforming SPY despite absolute gain - distribution warning"
    # "Sector rotation from Growth to Value detected"

def calculate_relative_strength(
    symbol_df: pd.DataFrame,
    benchmark_df: pd.DataFrame,
    period: int = 60,  # 60 days = 3 months
) -> float:
    """Calculate Mansfield Relative Strength.

    RS = (Symbol Price / Symbol MA) / (Benchmark Price / Benchmark MA)

    RS > 1.0 = Outperforming (buy)
    RS < 1.0 = Underperforming (sell/avoid)
    RS trend = Even better signal than absolute RS

    Args:
        symbol_df: Stock OHLCV data
        benchmark_df: Sector or market OHLCV data
        period: Moving average period for normalization

    Returns:
        Relative strength ratio
    """
    pass

def detect_sector_rotation(
    symbols: list[str],
    period: str = "1mo",
) -> dict[str, Any]:
    """Detect sector rotation patterns across compared symbols.

    Rotation Patterns:
    - "Risk-On": Growth > Value, Tech > Financials, Small > Large
    - "Risk-Off": Value > Growth, Utilities > Tech, Large > Small
    - "Late Cycle": Financials strong, Industrials weak
    - "Early Cycle": Materials strong, Utilities weak

    Returns:
        Rotation analysis with recommended sectors
    """
    pass
```

**Finance Expert Rationale:**
- **Professional traders trade relative strength**: Beat the market, not just make money
- **Sector rotation drives performance**: 70%+ of stock returns come from sector selection
- **Prevents false confidence**: Stock up 3% in market up 5% = you're losing
- **Identifies true leaders**: Leaders lead in corrections (high RS) = safer holdings
- **Rotation timing**: Catching sector rotation early = massive alpha

**Implementation Impact:**
- Add `relative_strength` section to comparison output
- Rank symbols by RS, not just absolute return
- Highlight sector rotation signals ("Rotate from Tech to Financials")
- Show which symbol is "market leader" (highest RS + best momentum)

---

### Enhancement 2.2: Correlation & Pairs Trading Opportunities

**Problem:**
Comparing securities without understanding their correlation misses arbitrage opportunities and portfolio risk.

**Solution:**
Implement correlation analysis and pairs trading signal generation:

```python
@dataclass
class CorrelationAnalysis:
    """Correlation and pairs trading analysis."""

    # Correlation Matrix
    correlation_matrix: dict[tuple[str, str], float]  # All symbol pairs
    highly_correlated: list[tuple[str, str, float]]  # Correlation > 0.7
    negatively_correlated: list[tuple[str, str, float]]  # Correlation < -0.3

    # Pairs Trading Opportunities
    pairs_candidates: list[PairsTrade]

    # Portfolio Risk Insights
    diversification_score: float  # 0-100, higher = better diversification
    concentration_risk: str  # "HIGH", "MODERATE", "LOW"
    hedging_suggestions: list[str]
    # "Long AAPL + Short MSFT = tech-neutral bet"
    # "Low correlation between AAPL and JPM = good diversification"

    # Cointegration (for pairs trading)
    cointegrated_pairs: list[tuple[str, str, float]]  # Statistically bound pairs

@dataclass
class PairsTrade:
    """Pairs trading opportunity."""

    symbol_long: str  # Undervalued symbol
    symbol_short: str  # Overvalued symbol
    spread_zscore: float  # Current spread in standard deviations
    entry_signal: bool  # True if spread is extreme (good entry)
    target_spread: float  # Expected mean reversion level
    stop_spread: float  # Stop loss if spread widens further

    # Statistical Backing
    correlation: float  # Historical correlation
    cointegration_pvalue: float  # < 0.05 = statistically cointegrated
    half_life: int  # Days for spread to mean-revert

    # Risk Metrics
    spread_volatility: float  # How much spread fluctuates
    expected_return: float  # % return if spread reverts to mean
    max_drawdown_hist: float  # Worst historical spread widening

    notes: list[str]
    # "AAPL/MSFT spread at 2.3 sigma - overbought AAPL vs MSFT"
    # "Historical mean reversion in 12 days (half-life)"
    # "7% expected return to spread mean"

def detect_pairs_opportunities(
    symbols: list[str],
    dfs: dict[str, pd.DataFrame],
    lookback: int = 252,  # 1 year
) -> list[PairsTrade]:
    """Detect statistical arbitrage opportunities via pairs trading.

    Process:
    1. Find cointegrated pairs (statistically bound)
    2. Calculate current spread z-score
    3. Identify extreme spreads (entry opportunities)
    4. Calculate expected returns and risks

    Classic Example:
    - PEP vs KO (both cola companies, similar fundamentals)
    - When spread deviates, mean reversion trade available
    - Long underperformer, short outperformer
    - Profit when spread normalizes (market-neutral)

    Args:
        symbols: List of symbols to analyze
        dfs: DataFrame for each symbol
        lookback: Historical data period

    Returns:
        List of actionable pairs trades
    """
    pass

def calculate_portfolio_concentration(
    symbols: list[str],
    correlation_matrix: dict[tuple[str, str], float],
) -> float:
    """Calculate portfolio diversification score.

    High correlation = low diversification = high risk

    Returns:
        Score 0-100, where 100 = perfectly diversified
    """
    pass
```

**Finance Expert Rationale:**
- **Correlation = hidden risk**: Diversified on paper, correlated in crashes
- **Pairs trading = market-neutral alpha**: Make money regardless of market direction
- **Cointegration > correlation**: Statistical mean reversion is tradeable
- **Hedge fund staple**: Pairs trading is bread-and-butter for quant funds
- **Risk management**: Understanding correlation prevents portfolio blowups

**Implementation Impact:**
- Add `correlation` and `pairs_trades` to comparison output
- Highlight pairs trade opportunities with expected returns
- Warn if selected symbols are highly correlated (concentration risk)
- Suggest hedging pairs for risk reduction

---

## 3. `screen_securities` - Market Screening

### Enhancement 3.1: Liquidity-Aware Filtering

**Problem:**
Screens return stocks that look great technically but can't be traded due to low liquidity (wide spreads, slippage, difficulty exiting).

**Solution:**
Implement multi-dimensional liquidity analysis:

```python
@dataclass
class LiquidityMetrics:
    """Comprehensive liquidity assessment."""

    symbol: str

    # Volume Metrics
    avg_daily_volume_20d: float
    avg_daily_dollar_volume: float  # Volume * Price (more important than share volume)
    volume_trend: str  # "INCREASING", "DECREASING", "STABLE"

    # Spread Metrics
    avg_bid_ask_spread_pct: float  # % spread (lower = more liquid)
    spread_cost_per_100k: float  # $ cost to trade $100k position

    # Depth Metrics
    market_depth_score: float  # 0-100, how deep the order book is
    slippage_estimate_1pct: float  # Est. slippage to move price 1%

    # Trading Difficulty
    liquidity_tier: str  # "TIER_1" (easy), "TIER_2" (moderate), "TIER_3" (difficult), "ILLIQUID"
    max_safe_position_size: float  # $ size before moving market
    estimated_exit_time: str  # "< 1 day", "2-3 days", "> 1 week"

    # Warnings
    liquidity_warnings: list[str]
    # "Low volume: May experience significant slippage"
    # "Wide spreads: 0.5% transaction cost"
    # "Position size > 5% of daily volume - may move market"

    # Institutional Accessibility
    institutional_tradeable: bool  # Can institutions trade this size?
    retail_friendly: bool  # Suitable for retail traders?

def assess_liquidity(
    symbol: str,
    df: pd.DataFrame,
    position_size_usd: float = 100_000,
) -> LiquidityMetrics:
    """Comprehensive liquidity assessment.

    Liquidity Factors:
    1. Dollar Volume = Price * Volume (most important)
       - $10M/day+ = institutional grade
       - $1M-$10M/day = retail accessible
       - < $1M/day = risky for anything but small positions

    2. Relative Volume:
       - Your position / Daily volume < 5% = safe
       - > 10% = you ARE the market (avoid)

    3. Spread as % of price:
       - < 0.1% = excellent
       - 0.1-0.5% = acceptable
       - > 0.5% = expensive

    4. Volume trend:
       - Increasing = improving liquidity (good)
       - Decreasing = drying up liquidity (warning)

    Args:
        symbol: Ticker symbol
        df: OHLCV data
        position_size_usd: Intended position size

    Returns:
        Comprehensive liquidity metrics
    """
    pass

def filter_by_liquidity(
    symbols: list[str],
    min_dollar_volume: float = 1_000_000,  # $1M minimum
    max_spread_pct: float = 0.5,  # 0.5% maximum spread
    position_size_usd: float = 100_000,
    max_market_impact: float = 0.05,  # Max 5% of daily volume
) -> list[str]:
    """Filter symbols by liquidity requirements.

    Returns only symbols that meet ALL criteria:
    - Sufficient dollar volume
    - Acceptable spreads
    - Can trade position without moving market
    """
    pass
```

**Finance Expert Rationale:**
- **Liquidity is everything**: Best signal useless if you can't enter/exit cleanly
- **Hidden cost of illiquidity**: Slippage and spreads destroy returns
- **Position sizing matters**: $10k position vs $1M position have different liquidity needs
- **Professional requirement**: No institutional fund trades illiquid stocks
- **Prevents disasters**: Getting stuck in illiquid stock during crash = total loss

**Implementation Impact:**
- Add `liquidity_tier` filter to screening criteria
- Show estimated transaction costs for each result
- Warn if user's intended position size is too large for stock
- Automatically exclude illiquid stocks unless explicitly requested

---

### Enhancement 3.2: Fundamental Overlay - Catalyst & Earnings Awareness

**Problem:**
Pure technical screens miss fundamental catalysts that can override technical patterns (earnings, FDA approvals, merger rumors, regulatory changes).

**Solution:**
Integrate fundamental calendar awareness into technical screening:

```python
@dataclass
class CatalystAwareness:
    """Fundamental catalyst overlay for technical analysis."""

    symbol: str

    # Earnings Calendar
    next_earnings_date: Optional[datetime]
    days_until_earnings: Optional[int]
    earnings_timing: str  # "PRE-EARNINGS" (<7 days), "POST-EARNINGS" (<3 days), "CLEAR"

    # Earnings Volatility
    historical_earnings_moves: list[float]  # Past 4 quarters % moves
    avg_earnings_move: float  # Average move on earnings
    implied_earnings_move: float  # Options market expectation

    # Economic Events
    upcoming_events: list[EconomicEvent]  # Fed meetings, CPI, NFP, etc.
    sector_specific_events: list[str]  # "FDA decision", "Clinical trial results"

    # Ex-Dividend
    next_ex_dividend_date: Optional[datetime]
    dividend_yield: float

    # Trading Recommendations
    pre_earnings_tradeable: bool  # Safe to enter before earnings?
    post_earnings_tradeable: bool  # Good entry after earnings?
    earnings_play_type: Optional[str]  # "LONG_VOLATILITY", "SHORT_VOLATILITY", "AVOID"

    # Risk Warnings
    catalyst_warnings: list[str]
    # "Earnings in 3 days - high volatility risk"
    # "FDA decision pending - binary outcome"
    # "Ex-dividend tomorrow - expect gap down"
    # "FOMC meeting this week - macro risk"

@dataclass
class EconomicEvent:
    """Economic or corporate event that could impact stock."""

    event_type: str  # "EARNINGS", "FDA", "FOMC", "CPI", etc.
    event_date: datetime
    importance: str  # "HIGH", "MEDIUM", "LOW"
    expected_impact: str  # "BULLISH", "BEARISH", "NEUTRAL", "UNKNOWN"
    notes: str

def add_catalyst_awareness(
    symbol: str,
    analysis: dict[str, Any],
) -> dict[str, Any]:
    """Overlay fundamental catalysts onto technical analysis.

    Integration Points:
    1. Pre-Earnings:
       - Suppress breakout signals (false breakout risk)
       - Flag mean-reversion setups (volatility crush post-earnings)
       - Recommend waiting for earnings clarity

    2. Post-Earnings:
       - Highlight earnings gap fills (technical reversion)
       - Identify new trends post-earnings
       - Adjust stop-loss for earnings volatility

    3. Dividend Ex-Date:
       - Expect price drop = dividend amount
       - Adjust technical levels for ex-dividend
       - Note increased put activity (dividend capture)

    4. Macro Events (Fed, CPI):
       - Increase caution in high-beta stocks
       - Prefer defensive sectors pre-event
       - Wait for volatility to settle

    Returns:
        Enhanced analysis with catalyst overlay
    """
    pass

def calculate_earnings_play_strategy(
    symbol: str,
    df: pd.DataFrame,
    days_to_earnings: int,
    implied_move: float,
) -> str:
    """Recommend earnings play strategy based on setup.

    Strategies:
    - "LONG_VOLATILITY": Buy straddle/strangle (expect big move)
    - "SHORT_VOLATILITY": Sell premium (expect muted move)
    - "BREAKOUT_POST": Wait for earnings, then trade breakout
    - "AVOID": Too risky, sit out

    Factors:
    - Technical setup (trending vs ranging)
    - Implied move vs historical move (over/under priced)
    - Option premium levels (expensive vs cheap)
    """
    pass
```

**Finance Expert Rationale:**
- **Earnings trump technicals**: Most explosive moves happen at earnings
- **Timing is everything**: Perfect technical setup + earnings in 2 days = disaster waiting
- **Volatility crush is real**: Buying calls before earnings = theta decay hell
- **Smart traders trade catalysts**: Earnings, FDA, Fed decisions drive 80% of big moves
- **Risk management**: Knowing when NOT to trade is as important as knowing when to trade

**Implementation Impact:**
- Add `catalyst_warnings` to screening output
- Filter option: "Exclude stocks with earnings in next 7 days"
- Show implied earnings move vs historical average (value opportunity?)
- Recommend waiting for clarity before entering position

---

## 4. `get_trade_plan` - Trade Plan Generation

### Enhancement 4.1: Multi-Timeframe Trade Plan Validation

**Problem:**
Single-timeframe trade plans miss context. A daily chart bull signal on a weekly downtrend is a weak setup.

**Solution:**
Implement multi-timeframe validation framework:

```python
@dataclass
class MultiTimeframePlan:
    """Trade plan validated across multiple timeframes."""

    symbol: str
    primary_timeframe: str  # User's requested timeframe (e.g., "1d")

    # Timeframe Analysis
    weekly_bias: str  # "BULLISH", "BEARISH", "NEUTRAL"
    daily_bias: str
    hourly_bias: str  # For day traders

    # Alignment Score
    timeframe_alignment: float  # 0-100, how aligned are timeframes
    alignment_quality: str  # "EXCELLENT" (all aligned), "GOOD", "MIXED", "POOR"

    # Trade Plan by Timeframe
    weekly_plan: Optional[TradePlan]
    daily_plan: TradePlan  # Primary
    hourly_plan: Optional[TradePlan]

    # Multi-TF Entry Strategy
    best_entry_timeframe: str  # Which TF to use for entry timing
    best_exit_timeframe: str  # Which TF to use for exit/stops

    # Confidence Adjustment
    confidence_multiplier: float  # 0.5-1.5 based on TF alignment
    # All timeframes aligned = 1.5x confidence
    # Mixed signals = 0.7x confidence

    # Professional Notes
    mtf_notes: list[str]
    # "Weekly uptrend + daily pullback = high-quality long setup"
    # "Daily bullish but weekly bearish = countertrend trade (risky)"
    # "All timeframes bearish = strong conviction short"

def validate_multitimeframe(
    symbol: str,
    primary_period: str = "1d",
) -> MultiTimeframePlan:
    """Validate trade plan across multiple timeframes.

    Process:
    1. Analyze weekly chart (market structure, major S/R)
    2. Analyze daily chart (immediate trend, setup)
    3. Analyze hourly chart (entry timing)

    Validation Rules:
    - Weekly trend = market structure (don't fight)
    - Daily trend = trade direction (main signal)
    - Hourly trend = entry timing (fine-tune)

    Examples:
    EXCELLENT Setup:
    - Weekly: Uptrend
    - Daily: Pullback to support
    - Hourly: Reversal pattern
    → "All timeframes aligned - high confidence long"

    POOR Setup:
    - Weekly: Downtrend
    - Daily: Bullish breakout
    - Hourly: Overbought
    → "Countertrend setup - low confidence"

    Returns:
        Multi-timeframe validated trade plan
    """
    pass

def calculate_timeframe_confidence(
    weekly_bias: str,
    daily_bias: str,
    hourly_bias: str,
) -> tuple[float, str]:
    """Calculate confidence multiplier based on timeframe alignment.

    Scoring:
    - All 3 aligned same direction: 1.5x (excellent)
    - 2 of 3 aligned: 1.0x (good)
    - Mixed signals: 0.7x (poor)
    - All conflicting: 0.5x (avoid)

    Returns:
        (confidence_multiplier, quality_label)
    """
    pass
```

**Finance Expert Rationale:**
- **Higher timeframe = stronger trend**: Weekly trend beats daily, daily beats hourly
- **Pullbacks in trends = best setups**: Daily pullback in weekly uptrend = pro setup
- **Countertrend = low probability**: Fighting higher timeframe = usually loses
- **Entry/exit timeframes differ**: Enter on hourly, exit on daily (different granularity)
- **Professional standard**: No serious trader uses single timeframe

**Implementation Impact:**
- Add `multitimeframe_validation` to trade plan output
- Show alignment score (0-100) and quality rating
- Adjust confidence/sizing based on timeframe alignment
- Warn if countertrend setup (daily bull but weekly bear)

---

### Enhancement 4.2: Scenario Analysis & Risk Projections

**Problem:**
Static trade plans don't account for "what-if" scenarios. What if earnings are bad? What if Fed pivots hawkish? What if sector rotation happens?

**Solution:**
Implement scenario-based risk projection:

```python
@dataclass
class ScenarioAnalysis:
    """What-if scenario projections for trade plan."""

    symbol: str
    base_case: TradePlan  # Expected scenario

    # Alternative Scenarios
    bull_case: ScenarioOutcome  # If everything goes right
    bear_case: ScenarioOutcome  # If everything goes wrong
    sideways_case: ScenarioOutcome  # If nothing happens

    # Event-Driven Scenarios
    earnings_beat_case: Optional[ScenarioOutcome]
    earnings_miss_case: Optional[ScenarioOutcome]
    fed_hawkish_case: Optional[ScenarioOutcome]
    sector_rotation_case: Optional[ScenarioOutcome]

    # Risk Metrics Across Scenarios
    best_case_return: float  # %
    worst_case_loss: float  # %
    expected_value: float  # Probability-weighted avg return
    risk_reward_ratio: float  # Upside / Downside

    # Position Sizing Recommendation
    recommended_position_size: float  # % of portfolio
    max_position_size: float  # Maximum risk tolerance allows
    kelly_criterion_size: float  # Mathematically optimal size

    # Probability Estimates
    scenario_probabilities: dict[str, float]
    # "bull_case": 0.25, "base_case": 0.50, "bear_case": 0.25

    # Adaptive Adjustments
    adjustment_triggers: list[AdjustmentTrigger]
    # "If price drops below $180, reduce position 50%"
    # "If breaks above $200, add to position"
    # "If VIX > 30, exit completely"

@dataclass
class ScenarioOutcome:
    """Outcome for a specific scenario."""

    scenario_name: str
    probability: float  # 0-1

    # Price Targets
    target_price: float
    stop_price: float
    expected_return: float  # %

    # What Needs to Happen
    required_conditions: list[str]
    # "Market continues uptrend"
    # "Earnings beat by > 10%"
    # "Fed pauses rate hikes"

    # Risk Assessment
    likelihood: str  # "HIGH", "MEDIUM", "LOW"
    confidence: str  # "HIGH", "MEDIUM", "LOW"

@dataclass
class AdjustmentTrigger:
    """Conditional adjustment to trade plan."""

    trigger_type: str  # "PRICE", "TIME", "VOLATILITY", "EVENT"
    condition: str  # "Price < $180", "10 days elapsed", "VIX > 30"
    action: str  # "REDUCE_50%", "ADD_25%", "EXIT", "TIGHTEN_STOP"
    rationale: str  # Why this adjustment

def generate_scenarios(
    symbol: str,
    df: pd.DataFrame,
    base_plan: TradePlan,
    current_macro_regime: str = "NEUTRAL",
) -> ScenarioAnalysis:
    """Generate scenario-based risk projections.

    Process:
    1. Define scenarios (bull/base/bear minimum)
    2. Estimate probability of each
    3. Project price targets for each
    4. Calculate expected value
    5. Recommend position sizing

    Scenarios Include:
    - Market scenarios (bull/bear/sideways)
    - Company scenarios (earnings beat/meet/miss)
    - Macro scenarios (Fed hawk/dove, recession/expansion)
    - Sector scenarios (rotation in/out)

    Position Sizing Formula:
    - Kelly Criterion: f = (bp - q) / b
      where f = position size, b = odds, p = win prob, q = loss prob
    - Conservative adjustment: Use half-Kelly to reduce volatility

    Returns:
        Comprehensive scenario analysis with position sizing
    """
    pass

def calculate_expected_value(
    scenarios: list[ScenarioOutcome],
) -> float:
    """Calculate probability-weighted expected return.

    EV = Σ (Probability_i × Return_i)

    Only take trade if EV > 0 (positive expectancy)
    """
    pass
```

**Finance Expert Rationale:**
- **Trade the probabilities, not predictions**: No one knows the future, but we can quantify risk
- **Expected value > win rate**: 40% win rate with 3:1 R:R still makes money
- **Position sizing = most important**: Kelly criterion mathematically optimal
- **Adapt to scenarios**: Good traders adjust, great traders pre-plan adjustments
- **Institutional standard**: All professional funds run scenario analysis

**Implementation Impact:**
- Add `scenarios` section to trade plan output
- Show expected value and Kelly-optimal position size
- List pre-planned adjustment triggers ("If X happens, do Y")
- Warn if negative expected value trade (don't take it)

---

## 5. `scan_trades` - Universe Scanning

### Enhancement 5.1: Unusual Options Activity (UOA) Scanner

**Problem:**
Pure price/volume scanning misses one of the most reliable edge signals: unusual options activity. When insiders or informed traders position, they often use options for leverage and limited risk.

**Solution:**
Integrate options activity scanning to detect informed positioning:

```python
@dataclass
class UnusualOptionsActivity:
    """Unusual options activity detection."""

    symbol: str

    # Volume Anomalies
    options_volume_today: int
    avg_options_volume_30d: int
    volume_ratio: float  # Today / 30-day avg (> 3.0 = unusual)

    # Call/Put Imbalance
    call_volume: int
    put_volume: int
    put_call_ratio: float
    imbalance_direction: str  # "BULLISH_CALLS", "BEARISH_PUTS", "NEUTRAL"

    # Large Trades (Block Trades)
    block_trades_today: list[BlockTrade]
    total_block_premium: float  # Total $ spent on blocks

    # Unusual Patterns
    sweep_detected: bool  # Options sweep (aggressive buying across strikes)
    golden_sweep: bool  # Very large sweep (> $1M premium)
    unusual_strikes: list[str]  # OTM strikes with unusual activity

    # Directional Bias
    smart_money_bias: str  # "BULLISH", "BEARISH", "NEUTRAL"
    conviction_level: str  # "HIGH", "MEDIUM", "LOW"

    # Trade Ideas
    suggested_follow: Optional[str]  # "Follow smart money: Buy calls at $X strike"
    expected_move: Optional[float]  # Implied move based on options activity

    # Warnings
    uoa_signals: list[str]
    # "Golden sweep: $2.5M in calls @ $200 strike - very bullish"
    # "Unusual put buying - bearish sentiment"
    # "Call/Put ratio 5:1 - extreme bullish positioning"

@dataclass
class BlockTrade:
    """Large institutional options trade."""

    timestamp: datetime
    option_type: str  # "CALL" or "PUT"
    strike: float
    expiration: datetime
    premium_paid: float  # Total $ premium
    contracts: int
    direction: str  # "BUY" or "SELL"
    aggressiveness: str  # "PASSIVE", "AGGRESSIVE", "SWEEP"

    # Interpretation
    bullish_or_bearish: str
    confidence: str  # Based on size and aggressiveness

def scan_unusual_options_activity(
    universe: list[str],
    min_volume_ratio: float = 3.0,  # 3x normal volume
    min_block_size: float = 100_000,  # $100k minimum premium
) -> list[UnusualOptionsActivity]:
    """Scan universe for unusual options activity.

    UOA Patterns:

    1. Volume Spike:
       - Options volume > 3x average = unusual
       - > 5x = very unusual (strong signal)

    2. Block Trades:
       - Single trade > $100k premium = institutional
       - > $1M = very large (whale)
       - Direction: buying or selling?

    3. Sweeps:
       - Simultaneous buying across multiple strikes
       - Indicates urgency (informed trader)
       - Golden sweep (> $1M) = very strong

    4. Call/Put Imbalance:
       - Ratio > 3:1 or < 0.33:1 = extreme sentiment
       - Watch for reversals at extremes

    5. Unusual Strikes:
       - OTM strikes with huge volume = specific price target
       - Example: Stock at $100, huge volume in $120 calls = bullish to $120

    Process:
    1. Get options chain data
    2. Compare today's volume to 30-day average
    3. Detect block trades and sweeps
    4. Classify as bullish/bearish
    5. Return actionable signals

    Returns:
        List of symbols with unusual options activity
    """
    pass

def interpret_uoa_signal(
    symbol: str,
    uoa: UnusualOptionsActivity,
) -> str:
    """Convert UOA data into actionable trade idea.

    Examples:
    - "Large call buying at $200 strike → bullish to $200"
    - "Put sweep detected → bearish, expect drop"
    - "Call/put ratio 5:1 → extreme bullish (contrarian warning?)"

    Returns:
        Human-readable interpretation
    """
    pass
```

**Finance Expert Rationale:**
- **Options don't lie**: Large options trades = someone knows something
- **Leverage = commitment**: Buying options requires conviction (vs selling stock)
- **Institutional tells**: Institutions telegraph moves via options before stock
- **Time advantage**: UOA often precedes big stock moves by hours/days
- **Proven edge**: Many retail traders make entire living following UOA

**Implementation Impact:**
- Add `unusual_options_activity` filter to scan
- Return symbols with significant UOA
- Show interpretation: "Bullish UOA - large call buying"
- Provide suggested follow trades (strikes, expiration)

---

### Enhancement 5.2: Breakout Scanner with False Breakout Filter

**Problem:**
Most breakout scanners return tons of false breakouts that immediately fail, causing whipsaw losses. Need intelligent filtering.

**Solution:**
Implement quality-filtered breakout scanner:

```python
@dataclass
class BreakoutScan:
    """High-quality breakout with false breakout filtering."""

    symbol: str

    # Breakout Details
    breakout_type: str  # "RESISTANCE", "SUPPORT", "RANGE", "ATH"
    breakout_level: float
    current_price: float
    breakout_pct: float  # How far past level (> 2% = more conviction)

    # Quality Filters
    volume_confirmation: bool  # Volume > 1.5x average?
    clean_consolidation: bool  # Tight range before breakout?
    retest_count: int  # How many times tested level before break?
    duration_days: int  # How long consolidation before breakout?

    # False Breakout Risk
    false_breakout_risk: str  # "LOW", "MODERATE", "HIGH"
    risk_factors: list[str]
    # "Low volume - higher false breakout risk"
    # "Only 2 days consolidation - needs more time"

    # Quality Score
    breakout_quality: str  # "EXCELLENT", "GOOD", "POOR"
    quality_score: float  # 0-100

    # Trade Setup
    entry_price: float  # Where to enter
    stop_loss: float  # Invalidation level (back below breakout)
    target: float  # Price target (measured move)
    risk_reward: float

    # Institutional Confirmation
    volume_surge: bool  # Volume spike on breakout?
    smart_money_participation: bool  # Large block trades?
    options_activity: Optional[str]  # "Bullish" if call activity

    # Notes
    breakout_notes: list[str]
    # "Clean breakout on high volume - low false breakout risk"
    # "6 retests of resistance before break - strong level"
    # "3-month consolidation - coiled spring breakout"

def scan_quality_breakouts(
    universe: list[str],
    min_quality_score: float = 70,  # Only high-quality setups
    min_consolidation_days: int = 5,  # Minimum time in consolidation
    min_retest_count: int = 2,  # Minimum tests of level
    require_volume_confirmation: bool = True,
) -> list[BreakoutScan]:
    """Scan for high-quality breakouts with false breakout filtering.

    Quality Breakout Criteria:

    1. Clean Consolidation:
       - Tight range (< 5% ATR) for minimum days
       - Multiple retests of level (shows strength)
       - Higher lows in consolidation = bullish

    2. Volume Confirmation:
       - Breakout volume > 1.5x average (minimum)
       - > 2x average = strong confirmation
       - No volume = likely false breakout

    3. Breakout Conviction:
       - Price > 2% past level = more likely real
       - < 1% past level = could be head fake
       - Intraday doesn't count - needs daily close

    4. Context:
       - Breaking multi-week/month range > daily noise
       - All-time high breakout = very bullish
       - Breakout WITH trend > counter-trend

    5. Follow-Through:
       - Day after breakout should hold or continue
       - Immediate reversal = false breakout

    Returns:
        List of high-quality breakout setups
    """
    pass

def calculate_breakout_quality_score(
    volume_ratio: float,
    consolidation_days: int,
    retest_count: int,
    breakout_pct: float,
    trend_aligned: bool,
) -> float:
    """Calculate objective breakout quality score (0-100).

    Scoring:
    - Volume confirmation: 30 points
    - Consolidation duration: 25 points
    - Retest count: 20 points
    - Breakout magnitude: 15 points
    - Trend alignment: 10 points

    Returns:
        Quality score 0-100
    """
    pass

def detect_false_breakout_patterns(
    symbol: str,
    df: pd.DataFrame,
) -> list[str]:
    """Detect historical false breakout patterns for risk assessment.

    False Breakout Indicators:
    - Low volume on breakout
    - Quick reversal (same day or next)
    - Multiple failed attempts (repeated whipsaws)
    - Approaching major resistance above

    Returns:
        List of risk factors
    """
    pass
```

**Finance Expert Rationale:**
- **Most breakouts fail**: 60-70% of breakouts are false (whipsaws)
- **Volume is truth serum**: No volume = no conviction = likely fake
- **Consolidation quality matters**: Tight coil > sloppy range
- **Retests show strength**: More touches of level = stronger when breaks
- **Professional traders wait**: Let breakout prove itself before entering

**Implementation Impact:**
- Return only high-quality breakouts (score > 70)
- Show quality score and risk factors
- Warn of false breakout risk if low volume
- Provide entry/stop/target levels

---

## 6. `portfolio_risk` - Portfolio Risk Assessment

### Enhancement 6.1: Tail Risk & Black Swan Hedging

**Problem:**
Standard portfolio risk metrics (VaR, beta, correlation) fail catastrophically in market crashes. Need tail risk awareness and hedging strategies.

**Solution:**
Implement tail risk analysis and hedge recommendations:

```python
@dataclass
class TailRiskAnalysis:
    """Tail risk and black swan protection analysis."""

    # Standard Risk Metrics (these FAIL in crashes)
    portfolio_var_95: float  # 95% VaR (normal times)
    portfolio_var_99: float  # 99% VaR (stressed)
    max_drawdown_historical: float  # Historical worst loss

    # Tail Risk Metrics (these MATTER in crashes)
    tail_risk_score: float  # 0-100, higher = more tail risk
    left_tail_exposure: float  # How exposed to extreme down moves
    convexity_score: float  # Portfolio profit curvature (want positive)

    # Black Swan Scenarios
    crash_scenario_10pct: float  # P&L if SPY drops 10% in 1 day
    crash_scenario_20pct: float  # P&L if SPY drops 20% in 1 week
    crash_scenario_flash: float  # P&L if 1987-style flash crash

    # Portfolio Vulnerabilities
    vulnerabilities: list[str]
    # "100% long, no downside protection"
    # "High correlation to tech - sector concentration risk"
    # "Low cash reserves - no dry powder"
    # "Leveraged positions - amplified crash risk"

    # Hedge Recommendations
    recommended_hedges: list[HedgeStrategy]
    hedge_cost: float  # % of portfolio to hedge tail risk
    hedged_crash_loss: float  # Loss WITH hedges in crash scenario

    # Antifragility Score
    antifragility: float  # -100 to +100
    # Negative = fragile (worse in volatility)
    # Positive = antifragile (better in volatility)

    # Stress Test Results
    stress_tests: dict[str, float]
    # "2008_crash": -45%, "2020_covid": -35%, "1987_crash": -22%

@dataclass
class HedgeStrategy:
    """Specific hedge recommendation."""

    hedge_type: str  # "PUTS", "VIX_CALLS", "INVERSE_ETF", "CASH"
    instrument: str  # "SPY puts", "VIX calls", "SH (inverse SPY)"
    size: str  # "5% of portfolio"
    cost: float  # % cost
    protection_level: float  # Max loss WITH this hedge

    # When to Use
    best_for: str  # "Crash protection", "Volatility spike", "Sector hedge"
    time_horizon: str  # "1 month", "3 months", "rolling"

    # Trade Details (if options)
    strike: Optional[float]
    expiration: Optional[datetime]
    delta: Optional[float]

    rationale: str
    # "SPY $400 puts (5% OTM) protect against 10-20% crash"

def analyze_tail_risk(
    positions: list[Position],
    portfolio_value: float,
) -> TailRiskAnalysis:
    """Analyze portfolio tail risk and recommend hedges.

    Tail Risk Components:

    1. Concentration Risk:
       - > 20% in one stock = high single-stock risk
       - > 40% in one sector = high sector risk
       - Solution: Diversify or hedge concentrated positions

    2. Directional Bias:
       - 100% long = exposed to crashes
       - Solution: Carry 5-10% in put protection

    3. Correlation Breakdown:
       - Diversification fails in crashes (correlations → 1.0)
       - Solution: True diversifiers (gold, bonds, volatility)

    4. Leverage:
       - Margin amplifies losses
       - Solution: Reduce leverage or hedge aggressively

    Hedging Strategies:

    A. Put Options (Direct Protection):
       - Buy OTM puts on SPY/QQQ (5-10% OTM)
       - Cost: ~1-2% per quarter
       - Benefit: Direct crash protection

    B. VIX Calls (Volatility Protection):
       - Buy VIX calls (spike in crashes)
       - Cost: ~0.5-1% per quarter
       - Benefit: Profit from vol spike

    C. Inverse ETFs (Tactical Hedge):
       - Buy SH (inverse SPY) or QID (inverse QQQ)
       - Cost: Decay over time
       - Benefit: Direct offset to portfolio

    D. Diversification (True Diversifiers):
       - Add gold, managed futures, volatility
       - Cost: Drag in bull markets
       - Benefit: Negative correlation in crashes

    Returns:
        Comprehensive tail risk analysis with hedge recommendations
    """
    pass

def calculate_antifragility_score(
    positions: list[Position],
    options_portfolio: list[OptionsPosition],
) -> float:
    """Calculate Taleb antifragility score.

    Antifragile portfolios BENEFIT from volatility:
    - Long gamma (options convexity)
    - Short correlation (diversified)
    - Asymmetric payoffs (limited downside, unlimited upside)

    Fragile portfolios SUFFER from volatility:
    - Short options (negative convexity)
    - Leverage
    - High correlation

    Score:
    +100 = Perfectly antifragile (loves chaos)
    0 = Neutral
    -100 = Extremely fragile (hates volatility)

    Returns:
        Antifragility score
    """
    pass
```

**Finance Expert Rationale:**
- **VaR useless in crashes**: Assumes normal distribution (crashes aren't normal)
- **Correlation → 1.0 in crashes**: Diversification fails when you need it most
- **Tail events = where money is lost/made**: 80% of returns from < 10 days
- **Hedge = insurance**: Small cost for protection against ruin
- **Institutional standard**: All pro funds stress test for tail risk

**Implementation Impact:**
- Add `tail_risk` section to portfolio risk output
- Show crash scenarios (10%, 20%, flash crash)
- Recommend specific hedges with cost/benefit
- Calculate antifragility score

---

### Enhancement 6.2: Dynamic Position Sizing & Kelly Criterion Integration

**Problem:**
Static position sizing (e.g., "2% per trade") doesn't account for varying edge quality, correlation, or portfolio heat. Optimal sizing is dynamic.

**Solution:**
Implement Kelly Criterion-based dynamic position sizing:

```python
@dataclass
class DynamicPositionSizing:
    """Kelly Criterion-based position sizing recommendations."""

    # Current Portfolio State
    total_portfolio_value: float
    available_capital: float
    current_heat: float  # % of portfolio at risk

    # Kelly Calculation Inputs
    win_rate: float  # Historical or estimated
    avg_win_size: float  # Average winning %
    avg_loss_size: float  # Average losing %
    edge: float  # Expected value per trade

    # Position Sizing Recommendations
    full_kelly: float  # % of portfolio (theoretical max)
    half_kelly: float  # % of portfolio (practical)
    quarter_kelly: float  # % of portfolio (conservative)
    recommended_size: float  # % of portfolio (accounting for correlations)

    # Risk Adjustments
    correlation_adjustment: float  # Reduce if correlated to existing positions
    volatility_adjustment: float  # Reduce if high-volatility stock
    liquidity_adjustment: float  # Reduce if illiquid
    regime_adjustment: float  # Reduce in high-VIX environments

    # Final Position Size
    final_size_pct: float  # After all adjustments
    final_size_usd: float  # Dollar amount
    max_loss_usd: float  # With stop loss

    # Portfolio Heat Management
    new_total_heat: float  # After adding this position
    heat_limit: float  # Maximum allowed heat
    heat_warning: Optional[str]  # If approaching limit

    # Scaling Logic
    scaling_plan: list[ScalingStep]  # How to scale in/out

@dataclass
class ScalingStep:
    """Position scaling logic."""

    trigger: str  # "INITIAL", "PRICE_+5%", "PRICE_-3%", "TIME_+7_DAYS"
    action: str  # "ADD_25%", "REDUCE_50%", "EXIT"
    reason: str  # "Take profit", "Cut loss", "Scale into winner"

def calculate_kelly_position_size(
    win_rate: float,
    avg_win_pct: float,
    avg_loss_pct: float,
    portfolio_value: float,
    risk_per_trade_pct: float = 1.0,
) -> float:
    """Calculate Kelly Criterion optimal position size.

    Kelly Formula:
    f* = (bp - q) / b

    Where:
    - f* = fraction of capital to bet
    - b = odds received (avg_win / avg_loss)
    - p = probability of winning
    - q = probability of losing (1 - p)

    Example:
    - Win rate: 55%
    - Avg win: 10%
    - Avg loss: 5%
    - Kelly: (0.55 * 2 - 0.45) / 2 = 0.325 = 32.5% of capital

    Practical Adjustments:
    - Use Half-Kelly (16.25%) to reduce volatility
    - Never exceed 10% in single position (diversification)
    - Adjust for correlation (reduce if correlated holdings)

    Returns:
        Recommended position size as % of portfolio
    """
    pass

def adjust_for_portfolio_heat(
    kelly_size: float,
    current_heat: float,
    max_heat: float = 6.0,
    correlation_to_portfolio: float = 0.5,
) -> float:
    """Adjust position size for current portfolio heat.

    Portfolio Heat = Sum of all position risks

    Rules:
    - If heat < 3%: Use full Kelly
    - If heat 3-5%: Use 75% Kelly
    - If heat > 5%: Use 50% Kelly or wait
    - If correlated to existing positions: Reduce further

    Returns:
        Adjusted position size
    """
    pass

def generate_scaling_plan(
    entry_price: float,
    stop_price: float,
    target_price: float,
    initial_size_pct: float,
) -> list[ScalingStep]:
    """Generate position scaling plan.

    Scaling Strategy:
    - Enter initial position (e.g., 50% of intended size)
    - If profitable (+5%), add 25%
    - If very profitable (+10%), add final 25%
    - If unprofitable (-stop%), exit all
    - Take partial profits at targets

    Benefits:
    - Pyramiding into winners (let winners run)
    - Cut losers quickly
    - Average cost improves if scaling in

    Returns:
        List of scaling steps with triggers
    """
    pass
```

**Finance Expert Rationale:**
- **Kelly Criterion = mathematically optimal**: Maximizes long-term growth
- **Full Kelly too aggressive**: Half-Kelly reduces volatility 50%, growth 25%
- **Heat management critical**: Don't blow up account on correlated bets
- **Scale into winners**: Best traders average up, not down
- **Dynamic > static**: Market conditions change, sizing should too

**Implementation Impact:**
- Add `position_sizing` section to portfolio risk
- Show Kelly-optimal size and adjusted recommendation
- Warn if portfolio heat approaching limits
- Provide scaling plan for new positions

---

## 7. `morning_brief` - Daily Market Briefing

### Enhancement 7.1: Economic Calendar Integration & Macro Context

**Problem:**
Technical analysis exists in a vacuum. Traders need to know what macro events are driving markets today.

**Solution:**
Integrate economic calendar and macro regime awareness:

```python
@dataclass
class MacroContext:
    """Macro economic context for trading day."""

    # Today's Events
    todays_events: list[EconomicEvent]
    high_impact_events: list[EconomicEvent]  # Events that will move markets

    # This Week's Calendar
    weekly_events: list[EconomicEvent]

    # Economic Data
    recent_data: dict[str, Any]
    # "CPI": {"value": 3.5%, "previous": 3.7%, "expected": 3.6%}
    # "NFP": {"value": 250k, "previous": 200k, "expected": 220k}
    # "GDP": {"value": 2.5%, "previous": 2.1%, "expected": 2.3%}

    # Fed Watch
    fed_funds_rate: float
    next_fed_meeting: datetime
    rate_hike_probability: float  # Market-implied probability
    fed_stance: str  # "HAWKISH", "NEUTRAL", "DOVISH"

    # Market Regime
    macro_regime: str  # "EXPANSION", "LATE_CYCLE", "RECESSION", "RECOVERY"
    regime_confidence: float  # 0-100

    # Trading Implications
    recommended_sectors: list[str]  # Sectors to favor in this regime
    sectors_to_avoid: list[str]  # Sectors likely to underperform
    volatility_expectation: str  # "HIGH", "MODERATE", "LOW"

    # Market Drivers
    primary_drivers: list[str]
    # "Fed policy expectations"
    # "Earnings season"
    # "Geopolitical tensions"

    # Trader Notes
    macro_notes: list[str]
    # "FOMC meeting Wednesday - expect volatility"
    # "CPI tomorrow - key inflation data"
    # "Earnings season starts - focus on stock-specific"

@dataclass
class EconomicEvent:
    """Economic data release or event."""

    event_name: str  # "CPI", "NFP", "FOMC", "GDP"
    scheduled_time: datetime
    importance: str  # "HIGH", "MEDIUM", "LOW"

    # Expectations
    consensus: Optional[float]
    previous: Optional[float]
    actual: Optional[float]  # Filled after release

    # Impact
    expected_market_impact: str  # "HIGH", "MODERATE", "LOW"
    affected_assets: list[str]  # ["USD", "Bonds", "Gold"]

    # Interpretation (if actual released)
    beat_or_miss: Optional[str]  # "BEAT", "MISS", "INLINE"
    market_reaction: Optional[str]  # "Risk-on", "Risk-off"

def generate_macro_briefing() -> MacroContext:
    """Generate macro economic context for trading day.

    Data Sources:
    - Economic calendar APIs (Trading Economics, Investing.com)
    - Fed Watch Tool (CME FedWatch)
    - Recent economic data releases
    - Market-implied probabilities

    Regime Classification:

    EXPANSION:
    - GDP growth > 2%
    - Unemployment falling
    - Fed on hold or easing
    → Favor: Growth stocks, small caps, cyclicals

    LATE_CYCLE:
    - GDP slowing but positive
    - Inflation rising
    - Fed hiking
    → Favor: Value stocks, large caps, defensives

    RECESSION:
    - GDP negative
    - Unemployment rising
    - Fed easing
    → Favor: Bonds, gold, defensive sectors

    RECOVERY:
    - GDP turning positive
    - Unemployment stabilizing
    - Fed still accommodative
    → Favor: Cyclicals, financials, industrials

    Returns:
        Comprehensive macro context
    """
    pass

def interpret_economic_data(
    event_name: str,
    actual: float,
    consensus: float,
    previous: float,
) -> str:
    """Interpret economic data release impact.

    Rules:
    - CPI > consensus = bearish (inflation pressure, Fed hikes)
    - NFP > consensus = bullish (strong economy)
    - GDP > consensus = bullish (growth)
    - Unemployment > consensus = bearish (weakness)

    Returns:
        Market impact interpretation
    """
    pass
```

**Finance Expert Rationale:**
- **Macro drives markets**: Technical analysis describes, macro explains
- **Event risk management**: Don't enter risky trade day before CPI
- **Regime = strategy**: Different strategies work in different regimes
- **Fed = most important**: All markets follow Fed policy
- **Professional standard**: All institutional traders check calendar daily

**Implementation Impact:**
- Add `macro_context` section to morning brief
- List today's high-impact events
- Show current macro regime
- Recommend sectors based on regime

---

### Enhancement 7.2: Overnight & Pre-Market Analysis

**Problem:**
Markets gap overnight. Morning brief should analyze overnight action and pre-market levels to prepare traders for the open.

**Solution:**
Implement overnight gap and pre-market analysis:

```python
@dataclass
class OvernightAnalysis:
    """Overnight and pre-market market analysis."""

    # Index Futures (ES, NQ, YM)
    es_overnight_change: float  # S&P 500 futures %
    nq_overnight_change: float  # Nasdaq 100 futures %
    ym_overnight_change: float  # Dow futures %

    # Pre-Market Levels
    spy_premarket: float
    spy_gap_pct: float  # % gap from yesterday's close
    spy_gap_type: str  # "GAP_UP", "GAP_DOWN", "NO_GAP"
    spy_gap_size: str  # "SMALL" (<0.5%), "MODERATE" (0.5-1.5%), "LARGE" (>1.5%)

    # Gap Behavior
    gap_character: str  # "CONTINUATION", "REVERSAL", "FILL"
    gap_quality: str  # "STRONG", "WEAK"
    gap_fill_probability: float  # % chance gap fills intraday

    # Overnight News
    overnight_catalyst: Optional[str]  # What caused gap
    news_sentiment: str  # "POSITIVE", "NEGATIVE", "NEUTRAL"
    news_items: list[str]  # Headlines

    # Global Markets
    asia_session: dict[str, float]  # {"Nikkei": +1.2%, "Hang Seng": -0.5%}
    europe_session: dict[str, float]  # {"FTSE": +0.8%, "DAX": +1.1%}
    global_risk_sentiment: str  # "RISK_ON", "RISK_OFF", "MIXED"

    # FX & Commodities
    usd_index_change: float
    gold_change: float
    crude_oil_change: float

    # Opening Range Projection
    projected_opening_range: tuple[float, float]  # (low, high) for first 30min
    key_levels_today: list[float]  # Important support/resistance

    # Trading Plan
    opening_strategy: str  # "WAIT_FOR_FILL", "FADE_GAP", "GO_WITH_GAP"
    premarket_watchlist: list[str]  # Stocks with big premarket moves

    # Risk Assessment
    overnight_risk: str  # "HIGH", "MODERATE", "LOW"
    volatility_expectation: str  # "HIGH", "MODERATE", "LOW"

def analyze_overnight_action() -> OvernightAnalysis:
    """Analyze overnight market action and prepare for open.

    Gap Analysis:

    1. Gap Up (bullish overnight):
       - Strong: Volume confirms, holds gains → continue buying
       - Weak: Low volume, fades → fade the gap (short)
       - Fill: Gap fills intraday → range trade

    2. Gap Down (bearish overnight):
       - Strong: Volume confirms, continues lower → continue selling
       - Weak: Low volume, recovers → buy the dip
       - Fill: Gap fills → range trade

    Gap Fill Statistics:
    - Small gaps (<0.5%): 70% fill intraday
    - Moderate gaps (0.5-1.5%): 40% fill
    - Large gaps (>1.5%): 20% fill

    Global Risk Sentiment:
    - Risk-On: Asia up, Europe up, futures up → buy dips
    - Risk-Off: Asia down, Europe down, futures down → sell rallies
    - Mixed: Wait for clarity, day trade only

    Opening Range Trading:
    - First 30 minutes = opening range
    - Breakout of range = direction for day (60% accuracy)
    - Stay flat if choppy opening range

    Returns:
        Comprehensive overnight analysis
    """
    pass

def detect_gap_fill_probability(
    gap_pct: float,
    gap_direction: str,
    volume: float,
    news_catalyst: bool,
) -> float:
    """Estimate probability of gap fill based on characteristics.

    Factors Increasing Fill Probability:
    - Small gap (<0.5%)
    - Low volume
    - No major news catalyst
    - Weak opening (fails to hold)

    Factors Decreasing Fill Probability:
    - Large gap (>1.5%)
    - High volume
    - Major news catalyst
    - Strong opening (extends move)

    Returns:
        Probability (0-100) gap fills intraday
    """
    pass

def generate_opening_strategy(
    gap_type: str,
    gap_quality: str,
    gap_size: str,
    fill_probability: float,
) -> str:
    """Generate trading strategy for market open.

    Strategies:

    1. "GO_WITH_GAP":
       - Strong gap with news/volume
       - Low fill probability
       - Trade: Enter in direction of gap

    2. "FADE_GAP":
       - Weak gap without news
       - High fill probability
       - Trade: Enter opposite direction (gap fill trade)

    3. "WAIT_FOR_FILL":
       - Moderate gap
       - Uncertain quality
       - Trade: Wait for gap fill, then enter long

    4. "WAIT_AND_SEE":
       - Choppy action
       - Mixed signals
       - Trade: Stay flat, wait for clarity

    Returns:
        Recommended opening strategy
    """
    pass
```

**Finance Expert Rationale:**
- **Gaps = opportunity**: 70% of small gaps fill, trade accordingly
- **Overnight matters**: 40% of daily movement happens overnight
- **Global markets lead**: Asia/Europe action predicts US open
- **Opening range = compass**: First 30min sets tone for day
- **Day traders live by this**: Premarket analysis essential for intraday

**Implementation Impact:**
- Add `overnight_analysis` section to morning brief
- Show gap size, quality, fill probability
- Recommend opening strategy
- List stocks with big premarket moves

---

## 8. `analyze_fibonacci` - Fibonacci Analysis

### Enhancement 8.1: Fibonacci Time Zones & Cycle Analysis

**Problem:**
Current Fibonacci analysis focuses only on price levels. Professional traders also use Fibonacci time zones to forecast when reversals occur.

**Solution:**
Implement Fibonacci time-based cycle analysis:

```python
@dataclass
class FibonacciTimeAnalysis:
    """Fibonacci time zones and cycle analysis."""

    symbol: str

    # Time Zone Projection
    swing_start_date: datetime  # Start of Fibonacci count
    time_zones: list[datetime]  # Fibonacci time zone dates
    # [Day 1, Day 2, Day 3, Day 5, Day 8, Day 13, Day 21, Day 34, Day 55, ...]

    # Current Cycle Position
    current_zone: int  # Which Fibonacci number are we in?
    days_into_zone: int
    days_until_next_zone: int

    # Reversal Windows
    upcoming_reversal_windows: list[ReversalWindow]
    # Time periods when price/time Fibonacci confluence suggests reversal

    # Historical Accuracy
    historical_time_zone_hits: int  # How many past zones had reversals
    time_zone_accuracy_pct: float  # Historical accuracy of time zones

    # Cycle Phase
    cycle_phase: str  # "EARLY", "MIDDLE", "LATE"
    cycle_maturity: float  # 0-100, how far into current cycle

    # Price-Time Confluence
    confluence_zones: list[PriceTimeConfluence]
    # Where Fibonacci time zones align with Fibonacci price levels

    # Trader Notes
    time_notes: list[str]
    # "Approaching Day 34 time zone - watch for reversal"
    # "Price and time confluence at $185 on March 15 - high probability turn"

@dataclass
class ReversalWindow:
    """Time window where Fibonacci suggests reversal."""

    start_date: datetime
    end_date: datetime  # Usually 1-3 day window
    fibonacci_number: int  # Which Fib number (8, 13, 21, etc.)
    significance: str  # "HIGH", "MODERATE", "LOW"

    # Context
    price_level_nearby: Optional[float]  # If price Fib level aligns
    historical_hits: int  # How many times this zone worked before
    recommended_action: str  # "WATCH_FOR_REVERSAL", "TAKE_PROFIT", "ENTER"

@dataclass
class PriceTimeConfluence:
    """Confluence of price and time Fibonacci."""

    date: datetime
    price_level: float
    fibonacci_time: int  # Time zone number
    fibonacci_price: float  # Price level ratio (0.618, etc.)

    # Strength
    confluence_strength: str  # "VERY_STRONG", "STRONG", "MODERATE"
    expected_impact: str  # "MAJOR_REVERSAL", "MINOR_REVERSAL", "SUPPORT_RESISTANCE"

    # Historical
    similar_confluences_hit: int  # How many times this worked historically

def calculate_fibonacci_time_zones(
    swing_start: datetime,
    current_date: datetime,
) -> list[datetime]:
    """Calculate Fibonacci time zone dates.

    Fibonacci Time Zones:
    - Start from significant swing (high or low)
    - Project Fibonacci numbers as days forward
    - Zones: 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144, 233, ...

    Theory:
    - Natural cycles follow Fibonacci sequences
    - Reversals tend to occur at Fibonacci time intervals
    - Especially powerful when time and price Fib align

    Usage:
    - At Fibonacci time zone, watch for reversal signals
    - Combine with price Fibonacci for confluence
    - Use for profit-taking or entry timing

    Returns:
        List of Fibonacci time zone dates
    """
    pass

def detect_price_time_confluence(
    time_zones: list[datetime],
    price_levels: list[float],
    current_price: float,
    df: pd.DataFrame,
) -> list[PriceTimeConfluence]:
    """Detect where Fibonacci time and price align.

    Confluence Occurs When:
    - Fibonacci time zone date
    - Fibonacci price level
    - Both happen simultaneously or within 1-2 days

    Strength Ratings:
    - VERY_STRONG: Multiple time zones + multiple price levels
    - STRONG: Single time zone + single price level
    - MODERATE: Close proximity (within 3 days / 2% price)

    Example:
    - Day 21 time zone
    - Price at 0.618 retracement ($185)
    - Both align on March 15
    → Very high probability reversal window

    Returns:
        List of price-time confluence zones
    """
    pass
```

**Finance Expert Rationale:**
- **Time + price = complete analysis**: Price alone is only half the picture
- **Natural cycles exist**: Markets move in rhythms (Fibonacci is one framework)
- **Confluence = highest probability**: When time and price agree, pay attention
- **Professional edge**: Retail traders ignore time, institutions use it
- **Timing matters**: Even perfect level fails if timing wrong

**Implementation Impact:**
- Add `time_zones` section to Fibonacci analysis
- Highlight upcoming time zone reversals
- Show price-time confluence zones (highest probability)
- Warn when approaching significant time zone

---

### Enhancement 8.2: Fibonacci Extensions for Price Targets & Projections

**Problem:**
Current system focuses on retracements (pullbacks). Need extensions to project breakout targets and trend continuation levels.

**Solution:**
Implement comprehensive Fibonacci extension analysis:

```python
@dataclass
class FibonacciExtensions:
    """Fibonacci extensions for price projections."""

    symbol: str
    current_price: float

    # Extension Levels (upside targets)
    extension_levels: list[ExtensionLevel]
    # 1.272, 1.414, 1.618, 2.000, 2.618, 3.000, 3.618, 4.236

    # Projection Scenarios
    bullish_targets: list[float]  # If uptrend continues
    bearish_targets: list[float]  # If downtrend continues

    # Measured Moves
    measured_move_projection: float  # AB=CD pattern projection
    swing_projection: float  # Swing high/low based projection

    # Confluence Targets
    high_confluence_targets: list[TargetZone]
    # Where multiple extension levels cluster

    # Target Probability
    target_probabilities: dict[float, float]
    # {185.0: 0.70, 195.0: 0.50, 205.0: 0.30}
    # Probability of reaching each level

    # Resistance Map
    extension_resistance_map: list[tuple[float, str]]
    # [(190.0, "WEAK"), (195.0, "MODERATE"), (205.0, "STRONG")]

    # Trading Plan
    profit_taking_zones: list[float]  # Where to take profits
    breakout_confirmation: float  # Price that confirms next leg up

@dataclass
class ExtensionLevel:
    """Single Fibonacci extension level."""

    ratio: float  # 1.272, 1.618, etc.
    price: float
    distance_pct: float  # % from current price

    # Context
    level_type: str  # "STANDARD_EXTENSION", "MEASURED_MOVE", "PROJECTION"
    strength: str  # "WEAK", "MODERATE", "STRONG"

    # Historical
    historical_hits: int  # Times price reacted at this level before
    hit_accuracy: float  # % of times level was respected

    # Timing
    estimated_days_to_reach: Optional[int]  # Based on momentum
    confidence: str  # "HIGH", "MEDIUM", "LOW"

@dataclass
class TargetZone:
    """Clustered target zone with multiple extensions."""

    center_price: float
    range_low: float
    range_high: float

    # Confluent Levels
    fibonacci_levels: list[float]  # Multiple Fib levels in this zone
    level_count: int

    # Strength
    confluence_strength: str  # "VERY_STRONG", "STRONG", "MODERATE"
    expected_reaction: str  # "REVERSAL", "PAUSE", "MINOR"

    # Usage
    recommended_action: str  # "TAKE_PROFIT", "PARTIAL_EXIT", "ADD_SHORT"

def calculate_fibonacci_extensions(
    swing_low: float,
    swing_high: float,
    current_price: float,
    trend: str = "BULLISH",
) -> list[ExtensionLevel]:
    """Calculate Fibonacci extension levels for price projections.

    Extension Calculations:
    For bullish trend:
    - 100% extension: swing_high + (swing_high - swing_low) * 1.0
    - 127.2% extension: swing_high + (swing_high - swing_low) * 1.272
    - 161.8% extension: swing_high + (swing_high - swing_low) * 1.618
    - 200% extension: swing_high + (swing_high - swing_low) * 2.0
    - And so on...

    Key Levels:
    - 1.272: Common first target in trends
    - 1.618: Golden ratio projection (strongest)
    - 2.0: Measured move (AB=CD)
    - 2.618: Extended projection
    - 4.236: Extreme extension (rare but powerful)

    Usage:
    - Set profit targets at extensions
    - Identify potential resistance zones
    - Plan position scaling (take profits)
    - Combine with other methods (measured moves, channels)

    Returns:
        List of extension levels with metadata
    """
    pass

def project_measured_move(
    point_a: float,
    point_b: float,
    point_c: float,
) -> float:
    """Calculate AB=CD measured move projection.

    AB=CD Pattern:
    - Identifies trend continuation targets
    - A to B = first leg
    - C to D = second leg (should equal AB)
    - D = C + (B - A)

    Example:
    - A = $100 (low)
    - B = $120 (high) → +$20 move
    - C = $110 (pullback)
    - D = $130 (projection) → $110 + $20 = $130

    This is a 100% Fibonacci extension (1.0 ratio)

    Returns:
        Projected target price (Point D)
    """
    pass

def identify_target_zones(
    extension_levels: list[ExtensionLevel],
    tolerance: float = 0.02,  # 2% clustering tolerance
) -> list[TargetZone]:
    """Identify clustered target zones where multiple levels converge.

    Clustering Logic:
    - Group extension levels within tolerance % of each other
    - More levels = stronger confluence
    - Strongest zones = highest probability targets

    Example:
    - 1.272 extension at $194
    - 1.414 extension at $196
    - 1.618 extension at $195
    → Target zone: $194-$196 (3-level confluence, VERY_STRONG)

    Returns:
        List of high-confluence target zones
    """
    pass
```

**Finance Expert Rationale:**
- **Targets = profit-taking plan**: Know where to exit before entering
- **Extensions > random targets**: Math-based, historically respected
- **Measured moves work**: AB=CD pattern is reliable
- **Confluence = conviction**: Multiple levels = higher probability
- **Professional standard**: All chart-based traders use extensions

**Implementation Impact:**
- Add `extensions` section to Fibonacci analysis
- Show projected upside/downside targets
- Highlight high-confluence zones
- Provide profit-taking recommendations at extensions

---

## 9. `options_risk_analysis` - Options Chain Analysis

### Enhancement 9.1: Gamma & Delta Exposure Analysis (Market Maker Positioning)

**Problem:**
Options chain analysis misses critical data: market maker positioning via gamma and delta exposure. These levels act as price magnets or repellers.

**Solution:**
Implement dealer gamma and delta exposure analysis:

```python
@dataclass
class GammaDeltaExposure:
    """Market maker gamma and delta exposure analysis."""

    symbol: str
    current_price: float

    # Gamma Exposure (GEX)
    total_gamma_exposure: float  # Net gamma (positive = long, negative = short)
    gamma_by_strike: dict[float, float]  # Gamma at each strike

    # Key Gamma Levels
    zero_gamma_level: Optional[float]  # Price where gamma flips sign
    max_gamma_strike: float  # Strike with highest gamma
    negative_gamma_zone: Optional[tuple[float, float]]  # Range of negative gamma

    # Delta Exposure (DEX)
    total_delta_exposure: float  # Net delta
    delta_by_strike: dict[float, float]  # Delta at each strike

    # Price Implications
    gamma_regime: str  # "POSITIVE" (stabilizing) or "NEGATIVE" (volatile)
    price_pinning_level: Optional[float]  # Price likely to pin to (max gamma)
    volatility_expectation: str  # "LOW" (pos gamma) or "HIGH" (neg gamma)

    # Support & Resistance from Dealers
    dealer_support_levels: list[float]  # Where dealers will buy
    dealer_resistance_levels: list[float]  # Where dealers will sell

    # Hedging Flow Forecast
    expected_dealer_flow: str  # "BUYING", "SELLING", "NEUTRAL"
    flow_magnitude: str  # "LARGE", "MODERATE", "SMALL"

    # Trading Implications
    trading_strategy: str  # "FADE_MOVES", "FOLLOW_BREAKOUT", "RANGE_TRADE"

    # Notes
    gex_notes: list[str]
    # "Large positive gamma at $200 - expect price pinning"
    # "Negative gamma zone $180-$190 - volatility amplified"
    # "Zero gamma at $195 - inflection point"

def calculate_gamma_exposure(
    options_chain: pd.DataFrame,
    current_price: float,
) -> GammaDeltaExposure:
    """Calculate market maker gamma and delta exposure.

    Gamma Exposure Theory:

    1. Market Makers (dealers) hedge option sales:
       - Sell call → short stock → buy as price rises (suppresses rallies)
       - Sell put → long stock → sell as price falls (suppresses declines)

    2. Positive Gamma (dealers long gamma):
       - Dealers buy dips, sell rallies
       - Price stabilizes (mean reversion)
       - Low volatility expected
       - Price "pins" to max gamma strike

    3. Negative Gamma (dealers short gamma):
       - Dealers sell dips, buy rallies
       - Price destabilizes (trend amplification)
       - High volatility expected
       - Price avoids max gamma strike

    4. Zero Gamma Level (ZGL):
       - Price where gamma flips from positive to negative
       - Critical inflection point
       - Above ZGL = stabilizing, below ZGL = volatile

    Calculation:
    For each strike:
    - Gamma_exposure = (Call_OI - Put_OI) × Gamma × 100 × Spot^2
    - Positive = dealers long gamma (stabilizing)
    - Negative = dealers short gamma (volatile)

    Usage:
    - Positive gamma → fade moves (mean revert)
    - Negative gamma → follow moves (trend)
    - Max gamma strike → price magnet (likely to pin)
    - Zero gamma → critical inflection level

    Returns:
        Comprehensive gamma/delta exposure analysis
    """
    pass

def identify_price_pinning_level(
    gamma_by_strike: dict[float, float],
    current_price: float,
    expiration_dte: int,
) -> Optional[float]:
    """Identify strike where price is likely to pin (max gamma).

    Price Pinning:
    - Occurs at strike with highest open interest
    - Strongest near expiration (OpEx week)
    - Dealers hedge forces price toward strike
    - More pronounced in low-volume stocks

    Example:
    - AAPL at $198
    - $200 strike has huge call open interest
    - Dealers short calls, hedge by buying stock
    - Price pulled toward $200
    → Price pins to $200 by expiration

    Returns:
        Strike price with highest pinning probability
    """
    pass

def determine_volatility_regime(
    total_gamma: float,
    current_price: float,
    zero_gamma_level: Optional[float],
) -> tuple[str, str]:
    """Determine volatility regime based on gamma exposure.

    Regimes:

    POSITIVE_GAMMA (Stabilizing):
    - Price above zero gamma level
    - Dealers dampen volatility
    - Range-bound trading likely
    - Fade extremes

    NEGATIVE_GAMMA (Volatile):
    - Price below zero gamma level
    - Dealers amplify volatility
    - Trending moves likely
    - Follow breakouts

    NEUTRAL:
    - Near zero gamma
    - Uncertain regime
    - Wait for clarity

    Returns:
        (regime, trading_strategy)
    """
    pass
```

**Finance Expert Rationale:**
- **Dealers move markets**: Market makers hedge $trillions in options
- **Gamma = volatility regime**: Positive gamma suppresses vol, negative amplifies
- **Pin risk is real**: Price gravitates to max gamma strike at expiration
- **ZGL = inflection point**: Critical level that changes market character
- **Professional edge**: Institutions track dealer positioning religiously

**Implementation Impact:**
- Add `gamma_delta_exposure` section to options analysis
- Show zero gamma level and pinning strike
- Indicate volatility regime (stabilizing vs volatile)
- Recommend strategy based on gamma (fade vs follow)

---

### Enhancement 9.2: Skew & Term Structure Analysis (Vol Surface Intelligence)

**Problem:**
Analyzing individual strikes misses the big picture: volatility skew and term structure reveal market fears, sentiment, and mispricings.

**Solution:**
Implement full volatility surface analysis:

```python
@dataclass
class VolatilitySurfaceAnalysis:
    """Volatility skew and term structure analysis."""

    symbol: str
    current_price: float
    current_iv: float  # At-the-money IV

    # Volatility Skew (same expiration, different strikes)
    skew_shape: str  # "NORMAL", "STEEP", "REVERSE", "SMILE"
    skew_direction: str  # "PUT_SKEW", "CALL_SKEW", "BALANCED"
    skew_steepness: float  # How steep (25-delta put IV - ATM IV)

    # Skew Implications
    market_fear_gauge: str  # "EXTREME_FEAR", "MODERATE_FEAR", "COMPLACENT"
    tail_risk_pricing: str  # "EXPENSIVE", "FAIR", "CHEAP"

    # Term Structure (same strike, different expirations)
    term_structure_shape: str  # "NORMAL", "INVERTED", "FLAT", "HUMPED"
    front_month_iv: float
    back_month_iv: float
    calendar_spread_opportunity: bool

    # Vol Smile Analysis
    smile_metrics: dict[str, float]
    # "25_delta_put_iv": 35%, "atm_iv": 30%, "25_delta_call_iv": 28%

    # Relative Value
    cheap_strikes: list[float]  # Strikes with low IV (buy)
    expensive_strikes: list[float]  # Strikes with high IV (sell)

    # Trading Strategies
    recommended_strategies: list[OptionsStrategy]
    # Based on skew and term structure inefficiencies

    # Historical Context
    current_iv_percentile: float  # Where is IV now vs history (0-100)
    iv_rank: float  # 0-100
    mean_reversion_signal: Optional[str]  # "IV_TOO_HIGH", "IV_TOO_LOW"

    # Volatility Events
    upcoming_vol_events: list[str]
    # "Earnings in 5 days - IV likely to spike"
    # "Approaching OpEx - vol crush expected"

    # Notes
    vol_surface_notes: list[str]
    # "Steep put skew - market pricing crash protection"
    # "Inverted term structure - near-term event expected"
    # "25-delta put IV 50% > ATM - extreme fear"

@dataclass
class OptionsStrategy:
    """Recommended options strategy based on vol surface."""

    strategy_name: str  # "IRON_CONDOR", "CALL_SPREAD", "CALENDAR_SPREAD"
    rationale: str

    # Legs
    legs: list[OptionsLeg]

    # Risk/Reward
    max_profit: float
    max_loss: float
    breakeven: list[float]

    # Greeks
    delta: float
    gamma: float
    theta: float
    vega: float

    # Best For
    market_outlook: str  # "NEUTRAL", "BULLISH", "BEARISH"
    vol_outlook: str  # "RISING", "FALLING", "STABLE"

@dataclass
class OptionsLeg:
    """Single leg of options strategy."""

    action: str  # "BUY" or "SELL"
    option_type: str  # "CALL" or "PUT"
    strike: float
    expiration: datetime
    quantity: int
    premium: float

def analyze_volatility_surface(
    symbol: str,
    options_chain: pd.DataFrame,
) -> VolatilitySurfaceAnalysis:
    """Analyze full volatility surface for inefficiencies.

    Volatility Skew Analysis:

    1. Put Skew (Most Common):
       - OTM put IV > ATM IV
       - Market paying up for downside protection
       - Interpretation: Fear, crash protection
       - Strategy: Sell put spreads (overpriced), avoid buying naked puts

    2. Call Skew (Rare):
       - OTM call IV > ATM IV
       - Market paying up for upside
       - Interpretation: FOMO, takeover speculation
       - Strategy: Sell call spreads

    3. Smile (Volatility):
       - Both OTM puts and calls elevated
       - Market expects big move but unsure direction
       - Interpretation: Event risk (earnings, FDA)
       - Strategy: Sell straddle/strangle (overpriced vol)

    Term Structure Analysis:

    1. Normal (Contango):
       - Front month IV < Back month IV
       - Market calm near-term, uncertainty long-term
       - Strategy: Buy calendar spreads (long back, short front)

    2. Inverted (Backwardation):
       - Front month IV > Back month IV
       - Near-term event driving vol spike
       - Strategy: Sell front month, buy back month

    3. Humped:
       - Mid-term IV highest
       - Specific event in middle expiration
       - Strategy: Target that expiration for vol trades

    Relative Value Opportunities:
    - Compare IV across strikes and expirations
    - Buy cheap vol, sell expensive vol
    - Arbitrage skew inefficiencies

    Returns:
        Comprehensive vol surface analysis with trade ideas
    """
    pass

def detect_skew_anomalies(
    atm_iv: float,
    put_25d_iv: float,
    call_25d_iv: float,
    historical_skew: float,
) -> list[str]:
    """Detect unusual skew patterns.

    Anomalies:
    - Skew > 2x historical average = extreme fear
    - Reverse skew (calls > puts) = rare, investigate
    - Flat skew = complacency or post-event normalization

    Returns:
        List of anomaly descriptions
    """
    pass

def recommend_skew_strategies(
    skew_shape: str,
    term_structure: str,
    iv_percentile: float,
) -> list[OptionsStrategy]:
    """Recommend options strategies based on vol surface.

    Strategy Selection:

    High IV + Steep Put Skew:
    → Sell put spreads (collect overpriced premium)

    Low IV + Normal Term Structure:
    → Buy call/put spreads (cheap directional bets)

    Inverted Term Structure:
    → Calendar spreads (sell front, buy back)

    Flat Skew + Low IV:
    → Buy straddles/strangles (cheap vol)

    Returns:
        List of recommended strategies with rationale
    """
    pass
```

**Finance Expert Rationale:**
- **Skew = market sentiment**: Steep put skew = fear, call skew = greed
- **Term structure = event timing**: Inverted term structure = near-term catalyst
- **Vol surface = inefficiency map**: Buy cheap vol, sell expensive vol
- **Professional options traders live by this**: Vol surface is the foundation
- **Mean reversion**: IV extremes revert (sell high IV, buy low IV)

**Implementation Impact:**
- Add `volatility_surface` section to options analysis
- Show skew shape and steepness
- Display IV percentile (mean reversion signal)
- Recommend strategies based on vol inefficiencies

---

## Summary & Implementation Priority

### Critical Enhancements (Implement First)

**Tier 1 (Maximum Impact):**
1. **Regime Detection** (`analyze_security`) - Changes entire interpretation framework
2. **Liquidity Filtering** (`screen_securities`) - Prevents untradeable results
3. **Multi-Timeframe Validation** (`get_trade_plan`) - Dramatically improves win rate
4. **Tail Risk Analysis** (`portfolio_risk`) - Prevents catastrophic losses
5. **GEX Analysis** (`options_risk_analysis`) - Reveals hidden market structure

**Tier 2 (High Value):**
6. **Smart Money Flow** (`analyze_security`) - Institutional footprints
7. **Relative Strength** (`compare_securities`) - Beat the market, not just make money
8. **Unusual Options Activity** (`scan_trades`) - Follow informed traders
9. **Macro Context** (`morning_brief`) - Know what's driving markets
10. **Fibonacci Extensions** (`analyze_fibonacci`) - Profit targets

**Tier 3 (Nice to Have):**
11. **Correlation Analysis** (`compare_securities`) - Pairs trading
12. **Catalyst Awareness** (`screen_securities`) - Event risk management
13. **Scenario Analysis** (`get_trade_plan`) - Probabilistic thinking
14. **Overnight Analysis** (`morning_brief`) - Pre-market edge
15. **Fibonacci Time Zones** (`analyze_fibonacci`) - Timing tool
16. **Volatility Surface** (`options_risk_analysis`) - Vol trading edge
17. **Kelly Sizing** (`portfolio_risk`) - Optimal bet sizing
18. **Breakout Scanner** (`scan_trades`) - Quality vs quantity

### Technical Complexity Assessment

**Low Complexity (Quick Wins):**
- Liquidity filtering (existing data)
- Macro calendar integration (API calls)
- Multi-timeframe validation (existing logic)

**Medium Complexity:**
- Regime detection (multiple indicators, logic)
- Smart money flow (volume profile analysis)
- Relative strength (comparative calculations)
- Fibonacci extensions (math, clustering)

**High Complexity:**
- GEX analysis (options Greeks, vol surface math)
- Tail risk / Kelly (statistical modeling)
- UOA scanning (options data feed, pattern recognition)
- Scenario analysis (probability modeling)

---

**Next Steps:**
1. Review enhancements with product/trading team
2. Prioritize based on user segment (retail vs institutional)
3. Create implementation tickets for Tier 1 enhancements
4. Design API contracts for new data requirements (options flow, economic calendar)
5. Build incremental - ship one enhancement per sprint

---

*This document represents institutional-grade enhancements that would transform MCP Finance from a retail technical analysis tool into a professional trading platform competitive with Bloomberg Terminal, TradingView Pro, and hedge fund internal tools.*
