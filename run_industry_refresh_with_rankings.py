#!/usr/bin/env python3
"""Run industry refresh with rankings for best/worst performers."""

import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Set up environment
os.environ['GCP_PROJECT_ID'] = 'ttb-lang1'

from tools.industry_tracker.api_service import IndustryService


async def main():
    print("Initializing IndustryService...")

    # Initialize service
    service = IndustryService(
        gcp_project_id='ttb-lang1',
        finnhub_key=os.getenv('FINNHUB_API_KEY', ''),
        alpha_vantage_key=os.getenv('ALPHA_VANTAGE_KEY', ''),
    )

    results = {
        'timestamp': datetime.utcnow().isoformat(),
        'refresh_single': None,
        'refresh_all': None,
        'rankings': None,
    }

    print("\n" + "="*80)
    print("RUNNING: refresh_all_industries()")
    print("="*80)

    try:
        all_result = await service.refresh_all_industries(batch_size=5)
        results['refresh_all'] = {
            'status': 'success',
            'summary': {
                'success_count': all_result.get('success_count'),
                'failure_count': all_result.get('failure_count'),
                'skipped_fresh': all_result.get('skipped_fresh'),
            },
        }

        performances = all_result.get('performances', [])
        print(f"✅ All industries refresh successful")
        print(f"Success: {all_result.get('success_count')}, Failed: {all_result.get('failure_count')}, Skipped: {all_result.get('skipped_fresh')}")

        # Generate rankings for all horizons
        print("\n" + "="*80)
        print("GENERATING RANKINGS FOR ALL TIME HORIZONS")
        print("="*80)

        horizons = ['1w', '2w', '1m', '2m', '3m', '6m', '52w', '2y', '3y', '5y', '10y']
        rankings_data = {}

        for horizon in horizons:
            print(f"\n📊 {horizon.upper()} HORIZON")
            print("-" * 80)

            # Get top performers
            top_performers = service._calculator.get_best_performers(performances, horizon, top_n=10)
            worst_performers = service._calculator.get_worst_performers(performances, horizon, bottom_n=10)

            # Add rankings to each result
            for i, perf in enumerate(top_performers, 1):
                perf['rank'] = i
                perf['rank_type'] = 'best'

            for i, perf in enumerate(worst_performers, 1):
                perf['rank'] = i
                perf['rank_type'] = 'worst'

            rankings_data[horizon] = {
                'top_performers': top_performers,
                'worst_performers': worst_performers,
            }

            # Print to console
            print(f"\n🏆 TOP 10 PERFORMERS ({horizon}):")
            for top in top_performers:
                ret = top['returns'].get(horizon, 0)
                print(f"  {top['rank']:2d}. {top['industry']:25s} {ret:7.2f}%  ({top['etf']})")

            print(f"\n📉 WORST 10 PERFORMERS ({horizon}):")
            for worst in worst_performers:
                ret = worst['returns'].get(horizon, 0)
                print(f"  {worst['rank']:2d}. {worst['industry']:25s} {ret:7.2f}%  ({worst['etf']})")

        results['rankings'] = rankings_data

        # Calculate aggregate stats
        print("\n" + "="*80)
        print("AGGREGATE STATISTICS")
        print("="*80)

        stats = {
            'total_industries': len(performances),
            'by_horizon': {}
        }

        for horizon in horizons:
            returns = [
                p['returns'].get(horizon)
                for p in performances
                if p.get('returns', {}).get(horizon) is not None
            ]

            if returns:
                returns_sorted = sorted(returns, reverse=True)
                stats['by_horizon'][horizon] = {
                    'count': len(returns),
                    'best_return': max(returns),
                    'worst_return': min(returns),
                    'average_return': sum(returns) / len(returns),
                    'median_return': returns_sorted[len(returns) // 2],
                    'positive_count': sum(1 for r in returns if r > 0),
                    'negative_count': sum(1 for r in returns if r < 0),
                }

                print(f"\n{horizon.upper()}:")
                print(f"  Best:     {stats['by_horizon'][horizon]['best_return']:7.2f}%")
                print(f"  Worst:    {stats['by_horizon'][horizon]['worst_return']:7.2f}%")
                print(f"  Average:  {stats['by_horizon'][horizon]['average_return']:7.2f}%")
                print(f"  Median:   {stats['by_horizon'][horizon]['median_return']:7.2f}%")
                print(f"  Positive: {stats['by_horizon'][horizon]['positive_count']}")
                print(f"  Negative: {stats['by_horizon'][horizon]['negative_count']}")

        results['aggregate_stats'] = stats

    except Exception as e:
        results['refresh_all'] = {
            'status': 'error',
            'error': str(e),
        }
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

    # Save to nu-logs2 folder
    output_dir = Path(__file__).parent.parent / 'nu-logs2'
    output_dir.mkdir(exist_ok=True)

    output_file = output_dir / f'industry_rankings_{datetime.utcnow().strftime("%Y%m%d_%H%M%S")}.json'

    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)

    print("\n" + "="*80)
    print(f"✅ RANKINGS SAVED TO: {output_file}")
    print("="*80)


if __name__ == '__main__':
    asyncio.run(main())
