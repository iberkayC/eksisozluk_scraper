# eksisozluk scraper

asynchronously scrapes eksisozluk threads in python, and puts entries in a csv file, named after the thread. intended for educational purposes only.

## installation

clone the repo to your local machine.

navigate to the cloned directory and run the following code to install the requirements:

```bash
pip3 install -r requirements.txt
```

## usage

run the scraper with the following command in the terminal:

```bash
python3 eksisozluk_scraper.py -t [thread1] [thread2] ...
```
replace `[thread1] [thread2] ...` with threads you want to scrape, use the parts of the url after the '/'. for example:

```bash
python3 eksisozluk_scraper.py -t murat-kurum--2582131 ekrem-imamoglu--2577439
```

## known problems

threads in the nature of 'ekrem imamoglu' and 'ekrem imamoğlu' gets saved to the same csv, impact is negligible, easily fixable.

long links get shortened with dots in eksisozluk, not clickable in the csv. impact is low for most usecases.

no whitespace between sentences if there is a paragraph break between them. impact is low.

## contact

reach out to me at ceylaniberkay@gmail.com
