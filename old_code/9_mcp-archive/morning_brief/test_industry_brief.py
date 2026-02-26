#!/usr/bin/env python3
"""Test script for Industry Tracker - Shows best performers for 1 week and 2 weeks.

This is a STANDALONE test of the industry_tracker module.
It is completely independent from the morning_brief logic.

Usage:
    cd /Users/adamaslan/code/gcp\ app\ w\ mcp/mcp-finance1/9_mcp/morning_brief
    mamba activate fin-ai1
    python test_industry_brief.py
"""

import asyncio
import json
import logging
from datetime import datetime
from industry_tracker import IndustryBrief

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_industry_brief():
    """Test industry brief generation for 1 week and 2 weeks."""

    print("=" * 80)
    print("INDUSTRY BRIEF TEST - Best Performers Analysis")
    print("=" * 80)
    print(f"Generated: {datetime.now().isoformat()}")
    print()

    # Initialize industry brief generator
    brief_gen = IndustryBrief()

    # Test 1: Best performers over last week (1w)
    print("📊 BEST PERFORMERS - LAST WEEK (1w)")
    print("-" * 80)
    try:
        brief_1w = brief_gen.generate_brief(horizon="1w", top_n=10)

        print(f"Time Horizon: Last Week (5 trading days)")
        print(f"Industries Analyzed: {brief_1w['metrics']['industries_with_data']}")
        print(f"Average Return: {brief_1w['metrics']['average_return']:+.2f}%")
        print(f"Positive: {brief_1w['metrics']['positive_count']} | Negative: {brief_1w['metrics']['negative_count']} | Neutral: {brief_1w['metrics']['neutral_count']}")
        print()

        print("Top 10 Performers:")
        print()
        for perf in brief_1w['top_performers']:
            industry = perf['industry']
            etf = perf['etf']
            ret = perf['returns'].get('1w')
            rank = perf.get('rank', '?')
            print(f"  {rank:2}. {industry:<30} ({etf:<6}) {ret:+7.2f}%")

        print()

    except Exception as e:
        logger.error("Failed to generate 1-week brief: %s", e)
        print(f"❌ ERROR: {e}")

    print()
    print("=" * 80)

    # Test 2: Best performers over last 2 weeks (2w)
    print("📊 BEST PERFORMERS - LAST 2 WEEKS (2w)")
    print("-" * 80)
    try:
        brief_2w = brief_gen.generate_brief(horizon="2w", top_n=10)

        print(f"Time Horizon: Last 2 Weeks (10 trading days)")
        print(f"Industries Analyzed: {brief_2w['metrics']['industries_with_data']}")
        print(f"Average Return: {brief_2w['metrics']['average_return']:+.2f}%")
        print(f"Positive: {brief_2w['metrics']['positive_count']} | Negative: {brief_2w['metrics']['negative_count']} | Neutral: {brief_2w['metrics']['neutral_count']}")
        print()

        print("Top 10 Performers:")
        print()
        for perf in brief_2w['top_performers']:
            industry = perf['industry']
            etf = perf['etf']
            ret = perf['returns'].get('2w')
            rank = perf.get('rank', '?')
            print(f"  {rank:2}. {industry:<30} ({etf:<6}) {ret:+7.2f}%")

        print()

    except Exception as e:
        logger.error("Failed to generate 2-week brief: %s", e)
        print(f"❌ ERROR: {e}")

    print()
    print("=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)


def main():
    """Run test synchronously."""
    asyncio.run(test_industry_brief())


if __name__ == "__main__":
    main()
