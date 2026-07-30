from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

class IngestionRun(BaseModel):
    """Tracks metadata for a specific ingestion run."""
    run_id: str
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    source_type: str
    record_count: int = 0
    status: str = "PENDING"  # PENDING, SUCCESS, SUCCESS_EMPTY, FAILURE, PARTIAL_SUCCESS
    error_summary: Optional[str] = None
