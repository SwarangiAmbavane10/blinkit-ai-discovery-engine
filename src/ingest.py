import os
import re
import json
import hashlib
import logging
from typing import List, Dict, Any

logger = logging.getLogger("PipelineLogger")

def clean_text(text: str) -> str:
    """Performs standard text cleaning: HTML removal, emoji/special char stripping, whitespace normalization."""
    if not text:
        return ""
    # Remove HTML tags
    text = re.sub(r"<[^>]*>", "", text)
    # Remove URL links
    text = re.sub(r"https?://\S+|www\.\S+", "", text)
    # Strip emojis and non-ascii characters
    text = text.encode("ascii", "ignore").decode("ascii")
    # Convert to lowercase
    text = text.lower()
    # Normalize whitespaces
    text = re.sub(r"\s+", " ", text).strip()
    return text

def ingest_raw_streams(raw_streams: List[Dict[str, Any]], output_path: str = "data/raw_reviews_dump.json") -> List[Dict[str, Any]]:
    """
    Aggregates review streams, normalizes them, filters duplicates by text hash,
    and writes the consolidated dataset to a local JSON file.
    """
    logger.info("Initializing Ingestion Layer...")
    cleaned_reviews = []
    unique_hashes = set()
    duplicate_count = 0

    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    for item in raw_streams:
        raw_text = item.get("text", "").strip()
        if not raw_text:
            continue

        # Text cleaning and normalization
        cleaned_body = clean_text(raw_text)

        # Skip extremely short texts
        if len(cleaned_body.split()) < 3:
            continue

        # Compute content hash for deduplication
        content_hash = hashlib.md5(cleaned_body.encode("utf-8")).hexdigest()

        if content_hash in unique_hashes:
            duplicate_count += 1
            continue

        unique_hashes.add(content_hash)
        
        # Populate normalized record attributes
        cleaned_reviews.append({
            "review_id": item.get("id"),
            "original_text": raw_text,
            "cleaned_text": cleaned_body,
            "rating": item.get("rating", 0.0),
            "timestamp": item.get("timestamp"),
            "source": item.get("source"),
            "review_url": item.get("review_url", ""),
            "content_hash": content_hash
        })

    logger.info(f"Ingestion completed: Processed {len(raw_streams)} total items. "
                f"Filtered {duplicate_count} duplicates. Exported {len(cleaned_reviews)} unique reviews.")

    # Write cleaned dataset to file
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(cleaned_reviews, f, indent=2)
        logger.info(f"Saved aggregated reviews to local dump: {output_path}")
    except Exception as e:
        logger.error(f"Failed to write ingested dump: {e}")
        raise e

    return cleaned_reviews

if __name__ == "__main__":
    # Test script standalone with dummy data
    logging.basicConfig(level=logging.INFO)
    test_data = [
        {"id": "t1", "text": "<b>Great app!</b> I love using it everyday.", "rating": 5.0, "timestamp": "2026-08-04", "source": "test"},
        {"id": "t2", "text": "Great app! I love using it everyday.", "rating": 5.0, "timestamp": "2026-08-04", "source": "test"}, # Duplicate
    ]
    ingest_raw_streams(test_data)
