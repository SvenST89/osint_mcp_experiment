# Overpass MCP Tool

This project provides a Python-based tool to query OpenStreetMap data via the Overpass API and expose it through both MCP (Model Context Protocol) and a lightweight REST endpoint for testing or integration. It allows asynchronous querying of OSM nodes, ways, and optionally relations, with tag-based filtering and bounding box or area-based queries. Geometries are parsed into GeoPandas objects and returned as fully JSON-serializable Pydantic models.

## Program Structure

- **`OverpassQuery`**: Builds and executes Overpass API queries. Supports filtering by tags, bounding boxes, or area names, with JSON or CSV output. Can parse geometries into Shapely objects and handles retries and Overpass server availability.

- **`AsyncOverpassClient`**: Asynchronous execution of multiple Overpass queries using `aiohttp` with concurrency control.

- **`OverpassStructuredTool`**: Wraps the Overpass client and provides a `query_region` method returning structured `OverpassFeature` Pydantic objects. Can be used both as an MCP tool and in a REST endpoint.

- **MCP Server**: Uses `FastMCP` to expose the tool via MCP. The `query_region` method is registered with `@mcp.tool()`. Supports `stateless_http` transport for streamable agent calls.

- **REST Endpoint**: A Starlette-based endpoint (`/query_region`) provides a lightweight HTTP interface for testing or integration. Includes full JSON sanitization of geometries and tags.

### Runnable Server Example

```python
# Instantiate MCP server
mcp = FastMCP(
    name="Overpass MCP Server",
    description="Overpass OSM Query Tool with Structured Output",
    stateless_http=True,
    host="127.0.0.1",
    port=8008
)

# Instantiate tool logic
client = AsyncOverpassClient(max_concurrent=3)
overpass_tool = OverpassStructuredTool(client)

# MCP tool registration
@mcp.tool()
async def query_region(params: OverpassQueryParams, ctx: Context):
    return await overpass_tool.query_region(params, ctx)

# REST endpoint setup
async def rest_query_region(request: Request):
    payload = await request.json()
    params = OverpassQueryParams(**payload)
    result = await overpass_tool.query_region(params, ctx=None)
    safe_result = sanitize_obj(result.model_dump())  # fully JSON-serializable
    return JSONResponse(safe_result, status_code=200)

rest_app = Starlette(routes=[Route("/query_region", rest_query_region, methods=["POST"])])

# Run both MCP and REST servers concurrently
async def main():
    from uvicorn import Config, Server
    mcp_task = asyncio.create_task(mcp.run_streamable_http_async())
    rest_server = Server(Config(app=rest_app, host="127.0.0.1", port=8010, log_level="info"))
    rest_task = asyncio.create_task(rest_server.serve())
    await asyncio.gather(mcp_task, rest_task)

if __name__ == "__main__":
    print("🚀 Overpass MCP running on 127.0.0.1:8008")
    print("🌍 REST API available on 127.0.0.1:8010/query_region")
    asyncio.run(main())
```

## Lessons Learned (so far...)

### JSON Serialization and Shapely Geometries

Shapely objects cannot be returned directly in JSON. All geometries must be converted to GeoJSON dictionaries using `mapping(geom)`.

### Coordinate Validation

OSM data may contain invalid coordinates (`NaN`, `Infinity`) or extremely large floats. A recursive validation is necessary for nested geometries (Polygons, MultiPolygons, LineStrings).

### Tag and Metadata Sanitization
Tags and other numeric fields may contain `NaN`, `Inf`, or NumPy numeric types (`numpy.float64`, `numpy.int64`) which are not JSON-compliant. All numbers should be **converted to native Python types**, with invalid values replaced by `None`.

### NumPy Scalars Are Problematic
Even finite NumPy floats or integers cannot be serialized directly by `json.dumps()`, which is used internally in `JSONResponse()` or `shapely.to_geojson()` (was used initially in the code for feature creation). Conversion to Python `float` or `int` is required.

### MCP Context Handling
When called via REST, `ctx: Context` may be `None`. Logging or other context-dependent operations should be guarded or use a dummy context to avoid *runtime errors*.

### Safe Recursive Serialization
Using a **recursive sanitization function ensures that geometries, tags, and all nested structures are fully JSON-safe**. This guarantees compatibility for MCP endpoints, REST APIs, Postman, and browser testing.

### Concurrent Server Setup
Running MCP and REST servers concurrently in the same Python process is feasible using `asyncio.create_task` and `asyncio.gather`, enabling both agent workflows and HTTP testing simultaneously.

## Open Issues (upcoming...)

### 1. Data Retrieval & Processing
- [ ] Filter in OverpassQuery for required columns using parameters
- [ ] Vectorize the iteration step when building OverpassFeature
- [ ] Adapt pydantic fields for the vectorized approach
- [ ] Implement dictionary unpacking as alternative for building OverpassFeature
- [ ] Define hard-typed Enum types for fields used in filtering step from OverpassFeature geo dataframe
- [ ] Further Abstraction / Base Classes MCP + Tool Usage

### 2. Testing Infrastructure
- [ ] Set up internal Python code testing suite for code execution testing
- [ ] Implement check-loop that tests generated code in test suite before execution
- [ ] Unit Tests

### 3. LLM Chain Implementation
- [ ] OpenAI + Anthropic API chat endpoint setup
- [ ] Overpass Tool connection to OpenAI LLM
- [ ] Further Abstraction / Base Classes for LLM
- [ ] Set up LLM chain using OverpassFeature tool to generate geo dataframe
- [ ] Create prompt templates for tool execution (generates geo dataframe) + analysis step (analyzes geo dataframe, if requested by user) + visualization plotly graph generation
- [ ] If analysis is requested: let LLM generate analysis dataframe using groupby/count on deduced columns
- [ ] Let LLM write code for appropriate chart generation (e.g., pie chart)

### 4. Frontend Development
- [ ] Build frontend with Dash/Plotly
- [ ] Display resulting charts or analysis tables in frontend
