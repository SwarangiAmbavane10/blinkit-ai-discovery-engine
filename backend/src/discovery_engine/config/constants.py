from enum import Enum

class SourceType(str, Enum):
    PLAY_STORE = "play_store"
    APP_STORE = "app_store"
    REDDIT = "reddit"
    GOOGLE_FORM = "google_form"

# Blinkit Default Constants
BLINKIT_PLAY_STORE_ID = "com.grofers.customerapp"
BLINKIT_APP_STORE_ID = "1393452285"
DEFAULT_SUBREDDITS = ["india", "bangalore", "delhi", "gurgaon", "mumbai"]
DEFAULT_SEARCH_TERMS = ["blinkit", "grofers"]

# Default Blinkit L1 Category Taxonomy
BLINKIT_CATEGORIES = [
    "Fresh Produce",
    "Dairy & Bread",
    "Snacks & Munchies",
    "Beverages",
    "Personal Care",
    "Household Essentials",
    "Baby Care",
    "Pet Care",
    "Health & Wellness",
    "Frozen Foods"
]
