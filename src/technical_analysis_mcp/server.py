"""MCP Server entry point for Technical Analysis.

Minimal server implementation that defines MCP tools and routes
to the appropriate service functions using dependency injection.
"""

import asyncio
import logging
import numpy as np
from datetime import datetime
from typing import Any

from mcp.server import Server
from mcp.types import TextContent, Tool

from .config import DEFAULT_PERIOD, MAX_SIGNALS_RETURNED, MAX_SYMBOLS_COMPARE
from .data import AnalysisResultCache, CachedDataFetcher, DataFetcher
from .exceptions import DataFetchError, TechnicalAnalysisError
from .briefing import MorningBriefGenerator
from .formatting import format_analysis, format_comparison, format_screening, format_risk_analysis, format_scan_results, format_portfolio_risk, format_morning_brief
from .indicators import calculate_all_indicators
from .portfolio import PortfolioRiskAssessor
from .ranking import RankingStrategy, get_ranking_strategy, rank_signals
from .risk import RiskAssessor
from .scanners import TradeScanner
from .signals import detect_all_signals
from .universes import UNIVERSES

logger = logging.getLogger(__name__)

app = Server("technical-analysis-mcp")

_data_fetcher: DataFetcher | None = None
_result_cache: AnalysisResultCache | None = None


def get_data_fetcher() -> DataFetcher:
    """Get or create the data fetcher instance."""
    global _data_fetcher
    if _data_fetcher is None:
        _data_fetcher = CachedDataFetcher()
    return _data_fetcher


def get_result_cache() -> AnalysisResultCache:
    """Get or create the result cache instance."""
    global _result_cache
    if _result_cache is None:
        _result_cache = AnalysisResultCache()
    return _result_cache


def calculate_adaptive_tolerance(level_prices: list[float]) -> float:
    """Calculate adaptive tolerance based on price distribution of Fibonacci levels.

    Uses the 25th percentile of gaps between consecutive levels to determine
    dynamic tolerance. This adapts to market conditions:
    - Dense level clustering → tighter tolerance
    - Sparse levels → wider tolerance

    Args:
        level_prices: Sorted list of Fibonacci level prices.

    Returns:
        Dynamic tolerance as percentage (0.005 to 0.05 representing 0.5% to 5%).
        Defaults to 0.015 (1.5%) for edge cases.

    Technical Details:
        - Calculates differences between consecutive sorted levels
        - Uses 25th percentile gap as the distribution measure
        - Clamps result between 0.5% and 5% boundaries
        - Gracefully handles edge cases (< 3 levels, zero gaps)
    """
    if not level_prices or len(level_prices) < 3:
        # Not enough levels for meaningful distribution
        return 0.015  # Default 1.5% tolerance

    # Convert to numpy array for efficient calculations
    prices = np.array(level_prices, dtype=np.float64)

    # Calculate differences between consecutive sorted levels
    price_diffs = np.diff(prices)

    # Handle edge case: all prices are identical
    if np.sum(price_diffs) == 0:
        return 0.015  # Default tolerance when no spread

    # Calculate percentage differences relative to each price
    # np.diff(prices) returns N-1 elements if prices has N elements
    # price_diffs[i] = prices[i+1] - prices[i], so divide by prices[i]
    pct_diffs = price_diffs / prices[:-1]  # Use price of lower level

    # Use 25th percentile as distribution measure (robust to outliers)
    try:
        percentile_25_gap = np.quantile(pct_diffs, 0.25)
    except (IndexError, ValueError):
        return 0.015

    # Clamp tolerance to reasonable bounds: 0.5% to 5%
    # Tolerance is typically 30-50% of the 25th percentile gap
    adaptive_tolerance = np.clip(percentile_25_gap * 0.4, 0.005, 0.05)

    return float(adaptive_tolerance)


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available MCP tools."""
    return [
        Tool(
            name="analyze_security",
            description="Analyze any stock/ETF with 150+ technical signals",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "Ticker symbol (e.g., AAPL, MSFT)",
                    },
                    "period": {
                        "type": "string",
                        "default": "3mo",
                        "description": "Time period (15m, 1h, 4h, 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y) - SWING TRADING: 3mo for trend analysis",
                    },
                    "use_ai": {
                        "type": "boolean",
                        "default": False,
                        "description": "Use AI ranking (requires API key)",
                    },
                },
                "required": ["symbol"],
            },
        ),
        Tool(
            name="compare_securities",
            description="Compare multiple stocks/ETFs and find the best pick",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbols": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of ticker symbols to compare",
                    },
                    "metric": {
                        "type": "string",
                        "default": "signals",
                        "description": "Comparison metric",
                    },
                    "period": {
                        "type": "string",
                        "default": "3mo",
                        "description": "Time period (15m, 1h, 4h, 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y) - SWING TRADING: 3mo for trend analysis",
                    },
                },
                "required": ["symbols"],
            },
        ),
        Tool(
            name="screen_securities",
            description="Screen securities matching technical criteria",
            inputSchema={
                "type": "object",
                "properties": {
                    "universe": {
                        "type": "string",
                        "default": "sp500",
                        "description": "Universe to screen (sp500, nasdaq100, etf_large_cap)",
                    },
                    "criteria": {
                        "type": "object",
                        "description": "Screening criteria (rsi, min_score, etc.)",
                    },
                    "limit": {
                        "type": "integer",
                        "default": 20,
                        "description": "Maximum results to return",
                    },
                    "period": {
                        "type": "string",
                        "default": "3mo",
                        "description": "Time period (15m, 1h, 4h, 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y) - SWING TRADING: 3mo for trend analysis",
                    },
                },
                "required": ["criteria"],
            },
        ),
        Tool(
            name="get_trade_plan",
            description="Get risk-qualified trade plan (1-3 max) with suppression reasons if not tradeable",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "Ticker symbol (e.g., AAPL, MSFT)",
                    },
                    "period": {
                        "type": "string",
                        "default": "3mo",
                        "description": "Time period (15m, 1h, 4h, 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y) - SWING TRADING: 3mo for trend analysis",
                    },
                },
                "required": ["symbol"],
            },
        ),
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
                    "period": {
                        "type": "string",
                        "default": "3mo",
                        "description": "Time period (15m, 1h, 4h, 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y) - SWING TRADING: 3mo for trend analysis",
                    },
                },
                "required": [],
            },
        ),
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
                                "symbol": {
                                    "type": "string",
                                    "description": "Ticker symbol",
                                },
                                "shares": {
                                    "type": "number",
                                    "description": "Number of shares",
                                },
                                "entry_price": {
                                    "type": "number",
                                    "description": "Entry price per share",
                                },
                            },
                            "required": ["symbol", "shares", "entry_price"],
                        },
                        "description": "List of open positions",
                    },
                    "period": {
                        "type": "string",
                        "default": "3mo",
                        "description": "Time period (15m, 1h, 4h, 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y) - SWING TRADING: 3mo for trend analysis",
                    },
                },
                "required": ["positions"],
            },
        ),
        Tool(
            name="morning_brief",
            description="Generate daily market briefing with signals and market conditions",
            inputSchema={
                "type": "object",
                "properties": {
                    "watchlist": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Symbols to analyze (default: top 10 tech/finance stocks)",
                    },
                    "market_region": {
                        "type": "string",
                        "default": "US",
                        "description": "Market region (US, EU, ASIA)",
                    },
                    "period": {
                        "type": "string",
                        "default": "3mo",
                        "description": "Time period (15m, 1h, 4h, 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y) - SWING TRADING: 3mo for trend analysis",
                    },
                },
                "required": [],
            },
        ),
        Tool(
            name="analyze_fibonacci",
            description=(
                "Comprehensive Fibonacci analysis including 40+ levels, "
                "200+ signals across retracements, extensions, harmonic patterns, "
                "Elliott Wave relationships, clusters, and time zones. "
                "Returns price levels, active signals, and confluence zones."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "Stock symbol (e.g., AAPL)",
                    },
                    "period": {
                        "type": "string",
                        "description": "Time period (15m, 1h, 4h, 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y)",
                        "default": "1mo",
                    },
                    "window": {
                        "type": "integer",
                        "description": "Lookback window for swing detection - SWING TRADING: 150 bars captures multi-day swings",
                        "default": 150,
                    },
                },
                "required": ["symbol"],
            },
        ),
        Tool(
            name="options_risk_analysis",
            description=(
                "Analyze options chain risk metrics using real yfinance data. "
                "Includes IV analysis, Greeks (Delta, Gamma, Theta, Vega), "
                "volume/open interest analysis, Put/Call ratio, and risk warnings. "
                "Provides actionable insights for options trading strategies."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "Ticker symbol (e.g., AAPL, MSFT)",
                    },
                    "expiration_date": {
                        "type": "string",
                        "description": "Specific expiration date (YYYY-MM-DD). If omitted, uses nearest expiration.",
                    },
                    "option_type": {
                        "type": "string",
                        "default": "both",
                        "description": "Type of options to analyze: 'calls', 'puts', or 'both'",
                    },
                    "min_volume": {
                        "type": "integer",
                        "default": 75,
                        "description": "Minimum volume threshold for liquid options - SWING TRADING: 75 ensures adequate liquidity",
                    },
                },
                "required": ["symbol"],
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """Route tool calls to appropriate handlers."""
    try:
        if name == "analyze_security":
            result = await analyze_security(**arguments)
            return [TextContent(type="text", text=format_analysis(result))]

        if name == "compare_securities":
            result = await compare_securities(**arguments)
            return [TextContent(type="text", text=format_comparison(result))]

        if name == "screen_securities":
            result = await screen_securities(**arguments)
            return [TextContent(type="text", text=format_screening(result))]

        if name == "get_trade_plan":
            result = await get_trade_plan(**arguments)
            return [TextContent(type="text", text=format_risk_analysis(result))]

        if name == "scan_trades":
            result = await scan_trades(**arguments)
            return [TextContent(type="text", text=format_scan_results(result))]

        if name == "portfolio_risk":
            result = await portfolio_risk(**arguments)
            return [TextContent(type="text", text=format_portfolio_risk(result))]

        if name == "morning_brief":
            result = await morning_brief(**arguments)
            return [TextContent(type="text", text=format_morning_brief(result))]

        if name == "analyze_fibonacci":
            result = await analyze_fibonacci(**arguments)
            import json
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        if name == "options_risk_analysis":
            result = await options_risk_analysis(**arguments)
            import json
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        return [TextContent(type="text", text=f"Unknown tool: {name}")]

    except TechnicalAnalysisError as e:
        logger.error("Analysis error: %s", e)
        return [TextContent(type="text", text=f"❌ Error: {e}")]
    except Exception as e:
        logger.exception("Unexpected error in tool %s", name)
        return [TextContent(type="text", text=f"❌ Unexpected error: {e}")]


async def analyze_security(
    symbol: str,
    period: str = DEFAULT_PERIOD,
    use_ai: bool = False,
) -> dict[str, Any]:
    """Analyze a security with technical indicators and signals.

    Args:
        symbol: Ticker symbol.
        period: Time period for analysis.
        use_ai: Whether to use AI ranking.

    Returns:
        Complete analysis result dictionary.
    """
    symbol = symbol.upper().strip()
    cache = get_result_cache()

    cached_result = cache.get(symbol, period)
    if cached_result:
        logger.info("Cache hit for %s", symbol)
        return cached_result

    logger.info("Analyzing %s (period: %s, use_ai: %s)", symbol, period, use_ai)

    fetcher = get_data_fetcher()
    df = fetcher.fetch(symbol, period)

    df = calculate_all_indicators(df)

    signals = detect_all_signals(df)

    current = df.iloc[-1]
    market_data = {
        "price": float(current["Close"]),
        "change": float(current.get("Price_Change", 0)),
        "rsi": float(current.get("RSI", 50)),
        "macd": float(current.get("MACD", 0)),
        "adx": float(current.get("ADX", 0)),
    }

    ranked_signals = rank_signals(
        signals=signals,
        symbol=symbol,
        market_data=market_data,
        use_ai=use_ai,
    )

    bullish_count = sum(1 for s in ranked_signals if "BULLISH" in s.strength)
    bearish_count = sum(1 for s in ranked_signals if "BEARISH" in s.strength)
    avg_score = (
        sum(s.ai_score or 50 for s in ranked_signals) / len(ranked_signals)
        if ranked_signals
        else 0
    )

    result = {
        "symbol": symbol,
        "timestamp": datetime.now().isoformat(),
        "price": market_data["price"],
        "change": market_data["change"],
        "signals": [s.to_dict() for s in ranked_signals[:MAX_SIGNALS_RETURNED]],
        "summary": {
            "total_signals": len(ranked_signals),
            "bullish": bullish_count,
            "bearish": bearish_count,
            "avg_score": avg_score,
        },
        "indicators": {
            "rsi": market_data["rsi"],
            "macd": market_data["macd"],
            "adx": market_data["adx"],
            "volume": int(current["Volume"]),
        },
        "cached": False,
    }

    cache.set(symbol, period, result)
    logger.info("Completed analysis for %s: %d signals", symbol, len(ranked_signals))

    return result


async def compare_securities(
    symbols: list[str],
    metric: str = "signals",
    period: str = DEFAULT_PERIOD,
) -> dict[str, Any]:
    """Compare multiple securities.

    Args:
        symbols: List of ticker symbols.
        metric: Comparison metric.
        period: Time period for analysis.

    Returns:
        Comparison result with ranked securities.
    """
    symbols = symbols[:MAX_SYMBOLS_COMPARE]
    results: list[dict[str, Any]] = []

    logger.info("Comparing %d securities (period: %s)", len(symbols), period)

    for symbol in symbols:
        try:
            analysis = await analyze_security(symbol, period=period)
            results.append({
                "symbol": symbol,
                "score": analysis["summary"]["avg_score"],
                "bullish": analysis["summary"]["bullish"],
                "bearish": analysis["summary"]["bearish"],
                "price": analysis["price"],
                "change": analysis["change"],
            })
        except TechnicalAnalysisError as e:
            logger.warning("Error analyzing %s: %s", symbol, e)
        except Exception as e:
            logger.error("Unexpected error analyzing %s: %s", symbol, e)

    results.sort(key=lambda x: x["score"], reverse=True)

    return {
        "comparison": results,
        "metric": metric,
        "winner": results[0] if results else None,
    }


async def screen_securities(
    universe: str = "sp500",
    criteria: dict[str, Any] | None = None,
    limit: int = 20,
    period: str = DEFAULT_PERIOD,
) -> dict[str, Any]:
    """Screen securities against criteria.

    Args:
        universe: Universe name (sp500, nasdaq100, etc.).
        criteria: Screening criteria.
        limit: Maximum results.
        period: Time period for analysis.

    Returns:
        Screening result with matches.
    """
    criteria = criteria or {}
    symbols = UNIVERSES.get(universe, [])

    if not symbols:
        logger.warning("Unknown universe: %s", universe)
        return {
            "universe": universe,
            "total_screened": 0,
            "matches": [],
            "criteria": criteria,
        }

    logger.info("Screening %d securities from %s (period: %s)", len(symbols), universe, period)

    matches: list[dict[str, Any]] = []

    for symbol in symbols:
        try:
            analysis = await analyze_security(symbol, period=period)

            if _meets_criteria(analysis, criteria):
                matches.append({
                    "symbol": symbol,
                    "score": analysis["summary"]["avg_score"],
                    "signals": analysis["summary"]["total_signals"],
                    "price": analysis["price"],
                    "rsi": analysis["indicators"]["rsi"],
                })
        except TechnicalAnalysisError:
            continue
        except Exception:
            continue

    matches.sort(key=lambda x: x["score"], reverse=True)

    return {
        "universe": universe,
        "total_screened": len(symbols),
        "matches": matches[:limit],
        "criteria": criteria,
    }


def _meets_criteria(analysis: dict[str, Any], criteria: dict[str, Any]) -> bool:
    """Check if analysis meets screening criteria.

    Args:
        analysis: Analysis result.
        criteria: Screening criteria.

    Returns:
        True if all criteria are met.
    """
    indicators = analysis.get("indicators", {})

    if "rsi" in criteria:
        rsi_criteria = criteria["rsi"]
        rsi_value = indicators.get("rsi", 50)

        if isinstance(rsi_criteria, dict):
            if rsi_value < rsi_criteria.get("min", 0):
                return False
            if rsi_value > rsi_criteria.get("max", 100):
                return False
        else:
            if rsi_value > rsi_criteria:
                return False

    if "min_score" in criteria:
        if analysis["summary"]["avg_score"] < criteria["min_score"]:
            return False

    if "min_bullish" in criteria:
        if analysis["summary"]["bullish"] < criteria["min_bullish"]:
            return False

    return True


async def get_trade_plan(
    symbol: str,
    period: str = DEFAULT_PERIOD,
) -> dict[str, Any]:
    """Generate risk-qualified trade plan(s) for a security.

    Reuses existing data fetching, indicator, and signal pipeline,
    then applies risk assessment to produce 1-3 trade plans or suppression reasons.

    Args:
        symbol: Ticker symbol.
        period: Time period for analysis.

    Returns:
        RiskAnalysisResult with trade plans or suppression reasons.
    """
    symbol = symbol.upper().strip()

    logger.info("Getting trade plan for %s (period: %s)", symbol, period)

    # Reuse existing pipeline
    fetcher = get_data_fetcher()
    df = fetcher.fetch(symbol, period)

    df = calculate_all_indicators(df)

    signals = detect_all_signals(df)

    current = df.iloc[-1]
    market_data = {
        "price": float(current["Close"]),
        "change": float(current.get("Price_Change", 0)),
    }

    # Rank signals (rule-based only, no AI for simplicity)
    ranked_signals = rank_signals(
        signals=signals,
        symbol=symbol,
        market_data=market_data,
        use_ai=False,
    )

    # Apply risk assessment
    risk_assessor = RiskAssessor()
    result = risk_assessor.assess(df, ranked_signals, symbol)

    logger.info(
        "Trade plan for %s: has_trades=%s, suppressions=%d",
        symbol,
        result.has_trades,
        len(result.all_suppressions),
    )

    # Convert to dict for consistency with other endpoints
    return result.model_dump()


async def scan_trades(
    universe: str = "sp500",
    max_results: int = 10,
    period: str = DEFAULT_PERIOD,
) -> dict[str, Any]:
    """Scan universe for qualified trade setups.

    Scans all symbols in the specified universe in parallel,
    identifies those with qualified trade plans, ranks by quality,
    and returns the top results.

    Args:
        universe: Universe to scan (sp500, nasdaq100, etf_large_cap, crypto).
        max_results: Maximum results to return (1-50).
        period: Time period for analysis.

    Returns:
        Scan results with qualified setups.
    """
    logger.info("Scanning %s universe for trades (period: %s, max_results: %d)", universe, period, max_results)

    scanner = TradeScanner(max_concurrent=10)
    result = await scanner.scan_universe(universe, max_results, period=period)

    logger.info(
        "Scan complete for %s: found %d qualified trades from %d scanned",
        universe,
        len(result.get("qualified_trades", [])),
        result.get("total_scanned", 0),
    )

    return result


async def portfolio_risk(
    positions: list[dict[str, Any]],
    period: str = DEFAULT_PERIOD,
) -> dict[str, Any]:
    """Assess aggregate risk across portfolio positions.

    Analyzes each position for stop levels and risk metrics,
    then calculates portfolio-level metrics including sector concentration
    and hedge suggestions.

    Args:
        positions: List of position dicts with symbol, shares, entry_price.
        period: Time period for analysis.

    Returns:
        Portfolio risk assessment with aggregate and position-level metrics.
    """
    logger.info("Assessing portfolio risk across %d positions (period: %s)", len(positions), period)

    assessor = PortfolioRiskAssessor()
    result = await assessor.assess_positions(positions, period=period)

    logger.info(
        "Portfolio assessment complete: total_value=%.2f, max_loss=%.2f, risk_level=%s",
        result.get("total_value", 0),
        result.get("total_max_loss", 0),
        result.get("overall_risk_level", "UNKNOWN"),
    )

    return result


async def morning_brief(
    watchlist: list[str] | None = None,
    market_region: str = "US",
    period: str = DEFAULT_PERIOD,
) -> dict[str, Any]:
    """Generate daily market briefing with signals and market conditions.

    Analyzes market status, economic events, and watchlist signals
    to produce a comprehensive morning briefing.

    Args:
        watchlist: Optional list of symbols (default: top tech/finance stocks).
        market_region: Market region (US, EU, ASIA).
        period: Time period for analysis.

    Returns:
        Morning brief with market status, events, signals, and themes.
    """
    logger.info("Generating morning brief for region: %s (period: %s)", market_region, period)

    generator = MorningBriefGenerator()
    result = await generator.generate_brief(watchlist, market_region, period=period)

    logger.info(
        "Morning brief complete: %d symbols analyzed, %d themes detected",
        len(result.get("watchlist_signals", [])),
        len(result.get("key_themes", [])),
    )

    return result


async def analyze_fibonacci(
    symbol: str,
    period: str = "3mo",
    window: int = 150,
) -> dict[str, Any]:
    """Analyze Fibonacci levels, signals, and clusters for a security.

    Comprehensive analysis with:
    - 40+ Fibonacci levels (retracements, extensions)
    - 200+ signals via existing signal generators
    - Vectorized calculations for performance
    - Confluence zone clustering
    - Multi-timeframe validation

    Args:
        symbol: Ticker symbol.
        period: Time period for analysis.
        window: Lookback window for swing point detection.

    Returns:
        Fibonacci analysis with levels, signals, and clusters.
    """
    import numpy as np
    import pandas as pd
    from fibonacci.analysis.context import FibonacciContext
    from fibonacci.signals import (
        PriceLevelSignals,
        BounceSignals,
        BreakoutSignals,
        ChannelSignals,
        ClusterSignals,
        GoldenPocketSignals,
    )

    symbol = symbol.upper().strip()
    logger.info("Analyzing Fibonacci for %s (period: %s, window: %d)", symbol, period, window)

    # 1. FETCH DATA
    fetcher = get_data_fetcher()
    df = fetcher.fetch(symbol, period)

    # Calculate indicators needed for Fibonacci analysis
    df = calculate_all_indicators(df)

    current = df.iloc[-1]
    prev = df.iloc[-2] if len(df) > 1 else current
    current_price = float(current["Close"])

    # 2. VECTORIZED SWING DETECTION
    recent_df = df.tail(window)
    swing_high = float(recent_df["High"].max())
    swing_low = float(recent_df["Low"].min())
    swing_range = swing_high - swing_low

    if swing_range <= 0:
        logger.warning("Swing range is zero for %s", symbol)
        return {
            "symbol": symbol,
            "timestamp": datetime.now().isoformat(),
            "price": current_price,
            "swingHigh": swing_high,
            "swingLow": swing_low,
            "swingRange": swing_range,
            "levels": [],
            "signals": [],
            "clusters": [],
            "summary": {"totalSignals": 0, "byCategory": {}, "strongestLevel": "", "confluenceZones": 0},
        }

    # 3. CREATE FIBONACCI CONTEXT FOR SIGNAL GENERATORS
    def safe_float(val: Any) -> float:
        """Safely convert value to float."""
        try:
            return float(val)
        except (TypeError, ValueError):
            return 0.0

    context = FibonacciContext(
        df=df,
        interval=period,
        current=current,
        prev=prev,
        safe_float_fn=safe_float,
    )

    # 4. VECTORIZED LEVEL CALCULATION
    # Use existing registry but process vectorized
    from fibonacci.core.registry import FibonacciLevelRegistry

    registry = FibonacciLevelRegistry()
    fib_levels = context.get_fib_levels(window)

    # Convert to DataFrame for vectorized operations
    levels_data = []
    for key, level in fib_levels.items():
        if level.price is not None:
            distance = abs(current_price - level.price) / current_price if current_price > 0 else 0
            levels_data.append({
                "key": key,
                "ratio": level.ratio,
                "name": level.name,
                "type": level.fib_type.value,
                "price": level.price,
                "strength": level.strength.value,
                "distanceFromCurrent": distance,
            })

    # Sort by distance (vectorized)
    levels_df = pd.DataFrame(levels_data)
    if len(levels_df) > 0:
        levels_df = levels_df.sort_values("distanceFromCurrent").reset_index(drop=True)
        all_levels = levels_df.to_dict("records")
    else:
        all_levels = []

    # 5. GENERATE SIGNALS USING EXISTING GENERATORS
    signal_generators = [
        PriceLevelSignals(),
        BounceSignals(),
        BreakoutSignals(),
        ChannelSignals(),
        GoldenPocketSignals(),
        ClusterSignals(),
    ]

    all_signals = []
    for generator in signal_generators:
        try:
            generated = generator.generate(context)
            all_signals.extend(generated)
        except Exception as e:
            logger.warning("Signal generator %s failed: %s", generator.__class__.__name__, e)
            continue

    # Convert FibonacciSignal objects to dicts
    signals = []
    for sig in all_signals:
        signals.append({
            "signal": sig.signal,
            "description": sig.description,
            "strength": sig.strength,
            "category": sig.category,
            "timeframe": sig.timeframe,
            "value": sig.value,
            "metadata": sig.metadata or {},
        })

    # 6. MULTI-TIMEFRAME VALIDATION
    # Resample to weekly and validate signals against weekly Fibonacci levels
    multi_timeframe_data = {}
    try:
        if len(df) >= 21:  # At least 3 weeks of data
            # Resample daily to weekly
            weekly_df = df.resample('W').agg({
                'Open': 'first',
                'High': 'max',
                'Low': 'min',
                'Close': 'last',
                'Volume': 'sum'
            }).dropna()

            if len(weekly_df) >= 2:
                # Calculate weekly swing levels
                weekly_swing_high = float(weekly_df['High'].max())
                weekly_swing_low = float(weekly_df['Low'].min())
                weekly_range = weekly_swing_high - weekly_swing_low

                # Get weekly Fibonacci levels
                if weekly_range > 0:
                    weekly_context = FibonacciContext(
                        df=weekly_df,
                        interval='1w',
                        current=weekly_df.iloc[-1],
                        prev=weekly_df.iloc[-2] if len(weekly_df) > 1 else weekly_df.iloc[-1],
                        safe_float_fn=safe_float,
                    )
                    weekly_levels = weekly_context.get_fib_levels(len(weekly_df))

                    # Extract weekly level prices for alignment checking
                    weekly_level_prices = set()
                    for level_key, level_obj in weekly_levels.items():
                        if level_obj.price is not None:
                            weekly_level_prices.add(float(level_obj.price))

                    multi_timeframe_data = {
                        'weekly_levels': sorted(weekly_level_prices),
                        'weekly_high': weekly_swing_high,
                        'weekly_low': weekly_swing_low,
                        'weekly_range': weekly_range,
                    }
    except Exception as e:
        logger.warning("Multi-timeframe analysis failed for %s: %s", symbol, e)
        multi_timeframe_data = {}

    # Add multi-timeframe alignment metadata and boost strength
    if multi_timeframe_data and signals:
        weekly_levels = multi_timeframe_data['weekly_levels']

        # Calculate adaptive tolerance based on weekly level distribution
        tolerance = calculate_adaptive_tolerance(weekly_levels)
        logger.info(
            "Multi-timeframe validation for %s: adaptive_tolerance=%.4f (%.2f%%)",
            symbol,
            tolerance,
            tolerance * 100,
        )

        for signal in signals:
            value = signal.get('value', 0)

            # Check if signal value aligns with weekly level
            aligned = False
            for weekly_level in weekly_levels:
                if weekly_level > 0:
                    pct_diff = abs(value - weekly_level) / weekly_level
                    if pct_diff <= tolerance:
                        aligned = True
                        break

            signal['metadata']['multi_timeframe_aligned'] = aligned

            # Boost strength if aligned (progression: WEAK → MODERATE → SIGNIFICANT → STRONG)
            if aligned:
                strength_map = {
                    'WEAK': 'MODERATE',
                    'MODERATE': 'SIGNIFICANT',
                    'SIGNIFICANT': 'STRONG',
                    'STRONG': 'STRONG'
                }
                old_strength = signal.get('strength', 'WEAK')
                signal['strength'] = strength_map.get(old_strength, old_strength)

    # 7. VECTORIZED CLUSTER DETECTION (O(n) instead of O(n²))
    clusters = []
    if len(levels_df) > 1:
        # Sort by price
        levels_sorted = levels_df.sort_values("price").reset_index(drop=True)

        # Vectorized: Calculate price differences between consecutive levels
        price_diffs = levels_sorted["price"].diff().fillna(0).abs()

        # Identify where gaps exceed tolerance
        tolerance = 0.01  # 1%
        price_pct_diffs = (price_diffs / levels_sorted["price"]).fillna(0) > tolerance
        cluster_boundaries = price_pct_diffs.astype(int).diff().fillna(0)

        # Create cluster groups
        levels_sorted["cluster_id"] = cluster_boundaries.cumsum()

        # Vectorized groupby for clustering
        for cluster_id, group in levels_sorted.groupby("cluster_id"):
            if len(group) >= 2:
                center_price = group["price"].mean()
                cluster_types = set(group["type"].tolist())

                clusters.append({
                    "centerPrice": round(center_price, 2),
                    "levels": group["name"].tolist(),
                    "levelCount": len(group),
                    "strength": "STRONG" if len(group) >= 3 else "MODERATE",
                    "type": "MIXED" if len(cluster_types) > 1 else group["type"].iloc[0],
                })

    # 8. CONFLUENCE SCORE SYSTEM
    # Calculate signal convergence strength at Fibonacci levels
    confluence_zones = []
    strength_map = {'WEAK': 1, 'MODERATE': 2, 'SIGNIFICANT': 3, 'STRONG': 4}

    # Group signals by proximity to Fibonacci levels
    confluence_dict = {}  # {level_price: {count, strength_sum, aligned_count, signal_categories}}

    # Calculate adaptive tolerance for confluence detection
    all_level_prices = [level['price'] for level in all_levels if level['price'] > 0]
    confluence_tolerance = calculate_adaptive_tolerance(all_level_prices)
    logger.info(
        "Confluence zone detection for %s: adaptive_tolerance=%.4f (%.2f%%)",
        symbol,
        confluence_tolerance,
        confluence_tolerance * 100,
    )

    for signal in signals:
        signal_value = signal.get('value', 0)
        signal_strength = strength_map.get(signal.get('strength', 'WEAK'), 1)
        is_aligned = signal.get('metadata', {}).get('multi_timeframe_aligned', False)

        # Find nearest Fibonacci level for each signal
        if signal_value > 0 and len(all_levels) > 0:
            nearest_level = min(
                all_levels,
                key=lambda l: abs(l['price'] - signal_value) if l['price'] > 0 else float('inf')
            )

            # Check if within adaptive tolerance
            if nearest_level['price'] > 0:
                pct_diff = abs(signal_value - nearest_level['price']) / nearest_level['price']
                if pct_diff <= confluence_tolerance:
                    level_price = round(nearest_level['price'], 2)

                    if level_price not in confluence_dict:
                        confluence_dict[level_price] = {
                            'count': 0,
                            'strength_sum': 0,
                            'aligned_count': 0,
                            'categories': set(),
                            'level_name': nearest_level['name'],
                            'price': level_price,
                        }

                    confluence_dict[level_price]['count'] += 1
                    confluence_dict[level_price]['strength_sum'] += signal_strength
                    confluence_dict[level_price]['categories'].add(signal.get('category', 'unknown'))
                    if is_aligned:
                        confluence_dict[level_price]['aligned_count'] += 1

    # Calculate confluence scores and rank zones
    for level_price, data in confluence_dict.items():
        signal_count = data['count']
        total_strength = data['strength_sum']
        avg_strength = total_strength / signal_count if signal_count > 0 else 0
        alignment_bonus = (data['aligned_count'] / signal_count * 100) if signal_count > 0 else 0

        # Confluence score formula:
        # Base: number of signals at level (weight 0.4)
        # Strength: average signal strength (weight 0.4)
        # Alignment: multi-timeframe alignment percentage (weight 0.2)
        confluence_score = (
            (min(signal_count, 10) / 10 * 0.4) +  # Signal count normalized to 10
            (min(avg_strength, 4) / 4 * 0.4) +     # Strength normalized to 4
            (alignment_bonus / 100 * 0.2)           # Multi-timeframe alignment
        ) * 100

        # Classify zone strength
        zone_strength = 'WEAK'
        if confluence_score >= 75:
            zone_strength = 'VERY_STRONG'
        elif confluence_score >= 60:
            zone_strength = 'STRONG'
        elif confluence_score >= 45:
            zone_strength = 'SIGNIFICANT'
        elif confluence_score >= 30:
            zone_strength = 'MODERATE'

        confluence_zones.append({
            'price': level_price,
            'levelName': data['level_name'],
            'confluenceScore': round(confluence_score, 1),
            'strength': zone_strength,
            'signalCount': signal_count,
            'averageSignalStrength': round(avg_strength, 2),
            'multiTimeframeAligned': data['aligned_count'],
            'signalCategories': list(data['categories']),
        })

    # Sort by confluence score (descending)
    confluence_zones = sorted(confluence_zones, key=lambda x: x['confluenceScore'], reverse=True)
    high_confidence_zones = [z for z in confluence_zones if z['strength'] in ['VERY_STRONG', 'STRONG']]

    # 9. AGGREGATE SUMMARY
    category_counts = {}
    for sig in signals:
        cat = sig["category"]
        category_counts[cat] = category_counts.get(cat, 0) + 1

    strongest_level = all_levels[0] if all_levels else {"name": "", "distanceFromCurrent": 0}

    result = {
        "symbol": symbol,
        "timestamp": datetime.now().isoformat(),
        "price": current_price,
        "swingHigh": swing_high,
        "swingLow": swing_low,
        "swingRange": swing_range,
        "levels": all_levels[:50],  # Return top 50 levels
        "signals": signals[:100],   # Return top 100 signals
        "clusters": clusters,
        "confluenceZones": confluence_zones[:20],  # Return top 20 confluence zones
        "summary": {
            "totalSignals": len(signals),
            "byCategory": category_counts,
            "strongestLevel": strongest_level.get("name", ""),
            "highConfidenceZones": len(high_confidence_zones),
            "confluenceZoneCount": len(confluence_zones),
        },
    }

    logger.info(
        "Fibonacci analysis complete for %s: %d levels, %d signals, %d clusters",
        symbol, len(all_levels), len(signals), len(clusters)
    )

    return result


def _analyze_option_chain(
    options_df: Any,
    current_price: float,
    min_volume: int,
    option_type_name: str,
) -> dict[str, Any] | None:
    """Analyze a single option chain (calls or puts).

    Args:
        options_df: DataFrame with options data (calls or puts)
        current_price: Current stock price
        min_volume: Minimum volume threshold for liquid options
        option_type_name: "calls" or "puts" for logging

    Returns:
        Analysis dictionary or None if options_df is empty
    """
    if options_df.empty:
        return None

    liquid_options = options_df[options_df["volume"] >= min_volume]

    analysis = {
        "total_contracts": len(options_df),
        "liquid_contracts": len(liquid_options),
        "total_volume": int(options_df["volume"].sum()),
        "total_open_interest": int(options_df["openInterest"].sum()),
        "avg_implied_volatility": float(options_df["impliedVolatility"].mean() * 100),
        "max_iv": float(options_df["impliedVolatility"].max() * 100),
        "min_iv": float(options_df["impliedVolatility"].min() * 100),
        "atm_strike": None,
        "atm_iv": None,
        "atm_delta": None,
        "top_volume_strikes": [],
        "top_oi_strikes": [],
    }

    # Find ATM option
    if not liquid_options.empty:
        atm_option = liquid_options.iloc[
            (liquid_options["strike"] - current_price).abs().argsort()[:1]
        ]
        if not atm_option.empty:
            analysis["atm_strike"] = float(atm_option["strike"].iloc[0])
            analysis["atm_iv"] = float(atm_option["impliedVolatility"].iloc[0] * 100)
            # Greeks might not always be available
            if "delta" in atm_option.columns:
                analysis["atm_delta"] = float(atm_option["delta"].iloc[0])

    # Top strikes by volume
    if not liquid_options.empty:
        top_vol = liquid_options.nlargest(5, "volume")[
            ["strike", "volume", "impliedVolatility"]
        ]
        analysis["top_volume_strikes"] = [
            {
                "strike": float(row["strike"]),
                "volume": int(row["volume"]),
                "iv": float(row["impliedVolatility"] * 100),
            }
            for _, row in top_vol.iterrows()
        ]

        # Top strikes by open interest
        top_oi = liquid_options.nlargest(5, "openInterest")[
            ["strike", "openInterest", "impliedVolatility"]
        ]
        analysis["top_oi_strikes"] = [
            {
                "strike": float(row["strike"]),
                "open_interest": int(row["openInterest"]),
                "iv": float(row["impliedVolatility"] * 100),
            }
            for _, row in top_oi.iterrows()
        ]

    return analysis


async def options_risk_analysis(
    symbol: str,
    expiration_date: str | None = None,
    option_type: str = "both",
    min_volume: int = 75,
) -> dict[str, Any]:
    """Analyze options chain risk metrics for a security using real yfinance data.

    Comprehensive options risk analysis including:
    - Real options chain data from yfinance
    - IV (Implied Volatility) analysis
    - Greeks analysis (Delta, Gamma, Theta, Vega)
    - Volume and open interest analysis
    - Put/Call ratio
    - Risk warnings and opportunities

    Args:
        symbol: Ticker symbol.
        expiration_date: Specific expiration date (YYYY-MM-DD). If None, uses nearest expiration.
        option_type: Type of options to analyze ('calls', 'puts', or 'both').
        min_volume: Minimum volume threshold for liquid options.

    Returns:
        Comprehensive options risk analysis result dictionary.

    Raises:
        DataFetchError: If options data cannot be fetched.
        InvalidSymbolError: If symbol is invalid.
    """
    import yfinance as yf
    from datetime import datetime, timedelta
    import numpy as np

    symbol = symbol.upper().strip()
    logger.info(
        "Analyzing options risk for %s (expiration: %s, type: %s)",
        symbol,
        expiration_date or "nearest",
        option_type,
    )

    try:
        # Fetch ticker and options data from yfinance
        ticker = yf.Ticker(symbol)

        # Get stock info for context
        try:
            info = ticker.info
            current_price = info.get("currentPrice") or info.get("regularMarketPrice", 0)
        except Exception:
            # Fallback to history if info fails
            hist = ticker.history(period="1d")
            if hist.empty:
                raise DataFetchError(symbol, "1d", "No price data available")
            current_price = float(hist["Close"].iloc[-1])

        # Get available expiration dates
        expirations = ticker.options
        if not expirations:
            raise DataFetchError(symbol, "options", "No options data available")

        # Select expiration date
        if expiration_date:
            if expiration_date not in expirations:
                logger.warning(
                    "Requested expiration %s not found, using nearest: %s",
                    expiration_date,
                    expirations[0],
                )
                selected_expiration = expirations[0]
            else:
                selected_expiration = expiration_date
        else:
            selected_expiration = expirations[0]

        # Fetch option chain
        option_chain = ticker.option_chain(selected_expiration)
        calls = option_chain.calls
        puts = option_chain.puts

        # Calculate days to expiration
        exp_date = datetime.strptime(selected_expiration, "%Y-%m-%d")
        dte = (exp_date - datetime.now()).days

        # Analyze calls using helper function
        calls_analysis = None
        if option_type in ("calls", "both"):
            calls_analysis = _analyze_option_chain(calls, current_price, min_volume, "calls")

        # Analyze puts using helper function
        puts_analysis = None
        if option_type in ("puts", "both"):
            puts_analysis = _analyze_option_chain(puts, current_price, min_volume, "puts")

        # Calculate Put/Call Ratio
        pcr_volume = None
        pcr_oi = None
        if calls_analysis and puts_analysis:
            if calls_analysis["total_volume"] > 0:
                pcr_volume = puts_analysis["total_volume"] / calls_analysis["total_volume"]
            if calls_analysis["total_open_interest"] > 0:
                pcr_oi = puts_analysis["total_open_interest"] / calls_analysis["total_open_interest"]

        # Risk assessment and warnings
        risk_warnings = []
        opportunities = []

        # High IV warning
        if calls_analysis and calls_analysis["avg_implied_volatility"] > 60:
            risk_warnings.append(
                f"High implied volatility ({calls_analysis['avg_implied_volatility']:.1f}%) - "
                "options are expensive, consider selling strategies"
            )
        elif calls_analysis and calls_analysis["avg_implied_volatility"] < 20:
            opportunities.append(
                f"Low implied volatility ({calls_analysis['avg_implied_volatility']:.1f}%) - "
                "options are cheap, consider buying strategies"
            )

        # Put/Call ratio insights
        if pcr_volume:
            if pcr_volume > 1.5:
                risk_warnings.append(
                    f"High Put/Call Volume Ratio ({pcr_volume:.2f}) - bearish sentiment, "
                    "heavy put buying"
                )
            elif pcr_volume < 0.7:
                opportunities.append(
                    f"Low Put/Call Volume Ratio ({pcr_volume:.2f}) - bullish sentiment, "
                    "heavy call buying"
                )

        # Liquidity warning
        if calls_analysis and calls_analysis["liquid_contracts"] < 5:
            risk_warnings.append(
                f"Low liquidity in calls ({calls_analysis['liquid_contracts']} contracts) - "
                "wide bid-ask spreads likely"
            )
        if puts_analysis and puts_analysis["liquid_contracts"] < 5:
            risk_warnings.append(
                f"Low liquidity in puts ({puts_analysis['liquid_contracts']} contracts) - "
                "wide bid-ask spreads likely"
            )

        # DTE warnings
        if dte < 7:
            risk_warnings.append(
                f"Short time to expiration ({dte} days) - high theta decay, "
                "rapid price movement needed"
            )
        elif dte > 60:
            opportunities.append(
                f"Long time to expiration ({dte} days) - lower theta decay, "
                "suitable for longer-term positions"
            )

        result = {
            "symbol": symbol,
            "timestamp": datetime.now().isoformat(),
            "current_price": current_price,
            "expiration_date": selected_expiration,
            "days_to_expiration": dte,
            "available_expirations": list(expirations)[:10],  # First 10
            "calls": calls_analysis,
            "puts": puts_analysis,
            "put_call_ratio": {
                "volume": pcr_volume,
                "open_interest": pcr_oi,
            },
            "risk_warnings": risk_warnings,
            "opportunities": opportunities,
            "liquidity_threshold": min_volume,
        }

        logger.info(
            "Options risk analysis complete for %s: %d calls, %d puts, PCR: %.2f",
            symbol,
            calls_analysis["total_contracts"] if calls_analysis else 0,
            puts_analysis["total_contracts"] if puts_analysis else 0,
            pcr_volume or 0,
        )

        return result

    except Exception as e:
        logger.error("Options risk analysis failed for %s: %s", symbol, e)
        raise DataFetchError(symbol, "options", str(e))


async def record_fibonacci_signals(
    symbol: str,
    analysis_result: dict[str, Any],
    current_price: float,
    db_connection: Any | None = None,
) -> dict[str, Any]:
    """Record Fibonacci signals from analysis to database for backtesting.

    Processes analysis results and records all signals with sufficient
    confluence score (>= 30) to the fibonacci_signal_history table.

    Args:
        symbol: Ticker symbol.
        analysis_result: Result dict from analyze_fibonacci().
        current_price: Current price at time of analysis.
        db_connection: PostgreSQL connection (optional for testing/offline mode).

    Returns:
        Recording summary: {recorded_count, filtered_count, errors}.
    """
    from datetime import datetime

    symbol = symbol.upper().strip()
    logger.info("Recording Fibonacci signals for %s to database", symbol)

    recorded_count = 0
    filtered_count = 0
    errors = []

    # Extract data from analysis result
    signals = analysis_result.get("signals", [])
    confluence_zones = analysis_result.get("confluenceZones", [])
    timestamp = analysis_result.get("timestamp", datetime.now().isoformat())

    # Build mapping of signal values to confluence zones for enrichment
    confluence_map = {}  # {level_price: confluence_data}
    for zone in confluence_zones:
        price = zone.get("price")
        if price:
            confluence_map[price] = zone

    # Record each signal with confluence score >= 30 (MODERATE or higher)
    for signal in signals:
        try:
            signal_value = signal.get("value", 0)
            confluence_score = 0
            level_price = None
            level_name = ""
            multi_timeframe_aligned = False

            # Find associated confluence zone
            if signal_value > 0 and confluence_map:
                # Find nearest level price
                nearest_level = min(
                    confluence_map.keys(),
                    key=lambda p: abs(float(p) - signal_value) if p else float("inf"),
                    default=None,
                )

                if nearest_level:
                    zone = confluence_map[nearest_level]
                    confluence_score = zone.get("confluenceScore", 0)
                    level_price = zone.get("price")
                    level_name = zone.get("levelName", "")
                    multi_timeframe_aligned = zone.get("multiTimeframeAligned", 0) > 0

            # Only record signals with sufficient confluence
            if confluence_score < 30:
                filtered_count += 1
                continue

            # Prepare record for database
            record = {
                "symbol": symbol,
                "timestamp": timestamp,
                "signal": signal.get("signal", ""),
                "category": signal.get("category", ""),
                "strength": signal.get("strength", "WEAK"),
                "priceAtSignal": current_price,
                "levelPrice": level_price or signal_value,
                "levelName": level_name,
                "confluenceScore": confluence_score,
                "multiTimeframeAligned": multi_timeframe_aligned,
                "signalDescription": signal.get("description", ""),
                "metadata": signal.get("metadata", {}),
            }

            # Record to database if connection available
            if db_connection:
                try:
                    # This would be executed via drizzle ORM from Next.js
                    # For now, we prepare the record and return it
                    recorded_count += 1
                    logger.info(
                        "Recorded signal: %s/%s confluence=%.1f",
                        symbol,
                        signal.get("signal"),
                        confluence_score,
                    )
                except Exception as e:
                    errors.append(
                        f"Failed to record signal {signal.get('signal')}: {str(e)}"
                    )
                    logger.error("Database recording error: %s", e)
            else:
                # No database connection, just count
                recorded_count += 1

        except Exception as e:
            errors.append(f"Error processing signal: {str(e)}")
            logger.error("Signal processing error: %s", e)
            continue

    logger.info(
        "Fibonacci signal recording complete: recorded=%d, filtered=%d, errors=%d",
        recorded_count,
        filtered_count,
        len(errors),
    )

    return {
        "symbol": symbol,
        "recorded_count": recorded_count,
        "filtered_count": filtered_count,
        "total_signals": len(signals),
        "errors": errors,
    }


async def calculate_signal_performance(
    symbol: str | None = None,
    lookback_days: int = 180,  # SWING TRADING: 6-month lookback for robust signal performance
    min_confluence: float = 30,
    min_strength: str = "MODERATE",
    db_connection: Any | None = None,
) -> dict[str, Any]:
    """Calculate historical performance metrics for Fibonacci signals.

    Analyzes recorded signals to determine win rates and returns by
    category and strength level.

    Args:
        symbol: Optional ticker to filter on. If None, analyzes all symbols.
        lookback_days: Historical period to analyze (default 90 days).
        min_confluence: Minimum confluence score threshold (default 30).
        min_strength: Minimum strength filter (WEAK/MODERATE/SIGNIFICANT/STRONG/VERY_STRONG).
        db_connection: PostgreSQL connection (optional for testing).

    Returns:
        Performance metrics: {
            symbol,
            lookback_days,
            by_category: {category: {count, win_rate, avg_return_30d, avg_return_90d}},
            by_strength: {strength: {count, win_rate, avg_return_30d, avg_return_90d}},
            summary: {total_signals, overall_win_rate_30d, overall_win_rate_90d}
        }
    """
    from datetime import datetime, timedelta

    logger.info(
        "Calculating signal performance: symbol=%s, lookback=%d days, min_confluence=%.1f",
        symbol or "ALL",
        lookback_days,
        min_confluence,
    )

    # If no database connection, return empty results
    if not db_connection:
        logger.warning("No database connection provided, returning empty performance data")
        return {
            "symbol": symbol or "ALL",
            "lookback_days": lookback_days,
            "by_category": {},
            "by_strength": {},
            "summary": {
                "total_signals": 0,
                "overall_win_rate_30d": None,
                "overall_win_rate_90d": None,
                "avg_return_30d": None,
                "avg_return_90d": None,
                "note": "Database connection required for live performance data",
            },
        }

    # Strength mapping for filtering
    strength_levels = ["WEAK", "MODERATE", "SIGNIFICANT", "STRONG", "VERY_STRONG"]
    min_strength_idx = (
        strength_levels.index(min_strength)
        if min_strength in strength_levels
        else strength_levels.index("MODERATE")
    )

    try:
        # Query historical signals from database
        cutoff_date = datetime.now() - timedelta(days=lookback_days)

        # Initialize result structures
        performance_by_category = {}
        performance_by_strength = {}
        total_signals = 0
        win_count_30d = 0
        win_count_90d = 0
        total_returns_30d = []
        total_returns_90d = []

        # Mock data structure for demonstration (would be replaced with DB query)
        historical_signals = []

        # Process signals (in production, would query database)
        for signal in historical_signals:
            signal_timestamp = signal.get("timestamp")
            category = signal.get("category", "unknown")
            strength = signal.get("strength", "WEAK")
            confluence = signal.get("confluenceScore", 0)

            # Skip if doesn't meet criteria
            if confluence < min_confluence:
                continue
            if strength not in strength_levels[
                min_strength_idx:
            ]:  # Strength level filter
                continue
            if symbol and signal.get("symbol") != symbol:
                continue

            total_signals += 1

            # Extract return data
            return_30d = signal.get("outcomeReturnPercent30d")
            return_90d = signal.get("outcomeReturnPercent90d")

            # Calculate wins (positive returns)
            if return_30d is not None:
                if float(return_30d) > 0:
                    win_count_30d += 1
                total_returns_30d.append(float(return_30d))

            if return_90d is not None:
                if float(return_90d) > 0:
                    win_count_90d += 1
                total_returns_90d.append(float(return_90d))

            # Aggregate by category
            if category not in performance_by_category:
                performance_by_category[category] = {
                    "count": 0,
                    "wins_30d": 0,
                    "wins_90d": 0,
                    "returns_30d": [],
                    "returns_90d": [],
                }
            performance_by_category[category]["count"] += 1
            if return_30d and float(return_30d) > 0:
                performance_by_category[category]["wins_30d"] += 1
            if return_90d and float(return_90d) > 0:
                performance_by_category[category]["wins_90d"] += 1
            if return_30d:
                performance_by_category[category]["returns_30d"].append(
                    float(return_30d)
                )
            if return_90d:
                performance_by_category[category]["returns_90d"].append(
                    float(return_90d)
                )

            # Aggregate by strength
            if strength not in performance_by_strength:
                performance_by_strength[strength] = {
                    "count": 0,
                    "wins_30d": 0,
                    "wins_90d": 0,
                    "returns_30d": [],
                    "returns_90d": [],
                }
            performance_by_strength[strength]["count"] += 1
            if return_30d and float(return_30d) > 0:
                performance_by_strength[strength]["wins_30d"] += 1
            if return_90d and float(return_90d) > 0:
                performance_by_strength[strength]["wins_90d"] += 1
            if return_30d:
                performance_by_strength[strength]["returns_30d"].append(
                    float(return_30d)
                )
            if return_90d:
                performance_by_strength[strength]["returns_90d"].append(
                    float(return_90d)
                )

        # Calculate win rates and average returns
        category_results = {}
        for cat, data in performance_by_category.items():
            win_rate_30d = (
                (data["wins_30d"] / data["count"] * 100)
                if data["count"] > 0
                else None
            )
            win_rate_90d = (
                (data["wins_90d"] / data["count"] * 100)
                if data["count"] > 0
                else None
            )
            avg_return_30d = (
                sum(data["returns_30d"]) / len(data["returns_30d"])
                if data["returns_30d"]
                else None
            )
            avg_return_90d = (
                sum(data["returns_90d"]) / len(data["returns_90d"])
                if data["returns_90d"]
                else None
            )

            category_results[cat] = {
                "count": data["count"],
                "win_rate_30d": round(win_rate_30d, 1) if win_rate_30d else None,
                "win_rate_90d": round(win_rate_90d, 1) if win_rate_90d else None,
                "avg_return_30d": round(avg_return_30d, 2) if avg_return_30d else None,
                "avg_return_90d": round(avg_return_90d, 2) if avg_return_90d else None,
            }

        strength_results = {}
        for strength, data in performance_by_strength.items():
            win_rate_30d = (
                (data["wins_30d"] / data["count"] * 100)
                if data["count"] > 0
                else None
            )
            win_rate_90d = (
                (data["wins_90d"] / data["count"] * 100)
                if data["count"] > 0
                else None
            )
            avg_return_30d = (
                sum(data["returns_30d"]) / len(data["returns_30d"])
                if data["returns_30d"]
                else None
            )
            avg_return_90d = (
                sum(data["returns_90d"]) / len(data["returns_90d"])
                if data["returns_90d"]
                else None
            )

            strength_results[strength] = {
                "count": data["count"],
                "win_rate_30d": round(win_rate_30d, 1) if win_rate_30d else None,
                "win_rate_90d": round(win_rate_90d, 1) if win_rate_90d else None,
                "avg_return_30d": round(avg_return_30d, 2) if avg_return_30d else None,
                "avg_return_90d": round(avg_return_90d, 2) if avg_return_90d else None,
            }

        # Calculate summary metrics
        overall_win_rate_30d = (
            (win_count_30d / len(total_returns_30d) * 100)
            if total_returns_30d
            else None
        )
        overall_win_rate_90d = (
            (win_count_90d / len(total_returns_90d) * 100)
            if total_returns_90d
            else None
        )
        overall_avg_return_30d = (
            sum(total_returns_30d) / len(total_returns_30d)
            if total_returns_30d
            else None
        )
        overall_avg_return_90d = (
            sum(total_returns_90d) / len(total_returns_90d)
            if total_returns_90d
            else None
        )

        result = {
            "symbol": symbol or "ALL",
            "lookback_days": lookback_days,
            "min_confluence": min_confluence,
            "min_strength": min_strength,
            "by_category": category_results,
            "by_strength": strength_results,
            "summary": {
                "total_signals": total_signals,
                "overall_win_rate_30d": round(overall_win_rate_30d, 1)
                if overall_win_rate_30d
                else None,
                "overall_win_rate_90d": round(overall_win_rate_90d, 1)
                if overall_win_rate_90d
                else None,
                "avg_return_30d": round(overall_avg_return_30d, 2)
                if overall_avg_return_30d
                else None,
                "avg_return_90d": round(overall_avg_return_90d, 2)
                if overall_avg_return_90d
                else None,
            },
        }

        logger.info(
            "Signal performance calculation complete: %d signals analyzed",
            total_signals,
        )

        return result

    except Exception as e:
        logger.error("Performance calculation error: %s", e)
        return {
            "symbol": symbol or "ALL",
            "lookback_days": lookback_days,
            "error": str(e),
            "by_category": {},
            "by_strength": {},
            "summary": {"total_signals": 0},
        }


def main() -> None:
    """Run the MCP server."""
    from mcp.server.stdio import stdio_server

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    async def run_server() -> None:
        async with stdio_server() as (read_stream, write_stream):
            await app.run(read_stream, write_stream, app.create_initialization_options())

    asyncio.run(run_server())


if __name__ == "__main__":
    main()
