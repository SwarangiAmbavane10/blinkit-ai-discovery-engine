import re
import hashlib
from datetime import datetime, timezone
from typing import Optional, Tuple
from discovery_engine.models.raw_record import RawRecord
from discovery_engine.models.canonical_review import CanonicalReview
from discovery_engine.utils.logging import logger

# Regex patterns for PII redaction
EMAIL_PATTERN = re.compile(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+')
# Indian phone numbers: +91 xxxxx xxxxx, 91xxxxxxxxx, 0xxxxxxxxx, 6-9xxxxxxxx
PHONE_PATTERN = re.compile(r'(?:\+?91[\-\s]?)?[6-9]\d{9}|(?:\+?91[\-\s]?)?\d{3}[\-\s]?\d{3}[\-\s]?\d{4}')
# Simple postal address matching
ADDRESS_PATTERN = re.compile(
    r'(?i)(?:plot\s+no|house\s+no|h\.no|flat\s+no|apt|sector|phase|street|road|ward|lane)\s+[\w\d\s,\-\/\#]+',
    re.IGNORECASE
)

# Gibberish / spam patterns
REPEATED_CHARS_PATTERN = re.compile(r'(.)\1{4,}') # Char repeated 5+ times (e.g. "aaaaa")
REPEATED_WORDS_PATTERN = re.compile(r'\b(\w+)\b(?:\s+\1\b){3,}') # Word repeated 4+ times

class ReviewValidator:
    """Validator class that handles raw data check, PII redaction, spam checks, and content hashing."""

    @staticmethod
    def calculate_hash(text: str) -> str:
        """Returns the SHA-256 hash of the normalized text."""
        normalized = text.strip().lower()
        return hashlib.sha256(normalized.encode('utf-8')).hexdigest()

    @staticmethod
    def redact_pii(text: str) -> str:
        """Redacts emails, phone numbers, and address patterns from the review text."""
        if not text:
            return ""
        text = EMAIL_PATTERN.sub("[REDACTED_EMAIL]", text)
        text = PHONE_PATTERN.sub("[REDACTED_PHONE]", text)
        text = ADDRESS_PATTERN.sub("[REDACTED_ADDRESS]", text)
        return text

    @classmethod
    def validate_and_normalize(
        cls,
        raw_record: RawRecord,
        run_id: str
    ) -> Tuple[bool, Optional[CanonicalReview], Optional[str]]:
        """
        Validates a RawRecord and normalizes it to a CanonicalReview.
        Returns (success_boolean, canonical_review, error_reason_if_failed).
        """
        payload = raw_record.payload
        source_type = raw_record.source_type
        source_id = raw_record.source_id

        # 1. Extract required text field
        text = payload.get("text", "").strip()
        if not text:
            return False, None, "MISSING_TEXT"

        # 2. Extract title if any
        title = payload.get("title", "").strip()
        if not title:
            title = None

        # 3. Check text length constraint (minimum 10 characters)
        if len(text) < 10:
            return False, None, "TEXT_TOO_SHORT"

        # 4. Spam / Gibberish checking
        if REPEATED_CHARS_PATTERN.search(text) or REPEATED_WORDS_PATTERN.search(text):
            return False, None, "SPAM_REJECTED"

        # 5. Extract and validate Rating (if present)
        rating_raw = payload.get("rating")
        rating: Optional[int] = None
        if rating_raw is not None:
            try:
                rating = int(rating_raw)
                if rating < 1 or rating > 5:
                    return False, None, f"INVALID_RATING_{rating}"
            except (ValueError, TypeError):
                return False, None, f"NON_INTEGER_RATING_{rating_raw}"

        # 6. Extract and validate Timestamp
        timestamp_raw = payload.get("timestamp")
        timestamp: datetime
        if timestamp_raw:
            try:
                if isinstance(timestamp_raw, datetime):
                    timestamp = timestamp_raw
                else:
                    # Try parsing ISO format
                    timestamp = datetime.fromisoformat(str(timestamp_raw).replace("Z", "+00:00"))
            except ValueError:
                return False, None, f"INVALID_TIMESTAMP_FORMAT_{timestamp_raw}"
        else:
            timestamp = datetime.now(timezone.utc)

        # Check future timestamp
        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=timezone.utc)
        
        now = datetime.now(timezone.utc)
        if timestamp > now:
            return False, None, "FUTURE_TIMESTAMP"

        # 7. Redact PII
        redacted_text = cls.redact_pii(text)

        # 8. Content Hash for duplicate detection
        content_hash = cls.calculate_hash(redacted_text)

        # 9. Derive Sentiment from rating
        sentiment = "NEUTRAL"
        if rating is not None:
            if rating >= 4:
                sentiment = "POSITIVE"
            elif rating <= 2:
                sentiment = "NEGATIVE"

        # 10. Generate document_id using a predictable name or source id hash
        # To avoid external uuid dependency, we can hash the source_type + source_id
        doc_id_hash = hashlib.md5(f"{source_type.value}:{source_id}".encode()).hexdigest()
        # Formatted like a UUID for compliance
        document_id = f"{doc_id_hash[:8]}-{doc_id_hash[8:12]}-{doc_id_hash[12:16]}-{doc_id_hash[16:20]}-{doc_id_hash[20:]}"

        canonical = CanonicalReview(
            document_id=document_id,
            source_type=source_type,
            source_id=source_id,
            text=text,
            cleaned_text=redacted_text, # default cleaned to redacted text, will do further cleaning in Phase 2
            title=title,
            rating=rating,
            timestamp=timestamp,
            metadata=payload.get("metadata", {}),
            ingestion_run_id=run_id,
            content_hash=content_hash,
            sentiment=sentiment
        )

        return True, canonical, None
