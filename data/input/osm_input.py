# Copyright (c) 2025 Polymath Analytics. All rights reserved.
# Unauthorized copying of this file, via any medium is strictly prohibited.
# Proprietary and confidential.
# Written by Sven Steinbauer <<email>>.
import requests
import time
import math
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point, Polygon, LineString, mapping
from typing import List, Dict, Tuple, Optional, Union, Any
from io import StringIO


class OverpassQuery:
    def __init__(
        self,
        area_name: str,
        tags: Dict[str, Union[str, bool]],
        bbox: Optional[Tuple[float, float, float, float]] = None,
        element_types: List[str] = ["node", "way", "relation"],
        timeout: int = 25,
        output: str = "json",
        csv_fields: Optional[List[str]] = None,
        parse_geometry: bool = False,
        server: str = "https://overpass-api.de/api/interpreter",
        max_retries: int = 3,
        retry_delay: int = 10
    ):
        self.tags = tags
        self.bbox = bbox
        self.area_name = area_name
        self.element_types = element_types
        self.timeout = timeout
        self.output = output
        self.csv_fields = csv_fields
        self.server = server
        self.parse_geometry = parse_geometry
        self.max_retries = max_retries
        self.retry_delay = retry_delay

    def _format_tags(self) -> str:
        tag_queries = []
        for k, v in self.tags.items():
            if v is True:
                tag_queries.append(f'[{k}]')
            elif v is False:
                tag_queries.append(f'[!{k}]')
            elif isinstance(v, str):
                if v.startswith("~"):
                    tag_queries.append(f'[{k}~"{v[1:]}"]')
                elif "|" in v:
                    tag_queries.append(f'[{k}~"^{v}$"]')  # regex for OR
                else:
                    tag_queries.append(f'[{k}="{v}"]')
        return "".join(tag_queries)

    def _build_area_query(self) -> str:
        if not self.area_name:
            return ""
        return f'area[name="{self.area_name}"][admin_level];'

    def _build_main_query(self) -> str:
        tag_filter = self._format_tags()

        if self.bbox:
            location = f"({','.join(map(str, self.bbox))})"
        elif self.area_name:
            location = "(area)"
        else:
            raise ValueError("Either bbox or area_name must be specified.")

        return "\n".join(
            f'{et}{tag_filter}{location};' for et in self.element_types
        )

    def _build_query(self) -> str:
        area_part = self._build_area_query()
        main_part = self._build_main_query()

        if self.output == "csv" and self.csv_fields:
            csv_header = ",".join(self.csv_fields)
            return f"""
            [out:csv({csv_header})][timeout:{self.timeout}];
            {area_part}
            (
                {main_part}
            );
            out center;
            """.strip()
        elif self.output == "json" and self.parse_geometry:
            return f"""
            [out:json][timeout:{self.timeout}];
            {area_part}
            (
                {main_part}
            );
            out geom;
            """.strip()
        else:
            return f"""
            [out:{self.output}][timeout:{self.timeout}];
            {area_part}
            (
                {main_part}
            );
            out body;
            >;
            out skel qt;
            """.strip()

    def _check_availability(self) -> bool:
        """Check if the Overpass server has free slots."""
        status_url = self.server.replace("/interpreter", "/status")
        try:
            response = requests.get(status_url, timeout=5)
            if response.status_code == 200:
                text = response.text
                if "Slot available" in text or "available now" in text:
                    return True
                elif "slots available" in text:
                    return True
                else:
                    return False
        except requests.RequestException:
            return False

    def _wait_for_slot(self, max_wait: int = 60):
        waited = 0
        while waited < max_wait:
            if self._check_availability():
                return
            time.sleep(5)
            waited += 5
        raise TimeoutError("Timed out waiting for Overpass API slot.")
            
    def is_valid_geometry(self, geom) -> bool:
        """
        Sanitizing function to check for valid geometries.
        
        Shapely geometry can contain invalid coordinates:
        - If OSM data has a node with lat or lon as NaN or Inf, then shapely.to_geojson() (or json.dumps) will fail because JSON spec does not allow NaN or Infinity!

        Overpass query / GeoPandas processing:
        - Sometimes ways or nodes are incomplete or missing geometry, e.g., el["geometry"] is empty or has bad coordinates.
        
        !!! POLYGONS !!!
        Polygons might contain interior rings with invalid coordinates as well! So we need to iterate through all coordinates.
        """
        if geom is None:
            return False

        geo_map = mapping(geom)
        coords = geo_map.get("coordinates")

        def check_coords(c):
            if isinstance(c, (float, int)):
                return math.isfinite(c)
            if isinstance(c, (list, tuple)):
                return all(check_coords(x) for x in c)
            return False

        return check_coords(coords)
    
    def json_to_geodataframe(self, osm_json: dict) -> gpd.GeoDataFrame:
        """
        Converts Overpass JSON elements into a GeoDataFrame, safely filtering invalid geometries.
        Each row includes a sanitized geometry and tags.
        """
        elements = osm_json.get("elements", [])
        records: List[Dict[str, Any]] = []

        if not elements:
            # Return empty GeoDataFrame
            return gpd.GeoDataFrame(columns=["id", "tags", "geometry"], geometry="geometry", crs="EPSG:4326")

        for el in elements:
            try:
                geom = None
                if el["type"] == "node":
                    if "lat" in el and "lon" in el:
                        geom = Point(el["lon"], el["lat"])
                elif el["type"] == "way":
                    coords = [(pt["lon"], pt["lat"]) for pt in el.get("geometry", []) if math.isfinite(pt["lon"]) and math.isfinite(pt["lat"])]
                    if not coords:
                        continue  # skip way without valid coordinates
                    if coords[0] == coords[-1] and len(coords) >= 3:
                        geom = Polygon(coords)
                    else:
                        geom = LineString(coords)
                elif el["type"] == "relation":
                    # For simplicity, skip relations (complex multipolygons)
                    continue

                if geom is None:
                    continue  # skip elements with no geometry

                if not self.is_valid_geometry(geom):
                    # Skip elements with NaN or Inf coordinates
                    continue

                tags = el.get("tags", {})
                record = {
                    "id": el["id"],
                    **tags,
                    "geometry": geom
                }
                records.append(record)

            except Exception as e:
                print(f"Skipping element ID {el.get('id')} due to error: {e}")
                continue

        return gpd.GeoDataFrame(records, geometry="geometry", crs="EPSG:4326")

    def run(self) -> Union[pd.DataFrame, gpd.GeoDataFrame, Dict, None]:
        self._wait_for_slot()
        query = self._build_query()

        for attempt in range(self.max_retries):
            try:
                response = requests.get(self.server, params={'data': query})
                if response.status_code == 200:
                    if self.output == "csv":
                        return pd.read_csv(StringIO(response.text))
                    elif self.output == "json":
                        data = response.json()
                        return self.json_to_geodataframe(data) if self.parse_geometry else data
                    else:
                        return response.text
                elif response.status_code in (429, 500, 503):
                    print(f"Retryable error ({response.status_code}), waiting...")
                    time.sleep(self.retry_delay)
                else:
                    print(f"Error {response.status_code}: {response.text}")
                    return None
            except requests.RequestException:
                print(f"Request failed, retrying ({attempt + 1}/{self.max_retries})...")
                time.sleep(self.retry_delay)

        return None


# if __name__ == "__main__":
#     # Example usage
#     query = OverpassQuery(
#         area_name="München",
#         tags={"amenity": "hospital|clinic"},
#         output="json",
#         parse_geometry=True
#     )
#     result = query.run()
#     if isinstance(result, gpd.GeoDataFrame):
#         print(result.tail())
#     else:
#         print(result)