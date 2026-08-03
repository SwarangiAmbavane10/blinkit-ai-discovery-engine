import logging
from datetime import datetime
from typing import List, Dict, Any
import xml.etree.ElementTree as ET
import httpx

logger = logging.getLogger("PipelineLogger")

def scrape_medium(tag: str = "quick-commerce", limit: int = 5) -> List[Dict[str, Any]]:
    """
    Scrapes public article listings from Medium RSS feeds for a given tag.
    Parses XML data credentials-free and falls back to mock growth blog summaries if it fails.
    """
    logger.info(f"Starting Medium RSS scraper for tag='{tag}' (limit={limit})...")
    scraped_data = []

    try:
        url = f"https://medium.com/feed/tag/{tag}"
        headers = {"User-Agent": "Mozilla/5.0"}
        
        with httpx.Client(headers=headers, timeout=10.0) as client:
            response = client.get(url)
            if response.status_code == 200:
                root = ET.fromstring(response.content)
                # Find all <item> tags representing articles
                items = root.findall(".//item")
                for item in items:
                    title = item.find("title").text if item.find("title") is not None else ""
                    link = item.find("link").text if item.find("link") is not None else ""
                    creator = item.find("{http://purl.org/dc/elements/1.1/}creator")
                    creator_name = creator.text if creator is not None else "Author"
                    
                    pub_date = item.find("pubDate").text if item.find("pubDate") is not None else ""
                    # Truncate text content safely
                    description_elem = item.find("description")
                    content = description_elem.text if description_elem is not None else title
                    
                    scraped_data.append({
                        "id": f"medium_{hash(link)}",
                        "text": f"Title: {title}. Curation summary: {content[:400]}... Written by {creator_name}.",
                        "rating": 5.0, # High default weight for professional posts
                        "timestamp": pub_date or datetime.utcnow().isoformat(),
                        "source": "medium",
                        "review_url": link
                    })
                    if len(scraped_data) >= limit:
                        break
                logger.info(f"Medium RSS parser successfully fetched {len(scraped_data)} article feeds.")
    except Exception as e:
        logger.warning(f"Medium RSS scraping failed: {e}. Moving to mock posts fallback.")

    # Fallback to mock data if empty
    if not scraped_data:
        scraped_data = get_mock_medium_posts(limit)
        logger.info(f"Loaded {len(scraped_data)} mock Medium summaries.")

    return scraped_data

def get_mock_medium_posts(limit: int) -> List[Dict[str, Any]]:
    """Returns static high-quality mock data representing Medium commerce articles."""
    mock_posts = [
        {
            "id": "medium_mock_001",
            "text": "Title: Why Category Discovery Stalls in Quick Commerce. Curation summary: While Blinkit and Zepto have achieved product-market fit for immediate replenishment (milk, bread, sodas), users rarely browse for new, premium, or discovery-driven categories. The frictionless 10-minute delivery model creates a cognitive tunnel vision where speed is prioritized over exploration, leading to stagnation in Category Exploration metrics. Written by Tech Analyst.",
            "rating": 5.0,
            "timestamp": datetime.utcnow().isoformat(),
            "source": "medium",
            "review_url": "https://medium.com/growth-insights/mock1"
        },
        {
            "id": "medium_mock_002",
            "text": "Title: Instamart vs Blinkit - The Freshness Curation Dilemma. Curation summary: Fresh produce is the gateway to weekly repeat purchases. When platforms fail to ensure fresh organic veggies, users develop deep quality trust barriers, choosing to buy staples online but reserving fresh categories for local mandis or premium vendors. Curation needs to be backed by robust local logistics checks to rebuild trust. Written by Product Lead.",
            "rating": 5.0,
            "timestamp": datetime.utcnow().isoformat(),
            "source": "medium",
            "review_url": "https://medium.com/product-growth/mock2"
        }
    ]
    return mock_posts[:limit]
