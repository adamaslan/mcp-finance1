#!/usr/bin/env python3
"""
Initialize Firestore with universe lists and sample data
"""

import os
from google.cloud import firestore
from datetime import datetime

PROJECT_ID = os.getenv("GCP_PROJECT_ID", "technical-analysis-prod")

db = firestore.Client(project=PROJECT_ID)

# Universe lists
UNIVERSES = {
    "sp500": [
        "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "BRK.B",
        "UNH", "XOM", "JNJ", "JPM", "V", "PG", "MA", "HD", "CVX", "MRK",
        "ABBV", "KO", "AVGO", "PEP", "COST", "WMT", "LLY", "MCD", "TMO",
        "ACN", "ABT", "CSCO", "DHR", "CRM", "ADBE", "NKE", "TXN", "PM",
        "NEE", "DIS", "VZ", "NFLX", "CMCSA", "BMY", "WFC", "INTC", "UPS",
        "AMD", "HON", "QCOM", "UNP", "LIN", "ORCL", "BA", "COP", "IBM"
        # ... add all 500
    ],
    
    "nasdaq100": [
        "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "AVGO",
        "COST", "NFLX", "AMD", "PEP", "ADBE", "CSCO", "CMCSA", "TMUS",
        "QCOM", "INTC", "HON", "INTU", "AMGN", "AMAT", "TXN", "BKNG",
        "ADP", "SBUX", "GILD", "MDLZ", "ADI", "ISRG", "LRCX", "REGN"
        # ... add all 100
    ],
    
    "etf_large_cap": [
        "SPY", "VOO", "IVV", "VTI", "QQQ", "DIA", "IWM", "VEA", "VWO",
        "EFA", "IEFA", "AGG", "BND", "VIG", "VYM", "SCHD", "VUG", "VTV"
    ],
    
    "etf_sector": [
        "XLK", "XLF", "XLV", "XLE", "XLY", "XLP", "XLI", "XLB", "XLU",
        "XLRE", "XLC", "VGT", "VFH", "VHT", "VDE", "VCR", "VDC", "VIS"
    ]
}

print("🗄️  Initializing Firestore collections...")

# Create universe collections
for universe_name, symbols in UNIVERSES.items():
    doc_ref = db.collection("universes").document(universe_name)
    doc_ref.set({
        "symbols": symbols,
        "last_updated": datetime.now(),
        "count": len(symbols)
    })
    print(f"✅ Created universe: {universe_name} ({len(symbols)} symbols)")

# Create health check doc
db.collection("_health_check").document("init").set({
    "initialized": True,
    "timestamp": datetime.now(),
    "version": "2.0.0"
})

print("\n✅ Firestore initialization complete!")
print(f"📊 Total universes: {len(UNIVERSES)}")
print(f"📈 Total unique symbols: {len(set([s for symbols in UNIVERSES.values() for s in symbols]))}")
