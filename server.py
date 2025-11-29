# Dependencies
# src/technical_analysis_mcp/server.py

from mcp.server import Server
from mcp.types import Tool, TextContent
import yfinance as yf
from cachetools import TTLCache
from datetime import datetime
import pandas as pd
from .analyzer import TechnicalAnalyzer
from .ranking import rank_signals_local, rank_signals_ai
import os

# In-memory cache (5 min TTL, max 100 symbols)
cache = TTLCache(maxsize=100, ttl=300)

app = Server("technical-analysis-mcp")

@app.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="analyze_security",
            description="Analyze any stock/ETF with 150+ signals",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {"type": "string"},
                    "period": {"type": "string", "default": "1mo"},
                    "use_ai": {"type": "boolean", "default": False}
                },
                "required": ["symbol"]
            }
        ),
        Tool(
            name="compare_securities",
            description="Compare multiple stocks/ETFs",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbols": {"type": "array", "items": {"type": "string"}},
                    "metric": {"type": "string", "default": "signals"}
                },
                "required": ["symbols"]
            }
        ),
        Tool(
            name="screen_securities",
            description="Screen for securities matching criteria",
            inputSchema={
                "type": "object",
                "properties": {
                    "universe": {"type": "string", "default": "sp500"},
                    "criteria": {"type": "object"},
                    "limit": {"type": "integer", "default": 20}
                },
                "required": ["criteria"]
            }
        )
    ]

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    if name == "analyze_security":
        result = await analyze_security(**arguments)
        return [TextContent(type="text", text=format_analysis(result))]
    
    elif name == "compare_securities":
        result = await compare_securities(**arguments)
        return [TextContent(type="text", text=format_comparison(result))]
    
    elif name == "screen_securities":
        result = await screen_securities(**arguments)
        return [TextContent(type="text", text=format_screening(result))]

async def analyze_security(symbol: str, period: str = "1mo", use_ai: bool = False):
    """
    Analyze stock/ETF with free data (yfinance)
    """
    symbol = symbol.upper()
    cache_key = f"{symbol}:{period}"
    
    # Check cache
    if cache_key in cache:
        print(f"✅ Cache hit for {symbol}")
        cached = cache[cache_key]
        cached["cached"] = True
        return cached
    
    print(f"📊 Fetching {symbol} from yfinance...")
    
    # Initialize analyzer (from your original code)
    analyzer = TechnicalAnalyzer(
        symbol=symbol,
        period=period,
        gemini_api_key=None  # No API key needed for local
    )
    
    # Run analysis (all local, free)
    analyzer.fetch_data()
    analyzer.calculate_indicators()
    analyzer.detect_signals()
    
    # Ranking
    if use_ai and os.getenv("GEMINI_API_KEY"):
        # Optional: Call Cloud Run for AI ranking
        analyzer.rank_signals_with_ai()
    else:
        # Use rule-based ranking (free, fast)
        rank_signals_local(analyzer.signals)
    
    # Build result
    current = analyzer.data.iloc[-1]
    result = {
        "symbol": symbol,
        "timestamp": datetime.now().isoformat(),
        "price": float(current["Close"]),
        "change": float(current["Price_Change"]),
        "signals": analyzer.signals[:50],  # Top 50
        "summary": {
            "total_signals": len(analyzer.signals),
            "bullish": sum(1 for s in analyzer.signals if "BULLISH" in s["strength"]),
            "bearish": sum(1 for s in analyzer.signals if "BEARISH" in s["strength"]),
            "avg_score": sum(s.get("ai_score", 50) for s in analyzer.signals) / len(analyzer.signals)
        },
        "indicators": {
            "rsi": float(current["RSI"]),
            "macd": float(current["MACD"]),
            "adx": float(current["ADX"]),
            "volume": int(current["Volume"])
        },
        "cached": False
    }
    
    # Cache result
    cache[cache_key] = result
    
    return result

async def compare_securities(symbols: list, metric: str = "signals"):
    """
    Compare multiple securities
    """
    results = []
    
    for symbol in symbols[:10]:  # Limit to 10 for speed
        try:
            analysis = await analyze_security(symbol, period="1mo")
            results.append({
                "symbol": symbol,
                "score": analysis["summary"]["avg_score"],
                "bullish": analysis["summary"]["bullish"],
                "bearish": analysis["summary"]["bearish"],
                "price": analysis["price"],
                "change": analysis["change"]
            })
        except Exception as e:
            print(f"❌ Error analyzing {symbol}: {e}")
    
    # Sort by score
    results.sort(key=lambda x: x["score"], reverse=True)
    
    return {
        "comparison": results,
        "metric": metric,
        "winner": results[0] if results else None
    }

async def screen_securities(universe: str, criteria: dict, limit: int = 20):
    """
    Screen securities by criteria (all local, free)
    """
    # Get universe symbols (hardcoded lists, no DB needed)
    from .universes import UNIVERSES
    
    symbols = UNIVERSES.get(universe, [])
    matches = []
    
    print(f"🔍 Screening {len(symbols)} securities...")
    
    for symbol in symbols:
        try:
            analysis = await analyze_security(symbol, period="1mo")
            
            # Check criteria
            if meets_criteria(analysis, criteria):
                matches.append({
                    "symbol": symbol,
                    "score": analysis["summary"]["avg_score"],
                    "signals": analysis["summary"]["total_signals"],
                    "price": analysis["price"],
                    "rsi": analysis["indicators"]["rsi"]
                })
        except:
            continue
    
    # Sort and limit
    matches.sort(key=lambda x: x["score"], reverse=True)
    
    return {
        "universe": universe,
        "total_screened": len(symbols),
        "matches": matches[:limit],
        "criteria": criteria
    }

def meets_criteria(analysis: dict, criteria: dict) -> bool:
    """Check if analysis meets screening criteria"""
    indicators = analysis["indicators"]
    
    # RSI criteria
    if "rsi" in criteria:
        rsi_criteria = criteria["rsi"]
        if indicators["rsi"] < rsi_criteria.get("min", 0):
            return False
        if indicators["rsi"] > rsi_criteria.get("max", 100):
            return False
    
    # Add more criteria checks...
    
    return True

def format_analysis(result: dict) -> str:
    """Format analysis for Claude"""
    output = f"""
📊 {result['symbol']} Technical Analysis
{'🟢' if result['change'] > 0 else '🔴'} Price: ${result['price']:.2f} ({result['change']:+.2f}%)

📈 Summary:
• Total Signals: {result['summary']['total_signals']}
• Bullish: {result['summary']['bullish']} | Bearish: {result['summary']['bearish']}
• Avg Score: {result['summary']['avg_score']:.1f}/100

🎯 Top 10 Signals:
"""
    
    for i, sig in enumerate(result['signals'][:10], 1):
        score = sig.get('ai_score', 'N/A')
        indicator = "🔥" if score >= 80 else "⚡" if score >= 60 else "📊"
        output += f"\n{i}. {indicator} [{score}] {sig['signal']}\n"
        output += f"   {sig['desc']}\n"
    
    if result.get('cached'):
        output += "\n💾 (Cached result)"
    
    return output

def format_comparison(result: dict) -> str:
    """Format comparison for Claude"""
    output = "📊 Security Comparison\n\n"
    
    for i, item in enumerate(result['comparison'], 1):
        output += f"{i}. {item['symbol']} - Score: {item['score']:.1f}\n"
        output += f"   Price: ${item['price']:.2f} ({item['change']:+.2f}%)\n"
        output += f"   Signals: {item['bullish']} bullish / {item['bearish']} bearish\n\n"
    
    return output

def format_screening(result: dict) -> str:
    """Format screening results for Claude"""
    output = f"🔍 Screened {result['total_screened']} securities\n"
    output += f"✅ Found {len(result['matches'])} matches\n\n"
    
    for i, match in enumerate(result['matches'][:10], 1):
        output += f"{i}. {match['symbol']} - Score: {match['score']:.1f}\n"
        output += f"   Price: ${match['price']:.2f} | RSI: {match['rsi']:.1f}\n"
    
    return output

if __name__ == "__main__":
    import asyncio
    from mcp.server.stdio import stdio_server
    
    async def main():
        async with stdio_server() as (read_stream, write_stream):
            await app.run(read_stream, write_stream, app.create_initialization_options())
    
    asyncio.run(main())
```





---

### Static Universe Lists (No Database Needed)

```python
# src/technical_analysis_mcp/universes.py

# Hardcoded lists (updated quarterly, no DB costs)
UNIVERSES = {
    "sp500": [
        "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "BRK.B",
        "UNH", "XOM", "JNJ", "JPM", "V", "PG", "MA", "HD", "CVX", "MRK",
        # ... 500 total symbols
    ],
    
    "nasdaq100": [
        "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "AVGO",
        "COST", "NFLX", "AMD", "PEP", "ADBE", "CSCO", "CMCSA", "TMUS",
        # ... 100 total symbols
    ],
    
    "etf_large_cap": [
        "SPY", "VOO", "IVV", "VTI", "QQQ", "DIA", "IWM", "VEA", "VWO",
        "EFA", "IEFA", "AGG", "BND", "VIG", "VYM", "SCHD", "VUG", "VTV"
    ],
    
    "etf_sector": [
        "XLK", "XLF", "XLV", "XLE", "XLY", "XLP", "XLI", "XLB", "XLU", "XLRE"
    ]
}

# Update quarterly with:
# pip install pandas-datareader
# df = pd.read_html('https://en.wikipedia.org/wiki/List_of_S%26P_500_companies')[0]
```





---

### Cloud Run API (Optional, AI Only)

```python
# cloud_run/main.py

from fastapi import FastAPI
from google import genai
import os

app = FastAPI()

@app.post("/api/rank-signals")
async def rank_signals(data: dict):
    """
    Use Gemini API to rank signals (only called when needed)
    """
    symbol = data["symbol"]
    signals = data["signals"]
    market_data = data["market_data"]
    
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    
    prompt = f"""
    Score these {len(signals)} trading signals for {symbol}.
    
    Market Data: {market_data}
    
    Signals:
    {format_signals_for_ai(signals)}
    
    Return JSON: {{"scores": [{{"signal_number": 1, "score": 85, "reasoning": "..."}}]}}
    """
    
    response = client.models.generate_content(
        model='gemini-2.0-flash-exp',
        contents=prompt
    )
    
    # Parse and return scores
    return parse_ai_response(response.text)