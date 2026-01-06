from __future__ import annotations

from .base_stix import StixObject
from typing import Optional, List
from datetime import datetime
import sys
from pathlib import Path
# Ensure repository root is on sys.path so both package and script execution work.
# This file is at: <repo>/data/models/ontology/ontology_description.py
# repo root is three parents up from this file.
_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
	sys.path.insert(0, str(_REPO_ROOT))
from data.models.ontology.location_ontology import Location

class Event(StixObject):
    def __init__(
        self,
        *,
        event_type: str,
        occurred_at: Optional[datetime] = None,
        location: Optional[Location] = None,
        description: Optional[str] = None,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self._event_type = event_type
        self._occurred_at = occurred_at
        self._location = location
        self._description = description
        
    def _identity_material(self) -> str:
        return f"{self._event_type}:{self._occurred_at}:{self._location.name if self._location else None}"

#=========================#
# VIOLENCE
#=========================#

class ViolentEvent(Event):
    def __init__(
        self,
        *,
        subtype: str,
        fatalities: int = 0,
        injured: int = 0,
        weapons: Optional[List["Weapon"]] = None,
        **kwargs,
    ):
        super().__init__(
            event_type = "violent-event",
            **kwargs,
        )
        self._subtype = subtype
        self._fatalities = fatalities
        self._injured = injured
        self._weapons = weapons or []
        
class KnifeAttack(ViolentEvent):
    def __init__(self, **k):
        super().__init__(subtype="knife-attack", **k)
class Shooting(ViolentEvent):
    def __init__(self, **k):
        super().__init__(subtype="shooting", **k)
class Bombing(ViolentEvent):
    def __init__(self, **k):
        super().__init__(subtype="bombing", **k)
class Arson(ViolentEvent):
    def __init__(self, **k):
        super().__init__(subtype="arson", **k)
class Riot(ViolentEvent):
    def __init__(self, **k):
        super().__init__(subtype="riot", **k)
class Kidnapping(ViolentEvent):
    def __init__(self, **k):
        super().__init__(subtype="kidnapping", **k)
class Assassination(ViolentEvent):#
    def __init__(self, **k):
        super().__init__(subtype="assassination", **k)
class Massacre(ViolentEvent):
    def __init__(self, **k):
        super().__init__(subtype="massacre", **k)


#=========================#
# POLITICS
#=========================#
class PoliticalEvent(Event):
    def __init__(
        self,
        *,
        subtype: str,
        **kwargs
    ):
        super().__init__(
            event_type="political-event",
            **kwargs
        )
        self._subtype = subtype

class Election(PoliticalEvent):
    def __init__(self, **kwargs):
        super().__init__(subtype="election", **kwargs)

class Protest(PoliticalEvent):
    def __init__(self, **kwargs):
        super().__init__(subtype="protest", **kwargs)

class Coup(PoliticalEvent):
    def __init__(self, **kwargs):
        super().__init__(subtype="coup", **kwargs)

class TradeDeal(PoliticalEvent):
    def __init__(self, **kwargs):
        super().__init__(subtype="trade-deal", **kwargs)

class Sanctions(PoliticalEvent):
    def __init__(self, **kwargs):
        super().__init__(subtype="sanctions", **kwargs)
        
class Repression(PoliticalEvent):
    def __init__(self, **kwargs):
        super().__init__(subtype="repression", **kwargs)


#=========================#
# MILITARY
#=========================#
class MilitaryEvent(Event):
    def __init__(
        self,
        *,
        subtype: str,
        **kwargs
    ):
        super().__init__(
            event_type="military-event",
            **kwargs
        )
        self._subtype = subtype
        
class Airstrike(MilitaryEvent):
    def __init__(self, **kwargs):
        super().__init__(subtype="airstrike", **kwargs)

class GroundOperation(MilitaryEvent):
    def __init__(self, **kwargs):
        super().__init__(subtype="ground-operation", **kwargs)

class DroneStrike(MilitaryEvent):
    def __init__(self, **kwargs):
        super().__init__(subtype="drone-strike", **kwargs)

class NavalIncident(MilitaryEvent):
    """
    E.g. torpedo
    """
    def __init__(self, **kwargs):
        super().__init__(subtype="naval-incident", **kwargs)

class TroopMovement(MilitaryEvent):
    def __init__(self, **kwargs):
        super().__init__(subtype="troop-movement", **kwargs)

class MilitaryExercise(MilitaryEvent):
    def __init__(self, **kwargs):
        super().__init__(subtype="military-exercise", **kwargs)

#=========================#
# CYBER
#=========================#
class CyberEvent(Event):
    def __init__(
        self,
        *,
        subtype: str,
        tools: Optional[List["CyberTool"]] = None,
        **kwargs,
    ):
        self._subtype = subtype
        self._tools = tools or []
        super().__init__(event_type="cyber-event", **kwargs)

class CyberAttack(CyberEvent):
    def __init__(self, **k):
        super().__init__(subtype="cyber-attack", **k)

class DataBreach(CyberEvent):
    def __init__(self, **k):
        super().__init__(subtype="data-breach", **k)

class Espionage(CyberEvent):
    def __init__(self, **k):
        super().__init__(subtype="espionage", **k)

class Disinformation(CyberEvent):
    def __init__(self, **k):
        super().__init__(subtype="disinformation", **k)
        
#=========================#
# CRIME
#=========================#
class CrimeEvent(Event):
    def __init__(
        self,
        *,
        subtype: str,
        severity: Optional[str] = None,
        **kwargs,
    ):
        self.subtype = subtype
        self.severity = severity
        super().__init__(event_type="crime-event", **kwargs)

class Theft(CrimeEvent):
    def __init__(self, **k):
        super().__init__(subtype="theft", **k)
        
class Fraud(CrimeEvent):
    def __init__(self, **k):
        super().__init__(subtype="fraud", **k)
        
class Homicide(CrimeEvent):
    def __init__(self, **k):
        super().__init__(subtype="homicide", **k)
        
class Robbery(CrimeEvent):
    def __init__(self, **k):
        super().__init__(subtype="robbery", **k)
        
class Extortion(CrimeEvent):
    def __init__(self, **k):
        super().__init__(subtype="extortion", **k)