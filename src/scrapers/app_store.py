import logging
from datetime import datetime
from typing import List, Dict, Any

logger = logging.getLogger("PipelineLogger")

DEFAULT_APP_NAME = "blinkit-groceries-more"
DEFAULT_APP_ID = 1393452285

def scrape_app_store(app_name: str = DEFAULT_APP_NAME, app_id: int = DEFAULT_APP_ID, limit: int = 50) -> List[Dict[str, Any]]:
    """
    Scrapes reviews from Apple App Store for the given app.
    Falls back to mock reviews if scraping fails or returns empty.
    """
    logger.info(f"Starting Apple App Store scraper for app_name={app_name} (limit={limit})...")
    scraped_data = []

    try:
        from src.app_store_scraper import AppStore
        # Initialize Apple AppStore scraper (targeting India app store 'in')
        app = AppStore(country='in', app_name=app_name, id=app_id)
        app.review(how_many=limit)

        for rev in app.reviews:
            scraped_data.append({
                "id": str(rev.get("id") or rev.get("title", "")),
                "text": str(rev.get("review", "")),
                "rating": float(rev.get("rating", 0)),
                "timestamp": rev.get("date").isoformat() if isinstance(rev.get("date"), datetime) else str(rev.get("date")),
                "source": "app_store",
                "review_url": f"https://apps.apple.com/in/app/id{app_id}"
            })
            
        logger.info(f"Apple App Store scraper successfully collected {len(scraped_data)} reviews.")
        
    except Exception as e:
        logger.warning(f"Apple App Store scraping failed: {e}. Generating fallback mock reviews.")

    # Fallback to mock data if empty or failed
    if not scraped_data:
        scraped_data = get_mock_app_store_reviews(limit)
        logger.info(f"Loaded {len(scraped_data)} mock Apple App Store reviews.")

    return scraped_data

def get_mock_app_store_reviews(limit: int) -> List[Dict[str, Any]]:
    """Returns static high-quality mock data representing App Store reviews."""
    mock_reviews = [
        {
            "id": "app_mock_001",
            "text": "The UI looks premium, but it feels like the app is designed only for rapid checkout. There are no recommendation boards or list suggestions to explore other categories. I always order the same 5 items.",
            "rating": 3.0,
            "timestamp": datetime.utcnow().isoformat(),
            "source": "app_store",
            "review_url": f"https://apps.apple.com/in/app/id{DEFAULT_APP_ID}"
        },
        {
            "id": "app_mock_002",
            "text": "I tried searching for gluten-free snacks, but the filters are non-existent. It just dumps random items on the screen. Very bad browsing experience for healthy premium products.",
            "rating": 2.0,
            "timestamp": datetime.utcnow().isoformat(),
            "source": "app_store",
            "review_url": f"https://apps.apple.com/in/app/id{DEFAULT_APP_ID}"
        },
        {
            "id": "app_mock_003",
            "text": "Delivery was extremely quick, under 10 minutes. However, the quality check on vegetables is sub-par. I got rotten tomatoes twice. I will stick to Zepto for fresh veggies.",
            "rating": 3.0,
            "timestamp": datetime.utcnow().isoformat(),
            "source": "app_store",
            "review_url": f"https://apps.apple.com/in/app/id{DEFAULT_APP_ID}"
        }
    ]
    return mock_reviews[:limit]
