import httpx
from datetime import datetime
from typing import List
from discovery_engine.config.constants import SourceType, BLINKIT_APP_STORE_ID
from discovery_engine.loaders.base_loader import BaseReviewLoader
from discovery_engine.models.raw_record import RawRecord
from discovery_engine.utils.logging import logger

class AppStoreReviewLoader(BaseReviewLoader):
    """Loader to ingest iOS customer reviews from the Apple App Store RSS feed."""

    def __init__(self, app_id: str = BLINKIT_APP_STORE_ID, count: int = 100):
        self.app_id = app_id
        self.count = count

    @property
    def source_type(self) -> SourceType:
        return SourceType.APP_STORE

    def fetch_raw(self, **kwargs) -> List[RawRecord]:
        app_id = kwargs.get("app_id", self.app_id)
        records = []

        url = f"https://itunes.apple.com/in/rss/customerreviews/id={app_id}/sortby=mostrecent/json"
        
        try:
            logger.info(f"Fetching iOS reviews from App Store RSS: {url}")
            response = httpx.get(url, timeout=10.0)
            if response.status_code == 200:
                data = response.json()
                entries = data.get("feed", {}).get("entry", [])
                
                # Check if entries exists and is a list (sometimes it's a single dict if only 1 review)
                if isinstance(entries, dict):
                    entries = [entries]
                
                # Skip the first entry if it's the app metadata info
                for idx, entry in enumerate(entries):
                    if idx == 0 and "im:name" in entry:
                        continue
                    
                    review_id = entry.get("id", {}).get("label")
                    author = entry.get("author", {}).get("name", {}).get("label", "Unknown")
                    title = entry.get("title", {}).get("label", "")
                    content = entry.get("content", {}).get("label", "")
                    rating_str = entry.get("im:rating", {}).get("label")
                    version = entry.get("im:version", {}).get("label", "")

                    try:
                        rating = int(rating_str) if rating_str else None
                    except ValueError:
                        rating = None

                    payload = {
                        "text": content,
                        "title": title,
                        "rating": rating,
                        "timestamp": datetime.utcnow().isoformat(), # RSS doesn't give precise timestamps for each review in a standardized way in some endpoints, default to utcnow
                        "metadata": {
                            "author": author,
                            "app_version": version
                        }
                    }
                    if review_id:
                        records.append(
                            RawRecord(
                                source_type=self.source_type,
                                source_id=str(review_id),
                                payload=payload,
                                fetched_at=datetime.utcnow()
                            )
                        )
                logger.info(f"Successfully fetched {len(records)} reviews from Apple App Store RSS.")
            else:
                logger.warning(f"App Store RSS returned status {response.status_code}. Falling back to mock data.")
                records = self._get_mock_reviews()
        except Exception as e:
            logger.warning(f"Failed to fetch live iOS App Store reviews ({e}). Falling back to mock data.")
            records = self._get_mock_reviews()

        return records

    def _get_mock_reviews(self) -> List[RawRecord]:
        """Provides mock App Store reviews centered on category discovery."""
        mock_data = [
            {
                "id": "app_ios_001",
                "title": "Nice app but discovery is poor",
                "content": "I love the speed, but the app doesn't help me explore new things. I buy groceries from store, but here I can't browse different categories easily. It forces the repeat buy screen on me.",
                "rating": 3,
                "version": "12.4"
            },
            {
                "id": "app_ios_002",
                "title": "Quality is hit or miss",
                "content": "I wanted to start buying dairy and fresh meat from Blinkit, but the trust factor is not there. I had a bad experience with milk once (it was near expiry) so I only use it for dry snacks now.",
                "rating": 2,
                "version": "12.4"
            },
            {
                "id": "app_ios_003",
                "title": "Unaware of catalog options",
                "content": "I didn't even realize Blinkit stocks electronics accessories! There is no home section displaying these categories. Highly recommend showing some variety on the home page.",
                "rating": 4,
                "version": "12.3"
            }
        ]

        records = []
        for item in mock_data:
            payload = {
                "text": item["content"],
                "title": item["title"],
                "rating": item["rating"],
                "timestamp": datetime.utcnow().isoformat(),
                "metadata": {
                    "author": "Mock iOS User",
                    "app_version": item["version"]
                }
            }
            records.append(
                RawRecord(
                    source_type=self.source_type,
                    source_id=item["id"],
                    payload=payload,
                    fetched_at=datetime.utcnow()
                )
            )
        return records
