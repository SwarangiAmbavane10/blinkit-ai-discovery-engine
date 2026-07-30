import os
import sys
import json
from datetime import datetime

# Dynamically add the backend/src directory to sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_SRC = os.path.join(BASE_DIR, "backend", "src")
sys.path.insert(0, BACKEND_SRC)

from discovery_engine.config.settings import settings
from discovery_engine.loaders.play_store_loader import PlayStoreReviewLoader
from discovery_engine.loaders.app_store_loader import AppStoreReviewLoader
from discovery_engine.loaders.reddit_loader import RedditReviewLoader
from discovery_engine.loaders.csv_loader import CSVReviewLoader
from discovery_engine.loaders.runner import CollectionRunner
from discovery_engine.cleaning.exporter import ReviewExporter
from discovery_engine.retrieval.engine import RetrievalEngine
from discovery_engine.llm.prompt_builder import PromptBuilder
from discovery_engine.llm.client import GeminiClient
from discovery_engine.utils.logging import logger, setup_logging

def create_sample_csv(csv_path: str):
    """Creates a sample CSV of Google Form feedback to simulate the CSV loader."""
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)
    
    headers = ["Timestamp", "Response ID", "Feedback Text", "Rating (1-5)", "Customer City"]
    rows = [
        ["2026-07-28T09:00:00Z", "form_001", "I really love Blinkit's speed, but I only use the app to buy milk and eggs. I don't feel motivated to try wellness products because they are expensive.", "4", "Delhi"],
        ["2026-07-27T10:15:00Z", "form_002", "I tried buying fresh paneer last week, but the app sent me one that was close to expiry. The trust isn't there, so I avoid other fresh categories now.", "2", "Bangalore"],
        ["2026-07-26T14:22:00Z", "form_003", "The search function is annoying. If I search for organic tea, it displays standard tea. Very frustrating to discover premium items.", "2", "Mumbai"],
        ["2026-07-25T16:30:00Z", "form_004", "I always check out in 15 seconds. It is a convenience tool. I don't use it for browsing new items, I use Zepto or physical stores for exploring snacks.", "3", "Gurgaon"]
    ]
    
    import csv
    with open(csv_path, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(rows)
    logger.info(f"Created sample feedback CSV at {csv_path}")

def main():
    setup_logging()
    logger.info("Starting Blinkit AI Discovery Engine pipeline...")

    # Define paths
    sample_csv_path = os.path.join(BASE_DIR, "backend", "data", "google_form_responses.csv")
    cleaned_csv_path = os.path.join(BASE_DIR, settings.CLEANED_DATA_PATH)
    discovery_path = os.path.join(BASE_DIR, "blinkit_discovery_reviews.csv")
    root_clean_path = os.path.join(BASE_DIR, "blinkit_reviews_clean.csv")
    if os.path.exists(discovery_path):
        cleaned_csv_path = discovery_path
    elif os.path.exists(root_clean_path):
        cleaned_csv_path = root_clean_path
    analysis_report_path = os.path.join(BASE_DIR, "analysis_report.json")

    # Update settings config paths to base dir absolute paths
    settings.RAW_STORE_DIR = os.path.join(BASE_DIR, "backend", "data", "raw")
    settings.DEAD_LETTER_QUEUE_DIR = os.path.join(BASE_DIR, "backend", "data", "dlq")

    # 1. Ensure sample CSV exists for Google Form loader
    if not os.path.exists(sample_csv_path):
        create_sample_csv(sample_csv_path)

    # 2. Initialize loaders for Phase 1
    loaders = [
        PlayStoreReviewLoader(),
        AppStoreReviewLoader(),
        RedditReviewLoader(),
        CSVReviewLoader(file_path=sample_csv_path)
    ]

    # 3. Ingest, Validate & Normalize (Phase 1)
    runner = CollectionRunner(loaders)
    runs_metadata, canonical_reviews = runner.run()

    # 4. Clean, Deduplicate & Export (Phase 2)
    logger.info("Running Review Cleaning & Export pipeline (Phase 2)...")
    unique_count = ReviewExporter.clean_and_export_csv(canonical_reviews, cleaned_csv_path)
    logger.info(f"Phase 2 complete. {unique_count} canonical reviews written to {cleaned_csv_path}")

    # 5. Retrieve top 20 relevant reviews (Phase 3)
    logger.info("Initializing Retrieval Engine (Phase 3)...")
    retriever = RetrievalEngine()
    retriever.load_corpus(cleaned_csv_path)
    
    question = "Why don't users explore categories?"
    top_reviews = retriever.retrieve(query=question, top_k=20)
    logger.info(f"Retrieved {len(top_reviews)} reviews for query: '{question}'")

    # Print top retrieved review titles/excerpts
    for idx, r in enumerate(top_reviews[:3]):
        logger.info(f"Top Match #{idx+1}: [{r['source_type']}] ID={r['review_id']} score={r['relevance_score']}: \"{r['original_text'][:100]}...\"")

    # 6. Build Prompt (Phase 4)
    business_goal = "Increase the percentage of Monthly Active Customers (MAC) who purchase from at least one new category every month."
    logger.info("Building LLM prompt (Phase 4)...")
    prompt = PromptBuilder.build_synthesis_prompt(
        business_goal=business_goal,
        question=question,
        reviews=top_reviews
    )

    # 7. Call Gemini & generate report (Phase 5)
    logger.info("Invoking Gemini Client for insight synthesis (Phase 5)...")
    client = GeminiClient()
    analysis_result = client.generate_content(prompt, json_mode=True)

    # 8. Output results
    print("\n" + "="*50)
    print("PHASE 5 ANALYSIS RESULT (JSON OUTPUT ONLY)")
    print("="*50)
    print(json.dumps(analysis_result, indent=2))
    print("="*50 + "\n")

    # Write report to file
    with open(analysis_report_path, "w", encoding="utf-8") as rf:
        json.dump(analysis_result, rf, indent=2)
    logger.info(f"Saved Phase 5 analysis report to {analysis_report_path}")

if __name__ == "__main__":
    main()
