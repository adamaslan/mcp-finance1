"""Industry Performance Tracker

Full-featured 50-industry ETF performance tracking with:
- Firebase caching for cloud deployments
- Persistent Firestore storage for zero-cost reads
- Multi-source API fallback (Finnhub → Alpha Vantage → yfinance)
- Local development mode (yfinance only, no Firebase needed)
- Cloud deployment mode (full Firebase + persistent storage)

Works both locally and on GCloud with automatic fallback chain.
"""

from .industry_mapper import IndustryMapper
from .performance_calculator import PerformanceCalculator
from .firebase_cache import FirebaseCache, FirebaseCacheError
from .persistent_store import PersistentETFStore, PersistentStoreError
from .etf_data_fetcher import ETFDataFetcher, ETFDataError
from .summary_generator import SummaryGenerator
from .api_service import IndustryService, IndustryServiceError

__all__ = [
    "IndustryMapper",
    "PerformanceCalculator",
    "FirebaseCache",
    "FirebaseCacheError",
    "PersistentETFStore",
    "PersistentStoreError",
    "ETFDataFetcher",
    "ETFDataError",
    "SummaryGenerator",
    "IndustryService",
    "IndustryServiceError",
]
