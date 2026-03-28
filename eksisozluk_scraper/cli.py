"""CLI entry point for eksi-scraper."""

import argparse
import asyncio
import csv
import json
import logging
import sys
import time
from pathlib import Path
from typing import Literal
from urllib.parse import urlparse

from curl_cffi import requests

from . import console
from .scraper import EksiSozlukScraper

logger = logging.getLogger(__name__)

BASE_URL = "https://www.eksisozluk.com/"
HTTP_OK = 200


def extract_slug(value: str) -> str:
    """Return the thread slug from either a full URL or a bare slug.

    Examples:
        'https://eksisozluk.com/murat-kurum--2582131?p=2' -> 'murat-kurum--2582131'
        'murat-kurum--2582131' -> 'murat-kurum--2582131'

    """
    parsed = urlparse(value)
    if parsed.scheme in ("http", "https"):
        return parsed.path.strip("/")
    return value


async def process_thread(
    scraper: EksiSozlukScraper,
    session: requests.AsyncSession,
    thread: str,
    output_format: Literal["csv", "json"],
) -> None:
    """Scrape a single thread and write it to a file.

    Args:
        scraper (EksiSozlukScraper): scraper object
        session (requests.AsyncSession): session to make requests
        thread (str): thread to scrape
        output_format (csv or json): output format

    """
    try:
        logger.info("Started scraping thread %s", thread)
        t0 = time.monotonic()
        scraped_data = await scraper.scrape_thread(session, thread)
        elapsed = time.monotonic() - t0

        if scraped_data:
            filename = f"{thread}.{output_format}"
            if output_format == "json":
                with Path(filename).open("w", encoding="utf-8") as f:
                    json.dump(scraped_data, f, ensure_ascii=False, indent=2)
            else:
                with Path(filename).open(
                    "w",
                    encoding="utf-8",
                    newline="",
                ) as f:
                    writer = csv.DictWriter(f, fieldnames=scraped_data[0].keys())
                    writer.writeheader()
                    writer.writerows(scraped_data)
            console.thread_done(thread, len(scraped_data), elapsed, filename)
            logger.info(
                "Successfully scraped and saved thread %s to %s",
                thread,
                filename,
            )
        else:
            console.warn(f"no entries scraped for {thread}")
            logger.warning("No data scraped for thread: %s", thread)

    except Exception as e:
        console.thread_error(thread, str(e))
        logger.exception("Unexpected error in process_thread")


async def main(
    threads: list[str],
    output_format: Literal["csv", "json"] = "csv",
) -> None:
    """Scrape threads from eksisozluk and write results.

    Args:
        threads (list): threads to scrape (url slug)
        output_format (str): csv or json

    """
    scraper = EksiSozlukScraper(BASE_URL)
    console.session_start(len(threads))

    async with requests.AsyncSession(impersonate="chrome124") as session:
        tasks = [
            process_thread(scraper, session, thread, output_format)
            for thread in threads
        ]
        await asyncio.gather(*tasks)

    console.session_end()


def cli() -> None:
    """Parse arguments and run the scraper."""
    logging.basicConfig(
        filename="eksisozluk_scraper.log",
        level=logging.INFO,
        format="%(asctime)s - %(message)s",
    )
    parser = argparse.ArgumentParser(description="Scrape threads from eksisozluk.com")
    parser.add_argument(
        "-t",
        "--threads",
        metavar="thread",
        required=False,
        type=str,
        nargs="+",
        help="Threads to scrape. Accepts full URLs or slugs (part of the URL after /).",
    )
    parser.add_argument(
        "-f",
        "--file",
        metavar="file",
        required=False,
        type=str,
        help="File to read threads from, one thread per line.",
    )
    parser.add_argument(
        "-o",
        "--output",
        choices=["csv", "json"],
        default="csv",
        help="Output format (csv or json). Default is csv.",
    )
    verbosity = parser.add_mutually_exclusive_group()
    verbosity.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="Suppress all console output.",
    )
    verbosity.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Show per-page progress during scraping.",
    )
    args = parser.parse_args()
    console.configure(quiet=args.quiet, verbose=args.verbose)

    thread_list = [extract_slug(t) for t in args.threads] if args.threads else []

    if args.file:
        try:
            with Path(args.file).open(encoding="utf-8") as file:
                thread_list.extend(
                    [extract_slug(line.strip()) for line in file],
                )
        except OSError as e:
            console.error(f"Cannot read file {args.file}: {e}")
            logger.exception("Error reading file %s", args.file)
            sys.exit(1)

    if thread_list:
        try:
            asyncio.run(main(thread_list, args.output))
        except KeyboardInterrupt:
            console.error("Interrupted by user")
            sys.exit(130)
    else:
        console.error("No threads provided.")
        logger.error("No threads provided. Exiting.")
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    cli()
