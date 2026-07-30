import os
import json
import uuid
from datetime import datetime
from typing import List, Dict, Any, Tuple
from discovery_engine.config.settings import settings
from discovery_engine.loaders.base_loader import BaseReviewLoader
from discovery_engine.models.raw_record import RawRecord
from discovery_engine.models.canonical_review import CanonicalReview
from discovery_engine.models.ingestion import IngestionRun
from discovery_engine.validation.validator import ReviewValidator
from discovery_engine.utils.logging import logger

class CollectionRunner:
    """Orchestrates loading reviews from multiple connectors, validating, and saving them."""

    def __init__(self, loaders: List[BaseReviewLoader]):
        self.loaders = loaders

    def run(self) -> Tuple[Dict[str, IngestionRun], List[CanonicalReview]]:
        """
        Executes ingestion for all loaders.
        Returns a tuple (runs_metadata_dict, list_of_canonical_reviews).
        """
        all_canonical_reviews = []
        runs_metadata = {}

        # Create output directories if they do not exist
        os.makedirs(settings.RAW_STORE_DIR, exist_ok=True)
        os.makedirs(settings.DEAD_LETTER_QUEUE_DIR, exist_ok=True)

        for loader in self.loaders:
            source = loader.source_type
            run_id = str(uuid.uuid4())
            started_at = datetime.utcnow()

            logger.info(f"Starting ingestion run for source={source.value}, run_id={run_id}")

            ingestion_run = IngestionRun(
                run_id=run_id,
                started_at=started_at,
                source_type=source.value,
                record_count=0,
                status="RUNNING"
            )

            try:
                # 1. Fetch raw data
                raw_records = loader.fetch_raw()
                ingestion_run.record_count = len(raw_records)

                if not raw_records:
                    logger.info(f"No records fetched for {source.value}.")
                    ingestion_run.status = "SUCCESS_EMPTY"
                    ingestion_run.completed_at = datetime.utcnow()
                    runs_metadata[source.value] = ingestion_run
                    self._save_run_manifest(ingestion_run)
                    continue

                # 2. Write raw payloads to storage for auditing/lineage
                self._save_raw_payloads(run_id, source.value, raw_records)

                # 3. Validate, redact PII, and normalize each record
                valid_count = 0
                invalid_count = 0

                for record in raw_records:
                    success, canonical, error_reason = ReviewValidator.validate_and_normalize(record, run_id)
                    if success and canonical:
                        all_canonical_reviews.append(canonical)
                        valid_count += 1
                    else:
                        # Write to DLQ
                        self._save_to_dlq(run_id, source.value, record, error_reason)
                        invalid_count += 1

                logger.info(
                    f"Completed validation for {source.value}: "
                    f"{valid_count} valid, {invalid_count} quarantined in DLQ"
                )

                if invalid_count == 0:
                    ingestion_run.status = "SUCCESS"
                elif valid_count > 0:
                    ingestion_run.status = "PARTIAL_SUCCESS"
                else:
                    ingestion_run.status = "FAILURE"
                    ingestion_run.error_summary = "All records failed validation check"

            except Exception as e:
                logger.error(f"Fatal error during ingestion for {source.value}: {e}")
                ingestion_run.status = "FAILURE"
                ingestion_run.error_summary = str(e)

            ingestion_run.completed_at = datetime.utcnow()
            runs_metadata[source.value] = ingestion_run
            self._save_run_manifest(ingestion_run)

        return runs_metadata, all_canonical_reviews

    def _save_raw_payloads(self, run_id: str, source: str, records: List[RawRecord]):
        """Persists raw records to JSON files in the raw store directory."""
        dir_path = os.path.join(settings.RAW_STORE_DIR, run_id, source)
        os.makedirs(dir_path, exist_ok=True)

        for rec in records:
            file_path = os.path.join(dir_path, f"{rec.source_id}.json")
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(rec.model_dump(mode="json"), f, indent=2, default=str)

    def _save_to_dlq(self, run_id: str, source: str, record: RawRecord, error_reason: str):
        """Persists failed records to the Dead Letter Queue directory with details."""
        dir_path = os.path.join(settings.DEAD_LETTER_QUEUE_DIR, source)
        os.makedirs(dir_path, exist_ok=True)

        file_path = os.path.join(dir_path, f"fail_{record.source_id}.json")
        data = {
            "run_id": run_id,
            "failed_at": datetime.utcnow().isoformat(),
            "error_reason": error_reason,
            "record": record.model_dump(mode="json")
        }
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)

    def _save_run_manifest(self, manifest: IngestionRun):
        """Saves run details to a central manifest log file."""
        manifest_path = os.path.join(settings.RAW_STORE_DIR, "manifests.jsonl")
        with open(manifest_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(manifest.model_dump(mode="json"), default=str) + "\n")
