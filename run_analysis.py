#!/usr/bin/env python
"""
Technical Analysis Pipeline Runner

Runs the full technical analysis pipeline with:
- Data fetching from yfinance
- 50+ technical indicator calculations
- 150+ signal detection
- AI-powered signal ranking (Gemini) or rule-based fallback
"""

import asyncio
import os
import sys

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("Note: python-dotenv not installed, using system environment variables")

sys.path.insert(0, 'src')

from technical_analysis_mcp.server import (
    analyze_security,
    compare_securities,
    get_trade_plan,
    morning_brief,
    portfolio_risk,
    scan_trades,
    screen_securities,
)
from technical_analysis_mcp.config import GEMINI_API_KEY
from technical_analysis_mcp.formatting import (
    format_analysis,
    format_comparison,
    format_morning_brief,
    format_portfolio_risk,
    format_risk_analysis,
    format_scan_results,
    format_screening,
)


def print_header():
    """Print startup banner."""
    print()
    print("=" * 70)
    print("  TECHNICAL ANALYSIS PIPELINE")
    print("=" * 70)
    print()


def verify_setup():
    """Verify environment configuration."""
    print("SETUP VERIFICATION")
    print("-" * 70)

    # Check Gemini API key
    api_key = os.getenv("GEMINI_API_KEY") or GEMINI_API_KEY
    if api_key:
        masked_key = api_key[:10] + "..." + api_key[-4:] if len(api_key) > 14 else "***"
        print(f"✓ Gemini API Key: {masked_key}")
    else:
        print("✗ Gemini API Key: NOT CONFIGURED")
        print("  → Set GEMINI_API_KEY in .env for AI-powered ranking")

    # Check GCP configuration
    gcp_project = os.getenv("GCP_PROJECT_ID", "not set")
    use_gcp = os.getenv("USE_GCP", "false").lower() == "true"
    print(f"{'✓' if use_gcp else '○'} GCP Project: {gcp_project} (USE_GCP={use_gcp})")

    print()
    return bool(api_key)


def test_gemini_connection():
    """Test Gemini API connection."""
    print("GEMINI API CONNECTION TEST")
    print("-" * 70)

    api_key = os.getenv("GEMINI_API_KEY") or GEMINI_API_KEY
    if not api_key:
        print("⚠ Skipping test - no API key configured")
        print()
        return False

    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-2.0-flash-exp")
        response = model.generate_content("Reply with only: OK")

        if response and response.text:
            print(f"✓ Gemini API connection successful!")
            print(f"  Model: gemini-2.0-flash-exp")
            print(f"  Response: {response.text.strip()[:50]}")
            print()
            return True
        else:
            print("✗ Gemini API returned empty response")
            print()
            return False

    except ImportError:
        print("✗ google-generativeai package not installed")
        print("  → Run: pip install google-generativeai")
        print()
        return False
    except Exception as e:
        print(f"✗ Gemini API error: {e}")
        print()
        return False


async def run_analysis(symbol: str, use_ai: bool = False):
    """Run technical analysis for a symbol."""
    print(f"ANALYZING: {symbol}")
    print("-" * 70)

    try:
        result = await analyze_security(symbol, period='3mo', use_ai=use_ai)

        print(format_analysis(result))
        print()
        return result

    except Exception as e:
        print(f"✗ Analysis failed: {e}")
        raise


def _parse_symbols(argv: list[str]) -> list[str]:
    parts: list[str] = []
    for arg in argv:
        if arg.startswith("--"):
            continue
        parts.extend([p.strip() for p in arg.replace(",", " ").split()])
    return [p.upper() for p in parts if p]


async def run_report(symbols: list[str], use_ai: bool) -> None:
    print("REPORT SYMBOLS")
    print("-" * 70)
    print(", ".join(symbols))
    print()

    for i in range(0, len(symbols), 10):
        brief = await morning_brief(watchlist=symbols[i:i + 10], market_region="US")
        print(format_morning_brief(brief))
        print()

    analyses: list[dict] = []
    for symbol in symbols:
        analyses.append(await run_analysis(symbol, use_ai=use_ai))

    comparison = await compare_securities(symbols=symbols)
    print(format_comparison(comparison))
    print()

    screening = await screen_securities(
        universe="sp500",
        criteria={"rsi": {"max": 40}, "min_score": 55},
        limit=15,
    )
    print(format_screening(screening))
    print()

    scan = await scan_trades(universe="sp500", max_results=10)
    print(format_scan_results(scan))
    print()

    positions = [
        {"symbol": a["symbol"], "shares": 10, "entry_price": a["price"]}
        for a in analyses
        if a and isinstance(a, dict) and "symbol" in a and "price" in a
    ]
    if positions:
        portfolio = await portfolio_risk(positions=positions)
        print(format_portfolio_risk(portfolio))
        print()

    for symbol in symbols:
        plan = await get_trade_plan(symbol=symbol, period="3mo")
        print(format_risk_analysis(plan))
        print()


async def main():
    """Main entry point."""
    print_header()

    default_symbols = ["RGTI", "QBTS", "LLY", "C", "AEM", "SLV", "TLRY", "SMCI", "ORCL", "GLD", "MU"]
    symbols = _parse_symbols(sys.argv[1:]) or default_symbols

    # Verify setup
    has_api_key = verify_setup()

    # Test Gemini connection if API key exists
    gemini_works = False
    if has_api_key:
        gemini_works = test_gemini_connection()

    # Run analysis
    use_ai = gemini_works
    if use_ai:
        print("🤖 AI Ranking: ENABLED (using Gemini)")
    else:
        print("📊 AI Ranking: DISABLED (using rule-based scoring)")
    print()

    await run_report(symbols, use_ai=use_ai)

    print("=" * 70)
    print("  ANALYSIS COMPLETE")
    print("=" * 70)
    print()


if __name__ == '__main__':
    asyncio.run(main())
