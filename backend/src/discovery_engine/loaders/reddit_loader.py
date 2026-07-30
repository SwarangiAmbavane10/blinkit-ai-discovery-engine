import praw
from datetime import datetime, timezone
from typing import List
from discovery_engine.config.constants import SourceType, DEFAULT_SUBREDDITS, DEFAULT_SEARCH_TERMS
from discovery_engine.config.settings import settings
from discovery_engine.loaders.base_loader import BaseReviewLoader
from discovery_engine.models.raw_record import RawRecord
from discovery_engine.utils.logging import logger

class RedditReviewLoader(BaseReviewLoader):
    """Loader to crawl and fetch Reddit posts and comments containing Blinkit keywords."""

    def __init__(self, limit: int = 50):
        self.limit = limit

    @property
    def source_type(self) -> SourceType:
        return SourceType.REDDIT

    def fetch_raw(self, **kwargs) -> List[RawRecord]:
        limit = kwargs.get("limit", self.limit)
        records = []

        # Check for PRAW config
        has_praw_config = (
            settings.REDDIT_CLIENT_ID and 
            settings.REDDIT_CLIENT_SECRET
        )

        if not has_praw_config:
            logger.info("Reddit PRAW credentials not set. Using mock Reddit discussions.")
            return self._get_mock_reddit_data()

        try:
            logger.info("Initializing Reddit PRAW client...")
            reddit = praw.Reddit(
                client_id=settings.REDDIT_CLIENT_ID,
                client_secret=settings.REDDIT_CLIENT_SECRET,
                user_agent=settings.REDDIT_USER_AGENT
            )

            search_query = " OR ".join(settings.REDDIT_SEARCH_TERMS)
            
            for sub_name in settings.REDDIT_SUBREDDITS:
                logger.info(f"Searching r/{sub_name} for '{search_query}'...")
                subreddit = reddit.subreddit(sub_name)
                
                # Fetch submissions
                submissions = subreddit.search(search_query, limit=limit, sort="relevance")
                for sub in submissions:
                    # Capture submission
                    created_utc = datetime.fromtimestamp(sub.created_utc, timezone.utc)
                    payload = {
                        "text": sub.selftext if sub.selftext else "",
                        "title": sub.title,
                        "timestamp": created_utc.isoformat(),
                        "rating": None, # Reddit posts do not have ratings
                        "metadata": {
                            "subreddit": sub_name,
                            "score": sub.score,
                            "num_comments": sub.num_comments,
                            "url": sub.url,
                            "type": "submission"
                        }
                    }
                    records.append(
                        RawRecord(
                            source_type=self.source_type,
                            source_id=f"reddit_sub_{sub.id}",
                            payload=payload,
                            fetched_at=datetime.utcnow()
                        )
                    )

                    # Also fetch top comments (briefly)
                    sub.comments.replace_more(limit=0) # Get top level comments
                    for comment in sub.comments[:5]:
                        c_created = datetime.fromtimestamp(comment.created_utc, timezone.utc)
                        c_payload = {
                            "text": comment.body,
                            "title": f"Comment on: {sub.title}",
                            "timestamp": c_created.isoformat(),
                            "rating": None,
                            "metadata": {
                                "subreddit": sub_name,
                                "score": comment.score,
                                "parent_submission_id": sub.id,
                                "type": "comment"
                            }
                        }
                        records.append(
                            RawRecord(
                                source_type=self.source_type,
                                source_id=f"reddit_cmt_{comment.id}",
                                payload=c_payload,
                                fetched_at=datetime.utcnow()
                            )
                        )
            logger.info(f"Successfully fetched {len(records)} Reddit records.")
        except Exception as e:
            logger.warning(f"Error fetching live Reddit threads ({e}). Falling back to mock data.")
            records = self._get_mock_reddit_data()

        return records

    def _get_mock_reddit_data(self) -> List[RawRecord]:
        """Provides high-quality mock Reddit discussions centering on Zepto/Instamart comparisons and Blinkit category issues."""
        mock_data = [
            {
                "id": "reddit_sub_101",
                "title": "Why do people only use Blinkit for staples but Zepto/Instamart for trial?",
                "text": "I noticed that whenever I need milk, eggs, or Maggi, I open Blinkit and checkout in 20 seconds. But when I want to try a new premium chocolate brand or some new soda, I look at Zepto or Instamart. They seem to have better curation and categories. Is it just me or does anyone else feel Blinkit has a mental lock-in as 'emergency grocery'?",
                "subreddit": "india",
                "score": 55,
                "type": "submission"
            },
            {
                "id": "reddit_cmt_201",
                "title": "Comment on category trial",
                "text": "True, Blinkit layout is heavily optimized for speed. Their 'Order Again' is the first thing you see. It completely blocks browsing. If I want to find gourmet categories or pet treats, I have to search, and the search results are full of random stuff. I substitution fear is another reason - Blinkit once substituted my organic tofu with normal paneer without asking!",
                "subreddit": "india",
                "score": 25,
                "type": "comment"
            },
            {
                "id": "reddit_sub_102",
                "title": "Blinkit vegetables quality has gone down drastically",
                "text": "Has anyone else stopped buying fruits and vegetables from Blinkit? The last three times I ordered tomatoes and bananas, they were bruised or stale. The convenience of 10-minute delivery doesn't make up for trash quality. I'm going back to the local vendor for fresh produce.",
                "subreddit": "bangalore",
                "score": 80,
                "type": "submission"
            },
            {
                "id": "reddit_cmt_202",
                "title": "Comment on pricing and trust",
                "text": "I agree. Plus, the prices in non-staple categories like wellness or gourmet snacks are overpriced. In staples it is fine, but for premium cheese or imported biscuits, they charge too much. If they expect me to discover and buy these, they need to offer better trial prices.",
                "subreddit": "bangalore",
                "score": 12,
                "type": "comment"
            }
        ]

        records = []
        for item in mock_data:
            payload = {
                "text": item["text"],
                "title": item["title"],
                "timestamp": datetime.utcnow().isoformat(),
                "rating": None,
                "metadata": {
                    "subreddit": item["subreddit"],
                    "score": item["score"],
                    "type": item["type"]
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
