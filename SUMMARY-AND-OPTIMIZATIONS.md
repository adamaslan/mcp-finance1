# Technical Analysis MCP Server - Guide Summary & Optimization Recommendations

## Overview

This repository provides a **comprehensive technical analysis system** for stocks, ETFs, and crypto, featuring 150+ trading signals, 50+ technical indicators, and optional AI-powered signal ranking via Google's Gemini.

---

## Guide Summaries

### Guide 1: Complete Setup (guide1.md)

**Purpose**: Step-by-step setup instructions for the 100% free local MCP server.

**Key Contents**:
- Project structure with `src/technical_analysis_mcp/server.py`
- Installation via `pip install -e .`
- Claude Desktop configuration (macOS/Windows)
- Usage examples: analyze stocks, compare securities, screen ETFs
- Troubleshooting common issues
- Optional Cloud Run deployment for AI ranking

**Target Audience**: Users who want a zero-cost, privacy-focused local solution.

---

### Guide 2: Architecture Options (guide2.md)

**Purpose**: Detailed comparison of two architecture approaches.

| Feature | Option 1 (Free) | Option 2 (GCP) |
|---------|-----------------|----------------|
| Monthly Cost | $0 | $0-2 |
| Storage | In-memory only | Firestore + Cloud Storage |
| AI Ranking | Rule-based | Gemini AI |
| Historical Data | None | 30 days |
| Parallel Screening | Sequential | 10x faster |

**Key Contents**:
- Full architecture diagrams for both options
- GCP Free Tier allocation details (2M Cloud Run requests, 1GB Firestore, etc.)
- Smart caching strategies (3-level cache)
- Advanced features: historical comparison, parallel screening, scheduled reports
- Cost monitoring scripts

**Target Audience**: Users deciding between simplicity vs. advanced features.

---

### Guide 3: GCP Project Structure (guide3-reqs.md)

**Purpose**: Complete file structure and requirements for GCP deployment.

**Key Contents**:
- Full directory layout for Option 2
- All `requirements.txt` files for Cloud Run and Cloud Functions
- Dockerfile for containerized API
- Terraform configuration variables
- Firestore initialization script with stock universe lists (S&P 500, NASDAQ 100, sector ETFs)
- Deployment, testing, and cleanup scripts
- Main README for GCP option

**Target Audience**: Developers ready to deploy the GCP version.

---

### Guide 4: Jupyter Notebook Quick Start (guide4-jupyter.md)

**Purpose**: Rapid onboarding guide for the Jupyter notebook version.

**Key Contents**:
- 3-minute quick start instructions
- Notebook structure overview (16 cells: 7 setup, 9 analysis)
- Common use cases: daily watchlist, oversold screening, sector comparison
- Customization: adding signals, adjusting AI prompts, custom screeners
- Docker deployment for API mode
- Output examples (terminal, JSON, Excel)
- Configuration options for performance tuning

**Target Audience**: Data scientists and Jupyter users.

---

### Guide 5: Cell-by-Cell Explanation (guide5-cells-explained.md)

**Purpose**: Detailed implementation guide for each Jupyter notebook cell.

**Cells Covered**:
1. Configuration & imports
2. Data fetching & indicator calculation (50+ indicators)
3. Trading signal detection (40+ signals)
4. AI signal ranking (Gemini + fallback rules)
5. Main analysis pipeline
6. Save & export functions (JSON, CSV, Excel)
7. Comparison & screening functions
8. Interactive Plotly dashboards
9. Historical tracking & trend analysis
10. Utilities & quick actions
11. Advanced screening & custom filters
12. Portfolio analysis & correlation
13. Machine learning signal prediction (optional)
14. Alerts & notifications
15. Backtesting & performance tracking
16. Automation & scheduling (APScheduler)

**Target Audience**: Developers who want to understand or modify the code.

---

### Guide 6: GCP & AI Setup (guide6-startup.md)

**Purpose**: Step-by-step instructions for enabling GCP and Gemini AI.

**Key Contents**:
- Creating a GCP project
- Enabling required APIs (Cloud Run, Firestore, Pub/Sub, etc.)
- Setting up service account authentication
- Obtaining Gemini API key from Google AI Studio
- API restrictions and rate limits (60 req/min, 1500 req/day free tier)
- Monitoring usage in Cloud Console

**Target Audience**: First-time GCP users setting up cloud features.

---

## 5 Optimization Recommendations

### 1. Consolidate Documentation into a Single README

**Current State**: Six separate guide files create a fragmented experience.

**Recommendation**:
- Create a main `README.md` with a quick start for the most common use case
- Move detailed guides into a `docs/` folder
- Add a decision tree or flowchart to help users choose their path
- Include cross-references between related sections

**Benefits**:
- Easier onboarding for new users
- Single entry point reduces confusion
- Better discoverability of features

---

### 2. Add Automated Testing

**Current State**: No visible test suite beyond a placeholder `tests/` folder.

**Recommendation**:
- Add unit tests for indicator calculations (`test_indicators.py`)
- Add integration tests for signal detection (`test_signals.py`)
- Add mock-based tests for yfinance API calls
- Configure GitHub Actions for CI/CD
- Add test coverage reporting

**Example Structure**:
```
tests/
├── test_indicators.py      # Test RSI, MACD, etc.
├── test_signals.py         # Test signal detection logic
├── test_server.py          # Test MCP server endpoints
├── test_export.py          # Test file export functions
└── conftest.py             # Pytest fixtures
```

**Benefits**:
- Catch regressions early
- Build confidence for contributors
- Enable safer refactoring

---

### 3. Implement Proper Error Handling and Logging

**Current State**: Guides show basic `print()` statements and minimal error handling.

**Recommendation**:
- Replace `print()` with Python's `logging` module
- Add structured logging with levels (DEBUG, INFO, WARNING, ERROR)
- Create custom exception hierarchy (e.g., `DataFetchError`, `IndicatorError`)
- Add retry logic for network failures with exponential backoff
- Log to file for debugging production issues

**Example**:
```python
import logging

logger = logging.getLogger(__name__)

class DataFetchError(Exception):
    """Raised when yfinance data fetching fails."""
    pass

def fetch_data(symbol: str, period: str) -> pd.DataFrame:
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=period)
        if df.empty:
            raise DataFetchError(f"No data for {symbol}")
        logger.info("Fetched %d rows for %s", len(df), symbol)
        return df
    except Exception as e:
        logger.error("Failed to fetch %s: %s", symbol, e)
        raise DataFetchError(f"Fetch failed: {e}") from e
```

**Benefits**:
- Better debugging in production
- Clearer error messages for users
- Easier issue diagnosis

---

### 4. Add Type Hints and Pydantic Models

**Current State**: Limited type annotations make code harder to understand.

**Recommendation**:
- Add type hints to all functions
- Use Pydantic models for data structures (signals, indicators, results)
- Add `mypy` to CI for type checking
- Document expected data shapes clearly

**Example**:
```python
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class Signal(BaseModel):
    signal: str
    description: str
    strength: str  # STRONG BULLISH, BULLISH, NEUTRAL, BEARISH, STRONG BEARISH
    category: str
    ai_score: Optional[int] = None
    ai_reasoning: Optional[str] = None

class AnalysisResult(BaseModel):
    symbol: str
    timestamp: datetime
    price: float
    change: float
    signals: list[Signal]
    summary: dict
    indicators: dict

def analyze_stock(symbol: str, period: str = "1mo") -> AnalysisResult:
    ...
```

**Benefits**:
- Self-documenting code
- IDE autocompletion
- Runtime validation with Pydantic
- Catch type errors before runtime

---

### 5. Modularize the Codebase

**Current State**: Most logic appears to be in `server.py` (11KB) and Jupyter cells.

**Recommendation**:
- Split into focused modules:
  ```
  src/technical_analysis_mcp/
  ├── __init__.py
  ├── server.py           # MCP server entry point only
  ├── indicators.py       # All indicator calculations
  ├── signals.py          # Signal detection logic
  ├── ranking.py          # AI and rule-based ranking
  ├── data.py             # Data fetching and caching
  ├── export.py           # JSON, CSV, Excel exports
  ├── models.py           # Pydantic data models
  └── utils.py            # Helper functions
  ```
- Extract constants to a `config.py` or use environment variables
- Create abstract interfaces for extensibility (e.g., `RankingStrategy` protocol)

**Benefits**:
- Easier testing of individual components
- Better code organization
- Simpler onboarding for contributors
- Enables parallel development

---

## Quick Reference: Getting Started

| Goal | Guide | Command |
|------|-------|---------|
| Local setup (free) | guide1.md | `pip install -e .` |
| Choose architecture | guide2.md | N/A (decision guide) |
| Deploy to GCP | guide3-reqs.md | `./scripts/deploy.sh` |
| Use Jupyter notebook | guide4-jupyter.md | `jupyter notebook` |
| Understand code | guide5-cells-explained.md | N/A (reference) |
| Enable Gemini AI | guide6-startup.md | Get API key from AI Studio |

---

## Summary

This repository provides a powerful, flexible technical analysis system with multiple deployment options. The documentation is comprehensive but could benefit from consolidation. The five optimizations above would significantly improve code quality, maintainability, and developer experience without changing the core functionality.
