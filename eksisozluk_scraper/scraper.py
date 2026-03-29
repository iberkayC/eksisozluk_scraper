"""Scrape threads from eksisozluk.com."""

import asyncio
import logging
import math
from typing import Any

import tenacity
from bs4 import BeautifulSoup
from curl_cffi import requests

from . import console

logger = logging.getLogger(__name__)

HTTP_OK = 200
ENTRIES_PER_PAGE = 10


class EksiSozlukScraper:
    """Scraper for EksiSozluk. Handle the scraping logic of threads."""

    def __init__(self, base_url: str) -> None:
        """Initialize the scraper with the base URL.

        Args:
            base_url (str): The base URL of EksiSozluk.

        """
        self.base_url = base_url

    async def _fetch_first_page(
        self,
        session: requests.AsyncSession,
        url: str,
    ) -> tuple[int, list[dict[str, Any]]]:
        """Fetch the first page, return (page_count, entries)."""
        try:
            response = await self._fetch_page(session, url)
            if response.status_code != HTTP_OK:
                logger.error(
                    "Failed to fetch %s (status %s)",
                    url,
                    response.status_code,
                )
                return 1, []
            soup = BeautifulSoup(response.text, "lxml")
            pager_div = soup.find("div", class_="pager")
            page_count = (
                int(pager_div["data-pagecount"])
                if pager_div and "data-pagecount" in pager_div.attrs
                else 1
            )
            entries = soup.find_all(id="entry-item")
            return page_count, [self._parse_entry(e) for e in entries]
        except Exception:
            logger.exception("Unexpected error fetching first page %s", url)
            return 1, []

    def _parse_entry(self, entry: BeautifulSoup) -> dict[str, Any]:
        """Parse an entry into a content/author/date dictionary.

        Args:
            entry (BeautifulSoup): an entry in the thread

        """
        content_div = entry.find(class_="content")
        # Replace shortened link text with the full URL from href
        for a in content_div.find_all("a", href=True):
            if a["href"].startswith("http"):
                a.string = a["href"]
        content = content_div.get_text(separator=" ").strip()
        author = entry.find(class_="entry-author").text.strip()
        entry_date_text = entry.find(class_="entry-date").text.strip()

        if "~" in entry_date_text:
            date_created, last_changed = [
                part.strip() for part in entry_date_text.split("~")
            ]
        else:
            date_created = entry_date_text
            last_changed = None

        return {
            "Content": content,
            "Author": author,
            "Date Created": date_created,
            "Last Changed": last_changed,
        }

    @tenacity.retry(
        retry=tenacity.retry_if_exception_type(requests.RequestsError),
        wait=tenacity.wait_exponential(),
        stop=tenacity.stop_after_attempt(8) | tenacity.stop_after_delay(300),
        reraise=True,
    )
    async def _fetch_page(
        self,
        session: requests.AsyncSession,
        url: str,
    ) -> requests.Response:
        """Fetch a page with retries on network errors."""
        return await session.get(url)

    async def scrape_page(
        self,
        session: requests.AsyncSession,
        url: str,
        semaphore: asyncio.Semaphore,
    ) -> list[dict[str, Any]]:
        """Scrape a page and return its entries.

        Args:
            session (requests.AsyncSession): session to make requests
            url (str): url of the page to scrape
            semaphore (asyncio.Semaphore): limits concurrent requests

        """
        async with semaphore:
            try:
                response = await self._fetch_page(session, url)
                if response.status_code != HTTP_OK:
                    logger.error(
                        "Failed to fetch %s (status %s)",
                        url,
                        response.status_code,
                    )
                    return []
                text = response.text
                soup = BeautifulSoup(text, "lxml")
                entries = soup.find_all(id="entry-item")
                return [self._parse_entry(entry) for entry in entries]
            except Exception:
                logger.exception("Unexpected error in scrape_page %s", url)
                return []

    async def scrape_thread(
        self,
        session: requests.AsyncSession,
        thread: str,
        max_concurrent_requests: int = 15,
        max_entries: int | None = None,
    ) -> list[dict[str, Any]]:
        """Scrape a thread and return all entries.

        Args:
            session (requests.AsyncSession): session to make requests
            thread (str): thread slug (url path after /)
            max_concurrent_requests (int): max concurrent requests
            max_entries (int | None): stop after collecting this many entries

        """
        semaphore = asyncio.Semaphore(max_concurrent_requests)

        thread_url = self.base_url + thread
        number_of_pages, first_page_entries = await self._fetch_first_page(
            session,
            thread_url,
        )

        if max_entries:
            pages_needed = min(
                number_of_pages, math.ceil(max_entries / ENTRIES_PER_PAGE),
            )
        else:
            pages_needed = number_of_pages

        console.thread_start(thread, pages_needed)

        if max_entries and len(first_page_entries) >= max_entries:
            console.page_done(thread, 1, pages_needed, max_entries, max_entries)
            return first_page_entries[:max_entries]

        running_total = len(first_page_entries)
        console.page_done(
            thread,
            1,
            pages_needed,
            len(first_page_entries),
            running_total,
        )

        async def _scrape_and_report(page_num: int) -> list[dict[str, Any]]:
            nonlocal running_total
            entries = await self.scrape_page(
                session,
                thread_url + "?p=" + str(page_num),
                semaphore,
            )
            running_total += len(entries)
            console.page_done(
                thread,
                page_num,
                pages_needed,
                len(entries),
                running_total,
            )
            return entries

        tasks = [_scrape_and_report(page) for page in range(2, pages_needed + 1)]
        results = await asyncio.gather(*tasks)

        all_entries = first_page_entries + [entry for page in results for entry in page]
        if max_entries:
            return all_entries[:max_entries]
        return all_entries
