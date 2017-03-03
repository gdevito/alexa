#!/usr/bin/python
import argparse
import io
import json
import logging
import pprint
import re
import requests
import sys
import time

from bs4 import BeautifulSoup

def get_alexa_sites(rank=100):
    ''' parse wiki table for top rank and collect additional info from 
    the table.  previous AWS Alexa api had not been working and found this
    to work nicely once read up on bs4 module'''

    r = requests.get('https://en.wikipedia.org/wiki/List_of_most_popular_websites')
    html = BeautifulSoup(r.content, 'lxml')
    top_sites = []

    for tr in html.findAll('tr'):
        tds = tr.findAll('td')
        it = 0
        site = {}
        for td in tds:
            if td.find('sup'):
                td.find('sup').extract()
            txt = td.getText()
            if it == 0: site['co'] = txt
            elif it == 1: site['url'] = txt
            elif it == 2: site['rank'] = txt
            elif it == 3: site['prev_rank'] = txt
            elif it == 4:
                site['type'] = txt
            #refs = td.find_all('a', href=True)
            #for r in refs:
            #    print site['type']
            #    print r.text
                #site['type'] = [site['type'] + r.text]
            elif it == 5: site['country'] = txt
            it += 1
        if site:
            top_sites.append(site)
    assert len(top_sites) >= rank
    return top_sites[:rank]

def get_words(url):
    
    try:
        r = requests.get('http://www.' + url)
    except requests.exceptions.RequestException as e:
        logging.error(e)
        sys.exit(1)
    html = BeautifulSoup(r.content, 'html.parser')
    #text = html.findAll(text=True)
    refs = html.find_all('a')
    words = []
    for ref in refs:
        strings = ref.get_text().encode('utf-8').split()
        for string in strings:
            string = re.sub('[^a-zA-Z0-9-_*.]', '', string)
            #for c in string:
                # very restrictive
                #if not c.isalphanum():
                #    string = None
            words.append(string)
    logging.info('URL: '+url)
    logging.info('LEN: '+str(len(words)))
         
    return words, len(words)

def main():

    logging.basicConfig(filename='alexa_ranks.log', level=logging.INFO)

    parser = argparse.ArgumentParser()
    parser.add_argument('-r', '--rank', type=int, help='Rankings to get 1 to 100')
    parser.add_argument('-w', '--words', dest='words', action='store_true', default=False, help='Calculate word counts')
    args = parser.parse_args()

    if args.rank:
        sites = get_alexa_sites(args.rank)
    else:
        sites = get_alexa_sites()
        logging.info('Default get 100')

    if args.words:
        for site in sites:
            logging.info(site)
            start = time.time()
            words, len = get_words(site['url'])
            site['wc'] = len
            site['words'] = words
            site['time'] = start - time.time()
            logging.info('Time: ', site['time'])
        with io.open('word_counts.txt', 'w', encoding='utf-8') as f:
            logging.info('Writing json out to word_counts.txt')
            f.write(unicode(json.dumps(sites, indent=4, ensure_ascii=False)))

if __name__ == "__main__":
    main()

