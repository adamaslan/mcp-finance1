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
from .formatting import format_analysis, format_comparison, format_screening
from .indicators import calculate_all_indicators
from .ranking import RankingStrategy, get_ranking_strategy, rank_signals
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
                },
                "required": ["criteria"],
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
) -> dict[str, Any]:
    """Compare multiple securities.

    Args:
        symbols: List of ticker symbols.
        metric: Comparison metric.

    Returns:
        Comparison result with ranked securities.
    """
    symbols = symbols[:MAX_SYMBOLS_COMPARE]
    results: list[dict[str, Any]] = []

    logger.info("Comparing %d securities", len(symbols))

    for symbol in symbols:
        try:
            analysis = await analyze_security(symbol, period="1mo")
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
) -> dict[str, Any]:
    """Screen securities against criteria.

    Args:
        universe: Universe name (sp500, nasdaq100, etc.).
        criteria: Screening criteria.
        limit: Maximum results.

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
            analysis = await analyze_security(symbol, period="1mo")

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
