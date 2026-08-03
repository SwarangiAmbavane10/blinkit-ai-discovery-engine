import os
import logging
from datetime import datetime
from typing import List, Dict, Any
import httpx

logger = logging.getLogger("PipelineLogger")

def scrape_twitter(query: str = "blinkit", limit: int = 10) -> List[Dict[str, Any]]:
    """
    Scrapes tweets matching query from Twitter/X API v2.
    Falls back to mock tweets if no Bearer Token is available or X API requests fail.
    """
    logger.info(f"Starting Twitter/X scraper for query='{query}' (limit={limit})...")
    scraped_data = []

    bearer_token = os.getenv("TWITTER_BEARER_TOKEN")

    if bearer_token:
        try:
            headers = {
                "Authorization": f"Bearer {bearer_token}",
                "User-Agent": "v2RecentSearchPython"
            }
            # Twitter API v2 Recent Search Endpoint
            url = f"https://api.twitter.com/2/tweets/search/recent?query={query}&max_results={limit}"
            
            with httpx.Client(headers=headers, timeout=10.0) as client:
                response = client.get(url)
                if response.status_code == 200:
                    tweets = response.json().get("data", [])
                    for t in tweets:
                        scraped_data.append({
                            "id": f"twitter_{t.get('id')}",
                            "text": str(t.get("text", "")),
                            "rating": 1.0,  # Default rating equivalent for tweets
                            "timestamp": datetime.utcnow().isoformat(),  # fallback timestamp
                            "source": "twitter",
                            "review_url": f"https://twitter.com/twitter/status/{t.get('id')}"
                        })
                    logger.info(f"X API search successfully collected {len(scraped_data)} tweets.")
                else:
                    logger.warning(f"X API returned status {response.status_code}: {response.text}")
        except Exception as e:
            logger.warning(f"X API scraping request failed: {e}. Moving to mock tweets fallback.")

    # Fallback to mock data if empty
    if not scraped_data:
        scraped_data = get_mock_tweets(limit)
        logger.info(f"Loaded {len(scraped_data)} mock tweets.")

    return scraped_data

def get_mock_tweets(limit: int) -> List[Dict[str, Any]]:
    """Returns static high-quality mock data representing tweets/X posts."""
    mock_tweets = [
        {
            "id": "twitter_mock_001",
            "text": "Blinkit is basically the modern pantry. Need butter? Done in 8 mins. But when it comes to buying organic foods, premium spices, or skincare, I prefer browsing elsewhere. The catalog design just does not inspire discovery. #QuickCommerce",
            "rating": 1.0,
            "timestamp": datetime.utcnow().isoformat(),
            "source": "twitter",
            "review_url": "https://twitter.com/user/status/mock1"
        },
        {
            "id": "twitter_mock_002",
            "text": "Why is the search so broken on Blinkit? I search for premium tea and it shows Tetley. Curation is badly needed to make people try new categories. Sticking to normal weekly orders.",
            "rating": 1.0,
            "timestamp": datetime.utcnow().isoformat(),
            "source": "twitter",
            "review_url": "https://twitter.com/user/status/mock2"
        },
        {
            "id": "twitter_mock_003",
            "text": "Got a batch of rotten onions from Blinkit today. Decided I'm never ordering fresh avocados or gourmet fresh fruits here. Trust issues are real. #Blinkit #Delivery",
            "rating": 1.0,
            "timestamp": datetime.utcnow().isoformat(),
            "source": "twitter",
            "review_url": "https://twitter.com/user/status/mock3"
        }
    ]
    return mock_tweets[:limit]
