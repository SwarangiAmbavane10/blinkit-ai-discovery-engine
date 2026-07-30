import os
import sys
import json
import csv
from datetime import datetime

# ---------------------------------------------------------
# 1. SETUP SYSTEM PATHS & IMPORTS
# ---------------------------------------------------------
# Dynamically add the backend/src directory to sys.path to resolve imports cleanly
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_SRC = os.path.join(BASE_DIR, "backend", "src")
sys.path.insert(0, BACKEND_SRC)

# Import existing modules
try:
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
except ImportError as ie:
    print(f"Error importing modules: {ie}")
    print("Please make sure you are running main.py from the root of the project.")
    sys.exit(1)

def ensure_raw_feedback_csv():
    """Checks if a sample CSV file exists for Google Form responses, creates one if missing."""
    sample_csv_path = os.path.join(BASE_DIR, "backend", "data", "google_form_responses.csv")
    if not os.path.exists(sample_csv_path):
        os.makedirs(os.path.dirname(sample_csv_path), exist_ok=True)
        headers = ["Timestamp", "Response ID", "Feedback Text", "Rating (1-5)", "Customer City"]
        rows = [
            ["2026-07-28T09:00:00Z", "form_001", "I really love Blinkit's speed, but I only use the app to buy milk and eggs. I don't feel motivated to try wellness products because they are expensive.", "4", "Delhi"],
            ["2026-07-27T10:15:00Z", "form_002", "I tried buying fresh paneer last week, but the app sent me one that was close to expiry. The trust isn't there, so I avoid other fresh categories now.", "2", "Bangalore"],
            ["2026-07-26T14:22:00Z", "form_003", "The search function is annoying. If I search for organic tea, it displays standard tea. Very frustrating to discover premium items.", "2", "Mumbai"],
            ["2026-07-25T16:30:00Z", "form_004", "I always check out in 15 seconds. It is a convenience tool. I don't use it for browsing new items, I use Zepto or physical stores for exploring snacks.", "3", "Gurgaon"]
        ]
        with open(sample_csv_path, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            writer.writerows(rows)
        logger.info(f"Generated sample feedback CSV at {sample_csv_path}")
    return sample_csv_path

def bootstrap_data_pipeline(cleaned_csv_path: str, sample_csv_path: str):
    """Orchestrates data collection and cleaning to bootstrap cleaned reviews."""
    logger.info("Clean reviews corpus not found. Bootstrapping data pipeline (Phases 1-2)...")
    
    # Configure directories dynamically
    settings.RAW_STORE_DIR = os.path.join(BASE_DIR, "backend", "data", "raw")
    settings.DEAD_LETTER_QUEUE_DIR = os.path.join(BASE_DIR, "backend", "data", "dlq")

    # Initialize sources
    loaders = [
        PlayStoreReviewLoader(),
        AppStoreReviewLoader(),
        RedditReviewLoader(),
        CSVReviewLoader(file_path=sample_csv_path)
    ]

    # Ingestion & Validation
    runner = CollectionRunner(loaders)
    runs_metadata, canonical_reviews = runner.run()

    # Cleaning & Export
    unique_count = ReviewExporter.clean_and_export_csv(canonical_reviews, cleaned_csv_path)
    logger.info(f"Bootstrapping complete. {unique_count} canonical reviews exported to {cleaned_csv_path}")

def main():
    # ---------------------------------------------------------
    # 2. INITIALIZATION & DATA LOADING
    # ---------------------------------------------------------
    setup_logging()
    logger.info("Initializing Blinkit AI Discovery Engine analysis runner...")

    cleaned_csv_path = os.path.join(BASE_DIR, "backend", "data", "clean_reviews.csv")
    discovery_path = os.path.join(BASE_DIR, "blinkit_discovery_reviews.csv")
    root_clean_path = os.path.join(BASE_DIR, "blinkit_reviews_clean.csv")
    if os.path.exists(discovery_path):
        cleaned_csv_path = discovery_path
    elif os.path.exists(root_clean_path):
        cleaned_csv_path = root_clean_path

    results_dir = os.path.join(BASE_DIR, "analysis", "results")
    output_report_path = os.path.join(results_dir, "report.json")

    # Check and bootstrap data if clean reviews don't exist
    try:
        # Only bootstrap if none of the datasets exist
        if not os.path.exists(cleaned_csv_path) and not os.path.exists(discovery_path) and not os.path.exists(root_clean_path):
            sample_csv_path = ensure_raw_feedback_csv()
            bootstrap_data_pipeline(cleaned_csv_path, sample_csv_path)
    except Exception as e:
        logger.error(f"Failed to bootstrap data pipeline: {e}")
        print(f"Error: Could not ingest and clean review data. Details: {e}")
        sys.exit(1)

    # Load cleaned reviews and compute stats
    reviews_count = 0
    source_counts = {}
    
    try:
        with open(cleaned_csv_path, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                reviews_count += 1
                src = row.get("source_type", "unknown")
                source_counts[src] = source_counts.get(src, 0) + 1
    except Exception as e:
        logger.error(f"Error loading clean reviews from {cleaned_csv_path}: {e}")
        print(f"Error: Failed to read cleaned data. Details: {e}")
        sys.exit(1)

    if reviews_count == 0:
        logger.warning("No reviews found in corpus.")
        print("Warning: The cleaned reviews file is empty. Please check your data sources.")
        sys.exit(0)

    # ---------------------------------------------------------
    # 3. RETRIEVAL & SEMANTIC SEARCH
    # ---------------------------------------------------------
    logger.info("Initializing Retrieval Engine (Phase 3)...")
    top_reviews = []
    try:
        retriever = RetrievalEngine()
        retriever.load_corpus(cleaned_csv_path)
        question = "Why don't users explore categories?"
        top_reviews = retriever.retrieve(query=question, top_k=20)
    except Exception as e:
        logger.error(f"Error retrieving reviews: {e}")
        print(f"Error: Failed to query/retrieve relevant reviews. Details: {e}")
        sys.exit(1)

    # ---------------------------------------------------------
    # 4. LLM SYNTHESIS & INSIGHT GENERATION
    # ---------------------------------------------------------
    logger.info("Structuring prompt and executing Google Gemini Analysis (Phases 4-5)...")
    business_goal = "Increase the percentage of Monthly Active Customers (MAC) who purchase from at least one new category every month."
    
    analysis_result = {}
    try:
        # Build prompt
        prompt = PromptBuilder.build_synthesis_prompt(
            business_goal=business_goal,
            question=question,
            reviews=top_reviews
        )

        # Call Gemini Client
        client = GeminiClient()
        analysis_result = client.generate_content(prompt, json_mode=True)

        # Save result to outputs folder
        os.makedirs(results_dir, exist_ok=True)
        with open(output_report_path, "w", encoding="utf-8") as rf:
            json.dump(analysis_result, rf, indent=2)
        logger.info(f"Saved analysis output to {output_report_path}")

    except Exception as e:
        logger.error(f"Error running LLM analysis pipeline: {e}")
        print(f"Error: Failed to synthesize insights via Google Gemini. Details: {e}")
        sys.exit(1)

    # ---------------------------------------------------------
    # 5. CLI REPORT FORMATTING & DISPLAY
    # ---------------------------------------------------------
    # Mapping sources to human readable names for CLI print
    source_map = {
        "play_store": "Play Store",
        "app_store": "App Store",
        "reddit": "Reddit",
        "google_form": "Google Forms"
    }
    sources_str = ", ".join(f"{source_map.get(k, k)} ({v})" for k, v in source_counts.items())

    print("\n" + "="*70)
    print("           BLINKIT AI DISCOVERY ENGINE — INSIGHT REPORT")
    print("="*70)
    print(f"• Total Cleaned Reviews Analyzed : {reviews_count}")
    print(f"• Ingested Feedback Sources      : {sources_str}")
    print(f"• Confidence Rating of Synthesis : {analysis_result.get('overall_analysis', {}).get('confidence_score', 'N/A')}")
    print(f"• Results Export Path            : {os.path.relpath(output_report_path)}")
    print("="*70)

    # Display Top User Pain Points
    print("\n[TOP USER PAIN POINTS]")
    pain_points_printed = 0
    for cluster in analysis_result.get("theme_clustering", []):
        for theme in cluster.get("themes", []):
            for pp in theme.get("pain_points", []):
                print(f"  - {pp}")
                pain_points_printed += 1
                if pain_points_printed >= 5: # limit to top 5
                    break
            if pain_points_printed >= 5:
                break
    if not pain_points_printed:
        print("  - No direct pain points extracted.")

    # Display Key Discovery Opportunities
    print("\n[KEY DISCOVERY OPPORTUNITIES]")
    opps = analysis_result.get("opportunities", [])
    for idx, opp in enumerate(opps[:3]): # top 3 opportunities
        print(f"  {idx+1}. {opp.get('opportunity_name')} (Impact: {opp.get('business_impact')})")
        print(f"     Action: {opp.get('description')}")
        print(f"     Target Segment: {opp.get('target_segment')}")

    # Display Generated Insights & Hypotheses
    print("\n[GENERATED INSIGHTS & HYPOTHESES]")
    overall_rationale = analysis_result.get("overall_analysis", {}).get("confidence_rationale", "")
    if overall_rationale:
        print(f"  Confidence Rationale: {overall_rationale}")
    
    jtbd_list = analysis_result.get("jtbd", [])
    if jtbd_list:
        print("\n  Jobs-To-Be-Done (JTBD) Hypotheses:")
        for idx, jtbd in enumerate(jtbd_list[:2]):
            print(f"    - {jtbd.get('situation')}, {jtbd.get('motivation')}, {jtbd.get('expected_outcome')}")
            
    print("="*70 + "\n")

if __name__ == "__main__":
    main()
