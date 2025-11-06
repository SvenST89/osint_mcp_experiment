# Copyright (c) 2025 Polymath Analytics. All rights reserved.
# Unauthorized copying of this file, via any medium is strictly prohibited.
# Proprietary and confidential.
# Written by Sven Steinbauer <<email>>.

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class OverpassQueryParams(BaseModel):
    """Input parameters for Overpass API query"""
    tags: Dict[str, str] = Field(..., description="Key-value pairs of OSM tags to filter by")
    area_name: str = Field(..., description="City or region name")
    bbox: Optional[List[float]] = Field(None, description="Bounding box [south, west, north, east]")
    element_types: Optional[List[str]] = Field(None, description="OSM element types, e.g. ['node','way', 'relation']")
    output: str = Field("json", description="Output format, usually 'json' or 'csv'")
    parse_geometry: bool = Field(True, description="Parse into geometries if True")

class OverpassFeature(BaseModel):
    """A simplified representation of an OSM feature"""
    id: int
    type: Optional[str]
    tags: Optional[Dict[str, Any]]
    geometry: Optional[Dict[str, Any]]  # can store GeoJSON geometry

class OverpassQueryResult(BaseModel):
    """Output returned by the MCP tool"""
    area_name: Optional[str]
    bbox: Optional[List[float]]
    element_types: Optional[List[str]]
    count: int
    features: List[OverpassFeature]
