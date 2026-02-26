"""Industry Performance Tracking Module.

Standalone module for tracking performance of 50 US economy industries
mapped to representative ETFs with multi-horizon analysis.

Main Components:
    - IndustryMapper: Static 50-industry → ETF mapping
    - ETFDataFetcher: Alpha Vantage historical data retrieval
    - PerformanceCalculator: Pandas-based multi-horizon returns calculation
    - FirebaseCache: Firestore caching layer
    - SummaryGenerator: Morning market summary generation
    - IndustryService: Business logic orchestration
"""

from .industry_mapper import IndustryMapper
from .etf_data_fetcher import ETFDataFetcher
from .performance_calculator import PerformanceCalculator
from .firebase_cache import FirebaseCache
from .summary_generator import SummaryGenerator
from .api_service import IndustryService

__all__ = [
    "IndustryMapper",
    "ETFDataFetcher",
    "PerformanceCalculator",
    "FirebaseCache",
    "SummaryGenerator",
    "IndustryService",
]

__version__ = "1.0.0"
