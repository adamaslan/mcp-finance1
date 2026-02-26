"""Firebase Firestore cache layer for industry performance data.

Stores and retrieves industry performance cache with atomic operations.
"""

import logging
from typing import Optional
from datetime import datetime
import os

logger = logging.getLogger(__name__)


class FirebaseCacheError(Exception):
    """Raised when Firebase operations fail."""
    pass


class FirebaseCache:
    """Firestore-based cache for industry performance data."""

    COLLECTION_NAME = "industry_cache"

    def __init__(self, project_id: Optional[str] = None):
        """Initialize Firebase cache.

        Args:
            project_id: GCP project ID. If None, uses GCP_PROJECT_ID env var.

        Raises:
            FirebaseCacheError: If Firebase initialization fails.
        """
        try:
            import firebase_admin
            from firebase_admin import credentials, firestore
            from google.cloud import firestore as gcloud_firestore

            self._firestore_module = firestore
            self._gcloud_firestore = gcloud_firestore

        except ImportError as e:
            raise FirebaseCacheError(
                "Firebase Admin SDK not installed. "
                "Install with: mamba install -c conda-forge firebase-admin"
            ) from e

        # Initialize Firebase app if not already initialized
        try:
            firebase_admin.get_app()
            logger.info("Using existing Firebase app")
        except ValueError:
            # No app exists, initialize new one
            project_id = project_id or os.getenv("GCP_PROJECT_ID")
            if not project_id:
                raise FirebaseCacheError(
                    "GCP_PROJECT_ID environment variable not set"
                )

            # Use Application Default Credentials (works in Cloud Run)
            cred = credentials.ApplicationDefault()
            firebase_admin.initialize_app(cred, {
                "projectId": project_id,
            })
            logger.info("Initialized Firebase app for project: %s", project_id)

        self._db = self._firestore_module.client()
        logger.info("Firebase cache initialized")

    def write(self, industry: str, performance_data: dict) -> None:
        """Write industry performance to cache.

        Args:
            industry: Industry name (used as document ID).
            performance_data: Performance dict from PerformanceCalculator.

        Raises:
            FirebaseCacheError: If write fails.
        """
        try:
            doc_ref = self._db.collection(self.COLLECTION_NAME).document(industry)
            doc_ref.set(performance_data)
            logger.info("Cached performance data for %s", industry)

        except Exception as e:
            raise FirebaseCacheError(
                f"Failed to write {industry} to Firestore: {e}"
            ) from e

    def read(self, industry: str) -> Optional[dict]:
        """Read industry performance from cache.

        Args:
            industry: Industry name.

        Returns:
            Performance dict or None if not cached.

        Raises:
            FirebaseCacheError: If read fails.
        """
        try:
            doc_ref = self._db.collection(self.COLLECTION_NAME).document(industry)
            doc = doc_ref.get()

            if not doc.exists:
                logger.debug("No cached data for %s", industry)
                return None

            data = doc.to_dict()
            logger.debug("Retrieved cached data for %s", industry)
            return data

        except Exception as e:
            raise FirebaseCacheError(
                f"Failed to read {industry} from Firestore: {e}"
            ) from e

    def read_all(self) -> list[dict]:
        """Read all cached industry performances.

        Returns:
            List of all performance dicts in cache.

        Raises:
            FirebaseCacheError: If read fails.
        """
        try:
            docs = self._db.collection(self.COLLECTION_NAME).stream()
            results = []

            for doc in docs:
                data = doc.to_dict()
                if data:
                    results.append(data)

            logger.info("Retrieved %d cached industries", len(results))
            return results

        except Exception as e:
            raise FirebaseCacheError(
                f"Failed to read all from Firestore: {e}"
            ) from e

    def read_batch(self, industries: list[str]) -> dict[str, dict]:
        """Read multiple industry performances in a single Firestore query.

        Uses Firestore 'in' query to batch-read up to 30 documents at once
        (Firestore 'in' limit is 30 per query). More efficient than N
        individual reads when fetching multiple symbols.

        Args:
            industries: List of industry names to read.

        Returns:
            Dict mapping industry name -> performance dict.
            Missing industries are omitted from the result.

        Raises:
            FirebaseCacheError: If read fails.
        """
        if not industries:
            return {}

        try:
            results: dict[str, dict] = {}
            batch_limit = 30  # Firestore 'in' query limit

            for i in range(0, len(industries), batch_limit):
                batch = industries[i:i + batch_limit]
                docs = (
                    self._db.collection(self.COLLECTION_NAME)
                    .where("industry", "in", batch)
                    .stream()
                )
                for doc in docs:
                    data = doc.to_dict()
                    if data:
                        industry_name = data.get("industry", doc.id)
                        results[industry_name] = data

            # Also check by document ID for entries without an 'industry' field
            missing = [ind for ind in industries if ind not in results]
            for ind in missing:
                doc_ref = self._db.collection(self.COLLECTION_NAME).document(ind)
                doc = doc_ref.get()
                if doc.exists:
                    data = doc.to_dict()
                    if data:
                        results[ind] = data

            logger.info("Batch read: %d/%d industries found", len(results), len(industries))
            return results

        except Exception as e:
            raise FirebaseCacheError(
                f"Failed to batch-read from Firestore: {e}"
            ) from e

    def write_batch(self, performances: list[dict]) -> int:
        """Write multiple industry performances in batches.

        Firestore batches support max 500 operations per batch.

        Args:
            performances: List of performance dicts.

        Returns:
            Number of records written.

        Raises:
            FirebaseCacheError: If batch write fails.
        """
        if not performances:
            logger.warning("No performances to write")
            return 0

        try:
            batch_size = 500
            total_written = 0

            for i in range(0, len(performances), batch_size):
                batch_data = performances[i:i + batch_size]
                batch = self._db.batch()

                for perf in batch_data:
                    industry = perf.get("industry")
                    if not industry:
                        logger.warning("Skipping performance with no industry key")
                        continue

                    doc_ref = self._db.collection(self.COLLECTION_NAME).document(industry)
                    batch.set(doc_ref, perf)

                batch.commit()
                total_written += len(batch_data)
                logger.info("Batch %d: wrote %d industries", i // batch_size + 1, len(batch_data))

            logger.info("Total industries written: %d", total_written)
            return total_written

        except Exception as e:
            raise FirebaseCacheError(
                f"Failed to write batch to Firestore: {e}"
            ) from e

    def delete(self, industry: str) -> None:
        """Delete industry from cache.

        Args:
            industry: Industry name.

        Raises:
            FirebaseCacheError: If delete fails.
        """
        try:
            doc_ref = self._db.collection(self.COLLECTION_NAME).document(industry)
            doc_ref.delete()
            logger.info("Deleted cached data for %s", industry)

        except Exception as e:
            raise FirebaseCacheError(
                f"Failed to delete {industry} from Firestore: {e}"
            ) from e

    def delete_all(self) -> int:
        """Delete all cached industry data.

        WARNING: This is destructive. Use with caution.

        Returns:
            Number of documents deleted.

        Raises:
            FirebaseCacheError: If delete fails.
        """
        try:
            docs = self._db.collection(self.COLLECTION_NAME).stream()
            count = 0

            for doc in docs:
                doc.reference.delete()
                count += 1

            logger.warning("Deleted all %d cached industries", count)
            return count

        except Exception as e:
            raise FirebaseCacheError(
                f"Failed to delete all from Firestore: {e}"
            ) from e

    def get_cache_age(self, industry: str) -> Optional[int]:
        """Get age of cached data in seconds.

        Args:
            industry: Industry name.

        Returns:
            Age in seconds or None if not cached.
        """
        data = self.read(industry)
        if not data:
            return None

        updated_str = data.get("updated")
        if not updated_str:
            return None

        try:
            updated = datetime.fromisoformat(updated_str)
            age = (datetime.utcnow() - updated).total_seconds()
            return int(age)
        except (ValueError, TypeError) as e:
            logger.warning("Invalid updated timestamp for %s: %s", industry, e)
            return None

    def is_stale(self, industry: str, max_age_seconds: int = 86400) -> bool:
        """Check if cached data is stale.

        Args:
            industry: Industry name.
            max_age_seconds: Max age before considering stale (default: 24 hours).

        Returns:
            True if stale or not cached, False if fresh.
        """
        age = self.get_cache_age(industry)
        if age is None:
            return True  # Not cached = stale

        return age > max_age_seconds

    def count_cached(self) -> int:
        """Count total cached industries.

        Returns:
            Number of documents in cache.
        """
        try:
            docs = self._db.collection(self.COLLECTION_NAME).stream()
            count = sum(1 for _ in docs)
            return count
        except Exception as e:
            logger.error("Failed to count cached industries: %s", e)
            return 0
