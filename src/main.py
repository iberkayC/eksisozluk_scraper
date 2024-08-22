"""Scrape threads from eksisozluk

Asynchronously scrapes threads from eksisozluk, 
taking threads as command line arguments and 
writes them to csv files. Some variables are too low 
for any real scraping, but it's good for educational
purposes.
"""
from typing import List, Literal
import argparse
import asyncio
import sys
import logging
import aiohttp
from eksisozluk_scraper import EksiSozlukScraper
from data_writer import DataWriter

BASE_URL = 'https://www.eksisozluk.com/'

logging.basicConfig(filename='eksisozluk_scraper.log', level=logging.INFO,
                    format='%(asctime)s - %(message)s')

async def process_thread(scraper: EksiSozlukScraper,
                         session: aiohttp.ClientSession,
                         thread: str,
                         output_format: Literal['csv', 'json']) -> None:
    """
    Process a thread, scrape it and write it to a file.

    Args:
        scraper (EksiSozlukScraper): scraper object
        session (aiohttp.ClientSession): session to make requests
        thread (str): thread to scrape
        output_format (csv or json): output format 
    """
    try:
        logging.info('Started scraping thread %s', thread)
        scraped_data = await scraper.scrape_thread(session, thread)

        if scraped_data:
            filename = f"{thread}.{output_format}"
            await DataWriter.write_data(filename, scraped_data, output_format)
            logging.info(f"Successfully scraped and saved thread {thread} to {filename}")
        else:
            logging.warning(f"No data scraped for thread: {thread}")

    except Exception as e:
        logging.error(f"Unexpected error in process_thread: {e}")


async def main(threads: List[str], output_format: Literal['csv', 'json'] = 'csv') -> None:
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
        tasks = [process_thread(scraper, session, thread, output_format) for thread in threads]
        await asyncio.gather(*tasks)


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
    parser.add_argument('-o', '--output',
                        choices=['csv', 'json'],
                        default='csv',
                        help='Output format (csv or json). Default is csv.')
    args = parser.parse_args()

    thread_list = args.threads if args.threads else []


    if args.file:
        try:
            with open(args.file, 'r', encoding='utf-8') as file:
                thread_list.extend([line.strip() for line in file.readlines()])
        except IOError as e:
            logging.error(f"Error reading file {args.file}: {e}")
            sys.exit(1)

    if thread_list:
        asyncio.run(main(thread_list, args.output))
    else:
        logging.error('No threads provided. Exiting.')
        parser.print_help()
        sys.exit(1)
