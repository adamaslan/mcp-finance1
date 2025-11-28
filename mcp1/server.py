"""
MCP Server with GCP Backend Integration
Location: option2-gcp/mcp-server/src/technical_analysis_mcp/server.py

Smart routing: Local cache → Firestore → GCP → yfinance
"""

import asyncio
import json
import os
from datetime import datetime
from typing import Any, Optional, List, Dict

import httpx
from cachetools import TTLCache
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool
from google.cloud import firestore

# Configuration
USE_GCP = os.getenv("USE_GCP", "true").lower() == "true"
CLOUD_RUN_URL = os.getenv("CLOUD_RUN_URL", "http://localhost:8080")
PROJECT_ID = os.getenv("GCP_PROJECT_ID", "technical-analysis-prod")

# Local cache (L1): 5 minute TTL
LOCAL_CACHE = TTLCache(maxsize=100, ttl=300)

# Initialize Firestore client (L2 cache)
db = None
if USE_GCP:
    try:
        db = firestore.Client(project=PROJECT_ID)
        print("✅ Connected to Firestore")
    except Exception as e:
        print(f"⚠️  Firestore connection failed: {e}")
        USE_GCP = False

# MCP Server
app = Server("technical-analysis-gcp")


# ============================================================================
# GCP CLIENT
# ============================================================================

class GCPClient:
    """Client for GCP backend services"""
    
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.timeout = httpx.Timeout(30.0)
    
    async def analyze(self, symbol: str, period: str = "1mo", use_ai: bool = True) -> dict:
        """Trigger analysis via Cloud Run"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/api/analyze",
                json={
                    "symbol": symbol,
                    "period": period,
                    "include_ai": use_ai,
                    "security_type": "auto"
                }
            )
            response.raise_for_status()
            return response.json()
    
    async def get_signals(
        self,
        symbol: str,
        category: Optional[str] = None,
        min_score: int = 0,
        limit: int = 50
    ) -> dict:
        """Get filtered signals from GCP"""
        params = {"limit": limit}
        if category:
            params["category"] = category
        if min_score > 0:
            params["min_score"] = min_score
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                f"{self.base_url}/api/signals/{symbol}",
                params=params
            )
            response.raise_for_status()
            return response.json()
    
    async def compare(self, symbols: List[str], period: str = "1mo") -> dict:
        """Compare multiple securities"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/api/compare",
                json={"symbols": symbols, "period": period}
            )
            response.raise_for_status()
            return response.json()
    
    async def screen(
        self,
        symbols: List[str],
        criteria: dict,
        limit: int = 20
    ) -> dict:
        """Screen securities via GCP parallel processing"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/api/screen",
                json={
                    "symbols": symbols,
                    "criteria": criteria,
                    "limit": limit
                }
            )
            response.raise_for_status()
            return response.json()


gcp_client = GCPClient(CLOUD_RUN_URL) if USE_GCP else None


# ============================================================================
# SMART CACHING
# ============================================================================

def get_from_local_cache(key: str) -> Optional[dict]:
    """L1: In-memory cache (instant)"""
    if key in LOCAL_CACHE:
        print(f"✅ L1 cache hit: {key}")
        return LOCAL_CACHE[key]
    return None


def get_from_firestore(symbol: str) -> Optional[dict]:
    """L2: Firestore cache (fast, persistent)"""
    if not db:
        return None
    
    try:
        doc_ref = db.collection("signals").document(symbol)
        doc = doc_ref.get()
        
        if doc.exists:
            data = doc.to_dict()
            timestamp = data.get("timestamp")
            
            # Check if cache is valid (5 min)
            if timestamp:
                age = (datetime.now() - timestamp).total_seconds()
                if age < 300:  # 5 minutes
                    print(f"✅ L2 cache hit (Firestore): {symbol}")
                    return data
        
    except Exception as e:
        print(f"⚠️  Firestore read error: {e}")
    
    return None


def save_to_caches(key: str, symbol: str, data: dict):
    """Save to both cache levels"""
    # L1: Local cache
    LOCAL_CACHE[key] = data
    
    # L2: Firestore cache
    if db:
        try:
            doc_ref = db.collection("signals").document(symbol)
            doc_ref.set({
                **data,
                "timestamp": datetime.now(),
                "cached_at": datetime.now().isoformat()
            })
            print(f"💾 Saved to Firestore: {symbol}")
        except Exception as e:
            print(f"⚠️  Firestore write error: {e}")


# ============================================================================
# MCP TOOLS
# ============================================================================

@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools"""
    return [
        Tool(
            name="analyze_security",
            description="Analyze stock/ETF with AI-powered insights. Uses GCP for advanced features.",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "Stock/ETF ticker (e.g., AAPL, SPY, QQQ)"
                    },
                    "period": {
                        "type": "string",
                        "description": "Time period: 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y",
                        "default": "1mo"
                    },
                    "use_ai": {
                        "type": "boolean",
                        "description": "Use AI ranking (Gemini)",
                        "default": True
                    }
                },
                "required": ["symbol"]
            }
        ),
        Tool(
            name="compare_securities",
            description="Compare multiple securities with historical context",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbols": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of tickers to compare"
                    },
                    "period": {
                        "type": "string",
                        "default": "1mo"
                    }
                },
                "required": ["symbols"]
            }
        ),
        Tool(
            name="screen_securities",
            description="Screen securities with parallel GCP processing (10x faster)",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbols": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of symbols to screen"
                    },
                    "criteria": {
                        "type": "object",
                        "description": "Criteria: {'rsi_max': 35, 'trend': 'bullish', 'min_score': 70}"
                    },
                    "limit": {
                        "type": "integer",
                        "default": 20
                    }
                },
                "required": ["symbols", "criteria"]
            }
        ),
        Tool(
            name="get_historical_comparison",
            description="Compare current signals vs past 7 days (GCP only)",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "Stock/ETF ticker"
                    },
                    "days": {
                        "type": "integer",
                        "description": "Days to look back (1-30)",
                        "default": 7
                    }
                },
                "required": ["symbol"]
            }
        ),
        Tool(
            name="get_daily_summary",
            description="Get automated daily market summary (generated by Cloud Scheduler)",
            inputSchema={
                "type": "object",
                "properties": {
                    "date": {
                        "type": "string",
                        "description": "Date (YYYY-MM-DD) or 'today'",
                        "default": "today"
                    }
                }
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool calls with smart routing"""
    try:
        if name == "analyze_security":
            result = await analyze_security(**arguments)
            text = format_analysis(result)
        
        elif name == "compare_securities":
            result = await compare_securities(**arguments)
            text = format_comparison(result)
        
        elif name == "screen_securities":
            result = await screen_securities(**arguments)
            text = format_screening(result)
        
        elif name == "get_historical_comparison":
            result = await get_historical_comparison(**arguments)
            text = format_historical(result)
        
        elif name == "get_daily_summary":
            result = await get_daily_summary(**arguments)
            text = format_summary(result)
        
        else:
            text = f"Unknown tool: {name}"
        
        return [TextContent(type="text", text=text)]
    
    except Exception as e:
        error_text = f"❌ Error: {str(e)}\n\nIf GCP backend is not deployed, use Option 1 (100% Free) instead."
        return [TextContent(type="text", text=error_text)]


# ============================================================================
# TOOL IMPLEMENTATIONS
# ============================================================================

async def analyze_security(
    symbol: str,
    period: str = "1mo",
    use_ai: bool = True
) -> dict:
    """
    Smart routing for analysis:
    L1 (local cache) → L2 (Firestore) → L3 (GCP full pipeline)
    """
    symbol = symbol.upper()
    cache_key = f"{symbol}:{period}"
    
    # L1: Check local cache
    cached = get_from_local_cache(cache_key)
    if cached:
        cached['cache_level'] = 'L1_local'
        return cached
    
    # L2: Check Firestore
    cached = get_from_firestore(symbol)
    if cached:
        LOCAL_CACHE[cache_key] = cached
        cached['cache_level'] = 'L2_firestore'
        return cached
    
    # L3: Trigger GCP pipeline
    if not USE_GCP or not gcp_client:
        raise Exception("GCP backend not configured. Set USE_GCP=true and CLOUD_RUN_URL")
    
    print(f"🔄 L3 cache miss: {symbol} - triggering GCP pipeline")
    
    result = await gcp_client.analyze(symbol, period, use_ai)
    result['cache_level'] = 'L3_gcp_fresh'
    
    # Save to caches
    save_to_caches(cache_key, symbol, result)
    
    return result


async def compare_securities(symbols: List[str], period: str = "1mo") -> dict:
    """Compare securities via GCP"""
    if not USE_GCP or not gcp_client:
        raise Exception("GCP backend required for comparison")
    
    return await gcp_client.compare(symbols, period)


async def screen_securities(
    symbols: List[str],
    criteria: dict,
    limit: int = 20
) -> dict:
    """Screen securities via GCP parallel processing"""
    if not USE_GCP or not gcp_client:
        raise Exception("GCP backend required for screening")
    
    print(f"🔍 Screening {len(symbols)} symbols via GCP (parallel)")
    return await gcp_client.screen(symbols, criteria, limit)


async def get_historical_comparison(symbol: str, days: int = 7) -> dict:
    """Get historical comparison from Firestore"""
    if not db:
        raise Exception("Firestore required for historical data")
    
    symbol = symbol.upper()
    
    # Get current analysis
    current = await analyze_security(symbol)
    
    # Get historical data
    history = []
    for i in range(1, days + 1):
        date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
        try:
            doc_ref = db.collection("analysis").document(symbol).collection("history").document(date)
            doc = doc_ref.get()
            if doc.exists:
                history.append({
                    "date": date,
                    **doc.to_dict()
                })
        except:
            continue
    
    return {
        "symbol": symbol,
        "current": current,
        "history": history,
        "trend": calculate_trend(current, history)
    }


async def get_daily_summary(date: str = "today") -> dict:
    """Get daily summary from Cloud Storage"""
    if date == "today":
        date = datetime.now().strftime("%Y-%m-%d")
    
    if not db:
        raise Exception("GCP backend required for daily summaries")
    
    # Try to get from Firestore first
    try:
        doc_ref = db.collection("reports").document("daily").collection("summaries").document(date)
        doc = doc_ref.get()
        if doc.exists:
            return doc.to_dict()
    except:
        pass
    
    # If not found, it means Cloud Scheduler hasn't run yet
    return {
        "date": date,
        "status": "pending",
        "message": "Daily summary not yet generated. Cloud Scheduler runs at market close."
    }


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def calculate_trend(current: dict, history: List[dict]) -> dict:
    """Calculate trend from historical data"""
    if not history:
        return {"trend": "insufficient_data"}
    
    current_score = current.get('summary', {}).get('avg_score', 50)
    past_scores = [h.get('summary', {}).get('avg_score', 50) for h in history if 'summary' in h]
    
    if not past_scores:
        return {"trend": "insufficient_data"}
    
    avg_past = sum(past_scores) / len(past_scores)
    change = current_score - avg_past
    
    return {
        "trend": "improving" if change > 5 else "declining" if change < -5 else "stable",
        "current_score": current_score,
        "avg_past_score": avg_past,
        "change": change
    }


# ============================================================================
# FORMATTING
# ============================================================================

def format_analysis(result: dict) -> str:
    """Format analysis for Claude"""
    cache_level = result.get('cache_level', 'unknown')
    cache_emoji = {
        'L1_local': '⚡ (Local cache)',
        'L2_firestore': '💾 (Firestore cache)',
        'L3_gcp_fresh': '🔄 (Fresh from GCP)'
    }.get(cache_level, '')
    
    output = f"""
📊 {result['symbol']} Technical Analysis {cache_emoji}
{'🟢' if result.get('change', 0) > 0 else '🔴'} Price: ${result.get('price', 0):.2f} ({result.get('change', 0):+.2f}%)

"""
    
    if 'summary' in result:
        summary = result['summary']
        output += f"""📈 Signal Summary:
• Total: {summary.get('total_signals', 0)}
• Bullish: {summary.get('bullish', 0)} | Bearish: {summary.get('bearish', 0)}
• AI Score: {summary.get('avg_score', 0):.1f}/100

"""
    
    if 'indicators' in result:
        ind = result['indicators']
        output += f"""📊 Key Indicators:
• RSI: {ind.get('rsi', 0):.1f}
• MACD: {ind.get('macd', 0):.4f}
• ADX: {ind.get('adx', 0):.1f}

"""
    
    if 'signals' in result:
        output += "🎯 Top 10 AI-Ranked Signals:\n"
        for i, sig in enumerate(result['signals'][:10], 1):
            score = sig.get('ai_score', 50)
            indicator = "🔥" if score >= 80 else "⚡" if score >= 60 else "📊"
            output += f"\n{i}. {indicator} [{score}] {sig.get('signal', 'Unknown')}\n"
            output += f"   {sig.get('desc', '')}\n"
            if sig.get('ai_reasoning'):
                output += f"   💡 {sig['ai_reasoning']}\n"
    
    return output


def format_comparison(result: dict) -> str:
    """Format comparison"""
    output = f"📊 Comparing {len(result.get('comparison', []))} Securities\n\n"
    
    if result.get('winner'):
        winner = result['winner']
        output += f"🏆 Top Pick: {winner.get('symbol')} (Score: {winner.get('score', 0):.1f})\n\n"
    
    for i, item in enumerate(result.get('comparison', []), 1):
        output += f"{i}. {item.get('symbol')} - ${item.get('price', 0):.2f} ({item.get('change', 0):+.2f}%)\n"
        output += f"   AI Score: {item.get('score', 0):.1f} | RSI: {item.get('rsi', 0):.1f}\n\n"
    
    return output


def format_screening(result: dict) -> str:
    """Format screening results"""
    output = f"🔍 Screened {result.get('total_screened', 0)} securities\n"
    output += f"✅ Found {len(result.get('matches', []))} matches\n\n"
    
    for i, match in enumerate(result.get('matches', [])[:20], 1):
        output += f"{i}. {match.get('symbol')} - Score: {match.get('score', 0):.1f}\n"
        output += f"   Price: ${match.get('price', 0):.2f} | RSI: {match.get('rsi', 0):.1f}\n\n"
    
    return output


def format_historical(result: dict) -> str:
    """Format historical comparison"""
    output = f"📈 Historical Analysis: {result.get('symbol')}\n\n"
    
    trend = result.get('trend', {})
    output += f"Trend: {trend.get('trend', 'unknown').upper()}\n"
    output += f"Current Score: {trend.get('current_score', 0):.1f}\n"
    output += f"Past Avg: {trend.get('avg_past_score', 0):.1f}\n"
    output += f"Change: {trend.get('change', 0):+.1f}\n\n"
    
    output += "📊 Historical Data Points:\n"
    for h in result.get('history', [])[:7]:
        output += f"• {h.get('date')}: Score {h.get('summary', {}).get('avg_score', 0):.1f}\n"
    
    return output


def format_summary(result: dict) -> str:
    """Format daily summary"""
    output = f"📊 Daily Market Summary - {result.get('date')}\n\n"
    
    if result.get('status') == 'pending':
        return output + result.get('message', '')
    
    output += "🔥 Top Bullish:\n"
    for item in result.get('top_bullish', [])[:3]:
        output += f"• {item.get('symbol')}: {item.get('bullish', 0)} signals\n"
    
    output += "\n🔻 Top Bearish:\n"
    for item in result.get('top_bearish', [])[:3]:
        output += f"• {item.get('symbol')}: {item.get('bearish', 0)} signals\n"
    
    return output


# ============================================================================
# MAIN
# ============================================================================

async def main():
    """Run MCP server"""
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())