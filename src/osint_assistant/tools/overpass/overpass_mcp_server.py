# Copyright (c) 2025 Polymath Analytics. All rights reserved.
# Unauthorized copying of this file, via any medium is strictly prohibited.
# Proprietary and confidential.
# Written by Sven Steinbauer <<email>>.

import asyncio
import os
import sys
# Ensure project root is in sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# to layer a normal http interface on top of the mcp tool
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route
from starlette.requests import Request
from mcp.server.fastmcp import FastMCP, Context
from data.service.osm_client import AsyncOverpassClient
from data.models.mcp_models import OverpassQueryParams
from src.osint_assistant.tools.overpass.overpass_struct_tool import OverpassStructuredTool
from src.osint_assistant.tools.utils import sanitize_obj

# instantiate the mcp server
mcp = FastMCP(name="Overpass MCP Server", stateless_http=True, host="127.0.0.1", port=8008)

# Instantiate tool logic
client = AsyncOverpassClient(max_concurrent=3)
overpass_tool = OverpassStructuredTool(client)

#***** MCP TOOL REGISTRATION *****#
# Registering method as an MCP tool manually
@mcp.tool()
async def query_region(params: OverpassQueryParams, ctx: Context):
    """Delegates to OverpassTool.query_region"""
    return await overpass_tool.query_region(params, ctx)

#***** REST ENDPOINT SETUP *****#
# REST Endpoint for MCP tool for testing purposes.
# Starlette is the lightweight ASGI core that FastAPI itself builds upon. 

async def rest_query_region(request: Request):
    """Expose the MCP tool as a simple REST endpoint."""
    try:
        payload = await request.json()
        params = OverpassQueryParams(**payload)
        result = await overpass_tool.query_region(params, ctx=None)
        
        # make sure the result is fully JSON-serializable
        safe_result = sanitize_obj(result.model_dump())
        #print("Sanitized REST query_region result:", safe_result)
        return JSONResponse(safe_result, status_code=200)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=400)


rest_app = Starlette(
    debug=True,
    routes=[
        Route("/query_region", rest_query_region, methods=["POST"]),
    ],
)

# Run both servers concurrently
async def main():
    from uvicorn import Config, Server

    # MCP server in background
    mcp_task = asyncio.create_task(mcp.run_streamable_http_async())

    # REST API with Starlette on another port
    rest_config = Config(app=rest_app, host="127.0.0.1", port=8010, log_level="info")
    rest_server = Server(rest_config)
    rest_task = asyncio.create_task(rest_server.serve())

    await asyncio.gather(mcp_task, rest_task)


if __name__ == "__main__":
    print("🚀 Overpass MCP running on 127.0.0.1:8008 (MCP)")
    print("🌍 REST API available on 127.0.0.1:8010/query_region")
    asyncio.run(main())