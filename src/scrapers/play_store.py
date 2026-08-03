import logging
from datetime import datetime
from typing import List, Dict, Any

logger = logging.getLogger("PipelineLogger")

DEFAULT_APP_ID = "com.grofers.customerapp"

def scrape_play_store(app_id: str = DEFAULT_APP_ID, limit: int = 50) -> List[Dict[str, Any]]:
    """
    Scrapes reviews from Google Play Store for the given app ID.
    Falls back to mock reviews if scraping fails or returns empty.
    """
    logger.info(f"Starting Google Play Store scraper for app_id={app_id} (limit={limit})...")
    scraped_data = []

    try:
        from google_play_scraper import Sort, reviews
        result, _ = reviews(
            app_id,
            lang='en',
            country='in',
            sort=Sort.NEWEST,
            count=limit
        )

        for rev in result:
            scraped_data.append({
                "id": str(rev.get("reviewId")),
                "text": str(rev.get("content", "")),
                "rating": float(rev.get("score", 0)),
                "timestamp": rev.get("at").isoformat() if isinstance(rev.get("at"), datetime) else str(rev.get("at")),
                "source": "play_store",
                "review_url": f"https://play.google.com/store/apps/details?id={app_id}"
            })
            
        logger.info(f"Google Play Store scraper successfully collected {len(scraped_data)} reviews.")
        
    except Exception as e:
        logger.warning(f"Google Play Store scraping failed: {e}. Generating fallback mock reviews.")

    # Fallback to mock data if empty or failed
    if not scraped_data:
        scraped_data = get_mock_play_store_reviews(limit)
        logger.info(f"Loaded {len(scraped_data)} mock Google Play Store reviews.")

    return scraped_data

def get_mock_play_store_reviews(limit: int) -> List[Dict[str, Any]]:
    """Returns static high-quality mock data representing Play Store reviews."""
    mock_reviews = [
        {
            "id": "play_mock_001",
            "text": "Blinkit speed is amazing as usual. However, I noticed that the fresh fruit section has very limited options compared to physical markets. I only buy staples like sugar and eggs here, rarely explore organic items.",
            "rating": 4.0,
            "timestamp": datetime.utcnow().isoformat(),
            "source": "play_store",
            "review_url": f"https://play.google.com/store/apps/details?id={DEFAULT_APP_ID}"
        },
        {
            "id": "play_mock_002",
            "text": "The app interface makes it hard to browse new arrivals. I search for snacks and it only displays the popular chips brands. How am I supposed to discover new health bars or premium items?",
            "rating": 2.0,
            "timestamp": datetime.utcnow().isoformat(),
            "source": "play_store",
            "review_url": f"https://play.google.com/store/apps/details?id={DEFAULT_APP_ID}"
        },
        {
            "id": "play_mock_003",
            "text": "I ordered some fresh berries, but they turned out stale and almost expired. The quality check is getting worse. I won't order fresh food here again, sticking to branded items like Maggi.",
            "rating": 2.0,
            "timestamp": datetime.utcnow().isoformat(),
            "source": "play_store",
            "review_url": f"https://play.google.com/store/apps/details?id={DEFAULT_APP_ID}"
        },
        {
            "id": "play_mock_004",
            "text": "Too expensive! The delivery fee and surge pricing are ridiculous. The coupons only work for generic categories I don't need.",
            "rating": 3.0,
            "timestamp": datetime.utcnow().isoformat(),
            "source": "play_store",
            "review_url": f"https://play.google.com/store/apps/details?id={DEFAULT_APP_ID}"
        }
    ]
    return mock_reviews[:limit]
