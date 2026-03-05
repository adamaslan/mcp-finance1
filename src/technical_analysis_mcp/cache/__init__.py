"""
Caching layer for MCP tool results.

Implements GCP-optimized 7-layer caching architecture:
- Layer 0: Secret Manager (API keys)
- Layer 1: Memorystore/Redis (distributed cache)
- Layer 2a: Firestore (real-time results)
- Layer 2b: Cloud Storage (historical data)
- Layer 3: BigQuery (pre-computed metrics)
- Layer 4: Cloud Tasks (background refresh)
- Layer 5: API Providers (yfinance, Alpha Vantage, Finnhub)
"""

from .firestore_cache import MCPFirestoreCache
from .gcp_cache_manager import GCPCacheManager, CacheLayer, CacheHit, get_cache_manager

__all__ = [
    "MCPFirestoreCache",
    "GCPCacheManager",
    "CacheLayer",
    "CacheHit",
    "get_cache_manager",
]
