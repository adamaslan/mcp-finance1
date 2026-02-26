#!/usr/bin/env python3
"""Local MCP server entry point. No GCP services required.

Run the MCP Finance server locally via stdio for Claude Desktop integration.

Usage:
    mamba activate fin-ai1
    python run_local.py

Prerequisites:
    - Copy .env.example to .env with real API keys:
      * FINNHUB_API_KEY (required, primary data source)
      * ALPHA_VANTAGE_KEY (optional, fallback data source)
      * GEMINI_API_KEY (optional, for AI analysis)
    - Ensure fin-ai1 environment is activated
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

# Add src/ and project root to Python path
_repo_root = Path(__file__).parent
sys.path.insert(0, str(_repo_root / "src"))
sys.path.insert(0, str(_repo_root))  # for fibonacci/ package

# Load environment variables from .env files if present
try:
    from dotenv import load_dotenv
    load_dotenv(_repo_root / ".env")
    load_dotenv(_repo_root / ".env.local", override=False)
except ImportError:
    pass  # python-dotenv not installed, rely on shell environment

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def main() -> None:
    """Run the MCP server via stdio."""
    logger.info("=" * 80)
    logger.info("MCP Finance - Local Mode")
    logger.info("=" * 80)
    logger.info("Repository root: %s", _repo_root)
    logger.info("Python path includes: src/ and fibonacci/")

    try:
        from mcp.server.stdio import stdio_server
        from technical_analysis_mcp.server import app

        logger.info("Loaded MCP server successfully")

    except ImportError as e:
        logger.error("Failed to import MCP server: %s", e)
        logger.error("Make sure fin-ai1 environment is activated")
        sys.exit(1)

    async def run_server() -> None:
        """Async wrapper to run the MCP server."""
        logger.info("Starting MCP server on stdio...")
        async with stdio_server() as (read_stream, write_stream):
            await app.run(read_stream, write_stream, app.create_initialization_options())

    try:
        asyncio.run(run_server())
    except KeyboardInterrupt:
        logger.info("MCP server stopped by user")
        sys.exit(0)
    except Exception as e:
        logger.exception("MCP server crashed: %s", e)
        sys.exit(1)


if __name__ == "__main__":
    main()
