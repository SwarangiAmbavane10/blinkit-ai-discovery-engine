import pytest
from datetime import datetime
from discovery_engine.models.raw_record import RawRecord
from discovery_engine.config.constants import SourceType
from discovery_engine.validation.validator import ReviewValidator

def test_validate_and_normalize_success():
    payload = {
        "text": "This is a very good app and I love using it!",
        "rating": 5,
        "timestamp": "2026-07-28T12:00:00Z"
    }
    raw = RawRecord(source_type=SourceType.PLAY_STORE, source_id="id_123", payload=payload)
    success, canonical, error = ReviewValidator.validate_and_normalize(raw, "run_test_123")
    
    assert success
    assert canonical is not None
    assert error is None
    assert canonical.rating == 5
    assert canonical.sentiment == "POSITIVE"
    assert canonical.source_id == "id_123"
    assert len(canonical.document_id) == 36 # UUID format length

def test_validate_and_normalize_too_short():
    payload = {
        "text": "Short",
        "rating": 5,
        "timestamp": "2026-07-28T12:00:00Z"
    }
    raw = RawRecord(source_type=SourceType.PLAY_STORE, source_id="id_123", payload=payload)
    success, canonical, error = ReviewValidator.validate_and_normalize(raw, "run_test_123")
    
    assert not success
    assert canonical is None
    assert error == "TEXT_TOO_SHORT"

def test_validate_and_normalize_invalid_rating():
    payload = {
        "text": "This is a very good app and I love using it!",
        "rating": 9,
        "timestamp": "2026-07-28T12:00:00Z"
    }
    raw = RawRecord(source_type=SourceType.PLAY_STORE, source_id="id_123", payload=payload)
    success, canonical, error = ReviewValidator.validate_and_normalize(raw, "run_test_123")
    
    assert not success
    assert canonical is None
    assert "INVALID_RATING" in error

def test_pii_redaction():
    text_with_pii = "Contact me at user@example.com or call me on +91 9876543210. Address: House No 42, Sector 15, Gurgaon."
    redacted = ReviewValidator.redact_pii(text_with_pii)
    
    assert "[REDACTED_EMAIL]" in redacted
    assert "[REDACTED_PHONE]" in redacted
    assert "[REDACTED_ADDRESS]" in redacted
    assert "user@example.com" not in redacted
    assert "9876543210" not in redacted
    assert "House No 42" not in redacted

def test_spam_detection():
    # Character repeating spam
    payload = {
        "text": "Worst app ever aaaaaaaaaaaaaaa",
        "rating": 1,
        "timestamp": "2026-07-28T12:00:00Z"
    }
    raw = RawRecord(source_type=SourceType.PLAY_STORE, source_id="id_123", payload=payload)
    success, canonical, error = ReviewValidator.validate_and_normalize(raw, "run_test_123")
    assert not success
    assert error == "SPAM_REJECTED"
