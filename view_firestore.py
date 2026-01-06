#!/usr/bin/env python
"""View Firestore analysis results."""

from google.cloud import firestore
import json
import sys

def main():
    # Initialize Firestore
    db = firestore.Client(project='ttb-lang1')

    print("=" * 70)
    print("FIRESTORE ANALYSIS RESULTS")
    print("=" * 70)

    # Get all analysis documents
    print("\n📊 INDIVIDUAL STOCK ANALYSES")
    print("-" * 70)
    print(f"{'Symbol':<6} | {'Price':>10} | {'Change':>7} | {'Score':>5} | {'Outlook':<8} | Signals")
    print("-" * 70)

    docs = db.collection('analysis').stream()
    results = []
    for doc in docs:
        data = doc.to_dict()
        results.append(data)
        symbol = data.get('symbol', doc.id)
        price = data.get('price', 0)
        change = data.get('change_pct', 0)
        score = data.get('ai_score', 0)
        outlook = data.get('ai_outlook', 'N/A')
        signals = data.get('signal_count', 0)

        print(f"{symbol:<6} | ${price:>9.2f} | {change:>+6.2f}% | {score:>5} | {outlook:<8} | {signals}")

    print("-" * 70)
    print(f"Total: {len(results)} stocks analyzed")

    # Get daily summary
    print("\n" + "=" * 70)
    print("📅 DAILY SUMMARY")
    print("-" * 70)

    summaries = db.collection('summaries').order_by('date', direction=firestore.Query.DESCENDING).limit(1).stream()
    for doc in summaries:
        data = doc.to_dict()
        print(f"Date: {data.get('date', 'N/A')}")
        print(f"Analyzed: {data.get('successful', 0)}/{data.get('total_analyzed', 0)}")

        if data.get('top_bullish'):
            print("\n🟢 Top Bullish:")
            for item in data.get('top_bullish', [])[:5]:
                summary = item.get('ai_summary', '')[:50]
                print(f"   {item.get('symbol')}: Score {item.get('ai_score')} - {summary}")

        if data.get('top_bearish'):
            print("\n🔴 Top Bearish:")
            for item in data.get('top_bearish', [])[:5]:
                summary = item.get('ai_summary', '')[:50]
                print(f"   {item.get('symbol')}: Score {item.get('ai_score')} - {summary}")

    # Show detailed view for specific stock if requested
    if len(sys.argv) > 1:
        symbol = sys.argv[1].upper()
        print("\n" + "=" * 70)
        print(f"📈 DETAILED VIEW: {symbol}")
        print("-" * 70)

        doc = db.collection('analysis').document(symbol).get()
        if doc.exists:
            data = doc.to_dict()
            print(json.dumps(data, indent=2, default=str))
        else:
            print(f"No data found for {symbol}")

    print("\n" + "=" * 70)


if __name__ == '__main__':
    main()
