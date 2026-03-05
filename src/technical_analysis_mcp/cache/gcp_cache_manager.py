"""
GCP-Optimized Cache Manager - Implements 7-Layer Workflow

Layer 0: Secret Manager (API keys)
Layer 1: Memorystore/Redis (distributed cache)
Layer 2a: Firestore (real-time results)
Layer 2b: Cloud Storage (historical data)
Layer 3: BigQuery (pre-computed metrics)
Layer 4: Cloud Tasks (background refresh)
Layer 5: API Providers (yfinance, Alpha Vantage, Finnhub)
"""

import json
import logging
import os
import time
from datetime import datetime
from typing import Optional, Any, Dict
from dataclasses import dataclass
from enum import Enum

import redis
from google.cloud import firestore, storage, bigquery, tasks_v2, secretmanager, datastore
from google.api_core import gapic_v1
import asyncio

logger = logging.getLogger(__name__)


class CacheLayer(Enum):
    """Cache layer names for tracking."""
    SECRET_MANAGER = "L0"
    REDIS = "L1"
    FIRESTORE = "L2a"
    CLOUD_STORAGE = "L2b"
    BIGQUERY = "L3"
    CLOUD_TASKS = "L4"
    API_PROVIDER = "L5"


@dataclass
class CacheHit:
    """Result of cache lookup."""
    layer: CacheLayer
    data: Any
    timestamp: datetime


class GCPCacheManager:
    """
    Unified cache manager implementing all 7 GCP-optimized layers.
    Automatically falls through layers until data found.
    """

    def __init__(self, project_id: str = "ttb-lang1"):
        self.project_id = project_id
        self.initialized = False
        self.layers_available = {}

        # Initialize all layers
        self._init_layers()

    def _init_layers(self):
        """Initialize all GCP services with fallback."""
        self.project_id = os.getenv("GCP_PROJECT_ID", self.project_id)

        # L0: Secret Manager
        try:
            self.secrets_client = secretmanager.SecretManagerServiceClient()
            self.layers_available[CacheLayer.SECRET_MANAGER] = True
            logger.info("✓ Secret Manager initialized")
        except Exception as e:
            logger.warning(f"✗ Secret Manager failed: {e}")
            self.layers_available[CacheLayer.SECRET_MANAGER] = False

        # L1: Redis/Memorystore
        try:
            redis_host = os.getenv("REDIS_HOST", "localhost")
            redis_port = int(os.getenv("REDIS_PORT", 6379))
            self.redis = redis.Redis(
                host=redis_host,
                port=redis_port,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_keepalive=True,
            )
            # Test connection
            self.redis.ping()
            self.layers_available[CacheLayer.REDIS] = True
            logger.info(f"✓ Redis initialized ({redis_host}:{redis_port})")
        except Exception as e:
            logger.warning(f"✗ Redis failed: {e}")
            self.layers_available[CacheLayer.REDIS] = False
            self.redis = None

        # L2a: Firestore
        try:
            self.firestore_db = firestore.Client(project=self.project_id)
            self.firestore_db.collection("_health").document("check").get()  # Test
            self.layers_available[CacheLayer.FIRESTORE] = True
            logger.info("✓ Firestore initialized")
        except Exception as e:
            logger.warning(f"✗ Firestore failed: {e}")
            self.layers_available[CacheLayer.FIRESTORE] = False
            self.firestore_db = None

        # L2b: Cloud Storage
        try:
            self.storage_client = storage.Client(project=self.project_id)
            bucket_name = os.getenv("BUCKET_NAME", "mcp-cache-historical")
            self.bucket = self.storage_client.bucket(bucket_name)
            self.bucket.reload()  # Test
            self.layers_available[CacheLayer.CLOUD_STORAGE] = True
            logger.info(f"✓ Cloud Storage initialized ({bucket_name})")
        except Exception as e:
            logger.warning(f"✗ Cloud Storage failed: {e}")
            self.layers_available[CacheLayer.CLOUD_STORAGE] = False
            self.bucket = None

        # L3: BigQuery
        try:
            self.bq_client = bigquery.Client(project=self.project_id)
            # Test connection
            self.bq_client.get_dataset(f"{self.project_id}.mcp_cache")
            self.layers_available[CacheLayer.BIGQUERY] = True
            logger.info("✓ BigQuery initialized")
        except Exception as e:
            logger.warning(f"✗ BigQuery failed: {e}")
            self.layers_available[CacheLayer.BIGQUERY] = False
            self.bq_client = None

        # L4: Cloud Tasks
        try:
            self.tasks_client = tasks_v2.CloudTasksClient()
            self.cloud_tasks_region = os.getenv("CLOUD_TASKS_REGION", "us-central1")
            self.cloud_tasks_queue = os.getenv("CLOUD_TASKS_QUEUE", "mcp-cache-refresh")
            self.layers_available[CacheLayer.CLOUD_TASKS] = True
            logger.info(f"✓ Cloud Tasks initialized ({self.cloud_tasks_queue})")
        except Exception as e:
            logger.warning(f"✗ Cloud Tasks failed: {e}")
            self.layers_available[CacheLayer.CLOUD_TASKS] = False
            self.tasks_client = None

        self.initialized = True
        logger.info(f"GCP Cache Manager initialized: {sum(self.layers_available.values())}/6 layers available")

    # ============================================================================
    # L0: SECRET MANAGER
    # ============================================================================

    def get_secret(self, secret_id: str, version: str = "latest") -> Optional[str]:
        """
        Fetch API key from Secret Manager.

        Args:
            secret_id: Name of secret (e.g., "finnhub-api-key")
            version: Version to fetch (default: "latest")

        Returns:
            Secret value or None if not available
        """
        if not self.layers_available.get(CacheLayer.SECRET_MANAGER):
            logger.warning("Secret Manager not available")
            return None

        try:
            name = f"projects/{self.project_id}/secrets/{secret_id}/versions/{version}"
            response = self.secrets_client.access_secret_version(request={"name": name})
            secret = response.payload.data.decode("UTF-8")
            logger.debug(f"✓ Secret retrieved: {secret_id}")
            return secret
        except Exception as e:
            logger.error(f"Secret Manager read failed for {secret_id}: {e}")
            return None

    # ============================================================================
    # L1: REDIS (Distributed Cache)
    # ============================================================================

    def get_from_redis(self, key: str) -> Optional[dict]:
        """
        Get value from Redis (L1).

        Args:
            key: Cache key

        Returns:
            Cached value or None
        """
        if not self.redis:
            return None

        try:
            value = self.redis.get(key)
            if value:
                logger.debug(f"L1 HIT: {key}")
                return json.loads(value)
            return None
        except redis.ConnectionError:
            logger.warning("Redis connection failed, skipping L1")
            return None

    def set_in_redis(self, key: str, value: Any, ttl: int = 300) -> bool:
        """
        Set value in Redis with TTL (non-blocking).

        Args:
            key: Cache key
            value: Data to cache
            ttl: Time-to-live in seconds (default: 300)

        Returns:
            True if successful, False otherwise
        """
        if not self.redis:
            return False

        try:
            self.redis.setex(key, ttl, json.dumps(value))
            logger.debug(f"L1 SET: {key} (TTL: {ttl}s)")
            return True
        except redis.ConnectionError:
            logger.warning("Redis write failed, continuing without L1")
            return False

    # ============================================================================
    # L2A: FIRESTORE (Real-time Results)
    # ============================================================================

    async def get_from_firestore(self, collection: str, doc_id: str) -> Optional[dict]:
        """
        Get cached tool result from Firestore (L2a).

        Args:
            collection: Firestore collection name
            doc_id: Document ID

        Returns:
            Cached result or None
        """
        if not self.firestore_db:
            return None

        try:
            doc = await self.firestore_db.collection(collection).document(doc_id).get()
            if doc.exists:
                logger.debug(f"L2a HIT: {collection}/{doc_id}")
                return doc.to_dict()
            return None
        except Exception as e:
            logger.warning(f"Firestore read failed: {e}")
            return None

    async def set_in_firestore(
        self,
        collection: str,
        doc_id: str,
        data: dict,
        ttl: int = 300
    ) -> bool:
        """
        Write tool result to Firestore (non-blocking, L2a).

        Args:
            collection: Firestore collection name
            doc_id: Document ID
            data: Data to store
            ttl: Time-to-live in seconds

        Returns:
            True if successful (non-blocking, so always returns immediately)
        """
        if not self.firestore_db:
            return False

        try:
            # Non-blocking write
            asyncio.create_task(
                self.firestore_db.collection(collection).document(doc_id).set({
                    "result": data,
                    "timestamp": firestore.SERVER_TIMESTAMP,
                    "ttl": ttl,
                }, merge=True)
            )
            logger.debug(f"L2a SET (async): {collection}/{doc_id}")
            return True
        except Exception as e:
            logger.warning(f"Firestore write failed: {e}")
            return False

    # ============================================================================
    # L2B: CLOUD STORAGE (Historical Data)
    # ============================================================================

    def get_from_cloud_storage(self, symbol: str, period: str = "daily") -> Optional[dict]:
        """
        Get historical data from Cloud Storage (L2b).

        Args:
            symbol: Stock symbol (e.g., "AAPL")
            period: Time period (e.g., "daily", "1h", "15m")

        Returns:
            Historical data or None
        """
        if not self.bucket:
            return None

        try:
            blob = self.bucket.blob(f"historical/{symbol}/{period}/data.json")
            if blob.exists():
                age = time.time() - blob.updated.timestamp()
                if age < 300:  # Still fresh (5 min TTL)
                    data = json.loads(blob.download_as_string())
                    logger.debug(f"L2b HIT: historical/{symbol}/{period}")
                    return data
            return None
        except Exception as e:
            logger.debug(f"Cloud Storage read failed: {e}")
            return None

    def set_in_cloud_storage(self, symbol: str, data: dict, period: str = "daily") -> bool:
        """
        Write historical data to Cloud Storage (non-blocking, L2b).

        Args:
            symbol: Stock symbol
            data: Data to store
            period: Time period

        Returns:
            True if successful
        """
        if not self.bucket:
            return False

        try:
            blob = self.bucket.blob(f"historical/{symbol}/{period}/data.json")
            blob.upload_from_string(
                json.dumps(data),
                content_type="application/json"
            )
            logger.debug(f"L2b SET: historical/{symbol}/{period}")
            return True
        except Exception as e:
            logger.warning(f"Cloud Storage write failed: {e}")
            return False

    # ============================================================================
    # L3: BIGQUERY (Pre-computed Metrics)
    # ============================================================================

    def get_from_bigquery(self, symbol: str) -> Optional[dict]:
        """
        Get pre-computed daily metrics from BigQuery (L3).

        Args:
            symbol: Stock symbol

        Returns:
            Pre-computed metrics or None
        """
        if not self.bq_client:
            return None

        try:
            query = f"""
            SELECT *
            FROM `{self.project_id}.mcp_cache.daily_analysis`
            WHERE symbol = '{symbol}'
            ORDER BY trade_date DESC
            LIMIT 1
            """
            results = self.bq_client.query_and_wait(query, timeout=10)
            if results.total_rows > 0:
                metrics = dict(results.to_dataframe().iloc[0])
                logger.debug(f"L3 HIT: BigQuery/{symbol}")
                return metrics
            return None
        except Exception as e:
            logger.debug(f"BigQuery query failed: {e}")
            return None

    # ============================================================================
    # L4: CLOUD TASKS (Background Refresh)
    # ============================================================================

    def schedule_cache_refresh(
        self,
        symbol: str,
        tool_name: str,
        delay_seconds: int = 5
    ) -> bool:
        """
        Schedule background cache refresh via Cloud Tasks (guaranteed execution).

        Args:
            symbol: Stock symbol
            tool_name: MCP tool name (e.g., "analyze_security")
            delay_seconds: Delay before execution (default: 5)

        Returns:
            True if scheduled successfully
        """
        if not self.tasks_client:
            logger.warning("Cloud Tasks not available, skipping background refresh")
            return False

        try:
            parent = self.tasks_client.queue_path(
                self.project_id,
                self.cloud_tasks_region,
                self.cloud_tasks_queue
            )

            # Get refresh endpoint URL from environment
            refresh_url = os.getenv(
                "CACHE_REFRESH_URL",
                "https://mcp-backend.cloud.run/api/cache-refresh"
            )

            task = {
                "http_request": {
                    "http_method": tasks_v2.HttpMethod.POST,
                    "url": refresh_url,
                    "headers": {"Content-Type": "application/json"},
                    "body": json.dumps({
                        "symbol": symbol,
                        "tool": tool_name,
                        "priority": "low"
                    }).encode(),
                },
                "schedule_time": {"seconds": int(time.time()) + delay_seconds}
            }

            self.tasks_client.create_task(request={"parent": parent, "task": task})
            logger.debug(f"L4 REFRESH SCHEDULED: {symbol}/{tool_name}")
            return True

        except Exception as e:
            logger.error(f"Cloud Tasks scheduling failed: {e}")
            return False

    # ============================================================================
    # QUOTA TRACKING (Datastore)
    # ============================================================================

    def get_api_quota(self, provider: str) -> int:
        """
        Get remaining API quota for provider.

        Args:
            provider: Provider name (e.g., "alpha-vantage")

        Returns:
            Remaining calls available
        """
        try:
            ds = datastore.Client(project=self.project_id)
            key = ds.key("APIQuota", provider)
            quota = ds.get(key)

            if quota is None:
                # Initialize with default
                if provider == "alpha-vantage":
                    return 25
                return 100

            remaining = quota.get("remaining", 0)
            logger.debug(f"Quota check: {provider} has {remaining} calls remaining")
            return remaining

        except Exception as e:
            logger.error(f"Quota check failed: {e}")
            return 0

    def decrement_api_quota(self, provider: str) -> bool:
        """
        Atomically decrement API quota.

        Args:
            provider: Provider name

        Returns:
            True if quota decremented, False if exhausted
        """
        try:
            ds = datastore.Client(project=self.project_id)
            key = ds.key("APIQuota", provider)

            with ds.transaction():
                quota = ds.get(key)
                if quota is None:
                    quota = datastore.Entity(key=key)
                    quota["remaining"] = 24 if provider == "alpha-vantage" else 99
                else:
                    quota["remaining"] -= 1

                quota["updated"] = datetime.utcnow()

                if quota["remaining"] <= 0:
                    logger.critical(f"API quota exhausted for {provider}")
                    return False

                ds.put(quota)
                logger.debug(f"Quota decremented: {provider} ({quota['remaining']} remaining)")
                return True

        except Exception as e:
            logger.error(f"Quota decrement failed: {e}")
            return False

    # ============================================================================
    # UNIFIED GET METHOD (Implements Full 7-Layer Fallthrough)
    # ============================================================================

    async def get(
        self,
        key: str,
        symbol: str = None,
        tool_name: str = None
    ) -> CacheHit:
        """
        Retrieve from cache following 7-layer hierarchy.

        Tries in order:
        1. L1: Redis (if available)
        2. L2a: Firestore (if available)
        3. L2b: Cloud Storage (if symbol provided)
        4. L3: BigQuery (if symbol provided)
        5. Returns None if all miss (caller should fetch from L5 API)

        Args:
            key: Cache key
            symbol: Stock symbol (optional, for L2b/L3)
            tool_name: Tool name (optional, for scheduling refresh)

        Returns:
            CacheHit with data and layer, or None if all miss
        """
        # L1: Redis
        if data := self.get_from_redis(key):
            hit = CacheHit(layer=CacheLayer.REDIS, data=data, timestamp=datetime.utcnow())
            # Schedule background refresh if specified
            if symbol and tool_name:
                self.schedule_cache_refresh(symbol, tool_name)
            return hit

        # L2a: Firestore
        if data := await self.get_from_firestore("mcp_tool_cache", key):
            hit = CacheHit(layer=CacheLayer.FIRESTORE, data=data, timestamp=datetime.utcnow())
            if symbol and tool_name:
                self.schedule_cache_refresh(symbol, tool_name)
            return hit

        # L2b: Cloud Storage (if symbol provided)
        if symbol:
            if data := self.get_from_cloud_storage(symbol):
                return CacheHit(
                    layer=CacheLayer.CLOUD_STORAGE,
                    data=data,
                    timestamp=datetime.utcnow()
                )

        # L3: BigQuery (if symbol provided)
        if symbol:
            if data := self.get_from_bigquery(symbol):
                return CacheHit(
                    layer=CacheLayer.BIGQUERY,
                    data=data,
                    timestamp=datetime.utcnow()
                )

        logger.debug(f"Cache miss on all layers: {key}")
        return None

    async def set(
        self,
        key: str,
        data: Any,
        symbol: str = None,
        ttl: int = 300
    ) -> int:
        """
        Write to all available cache layers (non-blocking).

        Writes to:
        1. L1: Redis (immediate)
        2. L2a: Firestore (async)
        3. L2b: Cloud Storage (async)

        Args:
            key: Cache key
            data: Data to cache
            symbol: Stock symbol (optional, for L2b)
            ttl: Time-to-live in seconds

        Returns:
            Number of layers written to
        """
        layers_written = 0

        # L1: Redis (immediate)
        if self.set_in_redis(key, data, ttl):
            layers_written += 1

        # L2a: Firestore (async, non-blocking)
        if await self.set_in_firestore("mcp_tool_cache", key, data, ttl):
            layers_written += 1

        # L2b: Cloud Storage (async, non-blocking)
        if symbol:
            asyncio.create_task(
                asyncio.to_thread(self.set_in_cloud_storage, symbol, data)
            )
            layers_written += 1

        logger.info(f"Cached to {layers_written} layers: {key}")
        return layers_written

    # ============================================================================
    # STATUS & MONITORING
    # ============================================================================

    def health_check(self) -> Dict[str, bool]:
        """
        Check status of all cache layers.

        Returns:
            Dictionary with layer names and availability
        """
        return self.layers_available.copy()

    def log_status(self):
        """Log current cache system status."""
        status = self.health_check()
        available = sum(status.values())
        total = len(status)

        logger.info(f"Cache system status: {available}/{total} layers available")
        for layer, available in status.items():
            symbol = "✓" if available else "✗"
            logger.info(f"  {symbol} {layer.name} ({layer.value})")


# Global instance
_cache_manager = None


def get_cache_manager() -> GCPCacheManager:
    """Get or create global cache manager instance."""
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = GCPCacheManager()
    return _cache_manager
