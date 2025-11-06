## Copyright (c) 2025 Polymath Analytics. All rights reserved.
# Unauthorized copying of this file, via any medium is strictly prohibited.
# Proprietary and confidential.
# Written by Sven Steinbauer <<email>>.
import aiohttp
import asyncio
from typing import List
import pandas as pd
from io import StringIO
from data.input.osm_input import OverpassQuery

class AsyncOverpassClient:
    def __init__(self, max_concurrent: int = 5):
        self.semaphore = asyncio.Semaphore(max_concurrent)

    async def _run_query(self, session, query_obj: OverpassQuery):
        await self.semaphore.acquire()
        try:
            query = query_obj._build_query()
            for _ in range(query_obj.max_retries):
                try:
                    async with session.get(query_obj.server, params={"data": query}) as resp:
                        if resp.status == 200:
                            text = await resp.text()
                            if query_obj.output == "csv":
                                return pd.read_csv(StringIO(text))
                            elif query_obj.output == "json":
                                data = await resp.json()
                                return query_obj.json_to_geodataframe(data) if query_obj.parse_geometry else data
                            else:
                                return text
                        await asyncio.sleep(query_obj.retry_delay)
                except aiohttp.ClientError:
                    await asyncio.sleep(query_obj.retry_delay)
        finally:
            self.semaphore.release()

    async def run_all(self, queries: List[OverpassQuery]):
        async with aiohttp.ClientSession() as session:
            return await asyncio.gather(*(self._run_query(session, q) for q in queries))
        
# if __name__ == "__main__":
#     queries = [
#         OverpassQuery(
#             area_name="Berlin",
#             tags={"amenity": "restaurant"},
#             output="json",
#             parse_geometry=True,
#             element_types=["node", "way"]
#         ),
#         OverpassQuery(
#             area_name="München",
#             tags={"amenity": "hospital|clinic"},
#             output="json",
#             parse_geometry=True,
#             element_types=["node", "way"]
#         )
#     ]

#     client = AsyncOverpassClient(max_concurrent=2)

#     # Run inside an asyncio context
#     results = asyncio.run(client.run_all(queries))

#     # Each result is a pandas.DataFrame
#     for df in results:
#         print(df.head())

