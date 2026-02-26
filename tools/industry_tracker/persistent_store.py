"""Persistent Firestore storage for ETF historical price data.

Stores full price history permanently in Firestore so that:
1. Initial fetch (50 ETFs × full history) happens once
2. Daily updates append only new data (delta fetch)
3. Performance calculations run from stored data with zero API calls
4. Data survives container restarts, cold starts, and redeployments

Firestore structure:
    etf_history/{symbol}/
        metadata: {last_updated, first_date, last_date, total_days, source}
        prices: [{date, adjusted_close, volume}, ...]  (embedded array)

    For ETFs with >10 years of data (>2520 rows), prices are chunked
    into yearly sub-documents to stay under Firestore's 1MB doc limit:
    etf_history/{symbol}/years/{YYYY} -> [{date, adjusted_close, volume}, ...]
"""

import logging
from datetime import datetime, timezone
from typing import Optional

import pandas as pd

logger = logging.getLogger(__name__)

COLLECTION_NAME = "etf_history"
CHUNK_THRESHOLD = 2000  # Switch to yearly chunks above this many rows
BATCH_LIMIT = 450  # Firestore batch write limit


class PersistentStoreError(Exception):
    """Raised when persistent storage operations fail."""
    pass


class PersistentETFStore:
    """Permanent Firestore storage for ETF price history.

    Designed for append-only updates: fetch full history once, then
    only add new trading days on subsequent runs.
    """

    def __init__(self, project_id: Optional[str] = None) -> None:
        """Initialize persistent store.

        Args:
            project_id: GCP project ID. Falls back to GCP_PROJECT_ID env var.

        Raises:
            PersistentStoreError: If Firestore initialization fails.
        """
        try:
            import os
            from google.cloud import firestore

            project = project_id or os.getenv("GCP_PROJECT_ID", "ttb-lang1")
            self._db = firestore.Client(project=project)
            logger.info("PersistentETFStore connected to project: %s", project)
        except Exception as e:
            raise PersistentStoreError(f"Failed to connect to Firestore: {e}") from e

    def store_full_history(
        self,
        symbol: str,
        df: pd.DataFrame,
        source: str = "alpha_vantage",
    ) -> int:
        """Store full price history for an ETF symbol.

        Writes the entire DataFrame to Firestore. For large datasets
        (>2000 rows), data is chunked into yearly sub-documents.

        Args:
            symbol: ETF ticker symbol (e.g., 'IGV').
            df: DataFrame with 'adjusted_close' and 'volume' columns,
                indexed by date (newest first).
            source: Data source identifier for provenance tracking.

        Returns:
            Number of price records stored.

        Raises:
            PersistentStoreError: If storage fails.
        """
        symbol = symbol.upper()

        if df.empty:
            logger.warning("Empty DataFrame for %s, nothing to store", symbol)
            return 0

        try:
            records = self._df_to_records(df)
            now = datetime.now(tz=timezone.utc).isoformat()

            dates = [r["date"] for r in records]
            first_date = min(dates)
            last_date = max(dates)

            doc_ref = self._db.collection(COLLECTION_NAME).document(symbol)

            if len(records) <= CHUNK_THRESHOLD:
                # Small enough to fit in one document
                doc_ref.set({
                    "symbol": symbol,
                    "source": source,
                    "last_updated": now,
                    "first_date": first_date,
                    "last_date": last_date,
                    "total_days": len(records),
                    "storage_mode": "embedded",
                    "prices": records,
                })
                logger.info(
                    "Stored %d days for %s (embedded, %s to %s)",
                    len(records), symbol, first_date, last_date,
                )
            else:
                # Chunk into yearly sub-documents
                doc_ref.set({
                    "symbol": symbol,
                    "source": source,
                    "last_updated": now,
                    "first_date": first_date,
                    "last_date": last_date,
                    "total_days": len(records),
                    "storage_mode": "chunked",
                })

                yearly = self._chunk_by_year(records)
                batch = self._db.batch()
                ops = 0

                for year_str, year_records in yearly.items():
                    year_ref = doc_ref.collection("years").document(year_str)
                    batch.set(year_ref, {
                        "year": year_str,
                        "count": len(year_records),
                        "prices": year_records,
                    })
                    ops += 1

                    if ops >= BATCH_LIMIT:
                        batch.commit()
                        batch = self._db.batch()
                        ops = 0

                if ops > 0:
                    batch.commit()

                logger.info(
                    "Stored %d days for %s (chunked into %d years, %s to %s)",
                    len(records), symbol, len(yearly), first_date, last_date,
                )

            return len(records)

        except Exception as e:
            raise PersistentStoreError(
                f"Failed to store history for {symbol}: {e}"
            ) from e

    def load_history(self, symbol: str) -> Optional[pd.DataFrame]:
        """Load full price history from Firestore into a DataFrame.

        This is the primary read path — returns stored data without
        any API calls.

        Args:
            symbol: ETF ticker symbol.

        Returns:
            DataFrame with date index, adjusted_close, volume columns,
            sorted newest-first. None if no data stored.

        Raises:
            PersistentStoreError: If read fails.
        """
        symbol = symbol.upper()

        try:
            doc_ref = self._db.collection(COLLECTION_NAME).document(symbol)
            doc = doc_ref.get()

            if not doc.exists:
                return None

            data = doc.to_dict()
            storage_mode = data.get("storage_mode", "embedded")

            if storage_mode == "embedded":
                records = data.get("prices", [])
            else:
                # Chunked: read all year sub-documents
                records = []
                years = doc_ref.collection("years").stream()
                for year_doc in years:
                    year_data = year_doc.to_dict()
                    records.extend(year_data.get("prices", []))

            if not records:
                return None

            df = pd.DataFrame(records)
            df["date"] = pd.to_datetime(df["date"])
            df.set_index("date", inplace=True)
            df.sort_index(ascending=False, inplace=True)

            logger.info(
                "Loaded %d days for %s from Firestore (%s to %s)",
                len(df), symbol,
                df.index[-1].strftime("%Y-%m-%d"),
                df.index[0].strftime("%Y-%m-%d"),
            )
            return df

        except Exception as e:
            raise PersistentStoreError(
                f"Failed to load history for {symbol}: {e}"
            ) from e

    def get_metadata(self, symbol: str) -> Optional[dict]:
        """Get metadata for a stored ETF (without loading prices).

        Args:
            symbol: ETF ticker symbol.

        Returns:
            Metadata dict or None if not stored.
        """
        symbol = symbol.upper()

        try:
            doc_ref = self._db.collection(COLLECTION_NAME).document(symbol)
            doc = doc_ref.get()

            if not doc.exists:
                return None

            data = doc.to_dict()
            # Return metadata only (exclude the prices array)
            return {
                "symbol": data.get("symbol"),
                "source": data.get("source"),
                "last_updated": data.get("last_updated"),
                "first_date": data.get("first_date"),
                "last_date": data.get("last_date"),
                "total_days": data.get("total_days"),
                "storage_mode": data.get("storage_mode"),
            }

        except Exception as e:
            logger.error("Failed to get metadata for %s: %s", symbol, e)
            return None

    def get_all_metadata(self) -> list[dict]:
        """Get metadata for all stored ETFs.

        Returns:
            List of metadata dicts (no price data).
        """
        try:
            docs = self._db.collection(COLLECTION_NAME).stream()
            results = []
            for doc in docs:
                data = doc.to_dict()
                results.append({
                    "symbol": data.get("symbol", doc.id),
                    "last_updated": data.get("last_updated"),
                    "last_date": data.get("last_date"),
                    "total_days": data.get("total_days"),
                    "storage_mode": data.get("storage_mode"),
                })
            return results
        except Exception as e:
            logger.error("Failed to get all metadata: %s", e)
            return []

    def has_history(self, symbol: str) -> bool:
        """Check if an ETF has stored history (metadata-only check).

        Args:
            symbol: ETF ticker symbol.

        Returns:
            True if history exists.
        """
        return self.get_metadata(symbol.upper()) is not None

    def delete_history(self, symbol: str) -> None:
        """Delete all stored history for an ETF.

        Args:
            symbol: ETF ticker symbol.
        """
        symbol = symbol.upper()
        try:
            doc_ref = self._db.collection(COLLECTION_NAME).document(symbol)

            # Delete year sub-documents if chunked
            years = doc_ref.collection("years").stream()
            for year_doc in years:
                year_doc.reference.delete()

            doc_ref.delete()
            logger.info("Deleted history for %s", symbol)
        except Exception as e:
            logger.error("Failed to delete history for %s: %s", symbol, e)

    @staticmethod
    def _df_to_records(df: pd.DataFrame) -> list[dict]:
        """Convert DataFrame to list of Firestore-friendly dicts.

        Args:
            df: DataFrame with adjusted_close, volume, indexed by date.

        Returns:
            List of {"date": str, "adjusted_close": float, "volume": int}.
        """
        records = []
        for idx, row in df.iterrows():
            date_str = idx.strftime("%Y-%m-%d") if hasattr(idx, "strftime") else str(idx)
            records.append({
                "date": date_str,
                "adjusted_close": float(row.get("adjusted_close", 0)),
                "volume": int(row.get("volume", 0)),
            })
        return records

    @staticmethod
    def _chunk_by_year(records: list[dict]) -> dict[str, list[dict]]:
        """Group records by year for chunked storage.

        Args:
            records: List of price record dicts with 'date' field.

        Returns:
            Dict mapping year string -> list of records.
        """
        yearly: dict[str, list[dict]] = {}
        for record in records:
            year = record["date"][:4]
            if year not in yearly:
                yearly[year] = []
            yearly[year].append(record)
        return yearly
