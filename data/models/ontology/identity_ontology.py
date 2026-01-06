import sys
from pathlib import Path
# Ensure repository root is on sys.path so both package and script execution work.
# This file is at: <repo>/data/models/ontology/ontology_description.py
# repo root is three parents up from this file.
_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
	sys.path.insert(0, str(_REPO_ROOT))
from data.models.ontology.base_stix import StixObject
from typing import Optional, List

class Identity(StixObject):
    def __init__(
        self,
        *,
        name: str,
        identity_class: str,
        roles: Optional[List[str]] = None,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self._name = name
        self._identity_class = identity_class
        self._roles = roles or []
        
    def _identity_material(self) -> str:
        """
        Same object (e.g. person) and same name results in same ID. However, adding time 'created' to the ID distinguishes version.
        """
        return f"{self._identity_class}:{self._name.lower()}"
        
class Person(Identity):
    def __init__(self, *, name: str, **kwargs):
        super().__init__(
            name=name,
            identity_class="individual",
            **kwargs,
        )

class Organization(Identity):
    def __init__(self, *, name: str, **kwargs):
        super().__init__(
            name=name,
            identity_class="organization",
            **kwargs,
        )

class State(Identity):
    def __init__(
        self,
        *,
        name: str,
        iso_code: Optional[str] = None,
        **kwargs,
    ):
        super().__init__(
            name=name,
            identity_class="state",
            **kwargs,
        )
        self._iso_code = iso_code
