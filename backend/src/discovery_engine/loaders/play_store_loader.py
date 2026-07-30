from datetime import datetime, timezone
from typing import List
from google_play_scraper import reviews, Sort
from discovery_engine.config.constants import SourceType, BLINKIT_PLAY_STORE_ID
from discovery_engine.loaders.base_loader import BaseReviewLoader
from discovery_engine.models.raw_record import RawRecord
from discovery_engine.utils.logging import logger

class PlayStoreReviewLoader(BaseReviewLoader):
    """Loader to ingest reviews from Google Play Store for the Blinkit App."""

    def __init__(self, app_id: str = BLINKIT_PLAY_STORE_ID, count: int = 100):
        self.app_id = app_id
        self.count = count

    @property
    def source_type(self) -> SourceType:
        return SourceType.PLAY_STORE

    def fetch_raw(self, **kwargs) -> List[RawRecord]:
        count = kwargs.get("count", self.count)
        app_id = kwargs.get("app_id", self.app_id)
        records = []

        try:
            logger.info(f"Fetching reviews from Play Store for app {app_id}...")
            result, _ = reviews(
                app_id,
                lang='en',
                country='in',
                sort=Sort.NEWEST,
                count=count
            )

            for rev in result:
                raw_time = rev.get("at")
                timestamp_str = raw_time.isoformat() if isinstance(raw_time, datetime) else str(raw_time)
                
                payload = {
                    "text": rev.get("content", ""),
                    "rating": rev.get("score"),
                    "timestamp": timestamp_str,
                    "metadata": {
                        "user_name": rev.get("userName"),
                        "thumbs_up_count": rev.get("thumbsUpCount"),
                        "app_version": rev.get("appVersion")
                    }
                }
                records.append(
                    RawRecord(
                        source_type=self.source_type,
                        source_id=str(rev.get("reviewId", "")),
                        payload=payload,
                        fetched_at=datetime.utcnow()
                    )
                )
            logger.info(f"Successfully fetched {len(records)} reviews from Google Play Store.")
        except Exception as e:
            logger.warning(f"Failed to fetch live Play Store reviews ({e}). Falling back to mock data.")
            records = self._get_mock_reviews()

        return records

    def _get_mock_reviews(self) -> List[RawRecord]:
        """Provides mock Play Store reviews focused on category exploration barriers."""
        mock_data = [
            {
                "id": "play_gp_001",
                "content": "Blinkit is super fast! I always order bread and milk every morning. But the layout only prompts me to reorder the same stuff, making it hard to see other options.",
                "score": 4,
                "at": "2026-07-28T10:00:00Z",
                "appVersion": "12.4.0"
            },
            {
                "id": "play_gp_002",
                "content": "The app is good but recommendations are useless. I bought organic soap once and now my whole home page is only soap. Why don't they recommend organic snacks or vegetables instead?",
                "score": 3,
                "at": "2026-07-27T15:30:00Z",
                "appVersion": "12.4.0"
            },
            {
                "id": "play_gp_003",
                "content": "I wanted to try ordering fresh vegetables from Blinkit but I am very hesitant. Last time my friend ordered tomatoes and they were rotten. I prefer going to the local market for vegetables because of quality concerns.",
                "score": 2,
                "at": "2026-07-26T08:45:00Z",
                "appVersion": "12.3.9"
            },
            {
                "id": "play_gp_004",
                "content": "Why is the search so bad for new categories? If I type premium tea, it shows the standard Tata tea that I buy regularly instead of showing artisanal brands.",
                "score": 2,
                "at": "2026-07-25T11:20:00Z",
                "appVersion": "12.3.9"
            },
            {
                "id": "play_gp_005",
                "content": "Very convenient app, delivery is always on time. However, I didn't even know they sell pet supplies until my coworker mentioned it. The app doesn't advertise new sections well.",
                "score": 4,
                "at": "2026-07-24T18:10:00Z",
                "appVersion": "12.4.0"
            }
        ]

        records = []
        for item in mock_data:
            payload = {
                "text": item["content"],
                "rating": item["score"],
                "timestamp": item["at"],
                "metadata": {
                    "user_name": "Mock User",
                    "thumbs_up_count": 0,
                    "app_version": item["appVersion"]
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
