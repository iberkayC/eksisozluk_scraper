# eksisozluk scraper

asynchronously scrapes eksisozluk threads in python, and puts entries in a csv or json file, named after the thread. intended for educational purposes only.

## installation

clone the repo to your local machine.

navigate to the cloned directory and run the following code to install the requirements:

```
pip3 install -r requirements.txt
```

## usage

the scraper can be run from the terminal with command-line arguments or by specifying a file containing thread URLs. the basic usage is as follows:

```
python3 main.py -t [thread1] [thread2] ... -f [inputFile.txt] -o (csv or json)
```
replace `[thread1] [thread2] ...` with threads or `[inputFile.txt]` with a file containing threads to scrape line by line. for specifying threads, use the part of the url after '/' and before possible '?'. for example:

```
python3 main.py -t murat-kurum--2582131 ekrem-imamoglu--2577439 -o json
```
or
```
python3 main.py -f threads.txt -o csv
```

where in threads.txt, threads are listed as such:
```
murat-kurum--2582131
ekrem-imamoglu--2577439
...
```
## known problems

long links get shortened with dots in eksisozluk, not clickable in the output. impact is low for most usecases.

no whitespace between sentences if there is a paragraph break between them. impact is low.

## contact

reach out to me at ceylaniberkay@gmail.com
