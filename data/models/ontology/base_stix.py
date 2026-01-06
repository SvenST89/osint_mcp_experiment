from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import List, Optional
import hashlib

class StixObject(ABC):
    """
    Base class for STIX-aligned ontology objects.
    The intention is to allow for OSINT ontology definitions, not just Cyber-centric intelligence.
    """
    
    def __init__(
        self,
        *, # define that following arguments must be explicitly given as keyword-arguments
        id: Optional[str] = None,
        created: Optional[datetime] = None,
        modified: Optional[datetime] = None,
        confidence: float = 0.1,
        sources: Optional[List[str]] = None,
    ):
        self._id = id or None
        self._created = created or datetime.now(timezone.utc)
        self._modified = modified or self._created
        self._confidence = confidence
        self._sources = sources or []

    @abstractmethod
    def _identity_material(self) -> str:
        """
        Return a string that uniquely represents this object semantically.
        Must be implemented by subclasses.
        """
        ...

    def _generate_id(self) -> str:
        rawstr = f"{self.__class__.__name__}:{self._identity_material()}:{self._created.isoformat()}"
        hashedstr = hashlib.sha256(rawstr.encode("utf-8")).hexdigest()
        return f"{self.__class__.__name__.lower()}_{hashedstr}"

    def touch(self) -> None:
        self._modified = datetime.now(timezone.utc)