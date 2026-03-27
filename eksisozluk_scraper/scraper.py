"""
Contains the EksiSozlukScraper class. Scrapes threads from eksisozluk.com
"""

from typing import List, Dict, Any
import logging
import asyncio

from bs4 import BeautifulSoup
from curl_cffi import requests
import tenacity

from . import console


class EksiSozlukScraper:
    """
    Scraper class for EksiSozluk. Handles the scraping logic of threads.
    """

    def __init__(self, base_url: str):
        """
        Initializes the scraper with the base URL.

        Args:
            base_url (str): The base URL of EksiSozluk.
        """
        self.base_url = base_url

    async def _fetch_first_page(
        self, session: requests.AsyncSession, url: str
    ) -> tuple[int, List[Dict[str, Any]]]:
        """Fetches the first page, returns (page_count, entries)."""
        try:
            response = await self._fetch_page(session, url)
            if response.status_code != 200:
                logging.error(
                    "Failed to fetch %s (status %s)", url, response.status_code
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
        except Exception as e:
            logging.error(f"Unexpected error fetching first page {url}: {e}")
            return 1, []

    def _parse_entry(self, entry: BeautifulSoup) -> Dict[str, Any]:
        """
        Parses an entry and returns a dictionary with the content,
        author, date created and last changed.

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
    async def _fetch_page(self, session: requests.AsyncSession, url: str):
        """Fetches a page with retries on network errors."""
        return await session.get(url)

    async def scrape_page(
        self, session: requests.AsyncSession, url: str, semaphore: asyncio.Semaphore
    ) -> List[Dict[str, Any]]:
        """
        Scrapes a page and returns its entries.

        Args:
            session (requests.AsyncSession): session to make requests
            url (str): url of the page to scrape
            semaphore (asyncio.Semaphore): semaphore to limit the number of concurrent requests
        """
        async with semaphore:
            try:
                response = await self._fetch_page(session, url)
                if response.status_code != 200:
                    logging.error(
                        "Failed to fetch %s (status %s)", url, response.status_code
                    )
                    return []
                text = response.text
                soup = BeautifulSoup(text, "lxml")
                entries = soup.find_all(id="entry-item")
                return [self._parse_entry(entry) for entry in entries]
            except Exception as e:
                logging.error(f"Unexpected error in scrape_page {url}: {e}")
                return []

    async def scrape_thread(
        self,
        session: requests.AsyncSession,
        thread: str,
        max_concurrent_requests: int = 15,
    ):
        """
        Scrapes a thread and returns all entries.

        Args:
            session (requests.AsyncSession): session to make requests
            thread (str): thread to scrape, the part of the url after the /, before, if exists, ?.
            max_concurrent_requests (int, optional): max # of concurrent requests. Defaults to 15.
        """
        semaphore = asyncio.Semaphore(max_concurrent_requests)

        thread_url = self.base_url + thread
        number_of_pages, first_page_entries = await self._fetch_first_page(
            session, thread_url
        )
        console.thread_start(thread, number_of_pages)

        running_total = len(first_page_entries)
        console.page_done(
            thread, 1, number_of_pages, len(first_page_entries), running_total
        )

        async def _scrape_and_report(page_num):
            nonlocal running_total
            entries = await self.scrape_page(
                session, thread_url + "?p=" + str(page_num), semaphore
            )
            running_total += len(entries)
            console.page_done(
                thread, page_num, number_of_pages, len(entries), running_total
            )
            return entries

        tasks = [_scrape_and_report(page) for page in range(2, number_of_pages + 1)]
        results = await asyncio.gather(*tasks)

        return first_page_entries + [entry for page in results for entry in page]
