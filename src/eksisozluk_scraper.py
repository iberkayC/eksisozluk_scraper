"""
Contains the EksiSozlukScraper class. Scrapes threads from eksisozluk.com
"""
import asyncio
import aiohttp
from bs4 import BeautifulSoup
import backoff


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

    async def find_number_of_pages(self,
                                   session: aiohttp.ClientSession,
                                   url: str) -> int:
        """Finds the number of pages in a thread

        Args:
            session (aiohttp.ClientSession): session to make requests
            url (str): url of the thread

        Returns:
            int: number of pages in the thread.
        """
        async with session.get(url) as response:
            soup = BeautifulSoup(await response.text(), 'lxml')
            pager_div = soup.find('div', class_='pager')
            if pager_div and 'data-pagecount' in pager_div.attrs:
                return pager_div['data-pagecount']
            return 1


    @backoff.on_exception(backoff.expo,
                          aiohttp.ClientError,
                          max_tries=8,
                          max_time=300)
    async def scrape_page(self,
                          session: aiohttp.ClientSession,
                          url: str,
                          semaphore: asyncio.Semaphore,
                          scraped_data: list) -> None:
        """
        Scrapes a page and appends the data to scraped_data

        Args:
            session (aiohttp.ClientSession): session to make requests
            url (str): url of the page to scrape
            semaphore (asyncio.Semaphore): semaphore to limit the number of concurrent requests
            scraped_data (list): list to append the scraped data
        """
        async with semaphore:
            async with session.get(url) as response:
                soup = BeautifulSoup(await response.text(), 'lxml')
                entries = soup.find_all(id='entry-item')
                for entry in entries:
                    content = entry.find(class_='content').text.strip()
                    author = entry.find(class_='entry-author').text.strip()
                    entry_date_text = entry.find(
                        class_='entry-date').text.strip()

                    if '~' in entry_date_text:
                        date_created, last_changed = [
                            part.strip() for part in entry_date_text.split('~')]
                    else:
                        date_created = entry_date_text
                        last_changed = 'null'

                    entry_data = {
                        'Content': content,
                        'Author': author,
                        'Date Created': date_created,
                        'Last Changed': last_changed
                    }
                    scraped_data.append(entry_data)


    async def scrape_thread(self,
                            session: aiohttp.ClientSession,
                            thread: str,
                            max_concurrent_requests: int = 15):
        """
        Scrapes a thread and writes the data to a csv file

        Args:
            session (aiohttp.ClientSession): session to make requests
            thread (str): thread to scrape, the part of the url after the /, before, if exists, ?.
            max_concurrent_requests (int, optional): max # of concurrent requests. Defaults to 15.
        """
        semaphore = asyncio.Semaphore(max_concurrent_requests)
        scraped_data = []

        thread_url = self.base_url + thread
        number_of_pages = await self.find_number_of_pages(session, thread_url)
        tasks = [self.scrape_page(session, thread_url + '?p=' + str(page), semaphore, scraped_data)
                 for page in range(1, int(number_of_pages) + 1)]
        await asyncio.gather(*tasks)

        return scraped_data
