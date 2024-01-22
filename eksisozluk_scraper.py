"""Scrape threads from eksisozluk

Asynchronously scrapes threads from eksisozluk, 
taking threads as command line arguments and 
writes them to csv files. 
"""
import argparse
import csv
import asyncio
import aiohttp
import backoff
from bs4 import BeautifulSoup

BASE_URL = 'https://eksisozluk111.com/'

class EksiSozlukScraper:
    """Scrapes threads from eksisozluk
    """
    def __init__(self, base_url: str) -> None:
        """Initializes EksiSozlukScraper with base_url

        Args:
            base_url (str): base url of eksisozluk
        """
        # necessary variable base_url because of government bans
        self.base_url = base_url

    @staticmethod
    def write_to_csv(filename: str,
                     data: list) -> None:
        """Writes data to csv file

        Args:
            filename (str): name of the file to write
            data (list): data to write
        """

        with open(filename, 'w', encoding='utf-8', newline='') as f:
            fieldnames = ['Content', 'Author', 'Date Created', 'Last Changed']
            writer = csv.DictWriter(f, fieldnames=fieldnames)

            writer.writeheader()
            for row in data:
                writer.writerow(row)

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
        """Scrapes a page and appends the data to scraped_data

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
        """Scrapes a thread and writes the data to a csv file

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

        thread_name = thread.split('--')[0].replace('-', ' ')
        self.write_to_csv(f'{thread_name}.csv', scraped_data)


async def main(threads: list):
    """Scrapes threads from eksisozluk

    Args:
        threads (list): _description_
    """
    scraper = EksiSozlukScraper(BASE_URL)
    header = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like\
            Gecko) Chrome/58.0.3029.110 Safari/537.3',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
    }

    async with aiohttp.ClientSession(headers=header) as session:
        tasks = [scraper.scrape_thread(session, thread) for thread in threads]
        await asyncio.gather(*tasks)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Scrape threads from eksisozluk.com')
    parser.add_argument('-t', '--threads', metavar='thread', required=True, type=str, nargs='+',
                        help='Threads to scrape, part of the url after the /, before possibly ?.')
    args = parser.parse_args()

    import time
    start_time = time.perf_counter()
    asyncio.run(main(args.threads))
    print(f'It took {time.perf_counter() - start_time} seconds\
          to scrape {len(args.threads)} thread(s).')
