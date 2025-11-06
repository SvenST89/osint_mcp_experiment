# Copyright (c) 2025 Polymath Analytics. All rights reserved.
# Unauthorized copying of this file, via any medium is strictly prohibited.
# Proprietary and confidential.
# Written by Sven Steinbauer <<email>>.
import asyncio
import json
import os
import sys
from typing import Dict, Any, List
# Ensure project root is in sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from data.service.osm_client import AsyncOverpassClient
from src.osint_assistant.tools.overpass.overpass_tool import OverpassTool

class OverpassToolServer:
    """
    MCP / Agentic-compatible server exposing the OverpassTool as callable functions.
    """
    
    def __init__(self, max_concurrent: int = 3):
        self.client = AsyncOverpassClient(max_concurrent=max_concurrent)
        self.tool = OverpassTool(self.client)
        self._tools = {
            "query_region": {
                "name": "query_region",
                "description": "Query OpenStreetMap via Overpass API for a region or bounding box.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "area_name": {"type": "string", "description": "Name of the city/region to query."},
                        "bbox": {"type": "array", "items": {"type": "number"}, "description": "Bounding box [south, west, north, east]."},
                        "tags": {"type": "object", "description": "Key-value pairs of OSM tags to filter by."},
                        "element_types": {"type": "array", "items": {"type": "string"}, "description": "OSM element types ['node', 'way', 'relation']."},
                        "output": {"type": "string", "enum": ["json", "csv"], "default": "json"},
                        "parse_geometry": {"type": "boolean", "default": True}
                    },
                    "required": ["area_name", "tags"]
                }
            }
        }

    def list_tools(self) -> List[Dict[str, Any]]:
        """Return metadata for all exposed tools."""
        return list(self._tools.values())

    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call a tool by name with JSON arguments."""
        if name not in self._tools:
            raise ValueError(f"Tool '{name}' not found.")

        if name == "query_region":
            return await self.tool.query_region(**arguments)
        else:
            raise ValueError(f"Tool '{name}' is not implemented.")
        
# Example: Running locally for debugging
if __name__ == "__main__":
    async def main():
        server = OverpassToolServer()
        print("Available tools:", json.dumps(server.list_tools(), indent=2))

        result = await server.call_tool("query_region", {
            "area_name": "Berlin",
            "tags": {"amenity": "restaurant"},
            "element_types": ["node", "way"],
            "parse_geometry": True
        })

        print(json.dumps(result, indent=2)[:2000])  # truncate for readability

    asyncio.run(main())