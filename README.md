# alexa
Get the most accessed sites on the internet and some info about them

## Scripts

`get_sites.py`
is script to parse wiki pages list of Alexa sites and additional metadata
Then scrapes sites for wordcounts
`get_alexa.py`
is where started, first dive into AWS Alexa TopSites api where hit issues, raised ticket, then started scraping. Had it relatively close with 98/100 sites and metadata where found additional functions in bs4 that 

## Use

For now, to get list of sites and word counts
`./get_sites.py -r 100 -w`

Log will output to `alexa_ranks.log` and data to `results/results.txt` 

Word counts and metrics logged to `results/metrics.txt`
Some json sorted artifacts in `results/top_lists.txt`

## Setup

TODO, but otherwise a few pip installs needed.

Possibly local aws username/key pair and access and java if are to run db locally

## Enhancements

1. Store data in proper JSON based DB like dynamoDB, quicker and allow sql like or plugin enabled querying
2. Get most up to date lists by using AWS Alexa TopSites api, if is working, although do like the wikipedia thing
4. Additional test cases in pytest
