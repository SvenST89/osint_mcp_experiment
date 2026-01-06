from __future__ import annotations

import inspect
import typing
from datetime import datetime
import sys
from pathlib import Path

# Ensure repository root is on sys.path so both package and script execution work.
# This file is at: <repo>/data/models/ontology/ontology_description.py
# repo root is three parents up from this file.
_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
	sys.path.insert(0, str(_REPO_ROOT))

try:
	# prefer absolute import so the module works when executed as a script
	from data.models.ontology import base_stix, identity_ontology, location_ontology, tools_ontology, event_ontology
except Exception:
	# fallback to package-relative import when running as part of the package
	from . import base_stix, identity_ontology, location_ontology, tools_ontology, event_ontology


_NAME_HINTS = {
	"name": "string",
	"description": "string",
	"event_type": "string",
	"subtype": "string",
	"category": "string",
	"identity_class": "string",
	"confidence": "float (0.0-1.0)",
	"occurred_at": "datetime (UTC)",
	"latitude": "float (degrees, -90 to 90)",
	"longitude": "float (degrees, -180 to 180)",
	"admin_level": "int (administrative level, e.g. 0..10)",
	"fatalities": "int (count)",
	"injured": "int (count)",
	"weapons": "List[Weapon]",
	"tools": "List[CyberTool]",
	"roles": "List[string]",
	"sources": "List[string]",
}


def _format_annotation(a) -> str:
	if a is inspect._empty:
		return "unknown"
	try:
		origin = typing.get_origin(a)
		args = typing.get_args(a)
	except Exception:
		origin = None
		args = ()
	if origin is list or origin is typing.List:
		inner = _format_annotation(args[0]) if args else "unknown"
		return f"List[{inner}]"
	if getattr(a, "__name__", None):
		return a.__name__
	# forward refs or strings
	s = str(a)
	if s.startswith("typing."):
		return s.replace("typing.", "")
	return s


def _infer_type_from_name(name: str) -> str:
	return _NAME_HINTS.get(name, "string")


def describe_module(module) -> str:
	lines = []
	lines.append(f"Module: {module.__name__}")
	classes = [c for _, c in inspect.getmembers(module, inspect.isclass) if c.__module__ == module.__name__]
	if not classes:
		lines.append("  (no classes found)")
		return "\n".join(lines)

	for cls in classes:
		lines.append("")
		lines.append(f"Class: {cls.__name__}")
		doc = (cls.__doc__ or "").strip()
		if doc:
			lines.append(f"  Doc: {doc}")

		# inspect __init__ params (skip self)
		try:
			sig = inspect.signature(cls.__init__)
		except (ValueError, TypeError):
			sig = None
		if sig:
			params = [p for p in sig.parameters.values() if p.name != "self" and p.kind in (p.POSITIONAL_OR_KEYWORD, p.KEYWORD_ONLY)]
			if params:
				lines.append("  Fields:")
				for p in params:
					annot = p.annotation
					annstr = _format_annotation(annot) if annot is not inspect._empty else _infer_type_from_name(p.name)
					default = None
					if p.default is not inspect._empty:
						default = repr(p.default)
					if default is not None:
						lines.append(f"    - {p.name}: {annstr} (default={default})")
					else:
						lines.append(f"    - {p.name}: {annstr}")
			else:
				lines.append("  (no explicit constructor fields)")

		# add common inherited STIX fields
		if issubclass(cls, base_stix.StixObject):
			lines.append(f"  Inherits from {inspect.getmro(cls)[1].__name__} with common fields:")
			lines.append("    - id: string (generated or provided)")
			lines.append("    - created: datetime (UTC)")
			lines.append("    - modified: datetime (UTC)")
			lines.append("    - confidence: float (0.0 - 1.0)")
			lines.append("    - sources: List[string]")

	return "\n".join(lines)


def build_ontology_description() -> str:
	parts = []
	parts.append("OSINT Ontology Overview")
	parts.append("")
	parts.append("Summary: This ontology models events, identities, locations, tools (including weapons and cyber tools), and base STIX-like metadata. Types, relationships and units are described below.")
	parts.append("")
	parts.append(describe_module(base_stix))
	parts.append("")
	parts.append(describe_module(identity_ontology))
	parts.append("")
	parts.append(describe_module(location_ontology))
	parts.append("")
	parts.append(describe_module(tools_ontology))
	parts.append("")
	parts.append(describe_module(event_ontology))
	parts.append("")
	parts.append("Notes:")
	parts.append("  - Strings: regular text fields (names, descriptions, categories, subtypes).")
	parts.append("  - Datetime fields are UTC; prefer ISO 8601 strings when serializing e.g. '2023-01-01T12:00:00Z'.")
	parts.append("  - Coordinates: latitude and longitude are decimal degrees (float).")
	parts.append("  - Confidence: float between 0.0 and 1.0; 0.0 = no confidence, 1.0 = fully certain.")
	parts.append("  - Collections: fields named 'weapons' or 'tools' are lists of ontology objects (Weapon, CyberTool respectively).")
	parts.append("  - Identity objects (Person, Organization, State) carry a 'name' and optional 'iso_code' for states.")

	return "\n".join(parts)


if __name__ == "__main__":
	print(build_ontology_description())

