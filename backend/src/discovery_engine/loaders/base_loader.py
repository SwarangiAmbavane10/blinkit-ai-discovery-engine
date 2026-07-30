from abc import ABC, abstractmethod
from typing import List
from discovery_engine.config.constants import SourceType
from discovery_engine.models.raw_record import RawRecord

class BaseReviewLoader(ABC):
    """Abstract base class for all review and feedback collection loaders."""

    @property
    @abstractmethod
    def source_type(self) -> SourceType:
        """Returns the SourceType enum value for this loader."""
        pass

    @abstractmethod
    def fetch_raw(self, **kwargs) -> List[RawRecord]:
        """
        Fetches raw reviews from the external source.
        Returns a list of RawRecord objects.
        """
        pass
