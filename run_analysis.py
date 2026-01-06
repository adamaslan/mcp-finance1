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

from technical_analysis_mcp.server import analyze_security
from technical_analysis_mcp.config import GEMINI_API_KEY


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

        # Price and change
        print(f"Price: ${result['price']:.2f} ({result['change']:+.2f}%)")
        print(f"Timestamp: {result['timestamp']}")
        print()

        # Summary
        print("SIGNAL SUMMARY")
        print("-" * 70)
        summary = result["summary"]
        print(f"Total Signals: {summary['total_signals']}")
        print(f"Bullish: {summary['bullish']} | Bearish: {summary['bearish']}")
        print(f"Average Score: {summary['avg_score']:.1f}/100")
        print()

        # Key indicators
        print("KEY INDICATORS")
        print("-" * 70)
        ind = result["indicators"]
        print(f"RSI: {ind['rsi']:.2f}", end="")
        if ind['rsi'] < 30:
            print(" (OVERSOLD)", end="")
        elif ind['rsi'] > 70:
            print(" (OVERBOUGHT)", end="")
        print()
        print(f"MACD: {ind['macd']:.4f}")
        print(f"ADX: {ind['adx']:.2f}", end="")
        if ind['adx'] > 25:
            print(" (TRENDING)", end="")
        print()
        print(f"Volume: {ind['volume']:,}")
        print()

        # Top signals
        print(f"TOP {'AI-RANKED ' if use_ai else ''}SIGNALS")
        print("-" * 70)
        for i, signal in enumerate(result['signals'][:15], 1):
            score = signal.get('ai_score', '-')
            strength = signal['strength']
            signal_name = signal['signal'][:35]
            reasoning = signal.get('ai_reasoning', '')[:40]

            print(f"{i:2d}. {signal_name:35s} [{strength:18s}] Score: {score:>3}")
            if use_ai and reasoning and reasoning != "Rule-based score":
                print(f"     └─ {reasoning}")

        print()
        return result

    except Exception as e:
        print(f"✗ Analysis failed: {e}")
        raise


async def main():
    """Main entry point."""
    print_header()

    # Get symbol from command line or default to MU
    symbol = sys.argv[1] if len(sys.argv) > 1 else "MU"

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

    await run_analysis(symbol, use_ai=use_ai)

    print("=" * 70)
    print("  ANALYSIS COMPLETE")
    print("=" * 70)
    print()


if __name__ == '__main__':
    asyncio.run(main())
