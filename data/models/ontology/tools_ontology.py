import sys
from pathlib import Path
# Ensure repository root is on sys.path so both package and script execution work.
# This file is at: <repo>/data/models/ontology/ontology_description.py
# repo root is three parents up from this file.
_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
	sys.path.insert(0, str(_REPO_ROOT))
from data.models.ontology.base_stix import StixObject
from typing import Optional

class Tool(StixObject):
    def __init__(
        self,
        *,
        name: str,
        category: str,
        description: Optional[str] = None,
        **kwargs,
    ):
        self._name = name
        self._category = category
        self._description = description
        super().__init__(**kwargs)

    def _identity_material(self) -> str:
        return f"{self._category}:{self._name.lower()}"

#=========================#
# WEAPONS
#=========================#
class Weapon(Tool):
    def __init__(self, *, name: str, weapon_type: str, **kwargs):
        self._weapon_type = weapon_type
        super().__init__(name=name, category="weapon", **kwargs)

    def _identity_material(self) -> str:
        return f"weapon:{self._weapon_type}:{self._name.lower()}"

#-------------------------
# firearms
class Firearm(Weapon):
    def __init__(self, *, name: str, **kwargs):
        super().__init__(name=name, weapon_type="firearm", **kwargs)

class Handgun(Firearm): pass
class Rifle(Firearm): pass
class Shotgun(Firearm): pass
class AutomaticWeapon(Firearm): pass

#-------------------------
# melee weapons
class MeleeWeapon(Weapon):
    def __init__(self, *, name: str, **kwargs):
        super().__init__(name=name, weapon_type="melee", **kwargs)

class Knife(MeleeWeapon): pass
class Machete(MeleeWeapon): pass
class Club(MeleeWeapon): pass

#-------------------------
# explosives
class Explosive(Weapon):
    def __init__(self, *, name: str, **kwargs):
        super().__init__(name=name, weapon_type="explosive", **kwargs)

class IED(Explosive): pass
class Grenade(Explosive): pass
class CarBomb(Explosive): pass

#=========================#
# VEHICLES
#=========================#
class Vehicle(Tool):
    def __init__(self, *, name: str, vehicle_type: str, **kwargs):
        self.vehicle_type = vehicle_type
        super().__init__(name=name, category="vehicle", **kwargs)

class ArmoredVehicle(Vehicle): pass
class CivilianVehicle(Vehicle): pass
class UnmannedVehicle(Vehicle): pass

#=========================#
# CYBER
#=========================#
class CyberTool(Tool):
    def __init__(self, *, name: str, **kwargs):
        super().__init__(name=name, category="cyber", **kwargs)

class Malware(CyberTool): pass
class ExploitKit(CyberTool): pass
class PhishingKit(CyberTool): pass
