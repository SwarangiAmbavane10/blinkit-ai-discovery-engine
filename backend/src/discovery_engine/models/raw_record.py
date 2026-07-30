from datetime import datetime
from typing import Dict, Any
from pydantic import BaseModel, Field
from discovery_engine.config.constants import SourceType

class RawRecord(BaseModel):
    """Pydantic model representing a raw user review/feedback item before cleaning."""
    source_type: SourceType
    source_id: str
    payload: Dict[str, Any]
    fetched_at: datetime = Field(default_factory=datetime.utcnow)
