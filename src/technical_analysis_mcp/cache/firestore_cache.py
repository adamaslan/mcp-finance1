"""Firestore Layer 2 persistent cache for MCP tool results.

Stores MCP tool results to Firestore for:
- Persistence across container restarts
- Sharing results across multiple Cloud Run instances
- Fallback when APIs are rate-limited or unavailable
"""

import logging
import os
from datetime import datetime
from typing import Any, Optional

logger = logging.getLogger(__name__)


class MCPFirestoreCache:
    """Firestore-based persistent cache for MCP tool results."""

    COLLECTION_NAME = "mcp_tool_cache"
    PORTFOLIO_TICKERS_DOC = "portfolio_tickers"

    def __init__(self, project_id: Optional[str] = None):
        """Initialize Firestore cache.

        Args:
            project_id: GCP project ID. If None, uses GCP_PROJECT_ID env var.

        Raises:
            ImportError: If firebase_admin not installed.
        """
        try:
            import firebase_admin
            from firebase_admin import credentials, firestore
        except ImportError as e:
            raise ImportError(
                "firebase_admin not installed. Install with: "
                "mamba install -c conda-forge firebase-admin"
            ) from e

        # Initialize Firebase app if not already initialized
        try:
            firebase_admin.get_app()
            logger.debug("Using existing Firebase app")
        except ValueError:
            # No app exists, initialize new one
            project_id = project_id or os.getenv("GCP_PROJECT_ID")
            if not project_id:
                raise ValueError(
                    "GCP_PROJECT_ID environment variable not set"
                )

            # Use Application Default Credentials (works in Cloud Run)
            cred = credentials.ApplicationDefault()
            firebase_admin.initialize_app(cred, {"projectId": project_id})
            logger.info("Initialized Firebase app for project: %s", project_id)

        self._db = firestore.client()
        logger.info("MCPFirestoreCache initialized")

    def write_tool_result(
        self,
        tool_name: str,
        cache_key: str,
        result: dict[str, Any],
        period: Optional[str] = None,
    ) -> None:
        """Write a tool result to Firestore.

        Args:
            tool_name: Name of the MCP tool (e.g., "analyze_security")
            cache_key: Cache key (e.g., symbol "AAPL" or joined key)
            result: The tool result dict to cache
            period: Optional period parameter (for tools that use it)
        """
        if not result:
            logger.warning("Skipping write of empty result for %s/%s", tool_name, cache_key)
            return

        try:
            data = {
                "result": result,
                "updated_at": datetime.utcnow().isoformat(),
            }
            if period:
                data["period"] = period

            doc_ref = (
                self._db.collection(self.COLLECTION_NAME)
                .document(tool_name)
                .collection("results")
                .document(cache_key)
            )
            doc_ref.set(data)
            logger.debug("Cached result for %s/%s", tool_name, cache_key)
        except Exception as e:
            logger.warning(
                "Failed to write cache for %s/%s: %s", tool_name, cache_key, e
            )

    def read_tool_result(
        self, tool_name: str, cache_key: str
    ) -> Optional[dict[str, Any]]:
        """Read a cached tool result from Firestore.

        Args:
            tool_name: Name of the MCP tool
            cache_key: Cache key

        Returns:
            The cached result dict, or None if not found/error
        """
        try:
            doc_ref = (
                self._db.collection(self.COLLECTION_NAME)
                .document(tool_name)
                .collection("results")
                .document(cache_key)
            )
            doc = doc_ref.get()
            if not doc.exists:
                logger.debug("No cached result for %s/%s", tool_name, cache_key)
                return None
            data = doc.to_dict()
            logger.debug("Retrieved cached result for %s/%s", tool_name, cache_key)
            return data
        except Exception as e:
            logger.warning(
                "Failed to read cache for %s/%s: %s", tool_name, cache_key, e
            )
            return None

    def read_latest_tool_result(self, tool_name: str) -> Optional[dict[str, Any]]:
        """Read the most recently cached result for a tool.

        Used by frontend to display cached data without specifying a key.

        Args:
            tool_name: Name of the MCP tool

        Returns:
            The most recently written result dict, or None if not found/error
        """
        try:
            docs = (
                self._db.collection(self.COLLECTION_NAME)
                .document(tool_name)
                .collection("results")
                .order_by("updated_at", direction="DESCENDING")
                .limit(1)
                .stream()
            )
            for doc in docs:
                data = doc.to_dict()
                logger.debug("Retrieved latest cached result for %s", tool_name)
                return data
            logger.debug("No cached results found for %s", tool_name)
            return None
        except Exception as e:
            logger.warning("Failed to read latest cache for %s: %s", tool_name, e)
            return None

    def write_portfolio_tickers(self, tickers: list[str]) -> None:
        """Write portfolio tickers to cache.

        Called after portfolio_risk() to enable other tools to target these tickers.

        Args:
            tickers: List of stock symbols (uppercase)
        """
        if not tickers:
            logger.warning("Skipping write of empty ticker list")
            return

        try:
            data = {
                "tickers": sorted(set(tickers)),  # deduplicate + sort
                "updated_at": datetime.utcnow().isoformat(),
            }
            doc_ref = self._db.collection(self.COLLECTION_NAME).document(
                self.PORTFOLIO_TICKERS_DOC
            )
            doc_ref.set(data)
            logger.info("Cached %d portfolio tickers", len(tickers))
        except Exception as e:
            logger.warning("Failed to write portfolio tickers: %s", e)

    def read_portfolio_tickers(self) -> list[str]:
        """Read cached portfolio tickers.

        Returns:
            List of symbols, or empty list if not found/error
        """
        try:
            doc_ref = self._db.collection(self.COLLECTION_NAME).document(
                self.PORTFOLIO_TICKERS_DOC
            )
            doc = doc_ref.get()
            if not doc.exists:
                logger.debug("No cached portfolio tickers")
                return []
            data = doc.to_dict()
            tickers = data.get("tickers", [])
            logger.debug("Retrieved %d cached portfolio tickers", len(tickers))
            return tickers
        except Exception as e:
            logger.warning("Failed to read portfolio tickers: %s", e)
            return []
