"""MCP Server entry point for Technical Analysis.

Minimal server implementation that defines MCP tools and routes
to the appropriate service functions using dependency injection.
"""

import asyncio
import logging
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
                        "default": "1mo",
                        "description": "Time period (1mo, 3mo, 6mo, 1y)",
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
                        "description": "Time period for analysis (1mo, 3mo, 6mo, 1y, etc)",
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
                        "description": "Time period for analysis (1mo, 3mo, 6mo, 1y, etc)",
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
                        "default": "1mo",
                        "description": "Time period (1mo, 3mo, 6mo, 1y)",
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
                        "description": "Time period for analysis (1mo, 3mo, 6mo, 1y, etc)",
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
                        "description": "Time period for analysis (1mo, 3mo, 6mo, 1y, etc)",
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
                        "description": "Time period for analysis (1mo, 3mo, 6mo, 1y, etc)",
                    },
                },
                "required": [],
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
    period: str = "3mo",
) -> dict[str, Any]:
    """Compare multiple securities.

    Args:
        symbols: List of ticker symbols.
        metric: Comparison metric.
        period: Time period for analysis (1mo, 3mo, 6mo, 1y, etc).

    Returns:
        Comparison result with ranked securities.
    """
    symbols = symbols[:MAX_SYMBOLS_COMPARE]
    results: list[dict[str, Any]] = []

    logger.info("Comparing %d securities", len(symbols))

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
    period: str = "3mo",
) -> dict[str, Any]:
    """Screen securities against criteria.

    Args:
        universe: Universe name (sp500, nasdaq100, etc.).
        criteria: Screening criteria.
        limit: Maximum results.
        period: Time period for analysis (1mo, 3mo, 6mo, 1y, etc).

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

    logger.info("Screening %d securities from %s", len(symbols), universe)

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
    period: str = "3mo",
) -> dict[str, Any]:
    """Scan universe for qualified trade setups.

    Scans all symbols in the specified universe in parallel,
    identifies those with qualified trade plans, ranks by quality,
    and returns the top results.

    Args:
        universe: Universe to scan (sp500, nasdaq100, etf_large_cap, crypto).
        max_results: Maximum results to return (1-50).
        period: Time period for analysis (1mo, 3mo, 6mo, 1y, etc).

    Returns:
        Scan results with qualified setups.
    """
    logger.info("Scanning %s universe for trades (max_results: %d)", universe, max_results)

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
    period: str = "3mo",
) -> dict[str, Any]:
    """Assess aggregate risk across portfolio positions.

    Analyzes each position for stop levels and risk metrics,
    then calculates portfolio-level metrics including sector concentration
    and hedge suggestions.

    Args:
        positions: List of position dicts with symbol, shares, entry_price.
        period: Time period for analysis (1mo, 3mo, 6mo, 1y, etc).

    Returns:
        Portfolio risk assessment with aggregate and position-level metrics.
    """
    logger.info("Assessing portfolio risk across %d positions", len(positions))

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
    period: str = "3mo",
) -> dict[str, Any]:
    """Generate daily market briefing with signals and market conditions.

    Analyzes market status, economic events, and watchlist signals
    to produce a comprehensive morning briefing.

    Args:
        watchlist: Optional list of symbols (default: top tech/finance stocks).
        market_region: Market region (US, EU, ASIA).
        period: Time period for analysis (1mo, 3mo, 6mo, 1y, etc).

    Returns:
        Morning brief with market status, events, signals, and themes.
    """
    logger.info("Generating morning brief for region: %s", market_region)

    generator = MorningBriefGenerator()
    result = await generator.generate_brief(watchlist, market_region, period=period)

    logger.info(
        "Morning brief complete: %d symbols analyzed, %d themes detected",
        len(result.get("watchlist_signals", [])),
        len(result.get("key_themes", [])),
    )

    return result


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
