import csv
import math
import os
import re
from datetime import datetime
from typing import List, Dict, Any, Tuple
from discovery_engine.cleaning.cleaner import ReviewCleaner
from discovery_engine.utils.logging import logger

class RetrievalEngine:
    """Retrieval Engine that processes cleaned reviews and scores their relevance to a search query."""

    def __init__(self):
        self.corpus: List[Dict[str, Any]] = []

    def load_corpus(self, csv_path: str):
        """Loads cleaned reviews from the exported CSV file."""
        if not os.path.exists(csv_path):
            logger.error(f"Cannot load corpus; file does not exist: {csv_path}")
            self.corpus = []
            return

        self.corpus = []
        import hashlib
        try:
            with open(csv_path, mode='r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    original_text = row.get("original_text") or row.get("review_text", "")
                    cleaned_text = row.get("cleaned_text", "")
                    
                    review_id = row.get("review_id")
                    if not review_id and original_text:
                        review_id = hashlib.md5(original_text.encode("utf-8")).hexdigest()[:8]
                    elif not review_id:
                        review_id = ""
                        
                    source_type = row.get("source_type") or row.get("source", "")
                    if source_type:
                        source_type_lower = source_type.lower().replace(" ", "_")
                        if source_type_lower == "google_forms":
                            source_type = "google_form"
                        else:
                            source_type = source_type_lower
                    
                    timestamp = row.get("timestamp") or row.get("date", "")
                    
                    sentiment = row.get("sentiment")
                    rating = row.get("rating", "")
                    if not sentiment and rating:
                        try:
                            val = float(rating)
                            if val >= 4:
                                sentiment = "POSITIVE"
                            elif val <= 2:
                                sentiment = "NEGATIVE"
                            else:
                                sentiment = "NEUTRAL"
                        except ValueError:
                            sentiment = "NEUTRAL"
                    elif not sentiment:
                        sentiment = "NEUTRAL"
                        
                    # Build generic fallback URL if review_url is missing
                    review_url = row.get("review_url") or row.get("url", "")
                    if not review_url:
                        if source_type == "play_store":
                            review_url = "https://play.google.com/store/apps/details?id=com.grofers.customerapp"
                        elif source_type == "app_store":
                            review_url = "https://apps.apple.com/in/app/blinkit-groceries-more/id1393452285"
                        elif source_type == "reddit":
                            review_url = "https://www.reddit.com/r/india/"
                        else:
                            review_url = "https://play.google.com/store/apps/details?id=com.grofers.customerapp"

                    self.corpus.append({
                        "review_id": review_id,
                        "source_type": source_type,
                        "source_id": row.get("source_id") or review_id,
                        "original_text": original_text,
                        "cleaned_text": cleaned_text,
                        "rating": rating,
                        "timestamp": timestamp,
                        "sentiment": sentiment,
                        "content_hash": row.get("content_hash") or review_id,
                        "review_url": review_url
                    })
            logger.info(f"Loaded {len(self.corpus)} reviews into Retrieval Engine corpus.")
        except Exception as e:
            logger.error(f"Error loading corpus from CSV {csv_path}: {e}")
            raise e

    def _compute_tfidf_relevance(self, query_terms: List[str]) -> List[Tuple[Dict[str, Any], float]]:
        """
        Calculates simple TF-IDF weights for each review based on query terms.
        Returns list of (review, score) tuples.
        """
        if not self.corpus or not query_terms:
            return []

        # 1. Calculate document frequency (DF) for each query term
        num_docs = len(self.corpus)
        df = {}
        for term in query_terms:
            df[term] = sum(1 for doc in self.corpus if term in doc["cleaned_text"].split())

        # 2. Calculate Inverse Document Frequency (IDF)
        idf = {}
        for term, doc_freq in df.items():
            # Standard smooth IDF formula
            idf[term] = math.log(1 + (num_docs / (doc_freq + 1)))

        scored_docs = []
        for doc in self.corpus:
            words = doc["cleaned_text"].split()
            if not words:
                continue

            score = 0.0
            # Sum TF-IDF for matching query terms
            for term in query_terms:
                tf = words.count(term)
                if tf > 0:
                    # Score contribution = TF * IDF
                    score += tf * idf[term]

            if score > 0.0:
                scored_docs.append((doc, score))

        # Sort by score descending
        scored_docs.sort(key=lambda x: x[1], reverse=True)
        return scored_docs

    def retrieve(self, query: str, top_k: int = 20) -> List[Dict[str, Any]]:
        """
        Processes query, computes term relevance, and returns the top_k matching reviews
        with source, date, sentiment, and ID metadata.
        """
        # Normalize and clean query words
        query_cleaned = ReviewCleaner.clean_review(query)
        query_terms = list(set(query_cleaned.split()))

        # Add synonyms or semantic expansion words for exploration barriers if search terms are sparse
        expansion_terms = ["explore", "category", "categories", "barrier", "trial", "discover", "trust", "freshness", "quality", "reorder", "repeat"]
        query_terms.extend([term for term in expansion_terms if term not in query_terms])
        query_terms = list(set(query_terms))

        logger.debug(f"Retrieving using query terms: {query_terms}")

        scored_results = self._compute_tfidf_relevance(query_terms)

        # Fallback: if no tfidf match, return by keyword occurrence or recent reviews
        if not scored_results:
            logger.info("No text matches found using TF-IDF. Returning top recent reviews as fallback.")
            # Sort by date descending
            sorted_by_date = sorted(self.corpus, key=lambda x: x["timestamp"], reverse=True)
            return sorted_by_date[:top_k]

        results = []
        for doc, score in scored_results[:top_k]:
            results.append({
                "review_id": doc["review_id"],
                "source_type": doc["source_type"],
                "source_id": doc["source_id"],
                "original_text": doc["original_text"],
                "cleaned_text": doc["cleaned_text"],
                "rating": doc["rating"],
                "timestamp": doc["timestamp"],
                "sentiment": doc["sentiment"],
                "relevance_score": round(score, 4),
                "review_url": doc.get("review_url", "")
            })

        logger.info(f"Retrieved {len(results)} matching records for query: '{query}'")
        return results
from typing import Tuple # Ensure imports inside this file are clean
