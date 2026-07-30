import csv
import os
import re
from datetime import datetime
from typing import List, Dict, Any, Optional
from discovery_engine.config.constants import SourceType
from discovery_engine.loaders.base_loader import BaseReviewLoader
from discovery_engine.models.raw_record import RawRecord
from discovery_engine.utils.logging import logger

class CSVReviewLoader(BaseReviewLoader):
    """Loader to ingest feedback/reviews from CSV files (e.g. Google Forms exports)."""

    def __init__(self, file_path: str, column_mapping: Optional[Dict[str, str]] = None):
        """
        Args:
            file_path: Path to the CSV file.
            column_mapping: Optional dictionary mapping csv column names to canonical fields
                            ('source_id', 'text', 'rating', 'timestamp').
        """
        self.file_path = file_path
        self.custom_mapping = column_mapping or {}

    @property
    def source_type(self) -> SourceType:
        return SourceType.GOOGLE_FORM

    def _detect_mappings(self, headers: List[str]) -> Dict[str, str]:
        """Detect column mappings based on common header names."""
        mapping = {}
        headers_lower = [h.lower().strip() for h in headers]

        # Helper to check if any keyword matches a header
        def find_match(keywords: List[str], exclude_keywords: Optional[List[str]] = None) -> Optional[str]:
            excludes = exclude_keywords or []
            for idx, h in enumerate(headers_lower):
                # Skip if any exclusion keyword is found in the header
                if any(ex in h for ex in excludes):
                    continue
                for kw in keywords:
                    # Match if the keyword matches exactly, or is in the header
                    # (using word boundaries to prevent false positives like 'id' matching 'friday')
                    if kw == h or (kw in h and len(kw) > 2) or re.search(r'\b' + re.escape(kw) + r'\b', h):
                        return headers[idx]
            return None

        # 1. Text column detection
        text_col = find_match(
            ["text", "review", "feedback", "comment", "body", "response", "answer", "opinion"],
            exclude_keywords=["id", "uuid", "ref", "key", "number"]
        )
        if text_col:
            mapping["text"] = text_col
        elif len(headers) > 1:
            mapping["text"] = headers[1]

        # 2. Source ID detection
        id_col = find_match(["id", "uuid", "key", "ref", "reference", "row"])
        if id_col:
            mapping["source_id"] = id_col

        # 3. Rating detection
        rating_col = find_match(["rating", "stars", "score", "star"])
        if rating_col:
            mapping["rating"] = rating_col

        # 4. Timestamp detection
        time_col = find_match(["timestamp", "date", "time", "created", "submitted"])
        if time_col:
            mapping["timestamp"] = time_col

        # Apply custom overrides
        for k, v in self.custom_mapping.items():
            if v in headers:
                mapping[k] = v

        logger.debug(f"Detected CSV column mapping: {mapping}")
        return mapping

    def fetch_raw(self, **kwargs) -> List[RawRecord]:
        """Reads the CSV file and constructs RawRecords."""
        file_path = kwargs.get("file_path", self.file_path)
        if not file_path or not os.path.exists(file_path):
            logger.warning(f"CSV file not found at path: {file_path}")
            return []

        records = []
        try:
            with open(file_path, mode='r', encoding='utf-8-sig') as f:
                reader = csv.reader(f)
                headers = next(reader, None)
                if not headers:
                    logger.warning(f"CSV file is empty: {file_path}")
                    return []

                mapping = self._detect_mappings(headers)
                text_col = mapping.get("text")
                id_col = mapping.get("source_id")
                rating_col = mapping.get("rating")
                time_col = mapping.get("timestamp")

                # Map column header strings to their index
                text_idx = headers.index(text_col) if text_col in headers else None
                id_idx = headers.index(id_col) if id_col in headers else None
                rating_idx = headers.index(rating_col) if rating_col in headers else None
                time_idx = headers.index(time_col) if time_col in headers else None

                for index, row in enumerate(reader):
                    # Skip empty rows
                    if not row or not any(row):
                        continue

                    # Extract values
                    row_text = row[text_idx] if text_idx is not None and text_idx < len(row) else ""
                    row_id = row[id_idx] if id_idx is not None and id_idx < len(row) else f"row_{index + 1}"
                    row_rating = row[rating_idx] if rating_idx is not None and rating_idx < len(row) else None
                    row_time = row[time_idx] if time_idx is not None and time_idx < len(row) else None

                    # Gather other fields for the payload metadata
                    metadata = {}
                    for col_idx, col_name in enumerate(headers):
                        if col_idx < len(row) and col_name not in [text_col, id_col, rating_col, time_col]:
                            metadata[col_name] = row[col_idx]

                    payload = {
                        "text": row_text,
                        "rating": row_rating,
                        "timestamp": row_time,
                        "metadata": metadata
                    }

                    records.append(
                        RawRecord(
                            source_type=self.source_type,
                            source_id=str(row_id),
                            payload=payload,
                            fetched_at=datetime.utcnow()
                        )
                    )

            logger.info(f"Loaded {len(records)} raw records from CSV: {file_path}")
        except Exception as e:
            logger.error(f"Error reading CSV file {file_path}: {e}")
            raise e

        return records
