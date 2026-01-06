import sys
from pathlib import Path
# Ensure repository root is on sys.path so both package and script execution work.
# This file is at: <repo>/data/models/ontology/ontology_description.py
# repo root is three parents up from this file.
_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
	sys.path.insert(0, str(_REPO_ROOT))
from data.models.ontology.base_stix import StixObject
from data.models.ontology.identity_ontology import State

class Location(StixObject):
    def __init__(
        self,
        *,
        name: str,
        state: State | None = None,
        latitude: float | None = None,
        longitude: float | None = None,
        admin_level: int | None = None,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self._name = name
        self._state = state
        self._latitude = latitude
        self._longitude = longitude
        self._admin_level = admin_level
        
    def _identity_material(self) -> str:
        state_id = self._state._iso_code if self._state else "unknown"
        return f"{self._name}:{state_id}:{self._latitude}:{self._longitude}"