#!/usr/bin/env python3
"""
Beta1 Universe Scan Script
Runs technical analysis scan on the Beta1 universe and saves results to Firebase.

Usage:
  Local: python run_beta1_scan.py
  Cloud Run Job: Deploy this script as a Cloud Run job or Cloud Function

Requirements:
  - Google Cloud credentials (via GOOGLE_APPLICATION_CREDENTIALS or gcloud auth)
  - GCP_PROJECT_ID environment variable set
  - Dependencies: pandas, numpy, yfinance, google-cloud-firestore
"""

import sys
import os
import asyncio
from datetime import datetime

# Add source to path for local testing
src_path = os.path.join(os.path.dirname(__file__), '..', 'src')
if os.path.exists(src_path):
    sys.path.insert(0, src_path)

def setup_project_id():
    """Set up GCP project ID"""
    project_id = os.environ.get('GCP_PROJECT_ID')
    if not project_id:
        # Fallback to default or try to infer from gcloud
        project_id = 'ttb-lang1'
        os.environ['GCP_PROJECT_ID'] = project_id
    return project_id


def print_header(title: str):
    """Print formatted header"""
    width = 80
    print("\n" + "=" * width)
    print(title.center(width))
    print("=" * width + "\n")


def print_section(title: str):
    """Print formatted section"""
    print(f"\n{'─' * 80}")
    print(f"  {title}")
    print(f"{'─' * 80}\n")


async def run_beta1_scan() -> dict:
    """Main function to run Beta1 scan and save to Firebase"""

    print_header("🚀 BETA1 UNIVERSE SCAN")

    project_id = setup_project_id()
    print(f"Project ID: {project_id}")

    # Import after setup
    try:
        print("\n⏳ Loading dependencies...")
        from technical_analysis_mcp.server import scan_trades
        from technical_analysis_mcp.universes import get_universe, list_universes
        from google.cloud import firestore
        print("✓ Dependencies loaded")

    except ImportError as e:
        print(f"✗ Failed to import dependencies: {e}")
        print("\nFor local testing, install dependencies:")
        print("  mamba create -f environment.yml")
        sys.exit(1)

    # Initialize Firestore
    print("\n⏳ Connecting to Firebase...")
    try:
        db = firestore.Client(project=project_id)
        # Test connection
        db.collection("_health").document("test").set({"timestamp": datetime.now()})
        print("✓ Firebase connected and tested")
    except Exception as e:
        print(f"✗ Firebase connection failed: {e}")
        print("\nEnsure you have:")
        print("  - Google Cloud credentials set (gcloud auth application-default login)")
        print("  - GCP_PROJECT_ID environment variable set")
        sys.exit(1)

    # Load Beta1 universe
    print_section("BETA1 UNIVERSE")
    try:
        beta1_symbols = get_universe("beta1")
        print(f"✓ Loaded {len(beta1_symbols)} symbols")
        print(f"\nSymbols: {', '.join(beta1_symbols)}")

        # Show all available universes
        all_universes = list_universes()
        print(f"\nAvailable universes ({len(all_universes)} total):")
        for u in sorted(all_universes):
            marker = "📍" if u == "beta1" else "  "
            print(f"  {marker} {u}")

    except Exception as e:
        print(f"✗ Failed to load universe: {e}")
        sys.exit(1)

    # Run scan
    print_section("SCANNING BETA1 UNIVERSE")
    print("⏳ Scanning for qualified trade setups...")
    print("   (This may take 30-90 seconds depending on network conditions)\n")

    try:
        result = await scan_trades(
            universe="beta1",
            max_results=len(beta1_symbols)  # Return all qualified trades
        )

        # Add metadata
        result["metadata"] = {
            "universe": "beta1",
            "symbols": beta1_symbols,
            "symbols_count": len(beta1_symbols),
            "scan_timestamp": datetime.now().isoformat(),
            "script_version": "1.0",
        }

        print("✓ Scan completed successfully!")

        # Display results summary
        total_scanned = result.get('total_scanned', 0)
        qualified_trades = result.get('qualified_trades', [])
        qualified_count = len(qualified_trades)

        print_section("SCAN RESULTS")
        print(f"Total symbols scanned:        {total_scanned}")
        print(f"Qualified trades found:      {qualified_count}")

        if qualified_count > 0:
            print(f"\n🔝 Top Qualified Trades:\n")
            for i, trade in enumerate(qualified_trades[:10], 1):
                symbol = trade.get('symbol', 'N/A')
                score = trade.get('quality_score', 0)
                signal = trade.get('primary_signal', 'N/A')
                price = trade.get('current_price', 0)
                print(f"  {i:2d}. {symbol:8s} | Score: {score:6.2f} | Signal: {signal:15s} | Price: ${price:.2f}")
        else:
            print("  (No qualified trades found in this scan)")

    except Exception as e:
        print(f"✗ Scan failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    # Save to Firebase
    print_section("SAVING TO FIREBASE")

    try:
        # Save latest version
        latest_ref = db.collection("scans").document("beta1_latest")
        latest_ref.set(result)
        print("✓ Saved: scans/beta1_latest")

        # Save timestamped version for history
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        history_ref = db.collection("scans").document(f"beta1_{timestamp}")
        history_ref.set(result)
        print(f"✓ Saved: scans/beta1_{timestamp}")

        # Save individual trade results
        if qualified_trades:
            print("\n⏳ Saving individual trades...")
            batch = db.batch()

            for trade in qualified_trades:
                symbol = trade.get('symbol', 'unknown')
                trade_ref = db.collection("beta1_trades").document(symbol)
                batch.set(trade_ref, {
                    **trade,
                    "last_updated": datetime.now().isoformat(),
                })

            batch.commit()
            print(f"✓ Saved {len(qualified_trades)} individual trades to beta1_trades/")

    except Exception as e:
        print(f"✗ Firebase save failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    # Display summary
    print_section("SUMMARY")
    print(f"Universe:        Beta1")
    print(f"Symbols:         {len(beta1_symbols)}")
    print(f"Qualified:       {qualified_count}")
    print(f"Timestamp:       {datetime.now().isoformat()}")
    print(f"Firebase:        Saved ✓")

    print_section("FIREBASE PATHS")
    print(f"Latest results:  db.collection('scans').document('beta1_latest')")
    print(f"Timestamped:     db.collection('scans').document('beta1_{timestamp}')")
    print(f"Trades:          db.collection('beta1_trades').document(symbol)")

    print(f"\nFirebase Console:")
    print(f"  {project_id}: https://console.firebase.google.com/project/{project_id}/firestore")

    print("\n✓ Beta1 scan complete!\n")

    return result


def main():
    """Entry point"""
    try:
        result = asyncio.run(run_beta1_scan())
        return 0
    except KeyboardInterrupt:
        print("\n\n⚠️  Scan interrupted by user")
        return 1
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
