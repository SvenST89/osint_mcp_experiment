# Copyright (c) 2025 Polymath Analytics. All rights reserved.
# Unauthorized copying of this file, via any medium is strictly prohibited.
# Proprietary and confidential.
# Written by Sven Steinbauer <<email>>.

import json
from typing import Dict, Any, List, Optional, Union

from data.input.osm_input import OverpassQuery
from data.service.osm_client import AsyncOverpassClient

class OverpassTool:
    """
    Defines the callable interface for Overpass queries that can be exposed as an MCP (model context protocol) or agent tool.
    """
    
    def __init__(self, client: AsyncOverpassClient):
        self.client = client
    
    async def query_region(
        self,
        area_name: str,
        tags: Dict[str, Union[str, bool]],
        bbox: Optional[List[float]] = None,
        element_types: Optional[List[str]] = None,
        output: str = "json",
        parse_geometry: bool = True,        
    ) -> Dict[str, Any]:
        """
        Execute an Overpass query for a region or bounding box with specified tags, i.e. the semantic data such as amenities, highways, etc. that you want to retrieve.
        """
        
        query = OverpassQuery(
            area_name=area_name,
            bbox=tuple(bbox) if bbox else None,
            tags=tags or {},
            element_types=element_types or ["node", "way", "relation"],
            output=output,
            parse_geometry=parse_geometry
        )

        # take care, if parse_geometry is True, the result will be a GeoDataFrame, else simply a json/dict.
        results = await self.client.run_all([query])
        result = results[0]

        # serialize to JSON
        if hasattr(result, "to_json"):
            return json.loads(result.to_json())
        elif isinstance(result, dict):
            return result
        else:
            return {"raw": str(result)}