"""Caching layer for MCP tool results (Layer 2: Firestore persistent cache)."""

from .firestore_cache import MCPFirestoreCache

__all__ = ["MCPFirestoreCache"]
