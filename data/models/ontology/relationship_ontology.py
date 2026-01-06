import sys
from pathlib import Path
# Ensure repository root is on sys.path so both package and script execution work.
# This file is at: <repo>/data/models/ontology/ontology_description.py
# repo root is three parents up from this file.
_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
	sys.path.insert(0, str(_REPO_ROOT))
from data.models.ontology.base_stix import StixObject
from datetime import datetime
from typing import Optional, List, TYPE_CHECKING

class Relationship(StixObject):
    def __init__(
        self,
        *,
        relationship_type: str,
        source: StixObject,
        target: StixObject,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        **kwargs,
    ):
        self._relationship_type = relationship_type
        self._source = source
        self._target = target
        self._start_time = start_time
        self._end_time = end_time
        super().__init__(**kwargs)

    def _identity_material(self) -> str:
        return f"{self._relationship_type}:{self._source.id}:{self._target.id}"