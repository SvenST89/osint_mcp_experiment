# Copyright (c) 2025 Polymath Analytics. All rights reserved.
# Unauthorized copying of this file, via any medium is strictly prohibited.
# Proprietary and confidential.
# Written by Sven Steinbauer <<email>>.

from shapely.geometry import mapping
from mcp.server.fastmcp import Context
from typing import Optional
import geopandas as gpd
# Ensure project root is in sys.path
# PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
# if PROJECT_ROOT not in sys.path:
#     sys.path.insert(0, PROJECT_ROOT)

from data.models.mcp_models import OverpassQueryParams, OverpassQueryResult, OverpassFeature
from data.input.osm_input import OverpassQuery
from data.service.osm_client import AsyncOverpassClient


class OverpassStructuredTool:
    """
    Defines the callable interface for Overpass queries that can be exposed as an MCP (model context protocol) or agent tool, with a structured pydantic data model as output.
    """
    
    def __init__(self, client: AsyncOverpassClient):
        self.client = client

    async def query_region(
        self,
        params: OverpassQueryParams,
        ctx: Optional[Context] = None # make context optional for the REST endpoint calls with starlette (otherwise a POST request will raise an error due to missing ctx)
    ) -> OverpassQueryResult:
        """
        Execute an Overpass query for a region or bounding box with specified tags, i.e. the semantic data such as amenities, highways, etc. that you want to retrieve.
        
        Args:
            params: OverpassQueryParams defining the query parameters; check the osm_input.OverpassQuery for details.
            ctx: Context is an MCP context object that exists only when the tool is called through MCP. 
                - When you call your tool via REST, ctx is None — so any calls to ctx.info(), ctx.warn(), etc. fail.
                - This is why you get 400 Bad Request: Starlette/Pydantic validated the input fine, but the tool crashed internally.
        """
        if ctx is not None:
            await ctx.info(f"Preparing OverpassQuery for {params.area_name or params.bbox}")
        
        query = OverpassQuery(
            area_name=params.area_name,
            tags=params.tags or {},
            bbox=tuple(params.bbox) if params.bbox else None,
            element_types=params.element_types or ["node", "way", "relation"],
            output=params.output,
            parse_geometry=params.parse_geometry
        )

        # take care, if parse_geometry is True, the result will be a GeoDataFrame, else simply a json/dict.
        results = await self.client.run_all([query])
        result = results[0]

        if isinstance(result, gpd.GeoDataFrame):
            features = []
            for _, row in result.iterrows():
                # according to: /workspaces/mcplanggraph/data/input/osm_input.py
                # there should be only valid geometries in the received GeoDataFrame.
                # Directly convert shapely geometry to a dict.
                geojson_geom = mapping(row.geometry) if row.geometry else None
                #print(f"Geometry for feature ID {row['id']}: {geojson_dict}")
                feat = OverpassFeature(
                    id=int(row["id"]),
                    type=row.get("amenity") or "feature",
                    tags={k: v for k, v in row.items() if k not in ["id", "geometry"]},
                    geometry=geojson_geom
                )
                features.append(feat)
            return OverpassQueryResult(
                area_name=params.area_name,
                bbox=params.bbox,
                element_types=params.element_types,
                count=len(features),
                features=features
            )
        else:
            return OverpassQueryResult(area_name=params.area_name, bbox=params.bbox, element_types=params.element_types, count=0, features=[])