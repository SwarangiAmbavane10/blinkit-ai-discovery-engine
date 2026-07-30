import csv
import os
from typing import List
from discovery_engine.models.canonical_review import CanonicalReview
from discovery_engine.cleaning.cleaner import ReviewCleaner
from discovery_engine.utils.logging import logger

class ReviewExporter:
    """Handles cleaning canonical reviews, removing content duplicates, and exporting to CSV."""

    @staticmethod
    def clean_and_export_csv(reviews: List[CanonicalReview], output_path: str) -> int:
        """
        Cleans the review text, applies deduplication by content hash, and exports to CSV.
        Returns the number of unique, cleaned reviews exported.
        """
        if not reviews:
            logger.info("No reviews provided for export.")
            # Create an empty CSV file with headers
            with open(output_path, mode='w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    "review_id", "source_type", "source_id", "original_text", 
                    "cleaned_text", "rating", "timestamp", "sentiment", "content_hash"
                ])
            return 0

        unique_reviews = {}
        duplicate_count = 0

        for rev in reviews:
            # 1. Clean the text using the full Phase 2 pipeline (stopwords, urls, emojis, normalize)
            cleaned = ReviewCleaner.clean_review(rev.text)
            rev.cleaned_text = cleaned

            # 2. Check for duplicate content hash
            if rev.content_hash in unique_reviews:
                duplicate_count += 1
                continue

            unique_reviews[rev.content_hash] = rev

        # Write to CSV
        try:
            # Ensure the directory exists
            dir_name = os.path.dirname(output_path)
            if dir_name:
                os.makedirs(dir_name, exist_ok=True)

            with open(output_path, mode='w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                # Write header
                writer.writerow([
                    "review_id", "source_type", "source_id", "original_text", 
                    "cleaned_text", "rating", "timestamp", "sentiment", "content_hash"
                ])

                for item in unique_reviews.values():
                    writer.writerow([
                        item.document_id,
                        item.source_type.value,
                        item.source_id,
                        item.text,
                        item.cleaned_text,
                        item.rating if item.rating is not None else "",
                        item.timestamp.isoformat(),
                        item.sentiment,
                        item.content_hash
                    ])

            logger.info(
                f"Exported {len(unique_reviews)} reviews to CSV ({output_path}). "
                f"Filtered out {duplicate_count} duplicates."
            )
            return len(unique_reviews)
        except Exception as e:
            logger.error(f"Failed to export cleaned reviews to CSV: {e}")
            raise e
