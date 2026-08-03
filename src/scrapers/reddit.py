import os
import logging
from datetime import datetime
from typing import List, Dict, Any
import httpx

logger = logging.getLogger("PipelineLogger")

def scrape_reddit(subreddits: List[str] = None, search_term: str = "blinkit", limit: int = 20) -> List[Dict[str, Any]]:
    """
    Scrapes Reddit threads/comments mentioning search terms in specified subreddits.
    Attempts:
      1. PRAW client if credentials present.
      2. Public JSON endpoint search if no credentials (credentials-free).
      3. Mock fallback.
    """
    if subreddits is None:
        subreddits = ["india", "bangalore", "delhi", "mumbai"]

    logger.info(f"Starting Reddit scraper for search_term='{search_term}' across {subreddits} (limit={limit})...")
    scraped_data = []

    client_id = os.getenv("REDDIT_CLIENT_ID")
    client_secret = os.getenv("REDDIT_CLIENT_SECRET")
    user_agent = os.getenv("REDDIT_USER_AGENT", "blinkit-scraper:v1.0.0")

    # 1. Attempt PRAW Scraping
    if client_id and client_secret:
        try:
            import praw
            logger.info("Initializing PRAW Reddit client...")
            reddit = praw.Reddit(
                client_id=client_id,
                client_secret=client_secret,
                user_agent=user_agent
            )
            for sub_name in subreddits:
                subreddit = reddit.subreddit(sub_name)
                for submission in subreddit.search(search_term, limit=limit // len(subreddits) + 1):
                    scraped_data.append({
                        "id": f"reddit_post_{submission.id}",
                        "text": f"{submission.title} - {submission.selftext}"[:1000],
                        "rating": float(submission.score),
                        "timestamp": datetime.utcfromtimestamp(submission.created_utc).isoformat(),
                        "source": "reddit",
                        "review_url": f"https://www.reddit.com{submission.permalink}"
                    })
            logger.info(f"PRAW Reddit scraper collected {len(scraped_data)} records.")
        except Exception as e:
            logger.warning(f"Reddit PRAW scraping failed: {e}. Attempting public JSON API feed...")

    # 2. Attempt Credentials-Free Public JSON API Search
    if not scraped_data:
        try:
            logger.info("Accessing public Reddit search feeds...")
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
            with httpx.Client(headers=headers, timeout=10.0) as client:
                for sub_name in subreddits:
                    url = f"https://www.reddit.com/r/{sub_name}/search.json?q={search_term}&restrict_sr=1&sort=new&limit={limit}"
                    response = client.get(url)
                    if response.status_code == 200:
                        children = response.json().get("data", {}).get("children", [])
                        for child in children:
                            post = child.get("data", {})
                            scraped_data.append({
                                "id": f"reddit_json_{post.get('id')}",
                                "text": f"{post.get('title', '')} - {post.get('selftext', '')}"[:1000],
                                "rating": float(post.get("score", 0)),
                                "timestamp": datetime.utcfromtimestamp(post.get("created_utc", datetime.utcnow().timestamp())).isoformat(),
                                "source": "reddit",
                                "review_url": f"https://www.reddit.com{post.get('permalink', '')}"
                            })
            logger.info(f"Reddit JSON feed search collected {len(scraped_data)} posts.")
        except Exception as e:
            logger.warning(f"Reddit Public JSON feed request failed: {e}. Proceeding to mock fallback.")

    # 3. Fallback to mock data if empty
    if not scraped_data:
        scraped_data = get_mock_reddit_reviews(limit)
        logger.info(f"Loaded {len(scraped_data)} mock Reddit posts.")

    return scraped_data[:limit]

def get_mock_reddit_reviews(limit: int) -> List[Dict[str, Any]]:
    """Returns static high-quality mock data representing Reddit discussions."""
    mock_posts = [
        {
            "id": "reddit_mock_001",
            "text": "Why doesn't anyone buy wellness or beauty items from Blinkit? Honestly, they advertise organic shampoo and serums, but I only use the app when I'm in a rush for eggs or milk. If I want to browse products, I'd rather go to Nykaa or look around physically.",
            "rating": 12.0,
            "timestamp": datetime.utcnow().isoformat(),
            "source": "reddit",
            "review_url": "https://www.reddit.com/r/india/comments/mock1"
        },
        {
            "id": "reddit_mock_002",
            "text": "Blinkit checkout speed vs Dunzo assortment. Blinkit is fast but Dunzo had much better gourmet options. Whenever I try to browse new cheese or import snacks, Blinkit just shows basic Amul stuff. There is no category curation.",
            "rating": 45.0,
            "timestamp": datetime.utcnow().isoformat(),
            "source": "reddit",
            "review_url": "https://www.reddit.com/r/bangalore/comments/mock2"
        },
        {
            "id": "reddit_mock_003",
            "text": "Has anyone faced issues with vegetables on quick commerce? Instamart and Blinkit keep sending near-expiry or bruised veggies. I am hesitant to try their premium fresh cuts because of this. How do we trust freshness?",
            "rating": 28.0,
            "timestamp": datetime.utcnow().isoformat(),
            "source": "reddit",
            "review_url": "https://www.reddit.com/r/delhi/comments/mock3"
        }
    ]
    return mock_posts[:limit]
