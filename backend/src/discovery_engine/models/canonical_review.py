from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from discovery_engine.config.constants import SourceType

class CanonicalReview(BaseModel):
    """Pydantic model representing a normalized, validated, and cleaned review."""
    document_id: str
    source_type: SourceType
    source_id: str
    text: str
    cleaned_text: Optional[str] = None
    title: Optional[str] = None
    rating: Optional[int] = None
    timestamp: datetime
    metadata: Dict[str, Any] = Field(default_factory=dict)
    ingestion_run_id: str
    content_hash: str
    sentiment: Optional[str] = "NEUTRAL"
