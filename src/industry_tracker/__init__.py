"""Industry Performance Tracking Module.

Standalone module for tracking performance of 50 US economy industries
mapped to representative ETFs with multi-horizon analysis.

Main Components:
    - IndustryMapper: Static 50-industry -> ETF mapping
    - ETFDataFetcher: Multi-source data retrieval (Finnhub/AV/yfinance)
    - PersistentETFStore: Permanent Firestore storage for ETF history
    - PerformanceCalculator: Pandas-based multi-horizon returns calculation
    - FirebaseCache: Firestore caching layer for computed performance
    - SummaryGenerator: Morning market summary generation
    - IndustryService: Business logic orchestration
"""

from .industry_mapper import IndustryMapper
from .etf_data_fetcher import ETFDataFetcher
from .performance_calculator import PerformanceCalculator
from .firebase_cache import FirebaseCache
from .summary_generator import SummaryGenerator
from .api_service import IndustryService
from .persistent_store import PersistentETFStore

__all__ = [
    "IndustryMapper",
    "ETFDataFetcher",
    "PersistentETFStore",
    "PerformanceCalculator",
    "FirebaseCache",
    "SummaryGenerator",
    "IndustryService",
]

__version__ = "2.0.0"
