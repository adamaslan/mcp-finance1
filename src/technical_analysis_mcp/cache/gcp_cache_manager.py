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

    Usage:
        manager = GCPCacheManager()
        await manager.initialize()   # must be called before use
    """

    def __init__(self, project_id: str = "ttb-lang1"):
        self.project_id = os.getenv("GCP_PROJECT_ID", project_id)
        self.initialized = False
        self.layers_available: Dict[CacheLayer, bool] = {}

        # Clients set during initialize()
        self.secrets_client: Optional[secretmanager.SecretManagerServiceClient] = None
        self.redis: Optional[redis.Redis] = None
        self.firestore_db: Optional[firestore.AsyncClient] = None
        self.storage_client: Optional[storage.Client] = None
        self.bucket: Optional[storage.Bucket] = None
        self.bq_client: Optional[bigquery.Client] = None
        self.tasks_client: Optional[tasks_v2.CloudTasksClient] = None
        self.ds_client: Optional[datastore.Client] = None
        self.cloud_tasks_region: str = ""
        self.cloud_tasks_queue: str = ""

    async def initialize(self) -> None:
        """
        Initialize all GCP service clients.

        Blocking I/O (ping, health-check reads) is offloaded to a thread pool
        so the event loop is never blocked. Safe to call from async startup.
        """
        await asyncio.gather(
            self._init_secret_manager(),
            self._init_redis(),
            self._init_firestore(),
            self._init_cloud_storage(),
            self._init_bigquery(),
            self._init_cloud_tasks(),
            self._init_datastore(),
        )
        self.initialized = True
        available = sum(self.layers_available.values())
        logger.info(f"GCP Cache Manager initialized: {available}/6 layers available")

    # ------------------------------------------------------------------
    # Layer initializers (each runs its blocking probe in a thread)
    # ------------------------------------------------------------------

    async def _init_secret_manager(self) -> None:
        try:
            self.secrets_client = secretmanager.SecretManagerServiceClient()
            self.layers_available[CacheLayer.SECRET_MANAGER] = True
            logger.info("✓ Secret Manager initialized")
        except Exception as e:
            logger.warning(f"✗ Secret Manager failed: {e}")
            self.layers_available[CacheLayer.SECRET_MANAGER] = False

    async def _init_redis(self) -> None:
        try:
            redis_host = os.getenv("REDIS_HOST", "localhost")
            redis_port = int(os.getenv("REDIS_PORT", 6379))
            r = redis.Redis(
                host=redis_host,
                port=redis_port,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_keepalive=True,
            )
            await asyncio.to_thread(r.ping)
            self.redis = r
            self.layers_available[CacheLayer.REDIS] = True
            logger.info(f"✓ Redis initialized ({redis_host}:{redis_port})")
        except Exception as e:
            logger.warning(f"✗ Redis failed: {e}")
            self.layers_available[CacheLayer.REDIS] = False
            self.redis = None

    async def _init_firestore(self) -> None:
        try:
            # AsyncClient is required so await calls inside async methods work
            self.firestore_db = firestore.AsyncClient(project=self.project_id)
            await self.firestore_db.collection("_health").document("check").get()
            self.layers_available[CacheLayer.FIRESTORE] = True
            logger.info("✓ Firestore initialized")
        except Exception as e:
            logger.warning(f"✗ Firestore failed: {e}")
            self.layers_available[CacheLayer.FIRESTORE] = False
            self.firestore_db = None

    async def _init_cloud_storage(self) -> None:
        try:
            bucket_name = os.getenv("BUCKET_NAME", "mcp-cache-historical")
            client = storage.Client(project=self.project_id)
            bucket = client.bucket(bucket_name)
            await asyncio.to_thread(bucket.reload)
            self.storage_client = client
            self.bucket = bucket
            self.layers_available[CacheLayer.CLOUD_STORAGE] = True
            logger.info(f"✓ Cloud Storage initialized ({bucket_name})")
        except Exception as e:
            logger.warning(f"✗ Cloud Storage failed: {e}")
            self.layers_available[CacheLayer.CLOUD_STORAGE] = False
            self.bucket = None

    async def _init_bigquery(self) -> None:
        try:
            client = bigquery.Client(project=self.project_id)
            await asyncio.to_thread(client.get_dataset, f"{self.project_id}.mcp_cache")
            self.bq_client = client
            self.layers_available[CacheLayer.BIGQUERY] = True
            logger.info("✓ BigQuery initialized")
        except Exception as e:
            logger.warning(f"✗ BigQuery failed: {e}")
            self.layers_available[CacheLayer.BIGQUERY] = False
            self.bq_client = None

    async def _init_cloud_tasks(self) -> None:
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

    async def _init_datastore(self) -> None:
        try:
            self.ds_client = datastore.Client(project=self.project_id)
            logger.info("✓ Datastore (quota tracker) initialized")
        except Exception as e:
            logger.warning(f"✗ Datastore failed: {e}")
            self.ds_client = None

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

    async def get_from_redis(self, key: str) -> Optional[dict]:
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
            value = await asyncio.to_thread(self.redis.get, key)
            if value:
                logger.debug(f"L1 HIT: {key}")
                return json.loads(value)
            return None
        except redis.ConnectionError:
            logger.warning("Redis connection failed, skipping L1")
            return None

    async def set_in_redis(self, key: str, value: Any, ttl: int = 300) -> bool:
        """
        Set value in Redis with TTL.

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
            await asyncio.to_thread(self.redis.setex, key, ttl, json.dumps(value))
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
            True if task scheduled
        """
        if not self.firestore_db:
            return False

        try:
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

    async def get_from_cloud_storage(self, symbol: str, period: str = "daily") -> Optional[dict]:
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
            return await asyncio.to_thread(self._read_cloud_storage_blob, symbol, period)
        except Exception as e:
            logger.debug(f"Cloud Storage read failed: {e}")
            return None

    def _read_cloud_storage_blob(self, symbol: str, period: str) -> Optional[dict]:
        """Blocking helper for get_from_cloud_storage — runs in thread pool."""
        blob = self.bucket.blob(f"historical/{symbol}/{period}/data.json")
        if blob.exists():
            age = time.time() - blob.updated.timestamp()
            if age < 300:
                data = json.loads(blob.download_as_string())
                logger.debug(f"L2b HIT: historical/{symbol}/{period}")
                return data
        return None

    async def set_in_cloud_storage(self, symbol: str, data: dict, period: str = "daily") -> bool:
        """
        Write historical data to Cloud Storage (L2b).

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
            await asyncio.to_thread(self._write_cloud_storage_blob, symbol, data, period)
            return True
        except Exception as e:
            logger.warning(f"Cloud Storage write failed: {e}")
            return False

    def _write_cloud_storage_blob(self, symbol: str, data: dict, period: str) -> None:
        """Blocking helper for set_in_cloud_storage — runs in thread pool."""
        blob = self.bucket.blob(f"historical/{symbol}/{period}/data.json")
        blob.upload_from_string(json.dumps(data), content_type="application/json")
        logger.debug(f"L2b SET: historical/{symbol}/{period}")

    # ============================================================================
    # L3: BIGQUERY (Pre-computed Metrics)
    # ============================================================================

    async def get_from_bigquery(self, symbol: str) -> Optional[dict]:
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
            return await asyncio.to_thread(self._query_bigquery, symbol)
        except Exception as e:
            logger.debug(f"BigQuery query failed: {e}")
            return None

    def _query_bigquery(self, symbol: str) -> Optional[dict]:
        """Blocking helper for get_from_bigquery — runs in thread pool."""
        query = f"""
        SELECT *
        FROM `{self.project_id}.mcp_cache.daily_analysis`
        WHERE symbol = @symbol
        ORDER BY trade_date DESC
        LIMIT 1
        """
        job_config = bigquery.QueryJobConfig(
            query_parameters=[bigquery.ScalarQueryParameter("symbol", "STRING", symbol)]
        )
        results = self.bq_client.query_and_wait(query, job_config=job_config, timeout=10)
        if results.total_rows > 0:
            metrics = dict(results.to_dataframe().iloc[0])
            logger.debug(f"L3 HIT: BigQuery/{symbol}")
            return metrics
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

    async def get_api_quota(self, provider: str) -> int:
        """
        Get remaining API quota for provider.

        Args:
            provider: Provider name (e.g., "finnhub")

        Returns:
            Remaining calls available
        """
        if not self.ds_client:
            return 0

        try:
            return await asyncio.to_thread(self._read_quota, provider)
        except Exception as e:
            logger.error(f"Quota check failed: {e}")
            return 0

    def _read_quota(self, provider: str) -> int:
        """Blocking helper for get_api_quota — runs in thread pool."""
        key = self.ds_client.key("APIQuota", provider)
        quota = self.ds_client.get(key)
        if quota is None:
            return 25 if provider == "alpha-vantage" else 100
        remaining = quota.get("remaining", 0)
        logger.debug(f"Quota check: {provider} has {remaining} calls remaining")
        return remaining

    async def decrement_api_quota(self, provider: str) -> bool:
        """
        Atomically decrement API quota.

        Args:
            provider: Provider name

        Returns:
            True if quota decremented, False if exhausted
        """
        if not self.ds_client:
            return False

        try:
            return await asyncio.to_thread(self._decrement_quota, provider)
        except Exception as e:
            logger.error(f"Quota decrement failed: {e}")
            return False

    def _decrement_quota(self, provider: str) -> bool:
        """Blocking helper for decrement_api_quota — runs in thread pool."""
        key = self.ds_client.key("APIQuota", provider)

        with self.ds_client.transaction():
            quota = self.ds_client.get(key)
            if quota is None:
                quota = datastore.Entity(key=key)
                quota["remaining"] = 24 if provider == "alpha-vantage" else 99
            else:
                quota["remaining"] -= 1

            quota["updated"] = datetime.utcnow()

            if quota["remaining"] <= 0:
                logger.critical(f"API quota exhausted for {provider}")
                return False

            self.ds_client.put(quota)
            logger.debug(f"Quota decremented: {provider} ({quota['remaining']} remaining)")
            return True

    # ============================================================================
    # UNIFIED GET METHOD (Implements Full 7-Layer Fallthrough)
    # ============================================================================

    async def get(
        self,
        key: str,
        symbol: str = None,
        tool_name: str = None
    ) -> Optional[CacheHit]:
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
        if data := await self.get_from_redis(key):
            hit = CacheHit(layer=CacheLayer.REDIS, data=data, timestamp=datetime.utcnow())
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
            if data := await self.get_from_cloud_storage(symbol):
                return CacheHit(
                    layer=CacheLayer.CLOUD_STORAGE,
                    data=data,
                    timestamp=datetime.utcnow()
                )

        # L3: BigQuery (if symbol provided)
        if symbol:
            if data := await self.get_from_bigquery(symbol):
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
        1. L1: Redis (async)
        2. L2a: Firestore (async)
        3. L2b: Cloud Storage (async background task)

        Args:
            key: Cache key
            data: Data to cache
            symbol: Stock symbol (optional, for L2b)
            ttl: Time-to-live in seconds

        Returns:
            Number of layers written to
        """
        layers_written = 0

        if await self.set_in_redis(key, data, ttl):
            layers_written += 1

        if await self.set_in_firestore("mcp_tool_cache", key, data, ttl):
            layers_written += 1

        if symbol:
            asyncio.create_task(self.set_in_cloud_storage(symbol, data))
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
        for layer, is_available in status.items():
            symbol = "✓" if is_available else "✗"
            logger.info(f"  {symbol} {layer.name} ({layer.value})")


# Global instance
_cache_manager: Optional[GCPCacheManager] = None


async def get_cache_manager() -> GCPCacheManager:
    """Get or create global cache manager instance (initializes on first call)."""
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = GCPCacheManager()
        await _cache_manager.initialize()
    return _cache_manager
