# Copyright (c) 2026 Polymath Analytics. All rights reserved.
# Unauthorized copying of this file, via any medium is strictly prohibited.
# Proprietary and confidential.
# Written by Sven Steinbauer <<email>>.
import asyncio
import logging
import random
import time
import datetime
import re
import os
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple
import dotenv
from dotenv import load_dotenv

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import sys
# Ensure project root is in sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
print(PROJECT_ROOT)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
from data.storage.osint_google_news_db import GoogleOSINTDB


# ---------------------------
# Logging Configuration
# ---------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
)
logger = logging.getLogger("custom-search")

# ============================================================
# Base Google Service
# ============================================================

class BaseGoogleService(ABC):
    """
    Abstract base class for Google API services.

    Responsibilities:
    - Client creation
    - Retry & backoff handling
    - Error classification
    """

    MAX_RETRIES = 5
    INITIAL_BACKOFF = 1.0  # seconds

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.logger = logging.getLogger(self.__class__.__name__)
        self._service = None

    @abstractmethod
    def _build_service(self):
        """Create and return a googleapiclient service."""
        raise NotImplementedError

    @property
    def service(self):
        if self._service is None:
            self._service = self._build_service()
        return self._service

    # ------------------------
    # Retry helpers
    # ------------------------

    @staticmethod
    def _should_retry(error: HttpError) -> bool:
        if error.resp is None:
            return True
        return error.resp.status in {429, 500, 502, 503, 504}

    def _sleep_with_backoff(self, attempt: int):
        delay = self.INITIAL_BACKOFF * (2 ** attempt)
        delay += random.uniform(0, delay * 0.25)
        self.logger.warning("Retrying in %.2f seconds", delay)
        time.sleep(delay)

    def _execute_with_retries(self, func):
        for attempt in range(self.MAX_RETRIES):
            try:
                return func()
            except HttpError as e:
                self.logger.error(
                    "HTTP error (status=%s)",
                    getattr(e.resp, "status", "unknown"),
                )
                if self._should_retry(e) and attempt < self.MAX_RETRIES - 1:
                    self._sleep_with_backoff(attempt)
                    continue
                raise
            except Exception:
                self.logger.exception("Unexpected error")
                raise

        return None

# ============================================================
# Custom Search Service
# ============================================================

class CustomSearchService(BaseGoogleService):
    """
    Google Custom Search API client with async pagination support.
    """

    RESULTS_PER_PAGE = 10
    MAX_RESULTS = 100

    def __init__(
        self,
        api_key: str,
        cx_id: str,
        *,
        language: Optional[str] = None,
        date_restrict: Optional[str] = "d1",
    ):
        super().__init__(api_key)
        self.cx_id = cx_id
        self.language = language
        self.date_restrict = date_restrict
        self.sort = "date" if self.date_restrict else None

    # ------------------------
    # Service creation
    # ------------------------

    def _build_service(self):
        self.logger.info("Creating Custom Search API client")
        return build(
            "customsearch",
            "v1",
            developerKey=self.api_key,
            cache_discovery=False,  # required for containers
        )

    # ------------------------
    # Sync fetch (internal)
    # ------------------------

    def _fetch_page(
        self,
        query: str,
        start: int,
    ) -> List[Dict[str, Any]]:
        self.logger.debug("Fetching page starting at %d", start)

        def request():
            params = {
                "q": query,
                "cx": self.cx_id,
                "num": self.RESULTS_PER_PAGE,
                "start": start,
            }

            if self.language:
                params["lr"] = self.language

            if self.date_restrict:
                params["dateRestrict"] = self.date_restrict

            if self.sort:
                params["sort"] = self.sort

            return self.service.cse().list(**params).execute()

        response = self._execute_with_retries(request)
        return response.get("items", []) if response else []

    # ------------------------
    # Async public API
    # ------------------------

    async def search(self, query: str) -> List[Dict[str, Any]]:
        """
        Perform a paginated async search.

        Returns:
            List of search result items (max 100).
        """
        self.logger.info("Starting search: %s", query)

        loop = asyncio.get_running_loop()
        results: List[Dict[str, Any]] = []

        start = 1
        max_start = self.MAX_RESULTS - self.RESULTS_PER_PAGE + 1

        while start <= max_start:
            self.logger.info("Requesting results starting at %d", start)

            page_items = await loop.run_in_executor(
                None,
                self._fetch_page,
                query,
                start,
            )

            if not page_items:
                self.logger.info("No more results returned")
                break

            results.extend(page_items)
            start += self.RESULTS_PER_PAGE

        self.logger.info("Search complete: %d results", len(results))
        return results

# ---------------------------
# Configuration
# ---------------------------
found_dotenv = dotenv.find_dotenv()
if found_dotenv:
    load_dotenv()
    API_KEY = os.getenv("GCP_API_KEY")
    CX_ID   = os.getenv("search_engine_ID")
    DB_USER = os.getenv("DB_USER") # or default user 'postgres'
    DB_PW = os.getenv("DB_PW") # edit the password if you switch to the default user 'postgres'; I setup different passwords.
    DB_HOST = "host.docker.internal"
    DB_PORT = os.getenv("DB_PORT")
    DB_NAME = os.getenv("DB_NAME")

# ============================================================
# Example Usage
# ============================================================

async def main(q: Tuple[str], date_restriction: Optional[str]="d1", language_restriction: Optional[str]=None, table_name: str="osint_news"):
    service = CustomSearchService(
        api_key=API_KEY,
        cx_id=CX_ID,
        date_restrict=date_restriction,
        language=language_restriction,
    )

    try:
        results = await service.search(q)
    except Exception:
        logging.exception("Search failed")
        return

    # PostgreSQL initialisieren
    db = GoogleOSINTDB(dbname=DB_NAME, user=DB_USER, password=DB_PW, host=DB_HOST)
    # Tabelle erstellen, falls nicht vorhanden
    db.execute_query(f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            id SERIAL PRIMARY KEY,
            search_time TEXT,
            display_link TEXT,
            snippet TEXT,
            title TEXT,
            link TEXT,
            description TEXT
        )
    """)

    batch_values = []
    
    for idx, item in enumerate(results, 1):
        match = re.search(r'^(.*?)(?:\s*\.\.\.)', item.get("snippet"))
        # description aus metatags
        pagemap = item.get("pagemap", {})
        metatags = pagemap.get("metatags")
        desc = metatags[0].get("og:description") if metatags else None
        logging.info(
            "[%02d] [%s] %s: %s (%s)\n%s",
            idx,
            item.get("displayLink"),
            match.group(1) if match else "No time given",
            item.get("title"),
            item.get("link"),
            desc,
        )
        
        batch_values.append((
            datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            item.get("displayLink"),
            match.group(1) if match else "No time given",
            item.get("title"),
            item.get("link"),
            desc,
        ))
        # Batch insert
        if batch_values:
            db.batch_insert(
                table=table_name,
                columns=["search_time", "display_link", "snippet", "title", "link", "description"],
                values=batch_values
            )
            
    db.close_pool()
        

if __name__ == "__main__":
    query = (
        "china taiwan"
    )
    asyncio.run(main(q=query, date_restriction="w1"))