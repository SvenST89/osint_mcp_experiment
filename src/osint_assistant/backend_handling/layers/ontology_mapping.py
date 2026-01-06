"""Object-oriented mapper: LLM outputs -> ontology objects.

The mapper creates ontology instances (events, identities, locations, tools,
weapons and relationships) from an `ExtractedEventOutput` instance. The main
entry point is `OntologyMapper.map()` which returns the created event and a
list of auxiliary objects (actors, tools, weapons, relationships).
"""

from __future__ import annotations

from typing import List, Optional, Tuple
from datetime import datetime
import re

from data.models.llm_ontology_output import ExtractedEventOutput, Actor

from data.models.ontology.identity_ontology import Person, Organization, State
from data.models.ontology.location_ontology import Location
from data.models.ontology.tools_ontology import Weapon, CyberTool
from data.models.ontology import event_ontology as eo
from data.models.ontology.relationship_ontology import Relationship


class OntologyMapper:
    """Maps LLM-extracted event outputs into ontology objects.

    Usage:
      mapper = OntologyMapper()
      event_obj, aux = mapper.map(extracted_event_output)

    Returns:
      - event_obj: an instance of an Event subclass (e.g. ViolentEvent)
      - aux: List of other created StixObjects (actors, tools, weapons, relationships)
    """

    FIREARM_KEYWORDS = {"gun", "rifle", "pistol", "handgun", "shotgun", "ak-", "m4", "firearm"}
    MELEE_KEYWORDS = {"knife", "machete", "blade", "sword", "club"}
    EXPLOSIVE_KEYWORDS = {"bomb", "explosive", "grenade", "ied", "car bomb"}

    def __init__(self):
        pass

    def map(self, event: ExtractedEventOutput) -> Tuple[eo.Event, List[object]]:
        """Map an `ExtractedEventOutput` to ontology objects.

        Returns the created event and a list of auxiliary objects.
        """
        created = []

        # Location
        location = Location(name=event.location) if event.location else None
        if location:
            created.append(location)

        # Actors -> Identity objects
        actors = [self._map_actor(a) for a in (event.actors or [])]
        created.extend(actors)

        # Weapons / tools
        weapons_objs = []
        tools_objs = []
        if event.event_type == "violent-event":
            for w in event.weapons:
                weapons_objs.append(self._map_weapon(w))
            created.extend(weapons_objs)
        elif event.event_type == "cyber-event":
            for t in event.weapons:
                tools_objs.append(self._map_cybertool(t))
            created.extend(tools_objs)

        # Parse occurred_at to datetime when possible
        occurred_at = self._parse_datetime(event.occurred_at)

        # Build event object depending on type
        evt = None
        common_kwargs = {
            "occurred_at": occurred_at,
            "location": location,
            "confidence": event.confidence,
            "sources": [event.source_url] if event.source_url else [],
        }

        if event.event_type == "violent-event":
            evt = eo.ViolentEvent(
                subtype=event.subtype,
                fatalities=event.fatalities or 0,
                injured=event.injured or 0,
                weapons=weapons_objs,
                **common_kwargs,
            )

        elif event.event_type == "cyber-event":
            evt = eo.CyberEvent(
                subtype=event.subtype,
                tools=tools_objs,
                **common_kwargs,
            )

        elif event.event_type == "political-event":
            evt = eo.PoliticalEvent(subtype=event.subtype, **common_kwargs)

        elif event.event_type == "military-event":
            evt = eo.MilitaryEvent(subtype=event.subtype, **common_kwargs)

        elif event.event_type == "crime-event":
            # ExtractedEventOutput does not carry severity; leave None
            evt = eo.CrimeEvent(subtype=event.subtype, severity=None, **common_kwargs)

        else:
            # Fallback: generic Event
            evt = eo.Event(event_type=event.event_type, occurred_at=occurred_at, location=location, **common_kwargs)

        # Create relationships between actors and event based on role
        relationships = []
        for a, actor in zip(event.actors or [], actors):
            rel_type = self._relationship_type_for_role(a.role)
            if rel_type:
                rel = Relationship(relationship_type=rel_type, source=actor, target=evt)
                relationships.append(rel)
        created.extend(relationships)

        # Return event and created helpers
        return evt, created

    def _map_actor(self, actor: Actor):
        """Infer an Identity subclass for an actor."""
        name = actor.name
        role = (actor.role or "").lower()

        if "state" in role or "government" in role:
            return State(name=name)

        if any(k in role for k in ("org", "organization", "company", "corp", "inc", "ltd")):
            return Organization(name=name)

        # Default to Person
        return Person(name=name)

    def _map_weapon(self, name: str) -> Weapon:
        """Create a Weapon with a simple type heuristic."""
        n = name.lower()
        wtype = "unknown"
        if any(k in n for k in self.FIREARM_KEYWORDS):
            wtype = "firearm"
        elif any(k in n for k in self.MELEE_KEYWORDS):
            wtype = "melee"
        elif any(k in n for k in self.EXPLOSIVE_KEYWORDS):
            wtype = "explosive"
        return Weapon(name=name, weapon_type=wtype)

    def _map_cybertool(self, name: str) -> CyberTool:
        return CyberTool(name=name)

    def _relationship_type_for_role(self, role: Optional[str]) -> Optional[str]:
        if not role:
            return None
        r = role.lower()
        if "attacker" in r or "perp" in r or "assailant" in r:
            return "attacker-of"
        if "victim" in r or "target" in r or "injured" in r:
            return "victim-of"
        if "government" in r or "state" in r:
            return "actor-in-state"
        if "participant" in r or "witness" in r or "reported" in r:
            return "participant-in"
        return None

    def _parse_datetime(self, s: Optional[str]) -> Optional[datetime]:
        if not s:
            return None
        # Basic ISO8601 handling. Convert trailing Z to +00:00 for fromisoformat
        try:
            ss = s.strip()
            if ss.endswith("Z"):
                ss = ss[:-1] + "+00:00"
            return datetime.fromisoformat(ss)
        except Exception:
            return None


def map(event: ExtractedEventOutput):
    """Compatibility wrapper for the previous functional API named `map`.

    Returns the primary event object (same behavior as before).
    """
    mapper = OntologyMapper()
    evt, _aux = mapper.map(event)
    return evt
