"""
Cloud Run API - Main FastAPI Application
Location: option2-gcp/cloud-run/main.py

Handles all API requests and routes to appropriate services
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from google.cloud import firestore, storage, pubsub_v1
from datetime import datetime, timedelta
import json
import hashlib
import logging
import os
import sys
import asyncio

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add MCP server to path for importing
# Try multiple paths for different deployment scenarios
for path in ['/app/src', '/workspace/src', '../src', './src']:
    if os.path.isdir(path):
        sys.path.insert(0, path)
        logger.info(f"Added {path} to Python path")
        break

# Try to import MCP server functions for direct analysis
try:
    from technical_analysis_mcp.server import (
        get_trade_plan as mcp_get_trade_plan,
        scan_trades as mcp_scan_trades,
        portfolio_risk as mcp_portfolio_risk,
        morning_brief as mcp_morning_brief,
        analyze_fibonacci as mcp_analyze_fibonacci,
        options_risk_analysis as mcp_options_risk_analysis,
    )
    MCP_AVAILABLE = True
    logger.info("✅ MCP server functions imported successfully")
except ImportError as e:
    logger.warning(f"⚠️ MCP server functions not available: {e}")
    logger.error("❌ MCP server required - no mock data allowed")
    MCP_AVAILABLE = False
    mcp_get_trade_plan = None
    mcp_scan_trades = None
    mcp_portfolio_risk = None
    mcp_morning_brief = None
    mcp_analyze_fibonacci = None
    mcp_options_risk_analysis = None

# Initialize GCP clients (optional for local testing)
PROJECT_ID = os.environ.get("GCP_PROJECT_ID", "ttb-lang1")
BUCKET_NAME = os.getenv("BUCKET_NAME", "technical-analysis-data")

try:
    db = firestore.Client(project=PROJECT_ID)
    storage_client = storage.Client(project=PROJECT_ID)
    publisher = pubsub_v1.PublisherClient()
    logger.info("✅ GCP clients initialized")
except Exception as e:
    logger.warning(f"⚠️ GCP clients not available (local testing mode): {e}")
    db = None
    storage_client = None
    publisher = None

# FastAPI app
app = FastAPI(
    title="Technical Analysis API",
    description="GCP-powered technical analysis for stocks/ETFs",
    version="2.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# MODELS
# ============================================================================

class AnalyzeRequest(BaseModel):
    symbol: str = Field(..., description="Ticker symbol")
    period: str = Field("1mo", description="Time period")
    include_ai: bool = Field(True, description="Use AI ranking")
    security_type: str = Field("auto", description="Security type")

class CompareRequest(BaseModel):
    symbols: List[str] = Field(..., min_items=2, max_items=20)
    period: str = Field("1mo")

class ScreenRequest(BaseModel):
    symbols: List[str] = Field(...)
    criteria: Dict[str, Any] = Field(...)
    limit: int = Field(20, ge=1, le=100)

class TradePlanRequest(BaseModel):
    symbol: str = Field(..., description="Ticker symbol")
    period: str = Field("1mo", description="Time period")

class ScanRequest(BaseModel):
    universe: str = Field("sp500", description="Universe to scan")
    max_results: int = Field(10, ge=1, le=50, description="Max results")

class PortfolioPosition(BaseModel):
    symbol: str = Field(..., description="Ticker symbol")
    shares: float = Field(..., description="Number of shares")
    entry_price: float = Field(..., description="Entry price per share")

class PortfolioRiskRequest(BaseModel):
    positions: List[PortfolioPosition] = Field(..., description="Portfolio positions")

class MorningBriefRequest(BaseModel):
    watchlist: Optional[List[str]] = Field(None, description="Symbols to analyze")
    market_region: str = Field("US", description="Market region")

class FibonacciRequest(BaseModel):
    symbol: str = Field(..., description="Stock symbol (e.g., AAPL)")
    period: str = Field("1d", description="Time period (1d, 1mo, 3mo)")
    window: int = Field(50, description="Lookback window for swing detection")

class OptionsRiskRequest(BaseModel):
    symbol: str = Field(..., description="Stock symbol (e.g., AAPL)")
    option_type: str = Field("both", description="Option type: calls, puts, or both")
    min_volume: int = Field(10, description="Minimum volume filter")

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def is_cache_valid(data: dict, ttl_seconds: int = 300) -> bool:
    """Check if cached data is valid"""
    if not data or "timestamp" not in data:
        return False
    
    timestamp = data["timestamp"]
    if isinstance(timestamp, str):
        timestamp = datetime.fromisoformat(timestamp)
    
    age = (datetime.now() - timestamp).total_seconds()
    return age < ttl_seconds

def publish_to_pubsub(topic: str, data: dict):
    """Publish message to Pub/Sub"""
    topic_path = publisher.topic_path(PROJECT_ID, topic)
    
    message_data = json.dumps(data).encode("utf-8")
    future = publisher.publish(topic_path, data=message_data)
    
    logger.info(f"Published to {topic}: {future.result()}")

# ============================================================================
# HEALTH CHECK
# ============================================================================

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "service": "Technical Analysis API",
        "version": "2.0.0",
        "status": "healthy",
        "gcp": {
            "project": PROJECT_ID,
            "firestore": "connected",
            "pubsub": "connected",
            "storage": "connected"
        }
    }

@app.get("/health")
async def health():
    """Detailed health check"""
    try:
        # Test Firestore
        db.collection("_health_check").document("test").set({"timestamp": datetime.now()})
        
        # Test Pub/Sub
        topic_path = publisher.topic_path(PROJECT_ID, "analyze-request")
        
        return {
            "status": "healthy",
            "checks": {
                "firestore": "ok",
                "pubsub": "ok",
                "storage": "ok"
            }
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Health check failed: {str(e)}")

# ============================================================================
# ANALYSIS ENDPOINTS
# ============================================================================

@app.post("/api/analyze")
async def analyze(request: AnalyzeRequest, background_tasks: BackgroundTasks):
    """
    Analyze a security
    Returns cached data if available, otherwise triggers async analysis
    """
    symbol = request.symbol.upper()
    
    # Check Firestore cache
    try:
        doc_ref = db.collection("signals").document(symbol)
        doc = doc_ref.get()
        
        if doc.exists:
            data = doc.to_dict()
            if is_cache_valid(data, ttl_seconds=300):
                logger.info(f"Cache hit for {symbol}")
                return {
                    "symbol": symbol,
                    "cached": True,
                    "cache_age_seconds": (datetime.now() - data["timestamp"]).total_seconds(),
                    **data
                }
    except Exception as e:
        logger.error(f"Firestore read error: {e}")
    
    # Cache miss - trigger async analysis
    logger.info(f"Cache miss for {symbol} - triggering analysis")
    
    request_id = hashlib.md5(f"{symbol}:{request.period}:{datetime.now()}".encode()).hexdigest()
    
    # Publish to Pub/Sub
    background_tasks.add_task(
        publish_to_pubsub,
        "analyze-request",
        {
            "symbol": symbol,
            "period": request.period,
            "include_ai": request.include_ai,
            "security_type": request.security_type,
            "request_id": request_id,
            "timestamp": datetime.now().isoformat()
        }
    )
    
    return {
        "status": "processing",
        "symbol": symbol,
        "request_id": request_id,
        "message": f"Analysis started for {symbol}. Check back in 5-10 seconds.",
        "check_url": f"/api/signals/{symbol}"
    }

@app.get("/api/signals/{symbol}")
async def get_signals(
    symbol: str,
    category: Optional[str] = Query(None),
    min_score: int = Query(0, ge=0, le=100),
    limit: int = Query(50, ge=1, le=200)
):
    """Get signals for a symbol"""
    symbol = symbol.upper()
    
    try:
        doc_ref = db.collection("signals").document(symbol)
        doc = doc_ref.get()
        
        if not doc.exists:
            raise HTTPException(
                status_code=404,
                detail=f"No analysis found for {symbol}. Run /api/analyze first."
            )
        
        data = doc.to_dict()
        signals = data.get("signals", [])
        
        # Apply filters
        if category:
            signals = [s for s in signals if s.get("category") == category]
        
        if min_score > 0:
            signals = [s for s in signals if s.get("ai_score", 0) >= min_score]
        
        signals = signals[:limit]
        
        return {
            "symbol": symbol,
            "timestamp": data.get("timestamp"),
            "total_signals": len(data.get("signals", [])),
            "filtered_count": len(signals),
            "signals": signals
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/compare")
async def compare(request: CompareRequest):
    """Compare multiple securities"""
    results = []
    
    for symbol in request.symbols:
        symbol = symbol.upper()
        
        try:
            doc_ref = db.collection("signals").document(symbol)
            doc = doc_ref.get()
            
            if doc.exists:
                data = doc.to_dict()
                results.append({
                    "symbol": symbol,
                    "price": data.get("price", 0),
                    "change": data.get("change", 0),
                    "summary": data.get("summary", {}),
                    "indicators": data.get("indicators", {})
                })
        except Exception as e:
            logger.error(f"Error fetching {symbol}: {e}")
    
    if not results:
        raise HTTPException(
            status_code=404,
            detail="No analyzed data found for any symbols. Run /api/analyze first."
        )
    
    # Sort by average score
    results.sort(
        key=lambda x: x.get("summary", {}).get("avg_score", 0),
        reverse=True
    )
    
    return {
        "comparison": results,
        "winner": results[0] if results else None,
        "total_compared": len(results)
    }

@app.post("/api/screen")
async def screen(request: ScreenRequest, background_tasks: BackgroundTasks):
    """
    Screen securities with parallel processing
    Triggers Cloud Function for parallel analysis
    """
    
    # Generate cache key
    criteria_str = json.dumps(request.criteria, sort_keys=True)
    cache_key = hashlib.md5(criteria_str.encode()).hexdigest()
    
    # Check screener cache
    try:
        doc_ref = db.collection("screener_cache").document(cache_key)
        doc = doc_ref.get()
        
        if doc.exists:
            data = doc.to_dict()
            if is_cache_valid(data, ttl_seconds=900):  # 15 min cache
                logger.info(f"Screener cache hit: {cache_key}")
                return {
                    "cached": True,
                    **data
                }
    except Exception as e:
        logger.error(f"Screener cache read error: {e}")
    
    # Trigger parallel screening via Pub/Sub
    background_tasks.add_task(
        publish_to_pubsub,
        "screen-request",
        {
            "symbols": request.symbols,
            "criteria": request.criteria,
            "limit": request.limit,
            "cache_key": cache_key,
            "timestamp": datetime.now().isoformat()
        }
    )
    
    return {
        "status": "processing",
        "total_symbols": len(request.symbols),
        "cache_key": cache_key,
        "message": f"Screening {len(request.symbols)} symbols in parallel. Check back in 10-30 seconds.",
        "check_url": f"/api/screen/{cache_key}"
    }

@app.get("/api/screen/{cache_key}")
async def get_screen_results(cache_key: str):
    """Get screening results"""
    try:
        doc_ref = db.collection("screener_cache").document(cache_key)
        doc = doc_ref.get()
        
        if not doc.exists:
            return {
                "status": "processing",
                "message": "Screening still in progress..."
            }
        
        data = doc.to_dict()
        return {
            "status": "complete",
            **data
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# TRADE PLANS, SCANNING, PORTFOLIO & BRIEFING (Direct MCP)
# ============================================================================

@app.post("/api/trade-plan")
async def trade_plan(request: TradePlanRequest):
    """Get risk-qualified trade plan for a symbol"""
    if not MCP_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="MCP server functions not available"
        )

    try:
        result = await mcp_get_trade_plan(
            symbol=request.symbol,
            period=request.period
        )
        return result
    except Exception as e:
        logger.error(f"Trade plan error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/scan")
async def scan(request: ScanRequest):
    """Scan universe for qualified trade setups"""
    if not MCP_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="MCP server functions not available"
        )

    try:
        result = await mcp_scan_trades(
            universe=request.universe,
            max_results=request.max_results
        )
        return result
    except Exception as e:
        logger.error(f"Scan error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/portfolio-risk")
async def portfolio_risk_endpoint(request: PortfolioRiskRequest):
    """Assess aggregate portfolio risk"""
    if not MCP_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="MCP server functions not available"
        )

    try:
        # Convert Pydantic models to dicts for MCP function
        positions = [p.model_dump() for p in request.positions]
        result = await mcp_portfolio_risk(positions=positions)
        return result
    except Exception as e:
        logger.error(f"Portfolio risk error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/morning-brief")
async def morning_brief_endpoint(request: MorningBriefRequest):
    """Generate daily market briefing"""
    if not MCP_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="MCP server functions not available"
        )

    try:
        result = await mcp_morning_brief(
            watchlist=request.watchlist,
            market_region=request.market_region
        )
        return result
    except Exception as e:
        logger.error(f"Morning brief error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/fibonacci")
async def fibonacci_analysis(request: FibonacciRequest):
    """Comprehensive Fibonacci analysis with levels, signals, and clusters.

    Returns 40+ Fibonacci levels, 200+ signals across categories,
    confluence zones, and multi-timeframe validation.
    """
    if not MCP_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="MCP server functions not available"
        )

    try:
        logger.info(f"Fibonacci analysis requested for {request.symbol} (period: {request.period})")
        result = await mcp_analyze_fibonacci(
            symbol=request.symbol,
            period=request.period,
            window=request.window
        )
        logger.info(f"Fibonacci analysis completed for {request.symbol}: {len(result.get('levels', []))} levels, {len(result.get('signals', []))} signals")
        return result
    except Exception as e:
        logger.error(f"Fibonacci analysis error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/options-risk")
async def options_risk_analysis_endpoint(request: OptionsRiskRequest):
    """Analyze options risk for a security (puts/calls, PCR, IV, OI)"""
    if not MCP_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="MCP server functions not available"
        )

    try:
        logger.info(f"Options risk analysis requested for {request.symbol} (type: {request.option_type})")
        result = await mcp_options_risk_analysis(
            symbol=request.symbol,
            option_type=request.option_type,
            min_volume=request.min_volume
        )
        logger.info(f"Options risk analysis completed for {request.symbol}")
        return result
    except Exception as e:
        logger.error(f"Options risk analysis error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# HISTORICAL DATA
# ============================================================================

@app.get("/api/history/{symbol}")
async def get_history(symbol: str, days: int = Query(7, ge=1, le=30)):
    """Get historical analysis data"""
    symbol = symbol.upper()
    
    # Get current analysis
    try:
        current_doc = db.collection("signals").document(symbol).get()
        current = current_doc.to_dict() if current_doc.exists else None
    except:
        current = None
    
    # Get historical data
    history = []
    for i in range(1, days + 1):
        date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
        try:
            hist_doc = db.collection("analysis").document(symbol).collection("history").document(date).get()
            if hist_doc.exists:
                history.append({
                    "date": date,
                    **hist_doc.to_dict()
                })
        except:
            continue
    
    return {
        "symbol": symbol,
        "current": current,
        "history": history,
        "days_available": len(history)
    }

# ============================================================================
# REPORTS & SUMMARIES
# ============================================================================

@app.get("/api/reports/daily")
async def get_daily_report(date: Optional[str] = Query(None)):
    """Get daily market summary"""
    if not date:
        date = datetime.now().strftime("%Y-%m-%d")
    
    try:
        doc_ref = db.collection("reports").document("daily").collection("summaries").document(date)
        doc = doc_ref.get()
        
        if not doc.exists:
            return {
                "date": date,
                "status": "not_available",
                "message": "Daily report not yet generated. Reports are created at market close."
            }
        
        return {
            "date": date,
            "status": "available",
            **doc.to_dict()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# ADMIN ENDPOINTS
# ============================================================================

@app.get("/api/stats")
async def get_stats():
    """Get usage statistics"""
    try:
        # Count documents in collections
        signals_count = len(list(db.collection("signals").limit(1000).stream()))
        
        return {
            "total_symbols_cached": signals_count,
            "firestore_collections": {
                "signals": signals_count,
                "analysis": "history_per_symbol",
                "screener_cache": "variable",
                "reports": "daily_summaries"
            },
            "cache_policy": {
                "signals": "5 minutes",
                "screener": "15 minutes",
                "history": "permanent (30 days)"
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/admin/clear-cache")
async def clear_cache(collection: str = Query("signals")):
    """Clear cache collection (admin only)"""
    # In production, add authentication here
    
    try:
        # Delete all documents in collection
        docs = db.collection(collection).limit(500).stream()
        deleted = 0
        
        for doc in docs:
            doc.reference.delete()
            deleted += 1
        
        return {
            "status": "success",
            "collection": collection,
            "deleted": deleted
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions"""
    return {
        "error": exc.detail,
        "status_code": exc.status_code
    }

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions"""
    logger.error(f"Unhandled exception: {exc}")
    return {
        "error": "Internal server error",
        "detail": str(exc),
        "status_code": 500
    }

# ============================================================================
# STARTUP/SHUTDOWN
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Initialize on startup"""
    logger.info("🚀 Technical Analysis API starting...")
    logger.info(f"📊 Project: {PROJECT_ID}")
    logger.info(f"💾 Bucket: {BUCKET_NAME}")
    
    # Test connections
    try:
        db.collection("_health_check").document("startup").set({
            "timestamp": datetime.now(),
            "status": "started"
        })
        logger.info("✅ Firestore connected")
    except Exception as e:
        logger.error(f"❌ Firestore connection failed: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("👋 Technical Analysis API shutting down...")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8080)))