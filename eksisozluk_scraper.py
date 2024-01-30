"""Scrape threads from eksisozluk

Asynchronously scrapes threads from eksisozluk, 
taking threads as command line arguments and 
writes them to csv files. 
"""
import argparse
import csv
import time
import asyncio
import sys
import logging
import aiofiles
import aiohttp
import backoff
from bs4 import BeautifulSoup

BASE_URL = 'https://eksisozluk111.com/'
logging.basicConfig(filename='eksisozluk_scraper.log', level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


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
    async def write_to_csv(filename: str,
                           data: list) -> None:
        """Asynchronous data writing to csv file.

        Args:
            filename (str): the name of the file to write.
            data (list): the data to write.
        """
        async with aiofiles.open(filename, 'w', encoding='utf-8', newline='') as f:
            fieldnames = ['Content', 'Author', 'Date Created', 'Last Changed']
            writer = csv.DictWriter(f, fieldnames=fieldnames)

            await writer.writeheader()
            for row in data:
                await writer.writerow(row)

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
        try:
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
        except Exception as exc:
            logging.error('Error scraping page: %s, error: %s', url, exc)

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

        # thread_name = thread.split('--')[0].replace('-', ' ')
        logging.info('Successfully scraped thread: %s', thread)


async def main(threads: list):
    """Scrapes threads from eksisozluk

    Args:
        threads (list): list of threads to scrape, part of the url after the /, before possibly ?.
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
    try:
        parser = argparse.ArgumentParser(
            description='Scrape threads from eksisozluk.com')
        parser.add_argument('-t', '--threads', metavar='thread', required=False, type=str, nargs='+',
                            help='Threads to scrape, part of the url after the /, before possibly ?.')
        parser.add_argument('-f', '--file', metavar='file', required=False, type=str,
                            help='File to read threads from, one thread per line.')
        args = parser.parse_args()

        MAX_THREADS_AT_ONCE = 30

        thread_list = args.threads if args.threads else []
        if args.file:
            with open(args.file, 'r', encoding='utf-8') as file:
                thread_list.extend([line.strip() for line in file.readlines()])

        if thread_list:
            for i in range(0, len(thread_list), MAX_THREADS_AT_ONCE):
                thread_subset = thread_list[i:i + MAX_THREADS_AT_ONCE]
                start_time = time.perf_counter()
                asyncio.run(main(thread_subset))
                logging.info('Successfully scraped %d thread(s).',
                             len(thread_subset))

        if not thread_list:
            print('No threads provided, exiting.')
            sys.exit(0)
    except Exception as e:
        logging.error('Error scraping threads: %s', e)
