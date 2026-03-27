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
you can pass full URLs or just the slug (the part of the url after '/' and before '?'). for example:

```
python3 main.py -t https://eksisozluk.com/murat-kurum--2582131 https://eksisozluk.com/ekrem-imamoglu--2577439 -o json
```
or using slugs:
```
python3 main.py -t murat-kurum--2582131 ekrem-imamoglu--2577439 -o json
```
or from a file:
```
python3 main.py -f threads.txt -o csv
```

where in threads.txt, threads are listed as URLs or slugs, one per line:

```
https://eksisozluk.com/murat-kurum--2582131
ekrem-imamoglu--2577439
...
```

## contact

reach out to me at ceylaniberkay@gmail.com
