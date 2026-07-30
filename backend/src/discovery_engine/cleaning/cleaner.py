import re
from typing import List, Set

# Regex patterns
URL_PATTERN = re.compile(r'https?://\S+|www\.\S+')
# Unicode range matching most emojis/symbols in supplementary plane
EMOJI_PATTERN = re.compile(r'[\U00010000-\U0010FFFF]', flags=re.UNICODE)

# Basic list of English stopwords to avoid external downloads/NLTK dependency
ENGLISH_STOPWORDS: Set[str] = {
    "i", "me", "my", "myself", "we", "our", "ours", "ourselves", "you", "your", 
    "yours", "yourself", "yourselves", "he", "him", "his", "himself", "she", 
    "her", "hers", "herself", "it", "its", "itself", "they", "them", "their", 
    "theirs", "themselves", "what", "which", "who", "whom", "this", "that", 
    "these", "those", "am", "is", "are", "was", "were", "be", "been", "being", 
    "have", "has", "had", "having", "do", "does", "did", "doing", "a", "an", 
    "the", "and", "but", "if", "or", "because", "as", "until", "while", "of", 
    "at", "by", "for", "with", "about", "against", "between", "into", "through", 
    "during", "before", "after", "above", "below", "to", "from", "up", "down", 
    "in", "out", "on", "off", "over", "under", "again", "further", "then", "once",
    "here", "there", "when", "where", "why", "how", "all", "any", "both", "each", 
    "few", "more", "most", "other", "some", "such", "no", "nor", "not", "only", 
    "own", "same", "so", "than", "too", "very", "s", "t", "can", "will", "just", 
    "don", "should", "now"
}

class ReviewCleaner:
    """Provides methods for cleaning and normalizing review texts for downstream matching."""

    @staticmethod
    def remove_urls(text: str) -> str:
        """Removes web links from the text."""
        return URL_PATTERN.sub('', text)

    @staticmethod
    def remove_emojis(text: str) -> str:
        """Removes emoji characters."""
        return EMOJI_PATTERN.sub('', text)

    @classmethod
    def remove_stopwords(cls, text: str) -> str:
        """Splits the text into words and filters out standard English stopwords."""
        # Use regex to split by non-word chars to get clean tokens
        tokens = re.findall(r'\b\w+\b', text.lower())
        filtered_tokens = [t for t in tokens if t not in ENGLISH_STOPWORDS]
        return ' '.join(filtered_tokens)

    @classmethod
    def normalize_text(cls, text: str) -> str:
        """Performs basic cleaning: lowercase, removes punctuation, simplifies spacing."""
        # Lowercase
        text = text.lower()
        # Clean URLs
        text = cls.remove_urls(text)
        # Clean Emojis
        text = cls.remove_emojis(text)
        # Remove non-alphanumeric (keep spaces, apostrophes, and letters)
        text = re.sub(r'[^a-zA-Z0-9\s]', '', text)
        # Collapse multiple spaces and trim
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    @classmethod
    def clean_review(cls, text: str) -> str:
        """Runs the full cleaning pipeline: url/emoji removal, normalization, and stopword removal."""
        normalized = cls.normalize_text(text)
        cleaned = cls.remove_stopwords(normalized)
        return cleaned
