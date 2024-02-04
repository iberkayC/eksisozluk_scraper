"""Scrape threads from eksisozluk

Asynchronously scrapes threads from eksisozluk, 
taking threads as command line arguments and 
writes them to csv files. 
"""
import argparse
import asyncio
import sys
import logging
import aiohttp
from eksisozluk_scraper import EksiSozlukScraper
from csvwriter import CSVWriter

BASE_URL = 'https://www.eksisozluk111.com/'

logging.basicConfig(filename='eksisozluk_scraper.log', level=logging.INFO,
                    format='%(asctime)s - %(message)s')

async def main(threads: list):
    """
    Main function to scrape threads from eksisozluk

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
        scrape_tasks = [scraper.scrape_thread(session, thread) for thread in threads]
        results = await asyncio.gather(*scrape_tasks)

        for thread, scraped_data in zip(threads, results):
            await CSVWriter.write_to_csv(f'{thread}.csv', scraped_data)
            logging.info('Successfully scraped and saved thread %s', thread)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Scrape threads from eksisozluk.com')
    parser.add_argument('-t', '--threads',
                        metavar='thread',
                        required=False,
                        type=str,
                        nargs='+',
                        help='Threads to scrape, part of the url after the /, before possibly ?.')
    parser.add_argument('-f', '--file',
                        metavar='file',
                        required=False,
                        type=str,
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
            logging.info('Started scraping.')
            asyncio.run(main(thread_subset))

    else:
        print('No threads provided, exiting.')
        sys.exit(0)
