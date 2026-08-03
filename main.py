import os
import sys
import logging
from dotenv import load_dotenv

# Load environment configurations from local .env file
load_dotenv()

# Setup logging system
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=LOG_LEVEL,
    format="[%(asctime)s] %(levelname)s [%(name)s:%(lineno)d] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("PipelineLogger")

# Import Scraping Layer Modules
from src.scrapers.play_store import scrape_play_store
from src.scrapers.app_store import scrape_app_store
from src.scrapers.reddit import scrape_reddit
from src.scrapers.twitter import scrape_twitter
from src.scrapers.medium import scrape_medium

# Import Ingestion & AI Processing & Storage Modules
from src.ingest import ingest_raw_streams
from src.process_insights import extract_insights_from_reviews
from src.generate_embeddings import generate_review_embeddings
from src.upsert_pinecone import index_embeddings_in_pinecone

def main():
    logger.info("=================================================================")
    logger.info("         STARTING AUTOMATED 5-LAYER AI DATA PIPELINE             ")
    logger.info("=================================================================")

    # -------------------------------------------------------------------------
    # LAYER 2: SCRAPING LAYER (External Data Collection)
    # -------------------------------------------------------------------------
    logger.info("[LAYER 2] Initiating multi-channel scraping...")
    
    raw_reviews = []
    
    # 1. Play Store reviews
    play_store_reviews = scrape_play_store(limit=30)
    raw_reviews.extend(play_store_reviews)
    
    # 2. App Store reviews
    app_store_reviews = scrape_app_store(limit=20)
    raw_reviews.extend(app_store_reviews)
    
    # 3. Reddit posts
    reddit_reviews = scrape_reddit(limit=20)
    raw_reviews.extend(reddit_reviews)
    
    # 4. Twitter/X mentions
    twitter_reviews = scrape_twitter(limit=15)
    raw_reviews.extend(twitter_reviews)
    
    # 5. Medium articles
    medium_reviews = scrape_medium(limit=10)
    raw_reviews.extend(medium_reviews)

    logger.info(f"[LAYER 2] Data collection finished. Aggregated {len(raw_reviews)} total raw records.")

    # -------------------------------------------------------------------------
    # LAYER 3: INGESTION LAYER (Cleanup & Local Dump)
    # -------------------------------------------------------------------------
    logger.info("[LAYER 3] Initiating ingestion clean-up and deduplication...")
    cleaned_reviews = ingest_raw_streams(raw_reviews, output_path="data/raw_reviews_dump.json")
    
    if not cleaned_reviews:
        logger.error("[LAYER 3] Ingestion returned 0 cleaned records. Aborting pipeline execution.")
        sys.exit(1)

    # -------------------------------------------------------------------------
    # LAYER 4: AI PROCESSING LAYER (Structured Insights & Dense Vectors)
    # -------------------------------------------------------------------------
    logger.info("[LAYER 4] Initiating AI processing layer...")
    
    # 1. Extract JSON Insights via Groq REST API (Llama 3.1)
    synthesized_reviews = extract_insights_from_reviews(cleaned_reviews, output_path="data/synthesized_needs.json")
    
    # 2. Generate 384D Vector Embeddings via sentence-transformers
    final_dataset = generate_review_embeddings(synthesized_reviews)

    # -------------------------------------------------------------------------
    # LAYER 5: STORAGE & INDEXING LAYER (Pinecone Upsert)
    # -------------------------------------------------------------------------
    logger.info("[LAYER 5] Initiating Pinecone storage and vector indexing...")
    success = index_embeddings_in_pinecone(final_dataset)

    if success:
        logger.info("=================================================================")
        logger.info("         PIPELINE RUN SUCCESSFULLY COMPLETED                     ")
        logger.info("=================================================================")
    else:
        logger.warning("=================================================================")
        logger.warning("         PIPELINE COMPLETED WITH STORAGE ERRORS/WARNINGS         ")
        logger.warning("=================================================================")

if __name__ == "__main__":
    main()
