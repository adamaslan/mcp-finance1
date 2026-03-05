#!/usr/bin/env python3
"""Run industry refresh and save results to JSON."""

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
    }

    print("\n" + "="*80)
    print("RUNNING: refresh_industry('Software')")
    print("="*80)

    try:
        single_result = await service.refresh_industry('Software')
        results['refresh_single'] = {
            'status': 'success',
            'industry': 'Software',
            'data': single_result,
        }
        print("✅ Single industry refresh successful")
        print(json.dumps(single_result, indent=2, default=str))
    except Exception as e:
        results['refresh_single'] = {
            'status': 'error',
            'industry': 'Software',
            'error': str(e),
        }
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

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
            'full_data': all_result,
        }
        print("✅ All industries refresh successful")
        print(f"Success: {all_result.get('success_count')}, Failed: {all_result.get('failure_count')}, Skipped: {all_result.get('skipped_fresh')}")
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

    output_file = output_dir / f'industry_refresh_results_{datetime.utcnow().strftime("%Y%m%d_%H%M%S")}.json'

    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)

    print("\n" + "="*80)
    print(f"✅ RESULTS SAVED TO: {output_file}")
    print("="*80)

if __name__ == '__main__':
    asyncio.run(main())
