# eksi-scraper

fast, asynchronous eksisozluk thread scraper. exports entries to csv or json.

## installation

```bash
uv pip install eksi-scraper
```
or with pip:
```bash
pip install eksi-scraper
```

## usage

```bash
eksi-scraper -t [thread1] [thread2] ... -f [inputFile.txt] -o (csv or json)
```
you can pass full URLs or just the slug (the part of the url after '/' and before '?'). for example:

```bash
eksi-scraper -t https://eksisozluk.com/murat-kurum--2582131 https://eksisozluk.com/ekrem-imamoglu--2577439 -o json
```
or using slugs:
```bash
eksi-scraper -t murat-kurum--2582131 ekrem-imamoglu--2577439 -o json
```
or from a file:
```bash
eksi-scraper -f threads.txt -o csv
```

where in threads.txt, threads are listed as URLs or slugs, one per line:

```
https://eksisozluk.com/murat-kurum--2582131
ekrem-imamoglu--2577439
...
```

### options

| flag | description |
|---|---|
| `-t, --threads` | threads to scrape (URLs or slugs) |
| `-f, --file` | file with threads, one per line |
| `-o, --output` | output format: `csv` (default) or `json` |
| `-v, --verbose` | show per-page progress |
| `-q, --quiet` | suppress all console output |

### console output

by default, eksi-scraper shows progress in the terminal:

```
[eksi-scraper] Scraping 2 threads
[murat-kurum--2582131] Found 47 pages
[ekrem-imamoglu--2577439] Found 112 pages
[murat-kurum--2582131] Done: 470 entries in 12.3s -> murat-kurum--2582131.json
[ekrem-imamoglu--2577439] Done: 1120 entries in 28.7s -> ekrem-imamoglu--2577439.json
[eksi-scraper] Finished: 2 threads, 1590 entries, 28.7s elapsed
```

use `-v` for per-page progress, `-q` for silent operation.

## output

each entry has the following fields:

| field | description |
|---|---|
| Content | the entry text, with full URLs restored |
| Author | username of the author |
| Date Created | original post date |
| Last Changed | last edit date, or null if never edited |

## contact

reach out to me at ceylaniberkay@gmail.com
