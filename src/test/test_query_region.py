import httpx

osm_url = "http://127.0.0.1:8010/query_region"

# define the payload for the overpass query params
payload = {
    "area_name": "Berlin",
    "tags": {"amenity": "restaurant"},
    "element_types": ["node", "way"],
    "parse_geometry": True
}

# send post request to the locally running server
try:
    response = httpx.post(osm_url, json=payload, timeout=60.0)
    response.raise_for_status() # raise errors for http codes 4xx/5xx
    print("Response JSON:", response.json())
except httpx.HTTPError as e:
    print(f"HTTP error occurred: {e}")
except httpx.RequestError as e:
    print(f"Request error occurred: {e}")
except httpx.HTTPStatusError as e:
    print(f"HTTP status error occurred: {e}")
except httpx.TimeoutException as e:
    print(f"Request timed out: {e}")