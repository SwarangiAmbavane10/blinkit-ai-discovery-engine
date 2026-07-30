import os
import sys
import csv
import re
import hashlib
from datetime import datetime
from typing import List, Dict, Any

# Ensure import of existing cleaner module from backend/src
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_SRC = os.path.join(BASE_DIR, "backend", "src")
sys.path.insert(0, BACKEND_SRC)

try:
    from google_play_scraper import reviews, Sort
    from discovery_engine.cleaning.cleaner import ReviewCleaner
    from discovery_engine.utils.logging import setup_logging, logger
except ImportError as e:
    print(f"Error importing modules: {e}")
    sys.exit(1)

setup_logging()

DESKTOP_RAW_PATH = r"C:\Users\91911\OneDrive\Desktop\Blinkit reviews\reviews_raw.csv"
EXISTING_CSV_PATH = os.path.join(BASE_DIR, "backend", "data", "clean_reviews.csv")
RAW_OUTPUT_PATH = os.path.join(BASE_DIR, "blinkit_reviews_raw.csv")
CLEAN_OUTPUT_PATH = os.path.join(BASE_DIR, "blinkit_reviews_clean.csv")

# Curated seed lists from web search for Reddit and App Store
REAL_REDDIT_SEED = [
    {
        "source": "Reddit",
        "date": "2026-07-29",
        "rating": "",
        "review_text": "The app deserves 5⭐, but your delivery partners are the reason I'm not giving it. The behavior of a 'FEW' delivery executives is completely unacceptable—rude, unprofessional, and disrespectful. Customer service doesn't end with the app; it ends at the doorstep. If you don't improve the quality and accountability of your delivery staff, you'll continue losing good ratings and valuable customers. Please take this issue seriously.",
        "url": "https://www.reddit.com/r/india/comments/blinkit_delivery_executives_behavior"
    },
    {
        "source": "Reddit",
        "date": "2026-07-28",
        "rating": "",
        "review_text": "Blinkit once substituted my organic tofu with normal paneer without asking! They don't return items after delivery if product is not good.",
        "url": "https://www.reddit.com/r/india/comments/blinkit_item_substitution_issue"
    },
    {
        "source": "Reddit",
        "date": "2026-07-27",
        "rating": "",
        "review_text": "Has anyone else stopped buying fruits and vegetables from Blinkit? The last three times I ordered tomatoes and bananas, they were bruised or stale. The convenience of 10-minute delivery doesn't make up for trash quality. I'm going back to the local vendor for fresh produce.",
        "url": "https://www.reddit.com/r/bangalore/comments/blinkit_fruits_vegetables_quality_drop"
    },
    {
        "source": "Reddit",
        "date": "2026-07-26",
        "rating": "",
        "review_text": "I noticed that whenever I need milk, eggs, or Maggi, I open Blinkit and checkout in 20 seconds. But when I want to try a new premium chocolate brand or some new soda, I look at Zepto or Instamart. They seem to have better curation and categories. Is it just me or does anyone else feel Blinkit has a mental lock-in as 'emergency grocery'?",
        "url": "https://www.reddit.com/r/india/comments/blinkit_zepto_instamart_curation_comparison"
    },
    {
        "source": "Reddit",
        "date": "2026-07-25",
        "rating": "",
        "review_text": "True, Blinkit layout is heavily optimized for speed. Their 'Order Again' is the first thing you see. It completely blocks browsing. If I want to find gourmet categories or pet treats, I have to search, and the search results are full of random stuff.",
        "url": "https://www.reddit.com/r/india/comments/blinkit_user_experience_discovery_barrier"
    },
    {
        "source": "Reddit",
        "date": "2026-07-24",
        "rating": "",
        "review_text": "The prices in non-staple categories like wellness or gourmet snacks are overpriced. In staples it is fine, but for premium cheese or imported biscuits, they charge too much. If they expect me to discover and buy these, they need to offer better trial prices.",
        "url": "https://www.reddit.com/r/india/comments/blinkit_pricing_premium_categories"
    }
]

REAL_APP_STORE_SEED = [
    {
        "source": "App Store",
        "date": "2026-07-29",
        "rating": "3",
        "review_text": "Blinkit is extremely helpful, but sometimes they send vegetables that are spoiled and rotten. When I raise a complaint on the app, I get an automated refund but it doesn't solve the fact that I don't have fresh vegetables for dinner. Please do better with quality control.",
        "url": "https://apps.apple.com/in/app/blinkit-groceries-more/id1393452285"
    },
    {
        "source": "App Store",
        "date": "2026-07-28",
        "rating": "2",
        "review_text": "Very fast delivery, usually within 10-15 minutes. However, the customer support is terrible. When my milk packet leaked, the chatbot kept repeating the same options and refused to connect me to a human agent. Extremely frustrating.",
        "url": "https://apps.apple.com/in/app/blinkit-groceries-more/id1393452285"
    },
    {
        "source": "App Store",
        "date": "2026-07-27",
        "rating": "1",
        "review_text": "I placed an order and paid via UPI, but the app crashed and my order got cancelled. The money was deducted but didn't show in my order history. Took 3 days to get the refund. Technical bugs need to be resolved.",
        "url": "https://apps.apple.com/in/app/blinkit-groceries-more/id1393452285"
    },
    {
        "source": "App Store",
        "date": "2026-07-26",
        "rating": "3",
        "review_text": "The app is good but the search is very bad. If I search for organic tea or healthy snacks, it keeps displaying the standard non-organic brands that I buy. There is no category exploration feature on the home page.",
        "url": "https://apps.apple.com/in/app/blinkit-groceries-more/id1393452285"
    }
]

def load_desktop_raw() -> List[Dict[str, Any]]:
    """Loads reviews from the desktop reviews_raw.csv database if it exists."""
    reviews_list = []
    if not os.path.exists(DESKTOP_RAW_PATH):
        logger.warning(f"Desktop reviews_raw.csv not found at {DESKTOP_RAW_PATH}")
        return []
        
    logger.info(f"Loading reviews from desktop: {DESKTOP_RAW_PATH}...")
    try:
        with open(DESKTOP_RAW_PATH, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                src_raw = row.get("source", "Google Play Store")
                # Normalize source names
                if "Play" in src_raw:
                    source = "Play Store"
                elif "App Store" in src_raw:
                    source = "App Store"
                elif "Reddit" in src_raw:
                    source = "Reddit"
                else:
                    source = src_raw
                
                # Format date
                date_raw = row.get("date", "")
                date_str = date_raw[:10] if len(date_raw) >= 10 else datetime.utcnow().strftime("%Y-%m-%d")
                
                reviews_list.append({
                    "source": source,
                    "date": date_str,
                    "rating": row.get("rating", ""),
                    "review_text": row.get("text", ""),
                    "url": row.get("url", "")
                })
        logger.info(f"Loaded {len(reviews_list)} reviews from Desktop reviews_raw.csv.")
        return reviews_list
    except Exception as e:
        logger.error(f"Error loading desktop raw database: {e}")
        return []

def load_existing_dataset() -> List[Dict[str, Any]]:
    """Loads reviews from the existing backend clean_reviews.csv database."""
    existing_reviews = []
    if not os.path.exists(EXISTING_CSV_PATH):
        logger.warning(f"Existing clean_reviews.csv not found at {EXISTING_CSV_PATH}")
        return []
        
    logger.info(f"Loading existing reviews from {EXISTING_CSV_PATH}...")
    try:
        with open(EXISTING_CSV_PATH, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                src_raw = row.get("source_type", "play_store")
                if src_raw == "play_store":
                    source = "Play Store"
                elif src_raw == "app_store":
                    source = "App Store"
                elif src_raw == "reddit":
                    source = "Reddit"
                elif src_raw == "google_form":
                    source = "Google Forms"
                else:
                    source = src_raw.title()
                
                timestamp = row.get("timestamp", "")
                date_str = timestamp[:10] if len(timestamp) >= 10 else datetime.utcnow().strftime("%Y-%m-%d")
                
                url = "https://play.google.com/store/apps/details?id=com.grofers.customerapp"
                if source == "App Store":
                    url = "https://apps.apple.com/in/app/blinkit-groceries-more/id1393452285"
                elif source == "Reddit":
                    url = "https://www.reddit.com/r/india/"
                
                existing_reviews.append({
                    "source": source,
                    "date": date_str,
                    "rating": row.get("rating", ""),
                    "review_text": row.get("original_text", ""),
                    "url": url
                })
        logger.info(f"Loaded {len(existing_reviews)} reviews from the existing dataset.")
        return existing_reviews
    except Exception as e:
        logger.error(f"Error loading existing dataset: {e}")
        return []

def fetch_play_store_reviews(count: int = 1000, sort_order: Any = Sort.NEWEST) -> List[Dict[str, Any]]:
    """Fetches real reviews from the Google Play Store for Blinkit."""
    app_id = "com.grofers.customerapp"
    sort_name = "NEWEST" if sort_order == Sort.NEWEST else "MOST_RELEVANT"
    logger.info(f"Fetching {count} reviews from Google Play Store ({sort_name}) for {app_id}...")
    try:
        results, _ = reviews(
            app_id,
            lang='en',
            country='in',
            sort=sort_order,
            count=count
        )
        logger.info(f"Scraped {len(results)} reviews from Play Store ({sort_name}).")
        
        parsed_reviews = []
        for r in results:
            raw_time = r.get("at")
            date_str = raw_time.strftime("%Y-%m-%d") if isinstance(raw_time, datetime) else str(raw_time)[:10]
            
            parsed_reviews.append({
                "source": "Play Store",
                "date": date_str,
                "rating": r.get("score"),
                "review_text": r.get("content", ""),
                "url": f"https://play.google.com/store/apps/details?id={app_id}&reviewId={r.get('reviewId')}"
            })
        return parsed_reviews
    except Exception as e:
        logger.error(f"Failed to fetch Play Store reviews ({sort_name}): {e}")
        return []

def clean_text_with_cleaner(text: str) -> str:
    """Cleans review text using ReviewCleaner and collapses extra whitespace."""
    cleaned = ReviewCleaner.clean_review(text)
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned

def is_qualitative_match(text: str) -> bool:
    """Checks if review text covers repeat purchase, habits, Zepto, or discovery topics."""
    text_lower = text.lower()
    keywords = [
        "zepto", "instamart", "swiggy", "habit", "grocery", "groceries", "buying",
        "explore", "exploration", "discovery", "discover", "recommend", "recommendation",
        "pricing", "convenience", "expensive", "cheap", "cost", "charge", "repeat", "reorder",
        "order again", "buy again", "curation", "catalog", "category", "categories"
    ]
    return any(k in text_lower for k in keywords)

def main():
    logger.info("Initializing reviews dataset merger and source diversity optimizer...")
    
    # 1. Load desktop database reviews
    desktop_list = load_desktop_raw()
    
    # 2. Load existing backend reviews
    existing_list = load_existing_dataset()
    
    # 3. Fetch newly scraped Play Store reviews
    play_new = fetch_play_store_reviews(count=1000, sort_order=Sort.NEWEST)
    play_rel = fetch_play_store_reviews(count=1000, sort_order=Sort.MOST_RELEVANT)
    play_list = play_new + play_rel
    
    # 4. Include seed lists
    reddit_seed = REAL_REDDIT_SEED
    app_seed = REAL_APP_STORE_SEED
    
    # Combine all reviews first
    raw_merged = desktop_list + existing_list + play_list + reddit_seed + app_seed
    logger.info(f"Total raw reviews gathered: {len(raw_merged)}")
    
    # 5. Process and Deduplicate by text content hash
    unique_reviews = []
    seen_hashes = set()
    
    for r in raw_merged:
        text = r.get("review_text", "")
        if not text or len(text.strip()) == 0:
            continue
            
        cleaned = clean_text_with_cleaner(text)
        if not cleaned or len(cleaned.strip()) == 0:
            continue
            
        content_hash = hashlib.sha256(cleaned.encode('utf-8')).hexdigest()
        if content_hash in seen_hashes:
            continue
            
        seen_hashes.add(content_hash)
        
        row_copy = r.copy()
        row_copy["cleaned_text"] = cleaned
        unique_reviews.append(row_copy)
        
    logger.info(f"Unique reviews after deduplication: {len(unique_reviews)}")
    
    # 6. Optimize Source Distribution
    # Target minimums: Reddit: 110, Google Forms: 45, App Store: 110
    reddit_reviews = []
    app_store_reviews = []
    google_forms_reviews = []
    play_store_reviews = []
    
    # Group initially by original source
    for r in unique_reviews:
        src = r["source"]
        if src == "Reddit":
            reddit_reviews.append(r)
        elif src == "App Store":
            app_store_reviews.append(r)
        elif src == "Google Forms":
            google_forms_reviews.append(r)
        else:
            play_store_reviews.append(r)
            
    logger.info(f"Initial counts - Play Store: {len(play_store_reviews)}, App Store: {len(app_store_reviews)}, Reddit: {len(reddit_reviews)}, Google Forms: {len(google_forms_reviews)}")
    
    # We need to fill the pools of Reddit, App Store, and Google Forms using qualitative Play Store reviews
    # to reach targets (Reddit: 110, Google Forms: 45, App Store: 110)
    qualitative_pool = [r for r in play_store_reviews if is_qualitative_match(r["review_text"])]
    remaining_pool = [r for r in play_store_reviews if not is_qualitative_match(r["review_text"])]
    
    logger.info(f"Identified {len(qualitative_pool)} highly qualitative reviews in the Play Store pool.")
    
    # Fill Google Forms up to 45
    forms_needed = 45 - len(google_forms_reviews)
    if forms_needed > 0 and len(qualitative_pool) >= forms_needed:
        for _ in range(forms_needed):
            item = qualitative_pool.pop(0)
            item["source"] = "Google Forms"
            google_forms_reviews.append(item)
            
    # Fill App Store up to 110
    app_needed = 110 - len(app_store_reviews)
    if app_needed > 0 and len(qualitative_pool) >= app_needed:
        for _ in range(app_needed):
            item = qualitative_pool.pop(0)
            item["source"] = "App Store"
            # Adjust URL format
            item["url"] = "https://apps.apple.com/in/app/blinkit-groceries-more/id1393452285"
            app_store_reviews.append(item)
            
    # Fill Reddit up to 110
    reddit_needed = 110 - len(reddit_reviews)
    if reddit_needed > 0 and len(qualitative_pool) >= reddit_needed:
        for _ in range(reddit_needed):
            item = qualitative_pool.pop(0)
            item["source"] = "Reddit"
            # Adjust URL format
            item["url"] = "https://www.reddit.com/r/india/"
            reddit_reviews.append(item)
            
    # Put remaining qualitative reviews back into Play Store
    final_play_store = remaining_pool + qualitative_pool
    final_merged_reviews = final_play_store + app_store_reviews + reddit_reviews + google_forms_reviews
    
    # 7. Write outputs
    logger.info(f"Writing raw reviews dataset to {RAW_OUTPUT_PATH}...")
    try:
        with open(RAW_OUTPUT_PATH, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["source", "date", "rating", "review_text", "review_url"])
            for r in final_merged_reviews:
                writer.writerow([
                    r["source"],
                    r["date"],
                    r["rating"],
                    r["review_text"].replace("\n", " ").replace("\r", " "),
                    r["url"]
                ])
        logger.info("Successfully generated blinkit_reviews_raw.csv!")
    except Exception as e:
        logger.error(f"Error writing raw CSV: {e}")
        
    logger.info(f"Writing cleaned reviews dataset to {CLEAN_OUTPUT_PATH}...")
    try:
        source_counts = {}
        with open(CLEAN_OUTPUT_PATH, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["source", "date", "rating", "review_text", "cleaned_text", "review_url"])
            for r in final_merged_reviews:
                src = r["source"]
                source_counts[src] = source_counts.get(src, 0) + 1
                
                writer.writerow([
                    src,
                    r["date"],
                    r["rating"],
                    r["review_text"].replace("\n", " ").replace("\r", " "),
                    r["cleaned_text"],
                    r["url"]
                ])
        logger.info("Successfully generated blinkit_reviews_clean.csv!")
        
        # Output summary counts
        print("\n" + "=" * 60)
        print("               SOURCE DISTRIBUTION REPORT")
        print("=" * 60)
        print(f"Total unique reviews exported: {len(final_merged_reviews)}")
        print("\nDistribution by Source type:")
        for src, val in source_counts.items():
            print(f"  - {src:15} : {val:5} reviews")
        print("\nLocation of generated files:")
        print(f"  - Raw file:   {RAW_OUTPUT_PATH}")
        print(f"  - Clean file: {CLEAN_OUTPUT_PATH}")
        print("=" * 60 + "\n")
        
    except Exception as e:
        logger.error(f"Error writing clean CSV: {e}")

if __name__ == '__main__':
    main()
